# =============================================================================
# Digital Convergence of Turkey-Affiliated Tourism Research
# Python version : 3.x
# Analysis       : Year-by-year convergence of TR-affiliated tourism papers
#                  with digital/smart/AI/data-driven terminology
# Files loaded   : Papers.txt, PaperAuthorAffiliations.txt, Affiliations.txt
#                  Source folder: C:\Users\Ekin\Downloads\6511057
#
# Column map — Papers.txt (tab-separated):
#   [0]  PaperID
#   [4]  NormalizedTitle  (lower-case)
#   [7]  Year
#
# Column map — PaperAuthorAffiliations.txt (tab-separated, 6 columns):
#   [0]  PaperID
#   [1]  AuthorID
#   [2]  AffiliationID
#   [3]  AuthorSequenceNumber
#   [4]  OriginalAuthor
#   [5]  OriginalAffiliation
#
# Column map — Affiliations.txt (tab-separated, 14 columns):
#   [0]  AffiliationID
#   [10] Iso3166Code  (filter: "TR")
# =============================================================================

import csv
import pandas as pd
import time
import sys
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── Configuration ─────────────────────────────────────────────────────────────
DATA_DIR   = r"C:\Users\Ekin\Downloads\6511057"
CHUNK_SIZE = 500_000

OUTPUT_LOG   = "output_log.txt"
OUTPUT_TABLE = "digital_convergence_table.txt"
OUTPUT_PNG   = "digital_convergence_trend.png"
OUTPUT_CSV   = "digital_convergence_data.csv"

SAMPLE_MODE = False
SAMPLE_ROWS = 5_000_000

YEAR_MIN_VALID = 1800
YEAR_MAX_VALID = 2026

PAPERS_FILE       = os.path.join(DATA_DIR, "Papers.txt",                  "Papers.txt")
PAA_FILE          = os.path.join(DATA_DIR, "PaperAuthorAffiliations.txt", "PaperAuthorAffiliations.txt")
AFFILIATIONS_FILE = os.path.join(DATA_DIR, "Affiliations.txt",            "Affiliations.txt")

# ── Keyword lists ─────────────────────────────────────────────────────────────
TOURISM_TERMS = [
    # English
    "tourism", "tourist", "hospitality",
    "hotel", "resort", "ecotourism", "gastronomy",
    "smart tourism", "e-tourism", "heritage tourism",
    "cultural tourism", "sightseeing", "leisure",
    "tourist destination", "travel destination",
    "travel agency", "air travel",
    # Turkish
    "turizm", "turistik", "otel", "konaklama", "tatil",
    "seyahat", "destinasyon", "misafirperverlik",
    "ekoturizm", "eko turizm", "kaplıca", "gastronomi",
    "kültür turizm", "kültürel turizm", "sağlık turizm",
    "kongre turizm", "kırsal turizm", "termal turizm",
    "kruvaziyer", "tur operatör", "seyahat acenta",
]

DIGITAL_TERMS = [
    # English
    "digital", "smart", "artificial intelligence", "machine learning",
    "data-driven", "big data", "internet of things", "algorithm",
    "deep learning", "blockchain", "chatbot", "automation",
    "data mining", "cloud computing", "recommendation system",
    "virtual reality", "augmented reality", "industry 4.0", "metaverse",
    "sensor",
    " ai ", " iot ",
    # Turkish
    "dijital", "akıllı", "yapay zeka", "makine öğrenmesi",
    "makine öğrenimi", "derin öğrenme", "veri odaklı",
    "büyük veri", "nesnelerin interneti", "algoritma",
    "veri madenciliği", "bulut bilişim", "otomasyon",
    "sanal gerçeklik", "artırılmış gerçeklik", "endüstri 4.0", "sensör",
]

# ── Tee: write stdout to both console and log file ────────────────────────────
class _Tee:
    def __init__(self, *streams): self.streams = streams
    def write(self, data):
        for s in self.streams: s.write(data)
    def flush(self):
        for s in self.streams: s.flush()

_log_fh = open(OUTPUT_LOG, "w", encoding="utf-8", buffering=1)
sys.stdout = _Tee(sys.__stdout__, _log_fh)

# ── Helper ────────────────────────────────────────────────────────────────────
def contains_any(text: str, terms: list) -> bool:
    for term in terms:
        if term in text:
            return True
    return False

