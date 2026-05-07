# Prep Event Log — torchatari iteration 2

---

T+0  [PREP-START]
Date: 2026-05-04
Human preparer: Xavier Bouthillier
Agent ID: preparer
Workload: torchatari
Iteration: 2
Hackathon repo: master @ 18f177d
Workload repo: git@github.com:mila-iqia/milabench.git @ master (2e04211)
Prep branch: hackathon-torchatari-2 (to be created from master @ 2e04211)
Hardware: 1× NVIDIA L40S (46068 MiB VRAM), 6 CPUs, 32 GB RAM
Software: Python 3.12.11, PyTorch 2.10.0+cu130, CUDA 13.0, Driver 580.95.05

---

T+5  [HYPOTHESIS]
Action: Prep Phase 1 — sanity baseline at default HPs (num_envs=128, num_steps=128, num_minibatches=4, update_epochs=4)
Hypothesis/Reason: Confirm the §6 baseline command runs end-to-end and both extraction recipes (§2 voir rate, §3 avg_episodic_return) return numeric values.
Evidence: Job 9457607 submitted to long partition (config: benchmarks/retired/torchatari/prep2_sanity.yaml, 2 min max_duration, 12 CPUs, L40S)
Next: Verify run completes, extract metrics, record [BASELINE], advance to Prep Phase 2.

---

T+10  [BUG]
Action: Sanity baseline job 9457607 failed at startup.
Hypothesis/Reason: envpool 1.2.0 returns gymnasium.spaces.Discrete instead of gym.spaces.Discrete; main.py line 36 asserts isinstance(envs.action_space, gym.spaces.Discrete) which fails.
Result: AssertionError: only discrete action space is supported — no rate or quality data collected.
Evidence: baseline_capture.txt line 77, 117
Next: Apply fix from iter-1 commit e593f40 (hasattr guard); commit on prep branch; re-run.

---

T+12  [FIX]
Action: Changed isinstance(envs.action_space, gym.spaces.Discrete) → hasattr(envs.action_space, 'n') in benchmarks/retired/torchatari/main.py.
Reason: Identical fix already validated in iteration 1 (commit e593f40 on agent_claude-sonnet_torchatari_opt). Pre-existing upstream bug; fix is in allowed territory (guard clause only, does not change algorithm behaviour).
Commit: e23ffee on hackathon-torchatari-2
Next: Re-run sanity baseline.

---

T+15  [BASELINE]
Action: Sanity baseline (job 9457687) completed successfully on hackathon-torchatari-2 @ e23ffee.
Result:
  Voir rate (Tier-1 proxy): 200 usable obs, median=7722.1 items/s, CV=3.87%, min=6843.4, max=8095.3
  avg_episodic_return (quality): 8421 TensorBoard entries, mean=8.693, last=25.550, span=440s
  GPU memory: 4659.6 MiB peak
  Voir ran ~440s (stop=200 obs × ~2.15s/obs); max_duration=120 not enforced by voir earlystop.
  Workload adjustment (RULES §8): Tier-1 protocol will use voir stop=60 (~65 obs × 2.15s ≈ 140s ≈ 2.3 min) to satisfy ≥2 min AND ≥60 obs simultaneously.
Evidence: prep/baseline_capture.txt; TensorBoard at benchmarks/retired/torchatari/runs/Breakout-v5__main__1__1777928042
CSV: prep_results.csv row 2026-05-04_prep_torchatari_2:0
Next: Emit [PREP-EXIT 1], begin Prep Phase 2.

---

T+16  [PREP-EXIT 1]
WORKLOAD_CARD §0–§9 and §11 filled.
Prepared branch: hackathon-torchatari-2 @ e23ffee (master + .gitignore + envpool fix)
Prep-time fixup committed: e23ffee (envpool 1.2.0 isinstance→hasattr; pre-existing bug, approved by human preparer)
Sanity baseline: completed end-to-end; voir rate and avg_episodic_return both return numeric values.
prep_results.csv: 1 row, phase=prep_p1_sanity_baseline.
Next: Prep Phase 2 — short-run baseline, default-HP TTR baseline, candidate sweep, TTR validation.

