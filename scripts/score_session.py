#!/usr/bin/env python3
"""Score a hackathon session's artifacts.

Consumes `results.csv` (schema: `playbook/SCHEMA.md` §1) and `event_log.md` (tags:
`playbook/RULES.md` §13.3 / milestones: `playbook/RULES.md` §14.3) from a single
session artifact root and produces:

- session_score.md    human-readable report (metrics, timeline, invariant checks)
- session_score.json  structured data for downstream consumption

Metrics reported:
  - session-quality counts and rates (experiments, wins, reverts, blocked, bugs,
    dead-end rate, human interventions by `H-*` tag)
  - `playbook/RULES.md` §14.2 checklist compliance (log completeness, per-box miss
    counts)
  - `playbook/RULES.md` §14.3 milestone timeline (time-to-first-baseline / profile /
    HPO-done / first-win, per-phase exit times, total duration)
  - `playbook/RULES.md` §14.3 invariant checks (SESSION-START present, exits unique,
    wins match results, PE2-after-BASELINE, WIN-after-PE3). Exits non-zero if any
    invariant FAILs.

Usage
-----
    python score_session.py --session path/to/sessions/<workload>/<iteration>/<agent-name>/ --out DIR
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd


# --- shared helpers (mirror plot_results.py / aggregate_sessions.py) -------

REQUIRED_COLUMNS = [
    "session_id", "experiment_id", "run_index", "timestamp", "tier", "phase",
    "candidate", "change", "baseline_ref", "commit_hash", "env_snapshot_id",
    "primary_metric", "quality_metric", "peak_gpu_mem_mib", "quality_verdict",
    "win_status", "logging_mode", "event_log_anchor", "notes",
    "gpu_util_avg", "cpu_util_avg", "compile_time_s", "hp_values_json",
]

TAG_LINE_RE = re.compile(r"^T\+(\S+)\s+\[([A-Z0-9\- ]+)\]")
T_OFFSET_RE = re.compile(r"(?:(?P<h>\d+)h)?(?:(?P<m>\d+)m)?(?:(?P<s>\d+)s)?")
CHECKLIST_RE = re.compile(
    r"Checklist:\s+ran\[([^\]]*)\]\s+logged\[([^\]]*)\]\s+csv\[([^\]]*)\]\s+"
    r"quality\[([^\]]*)\]\s+one-thing\[([^\]]*)\]\s+h-check\[([^\]]*)\]"
)

EXPERIMENT_TAGS = {"EXPERIMENT", "CHANGE", "REVERT", "FIX"}
UNFILLED_CONTENTS = {"", "_", "✗"}


@dataclass
class Event:
    t_minutes: float | None
    tag: str
    body_lines: list[str] = field(default_factory=list)


def parse_t_offset(raw: str) -> float | None:
    raw = raw.strip().rstrip(",").rstrip(".")
    if ":" in raw:
        try:
            parts = [int(p) for p in raw.split(":")]
        except ValueError:
            return None
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        if len(parts) == 3:
            return parts[0] * 60 + parts[1] + parts[2] / 60
        return None
    if raw.isdigit():
        return float(raw)
    m = T_OFFSET_RE.fullmatch(raw)
    if m and any(m.group(k) for k in ("h", "m", "s")):
        return (int(m.group("h") or 0) * 60
                + int(m.group("m") or 0)
                + int(m.group("s") or 0) / 60)
    return None


def load_results(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"{path}: results.csv missing required columns: {missing}")
    df = df[df["run_index"] >= 0].copy()
    return df


def parse_event_log(path: Path) -> list[Event]:
    """Return events with attached body lines (up to the next header or EOF)."""
    if not path.exists():
        return []
    events: list[Event] = []
    current: Event | None = None
    for raw_line in path.read_text().splitlines():
        m = TAG_LINE_RE.match(raw_line.strip())
        if m:
            if current is not None:
                events.append(current)
            current = Event(
                t_minutes=parse_t_offset(m.group(1)),
                tag=m.group(2).strip(),
            )
        elif current is not None:
            current.body_lines.append(raw_line)
    if current is not None:
        events.append(current)
    return events


def _first_tag_time(events: list[Event], tag: str) -> float | None:
    for e in events:
        if e.tag == tag and e.t_minutes is not None:
            return e.t_minutes
    return None


# --- metrics ---------------------------------------------------------------

def _checklist_compliance(events: list[Event]) -> dict:
    total = 0
    complete = 0
    box_names = ["ran", "logged", "csv", "quality", "one-thing", "h-check"]
    miss = {k: 0 for k in box_names}
    missing_line = 0
    for e in events:
        if e.tag not in EXPERIMENT_TAGS:
            continue
        total += 1
        blob = "\n".join(e.body_lines)
        m = CHECKLIST_RE.search(blob)
        if not m:
            missing_line += 1
            for k in box_names:
                miss[k] += 1
            continue
        boxes = list(m.groups())
        all_filled = True
        for name, content in zip(box_names, boxes):
            if content.strip() in UNFILLED_CONTENTS:
                miss[name] += 1
                all_filled = False
        if all_filled:
            complete += 1
    log_completeness = (complete / total) if total else None
    return {
        "n_experiment_entries": total,
        "n_complete_checklists": complete,
        "n_missing_checklist_line": missing_line,
        "log_completeness": log_completeness,
        "checklist_box_miss": miss,
    }


def compute_metrics(results: pd.DataFrame, events: list[Event]) -> dict:
    n_experiments = int(results["experiment_id"].nunique())
    full = results[results["tier"] == "full"]
    n_wins = int(full[full["win_status"] == "WIN"]["experiment_id"].nunique())

    n_reverts = sum(1 for e in events if e.tag == "REVERT")
    n_blocked = sum(1 for e in events if e.tag == "BLOCKED")
    n_bugs = sum(1 for e in events if e.tag == "BUG")
    dead_end_rate = ((n_reverts + n_blocked) / n_experiments
                     if n_experiments else None)

    interventions = {
        tag: sum(1 for e in events if e.tag == tag)
        for tag in ("H-STEER", "H-DEBUG", "H-ARCH", "H-OPS")
    }

    phase_exits = {N: _first_tag_time(events, f"PHASE-EXIT {N}")
                   for N in range(1, 5)}
    session_close = _first_tag_time(events, "SESSION-CLOSE")

    all_times = [e.t_minutes for e in events if e.t_minutes is not None]
    duration = max(all_times) if all_times else None

    out = {
        "n_experiments": n_experiments,
        "n_wins": n_wins,
        "n_reverts": n_reverts,
        "n_blocked": n_blocked,
        "n_bugs": n_bugs,
        "dead_end_rate": dead_end_rate,
        "interventions_by_tag": interventions,
        "total_interventions": sum(interventions.values()),
        "t_first_baseline_min": _first_tag_time(events, "BASELINE"),
        "t_first_profile_min": _first_tag_time(events, "PROFILE"),
        "t_hpo_done_min": phase_exits[2],
        "t_first_win_min": _first_tag_time(events, "WIN"),
        "phase_exits_min": phase_exits,
        "t_session_close_min": session_close,
        "session_duration_min": duration,
    }
    out.update(_checklist_compliance(events))
    return out


# --- invariants (RULES §14.3) ----------------------------------------------

def check_invariants(results: pd.DataFrame,
                     events: list[Event]) -> list[tuple[str, str, str]]:
    checks: list[tuple[str, str, str]] = []

    ss_events = [e for e in events if e.tag == "SESSION-START"]
    if len(ss_events) == 1:
        ss = ss_events[0]
        body = "\n".join(ss.body_lines)
        if re.search(r"(?mi)^\s*Hackathon repo:\s*\S+\s*@\s*\S+", body):
            checks.append(("session_start_unique", "PASS",
                           "exactly one [SESSION-START] with Hackathon repo line"))
        else:
            checks.append(("session_start_unique", "FAIL",
                           "[SESSION-START] missing 'Hackathon repo: <branch> @ "
                           "<commit>' line"))
    elif not ss_events:
        checks.append(("session_start_unique", "FAIL",
                       "missing [SESSION-START]"))
    else:
        checks.append(("session_start_unique", "FAIL",
                       f"{len(ss_events)} [SESSION-START] entries (expected 1)"))

    for N in range(1, 5):
        count = sum(1 for e in events if e.tag == f"PHASE-EXIT {N}")
        name = f"phase_exit_{N}_unique"
        if count == 1:
            checks.append((name, "PASS", f"exactly one [PHASE-EXIT {N}]"))
        elif count == 0:
            checks.append((name, "FAIL", f"missing [PHASE-EXIT {N}]"))
        else:
            checks.append((name, "FAIL",
                           f"{count} [PHASE-EXIT {N}] entries (expected 1)"))

    sc_count = sum(1 for e in events if e.tag == "SESSION-CLOSE")
    if sc_count == 1:
        checks.append(("session_close_unique", "PASS",
                       "exactly one [SESSION-CLOSE]"))
    elif sc_count == 0:
        checks.append(("session_close_unique", "FAIL",
                       "missing [SESSION-CLOSE]"))
    else:
        checks.append(("session_close_unique", "FAIL",
                       f"{sc_count} [SESSION-CLOSE] entries (expected 1)"))

    wins_in_results = int(results[
        (results["tier"] == "full")
        & (results["win_status"] == "WIN")
        & (results["quality_verdict"] == "PASS")
    ]["experiment_id"].nunique())
    win_events = sum(1 for e in events if e.tag == "WIN")
    if win_events == 0:
        checks.append(("wins_have_rows", "PASS", "no [WIN] events"))
    elif win_events == wins_in_results:
        checks.append(("wins_have_rows", "PASS",
                       f"{win_events} [WIN] event(s) match results rows"))
    else:
        checks.append(("wins_have_rows", "FAIL",
                       f"{win_events} [WIN] event(s) vs {wins_in_results} "
                       f"matching (tier=full, win_status=WIN, verdict=PASS) "
                       f"experiment(s)"))

    first_baseline = _first_tag_time(events, "BASELINE")
    first_pe2 = _first_tag_time(events, "PHASE-EXIT 2")
    if first_pe2 is None:
        checks.append(("pe2_after_baseline", "WARN",
                       "[PHASE-EXIT 2] missing (see phase_exit_2_unique)"))
    elif first_baseline is None:
        checks.append(("pe2_after_baseline", "FAIL",
                       "[PHASE-EXIT 2] emitted with no prior [BASELINE]"))
    elif first_baseline <= first_pe2:
        checks.append(("pe2_after_baseline", "PASS",
                       f"[BASELINE] T+{first_baseline:.1f}m ≤ "
                       f"[PHASE-EXIT 2] T+{first_pe2:.1f}m"))
    else:
        checks.append(("pe2_after_baseline", "FAIL",
                       f"[PHASE-EXIT 2] (T+{first_pe2:.1f}m) precedes "
                       f"[BASELINE] (T+{first_baseline:.1f}m)"))

    first_pe3 = _first_tag_time(events, "PHASE-EXIT 3")
    win_times = [e.t_minutes for e in events
                 if e.tag == "WIN" and e.t_minutes is not None]
    if not win_times:
        checks.append(("wins_after_pe3", "PASS", "no [WIN] events"))
    elif first_pe3 is None:
        checks.append(("wins_after_pe3", "FAIL",
                       f"{len(win_times)} [WIN] event(s) with no [PHASE-EXIT 3]"))
    else:
        early = [t for t in win_times if t < first_pe3]
        if not early:
            checks.append(("wins_after_pe3", "PASS",
                           f"all {len(win_times)} [WIN] event(s) after "
                           f"[PHASE-EXIT 3] T+{first_pe3:.1f}m"))
        else:
            checks.append(("wins_after_pe3", "FAIL",
                           f"{len(early)} [WIN] event(s) before [PHASE-EXIT 3] "
                           f"(T+{first_pe3:.1f}m)"))
    return checks


# --- output ----------------------------------------------------------------

def _fmt_min(x: float | None) -> str:
    return "—" if x is None else f"T+{x:.1f} min"


def _fmt_rate(x: float | None) -> str:
    return "—" if x is None else f"{x:.1%}"


MARKERS = {"PASS": "[OK]", "FAIL": "[!!]", "WARN": "[~]"}


def render_markdown(session_id: str, metrics: dict,
                    invariants: list[tuple[str, str, str]]) -> str:
    lines = [f"# Session score — {session_id}", ""]

    lines += ["## Session-quality metrics", "",
              f"- n_experiments: {metrics['n_experiments']}",
              f"- n_wins: {metrics['n_wins']}",
              f"- n_reverts: {metrics['n_reverts']}",
              f"- n_blocked: {metrics['n_blocked']}",
              f"- n_bugs: {metrics['n_bugs']}",
              f"- dead_end_rate: {_fmt_rate(metrics['dead_end_rate'])}",
              f"- total_interventions: {metrics['total_interventions']}"]
    for tag, n in metrics["interventions_by_tag"].items():
        lines.append(f"  - {tag}: {n}")
    lines.append("")

    lines += ["## Checklist compliance (RULES §14.2)", "",
              f"- experiment-like entries: {metrics['n_experiment_entries']}",
              f"- complete checklists: {metrics['n_complete_checklists']}",
              f"- entries missing checklist line entirely: "
              f"{metrics['n_missing_checklist_line']}",
              f"- log_completeness: {_fmt_rate(metrics['log_completeness'])}",
              "- per-box miss counts:"]
    for box, n in metrics["checklist_box_miss"].items():
        lines.append(f"  - {box}: {n}")
    lines.append("")

    lines += ["## Milestone timeline (RULES §14.3)", "",
              f"- time-to-first-baseline: {_fmt_min(metrics['t_first_baseline_min'])}",
              f"- time-to-first-profile: {_fmt_min(metrics['t_first_profile_min'])}",
              f"- time-to-HPO-done (PHASE-EXIT 2): {_fmt_min(metrics['t_hpo_done_min'])}",
              f"- time-to-first-win: {_fmt_min(metrics['t_first_win_min'])}"]
    for N in range(1, 5):
        lines.append(f"- PHASE-EXIT {N}: {_fmt_min(metrics['phase_exits_min'][N])}")
    lines.append(f"- SESSION-CLOSE: {_fmt_min(metrics['t_session_close_min'])}")
    lines.append(f"- session_duration: {_fmt_min(metrics['session_duration_min'])}")
    lines.append("")

    lines += ["## Invariant checks (RULES §14.3)", ""]
    for name, status, detail in invariants:
        marker = MARKERS.get(status, "[??]")
        lines.append(f"- {marker} `{name}` — {status}: {detail}")

    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--session", required=True, type=Path,
                    help="Session artifact root "
                         "(sessions/<workload>/<iteration>/<agent-name>/).")
    ap.add_argument("--out", required=True, type=Path,
                    help="Output directory for session_score.{md,json}.")
    args = ap.parse_args()

    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)

    results_path = args.session / "artifacts" / "benchmarks" / "results.csv"
    event_log_path = args.session / "artifacts" / "notes" / "event_log.md"
    results = load_results(results_path)
    events = parse_event_log(event_log_path)

    session_id = (str(results["session_id"].iloc[0]) if not results.empty
                  else args.session.name)

    metrics = compute_metrics(results, events)
    invariants = check_invariants(results, events)

    (out / "session_score.json").write_text(json.dumps(
        {
            "session_id": session_id,
            "metrics": metrics,
            "invariants": [{"name": n, "status": s, "detail": d}
                           for n, s, d in invariants],
        },
        indent=2, default=str,
    ))
    (out / "session_score.md").write_text(
        render_markdown(session_id, metrics, invariants)
    )

    # Concise stdout summary.
    n_fail = sum(1 for _, s, _ in invariants if s == "FAIL")
    n_warn = sum(1 for _, s, _ in invariants if s == "WARN")
    print(f"scored session: {session_id}")
    print(f"  wins={metrics['n_wins']}  experiments={metrics['n_experiments']}  "
          f"interventions={metrics['total_interventions']}  "
          f"log_completeness={_fmt_rate(metrics['log_completeness'])}")
    print(f"  invariants: {n_fail} FAIL, {n_warn} WARN, "
          f"{len(invariants) - n_fail - n_warn} PASS")
    print(f"  wrote {out / 'session_score.md'} and {out / 'session_score.json'}")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
