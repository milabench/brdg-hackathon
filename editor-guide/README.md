# Instructions Design Guidelines

> This file is an instruction file about editing instruction files. It governs how
> the **reviewing agent** should read, audit, revise, and apply changes to the
> hackathon instruction corpus. It applies to itself — the same trade-offs and
> style rules below must be respected when editing this file.

---

## 1) Purpose and audience

The reviewing agent reads this guide before touching any instruction file. The goal
is not to produce a pristine document set in the abstract — it is to keep the corpus
**internally consistent**, **mechanically usable**, and **economical to load** over
many sessions, while accepting that every change is a compromise between competing
pressures.

This guide answers three questions:
- **What is in scope?** (§2 — the corpus)
- **Which way do I lean when two pressures conflict?** (§3 — directional trade-offs)
- **What are the hard constraints I cannot trade away?** (§4 — invariants)

The later sections (§5–§9) tell you how to apply those answers in practice.

Audience note: you are an editing agent, not a session-running agent. Session-running
agents read `AGENT_HANDOFF.md → RULES.md / EXECUTION.md / ...`. You read those same
files in order to modify them; this guide is your lens.

---

## 2) The corpus

The instruction corpus spans **prose files**, a **per-iteration template**, and
**scripts**. All of them are in scope when reviewing or editing.

Layout (repo root):

```
playbook/                      session-agent corpus (eagerly + trigger-loaded)
workload-template/             per-iteration template + preparer surfaces
  WORKLOAD_CARD.md             (template, copied to sessions/ per iteration)
  AGENT_HANDOFF.md             (preparer-agent entry point)
  README.md                    (human preparer workflow)
sessions/                      <workload>/<iteration>/<agent-name>/ artifacts
editor-guide/                  this guide
scripts/                       validation / scoring / plotting / aggregation
README.md                      root: dispatcher + operator guide
```

Two agent audiences: the **session-running agent** reads from `playbook/`; the
**preparer-agent** reads `workload-template/AGENT_HANDOFF.md`. Cross-references
inside `playbook/` are bare filenames (`RULES §X`, `SCHEMA §1`) because the
files are siblings; references from outside `playbook/` (this guide, scripts,
the root README, `workload-template/AGENT_HANDOFF.md`) use the qualified form
(`playbook/RULES.md §X`).

### 2.1 Session-agent prose (eagerly loaded)

Read before acting; held for the whole session. All live in `playbook/` and
address the session-running optimisation agent.

- **`AGENT_HANDOFF.md`** — the entry pointer. Tells the agent what to read and in
  what order. Intentionally thin. Not a summary of `RULES.md`.
- **`RULES.md`** — the always-resident rulebook. Numbered sections `§1..§16`. Cited
  from everywhere else as `RULES §X`. The agent holds this loaded for the whole
  session, so every line it contains is paid for on every turn.
- **`EXECUTION.md`** — the phase-by-phase procedure (Phase 1 → 2 → 3 → 4 → wrap-up).
  Cites `RULES §X` repeatedly. Each phase has an explicit exit criterion.

### 2.2 Agent-facing prose (trigger-loaded)

Each file in this group declares its own load / hold / evict pattern, and all live
in `playbook/`. The pattern is encoded at the top of the file itself
(`SCHEMA.md` preamble, `REFERENCE.md` per-entry header, `AGENT_HANDOFF.md` wrap-up
pointer). Respect those declarations when editing — do not promote a trigger-loaded
file into the eagerly-loaded group without reconsidering the whole load pattern.

- **`SCHEMA.md`** — the `results.csv` data contract. Fixed 23-column header and
  validation rules. Load pattern: **loaded on first `results.csv` write (end of
  Phase 1 baseline), held through the session** — trigger-loaded but then resident
  once triggered, because CSV writes repeat on every experiment. Consumed
  mechanically by scripts (§2.5) and by the post-experiment checklist
  (`RULES §14.2`).
- **`REFERENCE.md`** — lookup tables consulted on demand. Each entry declares its
  own **Trigger / Loaded from / Hold / Evict** (see §5). Content that is only
  relevant in narrow situations lives here instead of in `RULES.md` — this is the
  corpus's main context-economy device.
- **`FINAL_SUMMARY_TEMPLATE.md`** — the shape of the session's terminal
  deliverable. Load pattern: **loaded during wrap-up** (`EXECUTION §6.4`) and not
  before. Changes here flow into every future session's `FINAL_SUMMARY.md`.

### 2.3 Preparer surfaces (`workload-template/`)

The `workload-template/` directory is where a new `<workload>-<iteration>` is
prepared. It holds one template and two preparer-facing docs:

- **`workload-template/WORKLOAD_CARD.md`** — the blank template the
  preparer-agent copies to `sessions/<workload>/<iteration>/WORKLOAD_CARD.md`
  and fills under the human preparer's supervision. The filled copy is shared
  across every `<agent-name>/` in the iteration. The only place where
  workload-specific values (metric names, tolerances, commands) are allowed
  to live.
- **`workload-template/AGENT_HANDOFF.md`** — the preparer-agent's entry
  pointer. Distinct audience from `playbook/AGENT_HANDOFF.md` (which is for
  the session-running optimisation agent). The preparer-agent reads it once
  per iteration, interviews the human, **creates the workload-repo prep
  branch `hackathon-<workload>-<iteration>` with the `brdg-hackathon/`
  gitignore entry and any approved prep-time fixups**, drafts the card
  (pinning that branch + commit in §1), verifies the baseline on that branch,
  pushes both branches; the file is not held turn-by-turn like the session
  corpus. Thin-entry-pointer rule (§3.7) still applies: it points into
  `WORKLOAD_CARD.md` and the relevant `playbook/` sections, it does not
  summarise them.
- **`workload-template/README.md`** — the human preparer's counterpart to
  the preparer-agent handoff. Covered in §2.4 (human-facing prose).

### 2.4 Human-facing prose

