# Workload Card — <workload name>

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

- Workload name (short slug):
- Iteration id (e.g. `1`, `2`):
- Session folder: `sessions/<workload>/<iteration>/`
- Date:
- Summary (one sentence — what is being optimized, in plain language):

---

## 1) Target workload

- Repo URL + commit (the state from which the session starts):
- Benchmark code path(s) (relative to repo root):
- Entry point (script / module that the baseline command invokes):
- Environment / dataset name:
- Read-only reference code (files the agent may read for context but **must not modify**
  unless explicitly approved):
  - e.g. environment implementation, dataset loader internals, eval logic
  - _list paths:_

---

## 2) Primary metric (the thing being optimized)

- Name: (e.g. `steps/sec`, `samples/sec`, `tokens/sec`, `time-to-accuracy`)
- Precise definition:
  - What counts as one "step" / sample / token / iteration?
  - Are units aggregated across vectorized / parallel workers? How?
- Unit:
- Where the value appears (stdout / log file / wandb key / …):
- Extraction recipe (regex, script, key name — whatever makes it mechanical to read):

---

## 3) Quality metric (the constraint that must be preserved)

- Name: (e.g. `best_mean_reward`, `top-1_accuracy`, `eval_loss`)
- Precise definition:
- Eval protocol:
  - Number of episodes / batches:
  - Horizon / sequence length (if applicable):
  - Number of seeds:
  - Deterministic or stochastic eval?
- Where it appears (stdout / log file / wandb key / …):

---

## 4) Quality tolerance (choose exactly one)

- [ ] **Option A** — quality metric within **-X%** of baseline. X =
- [ ] **Option B** — quality metric within **-Y · baseline_std** of baseline. Y =
- [ ] **Option C** — explicit rule (describe precisely):

Rationale for the chosen tolerance (why it is meaningful for this workload):

---

## 5) Benchmark window (choose exactly one)

- [ ] **Fixed units**: N =       (unit: steps / iterations / samples / episodes)
- [ ] **Fixed wall-clock time**: T =      seconds

Rationale (why this window is long enough to be representative but short enough to iterate on):

Notes on short-run vs time-to-result protocol (see `RULES.md` §8, two-tier cadence):
short-run budget for profiling and candidate screening, vs full-window budget for final
validation.

---

## 6) Entry command(s)

Baseline command — the exact command the agent runs (both baseline and comparisons). This is
copied verbatim into `artifacts/notes/event_log.md` at session start.

### Direct invocation
```bash
# e.g. cd benchmarks/<workload> && python main.py <args>
```

### Wrapper / milabench invocation (if applicable)
```bash
# e.g. milabench dev --config benchmarks/<workload>/dev.yaml
```

### Required environment variables
- (e.g. `CUDA_VISIBLE_DEVICES`, `XLA_FLAGS`, framework-specific flags)

### Working directory
- (relative to repo root)

---

## 7) Allowed edits (what the agent *may* change)

List the files, directories, or conceptual surfaces the agent is expected to touch:

- (e.g. the training loop, data pipeline, model code, config files)

---

## 8) Disallowed edits (semantic surfaces — do NOT modify unless explicitly approved)

List surfaces the agent must not modify. Changes here are **SEMANTIC CHANGES** and require
stronger quality checks (see `RULES.md` §11, correctness / quality checks):

- (e.g. environment / dataset internals, algorithm definition, eval code, reward computation)

---

## 9) Hardware expectations

- GPU model and count:
- Required GPU memory:
- CPU / RAM minimums:
- Isolation / pinning requirements (exclusive GPU access, clock pinning, NUMA binding, etc.):

---

## 10) Known caveats and prior art

- Optimizations already applied upstream (so the agent does not re-attempt them):
- Known bugs or quirks:
- Variance notes from prior sessions (baseline CV, typical noise floor), if any:
- Prior baseline numbers for reference (optional):
  - Primary metric: median ___, range [___, ___]
  - Quality metric: mean ___, std ___
- Pre-declared minimum-win threshold Δ_min (optional, for cross-agent comparability; see
  `RULES.md` §7, minimum-win gate): ___

---

## 11) Verification checklist (human fills before session start)

- [ ] All sections above filled; no `___` placeholders remain.
- [ ] Exactly one tolerance option chosen in §4.
- [ ] Exactly one benchmark window chosen in §5.
- [ ] Baseline command in §6 runs end-to-end from a clean environment before the session.
- [ ] Primary metric (§2) and quality metric (§3) are mechanically extractable from the
  baseline output using the recipe given.
- [ ] Allowed / disallowed edits (§7, §8) are explicit and non-overlapping.
