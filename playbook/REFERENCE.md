# REFERENCE — Lookup tables (load on trigger, evict when done)

Not resident. Each entry below declares its own **Trigger** (what the agent observes
that should cause a load), **Loaded from** (the RULES / EXECUTION citations that send
the agent here), **Hold** (how long to keep it resident), and **Evict** (when it is
safe to drop).

## Schema per entry

```
**Trigger.**     <single, observable condition>
**Loaded from.** <list of RULES §X / EXECUTION §X citations>
**Hold.**        until trigger completes | through Phase N | through session
**Evict.**       <positive statement: "after X is written", "at [PHASE-EXIT N]", etc.>
```

One trigger per entry. If a section would fire under two unrelated conditions, split
it. `Loaded from` is the audit trail — every RULES / EXECUTION cross-reference that
sends the agent here must appear, so editors of RULES / EXECUTION know which REFERENCE
entries they are contracting with.

## Index

| § | Title | Trigger (one-line) | Hold |
|---|-------|--------------------|------|
| 1 | Hidden-sync-point checklist | code change to hot-path / logging / hooks / callbacks | until scan done + benchmark run |
| 2 | Hyperparameter interactions | Prep Phase 2 HP sweep, or a session `H-STEER` that unlocks an HP | through prep Phase 2 / through session unlock |
| 3 | Preflight capture fields | Bootstrap (`EXECUTION §1.3`); also on any `[DRIFT]` re-capture | until preflight.txt written + event-log summary posted |
| 4 | Profiling tools | Choosing a profiler for a new profiling session | through session after first profile (then on-demand for tool swap) |

---

## 1) Hidden-sync-point checklist

**Trigger.** After any code change that touches hot-path, logging, hooks, or callbacks,
before benchmarking.
**Loaded from.** `RULES §15` (logging-overhead reporting), `EXECUTION §4` (Phase 3 loop
step 3).
**Hold.** until scan done + benchmark run.
**Evict.** after the benchmark run completes without flagging a sync regression, or
after the regression is logged and handled.

Hidden synchronization points silently serialize GPU work, producing idle gaps in
traces and per-step variance. They are the most common source of throughput regressions
when the agent adds logging, metrics, debugging hooks, or refactors hot paths. Scan
every change against this list before benchmarking.

**Device → host transfers (implicit sync).**
- PyTorch: `.item()`, `.cpu()`, `.tolist()`, `.numpy()`, `int(x)` / `float(x)` /
  `bool(x)` on a device tensor, `len(x)` on a dynamically-sized tensor.
- JAX: `.item()`, `float(x)` / `int(x)`, `np.asarray(x)`, `x.block_until_ready()`,
  unjitted `print(x)` or string formatting of a traced value.
- Effect: the host blocks until the device finishes every pending kernel.

**Python-side control flow on device values.**
- `if x > 0: …`, `while mask.any(): …`, list / dict comprehension over a device tensor
  — each condition forces a sync to decide the branch.
- JAX additionally retraces (recompiles) when the branching value changes shape / dtype.

**Eager fallbacks from JIT / compile.**
- PyTorch: `@torch.compile` falling back to eager on an unsupported op; dynamic shapes
  forcing recompilation.
- JAX: unsupported control flow inside `jit` causing retrace; `jax.debug.print` in a
  hot loop; `jax.experimental.io_callback(..., ordered=True)`.

**Synchronous logging and callbacks.**
- `print`, tqdm updates, TensorBoard / wandb / MLflow calls that materialise a device
  tensor on the host.
- PyTorch profiler / forward hooks that call `.item()` or `.cpu()` internally.
- Any callback that runs per-step and touches a device value.

**Explicit synchronization primitives.**
- `torch.cuda.synchronize()`, `torch.cuda.Event.synchronize()`,
  `cp.cuda.Stream.null.synchronize()`.
- JAX: `jax.block_until_ready(...)` called per-step rather than at end-of-epoch.

**Data-pipeline stalls (not a sync point per se, same symptom).**
- Unpinned host memory (`pin_memory=False`), `num_workers=0`, `prefetch_factor=0`.
- Host-side `.numpy()` collation inside the dataloader worker.

**How to detect.**
- Profiler traces (`nsys`, `jax.profiler`, PyTorch profiler) — look for GPU idle gaps
  and host-device round-trips between kernel launches.
- Coarse timers around the suspected block to confirm the stall.
- After any change, grep the diff for the patterns above before re-running benchmarks.

Pairs with `RULES.md §15` (reporting rule for logging / sync changes that alter
throughput).

---

## 2) Hyperparameter interactions reference

**Trigger.** Two independent situations load this entry:
- **Preparer-agent**, during Prep Phase 2 HP enumeration
  (`workload-template/AGENT_HANDOFF.md` Prep Phase 2).
- **Session-agent**, when an `H-STEER` intervention unlocks one of the HPs
  pinned in `WORKLOAD_CARD §10.1` and the agent needs to sweep it.

**Loaded from.** `RULES §9` (change-one-thing exceptions: coupled-HP groups),
`workload-template/AGENT_HANDOFF.md` (Prep Phase 2 HP search).
**Hold.** For the preparer: through Prep Phase 2. For the session-agent: from the
`H-STEER` unlock through the re-validation against the Tier-2 baseline.
**Evict.** Preparer: at `[PREP-EXIT 2]`. Session-agent: once the unlocked-HP
candidate is either committed or dropped.

Hyperparameters do not live in isolation — **coupled HPs** shift each other's effective
value when tuned in isolation, and **HPs with training-time dynamics** have short-run
behaviour that under-samples the dynamic regime. The HP-first sweep (preparer or
session-unlock) must watch for both.

**Common couplings.**

