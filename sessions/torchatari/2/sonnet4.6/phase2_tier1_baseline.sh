#!/bin/bash
#SBATCH --partition=long
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=256G
#SBATCH --time=00:45:00
#SBATCH --job-name=torchatari_p2_s46
#SBATCH --output=/home/mila/r/rygaards/proj/milabench/brdg-hackathon/sessions/torchatari/2/sonnet4.6/phase2_tier1_baseline.out

set -e

MILABENCH_REPO=/home/mila/r/rygaards/proj/milabench
export MILABENCH_BASE=/network/scratch/r/rygaards/milabench/base

cd $MILABENCH_REPO

echo "=== Phase 2 Tier-1 re-measurement — run 1/3 ==="
uv run milabench run \
    --config benchmarks/retired/torchatari/phase2_t1_e256_s32_m32_u4.yaml \
    --select torchatari \
    --base $MILABENCH_BASE \
    --run-name phase2_t1_run1

echo "=== Phase 2 Tier-1 re-measurement — run 2/3 ==="
uv run milabench run \
    --config benchmarks/retired/torchatari/phase2_t1_e256_s32_m32_u4.yaml \
    --select torchatari \
    --base $MILABENCH_BASE \
    --run-name phase2_t1_run2

echo "=== Phase 2 Tier-1 re-measurement — run 3/3 ==="
uv run milabench run \
    --config benchmarks/retired/torchatari/phase2_t1_e256_s32_m32_u4.yaml \
    --select torchatari \
    --base $MILABENCH_BASE \
    --run-name phase2_t1_run3

echo "=== DONE ==="
