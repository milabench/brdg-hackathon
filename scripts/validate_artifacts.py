#!/usr/bin/env python3
"""Validate a hackathon session's artifact tree before declaring done.

Checks that the artifact layout and `results.csv` schema meet the contract defined in
`playbook/RULES.md` §5 (preflight), §12 (profiling), `playbook/SCHEMA.md` §1 (CSV
schema), and `playbook/EXECUTION.md` §6.3 (required folder structure).

The `--session` argument points at the **session artifact root**
(`sessions/<workload>/<iteration>/<agent-name>/`). `WORKLOAD_CARD.md` is expected one
level up at `sessions/<workload>/<iteration>/WORKLOAD_CARD.md` (shared across
operators).

Usage
-----
    python validate_artifacts.py --session path/to/sessions/<workload>/<iteration>/<agent-name>/
    python validate_artifacts.py --session PATH --strict   # treat WARN as FAIL

Exits 0 on success, 1 if any FAIL occurs (or any WARN in `--strict` mode).
"""
from __future__ import annotations

import argparse
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
WIN_STATUSES = {"NA", "EXPERIMENT", "WIN", "INVALIDATED"}


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


def check_results_schema(session: Path) -> list[CheckResult]:
    results_csv = session / "artifacts" / "benchmarks" / "results.csv"
    df, err = _load_results_or_none(results_csv)
    if err is not None:
        return [err]
    assert df is not None

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
                                  "results.csv has no rows"))
        return checks
    checks.append(CheckResult("results_nonempty", "PASS", f"{len(df)} rows"))

    # Baseline recorded at tier=full.
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

    # Enum values.
    bad_verdict = set(df["quality_verdict"].dropna().astype(str).unique()) - QUALITY_VERDICTS
    if bad_verdict:
        checks.append(CheckResult("quality_verdict_enum", "FAIL",
                                  f"unexpected values: {sorted(bad_verdict)}"))
    else:
        checks.append(CheckResult("quality_verdict_enum", "PASS", ""))
    bad_win = set(df["win_status"].dropna().astype(str).unique()) - WIN_STATUSES
    if bad_win:
        checks.append(CheckResult("win_status_enum", "FAIL",
                                  f"unexpected values: {sorted(bad_win)}"))
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
                    help="Session artifact root "
                         "(sessions/<workload>/<iteration>/<agent-name>/).")
    ap.add_argument("--strict", action="store_true",
                    help="Treat WARN as FAIL.")
    args = ap.parse_args()

    session: Path = args.session
    checks: list[CheckResult] = []
    checks.extend(check_required_tree(session))
    checks.append(check_profiling_traces(session))
    checks.extend(check_results_schema(session))
    checks.extend(check_fillins(session))

    return print_report(checks, strict=args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
