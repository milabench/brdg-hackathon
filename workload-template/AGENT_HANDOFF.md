# Preparer-agent handoff — start here

You are pairing with a human preparer to set up a new hackathon iteration for a
milabench pipeline. Your job is to draft `WORKLOAD_CARD.md`, **run the HP search**,
lock the winning configuration, and commit — after the human confirms every
judgment call.

The pipeline catalogue lives at
[milabench/config/standard.yaml](https://github.com/milabench/milabench/blob/master/config/standard.yaml);
per-pipeline code lives under `benchmarks/<pipeline>/` in the same repo.

---

## Goal (one sentence)

Produce two prepared branches — `hackathon-<workload>-<iteration>` on the workload
repo (with `brdg-hackathon/` committed to `.gitignore` and the baseline verified
end-to-end) and `<workload>-<iteration>` on brdg-hackathon (with a filled
`sessions/<workload>/<iteration>/WORKLOAD_CARD.md` pinning that workload branch,
the locked HP configuration, and the Tier-1 / Tier-2 baselines every
session-agent will use) — ready for operators to run optimisation sessions
against.

Preparation is a real measurement exercise: you run the HP sweep once during
preparation so every session-agent starts from the same locked config. `RULES §6`
(noise-aware N), `§7` (min-win gate), `§8` (two-tier cadence), `§11` (quality
check), and `§16` (bug handling) apply to you exactly as they do to the session
agent. Prep artifacts (event log, CSV, tag family) are in `RULES §18`.

---

## Prep phases — the shape of your work

Three phases in order. Each has an explicit exit criterion and a `[PREP-EXIT N]`
milestone:

- **Prep Phase 1 — Workload discovery & card draft** (§3). Interview the human,
  fill `WORKLOAD_CARD §0–§9` and §11, create the workload-repo prep branch, run
  the sanity baseline at default HPs.
- **Prep Phase 2 — HP search & lock** (§4). Short-run + default-HP TTR
  baselines, proxy sweep, TTR validation with backtrack, lock the winner, fill
  `WORKLOAD_CARD §10`.
- **Prep Phase 3 — Publish** (§5). Human reviews the filled card; copy
  `SESSION_START_PROMPT.md`, commit, push both branches.

`RULES §16` (bug handling) fires from any prep phase.

---

## Your first actions, in order

1. Ask the human: "Which milabench pipeline are we preparing?" Wait for the
   answer before proceeding.
2. Infer the iteration number. List
   `brdg-hackathon/sessions/<workload>/` — if it does not exist, iteration is
   `1`; otherwise pick the highest existing integer + 1. Tell the human what
   you inferred so they can override if they are re-preparing a specific
   iteration.
3. Resolve the pipeline. Your shell cwd is the milabench repo root — read
   `config/standard.yaml`, find the pipeline entry, follow it to its code
   under `benchmarks/<pipeline>/`. If milabench is not present at the expected
   path, ask the human where it is (or whether to
   `git clone https://github.com/milabench/milabench`).
4. Read the pipeline code: main script, dataloader, any per-pipeline config.
   Identify what is trained, what is logged (stdout / files / wandb), typical
   run length, obvious bottleneck candidates.
5. Read `brdg-hackathon/workload-template/WORKLOAD_CARD.md` — the template you
   will fill.
6. Read `brdg-hackathon/workload-template/README.md` — the human preparer's
   counterpart. It is their verification checklist; knowing what they will
   check helps you fill fields they can actually verify.
7. Read `brdg-hackathon/playbook/RULES.md §§1, 3–4, 6–13, 16–18` and
   `brdg-hackathon/playbook/SCHEMA.md §§1–2, 4` — the contracts your work must
   satisfy (metric definitions, tolerance semantics, two-tier split,
   noise-aware N, quality-check rules, bug-handling, the prep artifact tree
   + tag family, the prep CSV schema).
8. Read `brdg-hackathon/playbook/REFERENCE.md §2` — hyperparameter-interaction
   lookup used by Prep Phase 2.
9. Run §2 Bootstrap.
10. Begin Prep Phase 1 (§3).

---

## Working model — three locations

- **Shell cwd**: milabench repo root. `config/standard.yaml` and `benchmarks/`
  are at your fingertips; baseline and HP-search commands run from here. You
  will also **create and push a `hackathon-<workload>-<iteration>` branch on
  this repo** carrying prep-time changes (the `.gitignore` entry below, and any
  fixups the human approves before baseline) — operators start their sessions
  from this branch, not from the upstream default.
- **Hackathon folder**: `brdg-hackathon/` (cloned inside milabench). Contains
  `workload-template/` (this file, the blank card, the human README),
  `playbook/` (the session-agent protocol you read selectively), `sessions/`
  (where you write the filled card and your prep artifacts).
- **Iteration folder** (you create it):
  `brdg-hackathon/sessions/<workload>/<iteration>/` — the filled card,
  `SESSION_START_PROMPT.md`, and the `prep/` artifact tree
  (`prep_event_log.md`, `prep_results.csv`, `baseline_capture.txt`) live
  here. Future session-agents read it read-only.

---

## File set

Eagerly loaded (read before acting):
- `workload-template/WORKLOAD_CARD.md` — the template to fill.
- `workload-template/SESSION_START_PROMPT.md` — template for the operator's
  session-start prompt; you copy it into the iteration folder and substitute
  `<workload>` / `<iteration>` (see §5).
- `workload-template/README.md` — the human's verification checklist.
- `playbook/RULES.md` §§1, 3–4, 6–13, 16–18 and `playbook/SCHEMA.md` §§1–2, 4 —
  shared rulebook + CSV contracts.
- `playbook/REFERENCE.md §2` — HP interactions lookup for Prep Phase 2.

Trigger-loaded:
- The pipeline's own code — load during pipeline discovery (steps 3–4 of
  "first actions"), hold through Prep Phase 1 and the HP search.
