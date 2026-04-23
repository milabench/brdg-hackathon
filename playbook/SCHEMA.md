# SCHEMA — `results.csv` and `prep_results.csv`

> **Loaded from.** `RULES §14.2` (post-experiment checklist, `csv[_]` box),
> `EXECUTION §2`/`§3`/`§4` (session CSV writes),
> `workload-template/AGENT_HANDOFF.md` Prep Phase 1 / 2 (prep CSV writes).
> **Load on.** first CSV write.
> **Hold.** through the session / preparation — referenced on every CSV append.
> Not eagerly loaded at bootstrap; each agent reads it the first time it needs to
> write a row, then keeps it resident.

Two CSVs, same 23 columns, different `phase` enum values:

- **Session CSV** (§1) — `artifacts/benchmarks/results.csv`, written by the
  session-agent during Phase 1 / Phase 2 / Phase 3.
- **Preparation CSV** (§2) — `sessions/<workload>/<iteration>/prep/prep_results.csv`,
  written by the preparer-agent during Prep Phase 1 / Prep Phase 2.

A fixed header makes per-session plotting (`plot_results.py`) and cross-session
aggregation (`aggregate_sessions.py`) mechanical, and lets the `csv[_]` box in
`RULES §14.2` (post-experiment checklist) be ticked by a simple schema-compliance
check.

One row per **measured run** (not per experiment). N measured runs → N rows sharing one
`experiment_id`. The warmup run uses `run_index = -1` and is kept for traceability even
though it is discarded from statistics.

---

## 1) Session `results.csv` — required columns (in this order)

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `session_id` | string | `<YYYY-MM-DD>_<agent_id>`, stable for the whole session. |
| 2 | `experiment_id` | string | Unique per experiment group; format `<session_id>:<counter>`. |
| 3 | `run_index` | int | `0..N-1` within this experiment; `-1` for the warmup run. |
| 4 | `timestamp` | ISO 8601 UTC | End time of this run. |
| 5 | `tier` | `short` / `full` | Measurement tier; see `RULES §8`. |
| 6 | `phase` | string | One of `phase_1_bugfix`, `phase_2_adopt`, `phase_3_iter`, `phase_3_validation`. Phase 3 rows split by tier: `phase_3_iter` ↔ `tier=short`, `phase_3_validation` ↔ `tier=full`. A row produced while handling a bug (`RULES §16`) carries the phase value of the phase active when the bug fired, not a dedicated bug phase. |
| 7 | `candidate` | string | `baseline` or a candidate label (e.g. `fused_sampler`, `compile_flag_a`). |
| 8 | `change` | string | One-line description of the single-variable change vs baseline (`none` for baseline rows). See `RULES §9` (change-one-thing discipline). |
| 9 | `baseline_ref` | string | `experiment_id` of the comparison baseline; empty for baseline rows themselves. |
| 10 | `commit_hash` | string | Git commit at which this run was taken. |
| 11 | `env_snapshot_id` | string | Environment-snapshot identifier from `RULES §5` (preflight). Comparisons across different ids require a drift-tagged re-baseline. |
| 12 | `primary_metric` | float | Value in the unit declared in `WORKLOAD_CARD.md §2`. |
| 13 | `quality_metric` | float | Value in the unit declared in `WORKLOAD_CARD.md §3`. Empty for primary-metric-only smoke runs. |
| 14 | `peak_gpu_mem_mib` | float | Nullable. |
| 15 | `quality_verdict` | `PASS` / `FAIL` / `INCONCLUSIVE` / `NA` | Experiment-level verdict; see `RULES §11`. Repeated across rows of the same `experiment_id`. |
| 16 | `win_status` | `NA` / `EXPERIMENT` / `WIN` / `INVALIDATED` | `WIN` is emitted only on Tier 2 after passing both `RULES §7` gates; `INVALIDATED` is set retroactively when a bug-fix shifts the baseline (`RULES §16`). |
| 17 | `logging_mode` | `original` / `modified` | For `RULES §15` (logging-overhead reporting). Defaults to `original`. |
| 18 | `event_log_anchor` | string | `T+…` offset or identifier pointing at the corresponding entry in `event_log.md`. |
| 19 | `notes` | string | Free text. Put `invalidated_reason` here when applicable. |
| 20 | `gpu_util_avg` | float | Average GPU utilization during the run (%). `NA` if unavailable. |
| 21 | `cpu_util_avg` | float | Average CPU utilization during the run (%). `NA` if unavailable. |
| 22 | `compile_time_s` | float | Compile / warmup time in seconds. `NA` if not applicable. |
| 23 | `hp_values_json` | string | JSON blob of HP settings for this run; `{}` for non-sweep rows. |

