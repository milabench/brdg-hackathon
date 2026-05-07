#!/bin/bash
#SBATCH --job-name=p2d-e32_s64_m4_u4-s1
#SBATCH --partition=long
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=256G
#SBATCH --time=0:34:00
#SBATCH --output=/network/scratch/b/bouthilx/milabench/milabench/brdg-hackathon/sessions/torchatari/2/prep/p2d_t2_e32_s64_m4_u4_s1.slurm-%j.out
#SBATCH --error=/network/scratch/b/bouthilx/milabench/milabench/brdg-hackathon/sessions/torchatari/2/prep/p2d_t2_e32_s64_m4_u4_s1.slurm-%j.err

set -uo pipefail
cd /network/scratch/b/bouthilx/milabench/milabench
export MILABENCH_BASE=/network/scratch/b/bouthilx/milabench/results

LOG=/network/scratch/b/bouthilx/milabench/milabench/brdg-hackathon/sessions/torchatari/2/prep/p2d_t2_e32_s64_m4_u4_s1.log
{
  echo "=== [p2d_t2_e32_s64_m4_u4_s1 jobid=$SLURM_JOB_ID host=$(hostname) T=$(date -Is)] ==="
  uv run milabench run \
    --config /network/scratch/b/bouthilx/milabench/milabench/benchmarks/retired/torchatari/p2d_t2_e32_s64_m4_u4_s1.yaml \
    --select torchatari \
    --base /network/scratch/b/bouthilx/milabench/results \
    --run-name "p2d_t2_e32_s64_m4_u4_s1_${SLURM_JOB_ID}" 2>&1
  echo "exit=$?"
} >> "$LOG" 2>&1
echo "Done: $LOG"
