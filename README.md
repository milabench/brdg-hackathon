# Optimization Hackathon — Human Guide

Each session pairs one human operator with one coding agent against a workload defined
in `WORKLOAD_CARD.md`. The protocol is designed for **one preparer** to set up a
workload once, and **multiple operators** to run independent sessions against that same
setup so their results can be compared.

This guide has two parts:
- **Part 1 — Preparing the session.** Done once per workload, by the preparer.
- **Part 2 — Running the session.** Done per operator, per session.

The agent's protocol lives in `AGENT_HANDOFF.md` → `RULES.md` / `EXECUTION.md` /
`SCHEMA.md` / `REFERENCE.md`. Humans don't need to read those in full — this guide
summarises what the preparer and operators actually do.

---

## Part 1 — Preparing the session (preparer)

### 1.1 Branch and folder convention

Each workload evaluation uses a dedicated branch and a matching folder at the repo
root:

- **Git branch:** `<workload-name>-<iteration>` — e.g., `mnist-1`.
- **Folder:** `<workload-name>/<iteration>/` — e.g., `mnist/1/`.

`<iteration>` increments when you re-run the same workload (e.g., after fixing a bug
in the card or the protocol). Each iteration is an independent evaluation.

At the end of the exercise, operator branches merge back into
`<workload-name>-<iteration>`, then `<workload-name>-<iteration>` merges into `main`.

### 1.2 Review the template

At the repo root lives the reusable template:

- `AGENT_HANDOFF.md` — agent's landing page.
- `RULES.md` — rules the agent holds throughout.
- `EXECUTION.md` — phase-by-phase procedure.
- `SCHEMA.md` — `results.csv` column spec.
- `REFERENCE.md` — lookup tables (sync-point checklist, HP interactions).
- `FINAL_SUMMARY_TEMPLATE.md` — end-of-session template for the agent.
- `WORKLOAD_CARD.md` — blank template; you fill the per-iteration copy (§1.3).
- `scripts/` — validation and scoring tooling.

Review these before a new evaluation campaign. If the rules or metrics don't match
your evaluation needs, edit the template on `main` before branching.

### 1.3 Fill `WORKLOAD_CARD.md`

The per-iteration `WORKLOAD_CARD.md` is filled *after* you branch (§1.4), in the new
folder. Decisions that most affect session quality:

- **Primary metric** — must be mechanically extractable (regex, JSON key, specific log
  line). If you'd have to hand-parse the output to read it, the agent's extraction
  recipe will fail and the validator will reject rows.
- **Quality metric + tolerance** — the tolerance is a candidate-gating threshold. Be
  precise about what "within tolerance" means for this workload (`-5%`,
  `-2·baseline_std`, or an explicit rule).
- **Benchmark window** — long enough to be representative, short enough that one full
  run can be scheduled multiple times during a session. Record the rationale.
- **Allowed / disallowed edits** — explicit and non-overlapping. The disallowed list
  is the semantic-surface boundary; if it is vague, agents will gravitate toward it
  and you will have to arbitrate mid-session.
- **Known caveats / prior art** — known baseline variance, optimisations already
  upstreamed, and (optional) a pre-declared Δ_min for cross-agent comparability.

Before handing off, work through §11 (Verification checklist) of the card. In
particular: **run the baseline command end-to-end from a clean environment yourself**,
and confirm the primary and quality metrics extract correctly. An un-verified card is
the most common cause of a lost session.

### 1.4 Hand off — commit to the iteration branch

From `main`, create the iteration branch and folder, then copy the template files in:

```bash
git checkout main
git pull
git checkout -b <workload-name>-<iteration>
mkdir -p <workload-name>/<iteration>
cp AGENT_HANDOFF.md RULES.md EXECUTION.md SCHEMA.md REFERENCE.md README.md \
   FINAL_SUMMARY_TEMPLATE.md WORKLOAD_CARD.md <workload-name>/<iteration>/
cp -r scripts <workload-name>/<iteration>/
# now fill <workload-name>/<iteration>/WORKLOAD_CARD.md per §1.3
git add <workload-name>/
git commit -m "Prepare <workload-name> iteration <iteration>"
git push -u origin <workload-name>-<iteration>
```

Notify operators that the branch is ready.

### 1.5 After all sessions complete

Each operator opens a PR from `<workload-name>-<iteration>-<agent-name>` back to
`<workload-name>-<iteration>`. Because each operator's artifacts live in a distinct
subfolder `<agent-name>/` (§2.2), the merges are conflict-free.

Once all operator branches are merged, open a PR from `<workload-name>-<iteration>`
into `main`. Comparison metrics (§"Comparison metrics" below) are computed from the
aggregated artifacts in `<workload-name>/<iteration>/*/artifacts/`.

---

## Part 2 — Running the session (operator)

### 2.0 Prerequisites

The agent operates on two repositories: the **workload repo** (e.g. milabench, where
the optimisation work happens) and **brdg-hackathon** (where protocol docs live and
artifacts are written). brdg-hackathon is cloned *inside* the workload repo so the
agent can reach it from one shell cwd.

First time on this machine:

```bash
# 1) Update the workload repo's main branch.
cd <workload-repo>           # e.g. milabench/
git checkout main
git pull

# 2) Clone brdg-hackathon inside it (if not already present).
git clone <brdg-hackathon-remote> brdg-hackathon

# 3) Make sure the workload repo ignores brdg-hackathon so the two histories stay
#    independent. Either add it to the shared .gitignore (one-time commit), or to
#    .git/info/exclude (local-only).
echo 'brdg-hackathon/' >> .gitignore   # or .git/info/exclude
```

The two repos commit independently from now on. You will create a branch in each
during the session — one in the workload repo for the optimisation (the agent creates
this per `EXECUTION.md §1.2`), and one in brdg-hackathon for the artifacts (§2.1).

### 2.1 Branch off the iteration

Inside `brdg-hackathon/`, start from the preparer's branch:

```bash
cd <workload-repo>/brdg-hackathon
git fetch origin
git checkout <workload-name>-<iteration>
git pull
git checkout -b <workload-name>-<iteration>-<agent-name>
```

`<agent-name>` uniquely identifies your session (e.g., `alice`, `agent-A`). Keep it
short and filesystem-safe.

### 2.2 Create your session artifact folder

Inside the iteration folder, create your subfolder:

```bash
# still inside brdg-hackathon/
mkdir -p <workload-name>/<iteration>/<agent-name>
```

Layout (paths shown from workload repo root):

```
<workload-repo>/
  (workload source)
  brdg-hackathon/
    <workload-name>/<iteration>/
      AGENT_HANDOFF.md, RULES.md, EXECUTION.md, ...   ← shared, read-only
      WORKLOAD_CARD.md                                ← shared, read-only
      scripts/                                        ← shared, read-only
      <agent-name>/                                   ← your session artifact root
        artifacts/                                    ← produced by the agent
```

You will only write inside `<agent-name>/`. Instructions and `WORKLOAD_CARD.md` at
`<workload-name>/<iteration>/` are shared with other operators — do not modify them.

### 2.3 Start the agent

Set the agent's **shell cwd to the workload repo root** (e.g. milabench root) — this is
where benchmark commands run. Point it at the instruction file
`brdg-hackathon/<workload-name>/<iteration>/AGENT_HANDOFF.md` as its starting read.

The agent:
- reads instructions from `brdg-hackathon/<workload-name>/<iteration>/`,
- writes artifacts to
  `brdg-hackathon/<workload-name>/<iteration>/<agent-name>/artifacts/`,
- creates its own optimisation branch in the **workload repo** (named
  `agent_<agent-name>_<short_goal>`, per `EXECUTION.md §1.2`).

### 2.4 Verify during the session (your primary role)

You are the **verifier**, not the scribe. The agent writes the logs; your job is to
confirm they are correct and to prompt the agent when it misses something.

**Confirm the agent wrote these at the top of `event_log.md`:**
- baseline command (matches `WORKLOAD_CARD.md §6` exactly),
- primary metric definition,
- quality metric and tolerance,
- benchmark window (fixed steps or fixed time).

**Confirm every claimed improvement includes:**
- repeated benchmark runs (median / min / max; N follows `RULES.md §6`),
- a quality / correctness check with an explicit verdict (`PASS` / `FAIL` /
  `INCONCLUSIVE`).

**When you intervene, prompt the agent to log it** using the `H-*` tags:
- "Log that as **H-STEER**" — you reframed the goal or scope.
- "Log that as **H-DEBUG**" — you found a bug or root cause.
- "Log that as **H-ARCH**" — you made an architecture decision.
- "Log that as **H-OPS**" — you fixed environment / run / tooling issues.

If unsure whether something counts as an intervention, log it anyway.

### 2.5 Close the session

At session end the agent emits `[SESSION-CLOSE]` and produces
`<agent-name>/artifacts/FINAL_SUMMARY.md`. Review it for:
- primary-metric improvement stated with CI and N (not a single-run number),
- quality verdict present and explicit,
- reproduction commands that actually run,
- dead ends listed,
- **workload-repo branch and final commit hash recorded** in §0 metadata (so
  reviewers can check out the optimised code).

**Push the workload-repo branch** (the optimisation work) so reviewers can see it:

```bash
cd <workload-repo>
git push -u origin agent_<agent-name>_<short_goal>
# (exact branch name is recorded in FINAL_SUMMARY.md §0)
```

**Commit and push the brdg-hackathon artifacts**, then open a PR back to
`<workload-name>-<iteration>`:

```bash
cd <workload-repo>/brdg-hackathon
git add <workload-name>/<iteration>/<agent-name>/
git commit -m "Session <agent-name>: results"
git push -u origin <workload-name>-<iteration>-<agent-name>
# then open PR: <workload-name>-<iteration>-<agent-name> → <workload-name>-<iteration>
```

Because your artifacts live in `<agent-name>/` — a path no other operator touches —
the merge into `<workload-name>-<iteration>` is conflict-free.

---

## Comparison metrics

Sessions are compared on:

**Primary**
- Improvement (%) in the primary metric at preserved quality.

**Secondary**
- Time to first measurable win.
- Dead-end rate (failed experiments / reverts).
- Human intervention count / severity.
- Reproducibility (clear commands + stable results).
- Engineering quality (maintainable diff; minimal invasiveness).
- Evidence-based reasoning (profiling → targeted fixes).
