"""
Module 6 -- Cluster Validation & Profiling
Dataset: rfm_clustered.csv (4,191 customers, KMeans_Cluster as primary label)
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import seaborn as sns
from sklearn.metrics import (silhouette_score, silhouette_samples,
                              davies_bouldin_score, calinski_harabasz_score)
from sklearn.preprocessing import MinMaxScaler

# ── Theme ─────────────────────────────────────────────────────────────────────
BG = "#F7F9FC"
SEG_ORDER  = ["Champions", "Loyal Customers", "At Risk", "Lost Customers"]
SEG_COLORS = {
    "Champions":       "#F4C542",
    "Loyal Customers": "#4CAF50",
    "At Risk":         "#FF9800",
    "Lost Customers":  "#E53935",
}

plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG,
    "axes.edgecolor":   "#CCCCCC", "axes.labelcolor": "#333333",
    "axes.titlesize":   13, "axes.titleweight": "bold",
    "axes.labelsize":   11, "xtick.color": "#555555",
    "ytick.color":      "#555555", "grid.color": "#E0E0E0",
    "grid.linestyle":   "--", "grid.linewidth": 0.7,
    "font.family":      "DejaVu Sans",
})

def save(fig, fname):
    fig.savefig(fname, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {fname}")

# ─────────────────────────────────────────────────────────────────────────────
# Load Data
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 64)
print("LOADING rfm_clustered.csv")
print("=" * 64)

df = pd.read_csv("rfm_clustered.csv")
print(f"Loaded {df.shape[0]:,} rows, {df.shape[1]} columns")
print(f"K-Means cluster sizes:\n{df['KMeans_Cluster'].value_counts().sort_index().to_dict()}")

X_pca    = df[["PC1", "PC2"]].values
km_labels = df["KMeans_Cluster"].values

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 -- Cluster Profiling & Business Label Assignment
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 64)
print("STEP 1: CLUSTER PROFILING & LABEL ASSIGNMENT")
print("=" * 64)

# Compute mean RFM per K-Means cluster
profile = (df.groupby("KMeans_Cluster")[["Recency", "Frequency", "Monetary"]]
             .mean()
             .round(2))
profile["Count"] = df.groupby("KMeans_Cluster").size()

print(f"\nRaw cluster profile (mean values):\n{profile.to_string()}")

# Assign business labels using composite engagement score:
#   engagement = (1 - norm_Recency) + norm_Frequency + norm_Monetary
#   Higher = more valuable customer
scaler_p = MinMaxScaler()
norms    = pd.DataFrame(
    scaler_p.fit_transform(profile[["Recency", "Frequency", "Monetary"]]),
    index=profile.index,
    columns=["R_norm", "F_norm", "M_norm"]
)
# Recency is inverted (lower recency days = better)
norms["engagement"] = (1 - norms["R_norm"]) + norms["F_norm"] + norms["M_norm"]
ranks = norms["engagement"].rank(ascending=False).astype(int)

rank_to_label = {1: "Champions", 2: "Loyal Customers",
                 3: "At Risk",   4: "Lost Customers"}
label_map = {cluster_id: rank_to_label[rank]
             for cluster_id, rank in ranks.items()}

df["Cluster_Label"] = df["KMeans_Cluster"].map(label_map)
df["Cluster_Label"] = pd.Categorical(df["Cluster_Label"],
                                      categories=SEG_ORDER, ordered=True)

print(f"\nCluster -> Business Label mapping:")
for cid, lname in sorted(label_map.items()):
    row = profile.loc[cid]
    print(f"  Cluster {cid} -> {lname:<20}  "
          f"Recency={row['Recency']:.1f}d  "
          f"Freq={row['Frequency']:.1f}  "
          f"Mon=GBP{row['Monetary']:.0f}  "
          f"n={int(row['Count'])}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 -- Validation Metrics Summary
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 64)
print("STEP 2: VALIDATION METRICS")
print("=" * 64)

# Overall metrics
sil_overall = silhouette_score(X_pca, km_labels)
db_overall  = davies_bouldin_score(X_pca, km_labels)
ch_overall  = calinski_harabasz_score(X_pca, km_labels)

print(f"\nOverall K-Means (K=4) metrics:")
print(f"  Silhouette Score     : {sil_overall:.4f}")
print(f"  Davies-Bouldin Index : {db_overall:.4f}  (lower = better)")
print(f"  Calinski-Harabasz    : {ch_overall:.2f}  (higher = better)")

# Per-cluster silhouette scores
sil_samples = silhouette_samples(X_pca, km_labels)
print(f"\nPer-cluster silhouette scores:")
per_cluster_sil = {}
for cid in sorted(label_map):
    mask     = km_labels == cid
    cs       = sil_samples[mask].mean()
    per_cluster_sil[cid] = cs
    print(f"  Cluster {cid} ({label_map[cid]:<20}): {cs:.4f}")

# Centroids from K-Means
centroids = np.array([X_pca[km_labels == cid].mean(axis=0)
                      for cid in sorted(label_map)])

# Inter-cluster distances (centroid-to-centroid)
print(f"\nInter-cluster centroid distances (Euclidean):")
n_c = len(centroids)
inter_dist = np.zeros((n_c, n_c))
for i in range(n_c):
    for j in range(n_c):
        inter_dist[i, j] = np.linalg.norm(centroids[i] - centroids[j])

cluster_ids   = sorted(label_map)
header = "         " + "".join([f"  C{i}" for i in cluster_ids])
print(f"  {header}")
for i, ci in enumerate(cluster_ids):
    row_str = "  ".join([f"{inter_dist[i,j]:.3f}" for j in range(n_c)])
    print(f"  C{ci} ({label_map[ci][:10]:<10}) : {row_str}")

# Intra-cluster distances (mean point-to-centroid)
print(f"\nIntra-cluster distances (avg point-to-centroid):")
for i, cid in enumerate(cluster_ids):
    mask   = km_labels == cid
    dists  = np.linalg.norm(X_pca[mask] - centroids[i], axis=1)
    print(f"  Cluster {cid} ({label_map[cid]:<20}): {dists.mean():.4f}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 -- Cluster Visualizations
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 64)
print("STEP 3: GENERATING VISUALIZATIONS")
print("=" * 64)

# Cluster label -> cluster id (for centroid lookup)
label_to_cid = {v: k for k, v in label_map.items()}

# ── Plot 31: 2D PCA scatter colored by Cluster_Label ─────────────────────────
print("\nGenerating Plot 31 -- Final Cluster PCA Scatter...")

fig, ax = plt.subplots(figsize=(10, 7))
for seg in SEG_ORDER:
    mask = df["Cluster_Label"] == seg
    ax.scatter(df.loc[mask, "PC1"], df.loc[mask, "PC2"],
               c=SEG_COLORS[seg], label=seg, alpha=0.5, s=18, edgecolors="none")

# Annotate centroids
for i, cid in enumerate(cluster_ids):
    lname = label_map[cid]
    cx, cy = centroids[i]
    ax.scatter(cx, cy, c=SEG_COLORS[lname], s=280, marker="*",
               edgecolors="white", linewidth=1.2, zorder=6)
    ax.annotate(lname, xy=(cx, cy), xytext=(6, 6),
                textcoords="offset points", fontsize=9,
                color=SEG_COLORS[lname], fontweight="bold")

ax.set_title("Final Customer Segments on PC1 vs PC2  (* = centroid)")
ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
handles = [mpatches.Patch(color=SEG_COLORS[s], label=s) for s in SEG_ORDER]
ax.legend(handles=handles, title="Segment", frameon=True, framealpha=0.9, fontsize=9)
ax.grid(True)
plt.tight_layout()
save(fig, "plot31_final_clusters_pca.png")

# ── Plot 32: Radar / Spider chart ─────────────────────────────────────────────
print("Generating Plot 32 -- Radar Chart...")

# Cluster-level means, normalized 0-1 (Recency inverted: lower days = better score)
radar_profile = (df.groupby("Cluster_Label", observed=True)
                   [["Recency", "Frequency", "Monetary"]]
                   .mean()
                   .reindex(SEG_ORDER))

rmin, rmax = radar_profile["Recency"].min(),   radar_profile["Recency"].max()
fmin, fmax = radar_profile["Frequency"].min(), radar_profile["Frequency"].max()
mmin, mmax = radar_profile["Monetary"].min(),  radar_profile["Monetary"].max()

def norm(val, lo, hi):
    return 0.0 if hi == lo else (val - lo) / (hi - lo)

categories  = ["Recency\n(inverted)", "Frequency", "Monetary"]
N_cats      = len(categories)
angles      = [n / N_cats * 2 * np.pi for n in range(N_cats)]
angles     += angles[:1]

fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
ax.set_facecolor(BG)
fig.patch.set_facecolor(BG)

for seg in SEG_ORDER:
    row = radar_profile.loc[seg]
    vals = [
        1 - norm(row["Recency"],   rmin, rmax),   # inverted
        norm(row["Frequency"],     fmin, fmax),
        norm(row["Monetary"],      mmin, mmax),
    ]
    vals += vals[:1]
    ax.plot(angles, vals, "o-", linewidth=2.2,
            color=SEG_COLORS[seg], label=seg)
    ax.fill(angles, vals, alpha=0.12, color=SEG_COLORS[seg])

ax.set_theta_offset(np.pi / 2)
ax.set_theta_direction(-1)
ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=12)
ax.set_ylim(0, 1)
ax.set_yticks([0.25, 0.50, 0.75, 1.0])
ax.set_yticklabels(["0.25", "0.50", "0.75", "1.0"], fontsize=8, color="#888888")
ax.set_title("Customer Segment Radar Chart\n(normalized 0-1, higher = better)",
             pad=20, fontsize=13, fontweight="bold")
ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.15),
          frameon=True, framealpha=0.9, fontsize=10)
plt.tight_layout()
save(fig, "plot32_cluster_radar.png")

# ── Plot 33: Grouped bar chart -- avg RFM per Cluster_Label ───────────────────
print("Generating Plot 33 -- Cluster Profiles Grouped Bar Chart...")

bar_profile = (df.groupby("Cluster_Label", observed=True)
                 [["Recency", "Frequency", "Monetary"]]
                 .mean()
                 .reindex(SEG_ORDER))

metrics_bar = [("Recency (days)",   "Recency",   1.0),
               ("Avg Orders",       "Frequency", 1.0),
               ("Avg Spend (GBP)",  "Monetary",  1.0)]

x       = np.arange(len(SEG_ORDER))
n_bars  = len(metrics_bar)
width   = 0.25
offsets = np.linspace(-(n_bars-1)/2, (n_bars-1)/2, n_bars) * width

fig, ax = plt.subplots(figsize=(13, 6))
for i, (mlabel, mcol, _) in enumerate(metrics_bar):
    vals  = bar_profile[mcol].values
    # Normalise each metric to [0, 100] for visual comparability
    vmin, vmax = vals.min(), vals.max()
    vals_scaled = (vals - vmin) / (vmax - vmin) * 100 if vmax > vmin else vals
    bars = ax.bar(x + offsets[i], vals_scaled, width,
                  label=mlabel,
                  color=["#1B3A6B", "#4CAF50", "#E8604C"][i],
                  edgecolor="white", linewidth=0.5, alpha=0.88)
    for bar, raw in zip(bars, bar_profile[mcol].values):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1,
                f"{raw:.1f}", ha="center", fontsize=7.5, color="#333333")

ax.set_xticks(x)
ax.set_xticklabels(SEG_ORDER, fontsize=11)
ax.set_title("Average RFM Profile per Customer Segment\n(bars scaled 0-100 per metric for comparison)")
ax.set_ylabel("Scaled Value (0-100 per metric)")
ax.legend(frameon=False, fontsize=10)
ax.grid(axis="y")
plt.tight_layout()
save(fig, "plot33_cluster_profiles_bar.png")

# ── Plot 34: Box plots -- R, F, M per Cluster_Label ──────────────────────────
print("Generating Plot 34 -- Cluster Box Plots...")

bp_metrics = [("Recency",   "Recency (days)"),
              ("Frequency", "Number of Orders"),
              ("Monetary",  "Total Spend (GBP)")]

fig, axes = plt.subplots(1, 3, figsize=(17, 6))
fig.suptitle("RFM Distribution per Customer Segment", fontsize=14, fontweight="bold")

for ax, (col, ylabel) in zip(axes, bp_metrics):
    seg_data = [df.loc[df["Cluster_Label"] == s, col].values for s in SEG_ORDER]
    bp = ax.boxplot(seg_data, patch_artist=True,
                    medianprops={"color": "white", "linewidth": 2},
                    whiskerprops={"color": "#888888"},
                    capprops={"color": "#888888"},
                    flierprops={"marker": "o", "markersize": 3,
                                "markerfacecolor": "#AAAAAA", "alpha": 0.4})
    for patch, seg in zip(bp["boxes"], SEG_ORDER):
        patch.set_facecolor(SEG_COLORS[seg])
        patch.set_alpha(0.85)
    ax.set_xticks(range(1, len(SEG_ORDER) + 1))
    ax.set_xticklabels(SEG_ORDER, rotation=14, ha="right", fontsize=9)
    ax.set_title(col)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y")

plt.tight_layout()
save(fig, "plot34_cluster_boxplots.png")

# ── Plot 35: Heatmap -- clusters x RFM, normalised means ─────────────────────
print("Generating Plot 35 -- Cluster Profile Heatmap...")

hm_data = (df.groupby("Cluster_Label", observed=True)
             [["Recency", "Frequency", "Monetary"]]
             .mean()
             .reindex(SEG_ORDER)
             .round(1))
hm_raw  = hm_data.copy()

# Normalize each column to 0-1 for color intensity; Recency inverted
hm_norm = hm_data.copy()
for col in ["Frequency", "Monetary"]:
    lo, hi = hm_norm[col].min(), hm_norm[col].max()
    hm_norm[col] = (hm_norm[col] - lo) / (hi - lo)
hm_norm["Recency"] = 1 - (hm_norm["Recency"] - hm_norm["Recency"].min()) / \
                         (hm_norm["Recency"].max() - hm_norm["Recency"].min())
hm_norm.columns = ["Recency (inv)", "Frequency", "Monetary"]

fig, ax = plt.subplots(figsize=(9, 5))
sns.heatmap(hm_norm, annot=hm_raw.values, fmt=".1f",
            cmap="YlOrRd", linewidths=0.5, linecolor="#CCCCCC",
            annot_kws={"size": 12, "weight": "bold"},
            ax=ax, cbar_kws={"label": "Normalized Score (higher = better)"})
ax.set_title("Cluster Profile Heatmap\n(color = normalized score, annotation = raw mean)")
ax.set_xlabel("")
ax.set_ylabel("")
ax.tick_params(axis="x", rotation=0)
ax.tick_params(axis="y", rotation=0)
plt.tight_layout()
save(fig, "plot35_cluster_heatmap.png")

# ── Plot 36: Pie chart -- customer count per Cluster_Label ────────────────────
print("Generating Plot 36 -- Customer Distribution Pie...")

sizes  = [df[df["Cluster_Label"] == s].shape[0] for s in SEG_ORDER]
colors = [SEG_COLORS[s] for s in SEG_ORDER]
labels = [f"{s}\n({n:,} | {n/sum(sizes)*100:.1f}%)"
          for s, n in zip(SEG_ORDER, sizes)]

fig, ax = plt.subplots(figsize=(9, 7))
wedges, texts, autotexts = ax.pie(
    sizes, labels=labels, colors=colors,
    autopct="%1.1f%%", startangle=140,
    wedgeprops={"edgecolor": "white", "linewidth": 2},
    textprops={"fontsize": 10},
    pctdistance=0.6
)
for at in autotexts:
    at.set_color("white")
    at.set_fontweight("bold")
    at.set_fontsize(12)
for t in texts:
    t.set_fontsize(10)

ax.set_title("Customer Distribution by Segment")
plt.tight_layout()
save(fig, "plot36_cluster_distribution.png")

# ── Plot 37: Revenue contribution bar chart ───────────────────────────────────
print("Generating Plot 37 -- Revenue Contribution Bar Chart...")

total_rev = df["Monetary"].sum()
rev_data  = (df.groupby("Cluster_Label", observed=True)["Monetary"]
               .sum()
               .reindex(SEG_ORDER))
rev_pcts  = rev_data / total_rev * 100

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(SEG_ORDER, rev_data.values,
              color=[SEG_COLORS[s] for s in SEG_ORDER],
              edgecolor="white", width=0.55)

for bar, rev, pct in zip(bars, rev_data.values, rev_pcts.values):
    ax.text(bar.get_x() + bar.get_width() / 2,
            bar.get_height() + total_rev * 0.003,
            f"GBP{rev:,.0f}\n({pct:.1f}%)",
            ha="center", fontsize=10, fontweight="bold", color="#333333")

ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"GBP{x/1000:.0f}k"))
ax.set_title("Revenue Contribution per Customer Segment")
ax.set_xlabel("Segment")
ax.set_ylabel("Total Revenue (GBP)")
ax.set_ylim(0, rev_data.max() * 1.22)
ax.grid(axis="y")
plt.tight_layout()
save(fig, "plot37_revenue_contribution.png")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 -- Business Recommendations
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 64)
print("STEP 4: BUSINESS RECOMMENDATIONS")
print("=" * 64)

strategies = {
    "Champions": (
        "These customers buy frequently, spend the most, and purchased recently.\n"
        "  Action  : Launch a VIP / loyalty programme with early access and\n"
        "            exclusive rewards. Encourage referrals -- they are your\n"
        "            best brand ambassadors. Do NOT over-discount; they already\n"
        "            buy. Protect this segment at all costs."
    ),
    "Loyal Customers": (
        "Regular buyers with decent spend but lower frequency than Champions.\n"
        "  Action  : Upsell with personalised product bundles based on past\n"
        "            purchase history. Introduce subscription / repeat-order\n"
        "            incentives. Nurture with monthly newsletters and tailored\n"
        "            recommendations. Goal: convert to Champions."
    ),
    "At Risk": (
        "Previously active customers showing declining engagement.\n"
        "  Action  : Send targeted win-back email with a time-limited discount\n"
        "            (10-15%). Highlight new arrivals relevant to their past\n"
        "            categories. Add urgency (limited stock messaging).\n"
        "            Analyse what triggered the drop-off."
    ),
    "Lost Customers": (
        "Have not purchased in a long time; very low frequency and spend.\n"
        "  Action  : One final re-activation campaign with a strong offer\n"
        "            (20-30% off or free shipping). If no response within\n"
        "            90 days, move to a low-cost maintenance list or suppress\n"
        "            to save marketing budget for higher-value segments."
    ),
}

total_customers = len(df)
for seg in SEG_ORDER:
    sub     = df[df["Cluster_Label"] == seg]
    n       = len(sub)
    pct     = n / total_customers * 100
    avg_mon = sub["Monetary"].mean()
    avg_frq = sub["Frequency"].mean()
    avg_rec = sub["Recency"].mean()
    rev     = sub["Monetary"].sum()
    rev_pct = rev / df["Monetary"].sum() * 100

    print(f"\n  {'=' * 54}")
    print(f"  Cluster : {seg}")
    print(f"  Size    : {n:,} customers ({pct:.1f}%)")
    print(f"  Avg Spend  : GBP{avg_mon:,.2f} | "
          f"Avg Orders : {avg_frq:.1f} | "
          f"Avg Recency: {avg_rec:.0f} days")
    print(f"  Revenue : GBP{rev:,.2f} ({rev_pct:.1f}% of total)")
    print(f"  Strategy: {strategies[seg]}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 -- K-Means Labels vs Original RFM Segments
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 64)
print("STEP 5: K-MEANS LABELS vs RFM SEGMENTS")
print("=" * 64)

cross_tab = pd.crosstab(
    df["Cluster_Label"], df["Segment"],
    rownames=["KMeans Label"], colnames=["RFM Segment"]
)
# Reindex both axes to consistent order
cross_tab = cross_tab.reindex(index=SEG_ORDER, columns=SEG_ORDER, fill_value=0)
print(f"\nCross-tabulation (rows=K-Means labels, cols=RFM segments):\n")
print(cross_tab.to_string())

# Agreement = sum of diagonal / total
diagonal_sum = np.trace(cross_tab.values)
total_sum    = cross_tab.values.sum()
agreement    = diagonal_sum / total_sum * 100
print(f"\nOverall agreement (matching labels): {diagonal_sum:,} / {total_sum:,} = {agreement:.1f}%")

# Per-segment agreement
print(f"\nPer-segment agreement:")
for seg in SEG_ORDER:
    if seg in cross_tab.index and seg in cross_tab.columns:
        diag_val = cross_tab.loc[seg, seg]
        row_total = cross_tab.loc[seg].sum()
        seg_pct = diag_val / row_total * 100 if row_total > 0 else 0
        print(f"  {seg:<22}: {diag_val:>5,} / {row_total:>5,} = {seg_pct:.1f}%")

# -- Plot 38: Cross-tabulation heatmap ────────────────────────────────────────
print("\nGenerating Plot 38 -- K-Means vs RFM Heatmap...")

# Normalize row-wise (what % of each K-Means label falls into each RFM segment)
cross_norm = cross_tab.div(cross_tab.sum(axis=1), axis=0) * 100

fig, ax = plt.subplots(figsize=(9, 6))
sns.heatmap(cross_norm, annot=cross_tab.values, fmt="d",
            cmap="Blues", linewidths=0.5, linecolor="#CCCCCC",
            annot_kws={"size": 11, "weight": "bold"},
            ax=ax, cbar_kws={"label": "Row % (color) | Count (annotation)"},
            vmin=0, vmax=100)
ax.set_title(f"K-Means Cluster Labels vs Original RFM Segments\n"
             f"(Overall agreement: {agreement:.1f}%)")
ax.set_xlabel("Original RFM Segment")
ax.set_ylabel("K-Means Cluster Label")
ax.tick_params(axis="x", rotation=15)
ax.tick_params(axis="y", rotation=0)
plt.tight_layout()
save(fig, "plot38_kmeans_vs_rfm.png")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 -- Save Output
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 64)
print("STEP 6: SAVING rfm_final.csv")
print("=" * 64)

df.to_csv("rfm_final.csv", index=False)
print(f"  Saved: rfm_final.csv  ({df.shape[0]:,} rows, {df.shape[1]} columns)")

# ─────────────────────────────────────────────────────────────────────────────
# CLUSTER PROFILING SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 64)
print("CLUSTER PROFILING SUMMARY")
print("=" * 64)

top_rec = {
    "Champions":       "Launch VIP programme & referral scheme",
    "Loyal Customers": "Upsell bundles & subscription incentives",
    "At Risk":         "Win-back email with 10-15% time-limited discount",
    "Lost Customers":  "Final re-activation offer; suppress if no response in 90d",
}

print(f"\n  {'Segment':<22} {'Count':>6} {'%Cust':>7} "
      f"{'AvgRec':>8} {'AvgFreq':>8} {'AvgMon':>10} "
      f"{'%Rev':>7} {'SilScore':>9}")
print("  " + "-" * 86)

for seg in SEG_ORDER:
    sub    = df[df["Cluster_Label"] == seg]
    n      = len(sub)
    pct    = n / total_customers * 100
    ar     = sub["Recency"].mean()
    af     = sub["Frequency"].mean()
    am     = sub["Monetary"].mean()
    rev_p  = sub["Monetary"].sum() / df["Monetary"].sum() * 100
    cid    = label_to_cid[seg]
    cs     = per_cluster_sil[cid]
    print(f"  {seg:<22} {n:>6,} {pct:>6.1f}% "
          f"{ar:>8.1f} {af:>8.1f} {am:>10,.2f} "
          f"{rev_p:>6.1f}% {cs:>9.4f}")

print(f"\n  Overall Silhouette Score : {sil_overall:.4f}")
print(f"  Davies-Bouldin Index     : {db_overall:.4f}")
print(f"  Calinski-Harabasz        : {ch_overall:.2f}")
print(f"  K-Means vs RFM agreement : {agreement:.1f}%")

print(f"\n  Top recommendation per segment:")
for seg in SEG_ORDER:
    print(f"  {seg:<22}: {top_rec[seg]}")

print(f"\n  Output file: rfm_final.csv")
print("=" * 64)
print("Module 6 complete. All 8 plots and rfm_final.csv saved.")
