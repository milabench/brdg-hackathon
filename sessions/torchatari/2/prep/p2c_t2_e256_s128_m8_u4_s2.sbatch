#!/bin/bash
#SBATCH --job-name=p2c-e256_s128_m8_u4-s2
#SBATCH --partition=long
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=256G
#SBATCH --time=0:37:00
#SBATCH --output=/network/scratch/b/bouthilx/milabench/milabench/brdg-hackathon/sessions/torchatari/2/prep/p2c_t2_e256_s128_m8_u4_s2.slurm-%j.out
#SBATCH --error=/network/scratch/b/bouthilx/milabench/milabench/brdg-hackathon/sessions/torchatari/2/prep/p2c_t2_e256_s128_m8_u4_s2.slurm-%j.err

set -uo pipefail
cd /network/scratch/b/bouthilx/milabench/milabench
export MILABENCH_BASE=/network/scratch/b/bouthilx/milabench/results

LOG=/network/scratch/b/bouthilx/milabench/milabench/brdg-hackathon/sessions/torchatari/2/prep/p2c_t2_e256_s128_m8_u4_s2.log
{
  echo "=== [p2c_t2_e256_s128_m8_u4_s2 jobid=$SLURM_JOB_ID host=$(hostname) T=$(date -Is)] ==="
  uv run milabench run \
    --config /network/scratch/b/bouthilx/milabench/milabench/benchmarks/retired/torchatari/p2c_t2_e256_s128_m8_u4_s2.yaml \
    --select torchatari \
    --base /network/scratch/b/bouthilx/milabench/results \
    --run-name "p2c_t2_e256_s128_m8_u4_s2_${SLURM_JOB_ID}" 2>&1
  echo "exit=$?"
} >> "$LOG" 2>&1
echo "Done: $LOG"
