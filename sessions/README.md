# Sessions — artifact tree

All per-session artifacts live here. The tree is:

```
sessions/
  <workload>/
    <iteration>/
      WORKLOAD_CARD.md                 (filled; shared across agents in this iteration)
      SESSION_START_PROMPT.md          (pre-filled; operators paste into agent at session start)
      prep/                            (preparer-agent artifacts; shared, read-only from sessions)
        prep_event_log.md
        prep_results.csv
        baseline_capture.txt
      <agent-name>/
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

Conventions:

- **One preparer, many operators.** The preparer fills `WORKLOAD_CARD.md` once per
  iteration, at `sessions/<workload>/<iteration>/`, and writes the `prep/` tree
  (HP-search artifacts) alongside it. Every `<agent-name>/` subfolder in that
  iteration reads from the same filled card and the same `prep/` baselines.
- **Session-agents write only inside `<agent-name>/`.** Iteration-level files
  (the filled card, `SESSION_START_PROMPT.md`, `prep/`) are read-only from the
  session-agent's perspective.
- **Preparer-agent writes only inside `<iteration>/` (card + `prep/`).** Never
  inside any `<agent-name>/` subfolder.
- **The playbook is not copied in.** Agents read the protocol from `playbook/` at the
  repo root. The brdg-hackathon branch + commit used for the session is recorded in
  the session's `[SESSION-START]` event-log entry (see `playbook/EXECUTION.md §1.2`);
  the preparer-agent records its own in `[PREP-START]` (see
  `playbook/RULES.md §18.3`).
- **One iteration per (workload, preparer revision).** Increment `<iteration>` when you
  re-prepare the same workload (fixing a bug in the card, revising the tolerance,
  re-running the HP search, etc.). Each iteration is an independent evaluation.

## Commit policy — what goes into `<agent-name>/` in git

The wholesale `git add sessions/<workload>/<iteration>/<agent-name>/` at
session close (root `README.md §5`) is filtered by `sessions/.gitignore`, but
the size + contents question is a policy, not a machine rule. Apply this
split when deciding what to keep under `artifacts/`:

**Always commit** — the machine-read contracts and key text evidence:

Session artifacts (inside `<agent-name>/`):

- `artifacts/benchmarks/results.csv` (schema parsed by scripts)
- `artifacts/benchmarks/baseline.txt` (raw baseline output)
- `artifacts/notes/event_log.md` (parsed by `score_session.py`)
- `artifacts/notes/preflight.txt` (environment capture)
- `artifacts/profiles/profiler_commands.md` (reproduction recipe)
- `artifacts/FINAL_SUMMARY.md` (the deliverable)

Preparation artifacts (inside `prep/`, at the iteration level):

- `prep/prep_results.csv` (schema: `playbook/SCHEMA.md §2`)
- `prep/prep_event_log.md` (prep tag family: `playbook/RULES.md §18`)
- `prep/baseline_capture.txt` (Prep Phase 1 sanity baseline stdout)

**Commit with a size cap** — trace files the reviewer may want to open:

- Text / JSON summaries of profiler output (flame graph JSON, chrome-trace
  JSON, hotspot tables): commit if under ~25 MB each and referenced from
  `FINAL_SUMMARY.md §Evidence`. Above that cap, store externally and link.

**Never commit** (enforced by `sessions/.gitignore`):

- Large proprietary traces: `*.qdrep`, `*.nsys-rep`, `*.ncu-rep`, `*.prof`,
  `*.pb`, `*.sqlite`. Summarise the finding in `FINAL_SUMMARY.md` and link
  to external storage if reviewers need the raw trace.
- Secrets: `.env`, API keys, tokens, `.netrc`, local `wandb/` state. If a
  secret leaked into `preflight.txt` from `env | grep` output, redact
  before committing.
- Ephemera: `__pycache__/`, `*.pyc`, `.ipynb_checkpoints/`, editor swap
  files, OS cruft.

When in doubt: if a file is not parsed by a script and not cited from
`FINAL_SUMMARY.md`, it probably does not earn its bytes in the commit.

See `workload-template/README.md` (human preparer) and
`workload-template/AGENT_HANDOFF.md` (preparer-agent) for the preparation
workflow, the root `README.md` for the operator's workflow, and
`playbook/AGENT_HANDOFF.md` for the session-agent's entry point.
