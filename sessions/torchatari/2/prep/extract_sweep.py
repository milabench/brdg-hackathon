"""Extract voir rate from milabench JSONL data files; print ranked table.

Usage:
    python3 extract_sweep.py
"""
import json, os, statistics, glob

MILABENCH_BASE = "/network/scratch/b/bouthilx/milabench/results"
PREP_DIR = "/network/scratch/b/bouthilx/milabench/milabench/brdg-hackathon/sessions/torchatari/2/prep"

# label → (job_id, run_prefix, num_envs, num_steps, num_minibatches, update_epochs)
# run_prefix: "prep2_sweep" for original, "prep2r_sweep" for reruns
CANDIDATES = {
    "e64_s128_m4_u4":   ("9464142", "prep2_sweep",  64, 128,  4, 4),
    "e128_s128_m4_u4":  ("9464143", "prep2_sweep", 128, 128,  4, 4),  # default
    "e256_s128_m4_u4":  ("9466516", "prep2r_sweep", 256, 128,  4, 4),
    "e512_s128_m4_u4":  ("9466517", "prep2r_sweep", 512, 128,  4, 4),
    "e128_s64_m4_u4":   ("9464146", "prep2_sweep", 128,  64,  4, 4),
    "e128_s256_m4_u4":  ("9466518", "prep2r_sweep", 128, 256,  4, 4),
    "e128_s512_m4_u4":  ("9466519", "prep2r_sweep", 128, 512,  4, 4),
    "e128_s128_m2_u4":  ("9464149", "prep2_sweep", 128, 128,  2, 4),
    "e128_s128_m8_u4":  ("9464150", "prep2_sweep", 128, 128,  8, 4),
    "e128_s128_m16_u4": ("9464151", "prep2_sweep", 128, 128, 16, 4),
    "e128_s128_m4_u1":  ("9464152", "prep2_sweep", 128, 128,  4, 1),
    "e128_s128_m4_u2":  ("9464153", "prep2_sweep", 128, 128,  4, 2),
    "e128_s128_m4_u8":  ("9464154", "prep2_sweep", 128, 128,  4, 8),
    "e256_s256_m8_u4":  ("9466520", "prep2r_sweep", 256, 256,  8, 4),
    "e512_s256_m8_u4":  ("9466521", "prep2r_sweep", 512, 256,  8, 4),
    "e256_s128_m2_u4":  ("9466522", "prep2r_sweep", 256, 128,  2, 4),
    "e512_s128_m2_u4":  ("9466523", "prep2r_sweep", 512, 128,  2, 4),
    "e256_s128_m4_u8":  ("9466524", "prep2r_sweep", 256, 128,  4, 8),
    "e128_s256_m4_u8":  ("9466525", "prep2r_sweep", 128, 256,  4, 8),
    "e512_s128_m4_u8":  ("9466526", "prep2r_sweep", 512, 128,  4, 8),
}

SHORT_BASELINES = {
    "s2": "9464174",
    "s3": "9464175",
}


def extract_from_data_file(data_path, skip=5):
    """Return (median_rate, n_usable, n_total, complete) from a milabench .data JSONL file."""
    if not os.path.exists(data_path):
        return None, 0, 0, False
    rates = []
    complete = False
    with open(data_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("event") == "data":
                d = obj.get("data", {})
                if d.get("task") == "train" and "rate" in d:
                    rates.append(float(d["rate"]))
            elif obj.get("event") == "end":
                complete = True
    n_total = len(rates)
    usable = rates[skip:]
    if not usable:
        return None, 0, n_total, complete
    return statistics.median(usable), len(usable), n_total, complete


def cv_pct(values):
    if len(values) < 2:
        return float('nan')
    return 100 * statistics.stdev(values) / statistics.mean(values)


print("=" * 95)
print(f"{'label':25s}  {'envs':>4} {'steps':>5} {'mb':>3} {'ep':>3}  "
      f"{'median_rate':>12} {'n_obs':>6} {'status':>12}")
print("=" * 95)

results = {}
for label, (jid, prefix, envs, steps, mb, ep) in CANDIDATES.items():
    run_name = f"{prefix}_{label}_{jid}"
    data_path = f"{MILABENCH_BASE}/runs/{run_name}/torchatari.D0.data"
    median, n_usable, n_total, complete = extract_from_data_file(data_path)
    status = "done" if complete else (f"running({n_total})" if n_total > 0 else "pending")
    rate_str = f"{median:12.1f}" if median is not None else f"{'N/A':>12}"
    flag = " *" if label == "e128_s128_m4_u4" else "  "
    print(f"{flag}{label:25s}  {envs:4d} {steps:5d} {mb:3d} {ep:3d}  {rate_str} {n_usable:6d} {status:>12}")
    if median is not None:
        results[label] = {"rate": median, "n": n_usable, "envs": envs, "steps": steps}

# Short-run baseline replicates
print()
print("── Short-run baseline replicates ──")
baseline_rates = [("sanity_s1", 7722.1)]  # seed=1 from Phase 1

for seed_label, jid in SHORT_BASELINES.items():
    run_name = f"prep2_short_baseline_{seed_label}_{jid}"
    data_path = f"{MILABENCH_BASE}/runs/{run_name}/torchatari.D0.data"
    median, n_usable, n_total, complete = extract_from_data_file(data_path)
    status = "done" if complete else (f"running({n_total})" if n_total > 0 else "pending")
    rate_str = f"{median:.1f}" if median is not None else "N/A"
    print(f"  short_baseline_{seed_label}: {rate_str}  n={n_usable}  {status}")
    if median is not None:
        baseline_rates.append((f"short_{seed_label}", median))

# Also include sweep default replicate
if "e128_s128_m4_u4" in results:
    baseline_rates.append(("sweep_default_s1", results["e128_s128_m4_u4"]["rate"]))

if len(baseline_rates) >= 1:
    vals = [r[1] for r in baseline_rates]
    print(f"\nTier-1 baseline (N={len(vals)}): "
          f"median={statistics.median(vals):.1f}  mean={statistics.mean(vals):.1f}  "
          f"CV={cv_pct(vals):.1f}%")
    print("  Individual rates:", ", ".join(f"{name}={v:.1f}" for name, v in baseline_rates))

# Ranked results
if results:
    default = results.get("e128_s128_m4_u4", {}).get("rate")
    print()
    print("── Ranked by median rate (vs default *) ──")
    ranked = sorted(results.items(), key=lambda x: x[1]["rate"], reverse=True)
    for rank, (label, info) in enumerate(ranked, 1):
        rate = info["rate"]
        delta = "" if default is None else f"  ({(rate/default-1)*100:+.1f}%)"
        flag = " *" if label == "e128_s128_m4_u4" else "  "
        print(f"{flag}{rank:2d}. {label:25s}  {rate:8.1f} items/s{delta}  n={info['n']}")
    print("\n(* = default baseline)")