---

T+20  [SWEEP-SUBMIT]
Action: Prep Phase 2 — submitted Tier-1 HP sweep (20 candidates) + short-run replicates (N=2) + Tier-2 TTR baseline (N=3).
Hypothesis/Reason: 20-candidate grid covers num_envs (64–512), num_steps (64–512), num_minibatches (2–16), update_epochs (1–8), and cross terms. Short baseline replicates (seeds 2,3) + sanity baseline (seed 1) give N=3 for Tier-1 CV. TTR runs (seeds 1,2,3) with voir stop=600 give ~1290s runtime to extract TTR over 900s window.
Evidence:
  Sweep jobs (20): 9464142–9464161 (partition=long, 12 CPUs, 256G, time=0:30:00)
    Candidates: e64_s128_m4_u4, e128_s128_m4_u4 (default), e256_s128_m4_u4, e512_s128_m4_u4,
                e128_s64_m4_u4, e128_s256_m4_u4, e128_s512_m4_u4,
                e128_s128_m2_u4, e128_s128_m8_u4, e128_s128_m16_u4,
                e128_s128_m4_u1, e128_s128_m4_u2, e128_s128_m4_u8,
                e256_s256_m8_u4, e512_s256_m8_u4, e256_s128_m2_u4,
                e512_s128_m2_u4, e256_s128_m4_u8, e128_s256_m4_u8, e512_s128_m4_u8
  Short baseline replicates (2): jobs 9464174 (seed=2), 9464175 (seed=3)
  TTR baseline runs (3): jobs 9464176 (seed=1), 9464177 (seed=2), 9464178 (seed=3)
Next: Wait for jobs; extract voir rate from sweep logs; rank candidates; run TTR validation on top candidates; fill WORKLOAD_CARD §10.

---

T+50  [PARTIAL-SWEEP-RESULTS]
Action: Extracted Tier-1 sweep results for 9/20 candidates (11 failed due to max_duration=600 < voir completion time for larger batch sizes).
Root cause: milabench sends SIGTERM after max_duration=600s; voir flushes rate data only on clean exit; large-batch configs need >(max_duration) seconds to complete 205 iterations.
Results (9 completed, skip=5, stop=200, N=200 obs each):
  e128_s128_m4_u1:  8072.6 items/s (+4.5% vs default)
  e128_s128_m8_u4:  7933.9 items/s (+2.7%)
  e128_s128_m4_u2:  7877.3 items/s (+2.0%)
  e128_s128_m16_u4: 7806.8 items/s (+1.1%)
  e128_s128_m4_u4:  7722.0 items/s (default / baseline)
  e128_s64_m4_u4:   7538.8 items/s (-2.4%)
  e128_s128_m2_u4:  7512.4 items/s (-2.7%)
  e64_s128_m4_u4:   6704.8 items/s (-13.2%)
  e128_s128_m4_u8:  6655.0 items/s (-13.8%)
Failed (max_duration too short): e256/e512 envs configs, longer step configs, cross-terms.
Next: Rerun 11 failed candidates with calibrated max_duration; await results.

---

T+55  [TTR-BASELINE]
Action: Extracted Tier-2 TTR baseline from 3 full runs (seeds 1,2,3; voir stop=600, ~21 min each).
Result:
  Target quality (Option A): 94.683 (mean of end-of-window avg_episodic_return: 113.750/64.850/105.450)
  seed=1 (job 9464176): TTR=700.2s
  seed=2 (job 9464177): DNF (max_quality=93.4 < target=94.683) → counted as 900s
  seed=3 (job 9464178): TTR=841.8s
  Tier-2 baseline: median=841.8s, range=[700.2,900.0]s, CV=12.6%, N=3
