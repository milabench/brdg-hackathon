#!/bin/bash
#SBATCH --partition=unkillable
#SBATCH --gres=gpu:l40s:1
#SBATCH -c 6
#SBATCH --job-name=torchatari_t2s2_s46
#SBATCH --output=/home/mila/r/rygaards/proj/milabench/brdg-hackathon/sessions/torchatari/2/sonnet4.6/phase2_tier2_seed2.out

set -e

MILABENCH_REPO=/home/mila/r/rygaards/proj/milabench
export MILABENCH_BASE=/network/scratch/r/rygaards/milabench/base

cd $MILABENCH_REPO

echo "=== Phase 2 Tier-2 baseline seed 2 — locked HPs e256 s32 m32 u4 ==="
echo "max_duration=2000 (fix for voir stop=1020 at 6 CPUs needing ~1598s)"
uv run milabench run \
    --config benchmarks/retired/torchatari/p2d_t2_e256_s32_m32_u4_s2.yaml \
    --select torchatari \
    --base $MILABENCH_BASE \
    --run-name phase2_tier2_s2

echo "=== DONE ==="
