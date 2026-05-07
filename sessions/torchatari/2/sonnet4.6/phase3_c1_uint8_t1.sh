#!/bin/bash
#SBATCH --partition=unkillable
#SBATCH --gres=gpu:l40s:1
#SBATCH -c 6
#SBATCH --job-name=torchatari_c1t1_s46
#SBATCH --output=/home/mila/r/rygaards/proj/milabench/brdg-hackathon/sessions/torchatari/2/sonnet4.6/phase3_c1_uint8_t1.out

set -e

MILABENCH_REPO=/home/mila/r/rygaards/proj/milabench
export MILABENCH_BASE=/network/scratch/r/rygaards/milabench/base

cd $MILABENCH_REPO

echo "=== Phase 3 candidate 1: uint8 obs buffer — Tier-1 screening run 1/3 ==="
uv run milabench run \
    --config benchmarks/retired/torchatari/phase3_c1_uint8_t1.yaml \
    --select torchatari \
    --base $MILABENCH_BASE \
    --run-name phase3_c1_uint8_t1_r1

echo "=== run 2/3 ==="
uv run milabench run \
    --config benchmarks/retired/torchatari/phase3_c1_uint8_t1.yaml \
    --select torchatari \
    --base $MILABENCH_BASE \
    --run-name phase3_c1_uint8_t1_r2

echo "=== run 3/3 ==="
uv run milabench run \
    --config benchmarks/retired/torchatari/phase3_c1_uint8_t1.yaml \
    --select torchatari \
    --base $MILABENCH_BASE \
    --run-name phase3_c1_uint8_t1_r3

echo "=== DONE ==="
