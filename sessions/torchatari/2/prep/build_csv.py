"""Append all Phase-2 rows to prep_results.csv."""
import json, csv, os

SESSION_ID = "2026-05-04_prep_torchatari_2"
COMMIT = "e23ffee"
CSV_PATH = "/network/scratch/b/bouthilx/milabench/milabench/brdg-hackathon/sessions/torchatari/2/prep/prep_results.csv"

FIELDS = [
    "session_id","experiment_id","run_index","timestamp","tier","phase",
    "candidate","change","baseline_ref","commit_hash","env_snapshot_id",
    "primary_metric","quality_metric","peak_gpu_mem_mib","quality_verdict",
    "win_status","logging_mode","event_log_anchor","notes",
    "gpu_util_avg","cpu_util_avg","compile_time_s","hp_values_json",
]

BASELINE_REF = f"{SESSION_ID}:0"  # sanity baseline row

def row(idx, ts, tier, phase, candidate, change, primary, quality, peak_gpu,
        quality_verdict, notes, hp_json, env_snap="env_2026-05-05_sweep",
        logging_mode="original", anchor="T+50"):
    eid = f"{SESSION_ID}:{idx}"
    return {
        "session_id": SESSION_ID,
        "experiment_id": eid,
        "run_index": idx,
        "timestamp": ts,
        "tier": tier,
        "phase": phase,
        "candidate": candidate,
        "change": change,
        "baseline_ref": BASELINE_REF,
        "commit_hash": COMMIT,
        "env_snapshot_id": env_snap,
        "primary_metric": primary,
        "quality_metric": quality,
        "peak_gpu_mem_mib": peak_gpu,
        "quality_verdict": quality_verdict,
        "win_status": "NA",
        "logging_mode": logging_mode,
        "event_log_anchor": anchor,
        "notes": notes,
        "gpu_util_avg": "NA",
        "cpu_util_avg": "NA",
        "compile_time_s": "NA",
        "hp_values_json": hp_json,
    }

rows = []
idx = 1
TS_SWEEP = "2026-05-05T10:12:00-04:00"
TS_RERUN = "2026-05-05T13:00:00-04:00"
TS_BASE  = "2026-05-05T10:12:00-04:00"
TS_TTR   = "2026-05-05T10:24:00-04:00"

# ── Short baseline replicates (seeds 2, 3) ──────────────────────────────────
for seed, rate, peak in [(2, 7733.0, 4659.6), (3, 7815.5, 4659.6)]:
    hp = json.dumps({"num_envs":128,"num_steps":128,"num_minibatches":4,"update_epochs":4,"seed":seed})
    rows.append(row(idx, TS_BASE, "short", "prep_p2_short_baseline", "baseline",
                    f"seed={seed}", rate, "NA", peak, "NA",
                    f"short-run baseline replicate seed={seed}; voir stop=200 skip=5; n=200 obs", hp,
                    anchor="T+50"))
    idx += 1

# Also add sweep default run as baseline replicate
hp_def = json.dumps({"num_envs":128,"num_steps":128,"num_minibatches":4,"update_epochs":4,"seed":1})
rows.append(row(idx, TS_SWEEP, "short", "prep_p2_short_baseline", "baseline",
                "sweep run seed=1", 7722.0, "NA", 4659.6, "NA",
                "default HP sweep run used as 4th short-run baseline replicate", hp_def,
                anchor="T+50"))
idx += 1