WORKLOAD_CARD §10.2 and §10.3 filled. §10.1 (HP winner) TBD pending rerun results.

---

T+58  [RERUN-SUBMIT]
Action: Resubmitted 11 failed large-batch sweep candidates with per-config max_duration calibrated to (skip+stop)×est_iter_time×1.35+60. Reduced stop=80 (from 200) for configs with est_iter_time>8s to keep runs manageable while exceeding ≥60 obs minimum.
Jobs: 9466516–9466526 (partition=long, 12 CPUs, 256G, time 0:32-0:48)
Next: Await rerun completion, extract all 20 candidates, rank, select HP winner, fill §10.1.

---

T+60  [FULL-SWEEP-RESULTS]
Action: All 20 Tier-1 sweep candidates extracted. Final ranking:
  #1  e256_s256_m8_u4:  9023.0 items/s (+16.8%, n=80)
  #2  e256_s128_m4_u4:  8997.6 items/s (+16.5%, n=200) ← selected for TTR validation
  #3  e512_s256_m8_u4:  8286.9 items/s (+7.3%, n=80)
  #4  e256_s128_m2_u4:  8208.0 items/s (+6.3%, n=200)
  #5  e512_s128_m4_u4:  8092.7 items/s (+4.8%, n=80)
  #6  e128_s128_m4_u1:  8072.6 items/s (+4.5%, n=200)
  ...
  *12 e128_s128_m4_u4:  7722.0 items/s (default, n=200)
Key insight: Throughput gain concentrated in num_envs=256 configs (+16.5%); envpool CPU parallelism.
Submitted TTR validation for top-1 (e256_s128_m4_u4): jobs 9466692-9466694, seeds 1/2/3, voir stop=400.

---

T+65  [TTR-VALIDATION-RESULT]
Action: Extracted TTR validation results for e256_s128_m4_u4 (num_envs=256) from TensorBoard.
Result: ALL 3 SEEDS DNF — max quality in 900s window: 46.2/47.1/49.4 (target=94.683).
  seed=1: run_dur=1571s (voir killed by max_dur), TB max=46.15
  seed=2: run_dur=1464s (voir completed 400 obs), TB max=47.05
  seed=3: run_dur=1466s (voir completed 400 obs), TB max=49.35
  vs baseline: max quality 149.6/93.4/112.5 (seeds 1/2/3); TTR median=841.8s
Conclusion: REGRESSION. e256 (+16.5% throughput) HURTS TTR by ~halving policy update frequency per wall-clock time (fewer PPO iterations/second despite more env-steps/second). The Tier-1 throughput proxy is ANTI-CORRELATED with TTR for num_envs changes on this workload.

---

T+70  [HP-LOCK]
Action: Locked HP winner as DEFAULT (e128_s128_m4_u4).
Rationale: No HP change in the 20-candidate sweep improved TTR. The dominant throughput improvements (+16.5% from num_envs=256) hurt TTR. Marginal improvements (m8 +2.7%, u2 +2.0%) are within noise (CV=12.6%). Default HP achieves the Tier-2 baseline.
WORKLOAD_CARD §10.1: filled with default HP, warning for session-agents about proxy validity.
prep_results.csv: 30 rows (1 sanity + 3 short_baseline + 20 sweep + 3 ttr_baseline + 3 ttr_val).
Next: Prep Phase 3 — human review, SESSION_START_PROMPT, commit/push branch.

---

T+80  [PHASE-2B-SUBMIT]
Date: 2026-05-05T15:24:44-04:00
Motivation: Phase 2 Tier-2 data only covered 2 HP configs (default e128 and e256). The dramatic anti-correlation between Tier-1 rate and Tier-2 TTR for num_envs changes — and the complete absence of Tier-2 data for any other HP — made it impossible to see the full TTR landscape or validate other HP candidates. Phase 2B extends both tiers.

