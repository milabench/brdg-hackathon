"""Submit N=3 Tier-2 TTR validation runs for the top-1 candidate: e256_s128_m4_u4.

At e256 throughput (~9000 items/s), each iteration (256*128=32768 env steps) takes ~3.6s.
To cover the 900s TTR window: need stop * 3.6 >= 900 → stop >= 250.
Using stop=400 → 405 * 3.6 = 1458s of training; max_duration=1600 as safety cap.
"""
import os, subprocess

REPO = "/network/scratch/b/bouthilx/milabench/milabench"
BENCH_DIR = f"{REPO}/benchmarks/retired/torchatari"
PREP_DIR  = f"{REPO}/brdg-hackathon/sessions/torchatari/2/prep"
MILABENCH_BASE = "/network/scratch/b/bouthilx/milabench/results"

TTR_VAL_YAML = """\
torchatari:
  max_duration: 1600
  inherits: _defaults
  definition: .
  install_variant: unpinned
  install_group: torch
  plan:
    method: per_gpu
  voir:
    options:
      stop: 400
      interval: "1s"
      skip: 5
  argv:
    --num-minibatches: 4
    --update-epochs: 4
    --num-steps: 128
    --num-envs: 256
    --total-timesteps: 500000000
    --env-id: Breakout-v5
    --exp-name: val_e256s128
    --seed: {seed}
"""

TTR_VAL_SBATCH = """\
#!/bin/bash
#SBATCH --job-name=p2-tval-s{seed}
#SBATCH --partition=long
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=256G
#SBATCH --time=0:50:00
#SBATCH --output={prep_dir}/ttr_val_e256s128_s{seed}.slurm-%j.out
#SBATCH --error={prep_dir}/ttr_val_e256s128_s{seed}.slurm-%j.err

set -uo pipefail
REPO={repo}
PREP={prep_dir}
CFG={bench_dir}/prep2_ttr_val_e256s128_s{seed}.yaml
LOG=$PREP/ttr_val_e256s128_s{seed}.log

cd "$REPO"
export MILABENCH_BASE={milabench_base}

{{
  echo "=== [ttr_val_e256s128_s{seed} jobid=$SLURM_JOB_ID host=$(hostname) T=$(date -Is)] ==="
  nvidia-smi 2>&1 | grep -E "NVIDIA-SMI|Driver|L40|MiB" | head -5
  echo ""
  uv run milabench run \\
    --config "$CFG" \\
    --select torchatari \\
    --base "$MILABENCH_BASE" \\
    --run-name "prep2_ttr_val_e256s128_s{seed}_${{SLURM_JOB_ID}}" 2>&1
  echo "exit=$?"
}} >> "$LOG" 2>&1
echo "Done: $LOG"
"""

jobs = {}
print("── TTR validation: e256_s128_m4_u4 (num_envs=256, num_steps=128, mb=4, ep=4) ──")
for seed in [1, 2, 3]:
    yaml_path = f"{BENCH_DIR}/prep2_ttr_val_e256s128_s{seed}.yaml"
    with open(yaml_path, "w") as f:
        f.write(TTR_VAL_YAML.format(seed=seed))

    sbatch_path = f"{PREP_DIR}/ttr_val_e256s128_s{seed}.sbatch"
    with open(sbatch_path, "w") as f:
        f.write(TTR_VAL_SBATCH.format(
            seed=seed, prep_dir=PREP_DIR, repo=REPO,
            bench_dir=BENCH_DIR, milabench_base=MILABENCH_BASE,
        ))

    result = subprocess.run(["sbatch", sbatch_path], capture_output=True, text=True)
    if result.returncode == 0:
        jid = result.stdout.strip().split()[-1]
        jobs[f"s{seed}"] = jid
        print(f"  seed={seed}  job {jid}")
    else:
        print(f"  seed={seed}  FAILED: {result.stderr.strip()}")

print(f"\nSubmitted {len(jobs)}/3 TTR validation jobs.")
print("Job IDs:", " ".join(jobs.values()))
