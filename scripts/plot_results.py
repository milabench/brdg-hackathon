#!/usr/bin/env python3
"""Standard plots for hackathon session artifacts.

Consumes `artifacts/benchmarks/results.csv` (schema: `SCHEMA.md` §1) and
`artifacts/notes/event_log.md` (tags: `RULES.md` §13.3 / milestones: `RULES.md` §14.3)
and produces:

1. throughput_distribution_<tier>.png  primary-metric distribution per candidate
2. pareto.png                          quality vs primary-metric scatter (win_status coded)
3. best_so_far.png                     best primary-metric so far over wall-clock time
4. session_timeline.png                per-session timeline with milestone + overlay tags

Multi-session mode (pass `--session` more than once) overlays the session timeline.

Usage
-----
Single session:
    python plot_results.py --session path/to/<workload>/<iteration>/<agent-name>/ --out path/to/out/

Multi-session overlay:
    python plot_results.py --session path/to/<workload>/<iteration>/alice \\
                           --session path/to/<workload>/<iteration>/bob \\
                           --out path/to/out/
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


REQUIRED_COLUMNS = [
    "session_id", "experiment_id", "run_index", "timestamp", "tier", "phase",
    "candidate", "change", "baseline_ref", "commit_hash", "env_snapshot_id",
    "primary_metric", "quality_metric", "peak_gpu_mem_mib", "quality_verdict",
    "win_status", "logging_mode", "event_log_anchor", "notes",
    "gpu_util_avg", "cpu_util_avg", "compile_time_s", "hp_values_json",
]

PHASE_EXIT_RE = re.compile(r"^PHASE-EXIT\s+(\d+)$")
TAG_LINE_RE = re.compile(r"^T\+(\S+)\s+\[([A-Z0-9\- ]+)\]")
T_OFFSET_RE = re.compile(r"(?:(?P<h>\d+)h)?(?:(?P<m>\d+)m)?(?:(?P<s>\d+)s)?")


@dataclass
class Event:
    session_id: str
    t_minutes: float
    tag: str


def parse_t_offset(raw: str) -> float | None:
    """Parse a `T+<offset>` tail into minutes. Returns None if unparseable.

    Accepts `1:30` (h:m), `1:30:00` (h:m:s), `1h30m`, `45m`, `90s`, `90`.
    """
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
        h = int(m.group("h") or 0)
        mm = int(m.group("m") or 0)
        ss = int(m.group("s") or 0)
        return h * 60 + mm + ss / 60
    return None


def load_results(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"{path}: results.csv missing required columns: {missing}")
    # Drop warmup (run_index == -1) from statistical plots.
    df = df[df["run_index"] >= 0].copy()
    return df


def parse_event_log(path: Path, session_id: str) -> list[Event]:
    if not path.exists():
        return []
    events: list[Event] = []
    for raw_line in path.read_text().splitlines():
        m = TAG_LINE_RE.match(raw_line.strip())
        if not m:
            continue
        offset_raw, tag = m.group(1), m.group(2).strip()
        t_min = parse_t_offset(offset_raw)
        if t_min is None:
            continue
        events.append(Event(session_id=session_id, t_minutes=t_min, tag=tag))
    return events


def _anchor_map(results: pd.DataFrame) -> dict[str, float]:
    """Map experiment_id -> T+ minutes parsed from `event_log_anchor`."""
    anchors: dict[str, float] = {}
    for _, row in results.iterrows():
        raw = str(row.get("event_log_anchor") or "")
        if raw.startswith("T+"):
            raw = raw[2:]
        t = parse_t_offset(raw)
        if t is not None:
            anchors.setdefault(str(row["experiment_id"]), t)
    return anchors


def plot_throughput_distribution(results: pd.DataFrame, out: Path) -> None:
    for tier in sorted(results["tier"].dropna().unique()):
        sub = results[results["tier"] == tier]
        candidates = list(sub["candidate"].unique())
        if not candidates:
            continue
        data = [sub[sub["candidate"] == c]["primary_metric"].dropna().to_numpy()
                for c in candidates]
        fig, ax = plt.subplots(figsize=(max(6.0, 0.6 * len(candidates)), 4))
        ax.boxplot(data, labels=candidates, vert=True, showmeans=True)
        ax.set_ylabel("primary_metric")
        ax.set_title(f"Throughput distribution per candidate (tier={tier})")
        ax.tick_params(axis="x", rotation=30)
        fig.tight_layout()
        fig.savefig(out / f"throughput_distribution_{tier}.png", dpi=120)
        plt.close(fig)


def plot_pareto(results: pd.DataFrame, out: Path) -> None:
    sub = results.dropna(subset=["quality_metric", "primary_metric"])
    if sub.empty:
        return
    agg = (
        sub.groupby(["candidate", "tier"], as_index=False)
        .agg(primary_metric=("primary_metric", "median"),
             quality_metric=("quality_metric", "median"),
             win_status=("win_status", "first"))
    )
    fig, ax = plt.subplots(figsize=(7, 5))
    status_color = {"WIN": "C2", "INVALIDATED": "C3", "FAIL": "C1"}
    tier_marker = {"short": "o", "full": "s"}
    seen_tiers = set()
    for _, row in agg.iterrows():
        marker = tier_marker.get(row["tier"], "^")
        color = status_color.get(row["win_status"], "C0")
        label = f"tier={row['tier']}" if row["tier"] not in seen_tiers else None
        ax.scatter(row["primary_metric"], row["quality_metric"],
                   marker=marker, c=color, s=60, label=label)
        seen_tiers.add(row["tier"])
        ax.annotate(row["candidate"],
                    (row["primary_metric"], row["quality_metric"]),
                    fontsize=8, xytext=(3, 3), textcoords="offset points")
    ax.set_xlabel("primary_metric (median)")
    ax.set_ylabel("quality_metric (median)")
    ax.set_title("Quality vs primary-metric Pareto")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "pareto.png", dpi=120)
    plt.close(fig)


def plot_best_so_far(results: pd.DataFrame, out: Path,
                     anchors: dict[str, float]) -> None:
    use_time = bool(anchors)
    fig, ax = plt.subplots(figsize=(8, 4))
    plotted_any = False
    for tier in ("short", "full"):
        sub = results[results["tier"] == tier]
        if sub.empty:
            continue
        medians = (sub.groupby("experiment_id", sort=False)["primary_metric"]
                   .median())
        exp_ids = [str(i) for i in medians.index.tolist()]

        if use_time:
            pairs = [(anchors[eid], v)
                     for eid, v in zip(exp_ids, medians.to_numpy())
                     if eid in anchors]
            if not pairs:
                continue
            pairs.sort()
            xs = [p[0] for p in pairs]
            vs = [p[1] for p in pairs]
        else:
            xs = list(range(len(exp_ids)))
            vs = list(medians.to_numpy())

        best = []
        current = -float("inf")
        for v in vs:
            current = max(current, v)
            best.append(current)
        ax.plot(xs, best, marker="o", label=f"tier={tier}")
        plotted_any = True

    if not plotted_any:
        plt.close(fig)
        return
    ax.set_xlabel("wall-clock (minutes since session start)" if use_time
                  else "experiment index")
    ax.set_ylabel("best primary_metric so far")
    ax.set_title("Best-so-far timeline")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "best_so_far.png", dpi=120)
    plt.close(fig)


def _tag_style(tag: str) -> dict:
    if PHASE_EXIT_RE.match(tag):
        return {"marker": "^", "color": "C3", "size": 90, "label": True}
    if tag == "SESSION-CLOSE":
        return {"marker": "s", "color": "C3", "size": 90, "label": True}
    if tag == "WIN":
        return {"marker": "*", "color": "C2", "size": 140, "label": True}
    if tag == "BASELINE":
        return {"marker": "o", "color": "C0", "size": 60, "label": True}
    if tag == "PROFILE":
        return {"marker": "D", "color": "C4", "size": 50, "label": True}
    if tag.startswith("H-"):
        return {"marker": "x", "color": "C7", "size": 50, "label": False}
    if tag in ("BUG", "REVERT", "BLOCKED"):
        return {"marker": "v", "color": "C1", "size": 50, "label": False}
    if tag in ("DRIFT", "NOISE", "AUDIT"):
        return {"marker": ".", "color": "C6", "size": 20, "label": False}
    return {"marker": ".", "color": "#888888", "size": 15, "label": False}


def plot_session_timeline(events_by_session: dict[str, list[Event]],
                          out: Path) -> None:
    if not events_by_session:
        return
    session_ids = list(events_by_session.keys())
    fig, ax = plt.subplots(figsize=(10, 1.2 + 0.6 * len(session_ids)))
    for i, sid in enumerate(session_ids):
        events = events_by_session[sid]
        t_max = max((e.t_minutes for e in events), default=1.0)
        ax.hlines(i, 0, t_max, colors="#cccccc", linewidths=1)
        for e in events:
            s = _tag_style(e.tag)
            ax.scatter([e.t_minutes], [i], marker=s["marker"], c=s["color"],
                       s=s["size"], zorder=3)
            if s["label"]:
                ax.annotate(e.tag, (e.t_minutes, i), fontsize=7,
                            xytext=(3, 6), textcoords="offset points")
    ax.set_yticks(list(range(len(session_ids))))
    ax.set_yticklabels(session_ids)
    ax.set_xlabel("wall-clock (minutes since session start)")
    ax.set_title("Session timeline")
    fig.tight_layout()
    fig.savefig(out / "session_timeline.png", dpi=120)
    plt.close(fig)


def process_session(session_dir: Path, out: Path, multi_session: bool
                    ) -> tuple[pd.DataFrame, str, list[Event]]:
    results_path = session_dir / "artifacts" / "benchmarks" / "results.csv"
    event_log_path = session_dir / "artifacts" / "notes" / "event_log.md"
    results = load_results(results_path)
    session_id = (str(results["session_id"].iloc[0])
                  if not results.empty else session_dir.name)
    events = parse_event_log(event_log_path, session_id)

    if not multi_session:
        plot_throughput_distribution(results, out)
        plot_pareto(results, out)
        plot_best_so_far(results, out, _anchor_map(results))

    return results, session_id, events


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--session", action="append", required=True,
                    help="Session artifact root "
                         "(<workload>/<iteration>/<agent-name>/). "
                         "Repeatable for multi-agent overlay.")
    ap.add_argument("--out", required=True, type=Path,
                    help="Output directory for generated PNGs.")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    sessions = [Path(s) for s in args.session]
    multi = len(sessions) > 1

    events_by_session: dict[str, list[Event]] = {}
    for sdir in sessions:
        _, sid, events = process_session(sdir, out, multi_session=multi)
        events_by_session.setdefault(sid, []).extend(events)

    plot_session_timeline(events_by_session, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
