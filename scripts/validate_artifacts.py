#!/usr/bin/env python3
"""Validate a hackathon session or prep artifact tree before declaring done.

Checks that the artifact layout and CSV schema meet the contracts defined in
`playbook/RULES.md` (§5 preflight, §12 profiling, §14.3 session milestones,
§18 preparer artifacts), `playbook/SCHEMA.md` §§1–2 (CSV schemas), and
`playbook/EXECUTION.md` §5.3 (required folder structure).

Session mode (`--mode session`, default):
  `--session path/to/sessions/<workload>/<iteration>/<agent-name>/`
  Validates the session artifact tree. `WORKLOAD_CARD.md` is expected one level
  up at `sessions/<workload>/<iteration>/WORKLOAD_CARD.md`.

Prep mode (`--mode prep`):
  `--session path/to/sessions/<workload>/<iteration>/`
  Validates the preparer-agent's artifact tree under that iteration's `prep/`
  subdirectory plus the filled `WORKLOAD_CARD.md` (§10 HP-lock consistency).

Usage
-----
    python validate_artifacts.py --session PATH                  # session mode
    python validate_artifacts.py --session PATH --mode prep      # prep mode
    python validate_artifacts.py --session PATH --strict         # WARN → FAIL

Exits 0 on success, 1 if any FAIL occurs (or any WARN in `--strict` mode).
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = [
    "session_id", "experiment_id", "run_index", "timestamp", "tier", "phase",
    "candidate", "change", "baseline_ref", "commit_hash", "env_snapshot_id",
    "primary_metric", "quality_metric", "peak_gpu_mem_mib", "quality_verdict",
    "win_status", "logging_mode", "event_log_anchor", "notes",
    "gpu_util_avg", "cpu_util_avg", "compile_time_s", "hp_values_json",
]

QUALITY_VERDICTS = {"PASS", "FAIL", "INCONCLUSIVE", "NA"}
SESSION_WIN_STATUSES = {"NA", "EXPERIMENT", "WIN", "INVALIDATED"}
PREP_WIN_STATUSES = {"NA", "EXPERIMENT"}

SESSION_PHASE_VALUES = {
    "phase_1_bugfix", "phase_2_adopt", "phase_3_iter", "phase_3_validation",
}
PREP_PHASE_VALUES = {
    "prep_p1_sanity_baseline", "prep_p2_short_baseline", "prep_p2_sweep",
    "prep_p2_default_ttr", "prep_p2_validation",
}

PREP_EXIT_RE = re.compile(r"^T\+\S+\s+\[PREP-EXIT\s+(\d+)\]", re.MULTILINE)
PREP_START_RE = re.compile(r"^T\+0\s+\[PREP-START\]", re.MULTILINE)
PREP_CLOSE_RE = re.compile(r"^T\+\S+\s+\[PREP-CLOSE\]", re.MULTILINE)
BASELINE_TAG_RE = re.compile(r"^T\+\S+\s+\[BASELINE\]", re.MULTILINE)
NOISE_TAG_RE = re.compile(r"^T\+\S+\s+\[NOISE\]", re.MULTILINE)

# Pulls the first ```json ... ``` block after the `### 10.1` heading. Tolerant of
# blank lines and trailing whitespace; fails open (returns None) if the card does
# not match the expected shape, so the check degrades to a WARN rather than a
# hard FAIL on idiosyncratic cards.
CARD_HP_VALUES_RE = re.compile(
    r"###\s*10\.1[\s\S]*?```json\s*(\{[^`]*\})\s*```",
    re.MULTILINE,
)


@dataclass
class CheckResult:
    name: str
    status: str              # PASS / FAIL / WARN
    detail: str = ""


# --- helpers ---------------------------------------------------------------

def _file_check(name: str, path: Path, required: bool = True) -> CheckResult:
    if not path.exists():
        return CheckResult(name, "FAIL" if required else "WARN",
                           f"missing: {path}")
    if path.is_file() and path.stat().st_size == 0:
        return CheckResult(name, "FAIL" if required else "WARN",
                           f"empty file: {path}")
    return CheckResult(name, "PASS", str(path))


# --- required-tree checks --------------------------------------------------

def check_required_tree(session: Path) -> list[CheckResult]:
    artifacts = session / "artifacts"
    # WORKLOAD_CARD.md lives one level up (shared across operators for this iteration).
    return [
        _file_check("workload_card", session.parent / "WORKLOAD_CARD.md", required=True),
        _file_check("baseline_txt",
                    artifacts / "benchmarks" / "baseline.txt", required=True),
        _file_check("results_csv",
                    artifacts / "benchmarks" / "results.csv", required=True),
        _file_check("profiler_commands",
                    artifacts / "profiles" / "profiler_commands.md", required=True),
        _file_check("event_log",
                    artifacts / "notes" / "event_log.md", required=True),
        _file_check("final_summary",
                    artifacts / "FINAL_SUMMARY.md", required=True),
        # §7.1 preflight dump is recommended, not strictly required — WARN if missing.
        _file_check("preflight_txt",
                    artifacts / "notes" / "preflight.txt", required=False),
    ]


def check_required_prep_tree(iteration: Path) -> list[CheckResult]:
    prep = iteration / "prep"
    return [
        _file_check("workload_card", iteration / "WORKLOAD_CARD.md", required=True),
        _file_check("prep_event_log",
                    prep / "prep_event_log.md", required=True),
        _file_check("prep_results_csv",
                    prep / "prep_results.csv", required=True),
        _file_check("prep_baseline_capture",
                    prep / "baseline_capture.txt", required=True),
    ]


def check_profiling_traces(session: Path) -> CheckResult:
    profiles = session / "artifacts" / "profiles"
    if not profiles.is_dir():
        return CheckResult("profiling_traces", "FAIL",
                           f"missing directory: {profiles}")
    traces = [p for p in profiles.iterdir()
              if p.is_file() and p.name != "profiler_commands.md"]
    if not traces:
        return CheckResult("profiling_traces", "FAIL",
                           f"no trace files in {profiles}")
    return CheckResult("profiling_traces", "PASS", f"{len(traces)} trace file(s)")


# --- schema checks ---------------------------------------------------------

def _load_results_or_none(path: Path
                          ) -> tuple[pd.DataFrame | None, CheckResult | None]:
    if not path.exists():
        return None, CheckResult("results_schema", "FAIL", "results.csv missing")
    try:
        return pd.read_csv(path), None
    except Exception as exc:
        return None, CheckResult("results_schema", "FAIL",
                                 f"failed to parse {path}: {exc!s}")


def check_results_schema(csv_path: Path, mode: str) -> list[CheckResult]:
    """Validate a CSV against SCHEMA §1 (session) or §2 (prep)."""
    df, err = _load_results_or_none(csv_path)
    if err is not None:
        return [err]
    assert df is not None

    phase_values = SESSION_PHASE_VALUES if mode == "session" else PREP_PHASE_VALUES
    win_statuses = SESSION_WIN_STATUSES if mode == "session" else PREP_WIN_STATUSES
    checks: list[CheckResult] = []

    # Header check: first N columns must match REQUIRED_COLUMNS exactly, in order.
    header = list(df.columns[:len(REQUIRED_COLUMNS)])
    if header != REQUIRED_COLUMNS:
        diffs = [(i, exp, got)
                 for i, (exp, got) in enumerate(zip(REQUIRED_COLUMNS, header))
                 if exp != got]
        detail = (f"first diff at col {diffs[0][0]} "
                  f"(expected {diffs[0][1]!r}, got {diffs[0][2]!r})"
                  if diffs else
                  f"header too short: {len(header)} < {len(REQUIRED_COLUMNS)}")
        checks.append(CheckResult("results_header", "FAIL", detail))
    else:
        checks.append(CheckResult("results_header", "PASS",
                                  f"{len(df.columns)} columns"))

    if df.empty:
        checks.append(CheckResult("results_nonempty", "FAIL",
                                  f"{csv_path.name} has no rows"))
        return checks
    checks.append(CheckResult("results_nonempty", "PASS", f"{len(df)} rows"))

    # Baseline recorded at tier=full (session-only; prep's Tier-2 baseline is
    # prep_p2_default_ttr, not a tier=full candidate=baseline row).
    if mode == "session":
        baseline_full = df[(df["tier"] == "full") & (df["candidate"] == "baseline")]
        if baseline_full.empty:
            checks.append(CheckResult("baseline_recorded", "FAIL",
                                      "no tier=full candidate=baseline rows"))
        else:
            checks.append(CheckResult(
                "baseline_recorded", "PASS",
                f"{baseline_full['experiment_id'].nunique()} baseline experiment(s)"
            ))

    # Per-experiment constancy of identity and verdict columns.
    identity_cols = ["candidate", "change", "baseline_ref", "phase", "tier",
                     "quality_verdict", "win_status"]
    constancy_fails: list[tuple[str, str]] = []
    for exp_id, group in df.groupby("experiment_id"):
        for c in identity_cols:
            if group[c].nunique(dropna=False) > 1:
                constancy_fails.append((str(exp_id), c))
    if constancy_fails:
        detail = "; ".join(f"{eid}/{col}" for eid, col in constancy_fails[:5])
        if len(constancy_fails) > 5:
            detail += f"; … (+{len(constancy_fails) - 5} more)"
        checks.append(CheckResult("per_experiment_constancy", "FAIL", detail))
    else:
        checks.append(CheckResult(
            "per_experiment_constancy", "PASS",
            f"{df['experiment_id'].nunique()} experiments"
        ))

    # Phase enum.
    bad_phase = set(df["phase"].dropna().astype(str).unique()) - phase_values
    if bad_phase:
        checks.append(CheckResult(
            "phase_enum", "FAIL",
            f"unexpected values for --mode {mode}: {sorted(bad_phase)}"
        ))
    else:
        checks.append(CheckResult("phase_enum", "PASS", ""))

    # quality_verdict / win_status enums.
    bad_verdict = set(df["quality_verdict"].dropna().astype(str).unique()) - QUALITY_VERDICTS
    if bad_verdict:
        checks.append(CheckResult("quality_verdict_enum", "FAIL",
                                  f"unexpected values: {sorted(bad_verdict)}"))
    else:
        checks.append(CheckResult("quality_verdict_enum", "PASS", ""))
    bad_win = set(df["win_status"].dropna().astype(str).unique()) - win_statuses
    if bad_win:
        checks.append(CheckResult(
            "win_status_enum", "FAIL",
            f"unexpected values for --mode {mode}: {sorted(bad_win)}"
        ))
    else:
        checks.append(CheckResult("win_status_enum", "PASS", ""))

    # baseline_ref validity: every non-baseline experiment must reference a
    # baseline experiment_id that exists in the same tier.
    baseline_ids_by_tier: dict[str, set[str]] = {}
    for tier_val, sub in df.groupby("tier"):
        baseline_ids_by_tier[str(tier_val)] = set(
            sub[sub["candidate"] == "baseline"]["experiment_id"]
            .astype(str).unique()
        )
    non_baseline = df[df["candidate"] != "baseline"]
    ref_fails: list[tuple[str, str]] = []
    for (exp_id, tier_val), group in non_baseline.groupby(["experiment_id", "tier"]):
        ref = group["baseline_ref"].iloc[0]
        if pd.isna(ref) or str(ref).strip() == "":
            ref_fails.append((str(exp_id), "empty baseline_ref"))
            continue
        valid_ids = baseline_ids_by_tier.get(str(tier_val), set())
        if str(ref) not in valid_ids:
            ref_fails.append((str(exp_id),
                              f"baseline_ref={ref!r} not in tier={tier_val}"))
    if ref_fails:
        detail = "; ".join(f"{eid}: {msg}" for eid, msg in ref_fails[:5])
        if len(ref_fails) > 5:
            detail += f"; … (+{len(ref_fails) - 5} more)"
        checks.append(CheckResult("baseline_ref_valid", "FAIL", detail))
    else:
        checks.append(CheckResult("baseline_ref_valid", "PASS", ""))

    return checks


def _card_hp_values_json(card_path: Path) -> str | None:
    """Extract the first json block under `### 10.1` in the filled card."""
    if not card_path.exists():
        return None
    m = CARD_HP_VALUES_RE.search(card_path.read_text())
    if not m:
        return None
    try:
        # Canonicalise via json load+dump so whitespace differences don't defeat match.
        return json.dumps(json.loads(m.group(1)), sort_keys=True)
    except json.JSONDecodeError:
        return None


def check_locked_hp_consistency(session: Path) -> CheckResult:
    """Session-mode check: phase_3_* rows' hp_values_json matches card §10.1."""
    card_json = _card_hp_values_json(session.parent / "WORKLOAD_CARD.md")
    if card_json is None:
        return CheckResult(
            "locked_hp_matches_card", "WARN",
            "could not parse WORKLOAD_CARD §10.1 json block; skipping match check"
        )
    results_csv = session / "artifacts" / "benchmarks" / "results.csv"
    df, _ = _load_results_or_none(results_csv)
    if df is None:
        return CheckResult("locked_hp_matches_card", "FAIL",
                           "results.csv unavailable")
    phase3 = df[df["phase"].astype(str).str.startswith("phase_3_")]
    if phase3.empty:
        return CheckResult("locked_hp_matches_card", "PASS",
                           "no phase_3_* rows yet (pre-Phase-3 snapshot)")
    bad: list[str] = []
    for _, row in phase3.iterrows():
        row_json = str(row.get("hp_values_json", "") or "")
        try:
            canonical = json.dumps(json.loads(row_json), sort_keys=True)
        except json.JSONDecodeError:
            bad.append(f"{row['experiment_id']}: non-json hp_values_json")
            continue
        if canonical != card_json:
            bad.append(f"{row['experiment_id']}: {row_json!r} != card §10.1")
    if bad:
        detail = "; ".join(bad[:3]) + (f"; … (+{len(bad) - 3} more)"
                                        if len(bad) > 3 else "")
        return CheckResult("locked_hp_matches_card", "FAIL", detail)
    return CheckResult("locked_hp_matches_card", "PASS",
                       f"{len(phase3)} phase_3_* row(s) match card")


