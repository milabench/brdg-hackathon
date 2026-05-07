#!/bin/bash
#SBATCH --partition=unkillable
#SBATCH --gres=gpu:l40s:1
#SBATCH -c 6
#SBATCH --job-name=torchatari_c1t2_s46
#SBATCH --output=/home/mila/r/rygaards/proj/milabench/brdg-hackathon/sessions/torchatari/2/sonnet4.6/phase3_c1_uint8_t2.out

set -e

MILABENCH_REPO=/home/mila/r/rygaards/proj/milabench
export MILABENCH_BASE=/network/scratch/r/rygaards/milabench/base

cd $MILABENCH_REPO

echo "=== Phase 3 C1 uint8 Tier-2 validation — seed 1/5 (voir stop=1020, max_duration=2000) ==="
uv run milabench run \
    --config benchmarks/retired/torchatari/phase3_c1_uint8_t2_s1.yaml \
    --select torchatari \
    --base $MILABENCH_BASE \
    --run-name phase3_c1_uint8_t2_s1

echo "=== Phase 3 C1 uint8 Tier-2 validation — seed 2/5 ==="
uv run milabench run \
    --config benchmarks/retired/torchatari/phase3_c1_uint8_t2_s2.yaml \
    --select torchatari \
    --base $MILABENCH_BASE \
    --run-name phase3_c1_uint8_t2_s2

echo "=== Phase 3 C1 uint8 Tier-2 validation — seed 3/5 ==="
uv run milabench run \
    --config benchmarks/retired/torchatari/phase3_c1_uint8_t2_s3.yaml \
    --select torchatari \
    --base $MILABENCH_BASE \
    --run-name phase3_c1_uint8_t2_s3

echo "=== Phase 3 C1 uint8 Tier-2 validation — seed 4/5 ==="
uv run milabench run \
    --config benchmarks/retired/torchatari/phase3_c1_uint8_t2_s4.yaml \
    --select torchatari \
    --base $MILABENCH_BASE \
    --run-name phase3_c1_uint8_t2_s4

echo "=== Phase 3 C1 uint8 Tier-2 validation — seed 5/5 ==="
uv run milabench run \
    --config benchmarks/retired/torchatari/phase3_c1_uint8_t2_s5.yaml \
    --select torchatari \
    --base $MILABENCH_BASE \
    --run-name phase3_c1_uint8_t2_s5

echo "=== DONE ==="
