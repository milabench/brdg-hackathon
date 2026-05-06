# Event log — torchatari / iteration 1 / claude-sonnet

All entries follow RULES §13.2 template:
```
T+___  [TAG]
Action/Change: ___
Hypothesis/Reason: ___
Result: ___  (metric: ___; baseline: ___; delta: ___)
Evidence: ___
Next: ___
```

`T+0` = session start on 2026-04-22 15:49:49 UTC. Later `T+HH:MM` offsets are
wall-clock from that point.

---

T+0  [SESSION-START]
Date: 2026-04-22
Human operator: bouthilx@mila.quebec
Agent ID: claude-sonnet
Workload: torchatari
Iteration: 1
Hackathon repo: torchatari-1 @ f79414c
Workload repo: git@github.com:mila-iqia/milabench.git @ 2e04211 (branch master)
Workload branch (agent creates now): agent_claude-sonnet_torchatari_opt
Hardware: target = 1× NVIDIA L40S (48 GB), 6 CPU cores, 32 GB RAM, allocated
  via `sbatch -c 6 --mem=32G --gres=gpu:l40s:1 --partition=unkillable
  --time=0:15:00` per operator steer. Current preflight node (cn-f004) is
  CPU-only (AMD EPYC 7502, 2 cores / 10 GB allocated to this job, 250 GB node
  total). GPU + driver + CUDA fields captured from the first benchmark job
  and appended to preflight.txt.
Software: system Python 3.10.12, uv 0.8.22, milabench venv CPython 3.12.11
  (created by `uv pip install -e ".[cuda]"`). Framework / CUDA driver
  versions deferred to the first GPU job.

---

T+0  [PREFLIGHT]
Summary of preflight capture (full dump: artifacts/notes/preflight.txt):
- cluster = mila; current interactive job 9339065 on partition main-cpu.
- benchmark jobs will target partition `unkillable` (1 parallel job/user)
  with `--gres=gpu:l40s:1 -c 6 --mem=32G --time=0:15:00`, escalating to
  partition `long` (1000 parallel jobs) only if parallelism is needed.
- GPU / driver / CUDA / torch versions not yet captured (CPU-only node).
  Deferred per RULES §5 — first GPU job will append `[GPU-PREFLIGHT jobid=...]`
  to preflight.txt. Cross-boundary comparisons against that first GPU run
  are valid; anything earlier is bootstrap, not measurement.
- Drift rule (RULES §5): any env-var flip / GPU clock change / framework bump
  during the session → log `[DRIFT]` and re-baseline.

---

T+0  [H-OPS]
Action/Change: Operator provided SLURM submission recipe and partition rules.
  `sbatch -c 6 --mem=32G --gres=gpu:l40s:1 --partition=unkillable
   --time=0:15:00` is the starting template. `unkillable` permits only 1
  simultaneous job per user; `long` permits up to 1000 parallel but has
  longer wait. Cluster docs: docs.mila.quebec.
Hypothesis/Reason: Steers all of Phase 1 / Phase 2 / Phase 4 run submission
  strategy — short serial runs on `unkillable`, any parallel sweeps move to
  `long`.
Result: Recorded for use across the session.
Evidence: operator message T+0.
Next: use `unkillable` for single-run Phase-1 baseline.

---

T+0  [H-OPS]
Action/Change: Operator confirmed "follow the instructions" for branch
  naming after initial ambiguity on the agent-name slot (hyphen-in-name
  vs underscore). Agent used `agent_claude-sonnet_torchatari_opt`.
Hypothesis/Reason: Keep the session folder name (`claude-sonnet/`) and the
  branch slug consistent so `score_session.py` / reviewers can map one to
  the other.
Result: Branch created; session folder created at
  `brdg-hackathon/sessions/torchatari/1/claude-sonnet/`.
Evidence: git branch, `ls brdg-hackathon/sessions/torchatari/1/`.
Next: proceed to HP-lock reconciliation then Phase 1.

---

