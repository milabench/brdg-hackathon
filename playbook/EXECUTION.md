# EXECUTION — session procedure

> Before running this procedure, you must have already read the filled
> `WORKLOAD_CARD.md` (one level up from your session root) and the `RULES.md` sibling
> in `playbook/`. Rules referenced below as `RULES §X` are defined there.
> `SCHEMA §X` refers to `SCHEMA.md` (also in `playbook/`).

Phases run in order: 1 → 2 → 3 → 4 → wrap-up. Each has an explicit exit criterion.
The standing bug-handling procedure (`RULES §16`) can fire from any phase and pauses
the current phase until resolved.

---

## 1) Bootstrap (before Phase 1)

### 1.1 Session folder layout

Your shell cwd is the workload repo root (e.g. milabench). `brdg-hackathon/` is cloned
inside it. The protocol files live in `brdg-hackathon/playbook/` (read-only); your
session artifacts go under `brdg-hackathon/sessions/<workload>/<iteration>/<agent-name>/`:

```
<workload-repo>/                                      ← your shell cwd
  (workload source code, benchmarks, etc.)
  brdg-hackathon/
    playbook/                                         ← read-only protocol
      AGENT_HANDOFF.md  RULES.md  EXECUTION.md
      SCHEMA.md  REFERENCE.md  FINAL_SUMMARY_TEMPLATE.md
    sessions/<workload>/<iteration>/                  ← this iteration
      WORKLOAD_CARD.md                                (filled; shared across agents)
      <agent-name>/                                   ← your session artifact root
        artifacts/                                    (you produce this)
          benchmarks/
          profiles/
          notes/
          FINAL_SUMMARY.md
    scripts/                                          ← validation / scoring tools
```

**Path convention.** All `artifacts/…` paths in these docs are relative to your
**session artifact root** (`brdg-hackathon/sessions/<workload>/<iteration>/<agent-name>/`),
not to your shell cwd. Benchmark commands (`WORKLOAD_CARD.md §6`) run from the shell
cwd (workload repo root). Instruction-file references (`RULES §X`, `SCHEMA §X`,
`REFERENCE §X`) resolve to sibling files in `brdg-hackathon/playbook/`. The filled
`WORKLOAD_CARD.md` lives one level up from your session root.

### 1.2 Session start — emit `[SESSION-START]`

Open `artifacts/notes/event_log.md` and write the `[SESSION-START]` milestone as the
first entry, at `T+0`. Its body records the session's identity and the corpus version
so a reviewer can reproduce the environment later:

```
T+0  [SESSION-START]
Date: 2026-04-21
Human operator: <name>
Agent ID: <agent-name>
Workload: <workload>
Iteration: <iteration>
Hackathon repo: <brdg-hackathon branch> @ <short-commit>
Workload repo: <workload-repo remote> @ <starting-commit>
Workload branch (agent creates now): agent_<agent-name>_<short-goal>
Hardware: GPU / CPU / RAM
Software: driver / CUDA / framework versions / Python
```

`<brdg-hackathon branch>` and `<short-commit>` come from the brdg-hackathon clone the
agent is running against (`git -C brdg-hackathon rev-parse --abbrev-ref HEAD` and
`git -C brdg-hackathon rev-parse --short HEAD`). `[SESSION-START]` is a milestone tag:
see `RULES §13.3` (role) and `RULES §14.3` (body shape + invariants).

Workload-specific fields (benchmark command, primary / quality metrics, tolerance) come
from `WORKLOAD_CARD.md` unchanged — do not duplicate them into the `[SESSION-START]`
body.

### 1.3 Pre-flight environment capture

Run the preflight check (`RULES §5`) **before** Phase 1, using the field list in
`REFERENCE §3`. Store the raw dumps in `artifacts/notes/preflight.txt`; summarise the
key fields in the event log immediately after `[SESSION-START]`.

---

## 2) Phase 1 — Bug-first pass

Before any optimization work, verify the workload is bug-free as-shipped. Optimization on
top of a buggy baseline produces meaningless deltas.

What to do:
- Read the benchmark entry point and the code paths listed in `WORKLOAD_CARD.md §1`
  (target workload) and `§7` (allowed edits). Form a mental model of control flow, data
  flow, and the likely hot path.
- Run the baseline command from `WORKLOAD_CARD.md §6` end-to-end **once** with default
  settings. Confirm:
  - the run completes successfully,
  - the primary metric and quality metric are produced, and
  - the extraction recipes in `WORKLOAD_CARD.md §2` and `§3` actually yield values from
    the output.
