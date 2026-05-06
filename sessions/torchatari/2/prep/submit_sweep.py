"""Generate YAML configs and sbatch scripts for the Tier-1 proxy sweep, then submit."""
import os, subprocess, textwrap

REPO = "/network/scratch/b/bouthilx/milabench/milabench"
BENCH_DIR = f"{REPO}/benchmarks/retired/torchatari"
PREP_DIR  = f"{REPO}/brdg-hackathon/sessions/torchatari/2/prep"
MILABENCH_BASE = "/network/scratch/b/bouthilx/milabench/results"

# --------------------------------------------------------------------------
# Candidate grid
# Each entry: (label, num_envs, num_steps, num_minibatches, update_epochs)
# Constraint: num_minibatches must divide num_envs*num_steps
# --------------------------------------------------------------------------
CANDIDATES = [
    # ── num_envs sweep (steps=128, mb=4, ep=4) ────────────────────────────
    ("e64_s128_m4_u4",    64,  128,  4, 4),
    ("e128_s128_m4_u4",  128,  128,  4, 4),   # default / baseline
    ("e256_s128_m4_u4",  256,  128,  4, 4),
    ("e512_s128_m4_u4",  512,  128,  4, 4),
    # ── num_steps sweep (envs=128, mb=4, ep=4) ────────────────────────────
    ("e128_s64_m4_u4",   128,   64,  4, 4),
    ("e128_s256_m4_u4",  128,  256,  4, 4),
    ("e128_s512_m4_u4",  128,  512,  4, 4),
    # ── num_minibatches sweep (envs=128, steps=128, ep=4) ─────────────────
    ("e128_s128_m2_u4",  128,  128,  2, 4),
    ("e128_s128_m8_u4",  128,  128,  8, 4),
    ("e128_s128_m16_u4", 128,  128, 16, 4),
    # ── update_epochs sweep (envs=128, steps=128, mb=4) ───────────────────
    ("e128_s128_m4_u1",  128,  128,  4, 1),
    ("e128_s128_m4_u2",  128,  128,  4, 2),
    ("e128_s128_m4_u8",  128,  128,  4, 8),
    # ── cross terms ───────────────────────────────────────────────────────
    ("e256_s256_m8_u4",  256,  256,  8, 4),   # more envs + longer rollout
    ("e512_s256_m8_u4",  512,  256,  8, 4),   # many envs + longer rollout
    ("e256_s128_m2_u4",  256,  128,  2, 4),   # more envs + fewer minibatches
    ("e512_s128_m2_u4",  512,  128,  2, 4),   # many envs + fewer minibatches
    ("e256_s128_m4_u8",  256,  128,  4, 8),   # more envs + more epochs
    ("e128_s256_m4_u8",  128,  256,  4, 8),   # longer rollout + more epochs
    ("e512_s128_m4_u8",  512,  128,  4, 8),   # many envs + more epochs
]

YAML_TEMPLATE = """\
torchatari:
  max_duration: 600
  inherits: _defaults
  definition: .
  install_variant: unpinned
  install_group: torch
  plan:
    method: per_gpu
  voir:
    options:
      stop: 200
      interval: "1s"
      skip: 5
  argv:
    --num-minibatches: {num_minibatches}
    --update-epochs: {update_epochs}
    --num-steps: {num_steps}
    --num-envs: {num_envs}
    --total-timesteps: 500000000
    --env-id: Breakout-v5
    --seed: 1
"""

SBATCH_TEMPLATE = """\
#!/bin/bash
#SBATCH --job-name=p2-{label}
#SBATCH --partition=long
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=256G
#SBATCH --time=0:30:00
#SBATCH --output={prep_dir}/sweep_{label}.slurm-%j.out
#SBATCH --error={prep_dir}/sweep_{label}.slurm-%j.err

set -uo pipefail
REPO={repo}
PREP={prep_dir}
CFG={bench_dir}/prep2_sweep_{label}.yaml
LOG=$PREP/sweep_{label}.log

cd "$REPO"
export MILABENCH_BASE={milabench_base}

{{
  echo "=== [{label} jobid=$SLURM_JOB_ID host=$(hostname) T=$(date -Is)] ==="
  nvidia-smi 2>&1 | grep -E "NVIDIA-SMI|Driver|L40|MiB" | head -5
  echo ""
  uv run milabench run \\
    --config "$CFG" \\
    --select torchatari \\
    --base "$MILABENCH_BASE" \\
    --run-name "prep2_sweep_{label}_${{SLURM_JOB_ID}}" 2>&1
  echo "exit=$?"
}} >> "$LOG" 2>&1
echo "Done: $LOG"
"""

job_ids = {}

for (label, num_envs, num_steps, num_minibatches, update_epochs) in CANDIDATES:
    # Verify divisibility
    batch_size = num_envs * num_steps
    assert batch_size % num_minibatches == 0, \
        f"{label}: batch_size={batch_size} not divisible by num_minibatches={num_minibatches}"

    # Write YAML config
    yaml_path = f"{BENCH_DIR}/prep2_sweep_{label}.yaml"
    with open(yaml_path, "w") as f:
        f.write(YAML_TEMPLATE.format(
            num_envs=num_envs, num_steps=num_steps,
            num_minibatches=num_minibatches, update_epochs=update_epochs,
        ))

    # Write sbatch script
    sbatch_path = f"{PREP_DIR}/sweep_{label}.sbatch"
    with open(sbatch_path, "w") as f:
        f.write(SBATCH_TEMPLATE.format(
            label=label, prep_dir=PREP_DIR, repo=REPO,
            bench_dir=BENCH_DIR, milabench_base=MILABENCH_BASE,
        ))

    # Submit
    result = subprocess.run(
        ["sbatch", sbatch_path],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        jid = result.stdout.strip().split()[-1]
        job_ids[label] = jid
        print(f"  {label:30s}  job {jid}")
    else:
        print(f"  {label:30s}  FAILED: {result.stderr.strip()}")

print(f"\nSubmitted {len(job_ids)}/{len(CANDIDATES)} jobs.")
print("Job IDs:", " ".join(job_ids.values()))
