# RULES — Optimization Hackathon

These rules govern every action you take during the session. Read them in full before
starting `EXECUTION.md`; keep them loaded throughout — `EXECUTION.md` cites them
repeatedly (as `RULES §X`). Workload-specific details (entry command, metric
definitions, tolerance, allowed edits) live in `WORKLOAD_CARD.md`. The `results.csv`
column spec referenced by `§14.2` lives in `SCHEMA.md`.

---

## 1) Scribe ownership — you are the primary scribe

You (the coding agent) are the **primary scribe**.

You must:
- Create and maintain `artifacts/notes/event_log.md`
- Record every benchmark / eval result in `artifacts/benchmarks/results.csv`
  (schema: `SCHEMA §1`)
- Save profiling artifacts and profiler commands under `artifacts/profiles/`
- Log **human interventions** using H-* tags whenever the human:
  - reframes goal / constraints (**H-STEER**)
  - finds bug / root cause (**H-DEBUG**)
  - makes an architecture decision (**H-ARCH**)
  - fixes ops / environment / run issues (**H-OPS**)

If unsure whether something counts as an intervention, **log it anyway**. If the human
prompts "log that as H-OPS", comply and add a short entry.

Human responsibility: **verify** you are logging correctly, and prompt you when you
missed an intervention.

---

## 2) Allowed / disallowed work

Workload-specific boundaries: see `WORKLOAD_CARD.md §7` (allowed edits) and `§8`
(disallowed / semantic surfaces).

### Allowed (generic)
- Systems / engineering optimizations: compilation behavior, Python overhead, data
  movement, logging overhead, batching, buffer / dataloader sampling, vectorization,
  synchronization points, etc.
- Small refactors when clearly tied to measured bottlenecks.

### Disallowed unless explicitly approved (semantic changes)
- Changing the algorithm, quality definition, or environment / dataset semantics
- Changing evaluation definition or metric definitions
- "Optimizations" that reduce work (fewer steps / episodes / iterations) without
  documenting and obtaining approval

If a change might be semantic, label it **SEMANTIC CHANGE** and run stronger quality
checks (`§11`).

---

## 3) Success criteria

**Primary objective.** Reduce **time-to-result** (TTR, defined in `EXECUTION §3.1`
and adopted as the Tier-2 reference in `EXECUTION §4`) at preserved quality vs
baseline. TTR is the end-goal metric and is expensive to measure, so candidate
screening is guided by a cheaper **throughput proxy** — the primary metric declared
in `WORKLOAD_CARD.md §2` (e.g. steps/sec, samples/sec). Tier 1 short runs measure the
throughput proxy for screening; Tier 2 full runs measure TTR and are the sole source
of `[WIN]` emissions (`§8`). A throughput improvement that does not translate into a
TTR improvement is not a win. Phase 2's HP search applies this principle inside HP
selection too: the proxy ranks candidates, but TTR gates the lock (`EXECUTION §3.3`).

(Exception: if `WORKLOAD_CARD §2` already declares a TTR-style primary metric such as
`time-to-accuracy`, Tier 1 short runs serve as a noisy screening signal on the quality
trajectory, and Tier 2 remains the sole WIN emitter.)

**Constraint: preserve quality.** Do not degrade the quality metric beyond the tolerance
stated in `WORKLOAD_CARD.md §4`. If the quality metric is noisy, do not hand-wave —
report variance and decide PASS / FAIL / INCONCLUSIVE explicitly (`§11`).

**Scorecard.** You will also be compared on:
- Time to first measurable win
- Dead-end rate (failed experiments / reverts)
- Human intervention count / severity
- Reproducibility (clear commands + stable results)
- Engineering quality (maintainable diff; minimal invasiveness)
- Evidence-based reasoning (profiling → targeted fixes)

---

## 4) "Baseline" — meanings in this protocol

The noun *baseline* is overloaded. Disambiguate when citing:

- **Session baseline** — the Phase-1 end-to-end run of the unmodified workload with
  default settings (`EXECUTION §2`). Tagged once with `[BASELINE]` (`§13.3`).