- `milabench.readthedocs.io` — load when the human asks about milabench
  semantics you did not learn from the code (e.g. `milabench dev` vs `run`).

Not your doc:
- `playbook/AGENT_HANDOFF.md` and the rest of `playbook/` beyond the sections
  above — that corpus is for the session-running optimisation agent, not you.
  In particular, `RULES §5` (preflight) and `§15` (logging-overhead reporting)
  are session-only, and `§14.3` covers session milestone body shapes distinct
  from yours (your tag family + body shapes are in §18).
- `editor-guide/` — meta; for agents editing the corpus.

---

## 2) Bootstrap (before Prep Phase 1)

Create the iteration folder and the `prep/` subtree. Open
`sessions/<workload>/<iteration>/prep/prep_event_log.md` and write
`[PREP-START]` at `T+0` — body shape in `RULES §18.3`. Capture the same hardware
/ software / repo-version context a session-agent records at `[SESSION-START]`
(hardware, driver, CUDA, framework versions, hackathon-repo branch + commit) so
the locked-HP measurements are reproducible.

**Cross-checks.** The `Hardware:` line should match `WORKLOAD_CARD §9` once you
fill it. The hackathon-repo branch + commit line is the version of the corpus
this preparation was performed against.

---

## 3) Prep Phase 1 — Workload discovery & card draft

### 3.1 Interview protocol

For every section of `WORKLOAD_CARD.md`, **propose defaults first, multiple
choice where possible, grounded in what you read from the code**. Do not ask
open-ended questions. Do not record your own guess without confirmation.
Pattern for every question:

```
I see <evidence from code>. Candidate answers:
  (a) <option grounded in evidence> — <why it fits>
  (b) <option grounded in evidence> — <why it fits>
  (c) custom (describe)
Which do you want?
```

Per-section guidance (Prep Phase 1 fills §0–§9 and §11; §10 is filled in Prep
Phase 2 after the HP search completes):

- **§0 Session identity.** Workload slug from the pipeline name; iteration
  from step 2 of "first actions" (inferred, human-confirmed); date = today;
  draft a one-sentence summary from the code, ask the human to approve or
  rewrite.
