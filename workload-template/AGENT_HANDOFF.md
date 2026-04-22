# Preparer-agent handoff — start here

You are pairing with a human preparer to set up a new hackathon iteration for a
milabench pipeline. Your job is to draft `WORKLOAD_CARD.md`, run the baseline
end-to-end, and commit — after the human confirms every judgment call.

The pipeline catalogue lives at
[milabench/config/standard.yaml](https://github.com/milabench/milabench/blob/master/config/standard.yaml);
per-pipeline code lives under `benchmarks/<pipeline>/` in the same repo.

---

## Goal (one sentence)

Produce two prepared branches — `hackathon-<workload>-<iteration>` on the
workload repo (with `brdg-hackathon/` committed to `.gitignore` and the baseline
verified end-to-end) and `<workload>-<iteration>` on brdg-hackathon (with a
filled `sessions/<workload>/<iteration>/WORKLOAD_CARD.md` pinning that workload
branch) — ready for operators to run optimisation sessions against.

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
7. Read `brdg-hackathon/playbook/RULES.md §2, §4, §8, §11` and
   `brdg-hackathon/playbook/SCHEMA.md §1` — the contracts the card must
   satisfy (metric definitions, tolerance semantics, two-tier split,
   quality-check rules, the CSV columns every session will write).
8. Begin the interview (§3).

---

## Working model — three locations

- **Shell cwd**: milabench repo root. `config/standard.yaml` and `benchmarks/`
  are at your fingertips; baseline commands run from here. You will also
  **create and push a `hackathon-<workload>-<iteration>` branch on this
  repo** carrying prep-time changes (the `.gitignore` entry below, and any
  fixups the human approves before baseline) — operators start their sessions
  from this branch, not from the upstream default.
- **Hackathon folder**: `brdg-hackathon/` (cloned inside milabench). Contains
  `workload-template/` (this file, the blank card, the human README),
  `playbook/` (the session-agent protocol you read selectively), `sessions/`
  (where you write the filled card).
- **Iteration folder** (you create it):
  `brdg-hackathon/sessions/<workload>/<iteration>/` — the filled card and
  baseline capture live here. Future session-agents read it read-only.

---

## File set

Eagerly loaded (read before acting):
- `workload-template/WORKLOAD_CARD.md` — the template to fill.
- `workload-template/README.md` — the human's verification checklist.
- `playbook/RULES.md` (§2, §4, §8, §11), `playbook/SCHEMA.md §1` — card
  contracts.

Trigger-loaded:
- The pipeline's own code — load during pipeline discovery (step 2–3 above),
  hold through the interview, evict at commit.
- `milabench.readthedocs.io` — load when the human asks about milabench
  semantics you did not learn from the code (e.g. `milabench dev` vs `run`).

Not your doc:
- `playbook/AGENT_HANDOFF.md` and the rest of `playbook/` beyond the sections
  above — that corpus is for the session-running optimisation agent, not you.
- `editor-guide/` — meta; for agents editing the corpus.

---

## Interview protocol

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

Per-section guidance:

- **§0 Session identity.** Workload slug from the pipeline name; iteration
  from step 2 (inferred, human-confirmed); date = today; draft a one-sentence
  summary from the code, ask the human to approve or rewrite.
- **§1 Target workload.** Repo URL = the workload remote; upstream base = the
  branch @ commit you branched from (normally `main @ <current HEAD>`);
  **prepared branch = `hackathon-<workload>-<iteration>`** (you will create and
  push it in §Workload-branch preparation below); prepared-branch head commit
  is filled in **after** that commit lands. Benchmark code path from
  `config/standard.yaml`; entry point from the config; read-only reference
  code = files whose change would alter semantics (dataset loader, eval,
  reward / loss). Ask the human to narrow.
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
- **§6 Entry command(s).** Draft the exact `milabench` / direct-invocation
  command from `config/standard.yaml`; include env vars and working directory.
  Run it end-to-end (§Baseline verification); the command that actually ran
  is what goes in the card.
- **§7, §8 Allowed / disallowed.** Propose a split based on the code:
  disallowed first (eval, dataset / environment internals, reward / loss);
  allowed second (training loop, data pipeline, model forward, config). Must
  be non-overlapping; ask the human to narrow or extend.
- **§9 Hardware.** Infer from the pipeline config (tensor sizes, batch
  counts); confirm with the human.
- **§10 Known caveats and prior art.** Open question — you cannot infer.

---

## Workload-branch preparation (before baseline)

The baseline runs on a dedicated workload-repo branch, not on upstream `main`,
so every operator starts from the same pinned commit. Create it after the
interview (so you know the workload slug + iteration) and before baseline
verification:

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
commit in `WORKLOAD_CARD §1` after the final prep commit.

Do **not** push yet — push both branches together at the end of the
§Mechanical pipeline, after baseline verifies and the human approves.

---

## Baseline verification (before commit)

Before filling §11 and committing, running **on the
`hackathon-<workload>-<iteration>` branch**:

1. Run the §6 baseline command end-to-end in a clean environment.
2. Capture stdout + relevant logs to
   `sessions/<workload>/<iteration>/baseline_capture.txt`.
3. Apply the §2 extraction recipe to the capture. It must return a numeric
   value. If not, fix §2 — do not paper over the failure.
4. Apply the §3 extraction. Same: must return a number.
5. Only then tick §11 boxes.

If any step fails, stop, report to the human, propose a correction. Never
commit a card with a §11 box ticked that was not actually verified — that is
the single biggest cause of a lost session.

---

## Mechanical pipeline

Once the interview is complete, the workload-repo prep branch exists with the
`.gitignore` commit, and baseline verifies:

```bash
# Still in the workload repo root. Record the workload-repo prep branch's
# head commit (you will paste it into WORKLOAD_CARD §1).
git -C . rev-parse --short HEAD

cd brdg-hackathon
git checkout main
git pull
git checkout -b <workload>-<iteration>

mkdir -p sessions/<workload>/<iteration>
cp workload-template/WORKLOAD_CARD.md \
   sessions/<workload>/<iteration>/WORKLOAD_CARD.md
# fill the copy (never the blank template in workload-template/), including
# the prepared-branch head commit captured above
# place baseline_capture.txt alongside WORKLOAD_CARD.md
```

Show the filled card to the human. Wait for **explicit approval** ("go",
"approved", "commit") — silent non-objection is not approval. On approval,
push both branches:

```bash
# 1) brdg-hackathon artifacts
git add sessions/<workload>/<iteration>/
git commit -m "Prepare <workload> iteration <iteration>"
git push -u origin <workload>-<iteration>

# 2) workload-repo prep branch (from the workload repo root, one level up)
cd ..
git push -u origin hackathon-<workload>-<iteration>
```

Report both pushed branch names to the human and point them at root
`README.md` for the operator workflow.

---

## Stop-and-ask rules

- **Never pick §2 primary metric unilaterally.** Propose and confirm. An
  unverified extraction recipe is the most common cause of a rejected
  session.
- **Never pick §4 tolerance unilaterally.** It is the gating threshold for
  every downstream win; domain judgment dominates.
- **Never commit without explicit approval.** Approval is an affirmative
  signal, not the absence of an objection.
- **If pipeline discovery fails** (name not in `standard.yaml`, code path
  missing), stop and ask. Do not invent a pipeline.
- **If baseline verification fails** (command errors, extraction non-numeric),
  stop and ask. Do not commit a half-working card.
- **Never force-push to the workload repo, and never commit to its default
  branch.** Prep-time changes land on `hackathon-<workload>-<iteration>`
  only. If the upstream prep branch name already exists (re-preparing the
  same iteration), confirm with the human before deleting or overwriting it.

---

## Two rules to hold even if you read nothing else

- **Propose, confirm, record.** You interview the human; you do not guess on
  their behalf. Every judgment call in the card is theirs.
- **You write only in `sessions/<workload>/<iteration>/`.** The blank template
  at `workload-template/WORKLOAD_CARD.md` and everything else under
  `workload-template/` and `playbook/` are read-only from your perspective.

---

## Next

Ask the human: "Which milabench pipeline are we preparing?"
