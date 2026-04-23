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
workload-template/   WORKLOAD_CARD.md + SESSION_START_PROMPT.md templates + preparer-agent handoff + human preparer guide
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
`sessions/<workload-name>/<iteration>/WORKLOAD_CARD.md` along with the
pre-filled `SESSION_START_PROMPT.md` alongside it. Your job is to branch
off that, start the agent, and verify what it logs.

## 1) Prerequisites

The agent operates on two repositories: the **workload repo** (e.g. milabench,
where the optimisation work happens) and **brdg-hackathon** (where protocol docs
live and artifacts are written). brdg-hackathon is cloned *inside* the workload
repo so the agent can reach it from one shell cwd.

The preparer has already pushed a workload-repo branch named
`hackathon-<workload>-<iteration>` with `brdg-hackathon/` committed to `.gitignore`
and the baseline verified end-to-end. You check that branch out — you do not
edit the workload repo's `.gitignore` yourself. The branch name and head commit
are pinned in `WORKLOAD_CARD.md §1`.

### Compute jobs (slurm clusters)

The agent process and the workload run in **separate** jobs. The agent itself
only shells out commands and reads files — it does not need a GPU — so it
sits in a small long-lived CPU-only job, and each benchmark command requests
GPU time on its own. On the Mila cluster, defaults:

- **Agent host (CPU-only, long-lived):**
  `salloc -c 2 --mem=10G --partition=main-cpu`
- **GPU for the workload:** `--partition=unkillable -c 6 --gres=gpu:l40s:1`
  — already wrapped into the baseline command in `WORKLOAD_CARD.md §6` by
  the preparer-agent, so you do not start it separately; the session-agent
  inherits it when it runs the command.

See [docs.mila.quebec](https://docs.mila.quebec) for Mila-specific docs. On a
different cluster, substitute partition names accordingly; the split between
agent-host and workload jobs stays the same.

### Clone the repos

First time on this machine (run inside the CPU-only job above, so the install
the agent does later lives where the agent lives):

```bash
# 1) Check out the prepared workload-repo branch.
cd <workload-repo>           # e.g. milabench/
git fetch
git checkout hackathon-<workload-name>-<iteration>

# 2) Clone brdg-hackathon inside the workload repo (if not already present).
#    It is already listed in .gitignore on this branch, so the workload repo's
#    tree stays clean — no local edits required.
git clone <brdg-hackathon-remote> brdg-hackathon
```

### Install the workload

You do not install the workload by hand. Once you start the agent (§3), it
reads the filled `WORKLOAD_CARD.md` — including the `WORKLOAD_CARD.md §6`
Install / environment setup sub-section — and runs the install commands the
preparer-agent recorded there as one of its first actions, before Bootstrap
and Phase 1. Install responsibility for the operator ends at the two clones
above and the CPU-only job that hosts the agent.

The two repos commit independently from now on. You will create a branch in each
during the session — one in the workload repo for the optimisation (the agent
creates this off `hackathon-<workload-name>-<iteration>` per `playbook/EXECUTION.md §1.2`),
and one in brdg-hackathon for the artifacts (§2).

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

## 3) Start the agent

Inside the CPU-only job from §1, start the agent at the workload repo root
(or set its shell cwd there). Benchmark commands run from there. Send the
agent a one-line starting message, substituting `<workload-name>`,
`<iteration>` (from §2), and `<agent-name>`:

```text
Read file brdg-hackathon/sessions/<workload-name>/<iteration>/SESSION_START_PROMPT.md. Your agent name is <agent-name>.
```

The agent reads that file and follows `playbook/AGENT_HANDOFF.md` from
there: runs `WORKLOAD_CARD.md §6` install if the workload is not yet set
up on this host, sets up its artifact root and event log, creates its
workload-repo optimisation branch
`hackathon-<workload-name>-<iteration>-<agent-name>` (off the preparer's
`hackathon-<workload-name>-<iteration>`, per `playbook/EXECUTION.md §1.2`),
and begins Phase 1. The filled `WORKLOAD_CARD.md` is shared read-only
across every operator on this iteration.

## 4) Verify during the session (your primary role)

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

## 5) Close the session

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
git push -u origin hackathon-<workload-name>-<iteration>-<agent-name>
# (exact branch name is recorded in FINAL_SUMMARY.md §0)
```

**Commit and push the brdg-hackathon artifacts**, then open a PR back to
`<workload-name>-<iteration>`. Before `git add`, scan the artifact folder
against `sessions/README.md §Commit policy` — `sessions/.gitignore` filters
the common large-binary and secret patterns automatically, but the size cap
and "machine-read vs evidence" split are judgment calls that land on you:

```bash
cd <workload-repo>/brdg-hackathon
git add sessions/<workload-name>/<iteration>/<agent-name>/
git status                                                   # review what was staged
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
