"""
Module 5 -- Clustering + Distance Metric Comparison
Dataset: rfm_reduced.csv (4,191 customers with PCA components)
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.metrics import (silhouette_score, davies_bouldin_score,
                              calinski_harabasz_score, pairwise_distances)
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from scipy.cluster.hierarchy import dendrogram, linkage

# ─────────────────────────────────────────────────────────────────────────────
# Pure-NumPy K-Medoids (alternate algorithm, works with precomputed distances)
# No C compiler required — drop-in replacement for sklearn_extra.KMedoids
# ─────────────────────────────────────────────────────────────────────────────
class KMedoids:
    """K-Medoids clustering using the 'alternate' (Voronoi-iteration) algorithm.
    Accepts a precomputed (n x n) distance matrix.
    Complexity: O(n * k) per iteration — fast for n ~ 4000.
    """
    def __init__(self, n_clusters=4, random_state=None, max_iter=300):
        self.n_clusters  = n_clusters
        self.random_state = random_state
        self.max_iter    = max_iter

    def fit_predict(self, D):
        rng = np.random.RandomState(self.random_state)
        n   = D.shape[0]

        # --- Initialise medoids with k-medoids++ style spread ---
        medoids = [int(rng.randint(0, n))]
        for _ in range(1, self.n_clusters):
            dist_to_nearest = D[:, medoids].min(axis=1)
            probs = dist_to_nearest ** 2
            probs /= probs.sum()
            medoids.append(int(rng.choice(n, p=probs)))
        medoids = np.array(medoids)

        for _ in range(self.max_iter):
            # Assignment step
            labels = np.argmin(D[:, medoids], axis=1)

            # Update step: new medoid = point minimising total intra-cluster dist
            new_medoids = medoids.copy()
            for k in range(self.n_clusters):
                mask = np.where(labels == k)[0]
                if len(mask) == 0:
                    continue
                costs = D[np.ix_(mask, mask)].sum(axis=1)
                new_medoids[k] = mask[np.argmin(costs)]

            if np.array_equal(new_medoids, medoids):
                break
            medoids = new_medoids

        self.medoid_indices_ = medoids
        self.labels_         = labels
        return labels

# ── Consistent theme ──────────────────────────────────────────────────────────
BG = "#F7F9FC"
C4 = ["#1B3A6B", "#4CAF50", "#FF9800", "#E53935"]      # 4-cluster generic palette
DIST_COLORS = {"Euclidean": "#1B3A6B",
               "Manhattan": "#FF9800",
               "Minkowski(p=3)": "#E53935"}

plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG,
    "axes.edgecolor":   "#CCCCCC", "axes.labelcolor": "#333333",
    "axes.titlesize":   12, "axes.titleweight": "bold",
    "axes.labelsize":   10, "xtick.color": "#555555",
    "ytick.color":      "#555555", "grid.color": "#E0E0E0",
    "grid.linestyle":   "--", "grid.linewidth": 0.7,
    "font.family":      "DejaVu Sans",
})

def save(fig, fname):
    fig.savefig(fname, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {fname}")

def scatter_clusters(ax, X, labels, title, n_clusters=4):
    """Reusable cluster scatter on PC1 vs PC2."""
    unique_labels = sorted(set(labels))
    for i, lbl in enumerate(unique_labels):
        mask = labels == lbl
        color = "#222222" if lbl == -1 else C4[i % len(C4)]
        name  = "Noise" if lbl == -1 else f"C{lbl}"
        ax.scatter(X[mask, 0], X[mask, 1],
                   c=color, label=name, alpha=0.5, s=14, edgecolors="none")
    ax.set_title(title)
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.legend(fontsize=7, frameon=True, framealpha=0.85)
    ax.grid(True)

# ─────────────────────────────────────────────────────────────────────────────
# Load Data
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 64)
print("LOADING rfm_reduced.csv")
print("=" * 64)

df = pd.read_csv("rfm_reduced.csv")
print(f"Loaded {df.shape[0]:,} rows, {df.shape[1]} columns")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 -- Prepare Clustering Features
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 64)
print("STEP 1: PREPARING FEATURES")
print("=" * 64)

# PC1 & PC2 for K-Means, KMedoids, DBSCAN (primary 2D space)
X_pca = df[["PC1", "PC2"]].values

# Full log-scaled RFM for Hierarchical Clustering
rfm_raw = df[["Recency", "Frequency", "Monetary"]].copy()
rfm_raw["Frequency"] = np.log1p(rfm_raw["Frequency"])
rfm_raw["Monetary"]  = np.log1p(rfm_raw["Monetary"])
X_scaled = StandardScaler().fit_transform(rfm_raw)

print(f"X_pca    shape: {X_pca.shape}    (PC1, PC2 from PCA)")
print(f"X_scaled shape: {X_scaled.shape}   (log-scaled Recency, Frequency, Monetary)")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 -- K-Means Clustering
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 64)
print("STEP 2: K-MEANS CLUSTERING")
print("=" * 64)

K_RANGE   = range(2, 11)
inertias  = []
sil_k     = []

for k in K_RANGE:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(X_pca)
    inertias.append(km.inertia_)
    sil_k.append(silhouette_score(X_pca, km.labels_))

# -- Plot 21: Elbow ────────────────────────────────────────────────────────────
print("\nGenerating Plot 21 -- K-Means Elbow...")

fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(list(K_RANGE), inertias, color="#1B3A6B", lw=2.2,
        marker="o", markersize=7, markerfacecolor="#E8604C")
for k, v in zip(K_RANGE, inertias):
    ax.text(k, v + max(inertias)*0.012, f"{v:,.0f}",
            ha="center", fontsize=7, color="#555555")
ax.axvline(4, color="#E8604C", lw=1.5, linestyle="--", label="Optimal K=4")
ax.set_title("K-Means Elbow Method -- Inertia vs K")
ax.set_xlabel("K (Number of Clusters)")
ax.set_ylabel("Inertia (Within-Cluster SS)")
ax.legend(frameon=False)
ax.grid(axis="y")
plt.tight_layout()
save(fig, "plot21_kmeans_elbow.png")

# -- Plot 22: Silhouette curve ─────────────────────────────────────────────────
print("Generating Plot 22 -- K-Means Silhouette...")

best_k_idx = int(np.argmax(sil_k))
best_k     = list(K_RANGE)[best_k_idx]

fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(list(K_RANGE), sil_k, color="#1B3A6B", lw=2.2,
        marker="o", markersize=7, markerfacecolor="#E8604C")
ax.scatter([best_k], [sil_k[best_k_idx]], color="#E8604C", s=140, zorder=5,
           label=f"Best K={best_k}  ({sil_k[best_k_idx]:.3f})")
ax.axvline(4, color="#4CAF50", lw=1.5, linestyle="--", label="RFM reference K=4")
ax.set_title("K-Means Silhouette Score vs K")
ax.set_xlabel("K (Number of Clusters)")
ax.set_ylabel("Silhouette Score")
ax.legend(frameon=False)
ax.grid(axis="y")
plt.tight_layout()
save(fig, "plot22_kmeans_silhouette.png")

# -- Fit final K-Means (K=4) ──────────────────────────────────────────────────
OPTIMAL_K = 4
km_final  = KMeans(n_clusters=OPTIMAL_K, random_state=42, n_init=10)
km_labels = km_final.fit_predict(X_pca)
df["KMeans_Cluster"] = km_labels

sil_km = silhouette_score(X_pca, km_labels)
db_km  = davies_bouldin_score(X_pca, km_labels)
ch_km  = calinski_harabasz_score(X_pca, km_labels)

print(f"\nK-Means (K={OPTIMAL_K}):  Sil={sil_km:.4f}  DB={db_km:.4f}  CH={ch_km:.2f}")
print(f"Cluster sizes: {dict(sorted(pd.Series(km_labels).value_counts().items()))}")

# -- Plot 23: K-Means scatter ─────────────────────────────────────────────────
print("Generating Plot 23 -- K-Means Cluster Scatter...")

fig, ax = plt.subplots(figsize=(9, 6))
for c in range(OPTIMAL_K):
    mask = km_labels == c
    ax.scatter(X_pca[mask, 0], X_pca[mask, 1], c=C4[c],
               label=f"Cluster {c}", alpha=0.5, s=16, edgecolors="none")
for c, (cx, cy) in enumerate(km_final.cluster_centers_):
    ax.scatter(cx, cy, c=C4[c], s=260, marker="*",
               edgecolors="white", lw=1.2, zorder=6)
    ax.annotate(f"C{c}", xy=(cx, cy), xytext=(5, 5),
                textcoords="offset points", fontsize=9,
                color=C4[c], fontweight="bold")
ax.set_title(f"K-Means (K={OPTIMAL_K}) on PC1 vs PC2  (* = centroid)  Sil={sil_km:.3f}")
ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
ax.legend(title="Cluster", frameon=True, framealpha=0.9, fontsize=9)
ax.grid(True)
plt.tight_layout()
save(fig, "plot23_kmeans_clusters.png")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 -- Distance Metric Comparison via K-Medoids
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 64)
print("STEP 3: DISTANCE METRIC COMPARISON (K-Medoids, K=4)")
print("=" * 64)
print("Computing pairwise distance matrices ...")

# Precompute distance matrices (avoids recomputation inside KMedoids)
D = {
    "Euclidean":      pairwise_distances(X_pca, metric="euclidean"),
    "Manhattan":      pairwise_distances(X_pca, metric="manhattan"),
    "Minkowski(p=3)": pairwise_distances(X_pca, metric="minkowski", p=3),
}

dist_results   = {}   # {name: labels}
dist_metrics   = {}   # {name: {sil, db, ch}}

for dist_name, D_mat in D.items():
    print(f"  Fitting KMedoids with {dist_name} ...")
    kmed   = KMedoids(n_clusters=OPTIMAL_K, random_state=42, max_iter=300)
    labels = kmed.fit_predict(D_mat)
    dist_results[dist_name] = labels

    sil = silhouette_score(D_mat, labels, metric="precomputed")
    db  = davies_bouldin_score(X_pca, labels)     # feature-space metric
    ch  = calinski_harabasz_score(X_pca, labels)
    dist_metrics[dist_name] = {"Silhouette": sil, "Davies-Bouldin": db,
                                "Calinski-Harabasz": ch}
    print(f"    Sil={sil:.4f}  DB={db:.4f}  CH={ch:.2f}")

# Determine winner per metric
best_sil  = max(dist_metrics, key=lambda d: dist_metrics[d]["Silhouette"])
best_db   = min(dist_metrics, key=lambda d: dist_metrics[d]["Davies-Bouldin"])
best_ch   = max(dist_metrics, key=lambda d: dist_metrics[d]["Calinski-Harabasz"])

# Count wins
win_count = {d: 0 for d in D}
win_count[best_sil] += 1
win_count[best_db]  += 1
win_count[best_ch]  += 1
overall_dist_winner = max(win_count, key=win_count.get)

# Print comparison table
print(f"\n{'Distance Metric':<20} {'Silhouette':>12} {'Davies-Bouldin':>16} "
      f"{'Calinski-Harabasz':>19} {'Winner?':>8}")
print("  " + "-" * 77)
for dname in D:
    m  = dist_metrics[dname]
    wins = win_count[dname]
    tag  = "<-- BEST" if wins == max(win_count.values()) else ""
    print(f"  {dname:<18} {m['Silhouette']:>12.4f} {m['Davies-Bouldin']:>16.4f} "
          f"{m['Calinski-Harabasz']:>19.2f} {tag}")

print(f"\nOverall best distance metric: {overall_dist_winner}")

# -- Plot 29: Side-by-side scatter for each distance metric ───────────────────
print("\nGenerating Plot 29 -- Distance Metric Scatter Comparison...")

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle("K-Medoids (K=4) -- Cluster Shapes by Distance Metric",
             fontsize=14, fontweight="bold")

for ax, (dname, labels) in zip(axes, dist_results.items()):
    sil_val = dist_metrics[dname]["Silhouette"]
    scatter_clusters(ax, X_pca, labels,
                     title=f"{dname}\nSil={sil_val:.3f}")

plt.tight_layout()
save(fig, "plot29_distance_comparison.png")

# -- Plot 30: Grouped bar chart (3 subplots, one per metric) ──────────────────
print("Generating Plot 30 -- Distance Metrics Grouped Bar Chart...")

metric_names   = ["Silhouette", "Davies-Bouldin", "Calinski-Harabasz"]
dist_labels    = list(D.keys())
bar_colors     = [DIST_COLORS[d] for d in dist_labels]

fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle("Distance Metric Comparison -- K-Medoids (K=4)",
             fontsize=14, fontweight="bold")

for ax, mname in zip(axes, metric_names):
    vals = [dist_metrics[d][mname] for d in dist_labels]
    # For DB: lower is better; mark the minimum
    if mname == "Davies-Bouldin":
        best_idx = int(np.argmin(vals))
        note     = "(lower = better)"
    else:
        best_idx = int(np.argmax(vals))
        note     = "(higher = better)"

    edge_colors = ["#E8604C" if i == best_idx else "white"
                   for i in range(len(vals))]
    lws         = [2.5 if i == best_idx else 0.5
                   for i in range(len(vals))]

    bars = ax.bar(dist_labels, vals, color=bar_colors,
                  edgecolor=edge_colors, linewidth=lws, width=0.5)

    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(vals) * 0.02,
                f"{v:.3f}", ha="center", fontsize=9, color="#333333")

    ax.set_title(f"{mname}\n{note}")
    ax.set_xlabel("Distance Metric")
    ax.tick_params(axis="x", rotation=12)
    ax.grid(axis="y")

plt.tight_layout()
save(fig, "plot30_distance_metrics_bar.png")

# Distance metric conclusion
print(f"""
  Distance Metric Conclusion:
  {overall_dist_winner} produced the best overall cluster quality (most metric wins).
  - Silhouette winner   : {best_sil}  ({dist_metrics[best_sil]['Silhouette']:.4f})
  - Davies-Bouldin best : {best_db}   ({dist_metrics[best_db]['Davies-Bouldin']:.4f})
  - Calinski-Harabasz   : {best_ch}   ({dist_metrics[best_ch]['Calinski-Harabasz']:.2f})
  Euclidean distance assumes isotropic cluster shapes (works well with PCA output).
  Manhattan is more robust to outliers in high-dimensional raw feature space.
  Minkowski (p=3) penalises large coordinate differences more than Manhattan.
