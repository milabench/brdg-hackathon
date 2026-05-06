Profiler commands log
=====================

No profiler traces were collected during this session.

Reason:
- The optimization loop used metric-driven SBATCH benchmark runs (`run_phase_job.sh`)
  and did not invoke Nsight, `torch.profiler`, or `py-spy`.

If profiling is resumed in a follow-up session, record:
- exact command
- run name / job id
- output trace file path under this directory