T+0:05  [CHANGE]  (pre-session setup, not a measured experiment)
Action/Change: Locked HPs in benchmarks/retired/torchatari/dev.yaml:
  `--num-envs: auto({cpu_per_gpu}, 128) → 8`,
  `--num-minibatches: 16 → 4`.
  (`--num-steps 128`, `--update-epochs 4`, `--total-timesteps 1000000`,
   `--env-id Breakout-v5` were already at the card's locked values.)
Hypothesis/Reason: WORKLOAD_CARD §6 and §10 declare the session starts from
  `hackathon_torchatari_v1 @ f323850`, which locked argv to CleanRL
  defaults (num_envs=8, num_minibatches=4, batch_size=1024,
  minibatch_size=256). That branch does not exist in this clone (origin =
  mila-iqia/milabench, master @ 2e04211; the hackathon fork was on
  github.com:milabench/milabench). Applying the HP lock as a
  pre-Phase-1 setup commit is the only way to match the card's declared
  starting state. Treating this as pre-session baseline setup, not a
  measured experiment — no results.csv row. Measured experiments (Phase-1
  baseline onward) will compare against this locked config.
Result: dev.yaml argv now matches WORKLOAD_CARD §6 locked values.
Evidence: `git diff benchmarks/retired/torchatari/dev.yaml`.
Next: install milabench env, submit Phase-1 baseline sbatch job.

---

T+0:20  [BUG]  (Phase 1 triage — pre-existing, not introduced by any change)
Action/Change: n/a (run crashed before producing any metric).
Hypothesis/Reason: SLURM job 9339313 failed at startup with:
  `AssertionError: only discrete action space is supported`
  at main.py:36 `isinstance(envs.action_space, gym.spaces.Discrete)`.
  envpool 1.2.0 (installed) returns `gymnasium.spaces.discrete.Discrete`
  rather than `gym.spaces.Discrete`; the isinstance check fails even though
  Breakout-v5 has a properly discrete action space with attribute `.n`.
  envpool switched from gym to gymnasium spaces in 1.x.
Result: crash; no rate / quality observations produced.
Evidence: phase1_baseline.slurm-9339313.err (empty); phase1_baseline.log
  lines 204–232.
Next: apply minimal fix (hasattr check), re-run.

T+0:22  [FIX]
Action/Change: Changed `isinstance(envs.action_space, gym.spaces.Discrete)`
  → `hasattr(envs.action_space, 'n')` in main.py:36.
Hypothesis/Reason: `.n` is the only envpool action-space attribute actually
  used downstream (main.py:170, 224, 292). This fix is semantically neutral —
  no algorithm change. Confirmed root cause: probe script verified
  `type(e.action_space) == gymnasium.spaces.discrete.Discrete` and
  `hasattr(e.action_space, 'n') == True`.
Result: Committed as e593f40 on agent_claude-sonnet_torchatari_opt.
Evidence: git show e593f40.
Next: re-submit Phase-1 baseline.

T+0:30  [BASELINE]
Action/Change: First clean end-to-end run on target hardware (NVIDIA L40S,
  cn-l033) with locked HPs (num_envs=8, num_minibatches=4) and envpool fix
  applied. SLURM job 9339348. Run dir:
  /network/scratch/b/bouthilx/milabench/results/runs/phase1_baseline_9339348/
  Voir stop=20 smoke run (25 total observations, ~45 s wall-clock).
Hypothesis/Reason: Confirm workload runs end-to-end and both metrics are
  mechanically extractable (Phase-1 exit criterion).
Result:
  PRIMARY METRIC (rate, env-steps/s):
    milabench median: 2135.32 items/s
    post-warmup (skip=5) observations: 19
    min=2016.59  median=2117.83  max=2269.46  std=69.65
    (milabench reports its own median across all post-skip obs: 2135.32)
  QUALITY METRIC (avg_episodic_return):
    TensorBoard key: charts/avg_episodic_return
    n=135 terminal-episode observations in ~45 s
    last value: 1.70  mean-last-5: 1.87
    (very early training at ~25k env-steps; returns near zero are expected)
  PEAK GPU MEMORY: 1174 MiB / 46068 MiB
  GPU UTIL: ~8% average (strong CPU bottleneck at num_envs=8 — key profiling
    insight: envpool CPU stepping is the throughput bottleneck, not GPU)
  LOSS: finite, ~0.01-0.04; no NaN/inf observed
  ENVPOOL: 1.2.0 used (not the fallback path) ✓
  run exit=0, milabench failure rate 0%
Evidence: phase1_baseline.log (lines 443–685),
  TensorBoard at benchmarks/retired/torchatari/runs/Breakout-v5__main__1__1776874185/
  results.csv row: 2026-04-22_claude-sonnet:001
Next: Phase-1 exit, proceed to Phase-2 HP sweep.
Checklist: ran[✓] logged[✓] csv[✓] quality[✓] one-thing[✓] h-check[✓]

T+0:30  [PHASE-EXIT 1]
Exit criterion met:
  - clean end-to-end run completed ✓
  - primary metric (rate) extractable: milabench median 2135.32 env-steps/s ✓
  - quality metric (avg_episodic_return) extractable: last=1.70, n=135 ✓
  - bugs found: 1 (envpool gymnasium type check) — fixed (e593f40) and
    re-run confirmed before exit ✓
  - all measurements are on fixed-commit e593f40 (HP-lock + gymnasium fix)
Notable: GPU util ~8% at locked HPs indicates significant CPU-side bottleneck.
Next: Phase 2 — HP sweep (num_envs as the primary lever; needs operator
  approval if treated as semantic, or profiling to confirm it's the top
  bottleneck).

T+0:35  [BLOCKED]  (non-fatal — card mentions a "typo fix" we can't
  reproduce without the source branch)
Action/Change: WORKLOAD_CARD §0 lists two "pin commits" that were on
  `hackathon_torchatari_v1`: (1) HP-lock-to-CleanRL-defaults (applied
  above) and (2) an `install_variant` typo fix.
Hypothesis/Reason: Without the source branch, the specific typo being
  fixed is unknown. Current dev.yaml has `install_variant: unpinned`,
  which pack.py handles as a first-class value (not a typo on its face).
  Other valid values observed in sibling benchmarks: `cuda`, `unpinned`.
  Could be that the typo was elsewhere in torchatari's install path, or
  has already been merged into mila-iqia master.
Result: Deferred. Will surface if milabench install or `milabench dev`
  fails with an install_variant-related error. No code change preemptively.
Evidence: n/a (no failure observed yet).
Next: Attempt milabench install of torchatari in the Phase-1 sbatch job;
  if install fails, enter RULES §16 standing bug-handling procedure.

---

T+0:50  [H-OPS]
Action/Change: Operator instructed: "use subagents to execute SLURM job work
  (submit/wait/extract) and return only key metrics to main context."
Hypothesis/Reason: Keep main context lean during long-running cluster
  experiments so phase progression stays coherent across many submissions.
Result: Saved as feedback memory. Subagent-first workflow adopted for job
  execution; main agent remains responsible for scribe duties, decisions,
  and correctness.
Evidence: memory/feedback_subagent_workflow.md.
Next: All subsequent Phase-2 / Phase-3 job submissions delegated to subagents
  for submit+poll+extract; main agent logs the structured results.

---

T+1:00  [CHANGE]
Action/Change: Abandoned `--override` path for Phase-2 HP sweep; created
  per-candidate YAML files under benchmarks/retired/torchatari/ instead:
  `phase2_envs{16,32,64,128}.yaml`, `phase2_envs256_c{6,12,24}.yaml`.
  Each file sets `voir.options.stop: 200` explicitly (stock voirfile.py
  default is stop=20, which caps short-run observations below RULES §8
  Tier-1 floor of 60).
Hypothesis/Reason: `milabench run --override "torchatari.argv.--num-envs=32"`
  crashed with `TypeError: string indices must be integers, not 'str'` at
  milabench/common.py:111 — the OmegaConf dotlist regex `r"[.\w]+"` does
  not accept hyphens, so argv keys like `--num-envs` produce an empty key
  and break `OmegaConf.merge()`. Per-candidate YAMLs route around the bug
  entirely (no behaviour change, no semantic impact).
Result: Clean configs; each short-run = 205 observations (skip=5 + 200),
  above the §8 Tier-1 floor.
Evidence: `benchmarks/retired/torchatari/phase2_envs*.yaml`;
  sbatch wrappers under `artifacts/benchmarks/phase2_envs*.sbatch`.
Next: Submit Phase-2 sweep jobs (num_envs ∈ {16,32,64,128,256}).

---

T+1:05  [EXPERIMENT]  (Phase-2 Tier-1 HP sweep — num_envs, c=6)
Action/Change: Submitted short-run sweep at cpus-per-task=6 (matching Phase-1
  allocation): num_envs ∈ {16, 32, 64, 128}. One-variable change per row
  (num_envs; coupled HP `num_minibatches=4` stays fixed per REFERENCE §2
  coupling declaration).
Hypothesis/Reason: Phase-1 showed num_envs=8 leaves GPU mean-util ≈8% — the
  pipeline is heavily CPU-bottlenecked by envpool stepping. Larger num_envs
  should grow wall-clock throughput until CPU saturates or GPU becomes the
  binding constraint. Tier-1 screening per RULES §8 (throughput proxy only).
Result: post-skip median rate (items/s):
  num_envs=16   → 3189.89 (jobid 9339473)
  num_envs=32   → 4133.33 (jobid 9339474)
  num_envs=64   → 4820.03 (jobid 9339475)
  num_envs=128  → 5542.02 (jobid 9339476)
  vs Phase-1 baseline (num_envs=8, c=6) → 2135.32
  Monotone improvement with diminishing returns (+1.49×, +1.29×, +1.17×, +1.15×).
  All runs exit=0; no NaN/inf; peak mem ≤ 4660 MiB (well under 48 GB).
Evidence: results.csv rows 002–005; run dirs
  /network/scratch/b/bouthilx/milabench/results/runs/phase2_envs{16,32,64,128}_93394*/
Next: push further with num_envs=256 and explore CPU core count (hypothesis:
  rate still CPU-bottlenecked at c=6).
Checklist: ran[✓] logged[✓] csv[✓] quality[deferred — RULES §8 Tier-1 throughput-only] one-thing[✓] h-check[✓]

---

T+1:30  [H-OPS]
Action/Change: Operator instructed: "consider increasing the number of cores
  per job if the experiments start looking bottlenecked by overhead of
  parallel env execution on few cores. If subagents are missing permissions,
  ask me to add them."
Hypothesis/Reason: Explicit green-light to vary CPU allocation (which is a
  system resource, not a WORKLOAD_CARD §8 semantic HP) if the Phase-2 sweep
  reveals CPU-bound regime. This expands the Phase-2 candidate space.
Result: CPU-scaling comparison added to Phase-2 plan: submit num_envs=256 at
  both c=6 and c=12 (doubled allocation) to quantify scaling.
Evidence: operator message at T+1:30.
Next: Submit envs=256 at c=6 and c=12 in parallel (long partition).

---

T+1:45  [EXPERIMENT]  (Phase-2 Tier-1 — num_envs=256, CPU scaling c6 vs c12)
Action/Change: Submitted num_envs=256 at two core counts to identify the
  CPU bottleneck threshold: jobid 9339668 (c=6, 32G) and 9339669 (c=12, 48G).
Hypothesis/Reason: If c=12 rate > 2× c=6 rate → CPU-bound even at c=12.
  If c=12 rate only moderately above c=6 → GPU compute is now limiting.
Result: post-skip median rate:
  envs=256, c=6  → 5937.44 (jobid 9339668)   mean gpu-util 2.7%  gpu-util-max 0.97
  envs=256, c=12 → 8982.31 (jobid 9339669)   mean gpu-util 5.6%  gpu-util-max 0.97
  c=12 / c=6 = 1.51× (sub-linear but substantial). Max GPU util 0.97 in both
  → GPU is fully saturated *during update bursts*; mean util low because
  long envpool-stepping gaps dominate wall-clock. CPU still limiting.
Evidence: results.csv rows 006–007; run dirs
  /network/scratch/b/bouthilx/milabench/results/runs/phase2_envs256_c{6,12}_*/
Next: operator asked to try c=24 to probe diminishing returns.
Checklist: ran[✓] logged[✓] csv[✓] quality[deferred — Tier-1] one-thing[✓] h-check[✓]

---

T+2:00  [H-STEER]
Action/Change: Operator message: "Looks like the 6 cpu job is taking a lot
  more time. Maybe worth trying one with 24 cpus."
Hypothesis/Reason: Push the CPU-scaling curve further to check whether c=24
  unlocks additional throughput or hits diminishing returns.
Result: Submitted jobid 9339830 (num_envs=256, c=24, 72G, long partition).
Evidence: operator message at T+2:00; artifacts/benchmarks/phase2_envs256_c24.sbatch.
Next: Compare c=6/c=12/c=24 once c=24 finishes.

---

T+2:10  [EXPERIMENT]  (Phase-2 Tier-1 — num_envs=256, c=24)
Action/Change: num_envs=256 at c=24 completed.
Hypothesis/Reason: Continue CPU scaling curve.
Result: post-skip median rate:
  envs=256, c=24 → 10735.42 (jobid 9339830)  mean gpu-util 4.2%  gpu-util-max 0.97
  c=24 / c=12 = 1.20×  (diminishing — 6→12 gave +51%, 12→24 only +20%).
  GPU-util-max unchanged at 0.97 across all three core counts → we are not
  starving the GPU at peak; we are compressing the env-stepping gaps.
Evidence: results.csv row 008.
Next: apply GPU fair-share accounting (RULES §14.1 self-audit due) before
  selecting Phase-2 winner.
Checklist: ran[✓] logged[✓] csv[✓] quality[deferred — Tier-1] one-thing[✓] h-check[✓]

---

T+2:15  [H-ARCH]
Action/Change: Operator reframed selection criterion: "each L40s has 12 cores
  dedicated, so using 24 cores potentially blocks another L40s. Speedup must
  be large enough to justify blocking 2 GPUs."
Hypothesis/Reason: Shared-cluster citizenship: selecting c=24 consumes 2×
  per-GPU core fair-share, effectively stranding a second GPU for lack of
  cores. The correct optimisation target is throughput per GPU-fair-share
  (cores/12), not throughput per job.
Result: Per-GPU-share accounting:
  c=6  → 5937.44  items/s / 0.5 GPU-share = 11874 items/s/share  (but requires
         GPU-sharing with a co-tenant to realize, which our protocol forbids
         — so this number is not achievable in practice)
  c=12 → 8982.31  items/s / 1.0 GPU-share =  8982 items/s/share  ← best achievable
  c=24 → 10735.42 items/s / 2.0 GPU-share =  5368 items/s/share  (40% worse
         per blocked GPU than c=12; a second GPU would sit idle for lack of cores)
  Selection: num_envs=256, cpus=12 wins on the fair-share criterion.
Evidence: operator message at T+2:15; results.csv rows 006–008.
Next: mark Phase-2 exit on this selection, proceed to Phase 3.

---

T+2:20  [NOISE]
Action/Change: Phase-2 CV characterisation (Tier-1 throughput proxy).
Hypothesis/Reason: RULES §6 requires CV on the short-run baseline to size N.
Result: Phase-2 Tier-1 runs are N=1 per (num_envs, cpus) cell — a sweep, not
  a replicated baseline. Per-run std% reported by milabench at the selected
  config (envs=256, c=12): std% = 5.6% (intra-run variance across post-skip
  observations; not a cross-seed CV). This suggests cross-seed CV should be
  similar magnitude. Δ_min will be set after Phase-3 (≥3 seeds) when a real
  cross-seed std is available.
Evidence: phase2_envs256_c12.log rate line.
Next: Phase-3 completes → compute cross-seed CV and set Δ_min.

---

T+2:25  [PHASE-EXIT 2]
Locked HPs for Phase 3: num_envs=256, num_steps=128, num_minibatches=4,
  update_epochs=4, total_timesteps=500000000, env_id=Breakout-v5, seed=varies,
  cpus-per-task=12, mem=48G.
Metrics (short-run, Tier-1): primary rate=8982.31 items/s (4.20× over Phase-1
  baseline 2135.32); quality deferred to Phase 3 (TTR regime).
Next: Phase 3 (Tier-2 TTR baseline: ≥3 full 600s runs with locked HPs) —
  seed=1/2/3 submitted as jobs 9340003/9340004/9340005.

---

T+2:30  [H-DEBUG]
Action/Change: Operator questioned HP selection rigour: "When selecting HP
  in phase 2, did you also compare with TTR? The HP can affect both items/s
  and TTR."
Hypothesis/Reason: In PPO, larger num_envs grows wall-clock throughput but
  can reduce sample efficiency (more off-policy-ness per update → slower
  return climb per env-step). Rate-optimal config need not be TTR-optimal.
  My Phase-2 selection was purely on the throughput proxy; Tier-1 short runs
  (stop=200, ~200s of training) were too brief to yield meaningful quality
  signal on Breakout (Phase-1 showed return ~2 at ~45s — still near zero
  for ~200s runs).
Result: Accepted as methodologically correct critique. Fix (additive, does
  not cancel Phase 3): submit Tier-2 (stop=600, c=12) comparison runs at
  two lower num_envs values alongside the Phase-3 seeds, then compare
  quality-at-matched-wall-clock to confirm or revise selection.
  Submitted jobid 9340065 (envs=64, c=12) and 9340066 (envs=128, c=12).
Evidence: operator message at T+2:30; phase2_ttr_envs{64,128}_c12.{yaml,sbatch}.
Next: Let Phase-3 seeds and TTR-comparison jobs finish; compare quality
  trajectories to make final HP selection before computing Phase-3 baseline.

---

T+2:45  [CHANGE]  (Phase-3 Tier-2 baseline submission)
Action/Change: Submitted 3 Tier-2 baseline runs with the Phase-2-selected
  config (num_envs=256, c=12) at seeds 1/2/3 — jobids 9340003/9340004/9340005.
  voir.options.stop=600 (→ ~600s of training + setup), --time=01:00:00.
Hypothesis/Reason: RULES §8 + EXECUTION §4 require ≥3 Tier-2 runs to set
  the TTR target, compute cross-seed CV, and derive N per RULES §6.
Result: Jobs running in parallel on long partition (3 GPUs allocated
  concurrently, non-competing since `long` admits 1000 parallel).
Evidence: phase3_envs256_c12_s{1,2,3}.{yaml,sbatch}.
Next: Wait for completion; extract rate + final avg_episodic_return per
  seed; compute baseline_mean/std; set Δ_min per RULES §7.

---

T+2:45  [EXPERIMENT]  (Phase-2.5 TTR-aware HP comparison, Tier-2)
Action/Change: Submitted quality-trajectory comparison at stop=600, c=12:
  jobid 9340065 (envs=64, seed=1)
  jobid 9340066 (envs=128, seed=1)
Hypothesis/Reason: If a smaller num_envs reaches higher avg_episodic_return
  at t=600s despite lower rate, the Phase-2 throughput-based selection must
  be revised before Phase-3 baseline_mean is computed.
Result (partial — rate from Tier-2 window):
  envs=64,  c=12 → 6927.37 items/s (rate)  [jobid 9340065 complete]
  envs=128, c=12 → 7940.64 items/s (rate)  [jobid 9340066 complete]
  envs=256, c=12 → 8982.31 items/s (rate from Phase-2 Tier-1; Tier-2 seeds pending)
  Rate at Tier-2 monotonic with num_envs, consistent with Tier-1 sweep.
  Quality (avg_episodic_return at t=400s and t=600s) extraction pending —
  needs per-run TensorBoard parse or `data` event scan.
Evidence: phase2_ttr_envs{64,128}_c12.log; run dirs
  /network/scratch/b/bouthilx/milabench/results/runs/phase2_ttr_envs*_c12_*/
Next: extract quality trajectories (all 5 runs: 3× envs=256 seeds + envs=64
  + envs=128); compare quality-at-600s; finalise Phase-2 HP selection.
Checklist: ran[partial — TTR jobs ✓; Phase-3 seeds still running] logged[✓]
  csv[pending — waiting for Phase-3 seeds before final Phase-2 decision]
  quality[pending extraction] one-thing[✓] h-check[✓]

---

T+2:50  [H-STEER]
Action/Change: Operator prompted: "It's been a while you did not log
  anything. Did you forget the instructions at AGENT_HANDOFF.md and
  WORKLOAD_CARD.md?"
Hypothesis/Reason: I had drifted from RULES §1 scribe discipline — no
  event-log entries between T+0:35 and T+2:45 despite several completed
  experiments and multiple human interventions. This self-audit catch-up
  entry (+ the 10 backfilled entries above) reconciles the log.
Result: Log caught up through T+2:50; added entries for Phase-2 sweep,
  CPU scaling comparisons, HP-selection H-ARCH, Phase-2 exit, H-DEBUG on
  TTR rigour, Phase-3 submission, and TTR comparison runs.
Evidence: this block of event_log.md.
Next: Finish quality extraction on the 5 Tier-2 runs once Phase-3 seeds
  finish; then make final HP selection and set Phase-3 baseline.

---

T+2:55  [AUDIT]
Since last audit: N/A (first audit — overdue per RULES §14.1 "every 30 min").
  Since Phase-1 exit: 7 experiments (Phase-2 sweep × 5 cells + c-scaling × 3
  − 1 overlap at envs=256/c=6), 5 human interventions (H-OPS subagents,
  H-OPS cores, H-STEER c=24, H-ARCH GPU-fair-share, H-DEBUG TTR-in-HP,
  H-STEER log-catch-up), 0 wins so far (wins Tier-2-only per §8).
Bottleneck stack (priority order):
  1) envpool CPU stepping gaps (evidence: mean gpu-util ≤5.6% at saturated
     peak-util 0.97 across all c ∈ {6,12,24} at envs=256 — GPU idle during
     env stepping, saturated during update bursts). Target for Phase 4:
     overlap rollout↔update (async env stepping or double-buffered rollouts).
  2) Tensor-transfer overhead (obs Tensor().to(device) on CPU every step at
     main.py:261,263 — allocation + copy in the hot loop).
  3) `info["lives"]` Python-level dict access inside per-env loop at
     main.py:265–271; could be vectorised.
  4) Weight-init `nn.init.orthogonal_` not a perf concern, but torch.compile
     on the Agent forward could fuse the Conv→ReLU chain.
  5) Per-iteration TensorBoard scalar writes (~8 writes × N terminations +
     7 writes per iteration) — likely tiny but RULES §15 mandates report.
