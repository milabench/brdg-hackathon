# Preparer guide

You are setting up a new hackathon iteration for a milabench pipeline. You do
this **by pairing with a preparer-agent** — the agent drives the mechanical
work (branching, copying the template, drafting the card, running the
baseline, committing). Your job is to specify the pipeline, answer judgment
questions, and verify what the agent produces before it commits.

The blank `WORKLOAD_CARD.md` and `SESSION_START_PROMPT.md` in this folder
are the templates the agent copies and fills. You do not edit them by hand.

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
- **A GPU slot for baseline verification.** The preparer-agent runs one
  end-to-end baseline during preparation, so it needs GPU access matching
  the workload's hardware requirements. On the Mila cluster, allocate one
  with `salloc --partition=unkillable -c 6 --gres=gpu:l40s:1`
  (docs: [docs.mila.quebec](https://docs.mila.quebec)); on other
  infrastructures, whatever satisfies what you would put in
  `WORKLOAD_CARD §9`.

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

- [ ] The **prepared workload-repo branch** `hackathon-<workload>-<iteration>`
  is the current branch in the workload repo and contains a commit adding
  `brdg-hackathon/` to `.gitignore`. The agent will also have pasted the
  branch's head commit short-SHA into `WORKLOAD_CARD §1`; confirm it matches.
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
- [ ] The **baseline command** in §6 ran on the prepared workload-repo
  branch. You do not need to re-run it; the capture is at
  `sessions/<workload>/<iteration>/baseline_capture.txt`.
- [ ] The **session-start prompt** at
  `sessions/<workload>/<iteration>/SESSION_START_PROMPT.md` has `<workload>`
  and `<iteration>` substituted throughout; `<agent-name>` remains the only
  placeholder (operators fill it at session start).

If any check fails, tell the agent what to correct. **Do not approve a
commit with a ticked §11 box that is not actually verified** — that is the
single biggest cause of a lost session downstream.

---

## 5) After the commit

The agent pushes two branches and reports both names:

- `hackathon-<workload>-<iteration>` on the workload repo (carries the
  `.gitignore` entry and any approved prep-time fixups; operators check it
  out when starting a session),
- `<workload>-<iteration>` on brdg-hackathon (carries the filled
  `WORKLOAD_CARD.md` pinning the workload-repo prep-branch head commit, and
  the pre-filled `SESSION_START_PROMPT.md` operators paste into the agent
  at session start).

Operators follow the root `README.md` from here: they check out
`hackathon-<workload>-<iteration>` on the workload repo, branch off
brdg-hackathon's `<workload>-<iteration>` into
`<workload>-<iteration>-<agent-name>`, and run their sessions.

Once all sessions have merged back into `<workload>-<iteration>`, open a PR
from `<workload>-<iteration>` to `main`. Comparison metrics (see root
`README.md`) are computed from the aggregated artifacts under
`sessions/<workload>/<iteration>/*/artifacts/`.
