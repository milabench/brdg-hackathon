# Preparer guide

You are setting up a new hackathon iteration for a workload. Done once per
`<workload>-<iteration>`. Operators will run sessions against what you produce
here.

The blank `WORKLOAD_CARD.md` in this folder is the only file you fill in. The
agent-facing protocol in `playbook/` is workload-agnostic and is not copied —
every session reads it directly from `playbook/` in the brdg-hackathon clone.

---

## 1) Branch and folder convention

Each workload evaluation uses a dedicated branch and a matching session folder:

- **Git branch:** `<workload-name>-<iteration>` — e.g., `mnist-1`.
- **Session folder:** `sessions/<workload-name>/<iteration>/` — e.g.,
  `sessions/mnist/1/`.

`<iteration>` increments when you re-run the same workload (e.g., after fixing a
bug in the card or the protocol). Each iteration is an independent evaluation.

At the end of the exercise, operator branches merge back into
`<workload-name>-<iteration>`, then `<workload-name>-<iteration>` merges into
`main`.

---

## 2) Review the corpus

Before a new evaluation campaign, review the protocol on `main`:

- `playbook/AGENT_HANDOFF.md` — agent's landing page.
- `playbook/RULES.md` — rules the agent holds throughout.
- `playbook/EXECUTION.md` — phase-by-phase procedure.
- `playbook/SCHEMA.md` — `results.csv` column spec.
- `playbook/REFERENCE.md` — lookup tables (sync-point checklist, HP interactions).
- `playbook/FINAL_SUMMARY_TEMPLATE.md` — end-of-session template for the agent.
- `workload-template/WORKLOAD_CARD.md` — blank template you will fill.
- `scripts/` — validation and scoring tooling.

If the rules or metrics don't match your evaluation needs, edit them on `main`
(or via a corpus-edit branch) before branching for this iteration. See
`editor-guide/README.md` for corpus-editing conventions.

---

## 3) Fill `WORKLOAD_CARD.md`

Copy `workload-template/WORKLOAD_CARD.md` into
`sessions/<workload-name>/<iteration>/WORKLOAD_CARD.md` and fill it *after* you
branch (§4). Decisions that most affect session quality:

- **Primary metric** — must be mechanically extractable (regex, JSON key,
  specific log line). If you'd have to hand-parse the output to read it, the
  agent's extraction recipe will fail and the validator will reject rows.
- **Quality metric + tolerance** — the tolerance is a candidate-gating threshold.
  Be precise about what "within tolerance" means for this workload (`-5%`,
  `-2·baseline_std`, or an explicit rule).
- **Benchmark window** — long enough to be representative, short enough that one
  full run can be scheduled multiple times during a session. Record the
  rationale.
- **Allowed / disallowed edits** — explicit and non-overlapping. The disallowed
  list is the semantic-surface boundary; if it is vague, agents will gravitate
  toward it and you will have to arbitrate mid-session.
- **Known caveats / prior art** — known baseline variance, optimisations already
  upstreamed, and (optional) a pre-declared Δ_min for cross-agent comparability.

Before handing off, work through §11 (Verification checklist) of the card. In
particular: **run the baseline command end-to-end from a clean environment
yourself**, and confirm the primary and quality metrics extract correctly. An
un-verified card is the most common cause of a lost session.

---

## 4) Hand off — commit to the iteration branch

From `main`, create the iteration branch and the session folder with the filled
card:

```bash
git checkout main
git pull
git checkout -b <workload-name>-<iteration>
mkdir -p sessions/<workload-name>/<iteration>
cp workload-template/WORKLOAD_CARD.md \
   sessions/<workload-name>/<iteration>/WORKLOAD_CARD.md
# now fill sessions/<workload-name>/<iteration>/WORKLOAD_CARD.md per §3
git add sessions/<workload-name>/
git commit -m "Prepare <workload-name> iteration <iteration>"
git push -u origin <workload-name>-<iteration>
```

Notify operators that the branch is ready. Operators follow the root `README.md`
from here.

---

## 5) After all sessions complete

Each operator opens a PR from `<workload-name>-<iteration>-<agent-name>` back to
`<workload-name>-<iteration>`. Because each operator's artifacts live in a
distinct subfolder `sessions/<workload-name>/<iteration>/<agent-name>/`, the
merges are conflict-free.

Once all operator branches are merged, open a PR from
`<workload-name>-<iteration>` into `main`. Comparison metrics (see root
`README.md`) are computed from the aggregated artifacts in
`sessions/<workload-name>/<iteration>/*/artifacts/`.