- Inspect for obvious bugs and misconfigurations. Common candidates:
  - wrong metric being reported (e.g. per-worker rather than aggregated; training loss
    mistaken for eval loss),
  - silent NaN / inf in loss or reward,
  - tensors on the wrong device, dtype mismatches, unintended casts,
  - logging that overwrites earlier output or double-counts steps,
  - eval invoked with training flags, or vice versa,
  - seeds that don't actually seed anything.

If a bug is found, follow `RULES §16` (standing bug-handling procedure); the only
Phase-1 wrinkle is that there is no prior experiment to revert, so triage collapses to
"fix in allowed territory, or escalate to the human".

**Exit criterion:**
- One clean end-to-end baseline run, with primary and quality metrics extracted, the
  run logged in the event log and tagged `[BASELINE]` (`RULES §13.3`), and any bugs
  either fixed-and-committed or explicitly flagged to the human.
- Emit `[PHASE-EXIT 1]`.

---

## 3) Phase 2 — HP-first pass

Engineering-knob HPs (batch size, num_envs, rollout length, dataloader workers, compile
flags, log frequency, etc.) materially affect the primary metric. Optimizing before
these are settled conflates HP wins with engineering wins. Settle them first, then
**lock** them.

What to do:
- Enumerate HPs that plausibly affect the primary metric. Separate them into:
  - **Engineering knobs** — HPs whose value does not change what the algorithm *is*
    (batch size, num_envs, rollout length, dataloader workers, log frequency, compile
    flags, etc.). These are candidates for tuning.
  - **Semantic / coupled HPs** — HPs that change algorithm dynamics or are coupled to
    others (learning rate, exploration schedule, target-sync frequency, replay buffer
    size, etc.). Kept at default unless the human explicitly approves tuning them. See
    `REFERENCE.md §2` for the couplings and schedule effects this builds on.
