# Profiler commands — torchatari iteration 2, agent sonnet4.6

No profiler traces were captured this session. Profiling was not pursued because
the bottleneck was identified analytically from GPU utilization metrics collected
by milabench (voir gpudata events) rather than via nsight/torch.profiler.

## Bottleneck evidence (analytical)

GPU utilization observed: 17.1–17.8% (all seeds, both baseline and C1 candidate).
This directly indicates the GPU is idle ~82% of the time, waiting for envpool
to produce the next batch of observations.

## How to reproduce the analytical bottleneck evidence

```bash
# Extract GPU utilization from a milabench run data file:
python3 -c "
import json, statistics
path = '/network/scratch/r/rygaards/milabench/base/runs/<run-name>/torchatari.D0.data'
gpu_utils = []
with open(path) as f:
    for line in f:
        obj = json.loads(line.strip())
        if obj.get('event') == 'data' and 'gpudata' in obj.get('data', {}):
            u = obj['data']['gpudata'].get('0', {}).get('load')
            if u is not None:
                gpu_utils.append(u * 100)
print(f'GPU util mean: {statistics.mean(gpu_utils):.1f}%')
"
```

## How to run a proper profiler trace (future work)

```bash
# Nsight Systems trace (requires running on the compute node):
nsys profile \
    --output=/path/to/trace \
    --trace=cuda,nvtx,osrt \
    --duration=60 \
    python benchmarks/retired/torchatari/main.py \
        --num-envs 256 --num-steps 32 --num-minibatches 32 \
        --update-epochs 4 --total-timesteps 500000000

# PyTorch profiler (add to main.py):
# with torch.profiler.profile(
#     activities=[torch.profiler.ProfilerActivity.CPU,
#                 torch.profiler.ProfilerActivity.CUDA],
#     schedule=torch.profiler.schedule(wait=5, warmup=2, active=3),
#     on_trace_ready=torch.profiler.tensorboard_trace_handler('./prof_trace')
# ) as prof:
#     for iteration in iterations:
#         prof.step()
#         # ... training loop ...
```

## Key finding (no trace required)

At 6 CPUs, the envpool `step()` call occupies ~82% of each iteration.
Any GPU-side optimization can only improve the remaining 17.8%.
To achieve 17.4% total improvement, a GPU-side speedup of ~45× would be needed
— infeasible for this small CNN. The root bottleneck is CPU allocation.
