#!/usr/bin/env bash
set -euo pipefail
cd "/home/mila/r/rygaards/proj/milabench"
{
  echo "# Preflight capture via SBATCH"
  echo "# Timestamp (UTC): \"2026-04-22T17:38:14Z""
  echo
  echo "## Host and OS"
  echo "uname -a:"; uname -a
  echo
  echo "hostname:"; hostname
  echo
  echo "## Date/time"
  echo "UTC: \"2026-04-22T17:38:14Z""
  echo "Local: \"
  echo
  echo "## GPU state"
  echo "nvidia-smi -q:"; nvidia-smi -q
  echo
  echo "nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu,temperature.gpu --format=csv,noheader:"
  nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu,temperature.gpu --format=csv,noheader
  echo
  echo "nvidia-smi --query-compute-apps=pid,process_name,gpu_uuid,used_memory --format=csv,noheader:"
  nvidia-smi --query-compute-apps=pid,process_name,gpu_uuid,used_memory --format=csv,noheader || true
  echo
  echo "## CPU / RAM"
  echo "nproc:"; nproc
  echo
  echo "free -h:"; free -h
  echo
  echo "## Relevant env vars"
  env | rg "^(CUDA_VISIBLE_DEVICES|CUDA_DEVICE_ORDER|XLA_FLAGS|XLA_PYTHON_CLIENT_|TORCH_COMPILE_|TORCHINDUCTOR_|PYTORCH_CUDA_ALLOC_CONF|OMP_NUM_THREADS|MKL_NUM_THREADS|MILABENCH_DIR_DATA|MILABENCH_CONFIG)=" || true
  echo
  echo "## Framework/tool versions"
  echo "python (system):"; python3 --version || true
  echo "python (milabench/base/venv/torch):"; milabench/base/venv/torch/bin/python --version || true
  echo
  echo "pip freeze (milabench/base/venv/torch):"
  milabench/base/venv/torch/bin/pip freeze || true
  echo
  echo "## Repo state"
  echo "workload repo:"; git rev-parse HEAD; git status --short || true
  echo
  echo "brdg-hackathon repo:"; git -C brdg-hackathon rev-parse HEAD; git -C brdg-hackathon status --short || true
} > "brdg-hackathon/sessions/torchatari/1/codex/artifacts/notes/preflight.sbatch.20260422_133814.txt"
