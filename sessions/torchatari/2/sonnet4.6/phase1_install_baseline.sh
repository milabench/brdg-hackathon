#!/bin/bash
#SBATCH --partition=long
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=256G
#SBATCH --time=01:30:00
#SBATCH --job-name=torchatari_p1_s46
#SBATCH --output=/home/mila/r/rygaards/proj/milabench/brdg-hackathon/sessions/torchatari/2/sonnet4.6/phase1_install_baseline.out

set -e

MILABENCH_REPO=/home/mila/r/rygaards/proj/milabench
export MILABENCH_BASE=/network/scratch/r/rygaards/milabench/base
SESSION_ARTIFACTS=$MILABENCH_REPO/brdg-hackathon/sessions/torchatari/2/sonnet4.6/artifacts

cd $MILABENCH_REPO

echo "=== PREFLIGHT CAPTURE ===" | tee $SESSION_ARTIFACTS/notes/gpu_preflight.txt
date | tee -a $SESSION_ARTIFACTS/notes/gpu_preflight.txt
nvidia-smi -q 2>&1 | tee -a $SESSION_ARTIFACTS/notes/gpu_preflight.txt

echo "" | tee -a $SESSION_ARTIFACTS/notes/gpu_preflight.txt
echo "=== GPU CSV SUMMARY ===" | tee -a $SESSION_ARTIFACTS/notes/gpu_preflight.txt
nvidia-smi --query-gpu=name,driver_version,memory.total,clocks.gr,clocks.mem,persistence_mode,power.draw,temperature.gpu \
           --format=csv 2>&1 | tee -a $SESSION_ARTIFACTS/notes/gpu_preflight.txt

echo "" | tee -a $SESSION_ARTIFACTS/notes/gpu_preflight.txt
echo "=== RELEVANT ENV VARS ===" | tee -a $SESSION_ARTIFACTS/notes/gpu_preflight.txt
for v in CUDA_VISIBLE_DEVICES CUDA_DEVICE_ORDER TORCH_COMPILE_DEBUG TORCHINDUCTOR_CACHE_DIR \
         PYTORCH_CUDA_ALLOC_CONF OMP_NUM_THREADS MKL_NUM_THREADS MILABENCH_BASE SLURM_JOB_ID \
         SLURM_NODELIST SLURM_CPUS_ON_NODE; do
    echo "$v=${!v:-<unset>}" | tee -a $SESSION_ARTIFACTS/notes/gpu_preflight.txt
done

echo "" | tee -a $SESSION_ARTIFACTS/notes/gpu_preflight.txt
echo "=== PYTHON / FRAMEWORK VERSIONS ===" | tee -a $SESSION_ARTIFACTS/notes/gpu_preflight.txt
source $MILABENCH_BASE/venv/torch/bin/activate
python --version 2>&1 | tee -a $SESSION_ARTIFACTS/notes/gpu_preflight.txt
python -c "
import torch, numpy, triton
print('torch:', torch.__version__)
print('cuda_build:', torch.version.cuda)
print('cuda_available:', torch.cuda.is_available())
print('cudnn:', torch.backends.cudnn.version())
print('numpy:', numpy.__version__)
print('triton:', triton.__version__)
" 2>&1 | tee -a $SESSION_ARTIFACTS/notes/gpu_preflight.txt
deactivate

echo "" | tee -a $SESSION_ARTIFACTS/notes/gpu_preflight.txt
echo "=== CONCURRENT GPU PROCESSES ===" | tee -a $SESSION_ARTIFACTS/notes/gpu_preflight.txt
nvidia-smi pmon -c 1 2>&1 | tee -a $SESSION_ARTIFACTS/notes/gpu_preflight.txt

echo ""
echo "=== STEP 1: milabench install ==="
uv run milabench install \
    --config benchmarks/retired/torchatari/dev.yaml \
    --base $MILABENCH_BASE

echo ""
echo "=== STEP 2: Phase 1 baseline run (locked HPs: e256 s32 m32 u4, seed 1) ==="
uv run milabench run \
    --config benchmarks/retired/torchatari/p2d_t2_e256_s32_m32_u4_s1.yaml \
    --select torchatari \
    --base $MILABENCH_BASE \
    --run-name phase1_baseline_s1

echo ""
echo "=== STEP 3: Find TensorBoard event files ==="
find $MILABENCH_BASE/runs/phase1_baseline_s1/ -name "events.out.*" 2>/dev/null \
    | tee $SESSION_ARTIFACTS/notes/tensorboard_paths.txt || true
find $MILABENCH_REPO -name "events.out.*" -newer $MILABENCH_REPO/brdg-hackathon/sessions/torchatari/2/sonnet4.6/phase1_install_baseline.sh 2>/dev/null \
    | tee -a $SESSION_ARTIFACTS/notes/tensorboard_paths.txt || true

echo ""
echo "=== DONE ==="