Plan reconciliation:
  - On-track: Phase-3 seeds running for Tier-2 baseline.
  - Adjusted: added Phase-2.5 TTR comparison (envs=64/128 @ c=12) per
    operator's H-DEBUG. If a smaller num_envs wins on q@600s, the Phase-3
    HP set changes and current seeds must be discarded.
  - Dead ends to avoid: do NOT re-attempt --override HP passing; do NOT
    run c=24 without justification > 2× c=12 rate; do NOT rely on Tier-1
    short-run quality (meaningless below ~M env-steps on Breakout).
Next: extract quality trajectories from the 5 Tier-2 runs → finalise
  Phase-2 selection → either proceed with envs=256 seeds as Phase-3
  baseline (compute CV, set Δ_min) OR discard current seeds and re-submit
  at the revised HP. Phase 4 profiling starts only after Phase-3 exit.


---

T+3:10  [EXPERIMENT]  (Phase-2.5 TTR quality extraction — N=1 per cell)
Action/Change: Extracted charts/avg_episodic_return from TB events files
  for all 5 Tier-2 runs (3× envs=256 seeds + envs=64 s=1 + envs=128 s=1).
  TB dir 1776880054 had a host-collision (both TTR runs started at same
  unix second with seed=1) — split by events-file hostname to recover
  per-run trajectories.
