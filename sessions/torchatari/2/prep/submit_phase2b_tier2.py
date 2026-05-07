#!/usr/bin/env python3
"""Phase 2B — extended Tier-2 TTR validation.

11 new HP configs × 3 seeds = 33 new full-length jobs.

Group A — num_envs sweep (s=128, m=4, u=4):
  e16, e32, e48, e64, e96, e192, e512   (have e128 and e256 from Phase 2)

Group B — non-envs HP validation (e=128, s=128):
  s64   (half steps  → faster iterations → more PPO updates/sec)
  s256  (double steps → slower iterations → fewer PPO updates/sec)
  m8    (top Tier-1 non-envs winner, +2.7%)
  u1    (highest Tier-1 overall excluding envs, +4.5%; but 1 epoch only)

Each config: voir stop calibrated so stop × iter_time ≥ 900 s (covers TTR window).
max_duration = ceil(stop × iter_time × 1.45 + 120), rounded to nearest minute.
"""
import os, math, subprocess

REPO           = "/network/scratch/b/bouthilx/milabench/milabench"
BENCH_DIR      = f"{REPO}/benchmarks/retired/torchatari"
PREP_DIR       = f"{REPO}/brdg-hackathon/sessions/torchatari/2/prep"
MILABENCH_BASE = "/network/scratch/b/bouthilx/milabench/results"

# (label, num_envs, num_steps, num_minibatches, update_epochs,
#   iter_time_est_s, t2_stop, max_duration_s, sbatch_min)
CONFIGS = [
    # Group A — num_envs sweep
    # iter_time estimated from power-law fit: 0.02797 * e^0.897
    ("e16_s128_m4_u4",    16, 128, 4, 4,  0.34, 2699, 1440, 34),
    ("e32_s128_m4_u4",    32, 128, 4, 4,  0.63, 1460, 1500, 35),
    ("e48_s128_m4_u4",    48, 128, 4, 4,  0.90, 1021, 1500, 35),
    ("e64_s128_m4_u4",    64, 128, 4, 4,  1.22,  757, 1500, 35),
    ("e96_s128_m4_u4",    96, 128, 4, 4,  1.67,  558, 1500, 35),
    ("e192_s128_m4_u4",  192, 128, 4, 4,  3.12,  309, 1560, 36),
    ("e512_s128_m4_u4",  512, 128, 4, 4,  7.51,  140, 1680, 38),
    # Group B — non-envs HPs
    # iter_time from measured Tier-1 rates
    ("e128_s64_m4_u4",   128,  64, 4, 4,  1.09,  849, 1500, 35),
    ("e128_s256_m4_u4",  128, 256, 4, 4,  4.20,  235, 1560, 36),
    ("e128_s128_m8_u4",  128, 128, 8, 4,  2.07,  456, 1500, 35),
    ("e128_s128_m4_u1",  128, 128, 4, 1,  2.03,  464, 1500, 35),
]

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
#SBATCH --job-name=p2b-t2-{label}-s{seed}
#SBATCH --partition=long
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=256G
#SBATCH --time=0:{sbatch_min}:00
#SBATCH --output={prep_dir}/p2b_t2_{label}_s{seed}.slurm-%j.out
#SBATCH --error={prep_dir}/p2b_t2_{label}_s{seed}.slurm-%j.err

set -uo pipefail
cd {repo}
export MILABENCH_BASE={milabench_base}

LOG={prep_dir}/p2b_t2_{label}_s{seed}.log
{{
  echo "=== [p2b_t2_{label}_s{seed} jobid=$SLURM_JOB_ID host=$(hostname) T=$(date -Is)] ==="
  uv run milabench run \\
    --config {bench_dir}/p2b_t2_{label}_s{seed}.yaml \\
    --select torchatari \\
    --base {milabench_base} \\
    --run-name "p2b_t2_{label}_s{seed}_${{SLURM_JOB_ID}}" 2>&1
  echo "exit=$?"
}} >> "$LOG" 2>&1
echo "Done: $LOG"
"""

jobs = {}
total = len(CONFIGS) * 3

print("── Phase 2B Tier-2 extended TTR validation ──")
print(f"{'label':30s}  {'e':>4} {'s':>4} {'m':>3} {'u':>3}  {'stop':>6} {'max_dur':>8} {'sbatch':>7}")
print("-" * 75)
for cfg in CONFIGS:
    label, e, s, m, u, it, stop, max_dur, sbatch_min = cfg
    print(f"  {label:30s}  {e:4d} {s:4d} {m:3d} {u:3d}  {stop:6d} {max_dur:7d}s  {sbatch_min:5d}min")
print(f"\nTotal: {len(CONFIGS)} configs × 3 seeds = {total} jobs\n")

for cfg in CONFIGS:
    label, e, s, m, u, it, stop, max_dur, sbatch_min = cfg
    exp_name = label.replace("_", "")  # compact name for TB dir

    for seed in [1, 2, 3]:
        yaml_path   = f"{BENCH_DIR}/p2b_t2_{label}_s{seed}.yaml"
        sbatch_path = f"{PREP_DIR}/p2b_t2_{label}_s{seed}.sbatch"

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

print(f"\nSubmitted {len(jobs)}/{total} Tier-2 jobs.")
print("Job IDs:", " ".join(jobs.values()))