- **Root `README.md`** — entry dispatcher ("who are you?") + operator guide. The
  dispatcher routes each reader to their own entry point; the operator guide
  below is the per-session workflow for humans running a session paired with an
  agent. Different audience from the agent files; the agent reads
  `playbook/AGENT_HANDOFF.md`, the operator reads the root `README.md`.
- **`workload-template/README.md`** — human preparer guide. One-time workflow
  for the human setting up a new `<workload>-<iteration>`: the human pairs
  with a preparer-agent (entry at `workload-template/AGENT_HANDOFF.md`),
  specifies the pipeline, answers judgment questions, and verifies the
  filled card before approving the commit. Written as a verifier's checklist,
  not a doer's manual — the agent does the mechanical work. Kept separate
  from the operator guide so each human audience reads only its own workflow.
- **`sessions/README.md`** — per-session artifact tree reference **and** the
  commit policy (what lands in git, what is excluded by `sessions/.gitignore`,
  what needs an external link). Dual audience: the human operator reads it at
  session close (cited from root `README.md §6`), and the session-agent
  trigger-loads it (listed in `playbook/AGENT_HANDOFF.md` file set, cited from
  `playbook/RULES.md §12` and `playbook/EXECUTION.md §6.5`). Cross-file
  citations use `sessions/README.md §Commit policy` — rename the heading
  only in lockstep with those citers.

### 2.5 Scripts

Scripts live in `scripts/` and are in scope for this guide because they **enforce the
contracts the prose describes**, and because several of them hold mirrored copies of
those contracts. When the prose changes, the scripts usually must change too — and
vice versa.

- **`validate_artifacts.py`** — enforces `RULES §5` (preflight), `§12` (profiling),
  `SCHEMA §1` (CSV schema), and `EXECUTION §6.3` (required folder structure).
- **`score_session.py`** — parses `event_log.md` tags (`RULES §13.3` / `§14.3`) and
  `results.csv`, computes timeline and quality metrics, and checks `§14.3`
  invariants.
- **`plot_results.py`** — renders the session timeline and per-tier primary-metric
  trajectories.
- **`aggregate_sessions.py`** — combines multiple sessions for cross-agent
  comparison.
- **`requirements.txt`** — Python dependencies for the above. Edits here are
  in scope for the same reason the scripts are.

**Mirrored constants** (edit in prose + scripts in the same change, per §4.1):

| Contract | Prose source of truth | Mirrored in |
|----------|-----------------------|-------------|
| 23-column `results.csv` header | `SCHEMA §1` | `REQUIRED_COLUMNS` in `validate_artifacts.py`, `score_session.py`, `plot_results.py`, `aggregate_sessions.py` (all four) |
| Event-log tag line regex | `RULES §13.2` / `§14.3` tag-line format | `TAG_LINE_RE` in `plot_results.py`, `score_session.py` |
| `[PHASE-EXIT N]` range `N ∈ {1..4}` | `RULES §13.3` / `§14.3` | `PHASE_EXIT_RE` + `range(1, 5)` loops in `score_session.py` |
| Tag `Role` column (milestone / overlay / —) | `RULES §13.3` table | `_tag_style` function in `plot_results.py` (distinct marker + label flags per role) |
| Milestone invariants (counts, ordering) | `RULES §14.3` invariants | `check_invariants` in `score_session.py` |
| `[SESSION-START]` / `[WIN]` / `[PHASE-EXIT N]` / `[SESSION-CLOSE]` body shapes | `RULES §14.3` | parsing logic in `score_session.py`, `aggregate_sessions.py` |
| Post-experiment checklist line | `RULES §14.2` | checklist regex in `score_session.py` |
| Script-printed section labels (e.g. `"Checklist compliance (RULES §14.2)"`) | `RULES §X` numbering | docstrings + `print` / output-building lines in `score_session.py` |

The last row is easy to miss: when you renumber or rename a `RULES §X`, the
scripts' *printed* labels that cite it drift silently. A label that still cites
`§12.2` after the rule moved to `§14.2` is not a runtime bug, but it misleads the
reader of the output. Grep the scripts for `§` when renumbering.

### 2.6 This guide

- **`editor-guide/README.md`** (this file) — meta. Applies to itself.

---

## 3) Directional trade-offs

This is the heart of the guide. Each subsection names a tension, states the default
direction, explains the reasoning, and tells you when to override. When two
subsections seem to conflict in a concrete case, reason explicitly about which
pressure dominates for that edit rather than picking one in the abstract.

### 3.1 Brevity vs clarity

**Default: favor clarity.** Cut filler words, redundant phrasing, and decorative
prose. Do not cut definitions, disambiguations, or the *why* behind a rule.

**Reasoning.** Every resident line costs context on every turn, so brevity is not a
free stylistic preference — it has a real budget impact. But a rule that is 20%
shorter and re-triggers the same clarifying question next session is a net loss: the
agent will either ask for clarification (costing more than the words saved) or guess
wrong (costing a lost session). A rule that has been misread in practice once is
almost always worth lengthening, not shortening.

**Override when:** a section is clearly padded (multiple paraphrases of the same
idea; two-sentence examples where one suffices; "as mentioned above" bridges). Cut
aggressively there.

### 3.2 Context economy vs file proliferation

**Default: prefer a small number of well-scoped files over either a monolith or many
tiny ones.**

**Reasoning.** Two failure modes bracket the right answer. A monolith
(`EVERYTHING.md`) is cheap to open but expensive to carry — the agent pays for the
whole file every turn even when only §3 is relevant. Many tiny files
(`rule_01.md`, `rule_02.md`, ...) are cheap to carry individually but expensive to
find — the agent wastes turns opening and skimming files to locate what it needs,
and cross-references multiply.

