# FINAL SUMMARY — Agent <ID>

> Lives at `sessions/<workload>/<iteration>/<agent-name>/artifacts/FINAL_SUMMARY.md`.
> Workload-specific definitions (primary metric, quality metric, tolerance, benchmark
> window) come from `../../WORKLOAD_CARD.md` (the filled card one level up from your
> session root). Copy their concrete values into §0 below.

## 0) Metadata
- Date:
- Agent:
- Human operator:
- Workload: `<workload>` / iteration: `<iteration>`
- **Hackathon repo**: `<brdg-hackathon branch>` @ `<commit-hash>` (as recorded in `[SESSION-START]`)
- Workload repo + starting commit (= prepared-branch head from `WORKLOAD_CARD §1`):
- Branch (in workload repo): `hackathon-<workload>-<iteration>-<agent-name>` (branched off `hackathon-<workload>-<iteration>`)
- **Final commit hash** (workload-repo branch HEAD at session close):
- Hardware: GPU / CPU / RAM
- Software: driver / CUDA / framework versions / Python / other
- Baseline command:
- Benchmark window: (fixed steps/iterations or fixed time)
- Primary metric (name + definition):
- Quality metric:
- Quality tolerance used:

---

## 1) Executive result (TL;DR)
**Baseline primary metric (median):** ___
**Best primary metric (median):** ___ (**+___%**)
**Quality status:** PASS / FAIL / INCONCLUSIVE
**Quality metric (baseline vs best):** ___ → ___ (Δ ___ / ___%)
**Primary tradeoffs / notes:** (e.g. +GPU mem, more variance, logging-overhead changes, etc.)

---

## 2) Baseline measurements

### 2.1 Benchmark (warmup discarded; N measured runs)
| Run | primary metric | quality snapshot | peak GPU mem (MiB) | notes |
|-----|---------------:|-----------------:|-------------------:|------|
| 1   |                |                  |                    |      |
| 2   |                |                  |                    |      |
| 3   |                |                  |                    |      |
| ... |                |                  |                    |      |

**Baseline summary:** median ___, min ___, max ___

### 2.2 Baseline profiling evidence
- Tools + commands:
- Top bottlenecks (ranked):
  1)
  2)
  3)
- Key trace filenames in `artifacts/profiles/`:

---

## 3) Changes implemented (what & why)

### 3.1 Final change set (used for best result)
Commits / diffs:
- Commit ___: (1-line summary) — bottleneck addressed:
- Commit ___:
- Config changes (if any):

### 3.2 Evidence-driven rationale
For each major change:
- Problem observed (profile or measurement):
- Hypothesis:
- Change:
- Evidence (benchmark deltas, trace references):

---

## 4) Best result measurements

### 4.1 Benchmark (same protocol)
| Run | primary metric | quality snapshot | peak GPU mem (MiB) | notes |
|-----|---------------:|-----------------:|-------------------:|------|
| 1   |                |                  |                    |      |
| 2   |                |                  |                    |      |
| 3   |                |                  |                    |      |
| ... |                |                  |                    |      |

**Best summary:** median ___, min ___, max ___
**Improvement vs baseline (median):** +___%

### 4.2 Quality / correctness checks
- Check type(s): smoke / quick eval / multi-seed eval / etc.
- Protocol: episodes, horizon, seeds, number of eval runs
- Result: PASS / FAIL / INCONCLUSIVE
- Notes on variance / noise:

---

## 5) Tradeoffs & risks
- GPU memory impact:
- CPU utilization impact:
- Stability / variance impact:
- Any semantic-risk changes? YES / NO
  If YES: describe why quality validity is still acceptable and what additional checks were run.

---

## 6) Timeline & efficiency (for comparison)
- Time to first measurable win (>=X%): T+___ min
- Total experiments run: ___
- Reverts / dead ends: ___
- Blocked time: ___ min (reasons)
- Human interventions:
  - H-STEER: ___
  - H-DEBUG: ___
  - H-ARCH: ___
  - H-OPS: ___

---

## 7) What didn't work (dead ends)
List top 3–5:
1) Attempt:
   - Why tried:
   - Result:
   - Lesson:
2)
3)

---

## 8) Reproduction

### 8.1 Reproduce baseline
```bash
# exact commands
```

### 8.2 Reproduce best result
```bash
# exact commands
```

### 8.3 Artifacts
- Benchmarks: `artifacts/benchmarks/...`
- Profiles: `artifacts/profiles/...`
- Notes: `artifacts/notes/event_log.md`

---

## 9) Next steps (if more time)
- Highest-confidence next optimization:
- One risky / high-reward idea:
- One tooling improvement (profiling / metrics) that would help:
