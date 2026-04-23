# Agent handoff — start here

## Goal (one sentence)
Reduce **time-to-result** (TTR — the end-goal metric, measured against the target
quality in `WORKLOAD_CARD.md §10.2` and the locked-HP Tier-2 baseline in `§10.3`,
both pinned during preparation) at preserved quality (within the tolerance declared
in `WORKLOAD_CARD.md §4`). The **primary metric** in `WORKLOAD_CARD.md §2` is the
cheap throughput proxy used to screen Phase 3 candidates; TTR is the sole gate for
`[WIN]` emission (`RULES §3`, `§8`). HPs are **already locked** by the preparer-agent
and carried in `WORKLOAD_CARD §10`; Phase 3 optimises at those locked HPs.

---

Paths in this file use `<workload>`, `<iteration>`, and `<agent-name>`
placeholders. The concrete values were supplied to you by the
`sessions/<workload>/<iteration>/SESSION_START_PROMPT.md` the operator
pointed you at (and `<agent-name>` by the operator's starting message).
Use those when resolving the paths below.

## Your first actions, in order

1. Read the filled workload card at
   `brdg-hackathon/sessions/<workload>/<iteration>/WORKLOAD_CARD.md` —
   workload-specific definitions (entry command, metric definitions, quality
   tolerance, allowed / disallowed edits, and crucially §10: locked HPs +
   pinned Tier-1 / Tier-2 baselines produced by the preparer-agent).
2. Ensure the workload is installed in this environment. If the
   `WORKLOAD_CARD.md §6` Install / environment setup commands have not been
   run on this host (e.g. the baseline command is not executable, required
   modules not importable), run them now — verbatim as recorded in the card.
   The preparer-agent already verified those commands produce a working
   baseline; do not invent alternatives. Skip this step on subsequent
   sessions on the same host.
3. Read `RULES.md` (sibling of this file in `playbook/`) — the measurement, logging,
   and bug-handling protocol you hold throughout the session. Session-agent reads
   the whole file; skip the `Preparer-agent` paragraphs in §1 and §18.
4. Run `EXECUTION.md §1` (Bootstrap: session folder, `[SESSION-START]` event,
   preflight capture) **before** Phase 1.
5. Then begin Phase 1 (`EXECUTION.md §2`): bug-first pass at the locked HPs from
   `WORKLOAD_CARD §10.1`. Phase 2 (`EXECUTION.md §3`) adopts the Tier-2 baseline
   from `§10.3` and re-measures Tier-1 on the session host. Phase 3
   (`EXECUTION.md §4`) is the optimization loop.

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
- `WORKLOAD_CARD.md` (filled, one level up from your session root) — workload spec,
  including §10 locked HPs + pinned Tier-1 / Tier-2 baselines.
- `RULES.md` — rules that govern every action you take during the session.
- `EXECUTION.md` — phase-by-phase procedure (Phase 1 → 2 → 3 → wrap-up).

Trigger-loaded (read when the trigger fires; evict when done):
- `SCHEMA.md` — `results.csv` column spec. Load on first CSV write (end of Phase 1
  baseline); hold through session.
- `REFERENCE.md` — lookup tables (sync-point checklist, HP interactions, and more).
  Each entry declares its own Trigger / Hold / Evict.
- `FINAL_SUMMARY_TEMPLATE.md` — end-of-session template; load during wrap-up.
- `sessions/README.md §Commit policy` — what to commit vs keep out of the
  artifact folder. Load (i) when producing profiler output (`RULES §12` cites
  it — save a committable summary instead of a binary trace), and (ii) at
  wrap-up (`EXECUTION §5`) before any `git add sessions/...` runs. Hold
  until the artifact commit is staged.

Not your doc:
- Root `README.md` — operator guide + dispatcher. Exception: `§5` cites the
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
- **Bugs pause everything.** If a bug surfaces in any phase — Phase 1 triage, Phase 3
  optimization, or wrap-up — stop and follow the standing bug-handling procedure in
  `RULES.md §16` before continuing.

---

## Next

Open `WORKLOAD_CARD.md`.