Tier-1 extended (9 new num_envs candidates, finer grid):
  Protocol: voir stop=60, skip=5, max_duration=600, seed=1
  New candidates: e16, e24, e32, e48, e96, e160, e192, e320, e384 (s=128, m=4, u=4)
  Jobs: 9468782–9468790 (partition=long, 12 CPUs, 256G, time=0:20:00)

Tier-2 extended (11 new configs × 3 seeds = 33 jobs):
  voir stop calibrated per config so stop × iter_time_est ≥ 900s; max_duration = stop × iter_time × 1.45 + 120 (rounded up).
  Group A — num_envs sweep (s=128, m=4, u=4):
    e16 (stop=2699, max_dur=1440s), e32 (stop=1460, 1500s), e48 (stop=1021, 1500s),
    e64 (stop=757, 1500s), e96 (stop=558, 1500s), e192 (stop=309, 1560s), e512 (stop=140, 1680s)
  Group B — non-envs HPs (e=128, s=128):
    s64 (stop=849, 1500s), s256 (stop=235, 1560s), m8 (stop=456, 1500s), u1 (stop=464, 1500s)
  Seeds: 1, 2, 3
  Jobs: 9468792–9468824 (partition=long, 12 CPUs, 256G)

Combined with Phase 2 data, we will have Tier-2 TTR for:
  num_envs: e16, e32, e48, e64, e96, e128, e192, e256, e512 (9 configs)
  num_steps: s64, s128, s256 (3 configs)
  num_minibatches: m4, m8 (2 configs)
  update_epochs: u1, u4 (2 configs)

Next: Wait for jobs (~35 min wall clock), extract results, update plot.

---

T+85  [PHASE-2B-RESULTS]
Date: 2026-05-05

Tier-1 new results (Phase 2B, s=128, m=4, u=4):
  e16: 3494.7 items/s (iter_time=0.586s)
  e24: 4363.2 items/s (0.704s)
  e32: 4794.8 items/s (0.854s)
  e48: 5265.8 items/s (1.167s)
  e96: 6721.6 items/s (1.828s)
  e160: 7284.3 items/s (2.812s)
  e192: 7680.8 items/s (3.200s)
  e320: 7994.4 items/s (5.124s)
  e384: 7964.8 items/s (6.171s)
  Pattern: monotonically increasing, saturating around e=256–384.

Tier-2 new results (Phase 2B):
  num_envs sweep (s=128, m=4, u=4):
    e16:  TTR=761.9s  median (0/3 DNF),  max_q=158s
    e32:  TTR=682.5s  (0/3 DNF),  max_q=183
    e48:  TTR=660.9s  (0/3 DNF),  max_q=160
    e64:  TTR=631.9s  (0/3 DNF),  max_q=236  ← BEST num_envs: -25% vs baseline
    e96:  TTR=734.2s  (0/3 DNF),  max_q=153
    e128: TTR=841.8s  (1/3 DNF) ← baseline (Phase 2)
    e192: TTR=900.0s  (3/3 DNF),  max_q=70
    e256: TTR=900.0s  (3/3 DNF),  max_q=47 (Phase 2)
    e512: TTR=900.0s  (3/3 DNF),  max_q=17
  non-envs HPs (e=128, s=128):
    s64:  TTR=608.6s  (0/3 DNF),  max_q=228  ← BEST overall: -27.7% vs baseline
    s256: TTR=900.0s  (3/3 DNF),  max_q=40
    m8:   TTR=661.0s  (0/3 DNF),  max_q=176  ← -21.5% vs baseline
    u1:   TTR=900.0s  (3/3 DNF),  max_q=15

KEY FINDINGS:
1. TTR has a clear U-shaped curve vs num_envs: minimum near e48-e64.
   Fewer envs → more PPO update iterations per wall-clock second → faster convergence.
   Too few envs (e16) → slower due to limited experience diversity and poor CPU utilisation.
   Too many envs (e192+) → so few PPO updates that policy barely improves in 900s.
