#!/usr/bin/env python3
"""HP sweep visualization — torchatari iteration 2 (Phase 2 + 2B combined).

Figure 1: Tier-1 rate curve (full) + Tier-2 TTR curve vs num_envs side-by-side.
Figure 2: 4×4 PDP matrix (Tier-1) with denser data + Tier-2 strip at bottom.
"""
import json, csv, glob, statistics
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D
from scipy.interpolate import griddata
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

PREP_DIR  = "/network/scratch/b/bouthilx/milabench/milabench/brdg-hackathon/sessions/torchatari/2/prep"
CSV_PATH  = f"{PREP_DIR}/prep_results.csv"
TB_BASE   = "/network/scratch/b/bouthilx/milabench/milabench/benchmarks/retired/torchatari/runs"
OUT1      = f"{PREP_DIR}/hp_sweep_ttr_curve.png"
OUT2      = f"{PREP_DIR}/hp_sweep_pdp.png"
TARGET    = 94.683
BASELINE_TTR  = 841.8   # default e128 median TTR
BASELINE_RATE = 7727.6  # default e128 median Tier-1 rate

HP_NAMES  = ["num_envs", "num_steps", "num_minibatches", "update_epochs"]
DEFAULTS  = np.array([128.0, 128.0, 4.0, 4.0])
N         = 4

# ── Data: Tier-1 — all sweep candidates ──────────────────────────────────────
# Phase 2 (from CSV)
X1_csv, y1_csv = [], []
with open(CSV_PATH) as f:
    for row in csv.DictReader(f):
        try:
            hp = json.loads(row["hp_values_json"])
        except Exception:
            continue
        if not all(k in hp for k in HP_NAMES):
            continue
        pm = row.get("primary_metric", "NA")
        if row["phase"] == "prep_p2_sweep" and pm not in ("NA", ""):
            X1_csv.append([float(hp[k]) for k in HP_NAMES])
            y1_csv.append(float(pm))

# Phase 2B Tier-1 (from JSONL files)
P2B_T1 = {
    16:  ("p2b_t1_e16_9468782",  3494.7),
    24:  ("p2b_t1_e24_9468783",  4363.2),
    32:  ("p2b_t1_e32_9468784",  4794.8),
    48:  ("p2b_t1_e48_9468785",  5265.8),
    96:  ("p2b_t1_e96_9468786",  6721.6),
    160: ("p2b_t1_e160_9468787", 7284.3),
    192: ("p2b_t1_e192_9468788", 7680.8),
    320: ("p2b_t1_e320_9468789", 7994.4),
    384: ("p2b_t1_e384_9468790", 7964.8),
}
X1_p2b, y1_p2b = [], []
for envs, (_, rate) in P2B_T1.items():
    X1_p2b.append([float(envs), 128.0, 4.0, 4.0])
    y1_p2b.append(rate)

X1 = np.array(X1_csv + X1_p2b)
y1 = np.array(y1_csv + y1_p2b)

# ── Data: Tier-2 TTR — all validated configs ──────────────────────────────────
def get_ttr(exp_name, seed, target=TARGET):
    pattern = f"{TB_BASE}/Breakout-v5__{exp_name}__{seed}__*"
    matches = glob.glob(pattern)
    if not matches:
        return None, None, None
    try:
        ea = EventAccumulator(matches[0]); ea.Reload()
        tags = ea.Tags().get("scalars", [])
        if "charts/avg_episodic_return" not in tags:
            return None, None, None
        events = ea.Scalars("charts/avg_episodic_return")
        t0 = events[0].wall_time
        window = [e for e in events if e.wall_time - t0 <= 900]
        max_q = max((e.value for e in window), default=0)
        ttr = next((e.wall_time - t0 for e in window if e.value >= target), None)
        return (900.0, max_q, True) if ttr is None else (ttr, max_q, False)
    except Exception:
        return None, None, None

# Phase 2 Tier-2 results (hardcoded from Phase 2 extraction)
T2_P2 = {
    # (label, e, s, m, u): [(ttr, max_q, dnf), ...]
    "e128_s128_m4_u4": {"e":128,"s":128,"m":4,"u":4,
        "seeds": [(700.2, 113.75, False), (900.0, 64.85, True), (841.8, 105.45, False)]},
    "e256_s128_m4_u4": {"e":256,"s":128,"m":4,"u":4,
        "seeds": [(900.0, 46.15, True), (900.0, 47.05, True), (900.0, 49.35, True)]},
}

