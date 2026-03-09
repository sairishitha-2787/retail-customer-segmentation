"""
Module 7 -- Market Basket Analysis (Apriori)
Datasets: df_clean.csv (transactions) + rfm_final.csv (customer segments)
"""

import warnings
warnings.filterwarnings("ignore")

import sys, subprocess

# Auto-install mlxtend if missing
try:
    from mlxtend.preprocessing import TransactionEncoder
    from mlxtend.frequent_patterns import apriori, association_rules as mlxt_rules
except ImportError:
    print("Installing mlxtend ...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "mlxtend", "-q"])
    from mlxtend.preprocessing import TransactionEncoder
    from mlxtend.frequent_patterns import apriori, association_rules as mlxt_rules

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.cm as cm
import seaborn as sns
import networkx as nx

# ── Theme ─────────────────────────────────────────────────────────────────────
BG = "#F7F9FC"
SEG_ORDER  = ["Champions", "Loyal Customers", "At Risk", "Lost Customers"]
SEG_COLORS = {
    "Champions":       "#F4C542",
    "Loyal Customers": "#4CAF50",
    "At Risk":         "#FF9800",
    "Lost Customers":  "#E53935",
}
SEG_PARAMS = {
    "Champions":       {"min_support": 0.05, "min_lift": 2.0},
    "Loyal Customers": {"min_support": 0.03, "min_lift": 1.5},
    "At Risk":         {"min_support": 0.02, "min_lift": 1.5},
    "Lost Customers":  {"min_support": 0.02, "min_lift": 1.5},
}

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

def trunc(s, n=38):
    """Truncate a string to n characters for display."""
    s = str(s)
    return s[:n] + ".." if len(s) > n else s

def fmt_itemset(itemset):
    """Convert frozenset to a readable string, truncated."""
    items = sorted(list(itemset))
    return " & ".join([trunc(i, 30) for i in items])

def run_apriori(basket_df, min_support, min_lift, label=""):
    """Run apriori + association_rules; return rules DataFrame or empty."""
    try:
        freq = apriori(basket_df, min_support=min_support,
                       use_colnames=True, verbose=0)
        if freq.empty:
            print(f"  [{label}] No frequent itemsets at support={min_support:.3f}")
            return pd.DataFrame(), freq

        rules = mlxt_rules(freq, metric="lift", min_threshold=min_lift)
        rules["antecedents_str"] = rules["antecedents"].apply(fmt_itemset)
        rules["consequents_str"] = rules["consequents"].apply(fmt_itemset)
        return rules.sort_values("lift", ascending=False).reset_index(drop=True), freq
    except Exception as e:
        print(f"  [{label}] Error: {e}")
        return pd.DataFrame(), pd.DataFrame()

def make_basket_df(transactions):
    """Create one-hot encoded basket DataFrame from a transaction DataFrame."""
    # Group each invoice into a list of products
    basket = (transactions.groupby("InvoiceNo")["Description"]
                          .apply(lambda x: list(x.dropna().unique()))
                          .reset_index(drop=True))
    # Remove single-item baskets (no associations possible)
    basket = basket[basket.apply(len) > 1]
    if basket.empty:
        return pd.DataFrame()
    te       = TransactionEncoder()
    te_array = te.fit_transform(basket)
    return pd.DataFrame(te_array, columns=te.columns_)

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 -- Prepare Transaction Data
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 64)
print("STEP 1: LOADING & PREPARING DATA")
print("=" * 64)

df_tx  = pd.read_csv("df_clean.csv",  parse_dates=["InvoiceDate"])
df_rfm = pd.read_csv("rfm_final.csv")[["CustomerID", "Cluster_Label"]]

# Merge to attach Cluster_Label to every transaction row
df_tx["CustomerID"] = df_tx["CustomerID"].astype(float)
df_rfm["CustomerID"] = df_rfm["CustomerID"].astype(float)
df = df_tx.merge(df_rfm, on="CustomerID", how="left")
df["Description"] = df["Description"].str.strip().str.upper()
df.dropna(subset=["Description", "Cluster_Label"], inplace=True)

print(f"Transactions loaded   : {len(df_tx):,}")
print(f"After segment merge   : {len(df):,}")
print(f"Unique invoices       : {df['InvoiceNo'].nunique():,}")
print(f"Unique products       : {df['Description'].nunique():,}")