Hypothesis/Reason: Compare quality at matched wall-clock (t=400s, t=600s)
  across HP candidates to confirm or revise Phase-2 throughput-based
  selection.
Result (quality at wall-clock, N=1 per cell except envs=256 where N=3):
  envs=64,  c=12  → q@400=37.0   q@600=70.8   q_final=123.4 @721s   (seed=1, 9340065)
  envs=128, c=12  → q@400=26.05  q@600=49.3   q_final=238.05 @1248s (seed=1, 9340066)
  envs=256, c=12  → q@400=16.95  q@600=28.00  q_final=325.0 @2166s  (seed=1, 9340003)
  envs=256, c=12  → q@400=11.6   q@600=21.95  q_final=280.7 @2202s  (seed=2, 9340004)
  envs=256, c=12  → q@400=11.05  q@600=21.3   q_final=250.65 @2138s (seed=3, 9340005)
  envs=256 at 600s: mean=23.75 std=3.68 CV=15.5% (N=3)
  envs=64 at 600s:  70.8 (N=1 — no CI)
  envs=128 at 600s: 49.3 (N=1 — no CI)
  Provisional ranking at the WORKLOAD_CARD §5 600s budget (UNREPLICATED):
    envs=64 ≫ envs=128 > envs=256, inverse of throughput-proxy ranking.
