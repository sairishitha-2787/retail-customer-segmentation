"""
Module 4 — Dimensionality Reduction: PCA + LDA
Dataset: rfm.csv (4,191 customers with RFM scores and segments)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from mpl_toolkits.mplot3d import Axes3D          # noqa: F401 (registers 3D projection)
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

# ── Consistent theme ──────────────────────────────────────────────────────────
BG = "#F7F9FC"
SEG_ORDER  = ["Champions", "Loyal Customers", "At Risk", "Lost Customers"]
SEG_COLORS = {
    "Champions":       "#F4C542",
    "Loyal Customers": "#4CAF50",
    "At Risk":         "#FF9800",
    "Lost Customers":  "#E53935",
}

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

def seg_legend(ax):
    handles = [mpatches.Patch(color=SEG_COLORS[s], label=s) for s in SEG_ORDER]
    ax.legend(handles=handles, title="Segment", frameon=True,
              framealpha=0.9, fontsize=9)

# ─────────────────────────────────────────────────────────────────────────────
# Load Data
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 62)
print("LOADING rfm.csv")
print("=" * 62)

rfm = pd.read_csv("rfm.csv")
rfm["Segment"] = pd.Categorical(rfm["Segment"], categories=SEG_ORDER, ordered=True)
print(f"Loaded {rfm.shape[0]:,} rows, {rfm.shape[1]} columns")
print(f"Segments: {rfm['Segment'].value_counts()[SEG_ORDER].to_dict()}\n")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Prepare Features
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 62)
print("STEP 1: FEATURE PREPARATION")
print("=" * 62)

# Select raw RFM features
features = ["Recency", "Frequency", "Monetary"]
X = rfm[features].copy()

# Apply log1p to skewed Frequency and Monetary
X["Frequency"] = np.log1p(X["Frequency"])
X["Monetary"]  = np.log1p(X["Monetary"])

# StandardScaler → zero mean, unit variance
scaler   = StandardScaler()
X_scaled = scaler.fit_transform(X)

labels   = rfm["Segment"].values
print(f"\nFeatures: {features}")
print(f"X_scaled shape: {X_scaled.shape}")
print(f"Mean per feature (should be ~0): {X_scaled.mean(axis=0).round(4)}")
print(f"Std  per feature (should be ~1): {X_scaled.std(axis=0).round(4)}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — PCA
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 62)
print("STEP 2: PRINCIPAL COMPONENT ANALYSIS (PCA)")
print("=" * 62)

pca = PCA(n_components=3, random_state=42)
X_pca = pca.fit_transform(X_scaled)

evr        = pca.explained_variance_ratio_
cumulative = np.cumsum(evr)

print("\nExplained Variance per Component:")
for i, (e, c) in enumerate(zip(evr, cumulative), 1):
    print(f"  PC{i}: {e*100:.2f}%   (Cumulative: {c*100:.2f}%)")

# Component loadings table
loadings_df = pd.DataFrame(
    pca.components_.T,
    index=features,
    columns=["PC1", "PC2", "PC3"]
).round(4)

print("\nComponent Loadings (contribution of each RFM feature):")
print(loadings_df.to_string())

dominant = {f"PC{i+1}": features[np.argmax(np.abs(pca.components_[i]))]
            for i in range(3)}
print("\nDominant feature per component:")
for pc, feat in dominant.items():
    print(f"  {pc} -> {feat}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — PCA Visualizations
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 62)
print("STEP 3: PCA VISUALIZATIONS")
print("=" * 62)

# ── Plot 15: Scree plot ───────────────────────────────────────────────────────
print("\nGenerating Plot 15 — Scree Plot...")

fig, ax1 = plt.subplots(figsize=(7, 5))
bars = ax1.bar([f"PC{i+1}" for i in range(3)], evr * 100,
               color=["#1B3A6B", "#3A6FB0", "#7DA8D4"],
               edgecolor="white", width=0.45, label="Individual variance")
ax1.set_ylabel("Explained Variance (%)", color="#1B3A6B")
ax1.set_ylim(0, 110)
ax1.tick_params(axis="y", labelcolor="#1B3A6B")

for bar, v in zip(bars, evr * 100):
    ax1.text(bar.get_x() + bar.get_width() / 2, v + 1.5,
             f"{v:.1f}%", ha="center", fontsize=11, color="#1B3A6B", fontweight="bold")

ax2 = ax1.twinx()
ax2.plot([f"PC{i+1}" for i in range(3)], cumulative * 100,
         color="#E8604C", marker="o", linewidth=2.2, markersize=7, label="Cumulative")
ax2.set_ylabel("Cumulative Variance (%)", color="#E8604C")
ax2.set_ylim(0, 110)
ax2.tick_params(axis="y", labelcolor="#E8604C")
ax2.axhline(100, color="#E8604C", linewidth=0.8, linestyle=":")

for i, c in enumerate(cumulative * 100):
    ax2.annotate(f"{c:.1f}%",
                 xy=(i, c), xytext=(8, 4), textcoords="offset points",
                 fontsize=9, color="#E8604C")

ax1.set_title("PCA Scree Plot — Variance Explained")
ax1.grid(axis="y")
fig.tight_layout()
save(fig, "plot15_pca_scree.png")

# ── Plot 16: 2D PCA scatter ───────────────────────────────────────────────────
print("Generating Plot 16 — 2D PCA Scatter...")

fig, ax = plt.subplots(figsize=(10, 7))
for seg in SEG_ORDER:
    mask = labels == seg
    ax.scatter(X_pca[mask, 0], X_pca[mask, 1],
               c=SEG_COLORS[seg], label=seg,
               alpha=0.55, s=18, edgecolors="none")

ax.set_xlabel(f"PC1 ({evr[0]*100:.1f}% variance explained)")
ax.set_ylabel(f"PC2 ({evr[1]*100:.1f}% variance explained)")
ax.set_title("PCA — 2D Projection by Customer Segment")
seg_legend(ax)
ax.grid(True)
plt.tight_layout()
save(fig, "plot16_pca_2d.png")

# ── Plot 17: 3D PCA scatter ───────────────────────────────────────────────────
print("Generating Plot 17 — 3D PCA Scatter...")

fig = plt.figure(figsize=(11, 8), facecolor=BG)
ax  = fig.add_subplot(111, projection="3d")
ax.set_facecolor(BG)

for seg in SEG_ORDER:
    mask = labels == seg
    ax.scatter(X_pca[mask, 0], X_pca[mask, 1], X_pca[mask, 2],
               c=SEG_COLORS[seg], label=seg,
               alpha=0.5, s=15, edgecolors="none")

ax.set_xlabel(f"PC1 ({evr[0]*100:.1f}%)", labelpad=8)
ax.set_ylabel(f"PC2 ({evr[1]*100:.1f}%)", labelpad=8)
ax.set_zlabel(f"PC3 ({evr[2]*100:.1f}%)", labelpad=8)
ax.set_title("PCA — 3D Projection by Customer Segment")
ax.legend(title="Segment", fontsize=9, loc="upper left")
plt.tight_layout()
save(fig, "plot17_pca_3d.png")

# ── Plot 18: PCA Biplot ───────────────────────────────────────────────────────
print("Generating Plot 18 — PCA Biplot...")

# Scale loadings for visibility
scale     = np.sqrt(pca.explained_variance_)
loadings  = pca.components_.T * scale      # shape (3 features, 3 PCs)

fig, ax = plt.subplots(figsize=(10, 7))
for seg in SEG_ORDER:
    mask = labels == seg
    ax.scatter(X_pca[mask, 0], X_pca[mask, 1],
               c=SEG_COLORS[seg], alpha=0.35, s=15, edgecolors="none")

# Draw feature vectors
arrow_kw = dict(arrowstyle="-|>", color="#1B3A6B", lw=1.8)
for i, feat in enumerate(features):
    ax.annotate("", xy=(loadings[i, 0] * 2.8, loadings[i, 1] * 2.8),
                xytext=(0, 0), arrowprops=arrow_kw)
    ax.text(loadings[i, 0] * 3.1, loadings[i, 1] * 3.1,
            feat, ha="center", fontsize=11, color="#1B3A6B", fontweight="bold")

ax.set_xlabel(f"PC1 ({evr[0]*100:.1f}%)")
ax.set_ylabel(f"PC2 ({evr[1]*100:.1f}%)")
ax.set_title("PCA Biplot — Feature Vectors + Customer Segments")
seg_legend(ax)
ax.axhline(0, color="#AAAAAA", linewidth=0.6)
ax.axvline(0, color="#AAAAAA", linewidth=0.6)
ax.grid(True)
plt.tight_layout()
save(fig, "plot18_pca_biplot.png")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — LDA
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 62)
print("STEP 4: LINEAR DISCRIMINANT ANALYSIS (LDA)")
print("=" * 62)

# With 4 classes, LDA produces at most 3 discriminant components
lda   = LinearDiscriminantAnalysis(n_components=3)
X_lda = lda.fit_transform(X_scaled, labels)

lda_evr  = lda.explained_variance_ratio_
lda_cum  = np.cumsum(lda_evr)

print("\nLDA Explained Variance Ratio per Component:")
for i, (e, c) in enumerate(zip(lda_evr, lda_cum), 1):
    print(f"  LD{i}: {e*100:.2f}%   (Cumulative: {c*100:.2f}%)")

# Within-class scatter measure: mean distance from own centroid
print("\nClass Separation Quality (mean distance from centroid):")
for seg in SEG_ORDER:
    mask     = labels == seg
    centroid = X_lda[mask].mean(axis=0)
    spread   = np.mean(np.linalg.norm(X_lda[mask] - centroid, axis=1))
    print(f"  {seg:<22}: within-class spread = {spread:.3f}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — LDA Visualizations
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 62)
print("STEP 5: LDA VISUALIZATIONS")
print("=" * 62)

# ── Plot 19: 2D LDA scatter with centroids ────────────────────────────────────
print("\nGenerating Plot 19 — 2D LDA Scatter...")

fig, ax = plt.subplots(figsize=(10, 7))
for seg in SEG_ORDER:
    mask     = labels == seg
    centroid = X_lda[mask, :2].mean(axis=0)
    ax.scatter(X_lda[mask, 0], X_lda[mask, 1],
               c=SEG_COLORS[seg], alpha=0.45, s=18, edgecolors="none", label=seg)
    ax.scatter(*centroid, c=SEG_COLORS[seg], s=280, marker="*",
               edgecolors="white", linewidth=1.2, zorder=5)
    ax.annotate(seg, xy=centroid, xytext=(6, 6), textcoords="offset points",
                fontsize=8.5, color=SEG_COLORS[seg], fontweight="bold")

ax.set_xlabel(f"LD1 ({lda_evr[0]*100:.1f}% variance explained)")
ax.set_ylabel(f"LD2 ({lda_evr[1]*100:.1f}% variance explained)")
ax.set_title("LDA — 2D Projection by Customer Segment\n(★ = segment centroid)")
seg_legend(ax)
ax.grid(True)
plt.tight_layout()
save(fig, "plot19_lda_2d.png")

# ── Plot 20: LDA class separation bar chart ───────────────────────────────────
print("Generating Plot 20 — LDA Class Separation...")

# Between-class distance: distance of each centroid from the global centroid
global_centroid = X_lda[:, :2].mean(axis=0)
sep_scores = {}
for seg in SEG_ORDER:
    mask     = labels == seg
    centroid = X_lda[mask, :2].mean(axis=0)
    sep_scores[seg] = np.linalg.norm(centroid - global_centroid)

fig, ax = plt.subplots(figsize=(9, 5))
bars = ax.bar(SEG_ORDER,
              [sep_scores[s] for s in SEG_ORDER],
              color=[SEG_COLORS[s] for s in SEG_ORDER],
              edgecolor="white", width=0.5)

for bar, seg in zip(bars, SEG_ORDER):
    ax.text(bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.02,
            f"{sep_scores[seg]:.3f}",
            ha="center", fontsize=11, fontweight="bold", color="#333333")

ax.set_title("LDA Class Separation\n(Distance of Segment Centroid from Global Centroid)")
ax.set_xlabel("Segment")
ax.set_ylabel("Centroid Distance (LD1–LD2 space)")
ax.grid(axis="y")
plt.tight_layout()
save(fig, "plot20_lda_separation.png")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — PCA vs LDA Comparison
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 62)
print("STEP 6: PCA vs LDA COMPARISON")
print("=" * 62)

pca_2comp = (evr[0] + evr[1]) * 100
lda_2comp = (lda_evr[0] + lda_evr[1]) * 100

comparison = pd.DataFrame({
    "Technique": ["PCA", "LDA"],
    "Variance by 2 components (%)": [f"{pca_2comp:.1f}%", f"{lda_2comp:.1f}%"],
    "Objective": ["Maximises total variance", "Maximises class separation"],
    "Supervision": ["Unsupervised", "Supervised (uses Segment labels)"],
    "Best for": ["Compression / noise reduction", "Classification / cluster separation"],
})
print(f"\n{comparison.to_string(index=False)}")

better = "LDA" if lda_2comp > pca_2comp else "PCA"
print(f"""
  Interpretation:
  - PCA captures {pca_2comp:.1f}% of total variance in 2 components.
  - LDA captures {lda_2comp:.1f}% of between-class variance in 2 components.
  - {better} gives better visual cluster separation because it directly
    maximises the ratio of between-class to within-class scatter,
    producing tighter, more distinct segment clusters in 2D space.
    PCA is blind to labels and spreads variance without regard for
    which customers belong to which segment.