def check_prep_invariants(iteration: Path) -> list[CheckResult]:
    """Prep-mode: [PREP-START], [PREP-EXIT 1/2/3], [PREP-CLOSE] uniqueness
    and ordering, plus BASELINE/NOISE-before-PREP-EXIT-2."""
    log = iteration / "prep" / "prep_event_log.md"
    checks: list[CheckResult] = []
    if not log.exists():
        return [CheckResult("prep_invariants", "FAIL",
                            f"missing {log}")]
    text = log.read_text()

    def _unique(name: str, pattern: re.Pattern[str]) -> CheckResult:
        matches = pattern.findall(text)
        if len(matches) == 1:
            return CheckResult(name, "PASS", "")
        if not matches:
            return CheckResult(name, "FAIL", f"missing tag")
        return CheckResult(name, "FAIL",
                           f"{len(matches)} occurrences (expected 1)")

    checks.append(_unique("prep_start_unique", PREP_START_RE))
    checks.append(_unique("prep_close_unique", PREP_CLOSE_RE))

    for n in range(1, 4):
        pat = re.compile(rf"^T\+\S+\s+\[PREP-EXIT\s+{n}\]", re.MULTILINE)
        checks.append(_unique(f"prep_exit_{n}_unique", pat))

    # [PREP-EXIT 2] must follow at least one [BASELINE] and one [NOISE].
    pe2_match = re.search(r"^T\+\S+\s+\[PREP-EXIT\s+2\]", text, re.MULTILINE)
    if not pe2_match:
        checks.append(CheckResult("prep_exit_2_preceded", "WARN",
                                  "[PREP-EXIT 2] missing"))
    else:
        prefix = text[:pe2_match.start()]
        have_baseline = bool(BASELINE_TAG_RE.search(prefix))
        have_noise = bool(NOISE_TAG_RE.search(prefix))
        if have_baseline and have_noise:
            checks.append(CheckResult("prep_exit_2_preceded", "PASS",
                                      "[BASELINE] and [NOISE] present before [PREP-EXIT 2]"))
        else:
            missing = [t for t, ok in
                       (("[BASELINE]", have_baseline), ("[NOISE]", have_noise)) if not ok]
            checks.append(CheckResult("prep_exit_2_preceded", "FAIL",
                                      f"missing before [PREP-EXIT 2]: {', '.join(missing)}"))

    # Card §10.1 hp_values_json must match a winning experiment's row.
    card_json = _card_hp_values_json(iteration / "WORKLOAD_CARD.md")
    prep_csv = iteration / "prep" / "prep_results.csv"
    if card_json is None:
        checks.append(CheckResult("card_hp_vs_winner", "WARN",
                                  "could not parse WORKLOAD_CARD §10.1"))
    else:
        df, _ = _load_results_or_none(prep_csv)
        if df is None:
            checks.append(CheckResult("card_hp_vs_winner", "FAIL",
                                      "prep_results.csv unavailable"))
        else:
            matching = 0
            for _, row in df.iterrows():
                row_json = str(row.get("hp_values_json", "") or "")
                try:
                    canonical = json.dumps(json.loads(row_json), sort_keys=True)
                except json.JSONDecodeError:
                    continue
                if canonical == card_json:
                    matching += 1
            if matching == 0:
                checks.append(CheckResult(
                    "card_hp_vs_winner", "FAIL",
                    "no prep_results.csv row matches card §10.1 hp_values_json"
                ))
            else:
                checks.append(CheckResult(
                    "card_hp_vs_winner", "PASS",
                    f"{matching} row(s) match card §10.1"
                ))
    return checks


