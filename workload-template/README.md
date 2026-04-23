# Preparer guide

You are setting up a new hackathon iteration for a milabench pipeline. You do
this **by pairing with a preparer-agent** — the agent drives the mechanical
work (branching, copying the template, drafting the card) **and the HP search**
(proxy sweep + full-length TTR validation), then locks the winning HP
configuration and commits. Your job is to specify the pipeline, answer judgment
questions, and verify what the agent produces before it commits.

The blank `WORKLOAD_CARD.md` and `SESSION_START_PROMPT.md` in this folder
are the templates the agent copies and fills. You do not edit them by hand.

**Rough time budget.** Preparation now includes the HP search that used to run
inside every session. Expect the agent to need **hours of GPU time** — a short
sanity baseline, then the short-run baseline, the default-HP TTR baseline
(≥3 full runs), a proxy sweep over a small candidate shortlist, and full-length
TTR validation for the top candidates. This cost is paid **once per iteration**
instead of once per session-agent, so every subsequent session starts from the
same locked HPs and skips straight to optimization.

---

## 1) What you bring

- **A milabench pipeline name** — the entry in
  [`config/standard.yaml`](https://github.com/milabench/milabench/blob/master/config/standard.yaml)
  that identifies the workload (e.g. `resnet`, `llm-lora-single`).
- **A rough sense of the goal** — what metric matters, what the quality
  constraint is, which parts of the code are in-scope to modify. You do not
  need to write this up; the agent will ask.
- **Push access to both remotes** — the workload repo (milabench or fork)
  and brdg-hackathon. The agent pushes a prepared branch to each:
  `hackathon-<workload>-<iteration>` on the workload repo, and
  `<workload>-<iteration>` on brdg-hackathon.
- **A GPU slot for the HP search.** The preparer-agent runs the sanity
  baseline, the short-run baseline, the default-HP TTR baseline, the proxy
  sweep, and TTR validation for the top candidates — all on GPU matching the
  workload's hardware requirements. On the Mila cluster, allocate with
  `salloc --partition=unkillable -c 6 --gres=gpu:l40s:1`
  (docs: [docs.mila.quebec](https://docs.mila.quebec)); on other
  infrastructures, whatever satisfies what you would put in
  `WORKLOAD_CARD §9`. Plan for hours of wall-clock, not minutes — the
  full-length runs at default HPs and at each surviving candidate dominate
  the time budget.

The iteration number is inferred by the agent from `sessions/<workload>/` —
confirm or override it when the agent reports what it found. Everything else
the agent handles.

---

## 2) Start the preparer-agent

Set the agent's shell cwd to the milabench repo root (that is where
`config/standard.yaml` lives and where baseline commands run). Clone
`brdg-hackathon/` inside milabench if it is not already there.

Point the agent at its entry file:
`brdg-hackathon/workload-template/AGENT_HANDOFF.md`.

Answer its first question — the pipeline name. The agent will report the
inferred iteration number next; confirm or override.

---

## 3) What the agent will ask

The agent reads `config/standard.yaml`, finds your pipeline, reads its code,
then interviews you. Expect **multiple-choice questions grounded in what it
saw**, not open-ended requests.

**Prep Phase 1 (card draft):**
- **Primary metric**: "I see `samples/sec` logged via `log_scalar` and
  `wall_time_per_step` from the profiler. Which is primary?"
- **Quality metric**: "I see `val_acc` every N epochs and `eval_loss` every
  step. Which constrains your optimisation?"
- **Tolerance**: `-2·baseline_std` (safe default) vs `-X%` vs explicit rule.
- **Benchmark window**: fixed N steps (agent estimates wall-time) vs fixed T
  seconds.
- **Allowed / disallowed edits**: agent proposes a split based on the code; you
  narrow or extend.
- **Known caveats / prior art**: open question — the agent cannot infer.

**Prep Phase 2 (HP search):**
- **Target quality for TTR (§10.2)**: Option A (mean end-of-run quality across
  the default-HP full runs — the default) vs Option B (a pre-declared threshold
  from prior art you specify).
- **Engineering-knob HP shortlist**: the agent proposes ≤ `k_max` candidate
  HP sets (batch size, num_envs, rollout length, dataloader workers, compile
  flags, etc.) grounded in `playbook/REFERENCE.md §2` couplings; you narrow.
- **Semantic-HP unlock approval**: if a coupled HP cannot be swept without
  also moving a semantic HP (learning rate, exploration schedule, target-sync
  frequency), the agent asks before tuning.

For every question the agent proposes defaults; you confirm, redirect, or
write in a custom answer.

---

## 4) What you verify before approving the commit

The agent runs Prep Phase 1 (card draft + sanity baseline), Prep Phase 2 (HP
search + lock), then fills §12 (the verification checklist). Before you say
"go", confirm:

**Card draft (Prep Phase 1 outputs):**

- [ ] The **prepared workload-repo branch** `hackathon-<workload>-<iteration>`
  is the current branch in the workload repo and contains a commit adding
  `brdg-hackathon/` to `.gitignore`. The agent will also have pasted the
  branch's head commit short-SHA into `WORKLOAD_CARD §1`; confirm it matches.
- [ ] The **primary-metric extraction recipe** in §2 returned a real number
  from the sanity baseline. Ask the agent to show the recipe applied to the
  capture if unclear.
- [ ] The **quality-metric extraction recipe** in §3 returned a real number.
  Same check.
- [ ] The **tolerance** in §4 reflects what you actually care about. This is
  the most common silent mistake — too tight rejects all optimisations; too
  loose masks regressions.
- [ ] **Allowed / disallowed** surfaces in §7 / §8 are non-overlapping and
  together cover everything. The disallowed list is the semantic-surface
  boundary; a vague one lets operators drift.
- [ ] The **baseline command** in §6 ran on the prepared workload-repo branch.
  Capture is at `sessions/<workload>/<iteration>/prep/baseline_capture.txt`.

**HP lock (Prep Phase 2 outputs) — `WORKLOAD_CARD §10`:**

- [ ] **§10.1 locked HPs**: the `hp_values_json` is a valid JSON object, and
  the winner candidate label matches an `experiment_id` in
  `prep/prep_results.csv`. For the default fallback, confirm the agent
  explicitly flagged that no candidate cleared the backtrack gate.
- [ ] **§10.2 target quality**: Option A or Option B, with a concrete numeric
  value. Option A (default-HP mean EoR) is the common choice.
- [ ] **§10.3 Tier-2 baseline**: median / range / CV / N are present; the
  pinned `experiment_id` exists in `prep/prep_results.csv` as a
  `prep_p2_validation` row (or `prep_p2_default_ttr` if defaults won).
- [ ] **§10.4 Tier-1 baseline**: short-run median / CV / N and the protocol
  match what the agent recorded in `prep/prep_event_log.md` during Prep
  Phase 2.
- [ ] **§10.5 prep-branch head commit**: same short-SHA as `§1`.

**Publish surface (Prep Phase 3 output):**

- [ ] The **session-start prompt** at
  `sessions/<workload>/<iteration>/SESSION_START_PROMPT.md` has `<workload>`
  and `<iteration>` substituted throughout; `<agent-name>` remains the only
  placeholder (operators fill it at session start).

If any check fails, tell the agent what to correct. **Do not approve a
commit with a ticked §12 box that is not actually verified** — that is the
single biggest cause of a lost session downstream. In particular, an HP-lock
that was never actually TTR-validated (§10.3 numbers invented or copied from
defaults without running the candidate) makes every downstream session
meaningless.

---

## 5) After the commit

The agent pushes two branches and reports both names:

- `hackathon-<workload>-<iteration>` on the workload repo (carries the
  `.gitignore` entry and any approved prep-time fixups; operators check it
  out when starting a session),
- `<workload>-<iteration>` on brdg-hackathon (carries the filled
  `WORKLOAD_CARD.md` pinning the workload-repo prep-branch head commit, the
  locked HP configuration, and the Tier-1 / Tier-2 baselines every
  session-agent will adopt; plus the pre-filled `SESSION_START_PROMPT.md`
  operators refer the agent to at session start, and the `prep/` tree with
  `prep_event_log.md` + `prep_results.csv` so the locked configuration is
  auditable).

Operators follow the root `README.md` from here: they check out
`hackathon-<workload>-<iteration>` on the workload repo, branch off
brdg-hackathon's `<workload>-<iteration>` into
`<workload>-<iteration>-<agent-name>`, and run their sessions.

Once all sessions have merged back into `<workload>-<iteration>`, open a PR
from `<workload>-<iteration>` to `main`. Comparison metrics (see root
`README.md`) are computed from the aggregated artifacts under
`sessions/<workload>/<iteration>/*/artifacts/`.
