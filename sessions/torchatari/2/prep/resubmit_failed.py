"""Resubmit sweep candidates that failed due to max_duration=600 being too short.

For each failed config, compute the iteration time from:
  iter_time_est = (num_envs * num_steps) / 8000  # pessimistic throughput
Then set:
  stop = 200 if iter_time_est <= 8s, else 80 (still >=60 obs minimum per RULES §8)
  max_duration = ceil((stop + skip) * iter_time_est * 1.35) + 60
  sbatch time = max_duration + 900s overhead
"""
import os, math, subprocess

REPO = "/network/scratch/b/bouthilx/milabench/milabench"
BENCH_DIR = f"{REPO}/benchmarks/retired/torchatari"
PREP_DIR  = f"{REPO}/brdg-hackathon/sessions/torchatari/2/prep"
MILABENCH_BASE = "/network/scratch/b/bouthilx/milabench/results"
SKIP = 5

# Failed candidates: (label, num_envs, num_steps, num_minibatches, update_epochs)
FAILED = [
    ("e256_s128_m4_u4",  256, 128,  4, 4),
    ("e512_s128_m4_u4",  512, 128,  4, 4),
    ("e128_s256_m4_u4",  128, 256,  4, 4),
    ("e128_s512_m4_u4",  128, 512,  4, 4),
    ("e256_s256_m8_u4",  256, 256,  8, 4),
    ("e512_s256_m8_u4",  512, 256,  8, 4),
    ("e256_s128_m2_u4",  256, 128,  2, 4),
    ("e512_s128_m2_u4",  512, 128,  2, 4),
    ("e256_s128_m4_u8",  256, 128,  4, 8),
    ("e128_s256_m4_u8",  128, 256,  4, 8),
    ("e512_s128_m4_u8",  512, 128,  4, 8),
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
      skip: {skip}
  argv:
    --num-minibatches: {num_minibatches}
    --update-epochs: {update_epochs}
    --num-steps: {num_steps}
    --num-envs: {num_envs}
    --total-timesteps: 500000000
    --env-id: Breakout-v5
    --seed: 1
"""

SBATCH_TEMPLATE = """\
#!/bin/bash
#SBATCH --job-name=p2r-{label}
#SBATCH --partition=long
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=256G
#SBATCH --time={sbatch_time}
#SBATCH --output={prep_dir}/rerun_{label}.slurm-%j.out
#SBATCH --error={prep_dir}/rerun_{label}.slurm-%j.err

set -uo pipefail
REPO={repo}
PREP={prep_dir}
CFG={bench_dir}/prep2r_sweep_{label}.yaml
LOG=$PREP/rerun_{label}.log

cd "$REPO"
export MILABENCH_BASE={milabench_base}

{{
  echo "=== [RERUN {label} jobid=$SLURM_JOB_ID host=$(hostname) T=$(date -Is)] ==="
  nvidia-smi 2>&1 | grep -E "NVIDIA-SMI|Driver|L40|MiB" | head -5
  echo ""
  uv run milabench run \\
    --config "$CFG" \\
    --select torchatari \\
    --base "$MILABENCH_BASE" \\
    --run-name "prep2r_sweep_{label}_${{SLURM_JOB_ID}}" 2>&1
  echo "exit=$?"
}} >> "$LOG" 2>&1
echo "Done: $LOG"
"""

BASE_THROUGHPUT = 8000.0  # pessimistic items/s estimate

def compute_params(num_envs, num_steps, update_epochs):
    spi = num_envs * num_steps
    # Adjust for extra GPU work from update_epochs > 4 (default=4)
    epoch_factor = update_epochs / 4.0
    iter_time_est = (spi / BASE_THROUGHPUT) * epoch_factor
    stop = 200 if iter_time_est <= 8.0 else 80
    total_obs = stop + SKIP
    raw_dur = total_obs * iter_time_est * 1.35 + 60
    max_duration = int(math.ceil(raw_dur / 60) * 60)  # round up to nearest minute
    sbatch_s = max_duration + 900
    h, m = divmod(sbatch_s, 3600)
    m = m // 60
    sbatch_time = f"{h}:{m:02d}:00"
    return stop, max_duration, sbatch_time, iter_time_est

job_ids = {}
print(f"{'label':28s}  {'stop':>4} {'max_dur':>7} {'sbatch':>7}  {'est_iter':>8}")
print("-" * 70)

for (label, num_envs, num_steps, num_minibatches, update_epochs) in FAILED:
    stop, max_duration, sbatch_time, iter_est = compute_params(num_envs, num_steps, update_epochs)
    print(f"  {label:26s}  {stop:4d} {max_duration:7d}s {sbatch_time:>7}  {iter_est:8.2f}s/iter")

    yaml_path = f"{BENCH_DIR}/prep2r_sweep_{label}.yaml"
    with open(yaml_path, "w") as f:
        f.write(YAML_TEMPLATE.format(
            max_duration=max_duration, stop=stop, skip=SKIP,
            num_envs=num_envs, num_steps=num_steps,
            num_minibatches=num_minibatches, update_epochs=update_epochs,
        ))

    sbatch_path = f"{PREP_DIR}/rerun_{label}.sbatch"
    with open(sbatch_path, "w") as f:
        f.write(SBATCH_TEMPLATE.format(
            label=label, prep_dir=PREP_DIR, repo=REPO,
            bench_dir=BENCH_DIR, milabench_base=MILABENCH_BASE,
            sbatch_time=sbatch_time,
        ))

    result = subprocess.run(["sbatch", sbatch_path], capture_output=True, text=True)
    if result.returncode == 0:
        jid = result.stdout.strip().split()[-1]
        job_ids[label] = jid
        print(f"    → job {jid}")
    else:
        print(f"    → FAILED: {result.stderr.strip()}")

print(f"\nSubmitted {len(job_ids)}/{len(FAILED)} rerun jobs.")
print("Job IDs:", " ".join(job_ids.values()))
