#!/usr/bin/env python3
import argparse
import json
import statistics
from pathlib import Path

from tensorboard.backend.event_processing import event_accumulator


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--run-dir", required=True)
    p.add_argument("--tb-root", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--warmup-skip", type=int, default=5)
    return p.parse_args()


def load_data_lines(run_dir: Path):
    data_files = sorted(run_dir.glob("*.data"))
    if not data_files:
        return []
    rows = []
    for f in data_files:
        with f.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return rows


def extract_rate(rows, warmup_skip: int):
    rates = []
    gpu_mem = []
    gpu_load = []
    for row in rows:
        if row.get("event") != "data":
            continue
        data = row.get("data", {})
        if data.get("task") == "train" and isinstance(data.get("rate"), (int, float)):
            rates.append(float(data["rate"]))
        gpudata = data.get("gpudata")
        if isinstance(gpudata, dict):
            for v in gpudata.values():
                mem = v.get("memory")
                if isinstance(mem, (list, tuple)) and len(mem) == 2:
                    gpu_mem.append(float(mem[0]))
                load = v.get("load")
                if isinstance(load, (int, float)):
                    gpu_load.append(float(load) * 100.0)
                break
    post = rates[warmup_skip:] if len(rates) > warmup_skip else rates
    median_rate = statistics.median(post) if post else None
    peak_mem = max(gpu_mem) if gpu_mem else None
    avg_gpu = (sum(gpu_load) / len(gpu_load)) if gpu_load else None
    return {
        "rate_series_count": len(rates),
        "rate_post_warmup_count": len(post),
        "primary_metric_rate_median": median_rate,
        "peak_gpu_mem_mib": peak_mem,
        "gpu_util_avg": avg_gpu,
    }


def extract_quality(tb_root: Path):
    run_dirs = sorted([p for p in tb_root.glob("*") if p.is_dir()], key=lambda p: p.stat().st_mtime)
    if not run_dirs:
        return {"quality_metric_avg_episodic_return_final": None, "tb_run_dir": None}

    chosen = run_dirs[-1]
    ea = event_accumulator.EventAccumulator(str(chosen))
    try:
        ea.Reload()
        scalars = ea.Scalars("charts/avg_episodic_return")
        if scalars:
            return {
                "quality_metric_avg_episodic_return_final": float(scalars[-1].value),
                "tb_run_dir": str(chosen),
            }
    except Exception:
        pass
    return {"quality_metric_avg_episodic_return_final": None, "tb_run_dir": str(chosen)}


def main():
    args = parse_args()
    run_dir = Path(args.run_dir)
    tb_root = Path(args.tb_root)
    rows = load_data_lines(run_dir)
    out = {
        "run_dir": str(run_dir),
    }
    out.update(extract_rate(rows, args.warmup_skip))
    out.update(extract_quality(tb_root))
    Path(args.output).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