# Global basket matrix (all customers)
print("\nBuilding global basket matrix ...")
basket_global = make_basket_df(df)
print(f"Global basket shape   : {basket_global.shape}  "
      f"(invoices x products)")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 -- Global Apriori (All Customers)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 64)
print("STEP 2: GLOBAL APRIORI  (min_support=0.02, min_lift=1.5)")
print("=" * 64)

rules_global, freq_global = run_apriori(basket_global,
                                        min_support=0.02, min_lift=1.5,
                                        label="Global")

print(f"\nFrequent itemsets found : {len(freq_global):,}")
print(f"Association rules found : {len(rules_global):,}")

if not rules_global.empty:
    top15 = rules_global.head(15)
    print(f"\nTop 15 rules by lift:")
    print(f"  {'Antecedent':<40} {'Consequent':<40} "
          f"{'Support':>8} {'Conf':>6} {'Lift':>6}")
    print("  " + "-" * 104)
    for _, row in top15.iterrows():
        print(f"  {row['antecedents_str']:<40} {row['consequents_str']:<40} "
              f"{row['support']:>8.4f} {row['confidence']:>6.3f} {row['lift']:>6.3f}")

    rules_global.to_csv("association_rules_global.csv", index=False)
    print(f"\n  Saved: association_rules_global.csv")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 -- Per-Cluster Apriori
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 64)
print("STEP 3: PER-CLUSTER APRIORI")
print("=" * 64)

cluster_rules  = {}      # {label: rules_df}
cluster_basket = {}      # {label: basket_df}
SAVE_NAMES = {
    "Champions":       "rules_champions.csv",
    "Loyal Customers": "rules_loyal.csv",
    "At Risk":         "rules_atrisk.csv",
    "Lost Customers":  "rules_lost.csv",
}

for seg in SEG_ORDER:
    params = SEG_PARAMS[seg]
    seg_tx = df[df["Cluster_Label"] == seg]
    print(f"\n  --- {seg} ---")
    print(f"  Transactions  : {len(seg_tx):,}")
    print(f"  Unique invoices: {seg_tx['InvoiceNo'].nunique():,}")
    print(f"  min_support={params['min_support']}  min_lift={params['min_lift']}")

    basket_seg = make_basket_df(seg_tx)
    if basket_seg.empty:
        print(f"  No multi-item baskets found for {seg}.")
        cluster_rules[seg]  = pd.DataFrame()
        cluster_basket[seg] = pd.DataFrame()
        continue

    cluster_basket[seg] = basket_seg
    print(f"  Basket shape  : {basket_seg.shape}")

    rules_seg, freq_seg = run_apriori(basket_seg,
                                      min_support=params["min_support"],
                                      min_lift=params["min_lift"],
                                      label=seg)

    # Fallback: lower support if no rules found
    if rules_seg.empty and not freq_seg.empty:
        fallback_sup = params["min_support"] / 2
        print(f"  No rules -- retrying with min_support={fallback_sup:.3f} ...")
        rules_seg, _ = run_apriori(basket_seg,
                                   min_support=fallback_sup,
                                   min_lift=1.2, label=seg + " fallback")

    cluster_rules[seg] = rules_seg
    print(f"  Frequent itemsets : {len(freq_seg):,}")
    print(f"  Association rules : {len(rules_seg):,}")

    if not rules_seg.empty:
        print(f"  Top 5 rules by lift:")
        for _, row in rules_seg.head(5).iterrows():
            print(f"    [{row['antecedents_str']}] -> [{row['consequents_str']}]"
                  f"  support={row['support']:.4f}"
                  f"  confidence={row['confidence']:.3f}"
                  f"  lift={row['lift']:.3f}")
        rules_seg.to_csv(SAVE_NAMES[seg], index=False)
        print(f"  Saved: {SAVE_NAMES[seg]}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 -- Visualizations
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 64)
print("STEP 4: GENERATING VISUALIZATIONS")
print("=" * 64)

# ── Plot 39: Top 15 global rules by lift ─────────────────────────────────────
print("\nGenerating Plot 39 -- Top 15 Global Rules (Lift)...")

