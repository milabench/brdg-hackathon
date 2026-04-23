#!/usr/bin/env bash
set -euo pipefail
cd "/home/mila/r/rygaards/proj/milabench"
export VIRTUAL_ENV="/home/mila/r/rygaards/proj/milabench/milabench/base/venv/torch"
export PATH="$VIRTUAL_ENV/bin:$PATH"
export MILABENCH_GPU_ARCH=cuda
export PYTHONUNBUFFERED=1

"/home/mila/r/rygaards/proj/milabench/milabench/base/venv/torch/bin/milabench" run \
  --base milabench/base \
  --config benchmarks/retired/torchatari/dev.yaml \
  --select torchatari \
  --use-current-env \
  --no-report \
  --dash no \
  --noterm \
  --run-name "torchatari_p1_baseline_fix1_20260422_115505" \
  --repeat 1 \
  

RUN_DIR="/home/mila/r/rygaards/proj/milabench/milabench/base/runs/torchatari_p1_baseline_fix1_20260422_115505"
TB_ROOT="/home/mila/r/rygaards/proj/milabench/benchmarks/retired/torchatari/runs"
METRIC_JSON="/home/mila/r/rygaards/proj/milabench/brdg-hackathon/sessions/torchatari/1/codex/artifacts/benchmarks/torchatari_p1_baseline_fix1_20260422_115505.metrics.json"
"/home/mila/r/rygaards/proj/milabench/milabench/base/venv/torch/bin/python" "/home/mila/r/rygaards/proj/milabench/brdg-hackathon/sessions/torchatari/1/codex/artifacts/tools/extract_run_metrics.py" --run-dir "$RUN_DIR" --tb-root "$TB_ROOT" --output "$METRIC_JSON" --warmup-skip 5