- **§1 Target workload.** Repo URL = the workload remote; upstream base = the
  branch @ commit you branched from (normally `main @ <current HEAD>`);
  **prepared branch = `hackathon-<workload>-<iteration>`** (you will create and
  push it in §3.2 below); prepared-branch head commit is filled in **after**
  that commit lands. Benchmark code path from `config/standard.yaml`; entry
  point from the config; read-only reference code = files whose change would
  alter semantics (dataset loader, eval, reward / loss). Ask the human to
  narrow.
- **§2 Primary metric.** Propose 2–3 candidates you saw logged, ordered by
  how mechanically extractable they are. Show the extraction recipe (regex /
  JSON key / log line) for each. Warn explicitly if any candidate needs
  hand-parsing — that recipe will fail the validator.
- **§3 Quality metric.** Propose 1–2 candidates (eval loss, accuracy, reward,
  …). For each, state the eval protocol you inferred (episodes / batches,
  horizon, seeds, deterministic or stochastic).
- **§4 Tolerance.** Propose: `(a) -2·baseline_std` (safe default for
  stochastic training), `(b) -X%` with X drawn from prior art if available,
  `(c) explicit rule`. Explain the tradeoff (tight = fewer false wins; loose
  = fewer false rejections).
- **§5 Benchmark window.** Estimate per-step wall time from log cadence or a
  short dry run. Propose `(a) fixed N steps ≈ M minutes on target hardware`
  (cite M) or `(b) fixed T seconds ≈ N steps`. Capture the rationale verbatim.
- **§6 Setup and entry command(s).** Two sub-parts. **Install / environment
  setup**: capture the exact commands that bring a freshly-cloned workload
  repo (on the prepared branch) to a runnable state — what you installed
  yourself, or what the workload's README / CI encodes. These are what the
  operator will run once before their first session; the sanity baseline in
  §3.3 is the acid test that the listed commands actually produce a working
  environment. Also record system-level prerequisites (driver / CUDA / Python
  versions, OS) that those commands assume. **Direct / wrapper invocation**:
  draft the exact `milabench` / direct-invocation command from
  `config/standard.yaml`; include env vars and working directory. On a slurm
  cluster, wrap the baseline in `srun` (or equivalent) with resources matching
  §9 hardware (e.g. Mila:
  `srun --partition=unkillable -c 6 --gres=gpu:l40s:1 <command>`) so the
  operator's session-agent inherits the right GPU placement. Run the command
  end-to-end in §3.3; the commands that actually ran are what go in the card.
- **§7, §8 Allowed / disallowed.** Propose a split based on the code:
  disallowed first (eval, dataset / environment internals, reward / loss);
  allowed second (training loop, data pipeline, model forward, config). Must
  be non-overlapping; ask the human to narrow or extend.
- **§9 Hardware.** Infer from the pipeline config (tensor sizes, batch
  counts); confirm with the human.
- **§11 Known caveats and prior art.** Open question — you cannot infer.

§10 (HP lock) stays blank at this point; you fill it at the end of Prep Phase 2.

### 3.2 Workload-branch preparation

The baseline runs on a dedicated workload-repo branch, not on upstream `main`,
so every operator starts from the same pinned commit. Create it after the
interview (so you know the workload slug + iteration) and before the sanity
baseline:

```bash
# Shell cwd is the workload repo root (e.g. milabench).
git checkout <upstream-base-branch>     # usually main
git pull
git checkout -b hackathon-<workload>-<iteration>

# Ensure brdg-hackathon/ is gitignored on this branch so the two repo histories
# stay independent. The sed normalises the trailing newline first — `echo >>`
# would otherwise merge with an unterminated last line.
sed -i -e '$a\' .gitignore
echo 'brdg-hackathon/' >> .gitignore

git add .gitignore
git commit -m "hackathon <workload> iteration <iteration>: ignore brdg-hackathon/"
```

If the human requests any other prep-time fixups (e.g. a known upstream bug
that must be patched before baseline), apply them on this branch with their
explicit approval before running the baseline. Record the prepared-branch head
commit in `WORKLOAD_CARD §1` (and, after Prep Phase 2, in `§10.5`) after the
final prep commit.

Do **not** push yet — push both branches together at the end of §5.

### 3.3 Sanity baseline (at default HPs)

Before committing hours to HP search, confirm the `§6` command runs end-to-end
at defaults and yields the metrics the card promises:

