# EXECUTION — session procedure

> Before running this procedure, you must have already read the filled
> `WORKLOAD_CARD.md` (one level up from your session root) and the `RULES.md` sibling
> in `playbook/`. Rules referenced below as `RULES §X` are defined there.
> `SCHEMA §X` refers to `SCHEMA.md` (also in `playbook/`).

Phases run in order: 1 → 2 → 3 → wrap-up. Each has an explicit exit criterion.
The standing bug-handling procedure (`RULES §16`) can fire from any phase and pauses
the current phase until resolved.

The HP search that used to live inside the session is now done once per iteration
by the preparer-agent (Prep Phase 2, `workload-template/AGENT_HANDOFF.md`). The
session inherits the locked configuration from `WORKLOAD_CARD §10` and goes
straight to bug triage → baseline adoption → optimization.

---

## 1) Bootstrap (before Phase 1)

### 1.1 Session folder layout

Your shell cwd is the workload repo root (e.g. milabench). `brdg-hackathon/` is cloned
inside it. The protocol files live in `brdg-hackathon/playbook/` (read-only); your
session artifacts go under `brdg-hackathon/sessions/<workload>/<iteration>/<agent-name>/`.
The iteration folder, filled `WORKLOAD_CARD.md`, and `prep/` tree already exist (the
preparer and operator set them up); **create your `<agent-name>/` subfolder yourself** —
it is your session artifact root and everything you write lands inside it:

```
<workload-repo>/                                      ← your shell cwd
  (workload source code, benchmarks, etc.)
  brdg-hackathon/
    playbook/                                         ← read-only protocol
      AGENT_HANDOFF.md  RULES.md  EXECUTION.md
      SCHEMA.md  REFERENCE.md  FINAL_SUMMARY_TEMPLATE.md
    sessions/<workload>/<iteration>/                  ← this iteration
      WORKLOAD_CARD.md                                (filled; shared across agents)
      SESSION_START_PROMPT.md
      prep/                                           (preparer's artifacts — read-only)
        prep_event_log.md  prep_results.csv  baseline_capture.txt
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
not to your shell cwd. Benchmark commands (`WORKLOAD_CARD §6`) run from the shell
cwd (workload repo root). Instruction-file references (`RULES §X`, `SCHEMA §X`,
`REFERENCE §X`) resolve to sibling files in `brdg-hackathon/playbook/`. The filled
`WORKLOAD_CARD.md` and `prep/` tree live one level up from your session root.

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
you emit must match the *Prepared-branch head commit* pinned in `WORKLOAD_CARD §1`
and `§10.5`. The operator checked out `hackathon-<workload>-<iteration>` per the root
`README.md`; your starting commit is that branch's HEAD. A mismatch means the operator
started from the wrong base — stop and report, do not paper over it. The Tier-2
baseline pinned in `§10.3` is only valid against that commit.

Workload-specific fields (benchmark command, primary / quality metrics, tolerance,
locked HPs, prep Tier-1 / Tier-2 baselines) come from `WORKLOAD_CARD.md` unchanged —
do not duplicate them into the `[SESSION-START]` body.

### 1.3 Pre-flight environment capture

Run the preflight check (`RULES §5`) **before** Phase 1, using the field list in
`REFERENCE §3`. Store the raw dumps in `artifacts/notes/preflight.txt`; summarise the
key fields in the event log immediately after `[SESSION-START]`.

---

## 2) Phase 1 — Bug-first pass

Before any optimization work, verify the workload is bug-free as-shipped at the
locked HP configuration. Optimization on top of a buggy baseline produces meaningless
deltas.

What to do:
- Read the benchmark entry point and the code paths listed in `WORKLOAD_CARD §1`
  (target workload) and `§7` (allowed edits). Form a mental model of control flow, data
  flow, and the likely hot path.
- Run the baseline command from `WORKLOAD_CARD §6` end-to-end **once with the locked
  HPs from `§10.1`** (apply them via whatever mechanism the workload exposes — CLI
  flags, config file edit, env vars). This is the session baseline, not a
  default-HP run. Confirm:
  - the run completes successfully,
  - the primary metric and quality metric are produced, and
  - the extraction recipes in `WORKLOAD_CARD §2` and `§3` actually yield values from
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
- One clean end-to-end baseline run at the locked HPs, with primary and quality
  metrics extracted, the run recorded in `results.csv` with
  `phase=phase_1_bugfix, candidate=baseline, tier=full,
  hp_values_json=<card §10.1 value>`, the corresponding event-log entry tagged
  `[BASELINE]` (`RULES §13.3`), and any bugs either fixed-and-committed or
  explicitly flagged to the human.
- Emit `[PHASE-EXIT 1]`.

---

## 3) Phase 2 — Tier baseline adoption

The HP lock and both tier baselines were produced during preparation and pinned in
`WORKLOAD_CARD §10`. Phase 2 is short: confirm the session host reproduces the
Tier-1 baseline, adopt the card's Tier-2 baseline as-is, and gate `[WIN]`
emissions on `[PHASE-EXIT 2]` (`RULES §14.3` invariant).

### 3.1 Adopt the Tier-2 baseline

No new full runs. Record the card's locked-HP Tier-2 baseline as the session's
Tier-2 reference:

- In `event_log.md`, log a `[NOISE]` entry citing `WORKLOAD_CARD §10.3`: prep
  `experiment_id`, TTR median / range, CV, N. This CV drives `RULES §6` N for every
  Phase 3 Tier-2 validation.
- Every Phase 3 `tier=full` row's `baseline_ref` will point at the prep
  `experiment_id` from `§10.3`. The prep row lives in `prep/prep_results.csv`
  (`SCHEMA §2`), not in your `results.csv`; the `baseline_ref` is a cross-CSV
  pointer.
- Confirm the target quality from `WORKLOAD_CARD §10.2` in the event log — the
  numeric value Phase 3 Tier-2 TTR is measured against.

### 3.2 Re-measure the Tier-1 baseline on this host

The short-run baseline is cheap. Re-measure it on the session host to catch
prep-host / session-host drift (different driver, thermal state, co-tenant) before
Phase 3 comparisons start.

- Declare the short-run protocol in `event_log.md` — duration, observation count,
  warmup — matching `WORKLOAD_CARD §10.4` exactly, and `RULES §8` (≥2 min wall-clock
  AND ≥60 primary-metric observations, unless the card documents a different
  workload-specific window).
- Measure with `phase=phase_2_adopt, candidate=baseline, tier=short`, recording N
  runs in `results.csv` (`SCHEMA §1`).
- Compute median and CV. Log a `[NOISE]` entry comparing your session CV to the
  card's `§10.4` value, and your session median to the card's median CI.
- **If the session median falls within the card's CI** (derived from the card's
  median ± the Welch-style CI of N short runs at CV from `§10.4`), the re-measurement
  passes — the session-host Tier-1 baseline is this session's N-run median, and the
  session CV drives `RULES §6` N for Phase 3 Tier-1 comparisons.
- **If it falls outside**, treat it as a host-or-environment drift signal: log
  `[DRIFT]` per `RULES §5`, escalate as `H-OPS`, and do not enter Phase 3 until the
  human either (a) confirms the drift is benign and authorises proceeding (note it
  in the event log) or (b) fixes the environment.

### 3.3 Exit criterion

- Tier-2 baseline adopted: card `§10.3` median / range / CV / prep `experiment_id`
  recorded as `[NOISE]` in `event_log.md`, cited for future `baseline_ref`.
- Tier-1 baseline re-measured: N short runs in `results.csv`
  (`phase=phase_2_adopt, tier=short`), `[NOISE]` entry logged, drift check
  resolved.
- Target quality confirmed in `event_log.md` (source: `WORKLOAD_CARD §10.2`).
- Emit `[PHASE-EXIT 2]`.

---

## 4) Phase 3 — Optimization loop

This is the main body of the session. Profile → hypothesise → change → measure → repeat.
The *rules* governing how runs are measured, how candidates are promoted from short to
full runs, and when a candidate counts as a win live in `RULES §8` (two-tier cadence),
`RULES §6` (noise-aware N), and `RULES §7` (min-win gate). Follow them for every
comparison. HPs stay at the locked values from `WORKLOAD_CARD §10.1` — any change to
a locked HP must be logged as `H-STEER` first and re-validated against the Tier-2
baseline (`RULES §4`).

### Loop

Repeat until time budget is exhausted or no further wins are expected:

1. Profile → identify the current top bottleneck.
2. Form a hypothesis and make a **single-variable** change (`RULES §9`).
3. Scan the change against the sync-point checklist (`REFERENCE §1`) before
   benchmarking.
4. Measure on Tier 1 (short run). Record rows with
   `phase=phase_3_iter, tier=short`, N per `RULES §6`, `baseline_ref` pointing at
   the Phase-2 Tier-1 re-measurement.
5. If the candidate passes the promotion rule (`RULES §8`), validate on Tier 2
   (full run) with `phase=phase_3_validation, tier=full`, `baseline_ref` pointing
   at the Tier-2 prep `experiment_id` from `WORKLOAD_CARD §10.3`.
6. If Tier 2 passes both min-win gates (`RULES §7`) and `quality_verdict=PASS`
   (`RULES §11`), emit `[WIN]` per `RULES §14.3`.
7. Append the post-experiment checklist line (`RULES §14.2`). Do not start the next
   experiment until all boxes resolve.
8. Run the periodic self-audit (`RULES §14.1`) on cadence.

### Exit criterion

Exit when the time budget is exhausted or no candidate from the current bottleneck stack
clears Tier 1 screening. Emit `[PHASE-EXIT 3]` with a short body listing number of
experiments run, number of wins, and the final bottleneck stack.

---

## 5) Wrap-up — deliverables

### 5.1 Session close

At session end, emit `[SESSION-CLOSE]` per `RULES §16` — body either
`clean close: no unresolved bugs` or `closed with unresolved bugs: <list>`. It is
always emitted regardless of outcome (exactly one per session, per `RULES §14.3`
invariants).

### 5.2 Code

- Branch: `hackathon-<workload>-<iteration>-<agent-name>` (branched off the
  preparer's `hackathon-<workload>-<iteration>`).
- Commits should mention the bottleneck addressed; put the optimisation
  hypothesis / short goal in the commit messages, not the branch name.

### 5.3 Artifacts folder (required structure)

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

### 5.4 Final summary

Create `artifacts/FINAL_SUMMARY.md` using `FINAL_SUMMARY_TEMPLATE.md`.

### 5.5 Commit policy (before any artifact `git add`)

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