# ── Tier-1 sweep (20 candidates) ────────────────────────────────────────────
SWEEP_DATA = [
    # (label, envs, steps, mb, ep, median_rate, peak_gpu, n_obs, ts, logging_mode, notes)
    ("e64_s128_m4_u4",   64,128,4,4, 6704.8, 2825.6, 200, TS_SWEEP, "original", "num_envs=64 (-50%)"),
    ("e128_s128_m4_u4", 128,128,4,4, 7722.0, 4659.6, 200, TS_SWEEP, "original", "default (baseline)"),
    ("e256_s128_m4_u4", 256,128,4,4, 8997.6, 7249.6, 200, TS_RERUN,  "rerun",   "num_envs=256 (+100%); rerun with max_dur=1200"),
    ("e512_s128_m4_u4", 512,128,4,4, 8092.7,13613.6,  80, TS_RERUN,  "rerun",   "num_envs=512 (+300%); stop=80 rerun"),
    ("e128_s64_m4_u4",  128, 64,4,4, 7538.8, 2529.6, 200, TS_SWEEP, "original", "num_steps=64 (-50%)"),
    ("e128_s256_m4_u4", 128,256,4,4, 7807.8, 8349.6, 200, TS_RERUN,  "rerun",   "num_steps=256 (+100%); rerun"),
    ("e128_s512_m4_u4", 128,512,4,4, 7042.7,14603.6,  80, TS_RERUN,  "rerun",   "num_steps=512 (+300%); stop=80 rerun"),
    ("e128_s128_m2_u4", 128,128,2,4, 7512.4, 6585.6, 200, TS_SWEEP, "original", "num_minibatches=2 (-50%)"),
    ("e128_s128_m8_u4", 128,128,8,4, 7933.9, 3411.6, 200, TS_SWEEP, "original", "num_minibatches=8 (+100%)"),
    ("e128_s128_m16_u4",128,128,16,4,7806.8, 3217.6, 200, TS_SWEEP, "original", "num_minibatches=16 (+300%)"),
    ("e128_s128_m4_u1", 128,128,4,1, 8072.6, 4659.6, 200, TS_SWEEP, "original", "update_epochs=1 (-75%)"),
    ("e128_s128_m4_u2", 128,128,4,2, 7877.3, 4659.6, 200, TS_SWEEP, "original", "update_epochs=2 (-50%)"),
    ("e128_s128_m4_u8", 128,128,4,8, 6655.0, 4659.6, 200, TS_SWEEP, "original", "update_epochs=8 (+100%)"),
    ("e256_s256_m8_u4", 256,256,8,4, 9023.0,10779.6,  80, TS_RERUN,  "rerun",   "cross: envs=256 steps=256 mb=8; stop=80 rerun"),
    ("e512_s256_m8_u4", 512,256,8,4, 8286.9,20671.6,  80, TS_RERUN,  "rerun",   "cross: envs=512 steps=256 mb=8; stop=80 rerun"),
    ("e256_s128_m2_u4", 256,128,2,4, 8208.0,11105.6, 200, TS_RERUN,  "rerun",   "cross: envs=256 mb=2; rerun"),
    ("e512_s128_m2_u4", 512,128,2,4, 7913.2,21319.6,  80, TS_RERUN,  "rerun",   "cross: envs=512 mb=2; stop=80 rerun"),
    ("e256_s128_m4_u8", 256,128,4,8, 7447.0, 7249.6,  80, TS_RERUN,  "rerun",   "cross: envs=256 ep=8; stop=80 rerun"),
    ("e128_s256_m4_u8", 128,256,4,8, 6548.3, 8349.6,  80, TS_RERUN,  "rerun",   "cross: steps=256 ep=8; stop=80 rerun"),
    ("e512_s128_m4_u8", 512,128,4,8, 6647.7,13613.6,  80, TS_RERUN,  "rerun",   "cross: envs=512 ep=8; stop=80 rerun"),
]

for (label, envs, steps, mb, ep, rate, peak, n_obs, ts, lmode, note) in SWEEP_DATA:
    hp = json.dumps({"num_envs":envs,"num_steps":steps,"num_minibatches":mb,"update_epochs":ep})
    rows.append(row(idx, ts, "short", "prep_p2_sweep", label,
                    note, rate, "NA", peak, "NA",
                    f"Tier-1 sweep; {note}; n={n_obs} obs", hp,
                    logging_mode=lmode, anchor="T+50"))
    idx += 1

# ── Tier-2 default-HP TTR baseline ──────────────────────────────────────────
TTR_BASELINE = [
    (1, 700.2, 113.750, "prep2_ttr_baseline_s1_9464176"),
    (2, 900.0, 64.850,  "prep2_ttr_baseline_s2_9464177"),  # DNF
    (3, 841.8, 105.450, "prep2_ttr_baseline_s3_9464178"),
]
for seed, ttr, end_q, run_name in TTR_BASELINE:
    hp = json.dumps({"num_envs":128,"num_steps":128,"num_minibatches":4,"update_epochs":4,"seed":seed})
    dnf_note = " (DNF: max quality 93.4 < target 94.683)" if seed == 2 else ""
    rows.append(row(idx, TS_TTR, "full", "prep_p2_default_ttr", "baseline",
                    f"seed={seed}", ttr, end_q, 4659.6, "PASS" if seed != 2 else "DNF",
                    f"Tier-2 TTR seed={seed}; voir stop=600; target=94.683; ttr={ttr}s{dnf_note}",
                    hp, anchor="T+55"))
    idx += 1

# Write to CSV (append)
existing_rows = []
with open(CSV_PATH, "r", newline="") as f:
    reader = csv.DictReader(f)
    for r in reader:
        existing_rows.append(r)

all_rows = existing_rows + rows

with open(CSV_PATH, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(all_rows)

print(f"Written {len(all_rows)} total rows to prep_results.csv ({len(rows)} new rows added).")