Evidence: /tmp/quality_extract.py; TB dirs under
  benchmarks/retired/torchatari/runs/Breakout-v5__main__*_17768{79869,80054}/
Next: operator H-STEER (below) — N=1 comparison is risky given noise; submit
  replicas to get CI before finalising HP.
Checklist: ran[✓] logged[✓] csv[pending — replicas pending] quality[PROVISIONAL]
  one-thing[✓] h-check[✓]

---

T+3:15  [H-STEER]
Action/Change: Operator critique: "Do we have CI here to make that
  comparison? The result is very noisy that early, so making a single-run
  comparison is risky."
Hypothesis/Reason: RULES §6 requires N sized to the tier's CV. At envs=256
  N=3 (Phase-3 seeds) gives std=3.68 at q@600s. envs=64 and envs=128 are
  N=1 — cannot compute CV, cannot compute confidence interval, cannot fire
  [WIN] or emit a decision per RULES §7.
Result: Accepted. Submitted 4 replica runs at c=12, stop=600 (distinct
  seeds to avoid TB-dir collisions):
    jobid 9340458 — envs=64,  seed=2
    jobid 9340459 — envs=64,  seed=3
    jobid 9340460 — envs=128, seed=4
    jobid 9340461 — envs=128, seed=5
  After completion: N=3 at each of envs=64, envs=128, envs=256 → proper
  Welch's t or bootstrap on q@600s.
  Phase-3 seeds 9340003/04/05 left running; they will cap at 60-min SLURM
  time limit. Their quality trajectories (through ~3500s of training) will
  remain useful as reference even if HP is revised — they characterize the
  envs=256 sample-efficiency curve.
Evidence: operator message at T+3:15;
  phase2_ttr_envs{64,128}_c12_s{2,3,4,5}.{yaml,sbatch}
Next: wait ~15 min for replicas to finish, recompute Phase-2.5 table with
  CI, fire [PHASE-EXIT 2] properly (the earlier one was provisional), set
  the real Phase-3 HP, possibly cancel/discard envs=256 seeds if envs=64 or
  envs=128 wins under replicated data.


---

T+3:30  [EXPERIMENT]  (Phase-2.5 TTR replicas N=3 — decisive)
Action/Change: 4 replica jobs completed: envs=64 seeds 2,3 and envs=128
  seeds 4,5 (9340460/61 scancelled per operator after N=3 was reached).
  All runs at c=12 stop=600, distinct seeds → no TB-dir collisions.
Hypothesis/Reason: RULES §6 N-sizing from replicas before finalizing HP.
Result (q@600s, N=3 per cell):
  envs=64:  vals=[70.8, 51.5, 79.0]   mean=67.10 std=14.12 CV=21.0%
  envs=128: vals=[49.3, 35.35, 37.65] mean=40.77 std=7.48  CV=18.3%
  envs=256: vals=[28.0, 21.95, 21.3]  mean=23.75 std=3.69  CV=15.6%
  Welch's t + bootstrap 95% CI:
    envs=64  vs envs=256: Δ=+43.35 (+182%), CI [+27.97, +55.25], t=5.14 df=2.3
    envs=128 vs envs=256: Δ=+17.02 (+71.6%), CI [+10.13, +25.33], t=3.53 df=2.9
  Both CIs exclude zero; envs=64 >> envs=128 >> envs=256 on q@600s.
  Rate CV at envs=64/c=12: 0.4% (vals: 6927.37, 6875.00, 6889.51).
