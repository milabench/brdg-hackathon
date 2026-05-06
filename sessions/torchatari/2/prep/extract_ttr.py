"""Extract TTR from Tier-2 baseline runs; compute target quality and Tier-2 baseline stats.

Usage:
    python3 extract_ttr.py [--target TARGET]

Without --target: prints end-of-window avg_episodic_return for each seed to determine target.
With --target: computes TTR for each run and prints Tier-2 baseline statistics.
"""
import sys, os, glob, argparse, statistics

REPO = "/network/scratch/b/bouthilx/milabench/milabench"
BENCH_DIR = f"{REPO}/benchmarks/retired/torchatari"
MILABENCH_BASE = "/network/scratch/b/bouthilx/milabench/results"
TTR_WINDOW_S = 900  # Tier-2 benchmark window

def find_tb_run_dirs(seed, job_kw=None):
    """Find TensorBoard run dirs for a given seed (and optionally job keyword)."""
    pattern = os.path.join(BENCH_DIR, "runs", f"Breakout-v5__main__{seed}__*")
    dirs = sorted(glob.glob(pattern))
    return dirs


def extract_events(run_dir):
    """Load avg_episodic_return events from a TensorBoard run dir."""
    venv_python = f"{MILABENCH_BASE}/venv/torch/bin/python"
    # Use the milabench venv's python to load tensorboard
    import subprocess, json, tempfile

    script = f"""
import sys
sys.path.insert(0, '{MILABENCH_BASE}/venv/torch/lib/python3.12/site-packages')
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
import json
ea = EventAccumulator('{run_dir}')
ea.Reload()
try:
    events = ea.Scalars('charts/avg_episodic_return')
    data = [(e.wall_time, e.value) for e in events]
except Exception as ex:
    data = []
print(json.dumps(data))
"""
    result = subprocess.run([venv_python, "-c", script],
                            capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [ERROR] {result.stderr.strip()}", file=sys.stderr)
        return []
    return json.loads(result.stdout.strip())


def get_ttr(events, target, window_s=TTR_WINDOW_S):
    """Return (ttr_s, end_quality) from event list [(wall_time, value)]."""
    if not events:
        return None, None
    t0 = events[0][0]
    within = [(t - t0, v) for t, v in events if t - t0 <= window_s]
    if not within:
        return None, None
    end_quality = within[-1][1]
    ttr = next((t for t, v in within if v >= target), None)
    return ttr, end_quality


def main():
    import json
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=float, default=None,
                        help="Quality target for TTR (if omitted, prints end-of-window values)")
    args = parser.parse_args()

    seeds = [1, 2, 3]
    seed_data = {}
    for seed in seeds:
        dirs = find_tb_run_dirs(seed)
        if not dirs:
            print(f"  seed={seed}: no TensorBoard run dir found under {BENCH_DIR}/runs/")
            continue
        # Use the most recent dir (highest timestamp)
        run_dir = dirs[-1]
        print(f"  seed={seed}: {os.path.basename(run_dir)}")
        events = extract_events(run_dir)
        if not events:
            print(f"    [no avg_episodic_return events]")
            continue
        t0 = events[0][0]
        within = [(t - t0, v) for t, v in events if t - t0 <= TTR_WINDOW_S]
        if within:
            end_t, end_q = within[-1]
            max_q = max(v for _, v in within)
            print(f"    Events within {TTR_WINDOW_S}s: n={len(within)}, "
                  f"end_time={end_t:.1f}s, end_quality={end_q:.3f}, max_quality={max_q:.3f}")
        seed_data[seed] = (run_dir, events)

    if not seed_data:
        print("No data found. Check that TTR jobs have completed.")
        return

    # Determine target quality
    if args.target is None:
        end_qualities = []
        for seed, (run_dir, events) in seed_data.items():
            t0 = events[0][0]
            within = [(t - t0, v) for t, v in events if t - t0 <= TTR_WINDOW_S]
            if within:
                end_qualities.append(within[-1][1])
        if end_qualities:
            mean_eq = statistics.mean(end_qualities)
            std_eq = statistics.stdev(end_qualities) if len(end_qualities) > 1 else 0
            print(f"\nEnd-of-window quality (N={len(end_qualities)}): "
                  f"mean={mean_eq:.3f}, std={std_eq:.3f}")
            print(f"Suggested target (Option A = mean): {mean_eq:.3f}")
            print(f"  Re-run with: python3 extract_ttr.py --target {mean_eq:.3f}")
        return

    # Compute TTR for each seed
    target = args.target
    print(f"\nTarget quality: {target:.3f}")
    ttrs = []
    for seed, (run_dir, events) in seed_data.items():
        ttr, end_q = get_ttr(events, target)
        if ttr is not None:
            print(f"  seed={seed}: TTR={ttr:.1f}s  end_quality={end_q:.3f}")
            ttrs.append(ttr)
        else:
            print(f"  seed={seed}: DNF (target not reached in {TTR_WINDOW_S}s)  end_quality={end_q}")
            ttrs.append(TTR_WINDOW_S)  # DNF = full window

    if ttrs:
        med = statistics.median(ttrs)
        mn, mx = min(ttrs), max(ttrs)
        cv = 100 * statistics.stdev(ttrs) / statistics.mean(ttrs) if len(ttrs) > 1 else float('nan')
        print(f"\nTier-2 baseline (N={len(ttrs)}, target={target:.3f}):")
        print(f"  TTR median = {med:.1f}s,  range = [{mn:.1f}, {mx:.1f}s],  CV = {cv:.1f}%")


if __name__ == "__main__":
    main()
