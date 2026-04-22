# Workload Card — torchatari

This file declares the **workload-specific** parameters for the hackathon session. The
generic protocol (`playbook/`) and the human guide (root `README.md`) reference this
card for everything workload-specific, so those files stay workload-agnostic and
reusable across sessions.

**Location.** This file in `workload-template/` is the blank template. The
**preparer-agent** copies it to `sessions/<workload>/<iteration>/WORKLOAD_CARD.md`
and fills it under the human preparer's supervision before any optimisation
session begins (see `workload-template/AGENT_HANDOFF.md` for the agent's flow
and `workload-template/README.md` for the human's). That filled copy is
shared read-only across every `<agent-name>/` subfolder in the iteration;
session-running agents never modify it.

Fill this file **before any session begins**. The session-agent reads it first;
the operator verifies it at session start.

---

## 0) Session identity

- Workload name (short slug): `torchatari`
- Iteration id (e.g. `1`, `2`): `1`
- Session folder: `sessions/torchatari/1/`
- Date: `2026-04-22`
- Summary (one sentence — what is being optimized, in plain language):
  PPO on Atari Breakout-v5 (CleanRL reference implementation under milabench's
  per-GPU plan with envpool vectorized envs); goal is to maximize environment-step
  throughput while preserving training correctness.

---

## 1) Target workload

- Repo URL + commit (the state from which the session starts):
  `git@github.com:milabench/milabench.git` @ `f323850` (branch `hackathon_torchatari_v1`,
  based on `master` @ `09a856f` + two pin commits: `install_variant` typo fix and
  baseline-HP lock to CleanRL defaults).
- Benchmark code path(s) (relative to repo root):
  `benchmarks/retired/torchatari/` — note this pipeline lives under `retired/` but is
  intact and runnable via `config/retired.yaml`.
- Entry point (script / module that the baseline command invokes):
  `benchmarks/retired/torchatari/main.py` (driven via milabench through
  `benchfile.py` → `Torchatari(Package)` → `main.py`, with voir instrumentation
  in `voirfile.py`).
- Environment / dataset name: `Breakout-v5` (Atari via `envpool`; falls back to
  stable-baselines3 `make_vec_env` if envpool isn't importable).
- Read-only reference code (files the agent may read for context but **must not modify**
  unless explicitly approved):
  - **None.** Per preparer steer, any surface may be modified provided the change
    is mathematically equivalent to the PPO + Atari baseline training dynamics in
    expectation. Non-equivalent changes are **SEMANTIC CHANGES** (§8) and require
    explicit approval + stronger quality checks (`RULES §11`).

---

## 2) Primary metric (the thing being optimized)

- Name: `rate` (env-steps per second), as reported by milabench's
  `BenchObserver` (from `benchmate.observer`).
- Precise definition:
  - What counts as one "step" / sample / token / iteration?
    One "step" = one environment step aggregated across all vectorized envs.
    `voirfile.py` declares `batch_size_fn(x) = step_per_iteration = num_envs *
    num_steps`, so each PPO rollout iteration (one outer `for iteration in
    iterations:` pass in `main.py`) contributes one rate measurement of
    `num_envs * num_steps` env-steps divided by the iteration's wall-clock time.
    With the locked HPs (num_envs=8, num_steps=128), each observation covers
    1024 env-steps.
  - Are units aggregated across vectorized / parallel workers? How?
    Yes — per the `batch_size_fn` above, all vectorized envs contribute to the
    same rate number for the iteration. Single-GPU `per_gpu` plan; no
    cross-GPU aggregation.
- Unit: env-steps / second.
- Where the value appears (stdout / log file / wandb key / …):
  milabench's `BenchObserver` emits rate events through voir; milabench persists
  them to `artifacts/benchmarks/` (raw trace + `results.json` / per-rate log)
  when `milabench run` is used, or prints them to stdout under `milabench dev`.
- Extraction recipe (regex, script, key name — whatever makes it mechanical to read):
  - From milabench's output stream: rate events are tagged as `rate` observations
    with `task=train` and a numeric `value`. Session-agent computes the median of
    the post-warmup rate values (20 observations after the 5-observation warmup
    skip declared in `voirfile.py`). In milabench's `results.json`, look for the
    `train.rate` series and take its median.
  - As a sanity-check / fallback from `main.py` stdout: `grep '^SPS: '
    <capture> | awk '{print $2}'` — note this is a *cumulative* env-steps/s and
    is not equivalent to the per-iteration `rate`; use only as a sanity-check.

---

## 3) Quality metric (the constraint that must be preserved)

- Name: `avg_episodic_return` (the 20-episode trailing mean of per-episode
  returns on Breakout-v5, written to TensorBoard by `main.py:269` as
  `charts/avg_episodic_return`).
- Precise definition:
  The mean of the last up to 20 terminal episode returns (per `main.py:229`:
  `avg_returns = deque(maxlen=20)`), recorded at each terminal step. At session
  close the "final" value is the last logged point for the Tier-2 run.
- Eval protocol:
  - Number of episodes / batches: whatever finishes inside the §5 wall-clock
    window; typically tens to low hundreds of episodes on Breakout-v5 at Tier-2
    with the locked HPs.
  - Horizon / sequence length (if applicable): one PPO rollout = 1024 env-steps
    (num_envs=8 × num_steps=128); episode horizon bounded by Atari's internal
    life/done dynamics with `episodic_life=True` and `reward_clip=True` via
    envpool.
  - Number of seeds: Phase-3 baseline requires ≥3 full runs (per
    `EXECUTION §4`); each candidate Tier-2 validation uses N per the CV table
    in `RULES §6`.
  - Deterministic or stochastic eval? Stochastic — on-policy PPO with
    `torch.backends.cudnn.deterministic = args.torch_deterministic` (True by
    default) and a seeded RNG for env reset; small HP / clock-driven
    non-determinism is expected, so the tolerance in §4 absorbs it.
- Where it appears (stdout / log file / wandb key / …):
  TensorBoard event file under `runs/<run_name>/events.out.tfevents…`, key
  `charts/avg_episodic_return`. Also `charts/episodic_return` (per-terminal-step)
  and `charts/episodic_length` (length). Not printed to stdout in the baseline
  code — extraction requires reading the TB event file (e.g. via
  `tensorboard.backend.event_processing.event_accumulator` or
  `tensorflow.core.util.event_pb2`).

---

## 4) Quality tolerance (choose exactly one)

- [ ] **Option A** — quality metric within **-X%** of baseline. X =
- [ ] **Option B** — quality metric within **-Y · baseline_std** of baseline. Y =
- [x] **Option C** — explicit rule (describe precisely):
  `quality_verdict = PASS` iff the final-window `avg_episodic_return`
  (median of the last 20 terminal-episode returns at run end) satisfies
  `candidate_mean ≥ baseline_mean − 2 · baseline_std`, where `baseline_mean` and
  `baseline_std` come from the Phase-3 tier-2 baseline (≥3 full runs with
  locked HPs, per `EXECUTION §4`).
  If the candidate's quality CI (computed with N per `RULES §6`) straddles
  the `baseline_mean − 2 · baseline_std` threshold after escalation
  (more seeds / longer horizon per `RULES §11`), record
  `quality_verdict = INCONCLUSIVE` and do not emit `[WIN]` regardless of the
  primary-metric delta.
  `FAIL` otherwise.

Rationale for the chosen tolerance (why it is meaningful for this workload):
PPO on Atari is stochastic with substantial run-to-run variance (typical CV
20–40% at the 10-min / few-M-env-step horizon). A pure `-X%` rule is brittle
when `baseline_mean` is small (early Breakout returns are near zero, where
percentage tolerances are either trivially met or trivially missed). A pure
`-Y · baseline_std` rule is the safe default for stochastic training, but
without an INCONCLUSIVE escape hatch a noisy run on the boundary would emit a
false `[WIN]` or false `[FAIL]`. The explicit rule above combines the
variance-aware threshold with `RULES §11`'s inconclusive-verdict mechanism so
boundary cases are reported honestly rather than silently decided.

---

## 5) Benchmark window (choose exactly one)

- [ ] **Fixed units**: N =       (unit: steps / iterations / samples / episodes)
- [x] **Fixed wall-clock time**: T = **600** seconds (10 minutes)

Rationale (why this window is long enough to be representative but short enough to iterate on):
At the locked HPs (num_envs=8, num_steps=128) and the §9 target hardware (1× L40S),
baseline throughput is expected to be on the order of a few thousand env-steps /
second, yielding roughly 1–3 M env-steps per 10-minute run. This is long enough
for `avg_episodic_return` to have a measurable signal above the noise floor
on Breakout-v5, which in turn lets Phase-3 establish a non-degenerate TTR
target and `baseline_std`. A 10-minute window is ≈2× the
otherwise-plausible 5-minute window; the extra wall-clock buys a lower quality-metric
CV, which reduces the N required per `RULES §6` (often 3 instead of 5) and
therefore does not necessarily increase total Tier-2 cost per validated
candidate.

Notes on short-run vs time-to-result protocol (see `RULES.md` §8, two-tier cadence):
short-run budget for profiling and candidate screening, vs full-window budget for final
validation.

- **Tier 1 (short / screening)** uses the `RULES §8` global default — each
  measurement runs until **both** thresholds are met: ≥2 minutes wall-clock AND
  ≥60 primary-metric observations. With 1024 env-steps per observation, 60
  observations = ~61 k env-steps (a small fraction of the total-timesteps
  budget); the 2-minute wall-clock constraint will typically be the binding one.
- **Tier 2 (full / TTR validation)** uses the §5 window above: 600 s
  wall-clock per run, ≥3 runs for the Phase-3 baseline, N-per-candidate per
  `RULES §6`.
- The stock `voirfile.py` earlystop (`skip=5, stop=20`) caps short runs at 25
  observations — insufficient for Tier 1's ≥60-observation floor. The session-agent
  will need to override voir's `stop` (and likely `--total-timesteps`) to
  reach both Tier-1 thresholds. Concretely: pass a higher `stop` to the voir
  configurable and raise `--total-timesteps` so `main.py` does not
  self-terminate before the wall-clock floor.
- Similarly, for Tier 2 the session-agent sets voir's `stop` high enough that
  the observer does not terminate the run before 600 s wall-clock, and raises
  `--total-timesteps` above the env-step count the baseline throughput reaches
  in 600 s.

---

## 6) Entry command(s)

Baseline command — the exact command the agent runs (both baseline and comparisons). This is
copied verbatim into `artifacts/notes/event_log.md` at session start.

### Direct invocation
```bash
# Fallback / reference: runs main.py directly without voir instrumentation.
# Not used for measurements — milabench's BenchObserver is the source of truth
# for the primary metric. Useful for profiling (torch.profiler, py-spy).
cd benchmarks/retired/torchatari && \
python main.py \
  --env-id Breakout-v5 \
  --num-envs 8 --num-steps 128 \
  --num-minibatches 4 --update-epochs 4 \
  --total-timesteps 1000000
```

### Wrapper / milabench invocation (if applicable)
```bash
# Primary path — all Tier-1 / Tier-2 measurements go through milabench dev.
# argv (num-envs=8, num-minibatches=4, ...) is already locked in dev.yaml on
# hackathon_torchatari_v1 @ f323850; the command below does not re-override it.
milabench dev --config benchmarks/retired/torchatari/dev.yaml

# Tier-1 short-run protocol requires ≥60 observations (RULES §8). The stock
# voirfile.py caps observations at 25 (skip=5 + stop=20). The session-agent
# must raise voir's `stop` and main.py's --total-timesteps before the Tier-1
# baseline is measured (exact override plumbing is discovered at session
# start — see §5 note).

# Tier-2 full-run protocol targets 600 s wall-clock (§5). Same override
# applies: raise `stop` high enough that voir does not early-terminate, and
# raise --total-timesteps above the env-step count reached in 600 s at
# baseline rate.
```

### Required environment variables
- Milabench's own: `MILABENCH_DIR_DATA`, `MILABENCH_CONFIG` (set automatically
  by `milabench dev`).
- Atari / envpool: no additional env vars required for Breakout-v5.
- The session-agent should **not** set `CUDA_VISIBLE_DEVICES` via the
  baseline command — milabench's `per_gpu` plan assigns GPU 0 automatically
  on a single-GPU node. If multi-GPU hardware is present and only one GPU
  should run, set `CUDA_VISIBLE_DEVICES=0` in the shell before invoking
  `milabench dev`.

### Working directory
- `~/projects/milabench/` (or wherever `hackathon_torchatari_v1` is checked
  out). All commands relative to that milabench repo root.

---

## 7) Allowed edits (what the agent *may* change)

Per preparer steer, any code surface is in-scope as long as the change is
mathematically equivalent to the baseline PPO + Atari training dynamics in
expectation:

- The PPO training loop in `main.py:241-366` (iteration structure, rollout
  collection, advantage computation layout, minibatch loop).
- The data pipeline: envpool backend, env wrappers (`RecordEpisodeStatistics`
  etc.), observation dtype / layout, frame transfer patterns.
- The model architecture (`Agent` class in `main.py:156-182`): CNN design,
  activation choices, weight-init style — permitted as long as the forward
  and gradient computations remain mathematically equivalent in expectation
  (e.g. a reshape or a fused kernel that produces the same tensor values is
  fine; changing channel counts or adding non-linearities is a §8 semantic
  change).
- Loss and advantage computation placement (may be moved, fused, or
  reordered) so long as the numerical result is the same.
- Optimizer implementation (Adam → a mathematically-equivalent fused Adam
  kernel is fine; switching optimizer family is §8).
- Runtime flags, compilation, CUDA graphs, mixed-precision autocast
  decisions, `torch.compile` usage, sync-point elimination, batching /
  vectorization.
- `voirfile.py` / `benchfile.py` / `prepare.py` (milabench harness glue) —
  changes that don't redefine the `rate` metric are allowed. If the
  `batch_size_fn` or observer wiring changes, apply `RULES §15`
  (logging-overhead reporting: report the primary metric before *and* after
  the change to prove comparability).
- Any new dependency pinned into `requirements.in` (or a replacement for
  envpool / gym versions) as long as env semantics are preserved (see §8).

---

## 8) Disallowed edits (semantic surfaces — do NOT modify unless explicitly approved)

Changes in this list are **SEMANTIC CHANGES** and require explicit approval +
`RULES §11` stronger quality checks:

- Changing the PPO objective: `clip_coef`, `ent_coef`, `vf_coef`, `gamma`,
  `gae_lambda`, `norm_adv`, `clip_vloss`, `target_kl`. These define the
  algorithm.
- Changing the optimizer's effective update: a different learning-rate
  schedule than linear anneal, different β's for Adam, a different optimizer
  family (e.g. SGD or Lion instead of Adam).
- Changing the environment semantics: `env_id` (away from Breakout-v5),
  `episodic_life`, `reward_clip`, frame-skip, observation stacking depth,
  seeding behavior, or any envpool → non-envpool backend swap that changes
  the observed reward / termination distribution.
- Changing the model capacity or expressivity (channel counts in the CNN,
  added / removed layers, different activation family, changed output-head
  shape) — anything that is not mathematically equivalent to the baseline
  `Agent` forward pass.
- Changing the quality-metric extraction: how `avg_episodic_return` is
  computed from per-episode returns (deque size, aggregation statistic,
  inclusion rule).
- Reducing work: fewer total env-steps per run, fewer PPO update_epochs,
  smaller rollout buffer (num_envs × num_steps), fewer minibatches, when
  that reduction isn't compensated elsewhere and changes the effective
  training budget.
- Changing evaluation protocol or eval-window definition.
- Changing the Tier-1 / Tier-2 windows declared in §5.
- Changing seeding or determinism flags in a way that alters the baseline's
  variance profile (e.g. setting `torch_deterministic = False` while leaving
  the rest unchanged).

---

## 9) Hardware expectations

- GPU model and count: 1× NVIDIA L40S (48 GB VRAM).
- Required GPU memory: ~13 GB peak at num_envs=128 per the
  `config/scaling/default.yaml` snapshot for torchatari; at the locked HPs
  (num_envs=8) peak memory is substantially lower (model + rollout buffer
  ≤ 4 GB). 48 GB of L40S is abundant headroom.
- CPU / RAM minimums: envpool runs Atari env-stepping on CPU; at num_envs=8
  CPU demand is modest (~8 active env threads). Minimum ~8 physical cores,
  ~16 GB system RAM recommended.
- Isolation / pinning requirements (exclusive GPU access, clock pinning, NUMA binding, etc.):
  - Exclusive GPU access during measurement (no co-tenant CUDA processes);
    co-tenants invalidate cross-comparison validity (`RULES §5` drift).
  - Clock pinning not required, but persistent-mode + stable GPU clocks
    reduce throughput CV. If the target machine supports `nvidia-smi -pm 1`
    and `nvidia-smi --lock-gpu-clocks`, turn them on at session start and
    log in `preflight.txt`.
  - NUMA binding helpful when `num_envs` is increased during optimisation
    experiments; not needed for the locked baseline with num_envs=8.

---

## 10) Known caveats and prior art

- **Retired pipeline.** `torchatari` is declared in `config/retired.yaml`
  rather than `config/standard.yaml` and the code is under
  `benchmarks/retired/torchatari/`. The pipeline is intact and runnable; the
  preparer intentionally selected it for this iteration. Session-agents
  should read paths under `benchmarks/retired/torchatari/`, not a
  hypothetical `benchmarks/torchatari/`.
- **Baseline not pre-verified on this machine.** The preparer environment had
  no milabench CLI and no GPU, so the §11 baseline-verification boxes were
  **not** checked by the preparer. The session-agent / operator must run the
  §6 command end-to-end at session start, confirm the §2 and §3 extraction
  recipes return numbers, and only then proceed to Phase 1 optimisation work.
  If the baseline fails (command errors or extraction returns non-numeric),
  halt and escalate per `RULES §16` before making any optimisation-loop edits.
- **HP lock deviates from the milabench `per_gpu` default.** Baseline locks
  `num_envs=8`, `num_minibatches=4` (batch_size=1024, minibatch_size=256) —
  the original CleanRL-reference defaults, not milabench's
  `num_envs=auto({cpu_per_gpu}, 128)`, `num_minibatches=16` (batch_size=16384,
  minibatch_size=1024). This materially changes expected throughput and
  memory profile relative to the numbers in
  `config/scaling/default.yaml` (`perf: 6910` was measured at num_envs=128,
  not num_envs=8).
- **Voir earlystop caps observations.** Stock `voirfile.py` stops the run
  after `skip(5) + stop(20) = 25` rate observations, which is below the
  `RULES §8` Tier-1 floor of 60 and below the env-step budget needed for a
  10-minute Tier-2 run. The session-agent must override voir's `stop`
  parameter (and `--total-timesteps` if `main.py` would self-terminate
  first). This override mechanism is not baked into the card command — it's
  the first thing the session-agent resolves in Phase 1 triage.
- **Quality signal is weak at this horizon.** At num_envs=8 and 600 s
  wall-clock, the baseline reaches on the order of 1–3 M env-steps, where
  Breakout-v5's `avg_episodic_return` is rising but still low and noisy
  (typical CV 20–40%). The §4 tolerance is designed around this; if the
  Phase-3 baseline shows `quality CV > 40%` or `baseline_mean` near zero,
  escalate per `RULES §11` (more seeds, longer horizon) and log `[H-STEER]`
  to the human.
- **Envpool fallback path.** `main.py:19-45` falls back to
  `stable_baselines3.common.env_util.make_vec_env` if `envpool` isn't
  importable. The fallback path is *not* a valid baseline — it has
  different env semantics (no `episodic_life` / `reward_clip`, different
  frame stacking). If envpool is missing at session start, treat as a
  `[BUG]` and fix the install, do not silently run the fallback.
- **No prior session on this iteration.** This is iteration 1; no prior
  baseline numbers, variance characterisation, or Δ_min are available.
- **Δ_min not pre-declared.** Session-agents set Δ_min per `RULES §7` from
  the measured short-run baseline CV. For cross-agent comparability a
  future iteration may pre-declare Δ_min here; iteration 1 leaves it
  session-local.
- Prior baseline numbers for reference (optional):
  - Primary metric: median ___, range [___, ___]  (to be measured at
    session start; `config/scaling/default.yaml` `perf: 6830–6910` is at
    num_envs=128 and does **not** apply to the locked HPs).
  - Quality metric: mean ___, std ___ (to be measured in Phase 3).
- Pre-declared minimum-win threshold Δ_min (optional, for cross-agent comparability; see
  `RULES.md` §7, minimum-win gate): not pre-declared for iteration 1.

---

## 11) Verification checklist (human fills before session start)

- [x] All sections above filled; no `___` placeholders remain. *(Only the
  "to be measured at session start" numbers in §10 remain as explicit
  placeholders — these are Phase-1 / Phase-3 outputs, not preparer
  responsibilities.)*
- [x] Exactly one tolerance option chosen in §4.
- [x] Exactly one benchmark window chosen in §5.
- [ ] Baseline command in §6 runs end-to-end from a clean environment before the session.
  *(Deferred — preparer machine had no milabench CLI and no GPU. The
  session-agent / operator must complete this check at session start
  before Phase-1 optimisation work. See §10 "Baseline not pre-verified".)*
- [ ] Primary metric (§2) and quality metric (§3) are mechanically extractable from the
  baseline output using the recipe given.
  *(Deferred for the same reason — recipes are declared, not yet applied to
  a captured baseline output on target hardware.)*
- [x] Allowed / disallowed edits (§7, §8) are explicit and non-overlapping.