Evidence: /tmp/quality_extract2.py; TB dirs
  Breakout-v5__main__{1,2,3}__17768{80054,82752}/
Next: fire [PHASE-EXIT 2] revised (the first was provisional on throughput
  only); use the 3 envs=64 runs as Phase-3 Tier-2 baseline.
Checklist: ran[✓] logged[✓] csv[✓] quality[PASS — envs=64 wins decisively] one-thing[✓] h-check[✓]

---

T+3:35  [PHASE-EXIT 2]  (revised — supersedes T+2:25)
Locked HPs for Phase 3: num_envs=**64**, num_steps=128, num_minibatches=4,
  update_epochs=4, total_timesteps=500000000, env_id=Breakout-v5,
  cpus-per-task=12, mem=48G.
Metrics (Tier-2, N=3): rate_median=6897.3 items/s (CV=0.4%); quality
  q@600s mean=67.10 std=14.12 CV=21.0%.
Rationale: envs=256 (prior provisional winner) maximised throughput proxy
  (8982 items/s) but converged slowly — q@600s mean 23.75 vs envs=64's
  67.10 (CI [+28, +55] rejects the null). TTR-aware selection flipped the
  verdict. envs=64 sits at the knee of the throughput-vs-sample-efficiency
  trade-off: rate 6897/s is ~77% of envs=256 but quality at budget is
  nearly 3× higher.
Next: Phase 3 — target / TTR declaration (EXECUTION §4).

---

T+3:40  [PHASE-EXIT 3]
Baseline runs: 3 Tier-2 full 600s runs at locked HPs (envs=64, c=12),
  seeds 1/2/3 — results.csv experiment_id 2026-04-22_claude-sonnet:009.
Target quality (EXECUTION §4 Option A): target = baseline_mean(q@600s) =
  **67.10** (mean of end-of-window quality across baseline seeds).
PASS tolerance (WORKLOAD_CARD §4): candidate q@600s ≥ baseline_mean -
  2·baseline_std = 67.10 - 2·14.12 = **38.86**.
Baseline TTR (wall-clock seconds to first-crossing, N=3):
  TTR to q≥38.86 (PASS threshold): median=407s  mean=407s  std=6s  CV=1.4%
  TTR to q≥50:                     median=441s  mean=449s  std=46s CV=10.1%
  TTR to q≥67.10 (target):         median=567s  mean=543s  std=57s CV=10.5%
  (TTR to q≥100 only reached by 2/3 seeds; not a reliable baseline target.)
Observed variance: quality CV=21.0% at q@600s; TTR CVs above. q@600s CV
  exceeds RULES §6 row "15% ≤ CV < 25%" → Phase-4 candidates need N≥5.
  But TTR to the PASS threshold has CV=1.4% (very tight) — screening on
  "time to cross 38.86" is a low-noise proxy that N=3 should suffice for
  in Phase 4.
Next: Phase 4 optimization loop.

---

T+3:40  [NOISE]
Action/Change: CV characterisation across tiers.
Result:
  Tier-1 rate (envs=64 c=12, intra-run std%): 5.1–5.5% across 3 seeds
    (milabench rate-line std%). Cross-seed rate CV = 0.4% (very tight).
  Tier-2 quality q@600s: CV=21.0% (N=3, the 15-25% band → N≥5 for Phase-4
    quality comparisons per RULES §6).
  Tier-2 TTR to PASS threshold (38.86): CV=1.4% → low-noise, N=3 adequate.
  Tier-2 TTR to target (67.10): CV=10.5% → moderate, N=5 preferred.
Δ_min (RULES §7):
  Tier-1 rate wins: Δ_min = max(2×0.4%, 3%) = 3% (absolute).
  Tier-2 TTR-to-PASS wins: Δ_min = max(2×1.4%, 3%) = 3% (tight).
  Tier-2 TTR-to-target wins: Δ_min = max(2×10.5%, 3%) = 21%.
Evidence: event_log T+3:30; /tmp/ttr_compute.py output.
Next: use these CVs to size N and accept/reject candidates in Phase 4.


---

T+4:00  [EXPERIMENT]  (Phase-4 candidate #1 — pinned HtoD staging)
Action/Change: Commit ea8df42 on agent_claude-sonnet_torchatari_opt —
  added pinned CPU staging buffers for obs/reward/done HtoD, non_blocking=True.
  Tier-1 N=3 runs at envs=64 c=12 stop=200: jobids 9340742/43/44.
Hypothesis/Reason: torch.profiler showed 7680 Pageable HtoD calls = 24.9% of
  CUDA time, 43.6% of CPU time in aten::copy_. Pinned memory → DMA fast path
  + non_blocking → potential overlap with GPU work.
Result: FAIL. Regression.
  Baseline rate: 6897.29 ± 26.97 (CV 0.4%)
  Candidate rate: 6376.74 ± 316.30 (CV 5.0%)
  Δ = -520.55 items/s (-7.55%), Welch t=-2.84 df≈2
  Intra-run rate std% also up (candidate 4.9-9.0% vs baseline 5.1-5.5%).
  Verdict: CI clearly excludes zero in the wrong direction AND variance
  inflated 12× — the async pattern introduces stalls, not overlap.
Evidence: phase4_cand1_c12_s{1,2,3}.log; results from Tier-1 short runs.
Next: revert commit, form candidate #2.
Checklist: ran[✓] logged[✓] csv[pending — negative result row] quality[N/A Tier-1] one-thing[✓] h-check[✓]

---

T+4:05  [REVERT]
Action/Change: Reverted commit ea8df42 (new commit 4584f6b).
Hypothesis/Reason: Candidate #1 regressed rate by -7.5%. Post-mortem:
  1) torch.Tensor(np) fuses view+cast+alloc in one optimised C call;
     obs_stage.copy_(from_numpy(np)) splits it into more Python/C hops
     with more allocations. Extra CPU overhead exceeds pinned-DMA savings.
  2) non_blocking=True doesn't overlap meaningfully here — the next GPU
     op (fwd pass) stream-order-blocks on the HtoD anyway, and the gap
     between `.to()` return and `fwd()` call is <1µs.
  3) The 1.8 MB obs transfer × 128 steps = 230 MB/iter. Pageable ~6 GB/s
     = 38 ms; pinned ~25 GB/s = 9 ms. Max ~29 ms savings per iter — too
     small to offset the extra Python per-step overhead (~100 ms).