if not rules_global.empty:
    plot_rules = rules_global.head(15).copy()
    plot_rules["rule"] = (plot_rules["antecedents_str"].apply(lambda x: trunc(x, 30))
                          + "  ->  "
                          + plot_rules["consequents_str"].apply(lambda x: trunc(x, 30)))
    plot_rules = plot_rules.sort_values("lift")

    cmap_lift = plt.cm.YlOrRd
    colors    = [cmap_lift(v) for v in
                 (plot_rules["lift"] - plot_rules["lift"].min()) /
                 (plot_rules["lift"].max() - plot_rules["lift"].min() + 1e-9)]

    fig, ax = plt.subplots(figsize=(13, 7))
    bars = ax.barh(plot_rules["rule"], plot_rules["lift"],
                   color=colors, edgecolor="white")
    for bar, v in zip(bars, plot_rules["lift"]):
        ax.text(v + 0.02, bar.get_y() + bar.get_height() / 2,
                f"{v:.2f}", va="center", fontsize=8.5, color="#333333")

    sm = plt.cm.ScalarMappable(cmap=cmap_lift,
                               norm=plt.Normalize(plot_rules["lift"].min(),
                                                  plot_rules["lift"].max()))
    plt.colorbar(sm, ax=ax, label="Lift")
    ax.set_title("Top 15 Global Association Rules by Lift")
    ax.set_xlabel("Lift")
    ax.set_ylabel("")
    ax.grid(axis="x")
    plt.tight_layout()
    save(fig, "plot39_global_rules_lift.png")

# ── Plot 40: Support vs Confidence scatter, bubble = lift ─────────────────────
print("Generating Plot 40 -- Support vs Confidence Scatter...")

if not rules_global.empty:
    plot_r = rules_global.head(80).copy()
    lift_norm = (plot_r["lift"] - plot_r["lift"].min()) / \
                (plot_r["lift"].max() - plot_r["lift"].min() + 1e-9)

    fig, ax = plt.subplots(figsize=(10, 7))
    sc = ax.scatter(plot_r["support"], plot_r["confidence"],
                    s=plot_r["lift"] * 60,
                    c=plot_r["lift"], cmap="YlOrRd",
                    alpha=0.7, edgecolors="#555555", linewidth=0.4)
    plt.colorbar(sc, ax=ax, label="Lift")
    ax.set_title("Support vs Confidence  (bubble size = lift)")
    ax.set_xlabel("Support")
    ax.set_ylabel("Confidence")
    ax.grid(True)
    plt.tight_layout()
    save(fig, "plot40_support_confidence_scatter.png")

# ── Plot 41: Lift heatmap top 10 antecedents x top 10 consequents ─────────────
print("Generating Plot 41 -- Rules Heatmap...")

if not rules_global.empty:
    # Filter to 1-item antecedent AND 1-item consequent for a clean heatmap
    r1 = rules_global[
        (rules_global["antecedents"].apply(len) == 1) &
        (rules_global["consequents"].apply(len) == 1)
    ].copy()

    if not r1.empty:
        r1["ant"] = r1["antecedents"].apply(lambda x: trunc(list(x)[0], 32))
        r1["con"] = r1["consequents"].apply(lambda x: trunc(list(x)[0], 32))

        top_ants = r1.groupby("ant")["lift"].mean().nlargest(10).index.tolist()
        top_cons = r1.groupby("con")["lift"].mean().nlargest(10).index.tolist()
        r1f = r1[r1["ant"].isin(top_ants) & r1["con"].isin(top_cons)]

        if not r1f.empty:
            hm = r1f.pivot_table(index="ant", columns="con",
                                 values="lift", aggfunc="max")
            hm = hm.reindex(index=top_ants, columns=top_cons)

            fig, ax = plt.subplots(figsize=(13, 8))
            sns.heatmap(hm, annot=True, fmt=".2f", cmap="YlOrRd",
                        linewidths=0.4, linecolor="#CCCCCC",
                        annot_kws={"size": 8}, ax=ax,
                        cbar_kws={"label": "Lift"},
                        mask=hm.isna())
            ax.set_title("Lift Heatmap: Top 10 Antecedents vs Top 10 Consequents\n"
                         "(single-item rules only)")
            ax.set_xlabel("Consequent")
            ax.set_ylabel("Antecedent")
            ax.tick_params(axis="x", rotation=35)
            ax.tick_params(axis="y", rotation=0)
            plt.tight_layout()
            save(fig, "plot41_rules_heatmap.png")
        else:
            print("  Skipping heatmap -- insufficient filtered rules.")
    else:
        print("  Skipping heatmap -- no 1->1 rules found.")

