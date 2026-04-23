#!/usr/bin/env python3
"""Aggregate results across multiple hackathon sessions into a comparison table.

Consumes per-session artifacts — `results.csv` (schema: `playbook/SCHEMA.md` §1) and
`event_log.md` (tags: `playbook/RULES.md` §13.3 / milestones:
`playbook/RULES.md` §14.3); `FINAL_SUMMARY.md` only checked for existence — and
produces:

- aggregated.csv  one row per session with comparable columns
- aggregated.md   markdown rendering of the same data, sorted by `improvement_pct`

Usage
-----
    python aggregate_sessions.py --session DIR [--session DIR ...] --out DIR

Each `DIR` is a session artifact root
(`sessions/<workload>/<iteration>/<agent-name>/`).
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


# --- shared helpers (mirror plot_results.py) -------------------------------

REQUIRED_COLUMNS = [
    "session_id", "experiment_id", "run_index", "timestamp", "tier", "phase",
    "candidate", "change", "baseline_ref", "commit_hash", "env_snapshot_id",
    "primary_metric", "quality_metric", "peak_gpu_mem_mib", "quality_verdict",
    "win_status", "logging_mode", "event_log_anchor", "notes",
    "gpu_util_avg", "cpu_util_avg", "compile_time_s", "hp_values_json",
]

TAG_LINE_RE = re.compile(r"^T\+(\S+)\s+\[([A-Z0-9\- ]+)\]")
T_OFFSET_RE = re.compile(r"(?:(?P<h>\d+)h)?(?:(?P<m>\d+)m)?(?:(?P<s>\d+)s)?")


@dataclass
class Event:
    t_minutes: float
    tag: str


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
    if not path.exists():
        return []
    events: list[Event] = []
    for line in path.read_text().splitlines():
        m = TAG_LINE_RE.match(line.strip())
        if not m:
            continue
        t = parse_t_offset(m.group(1))
        if t is None:
            continue
        events.append(Event(t_minutes=t, tag=m.group(2).strip()))
    return events


# --- aggregation -----------------------------------------------------------

def _first_tag_time(events: list[Event], tag: str) -> float | None:
    for e in events:
        if e.tag == tag:
            return e.t_minutes
    return None


def _best_full_candidate(full: pd.DataFrame) -> tuple[str | None, float | None]:
    wins = full[full["win_status"] == "WIN"]
    if wins.empty:
        return None, None
    per_exp = (wins.groupby(["experiment_id", "candidate"])["primary_metric"]
               .median().reset_index()
               .sort_values("primary_metric", ascending=False))
    top = per_exp.iloc[0]
    return str(top["candidate"]), float(top["primary_metric"])


def aggregate_session(session_dir: Path) -> dict:
    results = load_results(session_dir / "artifacts" / "benchmarks" / "results.csv")
    events = parse_event_log(session_dir / "artifacts" / "notes" / "event_log.md")
    final_summary_exists = (session_dir / "artifacts" / "FINAL_SUMMARY.md").exists()

    session_id = (str(results["session_id"].iloc[0]) if not results.empty
                  else session_dir.name)
    agent_id = session_id.split("_", 1)[1] if "_" in session_id else session_id

    full = results[results["tier"] == "full"]
    baseline_full = full[full["candidate"] == "baseline"]
    if baseline_full.empty:
        baseline_median: float | None = None
    else:
        baseline_median = float(
            baseline_full.groupby("experiment_id")["primary_metric"].median().median()
        )

    best_candidate, best_median = _best_full_candidate(full)
    improvement_pct: float | None = None
    if baseline_median is not None and best_median is not None and baseline_median > 0:
        improvement_pct = (best_median - baseline_median) / baseline_median * 100.0

    n_wins = int(full[full["win_status"] == "WIN"]["experiment_id"].nunique())
    n_experiments = int(results["experiment_id"].nunique())
    n_reverts = sum(1 for e in events if e.tag == "REVERT")

    return {
        "session_id": session_id,
        "agent_id": agent_id,
        "baseline_primary_median": baseline_median,
        "best_primary_median": best_median,
        "improvement_pct": improvement_pct,
        "best_candidate": best_candidate,
        "n_wins": n_wins,
        "n_experiments": n_experiments,
        "n_reverts": n_reverts,
        "h_steer": sum(1 for e in events if e.tag == "H-STEER"),
        "h_debug": sum(1 for e in events if e.tag == "H-DEBUG"),
        "h_arch": sum(1 for e in events if e.tag == "H-ARCH"),
        "h_ops": sum(1 for e in events if e.tag == "H-OPS"),
        "t_first_baseline_min": _first_tag_time(events, "BASELINE"),
        "t_first_profile_min": _first_tag_time(events, "PROFILE"),
        "t_baseline_adopted_min": _first_tag_time(events, "PHASE-EXIT 2"),
        "t_first_win_min": _first_tag_time(events, "WIN"),
        "duration_min": max((e.t_minutes for e in events), default=None),
        "final_summary": final_summary_exists,
    }


# --- output ---------------------------------------------------------------

MD_COLUMN_ORDER = [
    "session_id", "agent_id", "baseline_primary_median", "best_primary_median",
    "improvement_pct", "best_candidate", "n_wins", "n_experiments", "n_reverts",
    "h_steer", "h_debug", "h_arch", "h_ops",
    "t_first_baseline_min", "t_first_profile_min", "t_baseline_adopted_min",
    "t_first_win_min", "duration_min", "final_summary",
]


def _to_markdown(df: pd.DataFrame) -> str:
    cols = [c for c in MD_COLUMN_ORDER if c in df.columns]
    lines = ["| " + " | ".join(cols) + " |",
             "| " + " | ".join("---" for _ in cols) + " |"]
    for _, row in df.iterrows():
        cells = []
        for c in cols:
            v = row[c]
            if pd.isna(v):
                cells.append("")
            elif isinstance(v, float):
                cells.append(f"{v:.3g}")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def write_outputs(rows: list[dict], out: Path) -> None:
    df = pd.DataFrame(rows)
    if "improvement_pct" in df.columns:
        df = df.sort_values("improvement_pct", ascending=False, na_position="last")
    df.to_csv(out / "aggregated.csv", index=False)
    (out / "aggregated.md").write_text(
        "# Aggregated session comparison\n\n" + _to_markdown(df) + "\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--session", action="append", required=True,
                    help="Session artifact root "
                         "(<workload>/<iteration>/<agent-name>/). Repeatable.")
    ap.add_argument("--out", required=True, type=Path,
                    help="Output directory for aggregated.csv and aggregated.md.")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    rows = [aggregate_session(Path(s)) for s in args.session]
    write_outputs(rows, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