| HP pair / group | Coupling |
|-----------------|----------|
| batch size ↔ effective LR | Linear / sqrt scaling rule; warmup length. Changing batch size without rescaling LR confuses the two. |
| gradient-accumulation steps ↔ effective batch size ↔ LR | Same as above, viewed through accumulation. |
| num_envs / num_workers ↔ replay / update dynamics (RL) | Changes update-to-env-step ratio; replay staleness shifts. |
| rollout length ↔ gradient-estimate variance (RL) | Longer rollouts reduce variance but inflate memory and delay the first update. |
| mixed precision ↔ loss scaling ↔ LR | FP16 / BF16 loss scaling interacts with optimiser step magnitude. |
| dataloader workers ↔ prefetch_factor ↔ batch size | Pipeline saturation depends on all three; tuning one shifts the bottleneck. |
| compile flags ↔ shape polymorphism ↔ dynamic batch size | Recompiles on shape changes invalidate compile-time wins. |

**HPs with training-time dynamics.**
- **LR schedules** (warmup + decay / cosine). Short runs may observe only warmup → the
  peak LR looks "optimal" higher than it actually is at plateau.
- **Exploration schedules** (epsilon decay, softmax temperature). Pre-decay tuning
  biases toward too-exploratory settings.
- **Target-network sync frequency** (DQN-family). Optimal value depends on replay
  freshness; short runs under-sample policy drift.
- **Teacher-forcing ratio**, **curriculum**, **batch-size ramp**, **EMA / weight
  averaging**. All change behaviour across the run.

**Diagnostic questions** before tuning an HP:
1. Is this HP coupled to another? If yes, enumerate partners and either lock them or
   tune together as a group.
2. Does this HP have a schedule, or does its effect depend on training progress? If
   yes, is the short run long enough to include the relevant phase transition?
3. Would changing this HP change the effective value of another (e.g. batch size
   changing effective LR)?

If the answer to (1) or (3) is yes and the pair can't be cleanly separated, escalate
(`H-STEER` for the session-agent; raise with the human preparer for the preparer-agent)
rather than silently sweeping.

**Common short-run pitfalls.**
- LR tuned on warmup-only runs: peak choice masks plateau behaviour.
- Exploration tuned before decay: "optimal" exploration stays too high.
- Batch size tuned without LR rescaling: looks suboptimal when really LR-undertuned.
- num_envs tuned ignoring replay-ratio: optimal at the staleness sweet spot for that
  short run only.

---

## 3) Preflight capture fields

**Trigger.** Session-agent Bootstrap (`EXECUTION §1.3`) — first action of the
session. Also on any `[DRIFT]` event that requires re-capture.
**Loaded from.** `RULES §5` (preflight directive + drift rule), `EXECUTION §1.3`
(bootstrap step).
**Hold.** until `preflight.txt` is written and the event-log summary is posted; on
`[DRIFT]`, until the drift-delta is captured and re-baselined.
**Evict.** after `[BASELINE]` (Phase 1 baseline logged). Re-load only on `[DRIFT]`.

Capture the following fields. Store raw dumps in `artifacts/notes/preflight.txt` and
summarise the key ones at the top of `artifacts/notes/event_log.md`.

- **GPU state.** Model name, driver version, CUDA version, current clock frequencies
  (graphics + memory), persistent mode, whether clocks are locked or DVFS is on. Capture
  via `nvidia-smi -q` (or equivalent for the target hardware).
- **Concurrent processes on the GPU.** If any other CUDA process is running on the same
  device, declare whether the session will coexist with it or not. Co-tenancy
  invalidates throughput comparisons across agents.
- **Relevant environment variables.** At minimum, whichever of these are set:
  `CUDA_VISIBLE_DEVICES`, `CUDA_DEVICE_ORDER`, `XLA_FLAGS`, `XLA_PYTHON_CLIENT_*`,
  `TORCH_COMPILE_*`, `TORCHINDUCTOR_*`, `PYTORCH_CUDA_ALLOC_CONF`, `OMP_NUM_THREADS`,
  `MKL_NUM_THREADS`, plus any workload-specific flags listed in `WORKLOAD_CARD.md §6`.
- **Framework versions.** Python, CUDA, cuDNN, JAX / jaxlib, PyTorch, triton, NumPy —
  whichever the workload depends on. `pip freeze` (or equivalent) is acceptable.
- **Repo state.** Git commit hash, dirty status (the starting commit should be clean
  aside from the session folder itself).

Drift handling (re-baseline, tag `env_snapshot_id`, log `[DRIFT]`) is in `RULES §5`.

---

## 4) Profiling tools

**Trigger.** Choosing a profiler for a new profiling session (first session of the run,
or swapping tools to investigate a different layer).
**Loaded from.** `RULES §12` (profiling-evidence directive).
**Hold.** through session after first profile — held because the profiling cadence
repeats. The tool list can be evicted during intermediate analysis and re-loaded on
swap.
**Evict.** at `[SESSION-CLOSE]`, or earlier during analysis stretches between profiling
sessions.

Common profiler choices by layer:

- **GPU / system** — `nsys` (Nsight Systems), `nvprof`, `rocprof`, or vendor
  equivalents. Best for GPU idle gaps, kernel gaps, host-device round trips.
- **Framework level** — `jax.profiler`, PyTorch profiler (`torch.profiler`), TensorFlow
  profiler. Best for op-level breakdowns, autograd overhead, compile/trace artifacts.
- **CPU** — `py-spy`, `cProfile`, `perf`. Best for Python-side overhead, dataloader
  stalls, host-side hot loops.

Per `RULES §12`, each profiling session records: profiler command line, trace
filename(s), and brief notes (bottlenecks observed, hypothesis formed), under
`artifacts/profiles/`.