# ── Plot 42: Top 5 rules per cluster (4 subplots) ─────────────────────────────
print("Generating Plot 42 -- Rules per Cluster...")

fig, axes = plt.subplots(2, 2, figsize=(18, 12))
fig.suptitle("Top 5 Association Rules by Lift per Customer Segment",
             fontsize=14, fontweight="bold")
axes_flat = axes.flatten()

for ax, seg in zip(axes_flat, SEG_ORDER):
    rules_s = cluster_rules.get(seg, pd.DataFrame())
    ax.set_facecolor(BG)
    color = SEG_COLORS[seg]

    if rules_s.empty:
        ax.text(0.5, 0.5, f"No rules found\nfor {seg}",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=12, color="#888888")
        ax.set_title(f"{seg}  (no rules)")
        continue

    top5 = rules_s.head(5).copy()
    top5["rule"] = (top5["antecedents_str"].apply(lambda x: trunc(x, 24))
                    + " -> "
                    + top5["consequents_str"].apply(lambda x: trunc(x, 24)))
    top5 = top5.sort_values("lift")

    bars = ax.barh(top5["rule"], top5["lift"],
                   color=color, edgecolor="white", alpha=0.88)
    for bar, v in zip(bars, top5["lift"]):
        ax.text(v + top5["lift"].max() * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{v:.2f}", va="center", fontsize=8.5, color="#333333")

    ax.set_title(f"{seg}  ({len(rules_s)} rules total)")
    ax.set_xlabel("Lift")
    ax.grid(axis="x")

plt.tight_layout()
save(fig, "plot42_rules_per_cluster.png")

# ── Plot 43: Network graph of top 20 global rules ─────────────────────────────
print("Generating Plot 43 -- Network Graph...")

if not rules_global.empty:
    top_net = rules_global.head(20).copy()

    G = nx.DiGraph()
    for _, row in top_net.iterrows():
        ant = fmt_itemset(row["antecedents"])
        con = fmt_itemset(row["consequents"])
        G.add_edge(trunc(ant, 28), trunc(con, 28),
                   weight=row["lift"], confidence=row["confidence"])

    fig, ax = plt.subplots(figsize=(16, 11))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    pos = nx.spring_layout(G, seed=42, k=2.2)

    # Edge colors and widths scaled by lift
    edges    = G.edges(data=True)
    lifts    = [d["weight"] for _, _, d in edges]
    max_lift = max(lifts) if lifts else 1
    edge_widths = [1.5 + (l / max_lift) * 5 for l in lifts]
    edge_colors = [plt.cm.YlOrRd(l / max_lift) for l in lifts]

    nx.draw_networkx_nodes(G, pos, ax=ax,
                           node_color="#1B3A6B", node_size=1200, alpha=0.85)
    nx.draw_networkx_edges(G, pos, ax=ax,
                           width=edge_widths, edge_color=edge_colors,
                           arrows=True, arrowsize=20,
                           connectionstyle="arc3,rad=0.1",
                           min_source_margin=20, min_target_margin=20)
    nx.draw_networkx_labels(G, pos, ax=ax,
                            font_size=7.5, font_color="white",
                            font_weight="bold")

    sm = plt.cm.ScalarMappable(cmap=plt.cm.YlOrRd,
                               norm=plt.Normalize(min(lifts), max(lifts)))
    plt.colorbar(sm, ax=ax, label="Lift", shrink=0.6)
    ax.set_title("Product Association Network (Top 20 Rules)\n"
                 "edge thickness = lift  |  arrow = rule direction",
                 fontsize=13, fontweight="bold")
    ax.axis("off")
    plt.tight_layout()
    save(fig, "plot43_rules_network.png")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 -- Business Insights per Cluster
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 64)
print("STEP 5: BUSINESS INSIGHTS PER CLUSTER")
print("=" * 64)