""")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 — Save Output
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 62)
print("STEP 7: SAVING rfm_reduced.csv")
print("=" * 62)

rfm_reduced = rfm[["CustomerID", "Recency", "Frequency", "Monetary",
                    "RFM_Score", "RFM_Segment", "Segment"]].copy()
rfm_reduced["PC1"] = X_pca[:, 0]
rfm_reduced["PC2"] = X_pca[:, 1]
rfm_reduced["PC3"] = X_pca[:, 2]
rfm_reduced["LD1"] = X_lda[:, 0]
rfm_reduced["LD2"] = X_lda[:, 1]

rfm_reduced.to_csv("rfm_reduced.csv", index=False)
print(f"  Saved: rfm_reduced.csv  ({rfm_reduced.shape[0]:,} rows, {rfm_reduced.shape[1]} columns)")

# ─────────────────────────────────────────────────────────────────────────────
# DIMENSIONALITY REDUCTION SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 62)
print("DIMENSIONALITY REDUCTION SUMMARY")
print("=" * 62)

print(f"""
  PCA — Explained Variance:
    PC1 : {evr[0]*100:.2f}%   -> dominant feature: {dominant['PC1']}
    PC2 : {evr[1]*100:.2f}%   -> dominant feature: {dominant['PC2']}
    PC3 : {evr[2]*100:.2f}%   -> dominant feature: {dominant['PC3']}
    2-component cumulative: {pca_2comp:.2f}%
    3-component cumulative: {cumulative[2]*100:.2f}%

  PCA — Feature Loadings (PC1 | PC2 | PC3):""")
for feat in features:
    row = loadings_df.loc[feat]
    print(f"    {feat:<12}: {row['PC1']:+.4f}  {row['PC2']:+.4f}  {row['PC3']:+.4f}")

print(f"""
  LDA — Explained Variance:
    LD1 : {lda_evr[0]*100:.2f}%   (primary discriminant axis)
    LD2 : {lda_evr[1]*100:.2f}%
    2-component cumulative: {lda_2comp:.2f}%

  Recommendation:
    Use LDA projections (LD1, LD2) for visualising segment separation.
    Use PCA projections (PC1, PC2, PC3) as input features for
    unsupervised clustering (K-Means / DBSCAN) in Module 5.
""")
print("=" * 62)
print("Module 4 complete. All plots and rfm_reduced.csv saved.")