# Phase 2B Tier-2 configs
T2_P2B_DEFS = [
    ("e16_s128_m4_u4",  "e16s128m4u4",   16, 128, 4, 4),
    ("e32_s128_m4_u4",  "e32s128m4u4",   32, 128, 4, 4),
    ("e48_s128_m4_u4",  "e48s128m4u4",   48, 128, 4, 4),
    ("e64_s128_m4_u4",  "e64s128m4u4",   64, 128, 4, 4),
    ("e96_s128_m4_u4",  "e96s128m4u4",   96, 128, 4, 4),
    ("e192_s128_m4_u4", "e192s128m4u4", 192, 128, 4, 4),
    ("e512_s128_m4_u4", "e512s128m4u4", 512, 128, 4, 4),
    ("e128_s64_m4_u4",  "e128s64m4u4",  128,  64, 4, 4),
    ("e128_s256_m4_u4", "e128s256m4u4", 128, 256, 4, 4),
    ("e128_s128_m8_u4", "e128s128m8u4", 128, 128, 8, 4),
    ("e128_s128_m4_u1", "e128s128m4u1", 128, 128, 4, 1),
]
T2_all = dict(T2_P2)
for label, exp_name, e, s, m, u in T2_P2B_DEFS:
    seeds_data = []
    for seed in [1, 2, 3]:
        ttr, max_q, dnf = get_ttr(exp_name, seed)
        if ttr is not None:
            seeds_data.append((ttr, max_q, dnf))
    if seeds_data:
        T2_all[label] = {"e": e, "s": s, "m": m, "u": u, "seeds": seeds_data}

def summarize(info):
    ttrs  = [t for t,_,_ in info["seeds"]]
    max_qs= [q for _,q,_ in info["seeds"]]
    dnfs  = [d for _,_,d in info["seeds"]]
    return statistics.median(ttrs), statistics.median(max_qs), sum(dnfs), len(ttrs)

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 1 — TTR curve vs num_envs + full Tier-1 rate curve
# ═══════════════════════════════════════════════════════════════════════════════
fig1, axes1 = plt.subplots(1, 2, figsize=(15, 6))
fig1.suptitle("torchatari iteration 2 — num_envs effect on Tier-1 rate and Tier-2 TTR\n"
              "(other HPs fixed at default: num_steps=128, num_minibatches=4, update_epochs=4)",
              fontsize=12, fontweight="bold")

# ── Left: Tier-1 rate vs num_envs ─────────────────────────────────────────────
ax = axes1[0]
# All Tier-1 data points (all phases), coloured by whether other HPs are default
envs_rate = {}  # num_envs → list of rates (OAT only: s=128, m=4, u=4)
for x, rate in zip(X1, y1):
    e, s, m, u = x
    if s == 128 and m == 4 and u == 4:
        envs_rate.setdefault(int(e), []).append(rate)

xs_t1 = sorted(envs_rate.keys())
ys_t1 = [statistics.mean(envs_rate[e]) for e in xs_t1]

ax.plot(xs_t1, ys_t1, "o-", color="steelblue", lw=2.5, ms=7, zorder=4)
for e, r in zip(xs_t1, ys_t1):
    ax.annotate(f"{r:.0f}", (e, r), textcoords="offset points",
                xytext=(0, 8), ha="center", fontsize=7, color="steelblue")

ax.axvline(128, color="navy", lw=1.5, ls="--", alpha=0.7, label="default (e=128)")
ax.axhline(BASELINE_RATE, color="navy", lw=1, ls=":", alpha=0.5)
ax.set_xscale("log", base=2)
ax.set_xticks(xs_t1)
ax.set_xticklabels([str(e) for e in xs_t1], fontsize=8, rotation=45)
ax.set_xlabel("num_envs", fontsize=11)
ax.set_ylabel("Tier-1 rate (items/s)", fontsize=11, color="steelblue")
ax.set_title("Tier-1 rate saturates then plateaus →\nhigher envs = diminishing throughput gains", fontsize=10)
ax.legend(fontsize=9); ax.grid(True, alpha=0.3)
ax.set_ylim(2000, 10500)

# ── Right: Tier-2 TTR vs num_envs ─────────────────────────────────────────────
ax = axes1[1]
# Collect num_envs OAT points (s=128, m=4, u=4)
envs_labels = [l for l in T2_all if "s128" in l and "m4" in l and "u4" in l]
envs_ttr    = {}
for label in envs_labels:
    info = T2_all[label]
    med_ttr, med_maxq, n_dnf, n_tot = summarize(info)
    envs_ttr[info["e"]] = (med_ttr, n_dnf, n_tot,
                            [t for t,_,_ in info["seeds"]],
                            [d for _,_,d in info["seeds"]])

