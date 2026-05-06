# FINAL SUMMARY — Agent codex

## 0) Metadata
- Date: 2026-04-22
- Agent: codex
- Human operator: srygaard
- Workload: `torchatari` / iteration: `1`
- Hackathon repo: `torchatari-1-codex` @ `f79414c`
- Workload repo + starting commit: `https://github.com/srygaard/milabench.git` @ `2e04211`
- Branch (workload repo): `master` (session changes tracked in workspace)
- Final commit hash (workload repo HEAD): `2e04211`
- Hardware: 1x NVIDIA L40S, 64 CPU cores, ~503GiB RAM
- Software: Driver 580.95.05, CUDA 13.0, Python 3.12.13 (`milabench/base/venv/torch`)
- Baseline command: milabench run via SBATCH harness (`artifacts/tools/run_phase_job.sh`)
- Benchmark window: fixed wall-clock target 600s; practical observer caps via `voir.stop` (65 short, 250 full)
- Primary metric: `rate` (env-steps/s, median post-warmup)
- Quality metric: final `charts/avg_episodic_return`
- Quality tolerance: PASS if `candidate >= baseline_mean - 2*baseline_std` (Phase-3 baseline)

## 1) Executive result (TL;DR)
- Baseline primary metric (Phase-3 full mean): `3026.77`
- Best primary metric (Phase-4 non-HP codeopt full candidate): `4371.43` (**+44.39%**)
- Quality status: `PASS`
- Quality metric (baseline vs best): `16.30 -> 26.50`
- Tradeoffs: peak GPU memory increased from ~`1275.56` MiB to ~`1521.56` MiB.

## 2) Baseline measurements
- Phase-3 locked HP full baseline runs (`num_envs=16`, `num_minibatches=8`):
  - Run 1: rate `3010.85`, quality `16.30`
  - Run 2: rate `3037.50`, quality `16.30`
  - Run 3: rate `3031.97`, quality `16.30`
- Baseline summary: mean `3026.77`, std `11.48`, CV `0.379%`

## 3) Changes implemented (what & why)
- `benchmarks/retired/torchatari/main.py`
  - envpool-only pipeline
  - robust env `step()` tuple handling (4/5 return compatibility)
  - non-HP code optimization in the hot path:
    - `torch.as_tensor(...)` step-output ingestion
    - cached `b_actions.long()` outside minibatch loop
    - `optimizer.zero_grad(set_to_none=True)`
- `benchmarks/retired/torchatari/requirements.in`
  - removed `stable-baselines3`
- HP progression:
  - Phase-2 lock: `num_envs=16`, `num_minibatches=8`
  - Phase-4 winner (initial): `num_envs=24`, `num_minibatches=12`
  - Phase-4 winner (resumed): `num_envs=32`, `num_minibatches=16`

## 4) Best result measurements
- Full-tier candidate (`num_envs=32`, `num_minibatches=16`, non-HP code optimization enabled):
  - rate `4371.43`
  - quality `26.50`
  - peak GPU mem `1521.56 MiB`
- Improvement vs Phase-3 baseline mean: `+44.39%`
- Improvement vs prior resumed full baseline (`32/16`, pre-codeopt): `+15.82%` (`4371.43` vs `3774.29`)
- Quality check: `PASS` (`26.50 >= 16.30` threshold)

## 5) Tradeoffs & risks
- Memory increase: ~`+246 MiB`
- GPU utilization remained relatively low (~10–13%), suggesting further headroom
- Semantic-risk changes: `NO`

## 6) Timeline & efficiency
- Time to first strong measurable gain: Phase-2 short candidate (~T+103m)
- Initial Phase-4 win captured at ~T+135m; resumed HP win at ~T+222m; non-HP codeopt win at ~T+238m
- Drift boundary handled with re-baselining during resume (`env_2026-04-22T18:52Z`)
- Invalidated/dead-end attempts were logged and preserved in `results.csv`
- Human interventions logged: `H-STEER`, `H-DEBUG`, `H-OPS`

## 7) What didn't work (dead ends)
1. Direct CLI override of `argv.--*` keys in milabench caused parsing/merge failures.
2. Temp config with relative `definition` path failed to locate `benchfile.py`.
3. Strict 4-tuple `step()` unpacking crashed when env returned 5 values.
4. `torch.randperm` minibatch indexing yielded only marginal short-tier gain and was not promoted.
5. CPU-bookkeeping reductions in logging path were effectively neutral in short-tier runs.
6. In-place `next_obs/next_done` buffer reuse and `inference_mode` rollout both regressed throughput and were reverted.

## 8) Reproduction
### 8.1 Reproduce Phase-3 locked baseline (full)
```bash
MILABENCH_CONFIG_PATH=brdg-hackathon/sessions/torchatari/1/codex/artifacts/tmp/dev_env16_mb8.yaml \
brdg-hackathon/sessions/torchatari/1/codex/artifacts/tools/run_phase_job.sh \
  phase3 full baseline repro_p3_full \
  brdg-hackathon/sessions/torchatari/1/codex/artifacts/jobs/repro_p3_full.sh \
  brdg-hackathon/sessions/torchatari/1/codex/artifacts/jobs/repro_p3_full \
  torchatari.voir.options.stop=250
```

### 8.2 Reproduce best result (full)
```bash
MILABENCH_CONFIG_PATH=brdg-hackathon/sessions/torchatari/1/codex/artifacts/tmp/dev_env32_mb16.yaml \
brdg-hackathon/sessions/torchatari/1/codex/artifacts/tools/run_phase_job.sh \
  phase4r full codeopt_tensorcast repro_best \
  brdg-hackathon/sessions/torchatari/1/codex/artifacts/jobs/repro_best.sh \
  brdg-hackathon/sessions/torchatari/1/codex/artifacts/jobs/repro_best \
  torchatari.voir.options.stop=250
```

### 8.3 Artifacts
- Benchmarks: `artifacts/benchmarks/`
- Notes: `artifacts/notes/event_log.md`, `artifacts/notes/preflight.txt`
- Tools/helpers: `artifacts/tools/`

## 9) Next steps
- Run additional full-tier repeats for the non-HP codeopt winner (`32/16`) to tighten CI on delta.
- Profile the env-step handoff (`envs.step` + tensor ingest) with Nsight/PyTorch profiler to isolate remaining host bottlenecks.
