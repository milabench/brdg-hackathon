#!/bin/bash
#SBATCH --job-name=p2-e64_s128_m4_u4
#SBATCH --partition=long
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=256G
#SBATCH --time=0:30:00
#SBATCH --output=/network/scratch/b/bouthilx/milabench/milabench/brdg-hackathon/sessions/torchatari/2/prep/sweep_e64_s128_m4_u4.slurm-%j.out
#SBATCH --error=/network/scratch/b/bouthilx/milabench/milabench/brdg-hackathon/sessions/torchatari/2/prep/sweep_e64_s128_m4_u4.slurm-%j.err

set -uo pipefail
REPO=/network/scratch/b/bouthilx/milabench/milabench
PREP=/network/scratch/b/bouthilx/milabench/milabench/brdg-hackathon/sessions/torchatari/2/prep
CFG=/network/scratch/b/bouthilx/milabench/milabench/benchmarks/retired/torchatari/prep2_sweep_e64_s128_m4_u4.yaml
LOG=$PREP/sweep_e64_s128_m4_u4.log

cd "$REPO"
export MILABENCH_BASE=/network/scratch/b/bouthilx/milabench/results

{
  echo "=== [e64_s128_m4_u4 jobid=$SLURM_JOB_ID host=$(hostname) T=$(date -Is)] ==="
  nvidia-smi 2>&1 | grep -E "NVIDIA-SMI|Driver|L40|MiB" | head -5
  echo ""
  uv run milabench run \
    --config "$CFG" \
    --select torchatari \
    --base "$MILABENCH_BASE" \
    --run-name "prep2_sweep_e64_s128_m4_u4_${SLURM_JOB_ID}" 2>&1
  echo "exit=$?"
} >> "$LOG" 2>&1
echo "Done: $LOG"
