# =============================================================================
# STEP 10 — Enhanced Visual: 2002–2021 with gaps for zero/sparse years
# Reads  : digital_convergence_data.csv  (produced by mersin_conferance1.py)
# Outputs: digital_convergence_trend_2002_2021_gapped.png
# =============================================================================

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR    = os.path.join(SCRIPT_DIR, "4.çalıştırma_outputları")
os.makedirs(OUT_DIR, exist_ok=True)

INPUT_CSV  = os.path.join(SCRIPT_DIR, "1.çalıştırma_outputları",
                          "digital_convergence_data.csv")
OUTPUT_PNG = os.path.join(OUT_DIR,
                          "digital_convergence_trend_2002_2021_gapped.png")

YEAR_FROM = 2002
YEAR_TO   = 2021

# Minimum papers to draw the rate line through a point; below this threshold
# the year is treated as a statistical outlier (hollow marker, no line).
MIN_N_FOR_LINE = 17

# Years manually flagged as false positives — excluded from the main line,
# shown as hollow markers with an annotation.
FALSE_POSITIVE_YEARS = {2007}

# =============================================================================
# Load & prepare
# =============================================================================
df = pd.read_csv(INPUT_CSV)
df.columns = [c.strip() for c in df.columns]

required = {"Year", "Total", "Digital", "Rate"}
if not required.issubset(df.columns):
    print(f"ERROR: CSV columns missing. Found: {list(df.columns)}")
    sys.exit(1)

df = df[(df["Year"] >= YEAR_FROM) & (df["Year"] <= YEAR_TO)].copy()
df = df.sort_values("Year").reset_index(drop=True)

# Build a complete year index so the x-axis is evenly spaced
all_years = list(range(YEAR_FROM, YEAR_TO + 1))
df_full = pd.DataFrame({"Year": all_years})
df_full = df_full.merge(df, on="Year", how="left").fillna(0)

# "Reliable" years  : Total >= MIN_N_FOR_LINE AND not false positive → main line
# "Sparse" years    : 0 < Total < MIN_N_FOR_LINE, not false positive → hollow circle
# "False positive"  : manually flagged years → red X marker
# Zero years        : Total == 0 → NaN (gap in line)
def rate_for_line(row):
    if row["Total"] >= MIN_N_FOR_LINE and row["Year"] not in FALSE_POSITIVE_YEARS:
        return row["Rate"]
    return np.nan

df_full["Rate_line"] = df_full.apply(rate_for_line, axis=1)

# Sparse: low-n years (not false positive) with at least 1 paper
df_full["Rate_sparse"] = np.where(
    (df_full["Total"] > 0)
    & (df_full["Total"] < MIN_N_FOR_LINE)
    & (~df_full["Year"].isin(FALSE_POSITIVE_YEARS)),
    df_full["Rate"], np.nan
)

# False positive: manually flagged years with at least 1 paper
df_full["Rate_fp"] = np.where(
    df_full["Year"].isin(FALSE_POSITIVE_YEARS) & (df_full["Total"] > 0),
    df_full["Rate"], np.nan
)

# y-axis cap: headroom above the maximum reliable rate
reliable = df_full[df_full["Rate_line"].notna()]
rate_max = reliable["Rate"].max() if not reliable.empty else 6.0
y2_max   = max(rate_max * 1.25, 6.0)

# =============================================================================
# Plot
# =============================================================================
fig, ax1 = plt.subplots(figsize=(13, 6), facecolor="white")

# ── Bars (total papers) ───────────────────────────────────────────────────────
bar_years  = df_full["Year"].tolist()
bar_totals = df_full["Total"].tolist()
ax1.bar(bar_years, bar_totals, color="#d0e8f7", alpha=0.80,
        label="Total TR-Tourism Papers", zorder=1)
ax1.set_xlabel("Year", fontsize=11)
ax1.set_ylabel("Total TR-Tourism Papers", color="gray", fontsize=10)
ax1.tick_params(axis="y", labelcolor="gray")
ax1.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))

# ── Rate line (reliable years only, with gaps) ────────────────────────────────
ax2 = ax1.twinx()
ax2.plot(df_full["Year"], df_full["Rate_line"],
         color="steelblue", linewidth=2.4, zorder=2,
         label=f"Convergence Rate (%) — gap = 0 or n<{MIN_N_FOR_LINE}")
ax2.scatter(reliable["Year"], reliable["Rate"],
            color="steelblue", s=50, zorder=3)

# ── Sparse points: low-n, not false positive (hollow circle) ────────────────
sparse = df_full[df_full["Rate_sparse"].notna()]
ax2.scatter(sparse["Year"], sparse["Rate_sparse"],
            facecolors="none", edgecolors="steelblue",
            s=60, linewidths=1.4, zorder=4,
            label=f"Low sample (0 < n < {MIN_N_FOR_LINE}), rate unreliable")

# ── False positive points (red X) ────────────────────────────────────────────
fp_pts = df_full[df_full["Rate_fp"].notna()]
ax2.scatter(fp_pts["Year"], fp_pts["Rate_fp"],
            marker="x", color="dimgray", s=80, linewidths=2.0, zorder=5,
            label="Confirmed false positive")

ax2.set_ylabel("Digital Convergence Rate (%)", color="steelblue", fontsize=10)
ax2.tick_params(axis="y", labelcolor="steelblue")
ax2.set_ylim(0, y2_max)

# ── Annotate 2007 confirmed false positive ───────────────────────────────────
ax2.annotate(
    "confirmed false positive\nn=40, digital=1, rate=2.5%",
    xy=(2007, 2.5),
    xytext=(2004, y2_max * 0.72),
    fontsize=8, color="dimgray",
    arrowprops=dict(arrowstyle="->", color="dimgray", lw=1.2,
                    connectionstyle="arc3,rad=-0.25"),
    bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="gray", alpha=0.9),
)

# ── Title & legend ────────────────────────────────────────────────────────────
ax1.set_title(
    f"Digital Convergence of Turkey-Affiliated Tourism Research "
    f"({YEAR_FROM}–{YEAR_TO})\n"
    f"[Gaps = 0 publications or n < {MIN_N_FOR_LINE}; "
    f"○ = low sample (n<{MIN_N_FOR_LINE}); ✕ = confirmed false positive]",
    fontsize=12, pad=10,
)

# x-ticks: every 2 years for a clean 20-year span
tick_years = [y for y in all_years if (y - YEAR_FROM) % 2 == 0]
if all_years[-1] not in tick_years:
    tick_years.append(all_years[-1])
ax1.set_xticks(tick_years)
ax1.tick_params(axis="x", rotation=45)
ax1.set_xlim(YEAR_FROM - 0.8, YEAR_TO + 0.8)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2,
           loc="upper left", fontsize=9)

plt.tight_layout()
plt.savefig(OUTPUT_PNG, dpi=150, bbox_inches="tight", facecolor="white")
plt.close()

print(f"Saved: {OUTPUT_PNG}")