# --- content / fill-in checks ---------------------------------------------

def _placeholder_check(name: str, path: Path) -> CheckResult:
    if not path.exists():
        return CheckResult(name, "FAIL", f"missing: {path}")
    text = path.read_text()
    n = text.count("___")
    if n > 0:
        return CheckResult(name, "WARN",
                           f"{n} `___` placeholder(s) remain in {path}")
    return CheckResult(name, "PASS", "no placeholders")


def check_fillins(session: Path) -> list[CheckResult]:
    return [
        _placeholder_check("workload_card_filled",
                           session.parent / "WORKLOAD_CARD.md"),
        _placeholder_check("final_summary_filled",
                           session / "artifacts" / "FINAL_SUMMARY.md"),
    ]


# --- reporting -------------------------------------------------------------

MARKERS = {"PASS": "[OK]", "FAIL": "[!!]", "WARN": "[~]"}


def print_report(checks: list[CheckResult], strict: bool) -> int:
    width = max(len(c.name) for c in checks)
    n_fail = n_warn = n_pass = 0
    for c in checks:
        marker = MARKERS.get(c.status, "[??]")
        print(f"  {marker} {c.name:<{width}}  {c.status:<4}  {c.detail}")
        if c.status == "FAIL":
            n_fail += 1
        elif c.status == "WARN":
            n_warn += 1
        elif c.status == "PASS":
            n_pass += 1
    print(f"\n{len(checks)} checks | {n_fail} FAIL | {n_warn} WARN | {n_pass} PASS")
    if n_fail:
        return 1
    if strict and n_warn:
        print("(strict mode: WARN treated as failure)")
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--session", required=True, type=Path,
                    help="In session mode: session artifact root "
                         "(sessions/<workload>/<iteration>/<agent-name>/). "
                         "In prep mode: iteration root "
                         "(sessions/<workload>/<iteration>/).")
    ap.add_argument("--mode", choices=("session", "prep"), default="session",
                    help="Which artifact tree to validate (default: session).")
    ap.add_argument("--strict", action="store_true",
                    help="Treat WARN as FAIL.")
    args = ap.parse_args()

    path: Path = args.session
    checks: list[CheckResult] = []

    if args.mode == "session":
        checks.extend(check_required_tree(path))
        checks.append(check_profiling_traces(path))
        checks.extend(check_results_schema(
            path / "artifacts" / "benchmarks" / "results.csv", mode="session"))
        checks.append(check_locked_hp_consistency(path))
        checks.extend(check_fillins(path))
    else:
        checks.extend(check_required_prep_tree(path))
        checks.extend(check_results_schema(
            path / "prep" / "prep_results.csv", mode="prep"))
        checks.extend(check_prep_invariants(path))
        # Card fillins: only the card matters in prep mode (FINAL_SUMMARY is session-side).
        checks.append(_placeholder_check("workload_card_filled",
                                         path / "WORKLOAD_CARD.md"))

    return print_report(checks, strict=args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
