# Sessions — artifact tree

All per-session artifacts live here. The tree is:

```
sessions/
  <workload>/
    <iteration>/
      WORKLOAD_CARD.md                 (filled; shared across agents in this iteration)
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
  iteration, at `sessions/<workload>/<iteration>/`. Every `<agent-name>/` subfolder in
  that iteration reads from the same filled card.
- **Agents write only inside `<agent-name>/`.** The iteration-level files (the filled
  card) are read-only from the agent's perspective.
- **The playbook is not copied in.** Agents read the protocol from `playbook/` at the
  repo root. The brdg-hackathon branch + commit used for the session is recorded in
  the session's `[SESSION-START]` event-log entry (see `playbook/EXECUTION.md §1.2`).
- **One iteration per (workload, preparer revision).** Increment `<iteration>` when you
  re-prepare the same workload (fixing a bug in the card, revising the tolerance,
  etc.). Each iteration is an independent evaluation.

See `workload-template/README.md` for the preparer's workflow, the root
`README.md` for the operator's workflow, and `playbook/AGENT_HANDOFF.md` for the
agent's entry point.