# =============================================================================
# STEP 1: Affiliations.txt — extract TR affiliation IDs
# =============================================================================
print("=" * 60)
print("STEP 1: Affiliations.txt — extracting TR affiliation IDs ...")
print("=" * 60)
t0     = time.time()
t_step = time.time()

TR_affiliation_ids = set()
rows_scanned = 0

aff_reader = pd.read_csv(
    AFFILIATIONS_FILE, sep="\t", header=None,
    usecols=[0, 10],
    dtype={0: "Int64", 10: str},
    na_values=[""], keep_default_na=False,
    chunksize=CHUNK_SIZE, encoding="utf-8",
    on_bad_lines="skip", engine="c", low_memory=False,
)

for chunk in aff_reader:
    chunk.columns = ["AffiliationID", "Iso3166Code"]
    rows_scanned += len(chunk)
    tr_mask = chunk["Iso3166Code"] == "TR"
    TR_affiliation_ids.update(
        chunk.loc[tr_mask, "AffiliationID"].dropna().astype(int).tolist()
    )
    print(f"  ... {rows_scanned:>10,} rows | TR affiliations: {len(TR_affiliation_ids):>7,} | "
          f"{time.time()-t_step:.1f}s", end="\r")
    if SAMPLE_MODE and rows_scanned >= SAMPLE_ROWS:
        break

print(f"\n  TR affiliation IDs loaded: {len(TR_affiliation_ids):,}")
print(f"  [STEP 1 COMPLETE in {time.time()-t_step:.1f}s]")

# =============================================================================
# STEP 2: PaperAuthorAffiliations.txt — collect TR paper IDs
# =============================================================================
print()
print("=" * 60)
print("STEP 2: PaperAuthorAffiliations.txt — collecting TR paper IDs ...")
print("=" * 60)
t_step = time.time()

TR_paper_ids = set()
rows_scanned = 0

paa_reader = pd.read_csv(
    PAA_FILE, sep="\t", header=None,
    usecols=[0, 2],
    dtype={0: "Int64", 2: "Int64"},
    na_values=[""], keep_default_na=False,
    chunksize=CHUNK_SIZE, encoding="utf-8",
    on_bad_lines="skip", engine="c", low_memory=False,
)

for chunk in paa_reader:
    chunk.columns = ["PaperID", "AffiliationID"]
    rows_scanned += len(chunk)
    chunk = chunk.dropna(subset=["AffiliationID"])
    if not chunk.empty:
        chunk["AffiliationID"] = chunk["AffiliationID"].astype(int)
        tr_mask = chunk["AffiliationID"].isin(TR_affiliation_ids)
        TR_paper_ids.update(
            chunk.loc[tr_mask, "PaperID"].dropna().astype(int).tolist()
        )
    print(f"  ... {rows_scanned:>10,} rows | TR paper IDs: {len(TR_paper_ids):>9,} | "
          f"{time.time()-t_step:.1f}s", end="\r")
    if SAMPLE_MODE and rows_scanned >= SAMPLE_ROWS:
        break

print(f"\n  TR paper IDs collected: {len(TR_paper_ids):,}")
print(f"  [STEP 2 COMPLETE in {time.time()-t_step:.1f}s]")

# =============================================================================
# STEP 3: Papers.txt — filter TR tourism papers & classify digital
# =============================================================================
print()
print("=" * 60)
print("STEP 3: Papers.txt — filtering TR tourism papers ...")
print(f"  Tourism terms : {TOURISM_TERMS}")
print(f"  Digital terms : {DIGITAL_TERMS}")
print("=" * 60)
t_step = time.time()

year_stats        = {}   # { year: {"total": int, "digital": int} }
rows_scanned      = 0
tourism_found     = 0
SAMPLE_TITLE_MAX  = 1000
sample_title_rows = []   # for manual validation output

OUTPUT_MATCHED = "matched_titles.txt"
_matched_fh = open(OUTPUT_MATCHED, "w", encoding="utf-8", buffering=1)
_matched_fh.write("PaperID\tYear\tTitle\tIsDigital\n")

papers_reader = pd.read_csv(
    PAPERS_FILE, sep="\t", header=None,
    usecols=[0, 4, 7],
    dtype={0: "Int64", 4: str, 7: str},
    na_values=[""], keep_default_na=False,
    chunksize=CHUNK_SIZE, encoding="utf-8",
    on_bad_lines="skip", engine="c", low_memory=False,
)

