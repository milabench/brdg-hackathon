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

- Repo URL (workload remote the preparer branched from):
- Upstream base (branch @ commit the prep branch started from, e.g. `main @ <sha>`):
- Prepared branch (preparer pushes this; operators check it out): `hackathon-<workload>-<iteration>`
- Prepared-branch head commit (short SHA — what operators will start their sessions from):
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

## 6) Setup and entry command(s)

Baseline command — the exact command the agent runs (both baseline and comparisons). This is
copied verbatim into `artifacts/notes/event_log.md` at session start. The install subsection
below documents how to reach the state where that command runs; the preparer-agent captures
the exact commands it ran during preparation, so operators and session-agents reproduce the
same environment.

### Install / environment setup

The commands needed to go from a freshly-cloned workload repo on the prepared branch
(`hackathon-<workload>-<iteration>`) to a machine where the baseline command below runs
end-to-end. The preparer-agent fills this from what it actually executed during preparation;
operators run it once on their host before their first session.

```bash
# e.g.
# python -m venv .venv && source .venv/bin/activate
# pip install -e .
# milabench install --config <config path>        # if milabench-based
# any one-time dataset / checkpoint download
```

System-level prerequisites (driver / CUDA / Python versions, OS) that the install commands
above assume:

- (e.g. NVIDIA driver ≥ 535, CUDA 12.x, Python 3.11)

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

## 10) HP lock (filled by preparer-agent in Prep Phase 2)

The preparer-agent runs the HP search once during preparation (`workload-template/AGENT_HANDOFF.md`
Prep Phase 2) and pins its outputs here. The session-agent reads this section at
Phase 2 entry (`playbook/EXECUTION.md §3`) and uses it as the Tier-1 / Tier-2
reference for the optimization loop. Re-measurement on the session host happens
at session Phase 2 entry; large drift escalates as `H-OPS`.

### 10.1 Locked HP configuration

- Winner candidate label (or `default` if no candidate cleared the backtrack gate):
- `hp_values_json` (one line, machine-parseable; copied into every `phase=phase_3_*`
  row's `hp_values_json` column):

```json
{}
```

- Rationale (which HPs were swept, which were held at default, why this candidate
  won — cite the prep `experiment_id` of the winning candidate):

### 10.2 Target quality level

TTR is measured against this level. Declared in Prep Phase 2 per `RULES §4` (tier
baselines) and reused session-side.

- [ ] **Option A** — mean end-of-run quality across the default-HP full runs (value: ___).
- [ ] **Option B** — pre-declared threshold from prior art (value: ___; source: ___).

### 10.3 Tier-2 baseline (locked-HP TTR)

The locked-HP full-length TTR runs produced during Prep Phase 2. Session-agent
adopts these as the Tier-2 reference at Phase 2 entry (`RULES §6`, `§8`).

- Prep `experiment_id` (for session-agent's `baseline_ref` column):
- N (number of full-length runs):
- TTR median (seconds):
- TTR range [min, max] (seconds):
- TTR CV (%):
- Quality at target: mean ___, std ___

### 10.4 Tier-1 baseline (short-run throughput proxy)

The short-run baseline the prep HP sweep ranked candidates against. Session-agent
**re-measures** this on the session host at Phase 2 entry (cheap check) and
confirms within CI before entering Phase 3.

- Short-run protocol (wall-clock duration, N primary-metric observations per run,
  warmup, any workload-specific adjustment per `RULES §8`):
- N (number of short runs):
- Primary-metric median (unit from §2):
- Primary-metric CV (%):

### 10.5 Prep-branch head commit (Tier-2 baseline provenance)

The short-SHA in `§1` is the commit Tier-2 numbers above were measured at. Session
Tier-2 comparisons are only valid against that commit; session-agent branches off
it at Phase 1 entry.

---

## 11) Known caveats and prior art

- Optimizations already applied upstream (so the agent does not re-attempt them):
- Known bugs or quirks:
- Variance notes from prior sessions (baseline CV, typical noise floor), if any:
- Pre-declared minimum-win threshold Δ_min (optional, for cross-agent comparability;
  see `RULES.md` §7, minimum-win gate): ___

---

## 12) Verification checklist (human fills before session start)

- [ ] All sections above filled; no `___` placeholders remain.
- [ ] Exactly one tolerance option chosen in §4.
- [ ] Exactly one benchmark window chosen in §5.
- [ ] Baseline command in §6 runs end-to-end from a clean environment before the session.
- [ ] Primary metric (§2) and quality metric (§3) are mechanically extractable from the
  baseline output using the recipe given.
- [ ] Allowed / disallowed edits (§7, §8) are explicit and non-overlapping.
- [ ] §10 HP-lock section filled: `hp_values_json`, target quality, Tier-2 baseline
  (median / range / CV / N), Tier-1 baseline (median / CV / N / protocol). The
  winning prep `experiment_id` points at a row in `prep/prep_results.csv`.
- [ ] §10.5 prep-branch head commit matches the `Prepared-branch head commit` in §1.