The column set is fixed — every row has all 23 columns. Use `NA` (or `{}` for
`hp_values_json`) for values that don't apply to a given row. This keeps cross-session
aggregation mechanical: a single header is valid across every session and workload.

Every `phase=phase_3_*` row's `hp_values_json` must equal
`WORKLOAD_CARD §10.1`'s `hp_values_json` verbatim — the session optimizes **at the
locked HPs**, so every Phase 3 measurement is pinned to that config.

---

## 2) Preparation `prep_results.csv` — required columns

Same 23 columns and types as §1. Differences are limited to which enum values are
legal for two columns, reflecting the preparer-agent's role:

| Column | Allowed values in `prep_results.csv` |
|--------|--------------------------------------|
| `session_id` | Substitute `prep_id`: `<YYYY-MM-DD>_prep_<workload>_<iteration>`. Stable for the whole preparation. |
| `phase` | One of `prep_p1_sanity_baseline`, `prep_p2_short_baseline`, `prep_p2_sweep`, `prep_p2_default_ttr`, `prep_p2_validation`. Tier coupling: `prep_p1_sanity_baseline` and `prep_p2_short_baseline` / `prep_p2_sweep` are `tier=short`; `prep_p2_default_ttr` and `prep_p2_validation` are `tier=full`. |
| `win_status` | Only `NA` and `EXPERIMENT` are legal — preparation does not emit `[WIN]`. |

All other columns keep the §1 semantics. In particular:

- `hp_values_json` carries the candidate HP set for sweep and validation rows
  (`prep_p2_sweep`, `prep_p2_default_ttr`, `prep_p2_validation`); `{}` on
  `prep_p1_sanity_baseline` and `prep_p2_short_baseline` rows.
- `quality_verdict` applies per `RULES §11` for every TTR row.
- `baseline_ref` for sweep rows points at the `prep_p2_short_baseline`
  experiment_id (same-tier rule); for validation rows, at the
  `prep_p2_default_ttr` experiment_id.

The winning candidate's `experiment_id` (a `prep_p2_validation` row, or a
`prep_p2_default_ttr` row if the default-HP fallback wins) is pinned in
`WORKLOAD_CARD §10.3` as the session's Tier-2 baseline reference.

---

## 3) Append-only policy

Rows are never deleted. Retroactive updates are limited to:

- `win_status` → `INVALIDATED` after a bug-fix shifts the baseline (`RULES §16`);
- `notes` — appending a reason for invalidation or a correction pointer.

Any other correction is a **new** row with a pointer to the original in `notes`.

---

## 4) Validation (enforced by `scripts/validate_artifacts.py`)

Applies to both `results.csv` and `prep_results.csv`; the script takes a
`--mode session|prep` flag to pick the legal `phase` / `win_status` enum.

- The header matches the required column list exactly.
- For every `experiment_id`, `candidate`, `change`, `baseline_ref`, `phase`, and `tier`
  are constant across its rows.
- `quality_verdict` and `win_status` are constant within an `experiment_id`.
- Every non-baseline `experiment_id` has a valid `baseline_ref` that points to an
  existing baseline `experiment_id` in the same `tier`.
- Session mode only: every `phase=phase_3_*` row's `hp_values_json` matches
  `WORKLOAD_CARD §10.1` (pinned locked HPs).
- Prep mode only: `win_status ∈ {NA, EXPERIMENT}` (prep emits no wins).
