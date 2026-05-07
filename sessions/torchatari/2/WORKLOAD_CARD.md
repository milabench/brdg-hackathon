# Workload Card — torchatari

---

## 0) Session identity

- Workload name (short slug): `torchatari`
- Iteration id: `2`
- Session folder: `sessions/torchatari/2/`
- Date: 2026-05-04
- Summary: Reduce time-to-reach-target episodic return for PPO-Atari using envpool by improving per-step throughput.

---

## 1) Target workload

- Repo URL: `git@github.com:mila-iqia/milabench.git`
- Upstream base: `master @ 2e04211`
- Prepared branch: `hackathon-torchatari-2`
- Prepared-branch head commit: `e23ffee` (envpool 1.2.0 compatibility fix; see §11)
- Benchmark code path(s): `benchmarks/retired/torchatari/`
- Entry point: `benchmarks/retired/torchatari/main.py` (invoked via `milabench run`)
- Environment / dataset name: Breakout-v5 (Atari via envpool)
- Read-only reference code (must not modify unless explicitly approved):
  - `benchmarks/retired/torchatari/voirfile.py` — voir instrumentation and metric extraction
  - `config/retired.yaml` — benchmark registry entry
  - envpool library internals

---

## 2) Primary metric (the thing being optimized)

- Name: TTR (time-to-result)
- Precise definition:
  - Wall-clock time (seconds) from training start until `avg_episodic_return` first reaches or exceeds the target value declared in §10.2.
  - `avg_episodic_return` = rolling mean of undiscounted episodic return over the last 20 completed game episodes (lives=0 termination) across all parallel environments.
  - A run that does not reach the target within the Tier-2 benchmark window (§5) is counted as DNF (did not finish); its TTR is the wall-clock duration of the full window.
- Unit: seconds
- Where the value appears: derived from TensorBoard event files under `$MILABENCH_BASE/runs/<run_name>/`, scalar tag `charts/avg_episodic_return`
- Extraction recipe:
  ```python
  from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
  import os, sys
  run_dir = sys.argv[1]
  target = float(sys.argv[2])
  ea = EventAccumulator(run_dir); ea.Reload()
  events = ea.Scalars('charts/avg_episodic_return')
  # wall_time of first event where value >= target
  ttr = next((e.wall_time - events[0].wall_time for e in events if e.value >= target), None)
  print(ttr if ttr is not None else 'DNF')
  ```

**Tier-1 throughput proxy** (used for short-run screening only — not the primary metric):
- `rate` (items/s) from voir JSON: lines matching `'task': 'train'` and `'rate'` in the milabench run log.
- Extraction: `grep "'task': 'train'" <log> | grep "'rate'"` → parse floats, skip first 5, take median.
- One "item" = one environment step = 1/num_envs fraction of a PPO iteration's data.

---

## 3) Quality metric (the constraint that must be preserved)

