# Agent handoff — start here

## Goal (one sentence)
Reduce **time-to-result** (the end-goal metric, defined in `EXECUTION.md §4`) at
preserved quality (within the tolerance declared in `WORKLOAD_CARD.md §4`). The
**primary metric** in `WORKLOAD_CARD.md §2` is the cheap throughput proxy used to
guide the search; see `RULES.md §3` and `§8` for the relationship.

---

## Your first actions, in order

1. Read `WORKLOAD_CARD.md` (in this same folder) — workload-specific definitions (entry
   command, metric definitions, quality tolerance, allowed / disallowed edits).
2. Read `RULES.md` — the measurement, logging, and bug-handling protocol you hold
   throughout the session.
3. Run `EXECUTION.md §1` (Bootstrap: session-folder layout, session metadata,
   preflight capture) **before** Phase 1. The preflight capture is the first entry in
   `event_log.md`.
4. Then begin Phase 1 (`EXECUTION.md §2`).

## Working model — three locations

- **Shell cwd**: the workload repo root (e.g. milabench). All benchmark commands (see
  `WORKLOAD_CARD.md §6`) run from here.
- **Instruction folder**: `brdg-hackathon/<workload>/<iteration>/` — this folder,
  containing the protocol files and `WORKLOAD_CARD.md`. Read-only; shared with other
  operators.
- **Session artifact root**: `brdg-hackathon/<workload>/<iteration>/<agent-name>/` —
  where you write. All `artifacts/…` paths in these docs are relative to this root
  (e.g. `artifacts/notes/event_log.md` resolves to
  `brdg-hackathon/<workload>/<iteration>/<agent-name>/artifacts/notes/event_log.md`).

---

## File set

Eagerly loaded (read before acting):
- `WORKLOAD_CARD.md` — workload spec (filled by the human before the session).
- `RULES.md` — rules that govern every action you take during the session.
- `EXECUTION.md` — phase-by-phase procedure (Phase 1 → 2 → 3 → 4 → wrap-up).

Trigger-loaded (read when the trigger fires; evict when done):
- `SCHEMA.md` — `results.csv` column spec. Load on first CSV write (end of Phase 1
  baseline); hold through session.
- `REFERENCE.md` — lookup tables (sync-point checklist, HP interactions, and more).
  Each entry declares its own Trigger / Hold / Evict.
- `FINAL_SUMMARY_TEMPLATE.md` — end-of-session template; load during wrap-up.

Not your doc:
- `README.md` — human-verifier guide.

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