for chunk in papers_reader:
    chunk.columns = ["PaperID", "Title", "Year"]
    rows_scanned += len(chunk)

    # Keep only TR papers
    chunk = chunk[chunk["PaperID"].isin(TR_paper_ids)]
    if chunk.empty:
        print(f"  ... {rows_scanned:>10,} rows scanned | TR-tourism found: {tourism_found:>7,} | "
              f"{time.time()-t_step:.1f}s", end="\r")
        if SAMPLE_MODE and rows_scanned >= SAMPLE_ROWS:
            break
        continue

    # Valid 4-digit year
    valid_year = chunk["Year"].str.match(r"^\d{4}$", na=False)
    chunk = chunk[valid_year].copy()
    chunk["Year"] = chunk["Year"].astype(int)

    # Filter outlier years
    chunk = chunk[
        (chunk["Year"] >= YEAR_MIN_VALID) & (chunk["Year"] <= YEAR_MAX_VALID)
    ]

    # Valid titles (NormalizedTitle is already lower-case)
    chunk = chunk[chunk["Title"].notna() & (chunk["Title"] != "")]

    # Tourism keyword filter
    tourism_mask  = chunk["Title"].apply(lambda t: contains_any(t, TOURISM_TERMS))
    tourism_chunk = chunk[tourism_mask].copy()

    if not tourism_chunk.empty:
        tourism_chunk["is_digital"] = tourism_chunk["Title"].apply(
            lambda t: contains_any(" " + t + " ", DIGITAL_TERMS)
        )
        for year, grp in tourism_chunk.groupby("Year"):
            if year not in year_stats:
                year_stats[year] = {"total": 0, "digital": 0}
            year_stats[year]["total"]   += len(grp)
            year_stats[year]["digital"] += int(grp["is_digital"].sum())
        tourism_found += len(tourism_chunk)
        # Write all matched rows to matched_titles.txt (append, chunk by chunk)
        for row in tourism_chunk[["PaperID", "Year", "Title", "is_digital"]].itertuples(index=False, name=None):
            _matched_fh.write(f"{row[0]}\t{row[1]}\t{row[2]}\t{row[3]}\n")
        # Accumulate sample titles for manual validation (up to SAMPLE_TITLE_MAX)
        if len(sample_title_rows) < SAMPLE_TITLE_MAX:
            needed = SAMPLE_TITLE_MAX - len(sample_title_rows)
            sample_title_rows.extend(
                tourism_chunk[["Year", "Title", "is_digital"]]
                .head(needed)
                .itertuples(index=False, name=None)
            )

    print(f"  ... {rows_scanned:>10,} rows scanned | TR-tourism found: {tourism_found:>7,} | "
          f"{time.time()-t_step:.1f}s", end="\r")
    if SAMPLE_MODE and rows_scanned >= SAMPLE_ROWS:
        break

print(f"\n  TR-tourism papers found : {tourism_found:,}")
print(f"  Distinct years with data: {sorted(year_stats.keys())}")
_matched_fh.close()
print(f"  Matched titles saved    : {os.path.abspath(OUTPUT_MATCHED)}")
print(f"  [STEP 3 COMPLETE in {time.time()-t_step:.1f}s]")

# =============================================================================
# STEP 3b: Save sample titles for manual validation
# =============================================================================
print()
print("=" * 60)
print("STEP 3b: Saving sample titles -> sample_titles.txt")
print("=" * 60)
t_step = time.time()

OUTPUT_SAMPLE = "sample_titles.txt"
with open(OUTPUT_SAMPLE, "w", encoding="utf-8") as f:
    f.write(f"{'Year':>6}  {'Digital':>7}  Title\n")
    f.write("-" * 80 + "\n")
    for yr, title, is_dig in sample_title_rows:
        f.write(f"{yr:>6}  {'YES' if is_dig else 'no':>7}  {title}\n")

print(f"  {len(sample_title_rows)} başlık kaydedildi (max {SAMPLE_TITLE_MAX})")
print(f"  Kaydedildi: {os.path.abspath(OUTPUT_SAMPLE)}")
print(f"  [STEP 3b COMPLETE in {time.time()-t_step:.1f}s]")

# =============================================================================
# STEP 4: Compute convergence rates per year
# =============================================================================
print()
print("=" * 60)
print("STEP 4: Computing year-by-year convergence rates ...")
print("=" * 60)
t_step = time.time()

