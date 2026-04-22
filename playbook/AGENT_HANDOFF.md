# Agent handoff — start here

## Goal (one sentence)
Reduce **time-to-result** (the end-goal metric, defined in `EXECUTION.md §4`) at
preserved quality (within the tolerance declared in `WORKLOAD_CARD.md §4`). The
**primary metric** in `WORKLOAD_CARD.md §2` is the cheap throughput proxy used to
guide the search; see `RULES.md §3` and `§8` for the relationship.

---

## Your first actions, in order

1. Read the filled workload card at
   `brdg-hackathon/sessions/<workload>/<iteration>/WORKLOAD_CARD.md` —
   workload-specific definitions (entry command, metric definitions, quality
   tolerance, allowed / disallowed edits).
2. Read `RULES.md` (sibling of this file in `playbook/`) — the measurement, logging,
   and bug-handling protocol you hold throughout the session.
3. Run `EXECUTION.md §1` (Bootstrap: session folder, `[SESSION-START]` event,
   preflight capture) **before** Phase 1.
4. Then begin Phase 1 (`EXECUTION.md §2`).

## Working model — three locations

- **Shell cwd**: the workload repo root (e.g. milabench). All benchmark commands (see
  `WORKLOAD_CARD.md §6`) run from here.
- **Playbook folder**: `brdg-hackathon/playbook/` — contains this file and the other
  protocol files (`RULES.md`, `EXECUTION.md`, `SCHEMA.md`, `REFERENCE.md`,
  `FINAL_SUMMARY_TEMPLATE.md`). Read-only.
- **Session artifact root**:
  `brdg-hackathon/sessions/<workload>/<iteration>/<agent-name>/` — where you write.
  All `artifacts/…` paths in these docs are relative to this root (e.g.
  `artifacts/notes/event_log.md` resolves to
  `brdg-hackathon/sessions/<workload>/<iteration>/<agent-name>/artifacts/notes/event_log.md`).
  The filled `WORKLOAD_CARD.md` lives one level up, at
  `brdg-hackathon/sessions/<workload>/<iteration>/WORKLOAD_CARD.md`, shared with
  other operators of this iteration.

---

## File set

Eagerly loaded (read before acting):
- `WORKLOAD_CARD.md` (filled, one level up from your session root) — workload spec.
- `RULES.md` — rules that govern every action you take during the session.
- `EXECUTION.md` — phase-by-phase procedure (Phase 1 → 2 → 3 → 4 → wrap-up).

Trigger-loaded (read when the trigger fires; evict when done):
- `SCHEMA.md` — `results.csv` column spec. Load on first CSV write (end of Phase 1
  baseline); hold through session.
- `REFERENCE.md` — lookup tables (sync-point checklist, HP interactions, and more).
  Each entry declares its own Trigger / Hold / Evict.
- `FINAL_SUMMARY_TEMPLATE.md` — end-of-session template; load during wrap-up.
- `sessions/README.md §Commit policy` — what to commit vs keep out of the
  artifact folder. Load (i) when producing profiler output (`RULES §12` cites
  it — save a committable summary instead of a binary trace), and (ii) at
  wrap-up (`EXECUTION §6`) before any `git add sessions/...` runs. Hold
  until the artifact commit is staged.

Not your doc:
- Root `README.md` — operator guide + dispatcher. Exception: `§6` cites the
  commit policy you also load above; read from `sessions/README.md` directly.
- `workload-template/` — preparation-time surfaces (template, preparer-agent
  handoff, human preparer guide). The preparation is already done by the time
  you run; read the filled card at
  `sessions/<workload>/<iteration>/WORKLOAD_CARD.md`, not the blank template.
- `editor-guide/` — meta; read by agents editing the corpus, not by you.

---

## Two rules to hold even if you read nothing else

- **You are the primary scribe.** Maintain `artifacts/notes/event_log.md`,
  `artifacts/benchmarks/results.csv`, and `artifacts/profiles/`. Log every human
  intervention as `H-STEER` / `H-DEBUG` / `H-ARCH` / `H-OPS`. If unsure whether
  something is an intervention, log it anyway. Details: `RULES.md §1`.
- **Bugs pause everything.** If a bug surfaces in any phase — Phase 1 triage, Phase 4
  optimization, or wrap-up — stop and follow the standing bug-handling procedure in
  `RULES.md §16` before continuing.

---

## Next

Open `WORKLOAD_CARD.md`.
