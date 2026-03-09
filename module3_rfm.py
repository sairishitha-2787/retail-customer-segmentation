"""
Module 3 — RFM Feature Engineering
Dataset: df_clean.csv (338,151 rows after preprocessing)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# ── Consistent theme ──────────────────────────────────────────────────────────
BG     = "#F7F9FC"
NAVY   = "#1B3A6B"
CORAL  = "#E8604C"

# Segment colour palette
SEG_COLORS = {
    "Champions":       "#F4C542",   # gold
    "Loyal Customers": "#4CAF50",   # green
    "At Risk":         "#FF9800",   # orange
    "Lost Customers":  "#E53935",   # red
}
SEG_ORDER = ["Champions", "Loyal Customers", "At Risk", "Lost Customers"]

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor":   BG,
    "axes.edgecolor":   "#CCCCCC",
    "axes.labelcolor":  "#333333",
    "axes.titlesize":   13,
    "axes.titleweight": "bold",
    "axes.labelsize":   11,
    "xtick.color":      "#555555",
    "ytick.color":      "#555555",
    "grid.color":       "#E0E0E0",
    "grid.linestyle":   "--",
    "grid.linewidth":   0.7,
    "font.family":      "DejaVu Sans",
})

def save(fig, filename):
    fig.savefig(filename, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {filename}")

# ─────────────────────────────────────────────────────────────────────────────
# Load Data
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("LOADING df_clean.csv")
print("=" * 60)

df = pd.read_csv("df_clean.csv", parse_dates=["InvoiceDate"])
print(f"Loaded {df.shape[0]:,} rows\n")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Calculate RFM
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("STEP 1: CALCULATING RFM METRICS")
print("=" * 60)

# Snapshot date = 1 day after the last transaction date
snapshot_date = df["InvoiceDate"].max() + pd.Timedelta(days=1)
print(f"\nSnapshot date: {snapshot_date.date()}")

# Group by CustomerID and compute Recency, Frequency, Monetary
rfm = df.groupby("CustomerID").agg(
    LastPurchase=("InvoiceDate", "max"),
    Frequency   =("InvoiceNo",   "nunique"),
    Monetary    =("TotalPrice",  "sum")
).reset_index()

# Recency = days between snapshot and last purchase
rfm["Recency"] = (snapshot_date - rfm["LastPurchase"]).dt.days
rfm = rfm.drop(columns=["LastPurchase"])
rfm = rfm[["CustomerID", "Recency", "Frequency", "Monetary"]]

print(f"\nRFM dataframe shape: {rfm.shape}")
print(f"\nFirst 5 rows:\n{rfm.head()}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — RFM Distribution Analysis (raw)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 2: RFM DISTRIBUTION ANALYSIS (RAW)")
print("=" * 60)

print(f"\nDescriptive Statistics:\n{rfm[['Recency','Frequency','Monetary']].describe().round(2)}")

fig, axes = plt.subplots(1, 3, figsize=(15, 4))
fig.suptitle("RFM Distributions — Raw", fontsize=15, fontweight="bold", y=1.02)

for ax, col, color in zip(axes, ["Recency", "Frequency", "Monetary"],
                           [NAVY, CORAL, "#4CAF50"]):
    ax.hist(rfm[col], bins=50, color=color, edgecolor="white", linewidth=0.4)
    ax.set_title(col)
    ax.set_xlabel(col)
    ax.set_ylabel("Count")
    ax.grid(axis="y")

plt.tight_layout()
save(fig, "plot9_rfm_distributions_raw.png")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Log Transformation (Frequency & Monetary are skewed)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 3: LOG TRANSFORMATION")
print("=" * 60)

rfm["Frequency_log"] = np.log1p(rfm["Frequency"])
rfm["Monetary_log"]  = np.log1p(rfm["Monetary"])

print("log1p applied to Frequency and Monetary.")
print(rfm[["Frequency_log", "Monetary_log"]].describe().round(4))

fig, axes = plt.subplots(1, 3, figsize=(15, 4))
fig.suptitle("RFM Distributions — After Log Transformation", fontsize=15,
             fontweight="bold", y=1.02)

plot_data = [
    ("Recency (unchanged)", rfm["Recency"],       NAVY),
    ("Frequency (log1p)",   rfm["Frequency_log"], CORAL),
    ("Monetary (log1p)",    rfm["Monetary_log"],  "#4CAF50"),
]
for ax, (title, data, color) in zip(axes, plot_data):
    ax.hist(data, bins=50, color=color, edgecolor="white", linewidth=0.4)
    ax.set_title(title)
    ax.set_xlabel("Value")
    ax.set_ylabel("Count")
    ax.grid(axis="y")

plt.tight_layout()
save(fig, "plot10_rfm_distributions_log.png")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — RFM Scoring (quartile-based, 1–4)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 4: RFM SCORING (1–4 PER QUARTILE)")
print("=" * 60)

# Recency: lower = better → reverse scoring
rfm["R_Score"] = pd.qcut(rfm["Recency"],   q=4, labels=[4, 3, 2, 1]).astype(int)

# Frequency: higher = better
rfm["F_Score"] = pd.qcut(rfm["Frequency"].rank(method="first"),
                          q=4, labels=[1, 2, 3, 4]).astype(int)

# Monetary: higher = better
rfm["M_Score"] = pd.qcut(rfm["Monetary"].rank(method="first"),
                          q=4, labels=[1, 2, 3, 4]).astype(int)

# Composite numeric score (range 3–12)
rfm["RFM_Score"] = rfm["R_Score"] + rfm["F_Score"] + rfm["M_Score"]

# String segment code e.g. "444"
rfm["RFM_Segment"] = (rfm["R_Score"].astype(str) +
                       rfm["F_Score"].astype(str) +
                       rfm["M_Score"].astype(str))

print(f"\nRFM_Score range: {rfm['RFM_Score'].min()} – {rfm['RFM_Score'].max()}")
print(f"\nScore distribution:\n{rfm['RFM_Score'].value_counts().sort_index()}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — Customer Segment Labels
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 5: ASSIGNING SEGMENT LABELS")
print("=" * 60)

def assign_segment(score):
    if score >= 10:
        return "Champions"
    elif score >= 7:
        return "Loyal Customers"
    elif score >= 5:
        return "At Risk"
    else:
        return "Lost Customers"

rfm["Segment"] = rfm["RFM_Score"].apply(assign_segment)
rfm["Segment"] = pd.Categorical(rfm["Segment"], categories=SEG_ORDER, ordered=True)

print(f"\nSegment counts:\n{rfm['Segment'].value_counts()[SEG_ORDER]}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — Visualizations
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 6: GENERATING PLOTS")
print("=" * 60)

# ── Plot 11: Customer count per segment ──────────────────────────────────────
print("\nGenerating Plot 11 — Segment Counts...")

seg_counts = rfm["Segment"].value_counts()[SEG_ORDER]
bar_colors = [SEG_COLORS[s] for s in SEG_ORDER]

fig, ax = plt.subplots(figsize=(9, 5))
bars = ax.bar(SEG_ORDER, seg_counts.values, color=bar_colors,
              edgecolor="white", width=0.55)

for bar, val in zip(bars, seg_counts.values):
    pct = val / seg_counts.sum() * 100
    ax.text(bar.get_x() + bar.get_width() / 2,
            bar.get_height() + seg_counts.max() * 0.015,
            f"{val:,}\n({pct:.1f}%)", ha="center", fontsize=10, color="#333333")

ax.set_title("Customer Count per Segment")
ax.set_xlabel("Segment")
ax.set_ylabel("Number of Customers")
ax.set_ylim(0, seg_counts.max() * 1.18)
ax.grid(axis="y")
plt.tight_layout()
save(fig, "plot11_segment_counts.png")

# ── Plot 12: Box plots of R, F, M per segment ────────────────────────────────
print("Generating Plot 12 — Segment Box Plots...")

metrics = [("Recency",   "Recency (days)"),
           ("Frequency", "Number of Orders"),
           ("Monetary",  "Total Spend (£)")]

fig, axes = plt.subplots(1, 3, figsize=(17, 6))
fig.suptitle("RFM Metrics by Customer Segment", fontsize=15, fontweight="bold")

for ax, (col, ylabel) in zip(axes, metrics):
    seg_data = [rfm.loc[rfm["Segment"] == s, col].values for s in SEG_ORDER]
    bp = ax.boxplot(seg_data, patch_artist=True, medianprops={"color": "white", "linewidth": 2},
                    whiskerprops={"color": "#888888"},
                    capprops={"color": "#888888"},
                    flierprops={"marker": "o", "markersize": 3,
                                "markerfacecolor": "#AAAAAA", "alpha": 0.5})
    for patch, seg in zip(bp["boxes"], SEG_ORDER):
        patch.set_facecolor(SEG_COLORS[seg])
        patch.set_alpha(0.85)

    ax.set_xticks(range(1, len(SEG_ORDER) + 1))
    ax.set_xticklabels(SEG_ORDER, rotation=15, ha="right", fontsize=9)
    ax.set_title(col)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y")

plt.tight_layout()
save(fig, "plot12_segment_boxplots.png")

# ── Plot 13: Scatter Frequency vs Monetary, coloured by Segment ──────────────
print("Generating Plot 13 — Frequency vs Monetary Scatter...")

fig, ax = plt.subplots(figsize=(10, 7))

for seg in SEG_ORDER:
    subset = rfm[rfm["Segment"] == seg]
    ax.scatter(np.log1p(subset["Frequency"]),
               np.log1p(subset["Monetary"]),
               c=SEG_COLORS[seg], label=seg,
               alpha=0.55, s=25, edgecolors="none")

ax.set_title("Frequency vs Monetary by Segment (log scale)")
ax.set_xlabel("log1p(Frequency)")
ax.set_ylabel("log1p(Monetary)")
ax.legend(title="Segment", frameon=True, framealpha=0.9)
ax.grid(True)
plt.tight_layout()
save(fig, "plot13_rfm_scatter.png")

# ── Plot 14: Heatmap of average R, F, M scores per segment ───────────────────
print("Generating Plot 14 — RFM Score Heatmap...")

heatmap_data = (rfm.groupby("Segment", observed=True)[["R_Score", "F_Score", "M_Score"]]
                   .mean()
                   .reindex(SEG_ORDER)
                   .round(2))
heatmap_data.columns = ["Avg R Score", "Avg F Score", "Avg M Score"]

fig, ax = plt.subplots(figsize=(8, 5))
sns.heatmap(heatmap_data, annot=True, fmt=".2f", cmap="YlOrRd",
            linewidths=0.5, linecolor="#CCCCCC",
            annot_kws={"size": 13, "weight": "bold"},
            ax=ax, cbar_kws={"label": "Average Score"})
ax.set_title("Average RFM Scores per Segment")
ax.set_xlabel("")
ax.set_ylabel("")
ax.tick_params(axis="x", rotation=0)
ax.tick_params(axis="y", rotation=0)
plt.tight_layout()
save(fig, "plot14_rfm_heatmap.png")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 — Save RFM dataframe
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 7: SAVING rfm.csv")
print("=" * 60)

rfm.to_csv("rfm.csv", index=False)
print("  Saved: rfm.csv")

# ─────────────────────────────────────────────────────────────────────────────
# RFM SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
total_customers = len(rfm)
total_monetary  = rfm["Monetary"].sum()

seg_summary = rfm.groupby("Segment", observed=True).agg(
    Count      =("CustomerID", "count"),
    Avg_Recency=("Recency",    "mean"),
    Avg_Freq   =("Frequency",  "mean"),
    Avg_Mon    =("Monetary",   "mean"),
    Total_Rev  =("Monetary",   "sum"),
).reindex(SEG_ORDER).round(2)

seg_summary["Pct_Customers"] = (seg_summary["Count"] / total_customers * 100).round(1)
seg_summary["Pct_Revenue"]   = (seg_summary["Total_Rev"] / total_monetary * 100).round(1)

top_rev_seg = seg_summary["Total_Rev"].idxmax()

print("\n" + "=" * 60)
print("RFM SUMMARY")
print("=" * 60)
print(f"\n  Total customers: {total_customers:,}\n")
print(f"  {'Segment':<20} {'Count':>7} {'%Cust':>7} {'AvgRec':>8} "
      f"{'AvgFreq':>8} {'AvgMon':>10} {'%Rev':>7}")
print("  " + "-" * 72)
for seg in SEG_ORDER:
    r = seg_summary.loc[seg]
    print(f"  {seg:<20} {int(r['Count']):>7,} {r['Pct_Customers']:>6.1f}% "
          f"{r['Avg_Recency']:>8.1f} {r['Avg_Freq']:>8.1f} "
          f"£{r['Avg_Mon']:>9,.2f} {r['Pct_Revenue']:>6.1f}%")

print(f"\n  Segment with highest revenue contribution: {top_rev_seg}")
print("=" * 60)
print("Module 3 complete. All plots and rfm.csv saved.")
