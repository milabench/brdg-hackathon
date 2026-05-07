#!/bin/bash
#SBATCH --partition=unkillable
#SBATCH --gres=gpu:l40s:1
#SBATCH -c 6
#SBATCH --job-name=torchatari_t1_s46
#SBATCH --output=/home/mila/r/rygaards/proj/milabench/brdg-hackathon/sessions/torchatari/2/sonnet4.6/phase2_tier1_baseline_6cpu.out

set -e

MILABENCH_REPO=/home/mila/r/rygaards/proj/milabench
export MILABENCH_BASE=/network/scratch/r/rygaards/milabench/base

cd $MILABENCH_REPO

echo "=== Phase 2 Tier-1 re-measurement — run 1/3 (voir stop=200, max_duration=600) ==="
uv run milabench run \
    --config benchmarks/retired/torchatari/phase2_t1_e256_s32_m32_u4.yaml \
    --select torchatari \
    --base $MILABENCH_BASE \
    --run-name phase2_t1_6cpu_r1

echo "=== Phase 2 Tier-1 re-measurement — run 2/3 ==="
uv run milabench run \
    --config benchmarks/retired/torchatari/phase2_t1_e256_s32_m32_u4.yaml \
    --select torchatari \
    --base $MILABENCH_BASE \
    --run-name phase2_t1_6cpu_r2

echo "=== Phase 2 Tier-1 re-measurement — run 3/3 ==="
uv run milabench run \
    --config benchmarks/retired/torchatari/phase2_t1_e256_s32_m32_u4.yaml \
    --select torchatari \
    --base $MILABENCH_BASE \
    --run-name phase2_t1_6cpu_r3

echo "=== DONE ==="