xs_t2 = sorted(envs_ttr.keys())
ys_t2 = [envs_ttr[e][0] for e in xs_t2]
n_dnfs = [envs_ttr[e][1] for e in xs_t2]
n_tots = [envs_ttr[e][2] for e in xs_t2]

colors_t2 = ["salmon" if nd > 0 else "forestgreen" for nd in n_dnfs]

ax.scatter(xs_t2, ys_t2, c=colors_t2, s=120, zorder=5, edgecolors="k", lw=0.8)

# Draw ranges (min-max whiskers)
for e, (med, nd, nt, ttrs, _) in envs_ttr.items():
    ax.plot([e, e], [min(ttrs), max(ttrs)], color="gray", lw=1.5, zorder=3)

# Connect dots with line
ax.plot(xs_t2, ys_t2, "-", color="gray", lw=1.5, alpha=0.5, zorder=2)

# Annotate
for e, (med, nd, nt, _, _) in envs_ttr.items():
    suffix = f"\n({nd}/{nt}DNF)" if nd > 0 else f"\n{med:.0f}s"
    ax.annotate(suffix, (e, med), textcoords="offset points",
                xytext=(0, 12), ha="center", fontsize=7)

ax.axhline(900, color="k", lw=1.5, ls="--", alpha=0.7, label="900s window (DNF boundary)")
ax.axhline(BASELINE_TTR, color="navy", lw=1.5, ls=":", alpha=0.8, label=f"default median TTR ({BASELINE_TTR:.0f}s)")
ax.axvline(128, color="navy", lw=1.5, ls="--", alpha=0.5)
ax.set_xscale("log", base=2)
ax.set_xticks(xs_t2)
ax.set_xticklabels([str(e) for e in xs_t2], fontsize=8, rotation=45)
ax.set_xlabel("num_envs", fontsize=11)
ax.set_ylabel("Tier-2 TTR (s)  [DNF = 900 s]", fontsize=11)
ax.set_title("Tier-2 TTR has a minimum near e=64\n"
             "Optimum: more PPO updates/sec outweighs fewer env steps/sec", fontsize=10)
ax.set_ylim(400, 1050)
legend_els = [
    Line2D([0],[0], marker="o", color="w", markerfacecolor="forestgreen", ms=10, label="no DNF"),
    Line2D([0],[0], marker="o", color="w", markerfacecolor="salmon",      ms=10, label="≥1 DNF"),
    Line2D([0],[0], color="k",    lw=1.5, ls="--", label="900 s window"),
    Line2D([0],[0], color="navy", lw=1.5, ls=":",  label=f"default TTR ({BASELINE_TTR:.0f} s)"),
]
ax.legend(handles=legend_els, fontsize=8, loc="upper left")
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(OUT1, dpi=150, bbox_inches="tight")
print(f"Saved: {OUT1}")
plt.close()

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 2 — Full 4×4 PDP + Tier-2 multi-HP strip
# ═══════════════════════════════════════════════════════════════════════════════
norm_rate = mcolors.Normalize(vmin=y1.min(), vmax=y1.max())
cmap_rate = plt.cm.RdYlGn

fig2 = plt.figure(figsize=(16, 20))
gs2  = fig2.add_gridspec(N + 2, N, height_ratios=[1]*N + [0.7, 0.7],
                          hspace=0.55, wspace=0.45,
                          top=0.94, bottom=0.03, left=0.08, right=0.91)
cbar_ax = fig2.add_axes([0.935, 0.32, 0.013, 0.58])

def is_oat(x, i):
    return all(x[j] == DEFAULTS[j] for j in range(N) if j != i)

hp_vals = [np.unique(X1[:, i]) for i in range(N)]
X1_log  = np.log2(X1)

axes2 = [[fig2.add_subplot(gs2[i, j]) for j in range(N)] for i in range(N)]