- Name: `avg_episodic_return`
- Precise definition: rolling mean of undiscounted episodic return over the last 20 completed game episodes across all parallel environments (same as §2's TTR criterion)
- Eval protocol:
  - Tracked throughout training, not at a fixed evaluation point
  - Reported each time an episode ends with lives=0 (game over)
  - Seeds: 1 (fixed, via `--seed`); stochastic policy (sampling from Categorical)
  - Horizon: full episode (up to environment's natural termination)
- Where it appears: TensorBoard event files, tag `charts/avg_episodic_return`

---

## 4) Quality tolerance

**Tolerance**: `avg_episodic_return` must stay within **−2 · baseline_std** of the baseline mean.

Rationale: PPO on Atari at this training horizon is highly stochastic. A noise-aware tolerance prevents rejecting valid optimizations due to run-to-run variance while still catching genuine regressions.

---

## 5) Benchmark window

**Fixed wall-clock time**:
- Tier-1 (short run, throughput proxy): **120 s** (2 min)
- Tier-2 (full run, TTR): **900 s** (15 min)

Rationale: 15 min at ~8000 steps/sec (12 CPUs, num_envs=128) processes ~7.2M environment steps — sufficient to show meaningful learning on Breakout. 2-min Tier-1 gives ≈55–60 voir rate observations (rate ≈1 obs/iter, iter ≈2 s at this hardware/HP config; workload-specific adjustment per RULES §8: threshold ≥60 obs is approximately met and recorded as adjustment).

Notes on short-run vs TTR protocol:
- Tier-1 measures the throughput proxy (`rate` items/s from voir) and uses it to screen candidates.
- Tier-2 measures TTR against the target quality from §10.2 over a 15-min window.
- A candidate that improves throughput but does not reduce TTR is not a win (RULES §3).

---

## 6) Setup and entry command(s)

### Install / environment setup

```bash
# From milabench repo root on branch hackathon-torchatari-2:
export MILABENCH_BASE=/network/scratch/b/bouthilx/milabench/results

# Install torchatari dependencies into the milabench venv:
uv run milabench install \
    --config benchmarks/retired/torchatari/dev.yaml \
    --base $MILABENCH_BASE
```

System-level prerequisites:
- NVIDIA driver ≥ 580.95.05, CUDA 13.0
- Python 3.12.11 (milabench venv at `$MILABENCH_BASE/venv/torch`)
- PyTorch 2.10.0+cu130

### Direct invocation
```bash
# For quick local testing (no milabench wrapper):
source $MILABENCH_BASE/venv/torch/bin/activate
cd benchmarks/retired/torchatari
python main.py \
    --num-envs 128 --num-steps 128 --num-minibatches 4 --update-epochs 4 \
    --total-timesteps 500000000 --env-id Breakout-v5
```

### Wrapper / milabench invocation (standard — used for all prep and session runs)
```bash
# Submitted via sbatch on the Mila cluster:
#   sbatch --partition=long --gres=gpu:l40s:1 --cpus-per-task=12 --mem=256G \
#          --time=<HH:MM:SS> <script.sh>
# Inside the script:
export MILABENCH_BASE=/network/scratch/b/bouthilx/milabench/results
uv run milabench run \
    --config benchmarks/retired/torchatari/<run_config.yaml> \
    --select torchatari \
    --base $MILABENCH_BASE \
    --run-name <run_name>
```

### Required environment variables
- `MILABENCH_BASE=/network/scratch/b/bouthilx/milabench/results`

### Working directory
- Milabench repo root: `/network/scratch/b/bouthilx/milabench/milabench`

---

## 7) Allowed edits (what the agent *may* change)

Anything that does not alter the nature of the Atari environment simulation or the PPO learning algorithm. Specifically:

- Engineering HPs: `num_envs`, `num_steps`, `num_minibatches`, `update_epochs`
- CPU thread / worker allocation
- Observation buffer layout (dtype, pinning, async transfers)
- Training loop iteration mechanics (rollout collection, GAE computation, minibatch shuffling)
- Data movement (HtoD/DtoH transfers, memory formats)
- Compilation flags (`torch.compile`, inductor settings)
- Log / checkpoint frequency (with `RULES §15` reporting)
- Any code changes that demonstrably speed up the benchmark without changing what the algorithm computes

---

## 8) Disallowed edits (semantic surfaces — do NOT modify unless explicitly approved)

- envpool library internals (Atari simulation, observation generation)
- `RecordEpisodeStatistics` wrapper — episodic return accounting
- PPO algorithm structure: policy gradient loss, value loss, entropy bonus, advantage normalization, GAE computation
- `voirfile.py` — metric extraction instrumentation
- `config/retired.yaml` — benchmark registry

---

## 9) Hardware expectations

- GPU model and count: 1× NVIDIA L40S
- Required GPU memory: ~1.2 GB observed (model + buffers at num_envs=128); L40S has 46 GB
- CPU / RAM minimums: 12 CPUs, 256 GB RAM
- Isolation / pinning requirements: exclusive GPU allocation (1 job per GPU); no clock pinning required

---

## 10) HP lock (filled by preparer-agent in Prep Phase 2)

### 10.1 Locked HP configuration

- Winner candidate label: **e256_s32_m32_u4**
- `hp_values_json`:

```json
{"num_envs": 256, "num_steps": 32, "num_minibatches": 32, "update_epochs": 4}
```

- Derived quantities: `batch_size = 256×32 = 8192`, `minibatch_size = 8192/32 = 256`
- TTR improvement vs default: **−70%** (255.7 s vs 841.8 s baseline)

- Rationale: Extended multi-phase HPO (Phases 2B–2E, ~300 Tier-2 runs across 77 configs × 3 seeds):
  1. **Gradient update density drives TTR**: The key driver is `grad_steps/sec = (1/iter_time) × update_epochs × num_minibatches`. Voir rate (throughput) is anti-correlated with TTR when num_envs is increased without compensating num_minibatches — more envs means fewer iterations/sec without more gradient steps per rollout.
  2. **minibatch_size is the primary scalar predictor**: Across all tested configs, TTR is minimised at mb≈256. Larger mb (≥512) → too few gradient steps per sample; smaller mb (≤64) → gradient noise causes training instability (mb=32 DNF).
  3. **Interior optimum in s and m**: Phase 2E confirmed that s=16 and s=64 are both slower than s=32 at mb=256, and m=16 and m=64 are both slower than m=32 — so (s=32, m=32) is a genuine interior minimum, not a boundary artifact.
  4. **num_envs=256 at grid boundary**: Larger e was not explored (would require e=512 × s=32 × m=64 for equivalent mb=256), but the marginal gain is expected to be within seed variance (±8% CV at e=256). Accepted as converged.

  **Warning for session-agents**: voir rate (items/s) is NOT a reliable Tier-1 proxy for TTR when `num_envs` or `num_steps` is varied. Use only when both are held fixed relative to the locked HP config.

### 10.2 Target quality level

**Target**: mean end-of-window `avg_episodic_return` across the default-HP full runs = **94.683**.
- Seeds 1/2/3 end-of-window (900 s) avg_episodic_return: 113.750 / 64.850 / 105.450
- Mean = 94.683, std = 26.168 (N=3)
- TensorBoard dirs: Breakout-v5__main__1__1777990899, __2__1777990899, __3__1777990899

### 10.3 Tier-2 baseline (default-HP TTR, target = 94.683)

- Prep `experiment_id`: prep2_ttr_baseline_s{1,2,3}_{9464176,9464177,9464178}
- N: 3
- TTR median: **841.8 s**
- TTR range [min, max]: [700.2, 900.0] s  (seed=2 DNF — max quality 93.4 just below target)
- TTR CV: 12.6%
- Quality at end of window: mean 94.683, std 26.168

### 10.3b Tier-2 winner-HP TTR (e256_s32_m32_u4, target = 94.683)

- Prep `experiment_id`: p2d_t2_e256_s32_m32_u4_s{1,2,3}_{9474759,9474760,9474761}
- N: 3
- TTR seed 1 / 2 / 3: 267.1 s / 224.8 s / 255.7 s
- TTR median: **255.7 s**
- TTR range [min, max]: [224.8, 267.1] s
- TTR CV: 8.8%  (sample std=21.9 s, mean=249.2 s)
- n_dnf: 0

### 10.4 Tier-1 baseline (short-run throughput proxy)

- Short-run protocol: voir rate (items/s), skip=5, stop=200, interval=1s; ~200 usable observations per run
- N: 4 (sanity_s1 job 9457687, sweep_default_s1 job 9464143, short_s2 job 9464174, short_s3 job 9464175)
- Primary-metric median: **7727.6 items/s**
- Primary-metric CV: 0.6%
- Individual values: 7722.1, 7722.0, 7733.0, 7815.5 items/s
- Note: Tier-1 rate not collected for winner HP (e256_s32_m32_u4). voir rate is NOT a reliable proxy for TTR when num_envs or num_steps differ from default — winner was selected via direct Tier-2 TTR measurement only.

### 10.5 Prep-branch head commit (Tier-2 baseline provenance)

`e23ffee` (same as §1 prepared-branch head commit)

---

## 11) Known caveats and prior art

- **CPU count dominates throughput**: iteration 1 found 6 CPUs → ~2000 items/s; 12 CPUs → ~8000 items/s (4× speedup from CPU allocation alone; envpool Atari sim is CPU-bound).
- **Iteration 1 HP winner**: num_envs=128, 12 CPUs. Not yet on master.
- **uint8 obs optimization** (commit `a0b4241` on `agent_claude-sonnet_torchatari_opt`, not on master): keeping obs buffer as uint8 through HtoD and casting to float on GPU — validated in iter 1 but not yet merged. Iteration 2 prep starts from clean master so this will be re-evaluated or re-applied.
- **Attempted and reverted in iteration 1**: `torch.compile` on CNN backbone, async envpool rollout path, pinned CPU staging buffers, numpy loop for episode terminations — all showed regressions or were inconclusive.
- **Atari training is highly stochastic at short horizons**: avg_episodic_return at 7.2M steps (15 min) is noisy; expect high CV on quality metric.
- **envpool 1.2.0 compatibility**: `main.py` on master asserts `isinstance(envs.action_space, gym.spaces.Discrete)` which fails with envpool 1.2.0 (returns `gymnasium.spaces.Discrete`). Fixed on prep branch `e23ffee` via `hasattr(envs.action_space, 'n')`. Session-agents branch from `e23ffee` so this is already patched.
- **Pre-declared Δ_min**: not set (session-agents set their own per RULES §7).
- **Throughput proxy NOT reliable for num_envs changes** (iteration 2 finding): Increasing num_envs from 128→256 gave +16.5% voir rate but ALL 3 TTR validation seeds were DNF (max quality 46–49 vs target 94.683). More envs → more env steps/s via CPU parallelism, but also fewer PPO update iterations per second → slower learning convergence. Session-agents should NOT use voir rate as a proxy for TTR when varying num_envs.
- **HP sweep conclusion** (iteration 2): 20-candidate sweep showed no HP change improves TTR within the 900-s benchmark window. Session-agents should focus on **code-level optimizations** for TTR improvement: uint8 obs buffer (validated iter 1), compute scheduling, overlapping rollout/update.

---

## 12) Verification checklist (human fills before session start)

- [ ] All sections above filled; no `___` placeholders remain.
- [ ] Exactly one tolerance option chosen in §4.
- [ ] Exactly one benchmark window chosen in §5.
- [ ] Baseline command in §6 runs end-to-end from a clean environment before the session.
- [ ] Primary metric (§2) and quality metric (§3) are mechanically extractable from the baseline output using the recipe given.
- [ ] Allowed / disallowed edits (§7, §8) are explicit and non-overlapping.
- [x] §10 HP-lock section filled: `hp_values_json`, target quality, Tier-2 baseline (median / range / CV / N), Tier-1 baseline (median / CV / N / protocol). The winning prep `experiment_id` points at a row in `prep/prep_results.csv`.
- [ ] §10.5 prep-branch head commit matches the `Prepared-branch head commit` in §1.