- **Tier baseline** — the reference measurement within a tier. Each tier has one:
  the **short-run baseline** (recorded in `EXECUTION §3.2` / Phase 2, used by all
  Tier-1 comparisons) and the **full-run baseline** (≥3 full-length TTR runs at the
  locked HP configuration, used by all Tier-2 comparisons).
  The first full-run baseline produced is always the **default-HP TTR baseline**
  (`EXECUTION §3.1`): it grounds TTR for the session and serves as the comparison
  reference for Phase 2's backtrack gate (`§3.3`). If a candidate HP set wins the
  backtrack, its ≥3 full runs (`§3.3`) become the locked-HP TTR baseline; if no
  candidate passes, the default-HP runs themselves are the locked-HP TTR baseline.
  Either way, Phase 3 (`EXECUTION §4`) adopts the locked-HP runs as the Tier-2
  baseline for Phase 4.
- **Comparison baseline** — the specific `experiment_id` a candidate compares against
  in `results.csv` (`baseline_ref` column). Must be in the same tier as the candidate.

Unless prefixed, "baseline CV" / "baseline N" in `§§6–7` mean **the tier baseline for
the tier of the comparison in question**.

---

## 5) Pre-flight environment check

Capture environment state at session start so that measurement drift (GPU throttling,
new CUDA processes, env-var flips, framework bumps) does not masquerade as optimization
wins. Store raw dumps in `artifacts/notes/preflight.txt` and summarise key fields at
the top of `artifacts/notes/event_log.md`. The field list to capture is in
`REFERENCE §3`.

This check is the **first entry in the session's event log** — it runs before Phase 1
(`EXECUTION §1.3`).

**Drift rule.** Any change in the captured state during the session (env-var flip, GPU
clock change, framework version bump, new co-tenant process) invalidates cross-boundary
comparisons. If drift occurs:

- log `[DRIFT]` in `event_log.md` with what changed,
- re-run the relevant baseline under the new state,
- tag prior results with the environment snapshot they belong to (via the
  `env_snapshot_id` column in `results.csv`; see `SCHEMA §1`).

Do not silently compare numbers across a drift boundary.

---

## 6) Noise-aware comparison rule

The number of measured runs (N) per benchmark comparison is derived from the **observed
baseline coefficient of variation** (CV = stddev / mean of the primary metric), not a
fixed default. Fixed N wastes time when noise is low and produces false wins when noise
is high.

Measure CV once per tier from the baseline measurements already produced upstream.
Tier-2 CV comes from the locked-HP TTR runs adopted in `EXECUTION §4` (Phase 3) — i.e.
the full-length runs captured in `EXECUTION §3.3` (winning candidate) or `EXECUTION §3.1`
(default fallback). Tier-1 CV comes from the short-run baselines in `EXECUTION §3.2`
(Phase 2 sweep) and `EXECUTION §5` (Phase 4 loop entry). Phase 2's backtrack gate
(`EXECUTION §3.3`) uses the default-HP TTR CV from `EXECUTION §3.1` as its Tier-2
noise reference — that CV may differ from the locked-HP CV adopted in Phase 3. Record
each in `event_log.md` as a `[NOISE]` entry alongside the baseline results. Each tier
/ reference has its own CV and therefore its own N.

**Decision table for N per comparison.**

| Baseline CV of primary metric | N (measured runs) | Notes |
|-------------------------------|-------------------|-------|
| CV < 5%                       | 3                 | Low-noise regime; a single mean is trustworthy. |
| 5% ≤ CV < 15%                 | 5                 | Moderate noise; extra runs needed to separate signal. |
| 15% ≤ CV < 25%                | ≥5                | High noise; the min-win gate (`§7`) must reject wins whose CI crosses zero. |
| CV ≥ 25%                      | Switch to full-run TTR validation | Per-step throughput is too noisy; time-to-result integrates over the run and gives a cleaner signal. |