Result: Repo state back to e593f40 + 4584f6b (= e593f40 effectively).
Evidence: git log.
Next: propose candidate #2 targeting a different bottleneck or a lower-
  overhead transfer improvement.


---

T+4:25  [EXPERIMENT]  (Phase-4 candidate #2 — CPU-side termination iteration)
Action/Change: Commit 19554cd — replaced `for idx, d in enumerate(next_done)`
  (CUDA tensor iteration) with `for idx in range(args.num_envs)` + numpy
  `next_done_np[idx]` checks, moving the HtoD of next_done to after the loop.
  Tier-1 N=3 at envs=64 c=12 stop=200, jobids 9342158/59/60.
Hypothesis/Reason: Hypothesized 64 × 128 = 8192 per-element DtoH syncs
  from iterating the CUDA tensor. Eliminating them should free CPU time.
Result: NEUTRAL. Δ=+20.18 items/s (+0.29%), Welch t=0.84, CI crosses 0.
  Candidate rate: 6917.47 ± 31.56 (CV 0.5%); baseline 6897.29 ± 26.97
  (CV 0.4%). Intra-run std% unchanged (~5.2-5.8% both sides).
  Hypothesis disproved: PyTorch's iteration over a small 1-D CUDA tensor
  doesn't trigger expensive per-element DtoH — likely cached/fused. The
  8192-DtoH-per-iter mental model was wrong.
Evidence: phase4_cand2_c12_s{1,2,3}.log.
Next: revert; candidate #3 targets GPU-side compute (bf16 autocast).
Checklist: ran[✓] logged[✓] csv[✓-see-next-entry] quality[N/A Tier-1] one-thing[✓] h-check[✓]

---

T+4:30  [REVERT]
Action/Change: Reverted commit 19554cd (new commit 1f97943).
Hypothesis/Reason: Sub-threshold Tier-1 delta (+0.29% << Δ_min 3%).
  Revert per RULES §9 to keep baseline unambiguous for next candidate.
Result: Repo state back to e593f40 effective.
Evidence: git log.
Next: candidate #3.


---

T+4:50  [EXPERIMENT]  (Phase-4 candidate #3 — torch.compile(agent.network))
Action/Change: Commit e18ecd6 — `agent.network = torch.compile(agent.network)`.
  Tier-1 N=3 at envs=64 c=12 stop=200, jobids 9342182/83/84.
Hypothesis/Reason: Conv fwd+bwd = 53% of CUDA time; Inductor fusion could
  reduce GPU time and improve kernel occupancy. WORKLOAD_CARD §7 allows
  compile.
Result: FAIL. Δ=-704.93 items/s (-10.22%), Welch t=-3.33, CI clearly
  negative. CV 0.4% → 5.9%. Peak mem 2826 → 2552 MiB (fusion worked) but
  throughput regressed. Likely cause: Inductor's output for the tiny Atari
  CNN (3 conv + 1 linear, batch=64/256) is worse than the hand-tuned
  cuDNN kernels used by eager. Known weakness for small-batch CNNs.
Evidence: phase4_cand3_c12_s{1,2,3}.log.
Next: revert.
Checklist: ran[✓] logged[✓] csv[pending] quality[N/A Tier-1] one-thing[✓] h-check[✓]

---

T+4:55  [REVERT]
Action/Change: Reverted e18ecd6 (new commit 8672153).
Hypothesis/Reason: -10.22% regression vs baseline, well outside Δ_min.
Result: Repo state back to e593f40 effective.
Next: scoreboard 0-wins 3-experiments; consider further candidates.


---

T+5:30  [PROFILE]
Action/Change: py-spy --native record of main.py at locked HPs (envs=64 c=12).
  45s warmup + 30s capture, 4437 samples @ 200Hz, 3 threads.
Hypothesis/Reason: Identify whether envpool's 53% wall-clock share is
  addressable (sync overhead vs genuine CPU work).
Result: MainThread self-time leaf breakdown (19.36s of 30s sampled):
  sem_post                   11.9%   envpool worker coordination
  libgomp addresses          ~14%    OpenMP barriers
  libc 0x...c117              9.0%   futex/sem_wait
  libcuda internals           ~5%    GPU driver sync
  pthread_mutex_{lock,unlock} 2.7%   lock contention
  ≈ 30% of MainThread CPU is synchronization primitives.
  Inclusive time: at::native::copy_ chain 27.7%, torch::utils::internal_
  new_from_data 19.6% — torch.Tensor(np_array).to(device) is the hot line
  (main.py:263 accounts for ~47% of MainThread inclusive time).
Evidence: envpool_pyspy_speedscope.json, envpool_pyspy_native.svg.
Next: test candidate #4a (async envpool) — hypothesis: eliminate sync
  overhead by overlapping env stepping with GPU work.

---

T+5:50  [EXPERIMENT]  (Phase-4 candidate #4a — async envpool, batch_size=32)
Action/Change: Commit 484716d — `--async-batch-size=32` enables envpool
  async send/recv API. RecordEpisodeStatistics bypassed (not async-compat);
  episode-return tracking inlined. Per-env (num_envs, num_steps, ...)
  scratch buffers, transposed into sync-layout buffers at rollout end.
  Tier-1 N=3 at envs=64 c=12 stop=200, jobids 9344369/70/71.
Hypothesis/Reason: py-spy showed 30% sync overhead; async mode should
  overlap env.step with GPU fwd and reduce wait-for-slowest-env time.
Result: FAIL. Δ=-1819.86 items/s (-26.4%), Welch t=-78.7, CV tight (0.6%).
  Candidate rate: 5077.43 ± 29.65.
  Lesson: Atari Breakout env step times are uniform across workers; there's
  no "slowest env" to hide. The 30% sync primitives are thread-pool
  housekeeping that happens on EVERY send/recv — async mode doubles the
  cycles (batch_size=32 means 2× more send/recv), doubling coordination.
  Plus: Python housekeeping per recv (for-loop over 32 env_ids),
  fwd batch halved (32 instead of 64), extra scratch buffers (+900 MiB mem).
  Net: ~26% regression, no overlap benefit realised.
Evidence: phase4_cand4a_c12_s{1,2,3}.log.
Next: revert; decide on #4b (uint8 end-to-end) or wrap-up.
Checklist: ran[✓] logged[✓] csv[pending] quality[N/A Tier-1] one-thing[✓] h-check[✓]

---

T+5:55  [REVERT]
Action/Change: Reverted commit 484716d (new commit 5c76010). Repo at
  e593f40 effective.
Result: Scoreboard: 0 wins in 4 candidates.
  #1 pinned HtoD:           -7.55% FAIL
  #2 CPU-side termination:  +0.29% NEUTRAL
  #3 torch.compile(network):-10.22% FAIL
  #4a async envpool:       -26.40% FAIL
Next: consider #4b (uint8 end-to-end) or accept result and wrap up.


---

T+6:15  [EXPERIMENT]  (Phase-4 candidate #4b — uint8 obs through HtoD, GPU cast)
Action/Change: Commit a0b4241 — obs buffer dtype uint8; HtoD via
  `torch.from_numpy(x).to(device)` (no CPU cast); model forward casts
  `x.float() / 255.0` on GPU.
  Tier-1 N=3 at envs=64 c=12 stop=200, jobids 9344618/19/20.
Hypothesis/Reason: py-spy showed torch::utils::internal_new_from_data
  at 19.6% of MainThread inclusive time (from torch.Tensor(np_array)
  CPU float cast). Candidate eliminates that cast AND transfers 4×
  less data HtoD (uint8 vs float32).
Result: **FIRST Tier-1 WIN**. Δ=+793.44 items/s (+11.50%), Welch t=+13.35,
  CI excludes zero. CV 1.3% (slightly wider than baseline 0.4% — likely
  minibatch-update CPU variability, negligible). Peak mem 2826→2478 MiB
  (obs buffer 4× smaller on GPU).
  Candidate rate: 7690.73 ± 99.36.
Evidence: phase4_cand4b_c12_s{1,2,3}.log.
Next: promote to Tier-2 (stop=600) for TTR validation + quality check.
  Jobids 9344729/30/31 submitted.
Checklist: ran[✓] logged[✓] csv[pending] quality[N/A Tier-1] one-thing[✓] h-check[✓]


---

T+6:50  [EXPERIMENT]  (Phase-4 #4b Tier-2 validation)
Action/Change: Commit a0b4241 Tier-2 at envs=64 c=12 stop=600, seeds 1/2/3.
  Jobids 9344729/30/31.
Result: Rates (items/s): 8223.75, 8108.17, 8226.29 → mean=8186.07 std=67.48
  (+18.7% over baseline 6897.29 — Tier-2 rate even stronger than Tier-1's +11.5%).
  Quality (q@600s): vals=[121.90, 68.50, 137.55] mean=109.32 std=36.20 CV=33.1%.
  Quality vs baseline (67.10 ± 14.12): Δ=+42.22 (+63% higher quality).
  All 3 seeds > 38.86 PASS threshold → quality_verdict=PASS.
  TTR to q≥38.86: vals=[338, 348, 347] median=347s mean=344s std=5s CV=1.6%.
  TTR vs baseline (median 407s CV 1.4%): Δ=-62.9s (-15.45%).
  Welch t=-13.49; bootstrap 95% CI of ΔTTR = [-70.2, -56.2]s, excludes 0.
  Relative TTR reduction CI: [13.8%, 17.2%].
Evidence: phase4_cand4b_t2_c12_s{1,2,3}.log; TB dirs
  Breakout-v5__main__{1,2,3}__{1776958502,1776958538}/
Next: emit [WIN].
Checklist: ran[✓] logged[✓] csv[✓] quality[PASS] one-thing[✓] h-check[✓]

---

T+6:55  [WIN]
experiment_id: 2026-04-22_claude-sonnet:013
change: uint8 obs through HtoD + .float()/255.0 cast inside model forward
delta_ttr: -15.45% (CI: [-17.2%, -13.8%], N=3, tier=full)
quality_verdict: PASS
Rate proxy improvement: +18.7% at Tier-2 (8186 vs 6897 items/s)
Commit: a0b4241 on branch agent_claude-sonnet_torchatari_opt

Mechanism: py-spy identified `torch::utils::internal_new_from_data` at
19.6% inclusive MainThread CPU — that's torch.Tensor(np_array) doing a
CPU-side float cast on the Atari obs (uint8 input → float32 tensor).
The candidate keeps obs as uint8 across HtoD (4× less bandwidth), with
the cast now happening on GPU inside the model's `x.float() / 255.0`.
Numerical semantics identical to baseline.

---

T+7:00  [PHASE-EXIT 4]
Experiments run: 5 candidates
  #1 pinned HtoD staging        : Tier-1 -7.55%  FAIL, reverted
  #2 CPU-side termination loop  : Tier-1 +0.29%  NEUTRAL, reverted
  #3 torch.compile(agent.network): Tier-1 -10.22% FAIL, reverted
  #4a async envpool (B=32)      : Tier-1 -26.40% FAIL, reverted
  #4b uint8 obs + GPU cast      : Tier-1 +11.50%, Tier-2 ΔTTR=-15.45% WIN
Wins: 1 ([WIN] emitted)
Final bottleneck stack (for future sessions):
  1) envpool CPU env stepping (53% of iter) — hard to reduce without
     restructuring PPO to handle non-sync rollouts. For uniform Atari
     env timing, async mode made things WORSE (proven empirically).
  2) Remaining tensor-creation overhead for rewards/done transfers.
     Could investigate similar uint8-style reductions there but payoff
     is small (~1% of iter).
  3) The sync primitives (~30% of MainThread CPU self-time per py-spy)
     are envpool's internal thread-pool housekeeping; appears to be
     inherent to the library's design on this hardware.
Next: session wrap-up (FINAL_SUMMARY.md + [SESSION-CLOSE]).


---

T+7:15  [SESSION-CLOSE]
clean close: no unresolved bugs

FINAL_SUMMARY.md written at artifacts/FINAL_SUMMARY.md.
Branch agent_claude-sonnet_torchatari_opt HEAD: a0b4241 (the winning commit).
Hackathon repo branch torchatari-1 @ 6e88910.

Headline: 1 [WIN] — candidate #4b (uint8 obs + GPU cast).
  Primary metric: +18.7% (rate 6897 → 8186 items/s, Tier-2 N=3)
  Quality: PASS (q@600s 67.10 → 109.32; all seeds > 38.86 threshold)
  TTR: -15.45% (407s → 347s, 95% CI [-17.2%, -13.8%])
  Peak GPU memory: -12% (2826 → 2478 MiB)
  Commits on branch: e593f40 (phase-1 bugfix), a0b4241 (the win)