for i in range(N):
    for j in range(N):
        ax = axes2[i][j]
        if i == j:
            oat_mask = np.array([is_oat(x, i) for x in X1])
            X_oat = X1[oat_mask, i]; y_oat = y1[oat_mask]
            srt   = np.argsort(X_oat); xs, ys = X_oat[srt], y_oat[srt]

            ax.scatter(X1[:, i], y1, c=y1, cmap=cmap_rate, norm=norm_rate,
                       s=18, alpha=0.3, zorder=2, edgecolors="none")
            ax.plot(xs, ys, "k-", lw=2, zorder=4)
            ax.scatter(xs, ys, c=ys, cmap=cmap_rate, norm=norm_rate,
                       s=70, edgecolors="k", lw=0.9, zorder=5)
            for xv, yv in zip(xs, ys):
                ax.annotate(f"{yv:.0f}", (xv, yv), textcoords="offset points",
                            xytext=(0, 6), ha="center", fontsize=5.5)
            ax.axvline(DEFAULTS[i], color="navy", lw=1.5, ls="--", alpha=0.7)
            ax.set_xscale("log", base=2)
            ax.set_xticks(hp_vals[i])
            ax.set_xticklabels([str(int(v)) for v in hp_vals[i]], fontsize=6, rotation=30)
            ax.set_xlabel(HP_NAMES[i], fontsize=9, fontweight="bold")
            ax.set_ylabel("rate\n(items/s)", fontsize=7)
            ax.set_ylim(y1.min()-300, y1.max()+400)
            ax.set_title(HP_NAMES[i], fontsize=9, fontweight="bold", pad=3)
            ax.grid(True, alpha=0.2, lw=0.5)
            ax.tick_params(axis="y", labelsize=6)
        elif i > j:
            gx = np.linspace(np.log2(hp_vals[j].min()), np.log2(hp_vals[j].max()), 50)
            gy = np.linspace(np.log2(hp_vals[i].min()), np.log2(hp_vals[i].max()), 50)
            GX, GY = np.meshgrid(gx, gy)
            pts = np.column_stack([X1_log[:, j], X1_log[:, i]])
            try:
                Z  = griddata(pts, y1, (GX, GY), method="linear")
                Zn = griddata(pts, y1, (GX, GY), method="nearest")
                Z  = np.where(np.isnan(Z), Zn, Z)
                ax.contourf(2**GX, 2**GY, Z, levels=14, cmap=cmap_rate, norm=norm_rate, alpha=0.70)
            except Exception:
                pass
            ax.scatter(X1[:, j], X1[:, i], c=y1, cmap=cmap_rate, norm=norm_rate,
                       s=40, edgecolors="k", lw=0.7, zorder=5)
            ax.axvline(DEFAULTS[j], color="navy", lw=1.5, ls="--", alpha=0.7)
            ax.axhline(DEFAULTS[i], color="navy", lw=1.5, ls="--", alpha=0.7)
            ax.set_xscale("log", base=2); ax.set_yscale("log", base=2)
            ax.set_xticks(hp_vals[j])
            ax.set_xticklabels([str(int(v)) for v in hp_vals[j]], fontsize=5.5, rotation=30)
            ax.set_yticks(hp_vals[i])
            ax.set_yticklabels([str(int(v)) for v in hp_vals[i]], fontsize=5.5)
            ax.set_xlabel(HP_NAMES[j], fontsize=8)
            ax.set_ylabel(HP_NAMES[i], fontsize=8)
            ax.grid(True, alpha=0.15, lw=0.5)
        else:
            ax.axis("off")

sm = plt.cm.ScalarMappable(cmap=cmap_rate, norm=norm_rate)
sm.set_array([])
plt.colorbar(sm, cax=cbar_ax, label="Tier-1 rate (items/s)")
cbar_ax.tick_params(labelsize=8)

# ── Bottom row A: TTR for num_envs sweep ──────────────────────────────────────
ax_envs = fig2.add_subplot(gs2[N, :])
envs_order = sorted([l for l in T2_all if "s128" in l and "m4" in l and "u4" in l],
                     key=lambda l: T2_all[l]["e"])
bx = np.arange(len(envs_order), dtype=float)
for pos, label in enumerate(envs_order):
    info = T2_all[label]
    med, _, nd, nt = summarize(info)[:4]
    ttrs = [t for t,_,_ in info["seeds"]]
    color = "salmon" if nd > 0 else "forestgreen"
    ax_envs.bar(pos, med, color=color, alpha=0.85, width=0.6, zorder=3)
    ax_envs.plot([pos,pos], [min(ttrs), max(ttrs)], "k-", lw=1.5, zorder=4)
    dnf_str = f"\n({nd}/{nt}DNF)" if nd > 0 else ""
    ax_envs.text(pos, max(ttrs)+15, f"{med:.0f}s{dnf_str}", ha="center", fontsize=7)
ax_envs.axhline(900, color="k", lw=1.5, ls="--", alpha=0.7)
ax_envs.axhline(BASELINE_TTR, color="navy", lw=1.5, ls=":", alpha=0.8)
ax_envs.set_xticks(bx)
ax_envs.set_xticklabels([f"e{T2_all[l]['e']}" for l in envs_order], fontsize=9)
ax_envs.set_ylabel("TTR (s)\nDNF=900s", fontsize=9)
ax_envs.set_ylim(0, 1100)
ax_envs.set_title("Tier-2 TTR — num_envs sweep (s=128, m=4, u=4)", fontsize=10, fontweight="bold")
ax_envs.grid(True, axis="y", alpha=0.25, zorder=0)