1. Run the `WORKLOAD_CARD §6` baseline command end-to-end once, on the
   `hackathon-<workload>-<iteration>` branch, with default HP values.
2. Capture stdout + relevant logs to
   `sessions/<workload>/<iteration>/prep/baseline_capture.txt`.
3. Apply the §2 extraction recipe to the capture — must return a numeric
   value. If not, fix `§2` and re-run; do not paper over the failure.
4. Apply the §3 extraction — must return a numeric value. Same rule.
5. Record the sanity baseline in `prep/prep_results.csv` with
   `phase=prep_p1_sanity_baseline, tier=short, candidate=baseline,
   hp_values_json={}` (defaults). One row per run; this is a short run for
   sanity, not the full TTR (that comes in Prep Phase 2). Emit `[BASELINE]` in
   `prep_event_log.md`.

If any of (3), (4), (5) fails, stop and fix — either correct the card's
extraction recipe or surface a workload bug per `RULES §16`. Do not proceed to
Prep Phase 2 with a broken baseline.

### 3.4 Exit criterion

- `WORKLOAD_CARD §0–§9` and §11 filled (not §10 yet).
- Prepared workload-repo branch `hackathon-<workload>-<iteration>` exists with
  the `.gitignore` commit (and any approved prep-time fixups).
- `prep/baseline_capture.txt` contains a successful end-to-end run and both
  extraction recipes return numeric values.
- `prep_results.csv` has a `phase=prep_p1_sanity_baseline` row.
- Emit `[PREP-EXIT 1]` per `RULES §18.3`.

---

## 4) Prep Phase 2 — HP search & lock

Engineering-knob HPs (batch size, num_envs, rollout length, dataloader workers,
compile flags, log frequency, etc.) materially affect the primary metric.
Optimizing before these are settled conflates HP wins with engineering wins.
You settle them here and lock the winner in `WORKLOAD_CARD §10` so every
session-agent starts from the same config.

Two-tier discipline (`RULES §8`) applies: the throughput proxy ranks
candidates, but TTR gates the lock. An HP set that wins on the proxy but does
not reduce TTR is not a real win.

### 4.1 Short-run baseline (Tier 1 reference)

Declare the short-run protocol in `prep_event_log.md` — duration / observation
count / warmup — per `RULES §8` (default: ≥2 min wall-clock AND ≥60
primary-metric observations).

Measure a short-run baseline at default HPs. Record N short runs with
`phase=prep_p2_short_baseline, tier=short, candidate=baseline,
hp_values_json={}` in `prep_results.csv`. Compute median and CV; log a
`[NOISE]` entry. This is the Tier-1 baseline the sweep will rank candidates
against, and its median / CV get pinned in `WORKLOAD_CARD §10.4` at the end of
this phase.

### 4.2 Default-HP TTR baseline (Tier 2 reference for the backtrack gate)

Run ≥3 **full-length** runs at default HPs with the quality metric tracked
**over time** (not only at end-of-run — TTR requires the trajectory). Record
with `phase=prep_p2_default_ttr, tier=full, candidate=baseline,
hp_values_json={}` in `prep_results.csv`, sharing one `experiment_id`. Compute
and log a `[NOISE]` entry with the default-HP TTR CV per `RULES §6` — this CV
drives N for every candidate TTR validation in §4.5.

Then declare the target quality level that defines TTR. Pick one and record
the choice and numerical value in `prep_event_log.md`:
- **Option A** — target = mean end-of-run quality across the default-HP runs
  above. Candidate-quality gating later applies `WORKLOAD_CARD §4` tolerance to
  this target; the tolerance is not reused to widen the target itself.
- **Option B** — target = a pre-declared quality threshold from prior art,
  captured in `§11` or cited from an external source.

Record the default-HP TTR (median, range, CV) against this target. These are
the comparison reference for §4.5's backtrack gate.

### 4.3 Candidate enumeration

Enumerate HP sets that plausibly affect the primary metric. Separate them:

- **Engineering knobs** — HPs whose value does not change what the algorithm
  *is* (batch size, num_envs, rollout length, dataloader workers, log
  frequency, compile flags, etc.). These are candidates for tuning.