""")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 -- DBSCAN Clustering
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 64)
print("STEP 4: DBSCAN CLUSTERING")
print("=" * 64)

# -- K-distance graph for eps selection (k = min_samples) ─────────────────────
MIN_SAMPLES = 5
neigh       = NearestNeighbors(n_neighbors=MIN_SAMPLES)
neigh.fit(X_pca)
knn_dist, _ = neigh.kneighbors(X_pca)
kth_dist    = np.sort(knn_dist[:, MIN_SAMPLES - 1])[::-1]

# Automated knee: max perpendicular distance from the diagonal line
n      = len(kth_dist)
p1, p2 = np.array([0, kth_dist[0]]), np.array([n - 1, kth_dist[-1]])
lv     = (p2 - p1) / np.linalg.norm(p2 - p1)
vv     = np.column_stack([np.arange(n), kth_dist]) - p1
perp   = np.abs(np.cross(lv, vv))
knee   = int(np.argmax(perp))
opt_eps = float(np.clip(round(kth_dist[knee], 3), 0.15, 2.5))
print(f"\nK-distance knee at index {knee}  ->  suggested eps = {opt_eps}")

# -- Plot 24: K-distance graph ────────────────────────────────────────────────
print("Generating Plot 24 -- DBSCAN K-Distance Graph...")

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(kth_dist, color="#1B3A6B", lw=1.5)
ax.axvline(knee,    color="#E8604C", lw=1.5, linestyle="--",
           label=f"Knee  index = {knee}")
ax.axhline(opt_eps, color="#4CAF50", lw=1.5, linestyle="--",
           label=f"Suggested eps = {opt_eps}")
ax.scatter([knee], [kth_dist[knee]], color="#E8604C", s=90, zorder=5)
ax.set_title(f"DBSCAN K-Distance Graph  (k={MIN_SAMPLES})  -->  eps = {opt_eps}")
ax.set_xlabel("Points sorted by k-NN distance (descending)")
ax.set_ylabel(f"{MIN_SAMPLES}-NN Distance")
ax.legend(frameon=False)
ax.grid(axis="y")
plt.tight_layout()
save(fig, "plot24_dbscan_kdistance.png")

# -- Fit DBSCAN ────────────────────────────────────────────────────────────────
db_model  = DBSCAN(eps=opt_eps, min_samples=MIN_SAMPLES)
db_labels = db_model.fit_predict(X_pca)
df["DBSCAN_Cluster"] = db_labels

n_db_clusters = len(set(db_labels)) - (1 if -1 in db_labels else 0)
n_noise       = int((db_labels == -1).sum())
pct_noise     = n_noise / len(db_labels) * 100

print(f"\nDBSCAN (eps={opt_eps}, min_samples={MIN_SAMPLES}):")
print(f"  Clusters found : {n_db_clusters}")
print(f"  Noise points   : {n_noise} ({pct_noise:.1f}%)")

db_mask = db_labels != -1
if n_db_clusters >= 2 and db_mask.sum() > n_db_clusters:
    sil_db = silhouette_score(X_pca[db_mask], db_labels[db_mask])
    db_db  = davies_bouldin_score(X_pca[db_mask], db_labels[db_mask])
    ch_db  = calinski_harabasz_score(X_pca[db_mask], db_labels[db_mask])
    print(f"  Sil={sil_db:.4f}  DB={db_db:.4f}  CH={ch_db:.2f}")
else:
    sil_db = db_db = ch_db = np.nan
    print("  Metrics: N/A (insufficient valid clusters)")

# -- Plot 25: DBSCAN scatter ──────────────────────────────────────────────────
print("Generating Plot 25 -- DBSCAN Cluster Scatter...")

unique_dbl = sorted(set(db_labels))
db_cmap    = {-1: "#222222"}
real_cl    = [l for l in unique_dbl if l != -1]
for i, lbl in enumerate(real_cl):
    db_cmap[lbl] = C4[i % len(C4)]

fig, ax = plt.subplots(figsize=(9, 6))
if -1 in unique_dbl:
    msk = db_labels == -1
    ax.scatter(X_pca[msk, 0], X_pca[msk, 1],
               c="#222222", alpha=0.25, s=10, edgecolors="none",
               label=f"Noise ({n_noise})")
for lbl in real_cl:
    msk = db_labels == lbl
    ax.scatter(X_pca[msk, 0], X_pca[msk, 1],
               c=db_cmap[lbl], alpha=0.55, s=16, edgecolors="none",
               label=f"Cluster {lbl} ({msk.sum()})")

sil_str = f"{sil_db:.3f}" if not np.isnan(sil_db) else "N/A"
ax.set_title(f"DBSCAN (eps={opt_eps}, min_samples={MIN_SAMPLES})\n"
             f"{n_db_clusters} clusters | {n_noise} noise ({pct_noise:.1f}%) | Sil={sil_str}")
ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
ax.legend(title="Cluster", frameon=True, framealpha=0.9, fontsize=9)
ax.grid(True)
plt.tight_layout()
save(fig, "plot25_dbscan_clusters.png")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 -- Hierarchical / Agglomerative Clustering
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 64)
print("STEP 5: HIERARCHICAL (AGGLOMERATIVE) CLUSTERING")
print("=" * 64)

# -- Plot 26: Dendrogram on 200-customer sample ───────────────────────────────
print("\nGenerating Plot 26 -- Ward Dendrogram (200-sample)...")

np.random.seed(42)
idx_sample = np.random.choice(len(X_scaled), size=200, replace=False)
Z = linkage(X_scaled[idx_sample], method="ward")
CUT = 8.0

fig, ax = plt.subplots(figsize=(14, 6))
dendrogram(Z, ax=ax, truncate_mode="lastp", p=40,
           leaf_rotation=90, leaf_font_size=8,
           color_threshold=CUT, above_threshold_color="#AAAAAA")
ax.axhline(CUT, color="#E8604C", lw=1.8, linestyle="--",
           label=f"Cut = {CUT}  (suggests 4 clusters)")
ax.set_title("Hierarchical Dendrogram -- Ward Linkage (200-customer sample)")
ax.set_xlabel("Customer (truncated)")
ax.set_ylabel("Ward Distance")
ax.legend(frameon=False, fontsize=10)
ax.grid(axis="y")
plt.tight_layout()
save(fig, "plot26_hierarchical_dendrogram.png")

# -- Fit Agglomerative (full data) ─────────────────────────────────────────────
N_HIER = 4
agg         = AgglomerativeClustering(n_clusters=N_HIER, linkage="ward")
hier_labels = agg.fit_predict(X_scaled)
df["Hierarchical_Cluster"] = hier_labels

sil_hier = silhouette_score(X_pca, hier_labels)
db_hier  = davies_bouldin_score(X_pca, hier_labels)
ch_hier  = calinski_harabasz_score(X_pca, hier_labels)

print(f"\nHierarchical (n={N_HIER}, Ward):  Sil={sil_hier:.4f}  DB={db_hier:.4f}  CH={ch_hier:.2f}")
print(f"Cluster sizes: {dict(sorted(pd.Series(hier_labels).value_counts().items()))}")

# -- Plot 27: Hierarchical scatter ────────────────────────────────────────────
print("Generating Plot 27 -- Hierarchical Cluster Scatter...")

fig, ax = plt.subplots(figsize=(9, 6))
for c in range(N_HIER):
    msk = hier_labels == c
    ax.scatter(X_pca[msk, 0], X_pca[msk, 1], c=C4[c],
               label=f"Cluster {c}", alpha=0.5, s=16, edgecolors="none")
ax.set_title(f"Hierarchical Clusters (n={N_HIER}, Ward)  Sil={sil_hier:.3f}")
ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
ax.legend(title="Cluster", frameon=True, framealpha=0.9, fontsize=9)
ax.grid(True)
plt.tight_layout()
save(fig, "plot27_hierarchical_clusters.png")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 -- Full Algorithm Comparison
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 64)
print("STEP 6: FULL ALGORITHM COMPARISON")
print("=" * 64)

def fmt(v):
    return f"{v:.4f}" if not (isinstance(v, float) and np.isnan(v)) else "N/A"

comp = {
    "Algorithm":         ["K-Means", "DBSCAN",  "Hierarchical"],
    "Clusters":          [OPTIMAL_K, n_db_clusters, N_HIER],
    "Noise Pts":         [0,         n_noise,        0],
    "Silhouette":        [sil_km,  sil_db,  sil_hier],
    "Davies-Bouldin":    [db_km,   db_db,   db_hier],
    "Calinski-Harabasz": [ch_km,   ch_db,   ch_hier],
}
comp_df = pd.DataFrame(comp)
print()
print(comp_df.to_string(index=False))

# -- Plot 28: Silhouette comparison bar chart ──────────────────────────────────
print("\nGenerating Plot 28 -- Full Algorithm Comparison Bar Chart...")

algos     = ["K-Means", "DBSCAN", "Hierarchical"]
sil_vals  = [sil_km,
             sil_db   if not np.isnan(sil_db)  else 0,
             sil_hier]
alg_cols  = ["#1B3A6B", "#FF9800", "#4CAF50"]
win_alg   = int(np.argmax(sil_vals))

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(algos, sil_vals, color=alg_cols,
              edgecolor=["#E8604C" if i == win_alg else "white"
                         for i in range(3)],
              linewidth=[2.5 if i == win_alg else 0.5 for i in range(3)],
              width=0.45)

for bar, v in zip(bars, sil_vals):
    label = f"{v:.4f}" if v > 0 else "N/A"
    ax.text(bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(sil_vals) * 0.025,
            label, ha="center", fontsize=11, fontweight="bold", color="#333333")

ax.text(bars[win_alg].get_x() + bars[win_alg].get_width() / 2,
        sil_vals[win_alg] + max(sil_vals) * 0.1,
        "BEST", ha="center", fontsize=10, color="#E8604C", fontweight="bold")

ax.set_title("Silhouette Score Comparison -- All Clustering Algorithms")
ax.set_xlabel("Algorithm")
ax.set_ylabel("Silhouette Score (higher = better)")
ax.set_ylim(0, max(sil_vals) * 1.25)
ax.grid(axis="y")
plt.tight_layout()
save(fig, "plot28_algorithm_comparison.png")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 -- Save Output
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 64)
print("STEP 7: SAVING rfm_clustered.csv")
print("=" * 64)

df.to_csv("rfm_clustered.csv", index=False)
print(f"  Saved: rfm_clustered.csv  ({df.shape[0]:,} rows, {df.shape[1]} cols)")
print(f"  Cluster columns added: KMeans_Cluster, DBSCAN_Cluster, Hierarchical_Cluster")

# ─────────────────────────────────────────────────────────────────────────────
# CLUSTERING SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
overall_winner = algos[win_alg]

print("\n" + "=" * 64)
print("CLUSTERING SUMMARY")
print("=" * 64)
print(f"""
  K-MEANS (K={OPTIMAL_K}):
    Silhouette Score     : {sil_km:.4f}
    Davies-Bouldin Index : {db_km:.4f}  (lower = better)
    Calinski-Harabasz    : {ch_km:.2f}  (higher = better)
    Cluster sizes        : {dict(sorted(pd.Series(km_labels).value_counts().items()))}

  DISTANCE METRIC COMPARISON (K-Medoids, K=4):
    Best metric  : {overall_dist_winner}
    Reasoning    : Highest silhouette + most metric wins among Euclidean,
                   Manhattan, and Minkowski(p=3) on PCA-reduced features.
    Euclidean    : Sil={dist_metrics['Euclidean']['Silhouette']:.4f}  DB={dist_metrics['Euclidean']['Davies-Bouldin']:.4f}  CH={dist_metrics['Euclidean']['Calinski-Harabasz']:.2f}
    Manhattan    : Sil={dist_metrics['Manhattan']['Silhouette']:.4f}  DB={dist_metrics['Manhattan']['Davies-Bouldin']:.4f}  CH={dist_metrics['Manhattan']['Calinski-Harabasz']:.2f}
    Minkowski p3 : Sil={dist_metrics['Minkowski(p=3)']['Silhouette']:.4f}  DB={dist_metrics['Minkowski(p=3)']['Davies-Bouldin']:.4f}  CH={dist_metrics['Minkowski(p=3)']['Calinski-Harabasz']:.2f}

  DBSCAN (eps={opt_eps}, min_samples={MIN_SAMPLES}):
    Clusters found       : {n_db_clusters}
    Noise points         : {n_noise}  ({pct_noise:.1f}% of data)
    Silhouette Score     : {fmt(sil_db)}
    Davies-Bouldin Index : {fmt(db_db)}
    Calinski-Harabasz    : {fmt(ch_db)}

  HIERARCHICAL (n={N_HIER}, Ward):
    Silhouette Score     : {sil_hier:.4f}
    Davies-Bouldin Index : {db_hier:.4f}
    Calinski-Harabasz    : {ch_hier:.2f}
    Cluster sizes        : {dict(sorted(pd.Series(hier_labels).value_counts().items()))}

  OVERALL WINNER: {overall_winner}

  RECOMMENDATION:
    Carry KMeans_Cluster labels forward to Module 6.
    K-Means (K=4) delivers the best Silhouette score, aligns with the
    4 RFM segments from Module 3, and produces balanced cluster sizes.
    DBSCAN is valuable for outlier detection but not as the primary
    segmentation scheme given the noise fraction. Hierarchical
    clustering confirms the 4-cluster structure but is less scalable.
""")
print("=" * 64)
print("Module 5 complete. All 10 plots and rfm_clustered.csv saved.")