The current split is deliberate: `RULES.md` is the resident rulebook (≈600 lines is
acceptable because it's one file, read once, then held); `REFERENCE.md` is
trigger-loaded material that would inflate `RULES.md` without earning its keep;
`SCHEMA.md` is a small, rigid data contract that benefits from standing alone;
`EXECUTION.md` is the procedure that threads the rules together.

**Override when:**
- A `RULES.md` section is long, self-contained, and triggered only by narrow
  conditions → consider promoting to `REFERENCE.md` with a one-line hook back from
  `RULES.md`.
- A `REFERENCE.md` section is consulted on nearly every turn → consider demoting
  into `RULES.md`; the trigger-loading overhead is no longer paying off.
- You are about to create a tenth lookup file → stop. Add a section to
  `REFERENCE.md` instead.

### 3.3 DRY vs point-of-use reminders

**Default: one canonical statement, cited by `§ref` from other files. A one-line
reminder at the point of use is acceptable; full restatement is not.**

**Reasoning.** Duplicated rules drift. When the same rule is spelled out in two
places, an edit to one leaves the other stale, and the agent has no way to know
which version is current. Cross-references (`RULES §6`, `SCHEMA §1`) solve this by
making the citation the source of truth.

Point-of-use reminders are a useful middle ground: a sentence like "see `§6` for N"
inside `EXECUTION.md` costs one line but saves the agent from having to juggle the
full rule. The line must be short enough that it cannot contradict the canonical
statement — a pointer, not a paraphrase.

**Override when:** a single-sentence rule is genuinely cheaper to inline than to
cite. If the "see §X" pointer is longer than the rule itself, inline. Flag the
duplication in a comment so it is not silently diverged from later.

### 3.4 Workload-agnostic vs concrete examples

**Default: instructions stay workload-agnostic. Examples are fine when clearly
marked illustrative (`e.g.`, `— e.g. mnist-1`).**

**Reasoning.** The `playbook/` is used across workloads unchanged — only the
filled `WORKLOAD_CARD.md` at `sessions/<workload>/<iteration>/` differs between
workloads. Any workload-specific value (a metric name, a tolerance, a baseline
command) embedded in `RULES.md` or `EXECUTION.md` becomes wrong the next time the
playbook is used against a different workload. That is what `WORKLOAD_CARD.md`
exists for: everything workload-specific lives there, and only there.

Illustrative examples, however, help the agent form a mental model. "e.g.
`steps/sec`, `samples/sec`" makes the abstract "primary metric" concrete without
committing the template to a specific workload.

**Override when:** never, for hardcoded values. Always, for illustrative examples
where the illustration earns its words.

### 3.5 Prose flexibility vs mechanical parseability

**Default: anything a script reads is rigid. Prose that only humans and agents read
can be flexible.**

**Reasoning.** `score_session.py` parses event-log tags with regexes. The post-
experiment checklist in `RULES §14.2` has a canonical single-line shape. `SCHEMA.md`
fixes 23 columns in order. `validate_artifacts.py` checks the header matches
exactly. These are contracts, not suggestions. Rewording them "for clarity" breaks
the scripts silently.

Conversely, the phase descriptions in `EXECUTION.md`, the reasoning paragraphs in
`RULES.md`, and the human-facing narratives (root `README.md`,
`workload-template/README.md`) are read by humans and agents but not by scripts.
They can be reworked freely as long as cross-references and semantics hold.

**Override when:** never, for the machine-parsed surfaces. If a mechanical shape is
genuinely unclear, change the shape in prose **and scripts together** in one edit
(§7.3).

### 3.6 Prescriptive rules vs agent judgment

**Default: prescribe the floor — what *must* happen — and leave judgment above the
floor.**

**Reasoning.** Over-prescription produces ritual compliance: the agent ticks boxes
without understanding, and edge cases that the rule did not anticipate go wrong
silently. Under-prescription produces drift: each session solves the same problem
slightly differently, and cross-session comparison breaks down.

The corpus already draws this line well: the post-experiment checklist (`RULES
§14.2`) is rigidly prescriptive because it is the mechanism that catches omissions;
but the Phase 4 loop body (`EXECUTION §5`) is described at the level of "profile →
hypothesise → change → measure" and leaves the agent to judge which bottleneck is
top of stack.

**Override when:** if you catch yourself adding a new rule to cover a specific
past mistake, ask whether the mistake was a missing *floor* (add the rule) or a
judgment call gone wrong (improve the reasoning, don't add a rule). If you cannot
name the failure mode the rule prevents, drop it.

### 3.7 Entry-point thinness vs completeness

**Default: `AGENT_HANDOFF.md` stays thin. It points; it does not summarise.**

**Reasoning.** The entry file is the agent's first contact with the corpus. If it
summarises `RULES.md`, the agent has no incentive to read the full file, and the
summary drifts from the original. If it expands, the "read this first" framing
collapses. Its job is to route the agent into the rest of the corpus with the
minimum necessary framing: goal, first actions, file inventory, and the two rules
that apply even if the agent reads nothing else.

**Override when:** never, for adding rule content. Occasionally, to update the file
inventory when the corpus layout changes.

### 3.8 Agent-facing vs human-facing phrasing

**Default: preserve the split across four audiences — session-agent
(`playbook/AGENT_HANDOFF.md`), preparer-agent
(`workload-template/AGENT_HANDOFF.md`), operator (root `README.md`), preparer
(`workload-template/README.md`). Do not collapse them even when content
overlaps.**

**Reasoning.** The audiences read differently. Humans read their README once
before a session to know what to do as preparer or operator; they skim and skip.
Agents read their handoff once and are expected to internalise it. Phrasings
optimised for one audience feel wrong to the others: the human's "notify
operators that the branch is ready" has no meaning to an agent, and the
session-agent's "begin Phase 1 in `EXECUTION.md`" is not actionable for a
human. The same principle splits preparer and operator: preparer reads once,
up front; operator reads at the start of every session. It also splits
session-agent from preparer-agent: the session-agent's life is
profile→hypothesise→change→measure; the preparer-agent's life is
interview→draft→verify→commit. Mixing those protocols confuses both.

Some duplication is therefore expected — multiple files describe the session
folder layout, for example. That is acceptable as long as each framing is right
for its audience and they agree on the facts.

**Override when:** two files contradict each other on a fact (different folder
path, different command). Reconcile immediately — make the fact canonical in one
file and cite it from the others, or ensure all wordings describe the same
truth.

### 3.9 Backwards compatibility vs clean refactor

**Default: when a rename or renumber breaks `§ref` citations in other files, the
refactor re-threads every citation in the same change. Not a follow-up.**

**Reasoning.** Section numbers are citations, not decorative headings. A change
that renumbers `RULES §14` to `RULES §15` without updating every `RULES §14.*`
reference elsewhere silently breaks the corpus. Splitting that into a follow-up PR
leaves the corpus in a half-broken state between commits, which is worse than not
refactoring at all.

**Override when:** the renumber is trivially contained (a single file, no inbound
citations from others). Then it is a local edit.

### 3.10 New rule vs scope creep

**Default: a new rule must name a concrete failure mode it prevents. Hypothetical
protection is not enough.**

**Reasoning.** Every new rule inflates `RULES.md` — which is resident — and adds a
line the agent must hold for every future session. A rule justified by "someone
might make mistake X" has a cheap justification, and rules that accumulate on
hypothetical grounds drown out the rules that matter. Rules grounded in an actual
past failure, by contrast, are paying for themselves.

**Override when:** never. If you cannot cite the failure mode, drop the proposed
rule or file it as a `REFERENCE.md` lookup triggered narrowly, where it costs
nothing until relevant.

### 3.11 Prose spec vs executable validator

**Default: prose is canonical. Scripts mirror. When they disagree, investigate
which one is wrong rather than assuming the script is authoritative.**

**Reasoning.** Both `validate_artifacts.py` and `score_session.py` hold their own
copy of the 23-column header (`REQUIRED_COLUMNS`), and both use regexes that encode
shapes described in `RULES §13.3` / `§14.3`. This duplication is intentional: the
prose is the spec humans edit, and the scripts are the executable form that catches
drift the prose cannot catch by itself. But that duplication is also fragile — an
edit in one place and not the other produces a silent contradiction.

When the prose and a script disagree, one of them is out of date. The fix is to
identify which one matches the actual intent and bring the other into line. The
prose is canonical by default because it is where the rule is *decided*; the
script is canonical for questions about what is *enforced*. The edit that aligns
them must happen in the same change.

**Override when:** never on the "align them together" rule. The directional choice
(prose or script) flips case by case.

---

## 4) Invariants you cannot trade away

The trade-offs above describe how to lean. The invariants below are not negotiable
— no edit is allowed to break them. If an edit appears to require breaking one,
that is a signal to redesign the edit, not to break the invariant.

### 4.1 Machine-parsed contracts

See §2.5 for the full mirrored-constants table. The contracts below are not
negotiable — every edit touching them updates prose *and* every mirroring script
in the same change.

- The 23 columns in `SCHEMA §1`, in order, match exactly the `REQUIRED_COLUMNS`
  lists in all four scripts (`validate_artifacts.py`, `score_session.py`,
  `plot_results.py`, `aggregate_sessions.py`). Adding, removing, or reordering a
  column touches all five surfaces and is verified against the validator before
  merging.
- The tag set in `RULES §13.3` is the superset of tags that `score_session.py`
  parses. A tag used in `event_log.md` that is not in `§13.3` is a spec bug; a tag
  in `§13.3` that the scorer does not understand is a script bug. Both are
  blockers.
- The `Role` column in `RULES §13.3` (milestone / overlay / —) matches the branch
  structure of `_tag_style` in `plot_results.py`. Promoting a tag's role in the
  table without updating `_tag_style` silently mis-renders the timeline.
- The canonical single-line shapes for `[SESSION-START]`, `[WIN]`, `[PHASE-EXIT N]`,
  and `[SESSION-CLOSE]` in `RULES §14.3` are the shapes `score_session.py` parses.
  Do not reword them for prose reasons. The sign convention for `delta_ttr`
  (negative = improvement) is part of the canonical shape, not a prose preference.
  The `[SESSION-START]` body fields — including `Hackathon repo: <branch> @
  <commit>` — are the session's own version record; renaming them drops corpus
  provenance silently.
- `PHASE-EXIT N` is fixed at `N ∈ {1..4}`. `PHASE_EXIT_RE` and the `range(1, 5)`
  loops in `score_session.py` encode this; adding a phase number requires updating
  both.
- The post-experiment checklist line in `RULES §14.2` is parsed by
  `score_session.py`. The six boxes, their order, and their names are fixed.
- Script-printed section labels (e.g. `"Milestone timeline (RULES §14.3)"`) cite
  `RULES §X` numbering. Renumbering a `RULES §` re-threads these labels in the
  same change; a stale label is a documentation bug, not a runtime failure, but
  still an audit failure.

### 4.2 Cross-reference integrity

- Every `RULES §X`, `EXECUTION §X`, `SCHEMA §X`, `REFERENCE §X`, `WORKLOAD_CARD §X`
  citation in the corpus resolves to a real section.
- Renumbering a section re-threads every inbound citation in the same change.
- Deleting a section deletes or rewrites every inbound citation in the same
  change.

### 4.3 Structural invariants encoded in `§14.3`

- Exactly one `[SESSION-START]` per session, at `T+0`, with a
  `Hackathon repo: <branch> @ <commit>` line in its body.
- Exactly one `[PHASE-EXIT N]` per `N ∈ {1,2,3,4}` per session.
- Exactly one `[SESSION-CLOSE]` per session.
- `[WIN]` events appear only after `[PHASE-EXIT 3]`.
- `[PHASE-EXIT 2]` follows at least one `[BASELINE]`.
- Every `[WIN]` has a matching `results.csv` row with `tier=full`,
  `win_status=WIN`, `quality_verdict=PASS`.

These are enforced by `score_session.py`. Any edit that introduces a new milestone
tag or a new phase must either fit into these invariants or update `§14.3` and the
scorer together.

### 4.4 Metric-per-tier contract

The corpus optimises **two different metrics** and the split must not be
collapsed.

- **Tier 1 (short runs)** measures the **throughput proxy** declared in
  `WORKLOAD_CARD §2` (per-step or per-sample throughput). Cheap, fast, noisy.
  Used for profiling and candidate screening.
- **Tier 2 (full runs)** measures **time-to-result (TTR)** as defined in
  `EXECUTION §4` — wall-clock time to reach the target quality. Expensive,
  integrates run dynamics, and is the session's end-goal metric.
- `[WIN]` is Tier-2-only (`RULES §8` promotion rule, `§14.3` invariant) and
  reports `delta_ttr` in its body, not throughput (`RULES §14.3`). A throughput
  improvement that does not translate to a TTR win is not a win.
- `Δ_min` (`RULES §7`) is in tier-native units: throughput at Tier 1, TTR at
  Tier 2.
- Two metrics, two columns, two reporting surfaces:
  `results.csv.primary_metric` carries the throughput proxy;
  the event-log `[WIN]` body reports TTR as `delta_ttr`.
  They do not collapse into each other.

Edits that conflate the two — reverting `delta_ttr` to `delta_primary` "for
consistency", renaming the Tier-2 metric to "primary", deleting the
"Metric per tier" block in `RULES §8`, or removing the throughput/TTR split
from `RULES §3` — break the success criterion the whole protocol is built
around. Reject them and rework the edit.

### 4.5 Phase structure

- Phases run 1 → 2 → 3 → 4 → wrap-up, in order.
- Each phase has an explicit exit criterion stated at the end of its section in
  `EXECUTION.md`.
- The standing bug-handling procedure (`RULES §16`) can fire from any phase.

**Phase ↔ milestone coupling.** Phase numbers and milestone tag numbers are not
independent. Adding or removing a phase cascades into:
- the `[PHASE-EXIT N]` range in `RULES §13.3` / `§14.3` and its invariants;
- `PHASE_EXIT_RE` + `range(…)` loops in `score_session.py`;
- the `phase` enum values in `SCHEMA §1`;
- the `phase` values written by `EXECUTION §3` / `§4` / `§5` into rows;
- every `[PHASE-EXIT N]`, `[SESSION-START]`, or `[SESSION-CLOSE]` mention in prose.

A previous drift had `[PHASE-EXIT 5]` overloaded as a session-close marker for a
non-sequential phase, plus a `phase_5_bug` enum value with no consumer — that is
the exact shape to avoid. Treat phase changes as large, multi-file edits.

### 4.6 Role split

Two human roles and two agent roles, paired:

- **Preparer (human) ↔ preparer-agent.** The preparer-agent interviews the
  human, drafts `WORKLOAD_CARD.md`, creates the workload-repo prep branch
  `hackathon-<workload>-<iteration>` (with `brdg-hackathon/` gitignored and
  any approved prep-time fixups), runs the baseline on that branch, pushes
  both the workload-repo prep branch and the brdg-hackathon iteration
  branch. The human specifies the pipeline, answers judgment questions
  (metric, tolerance, scope), and verifies the filled card — including the
  pinned prep-branch commit — before approving the commit. Neither side
  fills the card alone. The prep branch carrying environment / ignore /
  known-upstream-bug changes is the preparer's surface, not the operator's
  or the session-agent's; edits that have the operator mutating the workload
  repo's tree (e.g. appending to `.gitignore`) or the session-agent doing
  so outside its declared optimisation branch are redesigns of the role
  split, not clarifications.
- **Operator (human) ↔ session-agent.** The session-agent is the primary
  scribe (maintains `event_log.md`, `results.csv`, profiles, `FINAL_SUMMARY.md`).
  The operator is the verifier. Neither collapses into the other.

Other invariants:

- `WORKLOAD_CARD.md` is filled during preparation (preparer + preparer-agent),
  not during the session. The session-agent and operator read it read-only.
- `playbook/AGENT_HANDOFF.md` / `playbook/RULES.md` / `playbook/EXECUTION.md`
  address the session-agent. `workload-template/AGENT_HANDOFF.md` addresses
  the preparer-agent. Root `README.md` addresses the operator.
  `workload-template/README.md` addresses the preparer.

Edits that have the session-agent editing `WORKLOAD_CARD.md` during the
session, that have the operator maintaining `event_log.md`, that have the
preparer editing the card by hand without an agent, or that have the
preparer-agent committing without explicit human approval, are redesigns of
the protocol, not clarifications. Flag them as such.

### 4.7 Append-only data log

`SCHEMA §2` states rows in `results.csv` are never deleted — only appended, or
retroactively updated on two narrow columns (`win_status → INVALIDATED` and
`notes`). Edits that introduce a mutable column, or that relax the append-only
policy, break cross-session aggregation and are not permitted.

---

## 5) Where new content belongs

When a change introduces new content, ask where it belongs before writing it. The
default answer is often "`REFERENCE.md` or nothing" — resist the pull to put
everything in `RULES.md`.

Decision order:

1. **Is it workload-specific?** → `WORKLOAD_CARD.md` (extend the template; every
   workload will fill it).
2. **Is it a data-shape contract?** → `SCHEMA.md` (and mirror into the scripts).
3. **Is it a rule the agent must hold for the entire session?** → `RULES.md`.
   Apply §3.1 and §3.10 aggressively — add only if the rule is earned.
4. **Is it a step in the session procedure?** → `EXECUTION.md`, inside the phase
   where it fires.
5. **Is it a lookup consulted on a narrow trigger?** → `REFERENCE.md`. New
   entries follow the file's per-entry schema **verbatim** (the schema block at
   the top of `REFERENCE.md` and its index table are part of the contract, not
   decoration):

   ```
   **Trigger.**     <single, observable condition>
   **Loaded from.** <list of RULES §X / EXECUTION §X citations>
   **Hold.**        until trigger completes | through Phase N | through session
   **Evict.**       <positive statement>
   ```

   Also: add the new entry to the index table, and add a pointer from every
   `RULES §X` / `EXECUTION §X` that cites it (those citations are the entry's
   `Loaded from` audit trail — if it's cited but not listed there, the contract
   drifts).

   A trigger must be **observable**: something the agent can check against its
   own state or actions without judgment calls.

   - Good: "after any code change to hot-path / logging / hooks, before
     benchmarking" (observable action sequence).
   - Good: "at Phase 2 entry" / "at `[PHASE-EXIT 2]`" (explicit phase boundary).
   - Good: "on every `[DRIFT]` event" (tag emission).
   - Good: "first `results.csv` write" (specific file operation).
   - Bad: "consult when relevant" (useless).
   - Bad: "during optimization" (too broad — covers most of Phase 4).
   - Bad: "when the agent is stuck" (subjective).
   - Bad: "if needed" (no observable precondition).
6. **Is it human workflow?** → the relevant human-facing README. Preparer
   workflow (specifying the pipeline, answering the preparer-agent's
   questions, verifying the filled card) → `workload-template/README.md`.
   Operator workflow (starting the session-agent, verifying during the
   session, closing) → root `README.md`. The root README also carries the
   "who are you?" dispatcher; add new audience entry-points there, not inline
   in a workflow section.
7. **Is it preparer-agent workflow?** → `workload-template/AGENT_HANDOFF.md`.
   Pipeline discovery, interview protocol, baseline verification, mechanical
   commit pipeline. Do not push this into `workload-template/README.md` — that
   file is the human's verification checklist, not the agent's manual.
8. **Is it a session-agent entry-point update?** → `playbook/AGENT_HANDOFF.md`,
   but only if it is a pointer or an invariant the agent must hold before
   reading the rest. Not a summary of rules.
9. **Is it something scripts must enforce?** → the relevant script, in the same
   change as the prose edit.
10. **None of the above?** → it probably does not belong in the instruction corpus.
    Leave it out.

When in doubt between `RULES.md` and `REFERENCE.md`: if the content is consulted
on nearly every turn, it belongs in `RULES.md`; if it is consulted on specific
triggers, it belongs in `REFERENCE.md`.

When in doubt between `RULES.md` and `EXECUTION.md`: `RULES.md` is the *what* and
*why*; `EXECUTION.md` is the *when* and *in what order*. A rule that applies in
one phase only usually belongs in `EXECUTION.md`, with any cross-phase invariant
extracted to `RULES.md`.

---

## 6) Review procedure (auditing the corpus as-is)

Use this when reviewing the corpus without a specific change request — e.g. a
periodic audit or a new-workload readiness check.

1. **Inventory walk.** Re-read `playbook/AGENT_HANDOFF.md` end to end, then
   follow its file list in the order the session-agent would:
   `playbook/RULES.md` → `playbook/EXECUTION.md` → `playbook/SCHEMA.md` →
   `playbook/REFERENCE.md` → `playbook/FINAL_SUMMARY_TEMPLATE.md` →
   `workload-template/WORKLOAD_CARD.md`. Then read the preparer-agent corpus
   (`workload-template/AGENT_HANDOFF.md`). Then the human-facing READMEs
   (root `README.md`, `workload-template/README.md`, `sessions/README.md`).
   Then open the scripts in `scripts/`.
2. **Cross-reference resolution.** Grep for `RULES §`, `EXECUTION §`, `SCHEMA §`,
   `REFERENCE §`, `WORKLOAD_CARD §`. Confirm each points at a real section.
   Dangling references are audit failures.
3. **Tag consistency.** Collect every tag mentioned anywhere in the corpus
   (`[BASELINE]`, `[WIN]`, `H-STEER`, etc.). Confirm the set is ⊆ the set listed in
   `RULES §13.3`. Confirm `score_session.py`'s tag regexes cover the milestone
   subset in `§14.3`.
4. **Schema consistency.** Confirm `SCHEMA §1`'s 23 columns match
   `REQUIRED_COLUMNS` in `validate_artifacts.py` and `score_session.py`.
5. **Phase exits.** Confirm each phase in `EXECUTION.md` has an explicit exit
   criterion and emits the right `[PHASE-EXIT N]` tag.
6. **Workload-specific leakage.** Scan `RULES.md`, `EXECUTION.md`, `SCHEMA.md`,
   and `REFERENCE.md` for hardcoded metric names, commands, or tolerances. If
   something looks workload-specific and is not an illustrative `e.g.`, flag it.
7. **Trigger-load discipline.** For each `REFERENCE.md` section, confirm the
   trigger is still named and still narrow. If a section is being loaded every
   session, it may need to move to `RULES.md`; if nothing triggers it, it may be
   dead weight.
8. **Role split.** Scan `playbook/RULES.md` and `playbook/EXECUTION.md` for any
   instruction that asks the operator to scribe. Scan the human-facing READMEs
   (root `README.md`, `workload-template/README.md`) for any instruction that
   asks an agent to set up environment. Scan
   `workload-template/AGENT_HANDOFF.md` for any step that commits without
   explicit human approval, or that silently picks §2 (primary metric) or §4
   (tolerance) on the human's behalf. Flag any crossing of the split.
9. **Self-consistency between prose and scripts.** Skim the scripts for any
   constant or regex that, if the prose changed, would now be out of date.

Report findings as a checklist; fix them in subsequent changes following §7.

---

## 7) Update procedure (applying a change)

Use this when you have been handed a specific change to apply. Do not skip steps
even if the change looks small — small changes with broken cross-references are
the most common corpus regression.

### 7.1 Scope the change

- Identify the **primary file**: the one file where the change is principally
  made.
- Grep for **inbound citations** to any section you will touch: `grep -n "RULES
  §14" *.md`, etc. List every file that references the section.
- Identify the **scripts** that consume the contract being changed. If the change
  touches `SCHEMA.md`, the validator and scorer are in scope. If it touches tag
  formats in `§13.3` / `§14.3`, the scorer is in scope.
- Identify whether a human-facing README needs to change. If the preparer
  surface shifts, decide which *half* of the surface: the human's verification
  checklist → `workload-template/README.md`; the preparer-agent's interview,
  pipeline-discovery, or commit flow → `workload-template/AGENT_HANDOFF.md`;
  often both, when the fact itself changes (a new card section, a renamed
  field). If the operator surface (starting the session-agent, verifying,
  closing) shifts, edit root `README.md`. If the change affects none of these
  — only the session-agent's internal procedure — none of the surfaces
  change.

### 7.2 Draft the primary edit

- Apply §3 (trade-offs) and §4 (invariants) as you write.
- Place new content per §5. If the change introduces a concept, decide where it
  belongs *before* drafting, not after.
- Keep the style (§9) consistent with the surrounding file.

### 7.3 Propagate

- Re-thread every inbound `§ref` to match the new section numbering or naming.
- Update mirrored constants in scripts (`REQUIRED_COLUMNS`, tag regexes,
  checklist regex) in the same change.
- Update the relevant preparer-surface file(s) if the preparer surface
  shifted: `workload-template/README.md` for the human's checklist,
  `workload-template/AGENT_HANDOFF.md` for the preparer-agent's flow, or
  both. Update root `README.md` if the operator surface shifted.
- Update `playbook/AGENT_HANDOFF.md` only if the session file inventory or the
  two "even if you read nothing else" rules change. Normal edits to
  `playbook/RULES.md` do not touch `playbook/AGENT_HANDOFF.md`. Same
  thin-entry-pointer discipline applies to
  `workload-template/AGENT_HANDOFF.md`: do not push interview protocol,
  metric-check rules, or tolerance semantics into it if they belong in
  `WORKLOAD_CARD.md` or `playbook/RULES.md`.

### 7.4 Validate

**Read as the session agent, not the editor.** This is the single
highest-leverage step. Open the primary file and read it top to bottom as an
agent starting a fresh session would, following every `§ref` when the prose
tells you to. An agent-facing instruction that seems fine to the editor often
breaks when you actually try to follow it — usually because it misrepresents
what the target section says (anti-pattern in §8). This read catches more bugs
than any other step.

**Re-grep every `§ref` you touched.** After the edit lands, grep for every
cross-reference that points at a section you changed. For each hit, open the
citer *and* the target and verify the claim the citer makes about the target
is still true. A `§ref` can be mechanically intact (`RULES §14.3` still
resolves) but semantically stale (the cited section no longer says what the
citer claims). The `§7.1` pre-edit grep finds inbound citations; the post-edit
re-grep confirms they still describe the current content.

**Run the scripts.**
- `validate_artifacts.py` on a sample session — confirm the schema still
  parses.
- `score_session.py` on the same sample — confirm it still produces a score and
  does not fire invariant failures that were not there before.

**If no real artifact tree is available, build a synthetic fixture.** It takes
~10 minutes: a minimal `event_log.md` covering every tag your edit touches
(plus `[BASELINE]`, `[PHASE-EXIT 1..4]`, `[SESSION-CLOSE]`, `[WIN]` so the
invariants have something to check), and a minimal `results.csv` with at least
one baseline `experiment_id` and one non-baseline `experiment_id` referencing
it. Synthetic fixtures are the only way to validate tag renames, new milestone
tags, or new `SCHEMA` columns before a real session runs.

### 7.5 Self-review against this guide

Before considering the change done, re-open §3 and §4 and ask:
- Did I apply the trade-off directions consciously, or by default?
- Did I break any §4 invariant without noticing?
- Is there a simpler change that achieves the same goal with fewer edits?

If any answer is uncertain, revise before shipping.

---

## 8) Anti-patterns

Specific shapes of edit to reject or revise when you see them. These are the
concrete forms of the trade-offs in §3 being violated.

- **Workload-specific leakage into `RULES.md` / `EXECUTION.md`.** A metric name,
  a tolerance, or a command that belongs in `WORKLOAD_CARD.md`. Always revise.
- **New tag without §13.3 / §14.3 / scorer update.** A tag introduced in
  `event_log.md` examples or in `EXECUTION.md` prose without being added to the
  tag list and the scorer's regex. The scorer will silently fail to recognise it.
- **New CSV column without schema / script update.** Adding a column to
  `SCHEMA.md` without touching the four mirrored `REQUIRED_COLUMNS` lists
  (`validate_artifacts.py`, `score_session.py`, `plot_results.py`,
  `aggregate_sessions.py`). The validator will immediately fail against any
  session using the new column.
- **`AGENT_HANDOFF.md` bloat.** Content being pushed up from `RULES.md` or
  `EXECUTION.md` into the entry pointer because "the agent should see this
  first". Every time this happens, the entry pointer loses its framing role.
- **Duplicated rules in two files.** The same rule stated in `RULES.md` and
  `EXECUTION.md` as independent prose. Keep one canonical statement and cite
  from the other.
- **Normative prose that contradicts a script.** A `RULES.md` rule that does
  not match what the validator or scorer actually enforces. One of them is
  wrong; find out which and align them in the same change.
- **Phase without exit criterion.** A new phase or sub-phase added to
  `EXECUTION.md` without an explicit exit criterion. The scorer cannot measure
  time-to-phase-N-exit without it.
- **Orphan `§ref`.** A citation to a section that does not exist, usually a
  residue from a renumber that did not re-thread.
- **Pointer that misrepresents its target.** A cross-file instruction (e.g. a
  step in `AGENT_HANDOFF.md`, or a `see RULES §X` pointer in `EXECUTION.md`)
  whose `§X` reference resolves, but where the referenced section actually says
  something different from what the citer claims. Distinct from "Orphan `§ref`"
  because the pointer works mechanically; it fails semantically. Example shape:
  `AGENT_HANDOFF.md` step "Begin Phase 1 in `EXECUTION.md`" when `EXECUTION §1`
  is actually Bootstrap (a pre-Phase-1 step), so an agent following the
  instruction literally would skip bootstrap. Caught by the read-as-agent pass
  in §7.4; fixed by rewriting the citer to match what the target actually says,
  or by updating the target if the citer had the right intent.
- **Collapsing the throughput/TTR split** (`§4.4`). Reverting `delta_ttr` to
  `delta_primary`, renaming the Tier-2 metric to "primary", removing the
  per-tier metric block in `RULES §8`, or otherwise conflating the throughput
  proxy with the end-goal TTR metric. These "consistency" edits break the
  protocol's success criterion.
- **Dead `REFERENCE.md` section.** A reference section no file triggers. Either
  wire a trigger in or delete it.
- **Hypothetical rule.** A rule justified by "someone might ..." with no named
  past failure. Drop it or move it to `REFERENCE.md` with a narrow trigger.
- **Paraphrased mechanical shape.** Rewording a canonical tag line or checklist
  shape in `RULES.md` or `EXECUTION.md` "for clarity" without updating the
  regex. Breaks the scorer.
- **Summary in the entry pointer.** `AGENT_HANDOFF.md` beginning to look like an
  abridged `RULES.md`. Revert.
- **Cross-file renumber without re-thread.** Renumbering a `RULES §` section and
  leaving inbound citations stale.

---

## 9) Style conventions

These are the style defaults for the corpus. Apply them when writing new content;
do not rewrite existing content purely for style unless it is genuinely unclear.

### 9.1 Voice

- Imperative for rules: "Do X.", "Record Y.", "Follow `§Z`."
- Descriptive for rationale paragraphs ("The reason is ...").
- Avoid first person.
- Avoid hedging modals in normative text ("might", "could", "try to") unless the
  hedging is intentional. A rule is either a rule (use "must" or bare
  imperative) or it is not.

### 9.2 Structure

- Numbered top-level sections (`## 1)`, `## 2)`, ...). Sub-sections as `### 1.1`.
- Section numbers are stable: renumbering breaks citations.
- Every section has a heading that describes its content in one phrase.
- Phases in `EXECUTION.md` end with an explicit `**Exit criterion:**` block.

### 9.3 References

- Inside the corpus: `RULES §X`, `EXECUTION §X`, `SCHEMA §X`, `REFERENCE §X`,
  `WORKLOAD_CARD §X` — with the file name and the §, no "Section" or "Part".
- Never cite by page number or line number — those shift with edits.
- When a reference is to a sub-section, use the full path: `RULES §14.3`, not
  `§14.3` (ambiguous across files).

### 9.4 Examples

- Illustrative examples use `e.g.` and are parenthetical where possible.
- Do not present an example in a way that looks prescriptive. If it looks like a
  spec, it will be read as one.
- Concrete workload names in examples (`mnist-1`, `milabench`) are allowed
  because the alternative — abstract placeholders everywhere — hurts readability
  more than it helps.

### 9.5 Canonical shapes

- Anything a script parses is rigid. Do not reword for prose reasons. Changes
  happen in prose and script together (§7.3).
- Tag lines in `event_log.md` examples are not prose; they are machine-parsed
  templates. Preserve them verbatim.

### 9.6 Formatting

- Markdown: headings, lists, tables, fenced code blocks.
- No emoji.
- Line-wrap at a reasonable width (≈90 cols is fine; the corpus is not strict
  about it).
- Code blocks have a language annotation when the language matters
  (` ```bash `, ` ```python `); plain ` ``` ` is acceptable for shell sessions
  where the language is obvious.

### 9.7 Definitions

- Define a term the first time it appears in a file, even if it is defined
  elsewhere in the corpus. Cite the canonical definition (`see RULES §4`) rather
  than restating the full definition.
- When a term is overloaded (like *baseline*, which `RULES §4` explicitly
  disambiguates), always qualify it in prose: "session baseline", "tier
  baseline", "comparison baseline".

---

## 10) Meta — this guide applies to itself

This file is an instruction file. The rules in it apply to editing it.

- §3 trade-offs apply: brevity vs clarity, DRY vs point-of-use, and so on. When
  editing this guide, lean the same way it tells you to lean.
- §4 invariants apply to the extent they are relevant. Cross-references from
  this file (`RULES §14.3`, `SCHEMA §1`, etc.) must resolve.
- §5 decision order applies: content that is not about editing instructions
  does not belong here.
- §9 style applies. Imperative voice for rules, descriptive for rationale, no
  emoji, references in the `FILE §X` format.

**Applying §7 to guide edits.** Most of §7 adapts; some of it does not.

- §7.1 Scope — grep for internal `§X` cross-refs within this file before
  renumbering one of its own sections. Inbound cross-file citations and
  mirrored script constants do not apply (no other file cites into this guide,
  no scripts mirror its content).
- §7.2 Draft — unchanged.
- §7.3 Propagate — re-thread internal `§X` cites when renumbering. Script
  updates and `README.md` / `AGENT_HANDOFF.md` propagation do not apply.
- §7.4 Validate — the "run scripts" sub-step does not apply. The
  **read-as-agent sub-step does**, with the audience changed: read the guide
  top-to-bottom as a *fresh editing agent* about to modify the corpus, and
  check whether the advice still lands without privileged context from the
  edit you just made.
- §7.5 Self-review — unchanged.

If a future edit makes this file noticeably contradict itself, that is an audit
failure. Treat it as you would treat a contradiction in `RULES.md`.
