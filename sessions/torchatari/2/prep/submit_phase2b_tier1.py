#!/usr/bin/env python3
"""Phase 2B — extended Tier-1 sweep.

9 new num_envs candidates to fill the density between e16 and e384.
Same protocol as Phase 2: stop=60, skip=5, max_duration=600.
"""
import os, subprocess, math

REPO           = "/network/scratch/b/bouthilx/milabench/milabench"
BENCH_DIR      = f"{REPO}/benchmarks/retired/torchatari"
PREP_DIR       = f"{REPO}/brdg-hackathon/sessions/torchatari/2/prep"
MILABENCH_BASE = "/network/scratch/b/bouthilx/milabench/results"

# New num_envs values not yet in the sweep (have: 64, 128, 256, 512)
NEW_ENVS = [16, 24, 32, 48, 96, 160, 192, 320, 384]

YAML_TEMPLATE = """\
torchatari:
  max_duration: 600
  inherits: _defaults
  definition: .
  install_variant: unpinned
  install_group: torch
  plan:
    method: per_gpu
  voir:
    options:
      stop: 60
      interval: "1s"
      skip: 5
  argv:
    --num-minibatches: 4
    --update-epochs: 4
    --num-steps: 128
    --num-envs: {num_envs}
    --total-timesteps: 500000000
    --env-id: Breakout-v5
    --exp-name: p2b_t1_e{num_envs}
    --seed: 1
"""

SBATCH_TEMPLATE = """\
#!/bin/bash
#SBATCH --job-name=p2b-t1-e{num_envs}
#SBATCH --partition=long
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=256G
#SBATCH --time=0:20:00
#SBATCH --output={prep_dir}/p2b_t1_e{num_envs}.slurm-%j.out
#SBATCH --error={prep_dir}/p2b_t1_e{num_envs}.slurm-%j.err

set -uo pipefail
cd {repo}
export MILABENCH_BASE={milabench_base}

LOG={prep_dir}/p2b_t1_e{num_envs}.log
{{
  echo "=== [p2b_t1_e{num_envs} jobid=$SLURM_JOB_ID host=$(hostname) T=$(date -Is)] ==="
  uv run milabench run \\
    --config {bench_dir}/p2b_t1_e{num_envs}.yaml \\
    --select torchatari \\
    --base {milabench_base} \\
    --run-name "p2b_t1_e{num_envs}_${{SLURM_JOB_ID}}" 2>&1
  echo "exit=$?"
}} >> "$LOG" 2>&1
echo "Done: $LOG"
"""

jobs = {}
print("── Phase 2B Tier-1 extended sweep ──")
for e in NEW_ENVS:
    label    = f"e{e}"
    yaml_p   = f"{BENCH_DIR}/p2b_t1_{label}.yaml"
    sbatch_p = f"{PREP_DIR}/p2b_t1_{label}.sbatch"

    with open(yaml_p, "w") as f:
        f.write(YAML_TEMPLATE.format(num_envs=e))

    with open(sbatch_p, "w") as f:
        f.write(SBATCH_TEMPLATE.format(
            num_envs=e, prep_dir=PREP_DIR, repo=REPO,
            bench_dir=BENCH_DIR, milabench_base=MILABENCH_BASE,
        ))

    result = subprocess.run(["sbatch", sbatch_p], capture_output=True, text=True)
    if result.returncode == 0:
        jid = result.stdout.strip().split()[-1]
        jobs[label] = jid
        print(f"  {label:<8}  job {jid}")
    else:
        print(f"  {label:<8}  FAILED: {result.stderr.strip()}")

print(f"\nSubmitted {len(jobs)}/{len(NEW_ENVS)} Tier-1 jobs.")
print("Job IDs:", " ".join(jobs.values()))
