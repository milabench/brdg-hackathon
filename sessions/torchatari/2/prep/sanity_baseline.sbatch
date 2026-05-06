#!/bin/bash
#SBATCH --job-name=torchatari-p2-sanity
#SBATCH --partition=long
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=256G
#SBATCH --time=0:10:00
#SBATCH --output=/network/scratch/b/bouthilx/milabench/milabench/brdg-hackathon/sessions/torchatari/2/prep/sanity_baseline.slurm-%j.out
#SBATCH --error=/network/scratch/b/bouthilx/milabench/milabench/brdg-hackathon/sessions/torchatari/2/prep/sanity_baseline.slurm-%j.err

set -uo pipefail

REPO=/network/scratch/b/bouthilx/milabench/milabench
PREP=/network/scratch/b/bouthilx/milabench/milabench/brdg-hackathon/sessions/torchatari/2/prep
RUN_LOG=$PREP/baseline_capture.txt
CFG=$REPO/benchmarks/retired/torchatari/prep2_sanity.yaml

cd "$REPO"
export MILABENCH_BASE=/network/scratch/b/bouthilx/milabench/results

{
  echo "=== [SANITY-BASELINE jobid=$SLURM_JOB_ID host=$(hostname) T=$(date -Is)] ==="
  nvidia-smi 2>&1 | head -20
  echo ""
  echo "=== [VERSIONS T=$(date -Is)] ==="
  $MILABENCH_BASE/venv/torch/bin/python -c "
import torch, sys
print('python:', sys.version.split()[0])
print('torch:', torch.__version__)
print('cuda:', torch.version.cuda)
"
  echo ""
  echo "=== [RUN host=$(hostname) T=$(date -Is)] ==="
  uv run milabench run \
    --config "$CFG" \
    --select torchatari \
    --base "$MILABENCH_BASE" \
    --run-name "prep2_sanity_${SLURM_JOB_ID}" 2>&1
  echo "run exit=$?"
  echo ""
  echo "=== [POST T=$(date -Is)] ==="
  LATEST=$(ls -td "$MILABENCH_BASE"/runs/prep2_sanity_* 2>/dev/null | head -1)
  if [ -n "$LATEST" ]; then
    echo "Run dir: $LATEST"
    ls -la "$LATEST" | head -10
    echo ""
    echo "=== [TENSORBOARD EVENTS] ==="
    find "$LATEST" -name "events.out.tfevents.*" 2>/dev/null | head -5
  fi
} >> "$RUN_LOG" 2>&1

echo "Sanity baseline complete. Log: $RUN_LOG"
