#!/bin/bash
#SBATCH --job-name=torchatari-phase1-baseline
#SBATCH --partition=unkillable
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=6
#SBATCH --mem=32G
#SBATCH --time=00:15:00
#SBATCH --output=/network/scratch/b/bouthilx/milabench/milabench/brdg-hackathon/sessions/torchatari/1/claude-sonnet/artifacts/benchmarks/phase1_baseline.slurm-%j.out
#SBATCH --error=/network/scratch/b/bouthilx/milabench/milabench/brdg-hackathon/sessions/torchatari/1/claude-sonnet/artifacts/benchmarks/phase1_baseline.slurm-%j.err

set -uo pipefail

REPO=/network/scratch/b/bouthilx/milabench/milabench
ARTIF=$REPO/brdg-hackathon/sessions/torchatari/1/claude-sonnet/artifacts
GPU_PRE=$ARTIF/notes/gpu_preflight.txt
RUN_LOG=$ARTIF/benchmarks/phase1_baseline.log

cd "$REPO"

# --- GPU preflight (captured once per unique GPU-node jobid) ---
{
  echo "=== [GPU-PREFLIGHT jobid=$SLURM_JOB_ID host=$(hostname)] ==="
  date -u
  echo "--- nvidia-smi ---"
  nvidia-smi 2>&1 | head -30
  echo "--- nvcc ---"
  nvcc --version 2>&1 | head -5 || echo "(nvcc not on PATH)"
  echo "--- modulepath-listing (if any) ---"
  module avail cuda 2>&1 | head -20 || true
} >> "$GPU_PRE"

# --- Reuse an existing torch venv if present, otherwise let milabench create it ---
export MILABENCH_BASE=/network/scratch/b/bouthilx/milabench/results
export MILABENCH_CONFIG="$REPO/benchmarks/retired/torchatari/dev.yaml"

# Pick the torch venv milabench installs into
VENV=$MILABENCH_BASE/venv/torch

{
  echo ""
  echo "=== [INSTALL-PROBE host=$(hostname)] ==="
  if [ -f "$VENV/bin/python" ]; then
    "$VENV/bin/python" -c 'import torch,sys; print("venv-torch:",torch.__version__,"cuda:",torch.version.cuda)' 2>&1 | head -3
    "$VENV/bin/python" -c 'import envpool; print("venv-envpool:",envpool.__version__)' 2>&1 | head -3 || echo "envpool missing from venv — install needed"
  else
    echo "torch venv not yet created at $VENV — install will create it"
  fi
} >> "$GPU_PRE"

# --- Install torchatari env (idempotent; fast if already installed) ---
{
  echo ""
  echo "=== [INSTALL host=$(hostname) T=$(date -Is)] ==="
  uv run milabench install \
    --config "$MILABENCH_CONFIG" \
    --select torchatari \
    --base "$MILABENCH_BASE" 2>&1
  echo "install exit=$?"
} >> "$RUN_LOG"

# --- Prepare (should be a no-op for torchatari; safe to call) ---
{
  echo ""
  echo "=== [PREPARE host=$(hostname) T=$(date -Is)] ==="
  uv run milabench prepare \
    --config "$MILABENCH_CONFIG" \
    --select torchatari \
    --base "$MILABENCH_BASE" 2>&1 || true
  echo "prepare exit=$?"
} >> "$RUN_LOG"

# --- Run the benchmark (Phase 1 baseline — default voir stop=20, smoke check) ---
{
  echo ""
  echo "=== [RUN host=$(hostname) T=$(date -Is)] ==="
  uv run milabench run \
    --config "$MILABENCH_CONFIG" \
    --select torchatari \
    --base "$MILABENCH_BASE" \
    --run-name phase1_baseline_${SLURM_JOB_ID} 2>&1
  echo "run exit=$?"
} >> "$RUN_LOG"

# --- Post-run capture: where milabench wrote results ---
{
  echo ""
  echo "=== [POST T=$(date -Is)] ==="
  echo "MILABENCH_BASE contents:"
  ls -la "$MILABENCH_BASE/runs/" 2>&1 | tail -10
  LATEST=$(ls -td "$MILABENCH_BASE"/runs/phase1_baseline_* 2>/dev/null | head -1)
  if [ -n "$LATEST" ]; then
    echo "Latest run dir: $LATEST"
    ls -la "$LATEST" | head -20
  fi
} >> "$RUN_LOG"

echo "[$(date -Is)] phase1 baseline sbatch complete"