cross_sell_strategy = {
    "Champions":
        "Bundle top associated products as a premium gift set or loyalty reward pack.",
    "Loyal Customers":
        "Use email recommendation engine: 'Customers who bought X also bought Y'.",
    "At Risk":
        "Include a complementary product sample or discount voucher for associated item.",
    "Lost Customers":
        "Re-activation bundle: pair popular item with its strongest associate at 20% off.",
}

for seg in SEG_ORDER:
    rules_s = cluster_rules.get(seg, pd.DataFrame())
    print(f"\n  {'-' * 54}")
    print(f"  Cluster    : {seg}")
    if not rules_s.empty:
        top_r = rules_s.iloc[0]
        print(f"  Top pair   : [{top_r['antecedents_str']}]")
        print(f"            -> [{top_r['consequents_str']}]")
        print(f"  Lift={top_r['lift']:.3f}  Conf={top_r['confidence']:.3f}  "
              f"Support={top_r['support']:.4f}")
    else:
        print("  No significant rules found.")
    print(f"  Strategy   : {cross_sell_strategy[seg]}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 -- Save Output
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 64)
print("STEP 6: SAVING rules_summary.csv")
print("=" * 64)

summary_parts = []
for seg in SEG_ORDER:
    rules_s = cluster_rules.get(seg, pd.DataFrame())
    if not rules_s.empty:
        top5 = rules_s.head(5).copy()
        top5["Cluster"] = seg
        summary_parts.append(top5[["Cluster", "antecedents_str",
                                    "consequents_str", "support",
                                    "confidence", "lift"]])

if summary_parts:
    rules_summary = pd.concat(summary_parts, ignore_index=True)
    rules_summary.columns = ["Cluster", "Antecedent", "Consequent",
                               "Support", "Confidence", "Lift"]
    rules_summary.to_csv("rules_summary.csv", index=False)
    print(f"  Saved: rules_summary.csv  ({len(rules_summary)} rows)")

# ─────────────────────────────────────────────────────────────────────────────
# MARKET BASKET SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 64)
print("MARKET BASKET SUMMARY")
print("=" * 64)

# Most frequently appearing product across global rules
if not rules_global.empty:
    all_items = []
    for _, row in rules_global.iterrows():
        all_items.extend(list(row["antecedents"]) + list(row["consequents"]))
    from collections import Counter
    top_products = Counter(all_items).most_common(3)

    print(f"\n  Global frequent itemsets  : {len(freq_global):,}")
    print(f"  Global association rules  : {len(rules_global):,}")

    print(f"\n  Top 3 product associations overall (by lift):")
    for i, row in rules_global.head(3).iterrows():
        print(f"    [{row['antecedents_str']}] -> [{row['consequents_str']}]  "
              f"lift={row['lift']:.3f}")

    print(f"\n  Most frequently appearing products in rules:")
    for prod, cnt in top_products:
        print(f"    {trunc(prod, 45):<47}: appears in {cnt} rules")

print(f"\n  Rules per cluster:")
for seg in SEG_ORDER:
    n = len(cluster_rules.get(seg, pd.DataFrame()))
    print(f"    {seg:<22}: {n:>4} rules")

print(f"\n  Strongest rule per cluster:")
for seg in SEG_ORDER:
    rules_s = cluster_rules.get(seg, pd.DataFrame())
    if not rules_s.empty:
        r = rules_s.iloc[0]
        print(f"    {seg:<22}: [{trunc(r['antecedents_str'],28)}] -> "
              f"[{trunc(r['consequents_str'],28)}]  lift={r['lift']:.3f}")
    else:
        print(f"    {seg:<22}: No rules found")

print(f"\n  Cross-sell recommendation per cluster:")
for seg in SEG_ORDER:
    rules_s = cluster_rules.get(seg, pd.DataFrame())
    rec = cross_sell_strategy[seg]
    if not rules_s.empty:
        r = rules_s.iloc[0]
        print(f"    {seg:<22}: Promote '{trunc(r['consequents_str'],30)}' "
              f"alongside '{trunc(r['antecedents_str'],30)}'")
    else:
        print(f"    {seg:<22}: {rec[:60]}")

print("\n" + "=" * 64)
print("Module 7 complete. All 5 plots and CSV files saved.")