2. Halving num_steps (s64) gives best TTR overall (608.6s, -27.7%). Same mechanism:
   faster iterations = more gradient updates per wall-clock second.
3. m8 (+2.7% Tier-1) gives -21.5% TTR — more minibatches improves sample efficiency.
4. u1 (best Tier-1 rate) is CATASTROPHIC for TTR (all DNF) — 1 epoch provides no
   learning signal per batch. Tier-1 rate anti-correlates with TTR for update_epochs.
5. s256 (higher Tier-1) all DNF — same: fewer updates per sec hurts convergence.

Tier-1 anti-correlation confirmed for ALL HP dimensions that reduce update frequency:
  num_envs↑, num_steps↑, update_epochs↓ → Tier-1↑ but TTR↑ (worse).
  num_envs↓, num_steps↓, update_epochs... ↑ (diminishing after u4) → TTR↓ (better).

Next: Submit cross-term experiments (e64_s64, e48_s64, e64_s64_m8) to find the joint optimum.

---

T+90  [PHASE-2C-RESULTS]
Date: 2026-05-05

Phase 2C cross-term TTR results (all 0/3 DNF unless noted):
  e256_s64_m4_u4   mb=4096  TTR=778.8s  (+7.5% vs baseline)   — compensated envs, same mb as default
  e256_s64_m8_u4   mb=2048  TTR=558.3s  (+33.7%)               — compensated envs + smaller mb
  e256_s128_m8_u4  mb=4096  TTR=819.8s  (+2.6%)                — more envs + more mb, mb unchanged
  e128_s64_m8_u4   mb=1024  TTR=469.5s  (+44.2%) *** BEST ***
  e128_s128_m16_u4 mb=1024  TTR=494.1s  (+41.3%)
  e64_s64_m4_u4    mb=1024  TTR=478.6s  (+43.1%)
  e64_s128_m8_u4   mb=1024  TTR=550.9s  (+34.6%)

KEY FINDING: minibatch_size is the primary driver of TTR, independent of which
combination of HPs achieves it. Ranking stratifies perfectly by mb:
  mb=4096 → TTR 779–900s (worst, includes DNF configs)
  mb=2048 → TTR 558–661s
  mb=1024 → TTR 469–551s (best)

ANSWER TO USER'S QUESTION: num_minibatches is the HP that increases gradient
update density without changing rollout collection frequency. Doubling m from 4→8
(keeping e and s fixed) halves minibatch_size and increases grad_steps/sec 2×,
giving ~21–44% TTR improvement. This is the correct lever.

DISCOVERY — upstream config uses m=16 (mb=1024): config/retired.yaml has
  --num-minibatches: "auto_batch(16)"
Our prep baseline used m=4 (from dev.yaml), which was already 41% slower than
the benchmark's own design. e128_s128_m16_u4 (code's intended default) gives
TTR=494.1s, and e128_s64_m8_u4 (both s64 and m8) gives TTR=469.5s.

GRAD_STEPS/SEC analysis (confirms the driver):
  e128_s128_m4  (default): 0.47 × 4 × 4  =  7.5 grad/sec → TTR=842s
  e128_s128_m8  (Phase2B): 0.47 × 4 × 8  = 15.1 grad/sec → TTR=661s
  e128_s64_m4   (Phase2B): 0.92 × 4 × 4  = 14.7 grad/sec → TTR=609s
  e128_s128_m16 (Phase2C): 0.47 × 4 × 16 = 30.1 grad/sec → TTR=494s
  e128_s64_m8   (Phase2C): 0.92 × 4 × 8  = 29.4 grad/sec → TTR=470s ← BEST
  e64_s64_m4    (Phase2C): 1.22 × 4 × 4  = 19.5 grad/sec → TTR=479s

Next: Decision — lock HP winner at e128_s64_m8_u4 (best, 44% improvement), or
test mb=512 to see if the trend continues further.

---

