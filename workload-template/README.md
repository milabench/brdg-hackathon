# Preparer guide

You are setting up a new hackathon iteration for a milabench pipeline. You do
this **by pairing with a preparer-agent** — the agent drives the mechanical
work (branching, copying the template, drafting the card, running the
baseline, committing). Your job is to specify the pipeline, answer judgment
questions, and verify what the agent produces before it commits.

The blank `WORKLOAD_CARD.md` in this folder is the template the agent will
copy and fill. You do not edit it by hand.

---

## 1) What you bring

- **A milabench pipeline name** — the entry in
  [`config/standard.yaml`](https://github.com/milabench/milabench/blob/master/config/standard.yaml)
  that identifies the workload (e.g. `resnet`, `llm-lora-single`).
- **An iteration number** — `1` if this pipeline has never been evaluated,
  otherwise the next unused integer.
- **A rough sense of the goal** — what metric matters, what the quality
  constraint is, which parts of the code are in-scope to modify. You do not
  need to write this up; the agent will ask.

Everything else the agent handles.

---

## 2) Start the preparer-agent

Set the agent's shell cwd to the milabench repo root (that is where
`config/standard.yaml` lives and where baseline commands run). Clone
`brdg-hackathon/` inside milabench if it is not already there.

Point the agent at its entry file:
`brdg-hackathon/workload-template/AGENT_HANDOFF.md`.

Answer its first question — pipeline name + iteration number.

---

## 3) What the agent will ask

The agent reads `config/standard.yaml`, finds your pipeline, reads its code,
then interviews you. Expect **multiple-choice questions grounded in what it
saw**, not open-ended requests:

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

For every question the agent proposes defaults; you confirm, redirect, or
write in a custom answer.

---

## 4) What you verify before approving the commit

The agent runs the baseline end-to-end and fills §11 (the verification
checklist). Before you say "go", confirm:

- [ ] The **primary-metric extraction recipe** in §2 returned a real number
  from the captured baseline. Ask the agent to show the recipe applied to the
  capture if unclear.
- [ ] The **quality-metric extraction recipe** in §3 returned a real number.
  Same check.
- [ ] The **tolerance** in §4 reflects what you actually care about. This is
  the most common silent mistake — too tight rejects all optimisations; too
  loose masks regressions.
- [ ] **Allowed / disallowed** surfaces in §7 / §8 are non-overlapping and
  together cover everything. The disallowed list is the semantic-surface
  boundary; a vague one lets operators drift.
- [ ] The **baseline command** in §6 ran. You do not need to re-run it; the
  capture is at `sessions/<workload>/<iteration>/baseline_capture.txt`.

If any check fails, tell the agent what to correct. **Do not approve a
commit with a ticked §11 box that is not actually verified** — that is the
single biggest cause of a lost session downstream.

---

## 5) After the commit

The agent pushes `<workload>-<iteration>` and reports the branch name.
Operators follow the root `README.md` from here: they branch off
`<workload>-<iteration>` into `<workload>-<iteration>-<agent-name>` and run
their sessions.

Once all sessions have merged back into `<workload>-<iteration>`, open a PR
from `<workload>-<iteration>` to `main`. Comparison metrics (see root
`README.md`) are computed from the aggregated artifacts under
`sessions/<workload>/<iteration>/*/artifacts/`.
