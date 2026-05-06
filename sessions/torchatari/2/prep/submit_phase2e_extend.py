#!/usr/bin/env python3
"""Phase 2E — grid extension along two boundary axes.

Phase 2D winner (e256_s32_m32_u4, mb=256, TTR=255.7s) sits at both the smallest
num_steps (s=32) and the largest num_minibatches (m=32) in the grid. Extend both.

Axis 1 — new num_steps: s=16 (for all e, m that keep mb >= 64)
Axis 2 — new num_minibatches: m=64, m=128 (for existing s in {32,64,128}, mb >= 64)
update_epochs = 4 (fixed throughout).

mb floor = 64  (mb=32 DNF'd in Phase 2D; no point testing smaller).

iter_time model: BASE_IT_S128[e] × s/128, floored at 0.10 s (same as Phase 2D).
stop = ceil(900/iter_time) + 20
max_dur = ceil((stop × iter_time × 1.45 + 120) / 60) × 60
sbatch_min = max_dur // 60 + 10
"""
import math, subprocess

REPO           = "/network/scratch/b/bouthilx/milabench/milabench"
BENCH_DIR      = f"{REPO}/benchmarks/retired/torchatari"
PREP_DIR       = f"{REPO}/brdg-hackathon/sessions/torchatari/2/prep"
MILABENCH_BASE = "/network/scratch/b/bouthilx/milabench/results"

BASE_IT_S128 = {32: 0.63, 64: 1.22, 128: 2.12, 256: 3.60}
MB_FLOOR = 64

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
#SBATCH --job-name=p2e-{label}-s{seed}
#SBATCH --partition=long
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=256G
#SBATCH --time=0:{sbatch_min}:00
#SBATCH --output={prep_dir}/p2e_t2_{label}_s{seed}.slurm-%j.out
#SBATCH --error={prep_dir}/p2e_t2_{label}_s{seed}.slurm-%j.err

set -uo pipefail
cd {repo}
export MILABENCH_BASE={milabench_base}

LOG={prep_dir}/p2e_t2_{label}_s{seed}.log
{{
  echo "=== [p2e_t2_{label}_s{seed} jobid=$SLURM_JOB_ID host=$(hostname) T=$(date -Is)] ==="
  uv run milabench run \\
    --config {bench_dir}/p2e_t2_{label}_s{seed}.yaml \\
    --select torchatari \\
    --base {milabench_base} \\
    --run-name "p2e_t2_{label}_s{seed}_${{SLURM_JOB_ID}}" 2>&1
  echo "exit=$?"
}} >> "$LOG" 2>&1
echo "Done: $LOG"
"""

ENVS = [32, 64, 128, 256]

configs = []

# Axis 1: new s=16, all (e, m) with mb >= MB_FLOOR
for e in ENVS:
    for m in [4, 8, 16, 32, 64, 128]:
        s = 16
        mb = (e * s) // m
        if mb < MB_FLOOR:
            continue
        it       = iter_time_est(e, s)
        stop     = math.ceil(900 / it) + 20
        max_dur  = math.ceil((stop * it * 1.45 + 120) / 60) * 60
        sbatch_min = max_dur // 60 + 10
        label    = f"e{e}_s{s}_m{m}_u4"
        configs.append((label, e, s, m, 4, it, stop, max_dur, sbatch_min, mb))

# Axis 2: new m=64 and m=128, existing s in {32, 64, 128}, mb >= MB_FLOOR
for e in ENVS:
    for s in [32, 64, 128]:
        for m in [64, 128]:
            mb = (e * s) // m
            if mb < MB_FLOOR:
                continue
            it       = iter_time_est(e, s)
            stop     = math.ceil(900 / it) + 20
            max_dur  = math.ceil((stop * it * 1.45 + 120) / 60) * 60
            sbatch_min = max_dur // 60 + 10
            label    = f"e{e}_s{s}_m{m}_u4"
            configs.append((label, e, s, m, 4, it, stop, max_dur, sbatch_min, mb))

print(f"── Phase 2E extension grid ──")
print(f"{len(configs)} new configs × 3 seeds = {len(configs)*3} jobs  (mb floor={MB_FLOOR})\n")
print(f"{'label':30s}  {'e':>4} {'s':>4} {'m':>4}  {'mb':>6}  {'it':>5}  {'stop':>6}  {'max_dur':>8}  sbatch")
print("-" * 97)
for cfg in configs:
    label, e, s, m, u, it, stop, max_dur, sbatch_min, mb = cfg
    print(f"  {label:30s}  {e:4d} {s:4d} {m:4d}  {mb:6d}  {it:5.2f}  {stop:6d}  {max_dur:7d}s  {sbatch_min}min")
print()

jobs = {}
for cfg in configs:
    label, e, s, m, u, it, stop, max_dur, sbatch_min, mb = cfg
    exp_name = label.replace("_", "")

    for seed in [1, 2, 3]:
        yaml_path   = f"{BENCH_DIR}/p2e_t2_{label}_s{seed}.yaml"
        sbatch_path = f"{PREP_DIR}/p2e_t2_{label}_s{seed}.sbatch"

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