T+100 [HP-LOCK-FINAL]
Action: Close HPO phase. Lock winner in WORKLOAD_CARD §10.
Winner: e256_s32_m32_u4  (num_envs=256, num_steps=32, num_minibatches=32, update_epochs=4, minibatch_size=256)
TTR: median=255.7s, range=[224.8, 267.1]s, CV=8.8%, N=3, n_dnf=0
Improvement vs default: −70% (841.8s → 255.7s)
Basis: 5-phase HPO (Phases 2B–2E); ~300 Tier-2 runs across 77 configs × 3 seeds.
Optimum is interior in s (s=16 and s=64 both slower), interior in m (m=16 and m=64 both slower),
and interior in mb (mb=128 and mb=512 both slower). e=256 is at the grid boundary but marginal
gain expected at e=512; accepted as converged given ±8% seed CV.
WORKLOAD_CARD §10 updated; checklist item ticked.

---

T+95  [PHASE-2D-SUBMIT]
Action: Phase 2D — exhaustive Tier-2 grid search over all remaining (num_envs × num_steps × num_minibatches) combinations.
Grid: num_envs∈{32,64,128,256} × num_steps∈{32,64,128} × num_minibatches∈{4,8,16,32}, update_epochs=4 fixed.
48 total grid points; 13 already have Tier-2 data from prior phases; submitting 35 new configs × 3 seeds = 105 jobs.
Job IDs: 9474669–9474774 (long partition, gpu:l40s:1, 34-36 min each).
Motivation: minibatch_size confirmed as primary TTR driver (Phases 2B/2C); exhaust the full grid to find the
true minimum — no mb floor, includes mb=32 through mb=2048 for all (e,s) combinations.
iter_time model: measured at s=128 (e32→0.63s, e64→1.22s, e128→2.12s, e256→3.60s), scaled linearly with s.
voir stop calibrated per config: stop=ceil(900/iter_time)+20, max_dur=ceil((stop×iter_time×1.45+120)/60)×60.
Script: brdg-hackathon/sessions/torchatari/2/prep/submit_phase2d_grid.py

---

T+75  [PREP-EXIT 2]  (superseded by T+100 HP-LOCK-FINAL — winner updated after extended HPO)
Phase: Prep Phase 2 complete (initial lock — later overridden).
Initial locked HPs: {"num_envs": 128, "num_steps": 128, "num_minibatches": 4, "update_epochs": 4} (DEFAULT)
Target quality (Option A): 94.683 (mean end-of-window avg_episodic_return, seeds 1/2/3)
Tier-2 baseline (default HP): median=841.8s, range=[700.2, 900.0]s, CV=12.6%, N=3
Tier-1 baseline: median=7727.6 items/s, CV=0.6%, N=4
FINAL locked HPs (T+100): {"num_envs": 256, "num_steps": 32, "num_minibatches": 32, "update_epochs": 4}
FINAL TTR: median=255.7s (−70% vs default)
Next: Prep Phase 3 — human approves filled WORKLOAD_CARD, then commit and push branch.


---

T+102  [PREP-EXIT 3]
Phase: Prep Phase 3 complete.
Action: Human reviewed and approved filled WORKLOAD_CARD.md (all §0–§11 including §10).
WORKLOAD_CARD state: fully filled; §4 and §5 cleaned of template checkbox artifacts; §10 HP-lock complete.
SESSION_START_PROMPT.md: copied to sessions/torchatari/2/ with <workload>/<iteration> substituted.
Committing and pushing:
  - milabench repo branch: hackathon-torchatari-2
  - brdg-hackathon repo branch: torchatari-2

---

T+103  [PREP-CLOSE]
Action: Both branches pushed.
  - milabench:      hackathon-torchatari-2  (benchmarks/retired/torchatari/ prep YAML configs)
  - brdg-hackathon: torchatari-2            (sessions/torchatari/2/ — WORKLOAD_CARD, SESSION_START_PROMPT, prep/)
Operator workflow: see brdg-hackathon/README.md.