**Applying the rule.**
- For every non-trivial change, compare baseline vs candidate using N measured runs per
  side **under the same tier**. Compute median / min / max (as `§10` requires), plus a
  confidence-interval delta (Welch's t, bootstrap, or equivalent).
- Do not compare a 3-run candidate against a 5-run baseline — re-measure the baseline
  with matching N if needed.
- The quality metric has its own noise; `§7` (min-win gate) and `§11` (correctness)
  cover how quality failures interact with throughput wins.

**Watch for CV drift.** If a candidate changes the variance of the primary metric (e.g.
by altering synchronization behavior), recompute CV and re-derive N for subsequent
comparisons. Log a follow-up `[NOISE]` entry.

---

## 7) Minimum-win gate

Without a declared win threshold, noise looks like progress — small blips on a noisy
baseline fire spurious `[WIN]` events that don't survive re-measurement. Every `[WIN]`
must pass two gates:
1. **Magnitude gate** — improvement ≥ a declared threshold Δ_min, measured in the
   **tier-native metric** (throughput proxy at Tier 1, TTR at Tier 2; see `§8`). Δ_min
   is set per tier; a single session-global Δ_min is fine only when both tiers share
   the same metric.
2. **Confidence gate** — the confidence interval of the delta (computed with the N chosen
   by `§6`) excludes zero.

**Both** must pass. Failure of either leaves the candidate as an `[EXPERIMENT]`, not a
`[WIN]`.

**Choosing Δ_min.**
- Δ_min must exceed the baseline CV measured in `§6` — otherwise noise alone can cross
  it.
- A reasonable default: `Δ_min = max(2 × baseline_CV, 3%)`.
- Record Δ_min in `event_log.md` at session start, right after the `§6` `[NOISE]` entry.
- For cross-agent comparability on the same workload, pre-declare Δ_min in
  `WORKLOAD_CARD.md §10`. Otherwise it is session-local.

**Quality-gate coupling.** A candidate that improves the primary metric but fails the
quality tolerance (`WORKLOAD_CARD.md §4`) does not count as a win regardless of
magnitude. See `§11`.

**Tier coupling.** `[WIN]` is emitted only on Tier 2 (full-run) validation; see `§8`.
Tier 1 improvements that exceed Δ_min are candidates for promotion, not wins.

**Sub-threshold improvements.** Keep logging them as `[EXPERIMENT]` with the measured
delta — they may aggregate into a later win, feed profiling intuition, or reveal noise
characteristics. Do not bundle them silently to manufacture a win; the change-one-thing
discipline (`§9`) still applies.

---

## 8) Two-tier measurement cadence

Full-scale iteration is too slow; short-run-only wins produce false positives (JIT /
compile / autotune amortisation, early-run dynamics, noise). Every optimization-loop
measurement runs under one of two tiers.

**Tier 1 — Iteration (short runs).** Used for profiling, screening hypotheses, and
eliminating dead ends. Budget: run until **both** thresholds are met — ≥2 minutes of
wall-clock **and** ≥60 primary-metric observations (adjust for the workload if clearly
inappropriate and record the adjustment). Same warmup + repeats protocol as `§10` but
at the reduced window. Results recorded in `artifacts/benchmarks/results.csv` with
`tier=short`. Decisions from this tier are **provisional**.

**Tier 2 — Validation (full time-to-result).** Used to accept or reject a candidate as
a real win. Full benchmark window from `WORKLOAD_CARD.md §5`, evaluated against the
target quality declared in `EXECUTION §3.1` and the Tier-2 baseline adopted in
`EXECUTION §4` (Phase 3). Results recorded with `tier=full`. Only full-run validation
produces a genuine win.

**Metric per tier — throughput proxy vs end-goal TTR.** Each tier uses a tier-native
metric; do not mix them across a comparison.
- **Tier 1 — throughput proxy.** The primary metric declared in `WORKLOAD_CARD §2`
  (per-step or per-sample throughput). Cheap, fast, noisy. Used for profiling and
  candidate screening. Δ_min at Tier 1 is in throughput units (`§7`).
- **Tier 2 — TTR.** Wall-clock time to reach the target quality declared in
  `EXECUTION §3.1` (adopted as the Tier-2 reference in `§4`). Integrates run-time
  dynamics, absorbs per-step noise, and is the session's end-goal metric. Δ_min at
  Tier 2 is in TTR units (seconds or %-reduction). `[WIN]` is Tier-2-only and reports
  `delta_ttr` (`§14.3`).

If `WORKLOAD_CARD §2` declares a TTR-style primary metric directly, Tier 1 still
screens on short-run throughput / quality trajectory, but the `[WIN]` delta at Tier 2
is reported against the same TTR-style metric (no renaming needed).

**Promotion rule.** A candidate moves from Tier 1 to Tier 2 when it
  (i) shows a consistent improvement over the short-run baseline across repeats,
  (ii) exceeds the minimum-win gate (`§7`), and
  (iii) has plausible profiling or mechanistic support.
Candidates that fail any of these stay in Tier 1 or are discarded. Do not waste full-run
budget on speculative candidates.

**Separation.** Do not compare short-run numbers to full-run numbers. Every
baseline-vs-candidate comparison must use the same tier. Each tier has its own baseline
— the short-run baseline measured during HP screening in `EXECUTION §3.2` (Phase 2),
the Tier-2 full-run baseline measured in `EXECUTION §3` (Phase 2) and adopted in
`EXECUTION §4` (Phase 3) for Phase 4 use.

**What short runs do *not* capture.**
- JIT / compile / autotune effects that amortise over full runs.
- The quality trajectory — short-run quality is a smoke check, not a verdict.
- Time-to-result under full training dynamics.
These gaps are exactly why Tier 2 exists.

---

## 9) Change-one-thing discipline

Every experiment changes **exactly one variable** relative to its comparison baseline.
Bundled changes produce deltas that cannot be attributed to any specific cause, cannot be
partially reverted, and confuse later profiling and root-cause analysis.

**What counts as "one thing".**
- A single code-level change (one function / kernel / loop rewritten).
- A single config flag toggle.
- A single HP change — or a single **coupled HP group** when the coupling
  (`REFERENCE.md §2`) requires them to move together. When moving a group, document it
  explicitly in `event_log.md` (e.g. "grouped change: batch_size + LR per linear-scaling
  rule").
- A single compiler / runtime flag.

**What must be split.**
- Refactor + algorithmic optimization → split into two experiments.
- Two independent performance fixes → split.
- Changing an HP + changing code → split.
- Introducing a feature flag and simultaneously changing its default → split (introduce
  it disabled and measure; then flip the default and measure).

**Commit discipline.** One change per commit. Commit messages should name the bottleneck
addressed (matching `EXECUTION §6.2`). This keeps `git bisect`, revert, and the
FINAL_SUMMARY commit list clean.

**Rollback.** A failed candidate is reverted by backing out its single commit. No
cross-contamination with other in-flight work.

**Reporting.** Each row in `results.csv` corresponds to a single change vs its
baseline. Bundled rows hide attribution and fail the `§11` correctness audit.

**Exceptions.**
- **Coupled-HP groups** (`REFERENCE.md §2`).
- **Refactor-prep commits** that provably don't change behaviour (identical output for a
  fixed seed / fixed input) may be bundled into a refactor, but labelled
  `NO-OP REFACTOR` in the commit message and not reported as a measured experiment.
- **Trivial style / comment cleanup** co-located with a real change is acceptable and
  not reported.

---

## 10) Benchmark protocol

### 10.1 Keep it comparable
- Same command / config for baseline and comparisons (unless testing config changes).
- Same benchmark window (either "run for X steps/iterations" or "run for Y seconds"; be
  explicit — defined in `WORKLOAD_CARD.md §5`).
- Warmup then repeats.

### 10.2 Warmup + repeats
- 1 warmup run (discard).
- Then N=3–5 measured runs (default; **`§6` supersedes this** once the baseline CV is
  known — N then comes from the CV decision table).
- Record median / min / max.

### 10.3 Metrics per measured run
Minimum:
- Primary metric + its definition.
- Quality snapshot (reward / accuracy / equivalent).
- Peak GPU memory (MiB), if available.

Optional: GPU util avg, CPU util avg, compile time, variability notes.

Store:
- `artifacts/benchmarks/baseline.txt` (raw output).
- `artifacts/benchmarks/results.csv` (structured summary; `SCHEMA §1`).

---

## 11) Correctness / quality checks

Quality is the **constraint** on every optimisation (`§3`). The metric definition,
extraction recipe, and tolerance come from `WORKLOAD_CARD.md §3–§4`. A primary-metric
improvement with a failing quality check is not a win (`§7`).

Each candidate improvement must include at least:
- Smoke: no NaN / inf; finite loss; no crash for short horizon.
- Quick quality check: fixed short eval; compare to `WORKLOAD_CARD.md §4` tolerance.
- If **SEMANTIC CHANGE**: stronger eval (more episodes / longer horizon / multiple seeds).

Rules:
- If the primary metric improves but quality fails tolerance → does not count as
  success.
- If quality is inconclusive (too noisy / too short), label **INCONCLUSIVE** and
  explain.

**Noisy quality metric.** If the quality metric's confidence interval straddles the
tolerance boundary:
- Escalate evaluation: more seeds, longer horizon, or more eval episodes (mirror the
  tier's N from `§6` applied to the quality metric).
- If the CI still straddles after escalation, record `quality_verdict=INCONCLUSIVE` and
  do **not** emit `[WIN]` regardless of the primary-metric delta.
- Record the number of seeds / eval length used in the `notes` column of `results.csv`
  so the verdict is reproducible.

---

## 12) Profiling evidence

Produce at least one profiler artifact. For each profiling session, save:
- profiler command line,
- trace filename(s),
- brief notes: bottlenecks observed, hypothesis formed.

Store under `artifacts/profiles/` and list commands in
`artifacts/profiles/profiler_commands.md`. Tool choices by layer: `REFERENCE §4`.
Commit policy for large traces (size cap, which formats are kept vs linked
externally) is in `sessions/README.md §Commit policy` — proprietary-format
traces (`*.qdrep`, `*.nsys-rep`, `*.ncu-rep`, `*.prof`) are not committed;
save a text or JSON summary alongside instead.

---

## 13) Logging during the session

### 13.1 Event log location
`artifacts/notes/event_log.md`

### 13.2 Minimal event entry format
```
T+___  [TAG]
Action/Change: ___
Hypothesis/Reason: ___
Result: ___  (metric: ___; baseline: ___; delta: ___)
Evidence: ___ (log path / trace filename)
Next: ___
```

### 13.3 Allowed tags — canonical table

One table covers every tag. The `Role` column says how the tag is consumed:
- **milestone** — parsed by `score_session.py` for timing / invariant checks
  (body format + invariants in `§14.3`).
- **overlay** — annotated on the session timeline by `plot_results.py` but not a
  timing milestone.
- **—** — neither; plain event-log entry.

| Group | Tag | When emitted (rule) | Role |
|-------|-----|---------------------|------|
| Experiment / change-tracking | `BASELINE` | Phase 1 session baseline — first successful end-to-end run (`EXECUTION §2`). Tier baselines (Phase 2 short-run, Phase 2 default-HP TTR, and the locked-HP TTR adopted in Phase 3) are marked by their own `[NOISE]` entries, not re-tagged. | milestone |
|  | `HYPOTHESIS` | Cause-effect claim a candidate tests. | — |
|  | `CHANGE` | Code / config change committed for measurement. | — |
|  | `EXPERIMENT` | Measured run recording primary / quality deltas vs baseline. | — |
|  | `REVERT` | A prior candidate was reverted (`§16`). | overlay |
| Correctness / debugging | `BUG` | Bug surfaced (`§16`). | overlay |
|  | `FIX` | Bug fix committed (`§16`). | — |
|  | `BLOCKED` | Agent is stuck (`§13.4`). | overlay |
| Measurement / environment | `PROFILE` | New profiling artifact saved (`§12`). First per session is a milestone; subsequent are overlays. | milestone (first) / overlay |
|  | `DRIFT` | Environment-state change (`§5`). | overlay |
|  | `NOISE` | CV / N decision recorded (`§6`). | overlay |
| Session-timeline milestones | `SESSION-START` | First event-log entry at `T+0`, emitted by `EXECUTION §1.2`. Body records session identity and the brdg-hackathon branch + commit (body shape in `§14.3`). Exactly one per session. | milestone |
|  | `PHASE-EXIT N` (N ∈ {1,2,3,4}) | Phase N's exit criterion met (`EXECUTION §2–§5`). Exactly one per N per session. | milestone |
|  | `SESSION-CLOSE` | End-of-session marker emitted by `EXECUTION §6.1` regardless of outcome. Body: `clean close: no unresolved bugs` or `closed with unresolved bugs: <list>` (see `§16`). Exactly one per session. | milestone |
|  | `WIN` | Experiment passes both `§7` gates on Tier 2 with `quality_verdict=PASS`. | milestone |
| Discipline cadence | `AUDIT` | Periodic self-audit (`§14.1`). | overlay |
| Human interventions | `H-STEER` | Human reframed goal / scope (`§1`). | overlay |
|  | `H-DEBUG` | Human found bug / root cause (`§1`). | overlay |
|  | `H-ARCH` | Human made architecture decision (`§1`). | overlay |
|  | `H-OPS` | Human fixed env / run / tooling issue (`§1`). | overlay |

Milestone body-format templates, invariants, and the `delta_ttr` sign convention are
in `§14.3`.

### 13.4 If you get stuck
Log a `[BLOCKED]` entry: cause, what you tried, next hypothesis. Then switch to
profiling or add coarse timers to isolate bottlenecks.

---

## 14) Agent discipline

Behavioural rules so the log, results file, and session timeline remain mechanically
useful for analysis.

### 14.1 Periodic self-audit checkpoint

Agents drift over many short iterations; the event log becomes read-only and prior
context decays. A scheduled self-audit forces the agent to re-read recent entries and
reconcile the plan.

**When.** Whichever comes first:
- Every ~30 minutes of wall-clock time, or
- Every N experiments (default N=5; short-run iteration may warrant audits more
  frequently than full-run validation).

**What to do.**
1. Re-read the event-log entries since the last audit.
2. Update the **prioritised bottleneck stack**: 3–7 bottlenecks to attack, ordered by
   expected impact × confidence, each tagged with the profiling / measurement evidence
   that justifies it. The latest stack supersedes earlier ones.
3. Reconcile against the **current plan** (declared in Phases 2 / 3 / 4, i.e.
   `EXECUTION §3–§5`, or an explicit update): are in-flight experiments aligned with
   the stack? If not, either pause and switch, or update the plan explicitly. No silent
   drift.
4. Note dead ends briefly (pointers to the relevant `[REVERT]` / `[EXPERIMENT]`
   entries) so they don't get re-tried by accident.

**Log format.** Each audit is a dedicated entry in `event_log.md`:

```
T+___  [AUDIT]
Since last audit: <N experiments, K human interventions, M wins>
Bottleneck stack (priority order): 1) ___ (evidence: ___)
                                   2) ___ (evidence: ___)
                                   ...
Plan reconciliation: on-track / adjusted (explain)
Dead ends to avoid: <brief list, pointing at event-log entries>
Next: <top bottleneck, planned experiment, tier>
```

If the audit surfaces a stale plan that needs human input, escalate as `H-STEER`.

### 14.2 Post-experiment checklist pattern

Agents silently omit log entries (especially H-interventions, CSV rows, and quality
verdicts). A one-line checklist after every experiment makes omissions visible.

**Checklist line.** Append a single line at the end of every `[EXPERIMENT]` (or
`[CHANGE]` / `[REVERT]` / `[FIX]`) event-log entry:

```
Checklist: ran[_] logged[_] csv[_] quality[_] one-thing[_] h-check[_]
```

Each box must resolve before moving to the next experiment.

| Box         | Meaning |
|-------------|---------|
| `ran`       | The run completed end-to-end (for both sides of the comparison). If not, downgrade the entry to `[BLOCKED]`. |
| `logged`    | This event-log entry is complete with the `§13.2` template (Action, Hypothesis, Result, Evidence, Next). |
| `csv`       | Row(s) appended to `artifacts/benchmarks/results.csv` using `SCHEMA §1`, including `tier`, matched N, `env_snapshot_id`. |
| `quality`   | `§11` correctness / quality verdict reached — PASS / FAIL / INCONCLUSIVE — and recorded in `results.csv`. |
| `one-thing` | `§9` verified — the change is a single variable (or a declared coupled-HP group). If no, split and redo. |
| `h-check`   | Agent actively reviewed the experiment window for human interventions and logged any as `H-STEER` / `H-DEBUG` / `H-ARCH` / `H-OPS`. "No interventions observed" still counts as a tick — the point is that the check was done. |

**When an item is `✗`.** Do not start the next experiment until the omission is
resolved. Failures are log-worthy themselves: if `csv✗` because the extraction recipe
broke, log a `[BUG]` and enter the standing bug-handling procedure (`§16`).

**Interaction with `§14.1`.** The periodic self-audit scans recent entries for
checklist misses — any experiment whose checklist is incomplete is listed in the
`[AUDIT]` entry under "dead ends / loose ends" until resolved.

### 14.3 Milestone body format, invariants, and sign convention

Milestones (role column in `§13.3`) are emitted at well-defined points so
`plot_results.py` and `score_session.py` can parse them without heuristics.

**Tag line format.** Use the standard `§13.2` entry block with the tag in the `[TAG]`
position. For `[SESSION-START]`, `[PHASE-EXIT N]`, `[SESSION-CLOSE]`, and `[WIN]`, the
body follows a canonical shape so parsing stays mechanical:

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

```
T+...  [PHASE-EXIT 2]
Locked HPs: batch_size=128, num_envs=64, rollout_length=32 (candidate hp_set_A)
Default-HP TTR: 1820s median (CV 4.2%, N=3)
Locked-HP TTR: 1485s median (CV 5.1%, N=3)
Target quality: 0.87 mean-acc (Option A: default-HP mean end-of-run)
Next: Phase 3 (adopt Tier-2 baseline)
```

```
T+...  [WIN]
experiment_id: 2026-03-24_A:0042
change: fused replay sampler
delta_ttr: -7.2% (CI: [-8.6%, -5.8%], N=5, tier=full)
quality_verdict: PASS
```

**Invariants** (checked by `score_session.py`):
- Exactly one `[SESSION-START]` per session, at `T+0` (first tagged entry). Body must
  include `Hackathon repo: <branch> @ <commit>` so the corpus version used is
  recoverable.
- Exactly one `[PHASE-EXIT N]` per `N ∈ {1,2,3,4}` per session. A missing tag means
  the phase was not completed; a duplicate means an edit error.
- Exactly one `[SESSION-CLOSE]` per session.
- Every `[WIN]` has a matching `results.csv` row with `tier=full`, `win_status=WIN`,
  `quality_verdict=PASS`.
- `[PHASE-EXIT 2]` must follow at least one `[BASELINE]` (Phase 2 needs a baseline to
  screen HPs against).
- `[WIN]` events only appear after `[PHASE-EXIT 3]` (no Phase-4 wins before the
  Tier-2 baseline is adopted; the TTR target itself is declared earlier, in
  `EXECUTION §3.1`).

**Sign convention for `delta_ttr`.** TTR is a time; a reduction is an improvement.
A winning `delta_ttr` is negative (e.g. `-7.2%` = "7.2% faster to target quality"). The
CI brackets make direction unambiguous. If a downstream consumer prefers the
"positive = improvement" sign, derive `ttr_reduction = -delta_ttr`.

---

## 15) Logging-overhead reporting

Benchmarks often include periodic logging and synchronization points. If you change
logging frequency, callback behavior, or synchronization:
1) Mark the change as **MEASUREMENT / LOGGING OVERHEAD** optimization.
2) Report the primary metric:
   - with original logging behavior (comparable), and
   - with modified logging behavior (if you keep it).