# ── Bottom row B: TTR for non-envs HPs ───────────────────────────────────────
ax_other = fig2.add_subplot(gs2[N+1, :])
other_labels = [
    ("e128\n(baseline)", "e128_s128_m4_u4"),
    ("s64",  "e128_s64_m4_u4"),
    ("s128\n(baseline)", "e128_s128_m4_u4"),
    ("s256", "e128_s256_m4_u4"),
    ("m4\n(baseline)", "e128_s128_m4_u4"),
    ("m8",   "e128_s128_m8_u4"),
    ("u4\n(baseline)", "e128_s128_m4_u4"),
    ("u1",   "e128_s128_m4_u1"),
]
# Deduplicate baseline so it only appears once per group
groups = [
    ("num_steps", [("s64","e128_s64_m4_u4"), ("s128\n(default)","e128_s128_m4_u4"), ("s256","e128_s256_m4_u4")]),
    ("num_minibatches", [("m4\n(default)","e128_s128_m4_u4"), ("m8","e128_s128_m8_u4")]),
    ("update_epochs",   [("u1","e128_s128_m4_u1"), ("u4\n(default)","e128_s128_m4_u4")]),
]
pos = 0; tick_pos = []; tick_labels = []
for gname, items in groups:
    for xtick, label in items:
        if label in T2_all:
            info = T2_all[label]
            med, _, nd, nt = summarize(info)[:4]
            ttrs = [t for t,_,_ in info["seeds"]]
            is_base = xtick.endswith("(default)")
            color = "lightgray" if is_base else ("salmon" if nd > 0 else "forestgreen")
            ax_other.bar(pos, med, color=color, alpha=0.85, width=0.6,
                         edgecolor="navy" if is_base else "k", lw=1.5 if is_base else 0.8, zorder=3)
            ax_other.plot([pos,pos], [min(ttrs), max(ttrs)], "k-", lw=1.5, zorder=4)
            dnf_str = f"\n({nd}/{nt}DNF)" if nd > 0 else ""
            ax_other.text(pos, max(ttrs)+15, f"{med:.0f}s{dnf_str}", ha="center", fontsize=7)
            tick_pos.append(pos); tick_labels.append(xtick)
            pos += 1
    pos += 0.7  # gap between groups

ax_other.axhline(900, color="k", lw=1.5, ls="--", alpha=0.7, label="900s window")
ax_other.axhline(BASELINE_TTR, color="navy", lw=1.5, ls=":", alpha=0.8, label=f"default ({BASELINE_TTR:.0f}s)")
ax_other.set_xticks(tick_pos)
ax_other.set_xticklabels(tick_labels, fontsize=9)
ax_other.set_ylabel("TTR (s)\nDNF=900s", fontsize=9)
ax_other.set_ylim(0, 1100)
ax_other.set_title("Tier-2 TTR — non-envs HPs (e=128)", fontsize=10, fontweight="bold")
ax_other.grid(True, axis="y", alpha=0.25, zorder=0)

legend_els2 = [
    Line2D([0],[0], marker="s", color="w", markerfacecolor="forestgreen", ms=11, label="no DNF"),
    Line2D([0],[0], marker="s", color="w", markerfacecolor="salmon",      ms=11, label="≥1 DNF"),
    Line2D([0],[0], marker="s", color="w", markerfacecolor="lightgray",   ms=11,
           markeredgecolor="navy", markeredgewidth=1.5, label="default (baseline)"),
    Line2D([0],[0], color="k",    lw=1.5, ls="--", label="900 s window"),
    Line2D([0],[0], color="navy", lw=1.5, ls=":",  label=f"default TTR ({BASELINE_TTR:.0f} s)"),
]
ax_other.legend(handles=legend_els2, fontsize=8, loc="upper right", ncol=3)

fig2.text(0.5, 0.965,
          "torchatari iteration 2 — HP sweep (Phase 2 + 2B, N=29 Tier-1 candidates)\n"
          "Upper: Tier-1 rate PDP  |  Lower: Tier-2 TTR by HP group",
          ha="center", fontsize=11, fontweight="bold")

plt.savefig(OUT2, dpi=150, bbox_inches="tight")
print(f"Saved: {OUT2}")
plt.close()