- **Semantic / coupled HPs** — HPs that change algorithm dynamics or are
  coupled to others (learning rate, exploration schedule, target-sync
  frequency, replay buffer size, etc.). Kept at default unless the human
  explicitly approves tuning them. See `REFERENCE §2` for the couplings and
  schedule effects this builds on.

Sweep HPs as **full configurations**, not one knob at a time. Each candidate
is a complete set of engineering-knob values moved together; semantic HPs stay
at default.

Declare the shortlist cap `k_max` up front in `prep_event_log.md` (e.g.
"≤3 candidate HP sets, plus the default fallback"). A small shortlist is
intentional: use `REFERENCE §2` HP-interaction knowledge to propose a few
well-reasoned sets rather than blanket-searching the space.

If enumeration surfaces strong coupling that is hard to reason about cleanly,
raise it with the human preparer before sweeping rather than silently
expanding scope.

### 4.4 Proxy sweep (Tier 1)

Sweep the candidate HP sets on short runs.

- Each candidate is measured with N short runs, N chosen per `RULES §6` from
  the short-run baseline CV (§4.1) and matched against the baseline's N — a
  single short run per candidate is not sufficient and does not defeat Tier-1
  noise.
- Record each run in `prep_results.csv` using `SCHEMA §2`:
  `phase=prep_p2_sweep, tier=short, candidate=hp_sweep_<label>,
  baseline_ref=<§4.1 experiment_id>, hp_values_json=<...>`.
- Rank candidates by the proxy metric (median across their N runs),
  discarding any that regress the quality metric outside `WORKLOAD_CARD §4`
  tolerance on short runs.
- Keep the top ≤ `k_max` that pass.

### 4.5 TTR validation with backtrack (Tier 2)

Take the ranked candidates in order and validate each on full-length TTR until
one passes, or the shortlist is exhausted:

1. Run N full-length runs at the candidate HP set, with N chosen per
   `RULES §6` using the default-HP TTR CV from §4.2. Record under a single
   `experiment_id` with
   `phase=prep_p2_validation, tier=full, candidate=hp_candidate_<label>,
   baseline_ref=<§4.2 experiment_id>, hp_values_json=<...>`.
2. Apply the `RULES §7` min-win gate (TTR Δ_min, confidence interval excludes
   zero) comparing candidate TTR against the default-HP TTR baseline from
   §4.2.
3. Apply the `RULES §11` quality gate (`quality_verdict=PASS`, or FAIL /
   INCONCLUSIVE → reject).
4. If both gates pass, **lock** this candidate's HP set. Stop.
5. Otherwise, drop to the next candidate and repeat.

If no candidate passes, lock **default HPs**; the `§4.2` default-HP TTR runs
become the locked-HP Tier-2 baseline. Defaults can already be optimal for a
given workload; the fallback path is a valid outcome, not a failure.

### 4.6 Fill `WORKLOAD_CARD §10`

With the winner chosen (a candidate from §4.5 or the default fallback), fill
`WORKLOAD_CARD §10` precisely:

- **§10.1** Locked HP configuration. Set `Winner candidate label` and write
  the winning `hp_values_json` on a single JSON line. This value will be
  copied verbatim into every `phase=phase_3_*` row's `hp_values_json` column
  session-side (`SCHEMA §1`).
- **§10.2** Target quality — whichever Option (A / B) you declared in §4.2,
  with the numeric value.
- **§10.3** Tier-2 baseline — the winning experiment's TTR median / range /
  CV / N and its `experiment_id` (a `prep_p2_validation` row, or the
  `prep_p2_default_ttr` row if defaults won).
- **§10.4** Tier-1 baseline — §4.1's short-run median / CV / N and the
  protocol used.
- **§10.5** Prep-branch head commit — same short-SHA as `§1` (the commit the
  Tier-2 runs were taken at).

### 4.7 Exit criterion

- Short-run baseline and default-HP TTR baseline recorded in
  `prep_results.csv` and `prep_event_log.md` (with `[NOISE]` entries).
