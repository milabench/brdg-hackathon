"""Submit N=2 additional short baseline replicates + N=3 Tier-2 TTR runs."""
import os, subprocess

REPO = "/network/scratch/b/bouthilx/milabench/milabench"
BENCH_DIR = f"{REPO}/benchmarks/retired/torchatari"
PREP_DIR  = f"{REPO}/brdg-hackathon/sessions/torchatari/2/prep"
MILABENCH_BASE = "/network/scratch/b/bouthilx/milabench/results"

# ── Short-run baseline replicates (seeds 2 and 3; seed 1 already done in sanity baseline) ──
SHORT_YAML = """\
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
      stop: 200
      interval: "1s"
      skip: 5
  argv:
    --num-minibatches: 4
    --update-epochs: 4
    --num-steps: 128
    --num-envs: 128
    --total-timesteps: 500000000
    --env-id: Breakout-v5
    --seed: {seed}
"""

SHORT_SBATCH = """\
#!/bin/bash
#SBATCH --job-name=p2-base-s{seed}
#SBATCH --partition=long
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=256G
#SBATCH --time=0:30:00
#SBATCH --output={prep_dir}/short_baseline_s{seed}.slurm-%j.out
#SBATCH --error={prep_dir}/short_baseline_s{seed}.slurm-%j.err

set -uo pipefail
REPO={repo}
PREP={prep_dir}
CFG={bench_dir}/prep2_short_baseline_s{seed}.yaml
LOG=$PREP/short_baseline_s{seed}.log

cd "$REPO"
export MILABENCH_BASE={milabench_base}

{{
  echo "=== [short_baseline_s{seed} jobid=$SLURM_JOB_ID host=$(hostname) T=$(date -Is)] ==="
  nvidia-smi 2>&1 | grep -E "NVIDIA-SMI|Driver|L40|MiB" | head -5
  echo ""
  uv run milabench run \\
    --config "$CFG" \\
    --select torchatari \\
    --base "$MILABENCH_BASE" \\
    --run-name "prep2_short_baseline_s{seed}_${{SLURM_JOB_ID}}" 2>&1
  echo "exit=$?"
}} >> "$LOG" 2>&1
echo "Done: $LOG"
"""

# ── Tier-2 TTR runs (seeds 1, 2, 3; voir stop=600 → ~1290s runtime; TTR extracted over 900s window) ──
TTR_YAML = """\
torchatari:
  max_duration: 1500
  inherits: _defaults
  definition: .
  install_variant: unpinned
  install_group: torch
  plan:
    method: per_gpu
  voir:
    options:
      stop: 600
      interval: "1s"
      skip: 5
  argv:
    --num-minibatches: 4
    --update-epochs: 4
    --num-steps: 128
    --num-envs: 128
    --total-timesteps: 500000000
    --env-id: Breakout-v5
    --seed: {seed}
"""

TTR_SBATCH = """\
#!/bin/bash
#SBATCH --job-name=p2-ttr-s{seed}
#SBATCH --partition=long
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=256G
#SBATCH --time=0:35:00
#SBATCH --output={prep_dir}/ttr_baseline_s{seed}.slurm-%j.out
#SBATCH --error={prep_dir}/ttr_baseline_s{seed}.slurm-%j.err

set -uo pipefail
REPO={repo}
PREP={prep_dir}
CFG={bench_dir}/prep2_ttr_baseline_s{seed}.yaml
LOG=$PREP/ttr_baseline_s{seed}.log

cd "$REPO"
export MILABENCH_BASE={milabench_base}

{{
  echo "=== [ttr_baseline_s{seed} jobid=$SLURM_JOB_ID host=$(hostname) T=$(date -Is)] ==="
  nvidia-smi 2>&1 | grep -E "NVIDIA-SMI|Driver|L40|MiB" | head -5
  echo ""
  uv run milabench run \\
    --config "$CFG" \\
    --select torchatari \\
    --base "$MILABENCH_BASE" \\
    --run-name "prep2_ttr_baseline_s{seed}_${{SLURM_JOB_ID}}" 2>&1
  echo "exit=$?"
}} >> "$LOG" 2>&1
echo "Done: $LOG"
"""

jobs = {}

print("── Short-run baseline replicates (seeds 2 & 3) ──")
for seed in [2, 3]:
    yaml_path = f"{BENCH_DIR}/prep2_short_baseline_s{seed}.yaml"
    with open(yaml_path, "w") as f:
        f.write(SHORT_YAML.format(seed=seed))

    sbatch_path = f"{PREP_DIR}/short_baseline_s{seed}.sbatch"
    with open(sbatch_path, "w") as f:
        f.write(SHORT_SBATCH.format(
            seed=seed, prep_dir=PREP_DIR, repo=REPO,
            bench_dir=BENCH_DIR, milabench_base=MILABENCH_BASE,
        ))

    result = subprocess.run(["sbatch", sbatch_path], capture_output=True, text=True)
    if result.returncode == 0:
        jid = result.stdout.strip().split()[-1]
        jobs[f"short_s{seed}"] = jid
        print(f"  short_baseline_s{seed:d}  job {jid}")
    else:
        print(f"  short_baseline_s{seed:d}  FAILED: {result.stderr.strip()}")

print("\n── Tier-2 TTR baseline runs (seeds 1, 2, 3) ──")
for seed in [1, 2, 3]:
    yaml_path = f"{BENCH_DIR}/prep2_ttr_baseline_s{seed}.yaml"
    with open(yaml_path, "w") as f:
        f.write(TTR_YAML.format(seed=seed))

    sbatch_path = f"{PREP_DIR}/ttr_baseline_s{seed}.sbatch"
    with open(sbatch_path, "w") as f:
        f.write(TTR_SBATCH.format(
            seed=seed, prep_dir=PREP_DIR, repo=REPO,
            bench_dir=BENCH_DIR, milabench_base=MILABENCH_BASE,
        ))

    result = subprocess.run(["sbatch", sbatch_path], capture_output=True, text=True)
    if result.returncode == 0:
        jid = result.stdout.strip().split()[-1]
        jobs[f"ttr_s{seed}"] = jid
        print(f"  ttr_baseline_s{seed:d}      job {jid}")
    else:
        print(f"  ttr_baseline_s{seed:d}      FAILED: {result.stderr.strip()}")

print(f"\nSubmitted {len(jobs)}/5 jobs.")
print("Job IDs:", " ".join(jobs.values()))
