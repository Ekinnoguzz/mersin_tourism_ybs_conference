# =============================================================================
# STEP 8 — Filtered Analysis: 2002–2021
# Reads  : digital_convergence_data.csv  (produced by mersin_conferance1.py)
# Outputs: digital_convergence_table_2002_2021.txt
#          digital_convergence_trend_2002_2021.png
# Output dir: C:\Users\Ekin\Desktop\Mersin Konferansı\konferans_kodları\1.çalıştırma_outputları
# =============================================================================

import csv
import os
import sys
import time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = r"C:\Users\Ekin\Desktop\Mersin Konferansı\konferans_kodları"
OUT_DIR    = os.path.join(SCRIPT_DIR, "1.çalıştırma_outputları")
os.makedirs(OUT_DIR, exist_ok=True)

INPUT_CSV    = os.path.join(SCRIPT_DIR, "1.çalıştırma_outputları", "digital_convergence_data.csv")
OUTPUT_LOG   = os.path.join(SCRIPT_DIR, "output_log_step8.txt")
OUTPUT_TABLE = os.path.join(SCRIPT_DIR, "digital_convergence_table_2002_2021.txt")
OUTPUT_PNG   = os.path.join(SCRIPT_DIR, "digital_convergence_trend_2002_2021.png")

YEAR_FROM = 2002
YEAR_TO   = 2021

# ── Tee ───────────────────────────────────────────────────────────────────────
class _Tee:
    def __init__(self, *streams): self.streams = streams
    def write(self, data):
        for s in self.streams: s.write(data)
    def flush(self):
        for s in self.streams: s.flush()

_log_fh    = open(OUTPUT_LOG, "w", encoding="utf-8", buffering=1)
sys.stdout = _Tee(sys.__stdout__, _log_fh)

t0 = time.time()

# =============================================================================
# STEP 8: Load CSV, filter 2002–2021, write table + chart with trend line
# =============================================================================
print("=" * 60)
print(f"STEP 8: Filtered analysis {YEAR_FROM}–{YEAR_TO}")
print(f"  Input : {INPUT_CSV}")
print(f"  OutDir: {OUT_DIR}")
print("=" * 60)
t_step = time.time()

# ── 8a: Load ──────────────────────────────────────────────────────────────────
df = pd.read_csv(INPUT_CSV)
df.columns = [c.strip() for c in df.columns]   # tolerate any whitespace

required = {"Year", "Total", "Digital", "Rate"}
if not required.issubset(df.columns):
    print(f"  ERROR: CSV sütunları eksik. Bulunanlar: {list(df.columns)}")
    sys.exit(1)

df = df[(df["Year"] >= YEAR_FROM) & (df["Year"] <= YEAR_TO)].copy()
df = df.sort_values("Year").reset_index(drop=True)

print(f"  Satır sayısı ({YEAR_FROM}–{YEAR_TO}): {len(df)}")
print(f"  Toplam TR-turizm paper : {df['Total'].sum():,}")
print(f"  Toplam dijital paper   : {df['Digital'].sum():,}")

# ── 8b: Write table ───────────────────────────────────────────────────────────
col_header = (f"{'Year':>6}  {'Total TR-Tourism':>17}  "
              f"{'Digital/Smart':>14}  {'Convergence %':>14}")
divider    = "-" * 58
print()
print(col_header)
print(divider)

with open(OUTPUT_TABLE, "w", encoding="utf-8") as f:
    f.write(col_header + "\n")
    f.write(divider + "\n")
    for _, row in df.iterrows():
        line = (f"{int(row['Year']):>6}  {int(row['Total']):>17,}  "
                f"{int(row['Digital']):>14,}  {row['Rate']:>13.2f}%")
        print(line)
        f.write(line + "\n")

print(f"\n  Kaydedildi: {OUTPUT_TABLE}")

# ── 8c: Linear trend (polyfit on years with data) ─────────────────────────────
active     = df[df["Total"] > 0].copy()
plot_years = active["Year"].tolist()
plot_rates = active["Rate"].tolist()
plot_total = active["Total"].tolist()

coeffs      = np.polyfit(plot_years, plot_rates, 1)   # slope, intercept
trend_line  = np.polyval(coeffs, plot_years)
slope       = coeffs[0]
print(f"\n  Lineer trend eğimi : {slope:+.3f} pp/yıl")
print(f"  (+ = artış, - = azalış)")

# ── 8d: Chart ─────────────────────────────────────────────────────────────────
fig, ax1 = plt.subplots(figsize=(13, 6), facecolor="white")

ax1.bar(plot_years, plot_total, color="#d0e8f7", alpha=0.75,
        label="Total TR-Tourism Papers", zorder=1)
ax1.set_xlabel("Year", fontsize=11)
ax1.set_ylabel("Total TR-Tourism Papers", color="gray", fontsize=10)
ax1.tick_params(axis="y", labelcolor="gray")
ax1.set_xticks(plot_years)
ax1.tick_params(axis="x", rotation=45)

ax2 = ax1.twinx()
ax2.plot(plot_years, plot_rates, color="steelblue", linewidth=2.5,
         marker="o", markersize=6, label="Convergence Rate (%)", zorder=2)
ax2.plot(plot_years, trend_line, color="tomato", linewidth=1.4,
         linestyle="--",
         label=f"Linear Trend ({slope:+.2f} pp/yr)", zorder=3)
ax2.set_ylabel("Digital Convergence Rate (%)", color="steelblue", fontsize=10)
ax2.tick_params(axis="y", labelcolor="steelblue")
ax2.set_ylim(bottom=0)

ax1.set_title(
    f"Digital Convergence of Turkey-Affiliated Tourism Research "
    f"({YEAR_FROM}–{YEAR_TO})",
    fontsize=13, pad=12,
)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=9)

plt.tight_layout()
plt.savefig(OUTPUT_PNG, dpi=150, bbox_inches="tight", facecolor="white")
plt.close()

print(f"  Kaydedildi: {OUTPUT_PNG}")
print(f"  [STEP 8 COMPLETE in {time.time()-t_step:.1f}s]")

print()
print("=" * 60)
print(f"Toplam süre: {time.time()-t0:.2f}s")
print("=" * 60)
