#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 6 ]]; then
  echo "Usage: $0 <phase_label> <tier> <candidate> <run_name> <job_script> <job_log_prefix> [override ...]" >&2
  exit 2
fi

PHASE_LABEL="$1"
TIER="$2"
CANDIDATE="$3"
RUN_NAME="$4"
JOB_SCRIPT="$5"
JOB_LOG_PREFIX="$6"
shift 6

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../../.." && pwd)"
VENV_PATH="$ROOT_DIR/milabench/base/venv/torch"
MILABENCH_BIN="$VENV_PATH/bin/milabench"
EXTRACTOR="$ROOT_DIR/brdg-hackathon/sessions/torchatari/1/codex/artifacts/tools/extract_run_metrics.py"
CONFIG_PATH="${MILABENCH_CONFIG_PATH:-benchmarks/retired/torchatari/dev.yaml}"

OVERRIDE_ARGS=()
for o in "$@"; do
  OVERRIDE_ARGS+=( "--override" "$o" )
done

mkdir -p "$(dirname "$JOB_SCRIPT")"
cat > "$JOB_SCRIPT" <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd "$ROOT_DIR"
export VIRTUAL_ENV="$VENV_PATH"
export PATH="\$VIRTUAL_ENV/bin:\$PATH"
export MILABENCH_GPU_ARCH=cuda
export PYTHONUNBUFFERED=1

"$MILABENCH_BIN" run \\
  --base milabench/base \\
  --config "$CONFIG_PATH" \\
  --select torchatari \\
  --use-current-env \\
  --no-report \\
  --dash no \\
  --noterm \\
  --run-name "$RUN_NAME" \\
  --repeat 1 \\
  ${OVERRIDE_ARGS[@]+"${OVERRIDE_ARGS[@]}"}

RUN_DIR="$ROOT_DIR/milabench/base/runs/$RUN_NAME"
TB_ROOT="$ROOT_DIR/benchmarks/retired/torchatari/runs"
METRIC_JSON="$ROOT_DIR/brdg-hackathon/sessions/torchatari/1/codex/artifacts/benchmarks/${RUN_NAME}.metrics.json"
"$VENV_PATH/bin/python" "$EXTRACTOR" --run-dir "\$RUN_DIR" --tb-root "\$TB_ROOT" --output "\$METRIC_JSON" --warmup-skip 5
EOF
chmod +x "$JOB_SCRIPT"

SBATCH_OUT="${JOB_LOG_PREFIX}.out"
SBATCH_ERR="${JOB_LOG_PREFIX}.err"
JOB_ID="$(sbatch --parsable \
  -c 6 --mem=32G --gres=gpu:l40s:1 --partition=unkillable --time=0:20:00 \
  -J "${PHASE_LABEL}_${TIER}_${CANDIDATE}" \
  -o "$SBATCH_OUT" \
  -e "$SBATCH_ERR" \
  "$JOB_SCRIPT")"

echo "$JOB_ID"
