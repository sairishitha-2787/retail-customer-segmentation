"""
Module 2 — Exploratory Data Analysis (EDA)
Dataset: df_clean.csv (338,151 rows after preprocessing)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# ── Consistent theme ──────────────────────────────────────────────────────────
NAVY   = "#1B3A6B"
CORAL  = "#E8604C"
SILVER = "#B0BEC5"
BG     = "#F7F9FC"

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor":   BG,
    "axes.edgecolor":   "#CCCCCC",
    "axes.labelcolor":  "#333333",
    "axes.titlesize":   14,
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
df["Month"]      = df["InvoiceDate"].dt.to_period("M")
df["DayName"]    = df["InvoiceDate"].dt.day_name()
df["DayOfWeek"]  = df["InvoiceDate"].dt.dayofweek   # 0=Mon
df["Hour"]       = df["InvoiceDate"].dt.hour

print(f"Loaded {df.shape[0]:,} rows, {df.shape[1]} columns\n")

# ─────────────────────────────────────────────────────────────────────────────
# PLOT 1 — Monthly Revenue Trend
# ─────────────────────────────────────────────────────────────────────────────
print("Generating Plot 1 — Monthly Revenue Trend...")

monthly = (df.groupby("Month")["TotalPrice"]
             .sum()
             .reset_index()
             .sort_values("Month"))
monthly["MonthStr"] = monthly["Month"].astype(str)

peak_idx = monthly["TotalPrice"].idxmax()
peak_month = monthly.loc[peak_idx, "MonthStr"]
peak_val   = monthly.loc[peak_idx, "TotalPrice"]

fig, ax = plt.subplots(figsize=(12, 5))
fig.patch.set_facecolor(BG)

ax.plot(monthly["MonthStr"], monthly["TotalPrice"],
        color=NAVY, linewidth=2.2, marker="o", markersize=6,
        markerfacecolor=NAVY, zorder=3, label="Monthly Revenue")

# Highlight peak
ax.scatter([peak_month], [peak_val],
           color=CORAL, s=120, zorder=5, label=f"Peak: {peak_month}")
ax.annotate(f"Peak\n£{peak_val:,.0f}",
            xy=(peak_month, peak_val),
            xytext=(0, 18), textcoords="offset points",
            ha="center", fontsize=9, color=CORAL, fontweight="bold",
            arrowprops=dict(arrowstyle="-", color=CORAL, lw=1.2))

ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"£{x/1000:.0f}k"))
ax.set_title("Monthly Revenue Trend (2010–2011)")
ax.set_xlabel("Month")
ax.set_ylabel("Total Revenue")
ax.tick_params(axis="x", rotation=45)
ax.grid(axis="y")
ax.legend(frameon=False)
plt.tight_layout()
save(fig, "plot1_monthly_revenue.png")

# ─────────────────────────────────────────────────────────────────────────────
# PLOT 2 — Top 10 Countries by Revenue (excluding UK)
# ─────────────────────────────────────────────────────────────────────────────
print("Generating Plot 2 — Top 10 Countries by Revenue...")

country_rev = (df[df["Country"] != "United Kingdom"]
               .groupby("Country")["TotalPrice"]
               .sum()
               .nlargest(10)
               .sort_values())

colors = [CORAL if i == len(country_rev) - 1 else NAVY
          for i in range(len(country_rev))]

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(country_rev.index, country_rev.values, color=colors, edgecolor="white")

for bar, val in zip(bars, country_rev.values):
    ax.text(bar.get_width() + country_rev.max() * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"£{val:,.0f}", va="center", fontsize=9, color="#333333")

ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"£{x/1000:.0f}k"))
ax.set_title("Top 10 Countries by Revenue (Excluding UK)")
ax.set_xlabel("Total Revenue")
ax.set_ylabel("Country")
ax.grid(axis="x")
plt.tight_layout()
save(fig, "plot2_top_countries.png")

# ─────────────────────────────────────────────────────────────────────────────
# PLOT 3 — Top 10 Best Selling Products
# ─────────────────────────────────────────────────────────────────────────────
print("Generating Plot 3 — Top 10 Best Selling Products...")

top_products = (df.groupby("Description")["Quantity"]
                  .sum()
                  .nlargest(10)
                  .sort_values())

# Truncate long names for readability
top_products.index = [d[:45] + "…" if len(d) > 45 else d
                      for d in top_products.index]

colors = [CORAL if i == len(top_products) - 1 else NAVY
          for i in range(len(top_products))]

fig, ax = plt.subplots(figsize=(11, 6))
bars = ax.barh(top_products.index, top_products.values, color=colors, edgecolor="white")

for bar, val in zip(bars, top_products.values):
    ax.text(bar.get_width() + top_products.max() * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{val:,}", va="center", fontsize=9, color="#333333")

ax.set_title("Top 10 Best Selling Products (by Quantity)")
ax.set_xlabel("Total Quantity Sold")
ax.set_ylabel("Product")
ax.grid(axis="x")
plt.tight_layout()
save(fig, "plot3_top_products.png")

# ─────────────────────────────────────────────────────────────────────────────
# PLOT 4 — Revenue by Day of Week
# ─────────────────────────────────────────────────────────────────────────────
print("Generating Plot 4 — Revenue by Day of Week...")

day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
day_rev = (df.groupby("DayName")["TotalPrice"]
             .sum()
             .reindex(day_order))

peak_day = day_rev.idxmax()
bar_colors = [CORAL if d == peak_day else NAVY for d in day_order]

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(day_order, day_rev.values, color=bar_colors, edgecolor="white", width=0.6)

for bar, val in zip(bars, day_rev.values):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + day_rev.max() * 0.01,
            f"£{val/1000:.0f}k", ha="center", fontsize=9, color="#333333")

ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"£{x/1000:.0f}k"))
ax.set_title("Revenue by Day of Week")
ax.set_xlabel("Day")
ax.set_ylabel("Total Revenue")
ax.grid(axis="y")
plt.tight_layout()
save(fig, "plot4_day_of_week.png")

# ─────────────────────────────────────────────────────────────────────────────
# PLOT 5 — Revenue by Hour of Day
# ─────────────────────────────────────────────────────────────────────────────
print("Generating Plot 5 — Revenue by Hour of Day...")

hour_rev = df.groupby("Hour")["TotalPrice"].sum().sort_index()
peak_hour = hour_rev.idxmax()
bar_colors = [CORAL if h == peak_hour else NAVY for h in hour_rev.index]

fig, ax = plt.subplots(figsize=(12, 5))
bars = ax.bar(hour_rev.index, hour_rev.values, color=bar_colors, edgecolor="white", width=0.7)

# Annotate peak
peak_bar = bars[list(hour_rev.index).index(peak_hour)]
ax.annotate(f"Peak\n{peak_hour:02d}:00\n£{hour_rev[peak_hour]/1000:.0f}k",
            xy=(peak_bar.get_x() + peak_bar.get_width() / 2, hour_rev[peak_hour]),
            xytext=(0, 10), textcoords="offset points",
            ha="center", fontsize=9, color=CORAL, fontweight="bold")

ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"£{x/1000:.0f}k"))
ax.set_title("Revenue by Hour of Day")
ax.set_xlabel("Hour (24h)")
ax.set_ylabel("Total Revenue")
ax.set_xticks(hour_rev.index)
ax.set_xticklabels([f"{h:02d}:00" for h in hour_rev.index], rotation=45)
ax.grid(axis="y")
plt.tight_layout()
save(fig, "plot5_hour_of_day.png")

# ─────────────────────────────────────────────────────────────────────────────
# PLOT 6 — Distribution of Order Values
# ─────────────────────────────────────────────────────────────────────────────
print("Generating Plot 6 — Distribution of Order Values...")

cap_95 = df["TotalPrice"].quantile(0.95)
order_vals = df[df["TotalPrice"] <= cap_95]["TotalPrice"]

fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(order_vals, bins=60, color=NAVY, edgecolor="white", linewidth=0.5)
ax.axvline(order_vals.mean(), color=CORAL, linewidth=1.8, linestyle="--",
           label=f"Mean: £{order_vals.mean():.2f}")
ax.axvline(order_vals.median(), color="#F4A261", linewidth=1.8, linestyle=":",
           label=f"Median: £{order_vals.median():.2f}")

ax.set_title("Distribution of Order Values (capped at 95th percentile)")
ax.set_xlabel("Order Value (£)")
ax.set_ylabel("Frequency")
ax.legend(frameon=False)
ax.grid(axis="y")
plt.tight_layout()
save(fig, "plot6_order_distribution.png")

# ─────────────────────────────────────────────────────────────────────────────
# PLOT 7 — UK vs Non-UK Revenue Split
# ─────────────────────────────────────────────────────────────────────────────
print("Generating Plot 7 — UK vs Non-UK Revenue Split...")

uk_rev    = df[df["Country"] == "United Kingdom"]["TotalPrice"].sum()
nonuk_rev = df[df["Country"] != "United Kingdom"]["TotalPrice"].sum()
labels    = ["United Kingdom", "International"]
sizes     = [uk_rev, nonuk_rev]
pie_colors = [NAVY, CORAL]

fig, ax = plt.subplots(figsize=(7, 7))
wedges, texts, autotexts = ax.pie(
    sizes, labels=labels, colors=pie_colors,
    autopct="%1.1f%%", startangle=140,
    wedgeprops={"edgecolor": "white", "linewidth": 2},
    textprops={"fontsize": 12}
)
for at in autotexts:
    at.set_color("white")
    at.set_fontweight("bold")
    at.set_fontsize(13)

ax.set_title("UK vs International Revenue Split")
plt.tight_layout()
save(fig, "plot7_uk_vs_nonuk.png")

# ─────────────────────────────────────────────────────────────────────────────
# PLOT 8 — Number of Orders per Customer
# ─────────────────────────────────────────────────────────────────────────────
print("Generating Plot 8 — Orders per Customer...")

orders_per_customer = df.groupby("CustomerID")["InvoiceNo"].nunique()
cap_95_orders = orders_per_customer.quantile(0.95)
capped_orders = orders_per_customer[orders_per_customer <= cap_95_orders]

fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(capped_orders, bins=40, color=NAVY, edgecolor="white", linewidth=0.5)
ax.axvline(capped_orders.mean(), color=CORAL, linewidth=1.8, linestyle="--",
           label=f"Mean: {capped_orders.mean():.1f} orders")
ax.axvline(capped_orders.median(), color="#F4A261", linewidth=1.8, linestyle=":",
           label=f"Median: {capped_orders.median():.0f} orders")

ax.set_title("Number of Orders per Customer (capped at 95th percentile)")
ax.set_xlabel("Number of Orders")
ax.set_ylabel("Number of Customers")
ax.legend(frameon=False)
ax.grid(axis="y")
plt.tight_layout()
save(fig, "plot8_orders_per_customer.png")

# ─────────────────────────────────────────────────────────────────────────────
# EDA SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
uk_pct    = uk_rev / (uk_rev + nonuk_rev) * 100
nonuk_pct = 100 - uk_pct
top_country = (df[df["Country"] != "United Kingdom"]
               .groupby("Country")["TotalPrice"].sum().idxmax())
top_product = (df.groupby("Description")["Quantity"].sum().idxmax())
avg_order   = df["TotalPrice"].mean()

print("\n" + "=" * 60)
print("EDA SUMMARY")
print("=" * 60)
print(f"""
  Peak revenue month       : {peak_month}  (£{peak_val:,.2f})
  Top country (excl. UK)   : {top_country}
  Top selling product      : {top_product}
  Peak shopping hour       : {peak_hour:02d}:00
  Peak day of week         : {peak_day}
  Average order value      : £{avg_order:.2f}
  UK revenue share         : {uk_pct:.1f}%
  International revenue    : {nonuk_pct:.1f}%
""")
print("=" * 60)
print("All 8 plots saved as PNG files.")
