#!/usr/bin/env python3
"""Phase 2C — cross-term Tier-2 TTR validation.

Hypotheses under test:
  H1 (compensated envs):    e256_s64_m4_u4  — same batch_size as default, 2× env diversity
  H2 (compensated+more mb): e256_s64_m8_u4  — same batch_size, 2× minibatches → same minibatch_size=2048
  H3 (more mb with more e): e256_s128_m8_u4 — 2× batch, same minibatch_size as default, 2× gradient steps/outer
  H4 (stack best two):      e128_s64_m8_u4  — combine s64 and m8 (both gave -21 to -28% TTR)
  H5 (smaller minibatch):   e128_s128_m16_u4 — minibatch=1024, code's own default m; test if smaller is better
  H6 (even smaller batch):  e64_s64_m4_u4   — batch=4096, minibatch=1024; fastest updates
  H7 (best envs+minibatch): e64_s128_m8_u4  — e64 (best envs) with m8 (same minibatch_size=1024)

minibatch_size summary:
  default   e128_s128_m4:   (128×128)/4  = 4096  (baseline)
  H1        e256_s64_m4:    (256×64)/4   = 4096  (same)
  H2        e256_s64_m8:    (256×64)/8   = 2048  (same as best single-HP winners)
  H3        e256_s128_m8:   (256×128)/8  = 4096  (same as default)
  H4        e128_s64_m8:    (128×64)/8   = 1024
  H5        e128_s128_m16:  (128×128)/16 = 1024
  H6        e64_s64_m4:     (64×64)/4    = 1024
  H7        e64_s128_m8:    (64×128)/8   = 1024

iter_time estimates (s):    update_freq relative to default (0.47 iter/s):
  H1 e256_s64:   0.028×256^0.897 × (64/128)^? ≈ 2.0s  → ~0.50 iters/s  (+6%)
  H2 e256_s64:   same collection as H1          → ~0.50 iters/s  (+6%)
  H3 e256_s128:  ~3.6s                          → ~0.28 iters/s  (-40%)
  H4 e128_s64:   ~1.09s (measured)              → ~0.92 iters/s  (+96%, same as s64 alone)
  H5 e128_s128:  ~2.12s (measured)              → ~0.47 iters/s  (same as default)
  H6 e64_s64:    ~0.7s (estimated)              → ~1.43 iters/s  (+204%)
  H7 e64_s128:   ~1.22s (measured)              → ~0.82 iters/s  (+74%)

Note: For H1 and H2, iter_time for e256_s64 estimated as ~2.0s
(e256_s128 took 3.6s; halving num_steps roughly halves collection time,
 though GPU update time changes little → actual iter_time ≈ 3.6/2 + small_const ≈ 2.0s).

stop = ceil(900 / iter_time) + 20; max_duration = ceil(stop × iter_time × 1.45 + 120), rounded up 60s.
"""
import os, math, subprocess

REPO           = "/network/scratch/b/bouthilx/milabench/milabench"
BENCH_DIR      = f"{REPO}/benchmarks/retired/torchatari"
PREP_DIR       = f"{REPO}/brdg-hackathon/sessions/torchatari/2/prep"
MILABENCH_BASE = "/network/scratch/b/bouthilx/milabench/results"

# (label, num_envs, num_steps, num_minibatches, update_epochs,
#  iter_time_est_s, t2_stop, max_duration_s, sbatch_min)
CONFIGS = [
    # H1: compensated envs — same batch_size as default, 2× env diversity
    ("e256_s64_m4_u4",   256,  64, 4, 4,  2.0,  470, 1440, 34),
    # H2: compensated envs + double minibatches → minibatch_size=2048 (same as single-HP winners)
    ("e256_s64_m8_u4",   256,  64, 8, 4,  2.0,  470, 1440, 34),
    # H3: more envs with proportional minibatches to keep minibatch_size fixed at 4096
    ("e256_s128_m8_u4",  256, 128, 8, 4,  3.6,  270, 1620, 37),
    # H4: stack s64 + m8 (both individually reduce TTR by 21-28%)
    ("e128_s64_m8_u4",   128,  64, 8, 4,  1.09, 849, 1500, 35),
    # H5: smaller minibatch at default envs/steps (m=16, code's own default)
    ("e128_s128_m16_u4", 128, 128, 16, 4, 2.12, 445, 1500, 35),
    # H6: smallest batch (fastest updates) — e64_s64
    ("e64_s64_m4_u4",     64,  64, 4, 4,  0.7, 1306, 1440, 34),
    # H7: e64 (best single-envs winner) + m8 → minibatch_size=1024
    ("e64_s128_m8_u4",    64, 128, 8, 4,  1.22, 757, 1500, 35),
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
#SBATCH --job-name=p2c-{label}-s{seed}
#SBATCH --partition=long
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=256G
#SBATCH --time=0:{sbatch_min}:00
#SBATCH --output={prep_dir}/p2c_t2_{label}_s{seed}.slurm-%j.out
#SBATCH --error={prep_dir}/p2c_t2_{label}_s{seed}.slurm-%j.err

set -uo pipefail
cd {repo}
export MILABENCH_BASE={milabench_base}

LOG={prep_dir}/p2c_t2_{label}_s{seed}.log
{{
  echo "=== [p2c_t2_{label}_s{seed} jobid=$SLURM_JOB_ID host=$(hostname) T=$(date -Is)] ==="
  uv run milabench run \\
    --config {bench_dir}/p2c_t2_{label}_s{seed}.yaml \\
    --select torchatari \\
    --base {milabench_base} \\
    --run-name "p2c_t2_{label}_s{seed}_${{SLURM_JOB_ID}}" 2>&1
  echo "exit=$?"
}} >> "$LOG" 2>&1
echo "Done: $LOG"
"""

print("── Phase 2C Tier-2 cross-term TTR validation ──")
print(f"{'label':25s}  {'e':>4} {'s':>4} {'m':>3} {'u':>3}  {'mb_size':>7}  {'stop':>5}  {'max_dur':>7}  sbatch")
print("-" * 80)
for cfg in CONFIGS:
    label, e, s, m, u, it, stop, max_dur, sbatch_min = cfg
    mb = (e * s) // m
    print(f"  {label:25s}  {e:4d} {s:4d} {m:3d} {u:3d}  {mb:7d}  {stop:5d}  {max_dur:6d}s  {sbatch_min}min")
print(f"\nTotal: {len(CONFIGS)} configs × 3 seeds = {len(CONFIGS)*3} jobs\n")

jobs = {}
for cfg in CONFIGS:
    label, e, s, m, u, it, stop, max_dur, sbatch_min = cfg
    exp_name = label.replace("_", "")

    for seed in [1, 2, 3]:
        yaml_path   = f"{BENCH_DIR}/p2c_t2_{label}_s{seed}.yaml"
        sbatch_path = f"{PREP_DIR}/p2c_t2_{label}_s{seed}.sbatch"

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

print(f"\nSubmitted {len(jobs)}/{len(CONFIGS)*3} jobs.")
print("Job IDs:", " ".join(jobs.values()))
