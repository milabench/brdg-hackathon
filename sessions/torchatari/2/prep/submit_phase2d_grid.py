#!/usr/bin/env python3
"""Phase 2D — exhaustive Tier-2 grid search over all remaining HP combinations.

Full grid (update_epochs=4 fixed):
  num_envs        : {32, 64, 128, 256}
  num_steps       : {32, 64, 128}
  num_minibatches : {4, 8, 16, 32}
  → 4×3×4 = 48 configs total; 13 already have Tier-2 data → 35 new configs × 3 seeds = 105 jobs.

iter_time model: measured baseline at s=128 (e32→0.63s, e64→1.22s, e128→2.12s, e256→3.60s),
scaled linearly with num_steps, floored at 0.10 s.

stop      = ceil(900 / iter_time) + 20     (so stop × iter_time ≥ 900 s)
max_dur   = ceil((stop × iter_time × 1.45 + 120) / 60) × 60   [rounded up to minute]
sbatch_min = max_dur // 60 + 10
"""
import math, subprocess

REPO           = "/network/scratch/b/bouthilx/milabench/milabench"
BENCH_DIR      = f"{REPO}/benchmarks/retired/torchatari"
PREP_DIR       = f"{REPO}/brdg-hackathon/sessions/torchatari/2/prep"
MILABENCH_BASE = "/network/scratch/b/bouthilx/milabench/results"

# (e, s, m) combos already run at Tier-2 with u=4 — skip these
HAVE = {
    (128, 128,  4),   # Phase 2  baseline
    (256, 128,  4),   # Phase 2
    ( 32, 128,  4),   # Phase 2B
    ( 64, 128,  4),   # Phase 2B
    (128,  64,  4),   # Phase 2B
    (128, 128,  8),   # Phase 2B
    (256,  64,  4),   # Phase 2C
    (256,  64,  8),   # Phase 2C
    (256, 128,  8),   # Phase 2C
    (128,  64,  8),   # Phase 2C
    (128, 128, 16),   # Phase 2C
    ( 64,  64,  4),   # Phase 2C
    ( 64, 128,  8),   # Phase 2C
}

# Measured iter_time at s=128 from Phase 2B/2C
BASE_IT_S128 = {32: 0.63, 64: 1.22, 128: 2.12, 256: 3.60}

def iter_time_est(e, s):
    it128 = BASE_IT_S128.get(e, 0.02797 * (e ** 0.897))
    return max(it128 * s / 128, 0.10)

YAML_TEMPLATE = """\
torchatari:
  max_duration: {max_duration}
  inherits: _defaults
  definition: .
  install_variant: unpinned
  install_group: torch
  plan:
    method: per_gpu
  voir:
    options:
      stop: {stop}
      interval: "1s"
      skip: 5
  argv:
    --num-minibatches: {num_minibatches}
    --update-epochs: {update_epochs}
    --num-steps: {num_steps}
    --num-envs: {num_envs}
    --total-timesteps: 500000000
    --env-id: Breakout-v5
    --exp-name: {exp_name}
    --seed: {seed}
"""

SBATCH_TEMPLATE = """\
#!/bin/bash
#SBATCH --job-name=p2d-{label}-s{seed}
#SBATCH --partition=long
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=256G
#SBATCH --time=0:{sbatch_min}:00
#SBATCH --output={prep_dir}/p2d_t2_{label}_s{seed}.slurm-%j.out
#SBATCH --error={prep_dir}/p2d_t2_{label}_s{seed}.slurm-%j.err

set -uo pipefail
cd {repo}
export MILABENCH_BASE={milabench_base}

LOG={prep_dir}/p2d_t2_{label}_s{seed}.log
{{
  echo "=== [p2d_t2_{label}_s{seed} jobid=$SLURM_JOB_ID host=$(hostname) T=$(date -Is)] ==="
  uv run milabench run \\
    --config {bench_dir}/p2d_t2_{label}_s{seed}.yaml \\
    --select torchatari \\
    --base {milabench_base} \\
    --run-name "p2d_t2_{label}_s{seed}_${{SLURM_JOB_ID}}" 2>&1
  echo "exit=$?"
}} >> "$LOG" 2>&1
echo "Done: $LOG"
"""

configs = []
for e in [32, 64, 128, 256]:
    for s in [32, 64, 128]:
        for m in [4, 8, 16, 32]:
            if (e, s, m) in HAVE:
                continue
            mb    = (e * s) // m
            it    = iter_time_est(e, s)
            stop  = math.ceil(900 / it) + 20
            max_dur = math.ceil((stop * it * 1.45 + 120) / 60) * 60
            sbatch_min = max_dur // 60 + 10
            label = f"e{e}_s{s}_m{m}_u4"
            configs.append((label, e, s, m, 4, it, stop, max_dur, sbatch_min, mb))

print(f"── Phase 2D Tier-2 exhaustive grid ──")
print(f"{len(configs)} new configs × 3 seeds = {len(configs)*3} jobs  (13 configs already in HAVE, skipped)\n")
print(f"{'label':30s}  {'e':>4} {'s':>4} {'m':>3}  {'mb':>6}  {'it':>5}  {'stop':>6}  {'max_dur':>8}  sbatch")
print("-" * 95)
for cfg in configs:
    label, e, s, m, u, it, stop, max_dur, sbatch_min, mb = cfg
    print(f"  {label:30s}  {e:4d} {s:4d} {m:3d}  {mb:6d}  {it:5.2f}  {stop:6d}  {max_dur:7d}s  {sbatch_min}min")
print()

jobs = {}
for cfg in configs:
    label, e, s, m, u, it, stop, max_dur, sbatch_min, mb = cfg
    exp_name = label.replace("_", "")

    for seed in [1, 2, 3]:
        yaml_path   = f"{BENCH_DIR}/p2d_t2_{label}_s{seed}.yaml"
        sbatch_path = f"{PREP_DIR}/p2d_t2_{label}_s{seed}.sbatch"

        with open(yaml_path, "w") as f:
            f.write(YAML_TEMPLATE.format(
                max_duration=max_dur, stop=stop,
                num_envs=e, num_steps=s, num_minibatches=m, update_epochs=u,
                exp_name=exp_name, seed=seed,
            ))
        with open(sbatch_path, "w") as f:
            f.write(SBATCH_TEMPLATE.format(
                label=label, seed=seed, sbatch_min=sbatch_min,
                prep_dir=PREP_DIR, repo=REPO,
                bench_dir=BENCH_DIR, milabench_base=MILABENCH_BASE,
            ))

        result = subprocess.run(["sbatch", sbatch_path], capture_output=True, text=True)
        key = f"{label}_s{seed}"
        if result.returncode == 0:
            jid = result.stdout.strip().split()[-1]
            jobs[key] = jid
            print(f"  {label} seed={seed}  job {jid}")
        else:
            print(f"  {label} seed={seed}  FAILED: {result.stderr.strip()}")

print(f"\nSubmitted {len(jobs)}/{len(configs)*3} jobs.")
print("Job IDs:", " ".join(jobs.values()))
