#!/bin/bash
#SBATCH --job-name=p2-base-s2
#SBATCH --partition=long
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=256G
#SBATCH --time=0:30:00
#SBATCH --output=/network/scratch/b/bouthilx/milabench/milabench/brdg-hackathon/sessions/torchatari/2/prep/short_baseline_s2.slurm-%j.out
#SBATCH --error=/network/scratch/b/bouthilx/milabench/milabench/brdg-hackathon/sessions/torchatari/2/prep/short_baseline_s2.slurm-%j.err

set -uo pipefail
REPO=/network/scratch/b/bouthilx/milabench/milabench
PREP=/network/scratch/b/bouthilx/milabench/milabench/brdg-hackathon/sessions/torchatari/2/prep
CFG=/network/scratch/b/bouthilx/milabench/milabench/benchmarks/retired/torchatari/prep2_short_baseline_s2.yaml
LOG=$PREP/short_baseline_s2.log

cd "$REPO"
export MILABENCH_BASE=/network/scratch/b/bouthilx/milabench/results

{
  echo "=== [short_baseline_s2 jobid=$SLURM_JOB_ID host=$(hostname) T=$(date -Is)] ==="
  nvidia-smi 2>&1 | grep -E "NVIDIA-SMI|Driver|L40|MiB" | head -5
  echo ""
  uv run milabench run \
    --config "$CFG" \
    --select torchatari \
    --base "$MILABENCH_BASE" \
    --run-name "prep2_short_baseline_s2_${SLURM_JOB_ID}" 2>&1
  echo "exit=$?"
} >> "$LOG" 2>&1
echo "Done: $LOG"
