#!/bin/bash
#SBATCH --job-name=p2r-e512_s256_m8_u4
#SBATCH --partition=long
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=256G
#SBATCH --time=0:48:00
#SBATCH --output=/network/scratch/b/bouthilx/milabench/milabench/brdg-hackathon/sessions/torchatari/2/prep/rerun_e512_s256_m8_u4.slurm-%j.out
#SBATCH --error=/network/scratch/b/bouthilx/milabench/milabench/brdg-hackathon/sessions/torchatari/2/prep/rerun_e512_s256_m8_u4.slurm-%j.err

set -uo pipefail
REPO=/network/scratch/b/bouthilx/milabench/milabench
PREP=/network/scratch/b/bouthilx/milabench/milabench/brdg-hackathon/sessions/torchatari/2/prep
CFG=/network/scratch/b/bouthilx/milabench/milabench/benchmarks/retired/torchatari/prep2r_sweep_e512_s256_m8_u4.yaml
LOG=$PREP/rerun_e512_s256_m8_u4.log

cd "$REPO"
export MILABENCH_BASE=/network/scratch/b/bouthilx/milabench/results

{
  echo "=== [RERUN e512_s256_m8_u4 jobid=$SLURM_JOB_ID host=$(hostname) T=$(date -Is)] ==="
  nvidia-smi 2>&1 | grep -E "NVIDIA-SMI|Driver|L40|MiB" | head -5
  echo ""
  uv run milabench run \
    --config "$CFG" \
    --select torchatari \
    --base "$MILABENCH_BASE" \
    --run-name "prep2r_sweep_e512_s256_m8_u4_${SLURM_JOB_ID}" 2>&1
  echo "exit=$?"
} >> "$LOG" 2>&1
echo "Done: $LOG"