if not year_stats:
    print("  ERROR: No TR tourism papers found. Verify file paths and data.")
    sys.exit(1)

all_years = sorted(year_stats.keys())
year_min  = all_years[0]
year_max  = all_years[-1]

table_rows = []
for yr in range(year_min, year_max + 1):
    s       = year_stats.get(yr, {"total": 0, "digital": 0})
    total   = s["total"]
    digital = s["digital"]
    rate    = (digital / total * 100.0) if total > 0 else 0.0
    table_rows.append({"Year": yr, "Total": total, "Digital": digital, "Rate": rate})

print(f"  Year range detected : {year_min} – {year_max}")
print(f"  Years with papers   : {len([r for r in table_rows if r['Total'] > 0])}")
print(f"  [STEP 4 COMPLETE in {time.time()-t_step:.1f}s]")

# =============================================================================
# STEP 5: Save digital_convergence_table.txt
# =============================================================================
print()
print("=" * 60)
print(f"STEP 5: Saving table -> {OUTPUT_TABLE}")
print("=" * 60)
t_step = time.time()

col_header = f"{'Year':>6}  {'Total TR-Tourism':>17}  {'Digital/Smart':>14}  {'Convergence %':>14}"
divider    = "-" * 58
print(col_header)
print(divider)

with open(OUTPUT_TABLE, "w", encoding="utf-8") as f:
    f.write(col_header + "\n")
    f.write(divider + "\n")
    for r in table_rows:
        line = (f"{r['Year']:>6}  {r['Total']:>17,}  "
                f"{r['Digital']:>14,}  {r['Rate']:>13.2f}%")
        print(line)
        f.write(line + "\n")

print(f"\n  Saved: {os.path.abspath(OUTPUT_TABLE)}")
print(f"  [STEP 5 COMPLETE in {time.time()-t_step:.1f}s]")

# =============================================================================
# STEP 6: Save digital_convergence_data.csv
# =============================================================================
print()
print("=" * 60)
print(f"STEP 6: Saving CSV -> {OUTPUT_CSV}")
print("=" * 60)
t_step = time.time()

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["Year", "Total", "Digital", "Rate"])
    writer.writeheader()
    writer.writerows(table_rows)

print(f"  Saved: {os.path.abspath(OUTPUT_CSV)}")
print(f"  [STEP 6 COMPLETE in {time.time()-t_step:.1f}s]")

# =============================================================================
# STEP 7: Save digital_convergence_trend.png
# =============================================================================
print()
print("=" * 60)
print(f"STEP 7: Saving trend chart -> {OUTPUT_PNG}")
print("=" * 60)
t_step = time.time()

active       = [r for r in table_rows if r["Total"] > 0]
plot_years   = [r["Year"]  for r in active]
plot_rates   = [r["Rate"]  for r in active]
plot_totals  = [r["Total"] for r in active]

fig, ax1 = plt.subplots(figsize=(13, 6), facecolor="white")

ax1.bar(plot_years, plot_totals, color="#d0e8f7", alpha=0.75,
        label="Total TR-Tourism Papers", zorder=1)
ax1.set_xlabel("Year", fontsize=11)
ax1.set_ylabel("Total TR-Tourism Papers", color="gray", fontsize=10)
ax1.tick_params(axis="y", labelcolor="gray")

ax2 = ax1.twinx()
ax2.plot(plot_years, plot_rates, color="steelblue", linewidth=2.5,
         marker="o", markersize=6, label="Convergence Rate (%)", zorder=2)
ax2.set_ylabel("Digital Convergence Rate (%)", color="steelblue", fontsize=10)
ax2.tick_params(axis="y", labelcolor="steelblue")
ax2.set_ylim(bottom=0)

ax1.set_title(
    f"Digital Convergence of Turkey-Affiliated Tourism Research ({year_min}–{year_max})",
    fontsize=13, pad=12,
)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=9)

plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(OUTPUT_PNG, dpi=150, bbox_inches="tight", facecolor="white")
plt.close()

print(f"  Saved: {os.path.abspath(OUTPUT_PNG)}")
print(f"  [STEP 7 COMPLETE in {time.time()-t_step:.1f}s]")

# =============================================================================
total_time = time.time() - t0
print()
print("=" * 60)
print(f"All steps complete.  Total runtime: {total_time / 60:.1f} min")
print("=" * 60)