- Declare the sweep budget up front (e.g. "≤5 HPs × 3 values each on short runs, plus one
  long-run validation of the chosen setting") and log it in the event log.
- Record a **short-run baseline** (`tier=short, candidate=baseline`) before sweeping;
  this is the tier-1 reference used by `RULES §6` to derive CV/N and by every sweep
  row's `baseline_ref`. Sweep points compare against it, not against the Phase-1 session
  baseline (which ran at default, not locked, HPs).
- Sweep the engineering knobs on short runs (see `EXECUTION §5` for the short-run vs
  full-run cadence). Record each point in `artifacts/benchmarks/results.csv` using
  `SCHEMA §1` (`phase=phase_2_hp`, `candidate=hp_sweep_<label>`, optional
  `hp_values_json`).
- For each HP, pick the value that maximises the primary metric **while keeping the
  quality metric within tolerance** (`WORKLOAD_CARD.md §4`). HP settings that regress
  quality do not count.
- Validate the chosen configuration once on a full time-to-result run (Phase 3 defines
  the target).
- Lock the configuration. Any later change to a locked HP must be logged explicitly and
  compared against a re-measured baseline using the locked HPs — engineering deltas from
  Phase 4 onward are measured against locked HPs, not defaults.

If the sweep surfaces strong coupling that is hard to reason about cleanly, escalate as
an `H-STEER` intervention rather than silently expanding scope.

**Exit criterion:**
- Selected engineering-knob HPs are measured, validated on a full-run, and locked. Their
  values and the measured primary / quality metrics are recorded in `event_log.md`.
- Emit `[PHASE-EXIT 2]`.

---

## 4) Phase 3 — Time-to-result target

The primary objective is **time to result** (TTR): wall-clock time to reach a given
quality level. Phase 3 defines the target — which quality level counts as "done" — by
measuring what the locked-HP baseline achieves in practice.

Inputs: the locked HP configuration from Phase 2, the full benchmark window from
`WORKLOAD_CARD.md §5`, the quality metric and tolerance from `WORKLOAD_CARD.md §3–§4`.

What to do:
- Run at least **three** full-length baseline runs with the locked Phase-2 HPs — the
  minimum `RULES §6` needs to compute tier-2 CV from this baseline. Record them under a
  **single `experiment_id`** with `phase=phase_3_ttr, tier=full, candidate=baseline`.
  The Phase-2 validation run stays in its own `experiment_id` with `phase=phase_2_hp`
  and is **not** counted toward the Phase-3 baseline: it answered a different question
  (does the locked HP config pass a full-run smoke) than Phase 3 (locate the TTR and
  measure its variance).
- Track the quality metric **over time** (not only at the end of the run). This is what
  makes "time to reach quality X" measurable — a single final scalar is not enough.
- Define the target result explicitly. Two options; pick one and record the choice and
  the numerical value in `event_log.md`:
  - **Option A** — target = the baseline's mean end-of-run quality across the Phase-3
    baseline runs. Candidate-quality gating later applies `WORKLOAD_CARD.md §4`
    tolerance to this target; the tolerance is not reused to widen the target itself.
  - **Option B** — target = a pre-declared quality threshold stated in
    `WORKLOAD_CARD.md §10` ("prior art" or explicit target from a previous session).
- Define the baseline **time-to-result**: the wall-clock time at which the baseline
  first reaches the target quality **and** the following-window average of the quality
  metric remains within its CI (i.e. the metric does not drop significantly outside
  mean ± std after the first crossing — our pipelines should not exhibit such drops).
  Record median and range across the baseline full runs.
- If variance on time-to-result is large (e.g. CV > 20%), flag it — downstream
  optimization validation will then need multiple full-length runs, not one. See
  `RULES §6` for how to choose N.

**Exit criterion:**
- Target quality level declared and recorded in `event_log.md`.
- Baseline time-to-result (median and range) recorded.
- Observed variance noted for use in later validation decisions.
- Emit `[PHASE-EXIT 3]`.

---

## 5) Phase 4 — Optimization loop

This is the main body of the session. Profile → hypothesise → change → measure → repeat.
The *rules* governing how runs are measured, how candidates are promoted from short to
full runs, and when a candidate counts as a win live in `RULES §8` (two-tier cadence),
`RULES §6` (noise-aware N), and `RULES §7` (min-win gate). Follow them for every
comparison.

### Entry steps (once, on starting Phase 4)

- Declare the short-run protocol (duration / observations, warmup, metrics recorded) in
  `event_log.md`. Per `RULES §8`, default is ≥2 minutes wall-clock **and** ≥60
  primary-metric observations; record any workload-specific adjustment.
- Measure the short-run baseline with `tier=short, candidate=baseline` and record its
  rows in `results.csv` per `SCHEMA §1`.
- Compute and log a `[NOISE]` entry for the short-run baseline CV per `RULES §6`.
- Acknowledge the promotion rule (`RULES §8`) — you will follow the short→full cadence
  for the rest of the session.

### Loop

Repeat until time budget is exhausted or no further wins are expected:

1. Profile → identify the current top bottleneck.
2. Form a hypothesis and make a **single-variable** change (`RULES §9`).
3. Scan the change against the sync-point checklist (`REFERENCE.md §1`) before
   benchmarking.
4. Measure on Tier 1 (short run). Record rows with `tier=short`, N per `RULES §6`.
5. If the candidate passes the promotion rule (`RULES §8`), validate on Tier 2
   (full run) with `tier=full`.
6. If Tier 2 passes both min-win gates (`RULES §7`) and `quality_verdict=PASS`
   (`RULES §11`), emit `[WIN]` per `RULES §14.3`.
7. Append the post-experiment checklist line (`RULES §14.2`). Do not start the next
   experiment until all boxes resolve.
8. Run the periodic self-audit (`RULES §14.1`) on cadence.

### Exit criterion

Exit when the time budget is exhausted or no candidate from the current bottleneck stack
clears Tier 1 screening. Emit `[PHASE-EXIT 4]` with a short body listing number of
experiments run, number of wins, and the final bottleneck stack.

---

## 6) Wrap-up — deliverables

### 6.1 Session close

At session end, emit `[SESSION-CLOSE]` per `RULES §16` — body either
`clean close: no unresolved bugs` or `closed with unresolved bugs: <list>`. It is
always emitted regardless of outcome (exactly one per session, per `RULES §14.3`
invariants).

### 6.2 Code

- Branch: `agent_<ID>_<short_goal>`
- Commits should mention the bottleneck addressed.

### 6.3 Artifacts folder (required structure)

```
artifacts/
  benchmarks/
    baseline.txt
    results.csv
  profiles/
    <trace files>
    profiler_commands.md
  notes/
    event_log.md
    preflight.txt
  FINAL_SUMMARY.md
```

### 6.4 Final summary

Create `artifacts/FINAL_SUMMARY.md` using `FINAL_SUMMARY_TEMPLATE.md`.