- Target quality declared in `prep_event_log.md`.
- Proxy shortlist with declared `k_max` recorded in `prep_event_log.md`.
- TTR-validation attempts recorded in `prep_results.csv`; rejected candidates
  carry `win_status=EXPERIMENT` with the quality / magnitude reason in
  `notes`.
- Winner locked (either a candidate or the default fallback).
- `WORKLOAD_CARD §10` filled.
- Emit `[PREP-EXIT 2]` per `RULES §18.3` — body pins locked HPs, default-HP
  TTR, locked-HP TTR, short-run baseline, target quality.

---

## 5) Prep Phase 3 — Publish

### 5.1 Human review

Show the filled card (all of §0–§11) to the human. They verify via
`workload-template/README.md §4`. Wait for **explicit approval** ("go",
"approved", "commit") — silent non-objection is not approval.

### 5.2 Copy the session-start prompt

```bash
cp workload-template/SESSION_START_PROMPT.md \
   sessions/<workload>/<iteration>/SESSION_START_PROMPT.md
# in the copy, replace every `<workload>` with the actual workload slug and
# every `<iteration>` with the actual iteration id. Leave `<agent-name>` as
# a placeholder — the operator fills it at session start.
```

### 5.3 Commit and push

On approval, commit the brdg-hackathon artifacts and push both branches:

```bash
# brdg-hackathon: filled card + SESSION_START_PROMPT + prep/ tree
cd brdg-hackathon
git checkout main
git pull
git checkout -b <workload>-<iteration>
git add sessions/<workload>/<iteration>/
git status   # confirm WORKLOAD_CARD.md, SESSION_START_PROMPT.md, and prep/ are staged
git commit -m "Prepare <workload> iteration <iteration>"
git push -u origin <workload>-<iteration>

# workload repo: prep branch (from the workload repo root, one level up)
cd ..
git push -u origin hackathon-<workload>-<iteration>
```

### 5.4 Exit criterion

- Both branches pushed.
- Emit `[PREP-CLOSE]` in `prep_event_log.md` with the pushed branch names
  (body shape: `RULES §18.3`). Also emit `[PREP-EXIT 3]` just before
  `[PREP-CLOSE]`.
- Report both pushed branch names to the human and point them at the root
  `README.md` for the operator workflow.

---

## 6) Stop-and-ask rules

- **Never pick §2 primary metric unilaterally.** Propose and confirm. An
  unverified extraction recipe is the most common cause of a rejected
  session.
- **Never pick §4 tolerance unilaterally.** It is the gating threshold for
  every downstream win; domain judgment dominates.
- **Never pick §10.2 target quality unilaterally.** Option A (default-HP
  mean end-of-run) is the default; Option B requires a concrete prior-art
  threshold.
- **Never tune a semantic / coupled HP without explicit approval.** `REFERENCE §2`
  lists the common couplings. If you cannot cleanly decouple, ask.
- **Never commit without explicit approval.** Approval is an affirmative
  signal, not the absence of an objection.
- **If pipeline discovery fails** (name not in `standard.yaml`, code path
  missing), stop and ask. Do not invent a pipeline.
- **If the sanity baseline fails** (command errors, extraction non-numeric),
  stop and ask. Do not proceed to Prep Phase 2 with a half-working card.
- **If Prep Phase 2's TTR validation surfaces a bug**, pause and follow
  `RULES §16`. Restart §4.2 after the fix — do not carry a prep measurement
  across a bug boundary.
- **Never force-push to the workload repo, and never commit to its default
  branch.** Prep-time changes land on `hackathon-<workload>-<iteration>`
  only. If the upstream prep branch name already exists (re-preparing the
  same iteration), confirm with the human before deleting or overwriting it.

---

## 7) Two rules to hold even if you read nothing else

- **Propose, confirm, record.** You interview the human; you do not guess on
  their behalf. Every judgment call in the card is theirs. That includes §2
  primary metric, §4 tolerance, §10.1 locked winner, §10.2 target quality.
- **You write only in `sessions/<workload>/<iteration>/`.** The blank template
  at `workload-template/WORKLOAD_CARD.md` and everything else under
  `workload-template/` and `playbook/` are read-only from your perspective.

---

## Next

Ask the human: "Which milabench pipeline are we preparing?"