3) Ensure quality checks remain valid.

Pairs with `REFERENCE.md §1` (sync-point detection checklist): if you remove or add a
sync point, also apply this rule.

---

## 16) Standing bug-handling procedure

Invoked whenever a bug surfaces in any phase (Phase 1 triage, Phase 4 optimization, or
later). Running further optimization on top of an unresolved bug invalidates every
measurement until it is fixed.

**Signals.** Unexpected crash, NaN / inf, metric-extraction failure, quality drops
unexplained by the change made, results inconsistent with profiling evidence, or Tier 1
and Tier 2 deltas diverging beyond the CI implied by `§6`'s N for the relevant tier.

**Procedure.**
1. **Pause optimisation** and log `[BUG]` with the symptom and the commit where it first
   appeared.
2. **Triage origin.**
   - Bug introduced by the last change → log `[REVERT]`, re-measure the baseline, then
     decide whether to retry more carefully or drop the hypothesis.
   - Pre-existing bug (Phase 1 miss) → treat as a new Phase 1 finding: fix in allowed
     territory, or escalate as `H-DEBUG` / `H-STEER` if the fix would touch semantic
     surfaces (`WORKLOAD_CARD.md §8`).
3. **Delegate when context cost is high.** If investigation requires many file reads,
   multiple hypotheses, or unrelated code paths, delegate to a sub-agent so the main
   agent's context stays focused on optimisation. The sub-agent receives the failing
   command, the hypothesis to investigate, and the allowed-edit surfaces, and returns a
   minimal diff + root-cause explanation. The main agent reviews the proposed fix before
   applying it.
4. **Fix in its own commit** and log `[FIX]` with the root cause.
5. **Re-measure.** A bug fix shifts the baseline. Prior wins measured across the buggy
   code are suspect — re-measure them, or annotate them as `INVALIDATED` in
   `results.csv` rather than deleting them. Never carry deltas across a bug-fix boundary
   without re-measurement.
6. **Resume** with a brief resumption note in `event_log.md` pointing at the `[FIX]` so
   the session timeline stays readable.

Escalate as `H-DEBUG` / `H-STEER` if the bug is in disallowed territory, if the fix's
semantic impact is uncertain, or if the same bug reappears after a fix.

**Session-close emission.** At session end, emit `[SESSION-CLOSE]` with body
`clean close: no unresolved bugs` or `closed with unresolved bugs: <list>`. See `§14.3`
for the invariant; `EXECUTION §6.1` performs the emission.

