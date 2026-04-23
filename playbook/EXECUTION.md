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
session artifacts go under `brdg-hackathon/sessions/<workload>/<iteration>/<agent-name>/`.
The iteration folder and filled `WORKLOAD_CARD.md` already exist (the preparer and the
operator set them up); **create your `<agent-name>/` subfolder yourself** — it is your
session artifact root and everything you write lands inside it:

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
Workload branch (agent creates now): hackathon-<workload>-<iteration>-<agent-name>
Hardware: GPU / CPU / RAM
Software: driver / CUDA / framework versions / Python
```

`<brdg-hackathon branch>` and `<short-commit>` come from the brdg-hackathon clone the
agent is running against (`git -C brdg-hackathon rev-parse --abbrev-ref HEAD` and
`git -C brdg-hackathon rev-parse --short HEAD`). `[SESSION-START]` is a milestone tag:
see `RULES §13.3` (role) and `RULES §14.3` (body shape + invariants).

**Workload-repo starting commit consistency.** The `Workload repo: ... @ <starting-commit>`
you emit must match the *Prepared-branch head commit* pinned in `WORKLOAD_CARD §1`.
The operator checked out `hackathon-<workload>-<iteration>` per the root `README.md`;
your starting commit is that branch's HEAD. A mismatch means the operator started from
the wrong base — stop and report, do not paper over it.

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

## 3) Phase 2 — HP search with TTR validation

Engineering-knob HPs (batch size, num_envs, rollout length, dataloader workers, compile
flags, log frequency, etc.) materially affect the primary metric. Optimizing before
these are settled conflates HP wins with engineering wins. Settle them first, then
**lock** them.

The throughput proxy alone is not sufficient for HP selection: an HP set that wins on
the proxy but does not reduce TTR is not a real win. Phase 2 therefore measures TTR at
both ends — default HPs and the proxy-selected candidates — and backtracks through a
ranked shortlist until one candidate clears the TTR gate, or falls back to defaults.
Defaults can already be optimal for a given workload; the fallback path is a valid
outcome, not a failure.

### 3.1 Default-HP TTR baseline and target quality

Run at least **three** full-length runs at default HPs with the quality metric tracked
**over time** (not only at end-of-run — time-to-result requires the trajectory).
Record under a single `experiment_id` with
`phase=phase_2_hp, candidate=baseline_default, tier=full`. Compute and log a `[NOISE]`
entry with the default-HP TTR CV per `RULES §6` — this is the noise reference that
drives N for every candidate validation in §3.3.

The Phase-1 session baseline (one run, sanity-check purpose) does **not** count toward
this baseline.

Then declare the target quality level that defines TTR. Pick one and record the choice
and numerical value in `event_log.md`:
- **Option A** — target = mean end-of-run quality across the default-HP runs above.
  Candidate-quality gating later applies `WORKLOAD_CARD.md §4` tolerance to this
  target; the tolerance is not reused to widen the target itself.
- **Option B** — target = a pre-declared quality threshold stated in
  `WORKLOAD_CARD.md §10` ("prior art" or explicit target from a previous session).

Record the default-HP TTR (median + range) against this target — wall-clock time at
which the run first reaches target quality **and** the following-window average of the
quality metric remains within its CI. These are the session's **first TTR baseline**:
they serve as the comparison reference for §3.3's backtrack gate, and (if no candidate
passes) remain the locked-HP TTR baseline that Phase 3 adopts as the Tier-2 reference
for Phase 4.

### 3.2 Proxy sweep over full HP sets

- Enumerate HPs that plausibly affect the primary metric. Separate them into:
  - **Engineering knobs** — HPs whose value does not change what the algorithm *is*
    (batch size, num_envs, rollout length, dataloader workers, log frequency, compile
    flags, etc.). These are candidates for tuning.
  - **Semantic / coupled HPs** — HPs that change algorithm dynamics or are coupled to
    others (learning rate, exploration schedule, target-sync frequency, replay buffer
    size, etc.). Kept at default unless the human explicitly approves tuning them. See
    `REFERENCE.md §2` for the couplings and schedule effects this builds on.
- Sweep HPs as **full configurations**, not one knob at a time. Each candidate is a
  complete set of engineering-knob values moved together; semantic HPs stay at default.
- Declare the shortlist cap `k_max` up front (e.g. "≤3 candidate HP sets, plus the
  default fallback") and log it in the event log. A small shortlist is intentional:
  use `REFERENCE §2` HP-interaction knowledge to propose a few well-reasoned sets
  rather than blanket-searching the space.
- Record a **short-run baseline** (`tier=short, candidate=baseline`) before sweeping;
  this is the tier-1 reference used by `RULES §6` to derive CV/N and by every sweep
  row's `baseline_ref`. Sweep points compare against it, not against the default-HP
  TTR baseline from §3.1 (which is `tier=full`).
- Sweep the candidate HP sets on short runs (see `EXECUTION §5` for the short-run
  cadence). **Each candidate HP set is measured with N short runs**, N chosen per
  `RULES §6` from the short-run baseline CV and matched against the baseline's N —
  a single short run per candidate is not sufficient and does not defeat Tier-1
  noise. Record each run in `artifacts/benchmarks/results.csv` using `SCHEMA §1`
  (`phase=phase_2_hp`, `candidate=hp_sweep_<label>`, `hp_values_json=<...>`).
- Rank the candidate sets by the proxy metric (median across their N runs),
  discarding any that regress the quality metric outside `WORKLOAD_CARD.md §4`
  tolerance on short runs. Keep the top ≤ `k_max` that pass.

If the sweep surfaces strong coupling that is hard to reason about cleanly, escalate as
an `H-STEER` intervention rather than silently expanding scope.

### 3.3 TTR validation with backtrack

Take the ranked candidates in order and validate each on full-length TTR until one
passes, or the shortlist is exhausted:

1. Run N full-length runs at the candidate HP set, with N chosen per `RULES §6` using
   the default-HP TTR CV from §3.1. Record under a single `experiment_id` with
   `phase=phase_2_hp, candidate=hp_candidate_<label>, tier=full,
   baseline_ref=<default-HP experiment_id>, hp_values_json=<...>`.
2. Apply the `RULES §7` min-win gate (TTR Δ_min, confidence interval excludes zero)
   comparing candidate TTR against the default-HP TTR baseline from §3.1.
3. Apply the `RULES §11` quality gate (`quality_verdict=PASS`, or FAIL /
   INCONCLUSIVE → reject).
4. If both gates pass, **lock** this candidate's HP set. Stop.
5. Otherwise, drop to the next candidate and repeat.

If no candidate passes, lock **default HPs**. Phase 4 then proceeds with the default-HP
TTR runs from §3.1 as the Tier-2 baseline.

Once locked, any later change to a locked HP must be logged explicitly as an
`H-STEER` and re-measured against the locked-HP TTR baseline — engineering deltas from
Phase 4 onward are measured against locked HPs, not defaults.

**Exit criterion:**
- Default-HP TTR baseline recorded (≥3 full runs + `[NOISE]` CV entry).
- Target quality level declared and recorded in `event_log.md`.
- Proxy shortlist with declared `k_max` recorded in `event_log.md`.
- TTR-validation attempts recorded in `results.csv`; rejected candidates carry
  `win_status=EXPERIMENT` with the quality / magnitude reason in `notes`.
- Locked configuration recorded in `event_log.md` — either a winning candidate HP set
  or the default fallback. If a candidate won, its ≥3 full-length runs are captured
  under its own `experiment_id`.
- Emit `[PHASE-EXIT 2]`.

---

## 4) Phase 3 — Tier-2 baseline for optimization

Phase 2 did the search (default-HP TTR baseline, proxy sweep, candidate TTR
validation, locking). Phase 3 turns that output into the formal Tier-2 baseline
Phase 4 compares against, and gates `[WIN]` emissions: no wins may fire before
`[PHASE-EXIT 3]` (`RULES §14.3` invariant).

Inputs: the locked HP configuration from `EXECUTION §3.3`, the target quality declared
in `EXECUTION §3.1`, and the ≥3 full-length TTR runs at the locked config already
captured in Phase 2 (either the winning candidate's runs from §3.3 or the default-HP
runs from §3.1, depending on which way the backtrack resolved).

No new full runs are required. Phase 3 consumes Phase 2's measurements.

What to do:
- Confirm the target quality level from `EXECUTION §3.1` is recorded in `event_log.md`
  and that the locked-config full runs tracked the quality metric over time (required
  at §3.1; if missing, re-run now).
- **Adopt** the locked-config Phase-2 TTR runs as the Tier-2 baseline. Record the
  baseline's `experiment_id` in `event_log.md` with its TTR median, range, and CV —
  this is the single reference Phase 4 Tier-2 comparisons use (`RULES §8`).
- Compute and log a `[NOISE]` entry for the Tier-2 baseline using the locked-config
  CV — this is what drives `RULES §6` N for Phase 4 Tier-2 validations, and may
  differ from the default-HP CV that drove §3.3's backtrack gate.
- If Tier-2 CV is large (e.g. CV > 20%), flag it — Phase 4 validations will then need
  multiple full-length runs, not one.

**Exit criterion:**
- Target quality level confirmed in `event_log.md` (declared in §3.1).
- Tier-2 baseline adopted: locked-config TTR median / range / CV recorded, with its
  `experiment_id` cited for Phase 4 `baseline_ref`.
- `[NOISE]` entry for the Tier-2 baseline CV logged.
- Observed variance noted for Phase 4 N decisions.
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

- Branch: `hackathon-<workload>-<iteration>-<agent-name>` (branched off the
  preparer's `hackathon-<workload>-<iteration>`).
- Commits should mention the bottleneck addressed; put the optimisation
  hypothesis / short goal in the commit messages, not the branch name.

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

### 6.5 Commit policy (before any artifact `git add`)

Before staging the session artifacts — whether you run the commands yourself
or the operator does — read `sessions/README.md §Commit policy` and confirm
the `<agent-name>/` folder contents match it. Specifically:

- Every "always commit" file listed there is present
  (`results.csv`, `baseline.txt`, `event_log.md`, `preflight.txt`,
  `profiler_commands.md`, `FINAL_SUMMARY.md`).
- Any profile you saved is either a committable text/JSON summary, or is
  excluded by `sessions/.gitignore` (the proprietary formats `*.qdrep`,
  `*.nsys-rep`, `*.ncu-rep`, `*.prof`, `*.pb`, `*.sqlite`). Large raw traces
  go to external storage with a link from `FINAL_SUMMARY.md §Evidence`.
- `preflight.txt` and any captured env dumps do not contain secrets (API
  keys, tokens, `.netrc` contents). Redact in place if they do.

Mismatches block the commit until fixed. Do not paper over them with
`git add -f`.
