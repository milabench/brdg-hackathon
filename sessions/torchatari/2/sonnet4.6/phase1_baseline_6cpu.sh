#!/bin/bash
#SBATCH --partition=unkillable
#SBATCH --gres=gpu:l40s:1
#SBATCH -c 6
#SBATCH --job-name=torchatari_p1b_s46
#SBATCH --output=/home/mila/r/rygaards/proj/milabench/brdg-hackathon/sessions/torchatari/2/sonnet4.6/phase1_baseline_6cpu.out

set -e

MILABENCH_REPO=/home/mila/r/rygaards/proj/milabench
export MILABENCH_BASE=/network/scratch/r/rygaards/milabench/base
SESSION_ARTIFACTS=$MILABENCH_REPO/brdg-hackathon/sessions/torchatari/2/sonnet4.6/artifacts

cd $MILABENCH_REPO

echo "=== PREFLIGHT CAPTURE (6-CPU re-run) ===" | tee $SESSION_ARTIFACTS/notes/gpu_preflight_6cpu.txt
date | tee -a $SESSION_ARTIFACTS/notes/gpu_preflight_6cpu.txt
nvidia-smi -q 2>&1 | tee -a $SESSION_ARTIFACTS/notes/gpu_preflight_6cpu.txt
echo "" | tee -a $SESSION_ARTIFACTS/notes/gpu_preflight_6cpu.txt
echo "=== CPU INFO ===" | tee -a $SESSION_ARTIFACTS/notes/gpu_preflight_6cpu.txt
echo "SLURM_CPUS_ON_NODE=$SLURM_CPUS_ON_NODE" | tee -a $SESSION_ARTIFACTS/notes/gpu_preflight_6cpu.txt
echo "nproc=$(nproc)" | tee -a $SESSION_ARTIFACTS/notes/gpu_preflight_6cpu.txt

echo ""
echo "=== Phase 1 baseline (6 CPUs, unkillable) — locked HPs e256 s32 m32 u4 seed 1 ==="
uv run milabench run \
    --config benchmarks/retired/torchatari/p2d_t2_e256_s32_m32_u4_s1.yaml \
    --select torchatari \
    --base $MILABENCH_BASE \
    --run-name phase1_baseline_s1_6cpu

echo ""
echo "=== Find TensorBoard events ==="
find $MILABENCH_REPO/benchmarks/retired/torchatari/runs/ -name "events.out.*" \
    -newer $SESSION_ARTIFACTS/notes/gpu_preflight_6cpu.txt 2>/dev/null \
    | tee $SESSION_ARTIFACTS/notes/tensorboard_paths_6cpu.txt || true

echo "=== DONE ==="
