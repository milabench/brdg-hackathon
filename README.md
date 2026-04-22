# Optimization Hackathon

This repo hosts the protocol for an ML-optimization hackathon: one human operator
pairs with one coding agent to optimize a workload, against a written rulebook
that keeps results comparable across sessions.

## Who are you?

- **An agent improving the instruction corpus** → read
  [`editor-guide/README.md`](editor-guide/README.md).
- **An agent running an optimization session** → start at
  [`playbook/AGENT_HANDOFF.md`](playbook/AGENT_HANDOFF.md).
- **An agent preparing a new hackathon iteration** → start at
  [`workload-template/AGENT_HANDOFF.md`](workload-template/AGENT_HANDOFF.md).
- **A human preparing a new hackathon iteration** → read
  [`workload-template/README.md`](workload-template/README.md).
- **A human running a hackathon as operator** → continue below.

## Repo layout

```
playbook/            session-agent protocol (read-only; not copied per session)
workload-template/   WORKLOAD_CARD.md template + preparer-agent handoff + human preparer guide
sessions/            per-session artifacts, grouped by workload/iteration/agent
editor-guide/        for agents editing the instruction corpus
scripts/             validation, scoring, plotting, aggregation
README.md            this file — operator guide + dispatcher
```

The `playbook/` and `workload-template/` are shared read-only across all
sessions. Sessions write only under
`sessions/<workload>/<iteration>/<agent-name>/`. The brdg-hackathon branch +
commit used for each session is recorded in the session's `[SESSION-START]`
event-log entry, so the protocol files do not need to be copied into the session
folder.

---

# Operator guide

You are running a session as operator, paired with a coding agent. The preparer
has already branched `<workload-name>-<iteration>` and committed the filled
`sessions/<workload-name>/<iteration>/WORKLOAD_CARD.md`. Your job is to branch
off that, start the agent, and verify what it logs.

## 1) Prerequisites

The agent operates on two repositories: the **workload repo** (e.g. milabench,
where the optimisation work happens) and **brdg-hackathon** (where protocol docs
live and artifacts are written). brdg-hackathon is cloned *inside* the workload
repo so the agent can reach it from one shell cwd.

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
during the session — one in the workload repo for the optimisation (the agent
creates this per `playbook/EXECUTION.md §1.2`), and one in brdg-hackathon for the
artifacts (§2).

## 2) Branch off the iteration

Inside `brdg-hackathon/`, start from the preparer's branch:

```bash
cd <workload-repo>/brdg-hackathon
git fetch origin
git checkout <workload-name>-<iteration>
git pull
git checkout -b <workload-name>-<iteration>-<agent-name>
```

`<agent-name>` uniquely identifies your session (e.g., `alice`, `agent-A`). Keep
it short and filesystem-safe.

## 3) Create your session artifact folder

```bash
# still inside brdg-hackathon/
mkdir -p sessions/<workload-name>/<iteration>/<agent-name>
```

Layout (paths shown from workload repo root):

```
<workload-repo>/
  (workload source)
  brdg-hackathon/
    playbook/                                       ← read-only protocol
    sessions/<workload-name>/<iteration>/
      WORKLOAD_CARD.md                              ← shared, read-only (filled)
      <agent-name>/                                 ← your session artifact root
        artifacts/                                  ← produced by the agent
```

You will only write inside `<agent-name>/`. The filled `WORKLOAD_CARD.md` one
level up is shared with other operators — do not modify it.

## 4) Start the agent

Set the agent's **shell cwd to the workload repo root** (e.g. milabench root) —
this is where benchmark commands run. Point it at the protocol entry point
`brdg-hackathon/playbook/AGENT_HANDOFF.md` as its starting read.

The agent:
- reads the protocol from `brdg-hackathon/playbook/`,
- reads the filled workload card from
  `brdg-hackathon/sessions/<workload-name>/<iteration>/WORKLOAD_CARD.md`,
- writes artifacts to
  `brdg-hackathon/sessions/<workload-name>/<iteration>/<agent-name>/artifacts/`,
- creates its own optimisation branch in the **workload repo** (named
  `agent_<agent-name>_<short_goal>`, per `playbook/EXECUTION.md §1.2`).

## 5) Verify during the session (your primary role)

You are the **verifier**, not the scribe. The agent writes the logs; your job is
to confirm they are correct and to prompt the agent when it misses something.

**Confirm the agent wrote `[SESSION-START]` at the top of `event_log.md`** with
the brdg-hackathon branch + commit, the workload / iteration, hardware, and
software info (`playbook/EXECUTION.md §1.2`).

**Confirm the agent wrote these in its event log after `[SESSION-START]`:**
- baseline command (matches `WORKLOAD_CARD.md §6` exactly),
- primary metric definition,
- quality metric and tolerance,
- benchmark window (fixed steps or fixed time).

**Confirm every claimed improvement includes:**
- repeated benchmark runs (median / min / max; N follows `playbook/RULES.md §6`),
- a quality / correctness check with an explicit verdict (`PASS` / `FAIL` /
  `INCONCLUSIVE`).

**When you intervene, prompt the agent to log it** using the `H-*` tags:
- "Log that as **H-STEER**" — you reframed the goal or scope.
- "Log that as **H-DEBUG**" — you found a bug or root cause.
- "Log that as **H-ARCH**" — you made an architecture decision.
- "Log that as **H-OPS**" — you fixed environment / run / tooling issues.

If unsure whether something counts as an intervention, log it anyway.

## 6) Close the session

At session end the agent emits `[SESSION-CLOSE]` and produces
`<agent-name>/artifacts/FINAL_SUMMARY.md`. Review it for:
- primary-metric improvement stated with CI and N (not a single-run number),
- quality verdict present and explicit,
- reproduction commands that actually run,
- dead ends listed,
- **workload-repo branch and final commit hash recorded** in §0 metadata (so
  reviewers can check out the optimised code),
- **brdg-hackathon branch and commit** recorded in §0 metadata (from
  `[SESSION-START]`).

**Push the workload-repo branch** (the optimisation work) so reviewers can see
it:

```bash
cd <workload-repo>
git push -u origin agent_<agent-name>_<short_goal>
# (exact branch name is recorded in FINAL_SUMMARY.md §0)
```

**Commit and push the brdg-hackathon artifacts**, then open a PR back to
`<workload-name>-<iteration>`:

```bash
cd <workload-repo>/brdg-hackathon
git add sessions/<workload-name>/<iteration>/<agent-name>/
git commit -m "Session <agent-name>: results"
git push -u origin <workload-name>-<iteration>-<agent-name>
# then open PR: <workload-name>-<iteration>-<agent-name> → <workload-name>-<iteration>
```

Because your artifacts live in `sessions/<workload-name>/<iteration>/<agent-name>/`
— a path no other operator touches — the merge into
`<workload-name>-<iteration>` is conflict-free.

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
