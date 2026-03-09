"""
Module 1 — Data Loading & Preprocessing
Dataset: UCI Online Retail (Online Retail.xlsx)
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Load Data
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("STEP 1: LOADING DATA")
print("=" * 60)

df = pd.read_excel("Online Retail.xlsx", engine="openpyxl")

print(f"\nShape: {df.shape}")
print(f"\nData Types:\n{df.dtypes}")
print(f"\nFirst 5 Rows:\n{df.head()}")
print(f"\nNull Value Count per Column:\n{df.isnull().sum()}")

rows_before_cleaning = df.shape[0]

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Clean Data
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 2: CLEANING DATA")
print("=" * 60)

# Drop rows where CustomerID is null
df = df.dropna(subset=["CustomerID"])
print(f"\nAfter dropping null CustomerID rows: {df.shape[0]} rows")

# Remove cancellation invoices (InvoiceNo starts with 'C')
df = df[~df["InvoiceNo"].astype(str).str.startswith("C")]
print(f"After removing cancellations (InvoiceNo starts with 'C'): {df.shape[0]} rows")

# Remove rows where Quantity <= 0
df = df[df["Quantity"] > 0]
print(f"After removing Quantity <= 0: {df.shape[0]} rows")

# Remove rows where UnitPrice <= 0
df = df[df["UnitPrice"] > 0]
print(f"After removing UnitPrice <= 0: {df.shape[0]} rows")

# Convert InvoiceDate to datetime
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
print(f"\nInvoiceDate dtype after conversion: {df['InvoiceDate'].dtype}")

rows_after_cleaning = df.shape[0]

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Feature Addition
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 3: ADDING FEATURES")
print("=" * 60)

# Add TotalPrice column
df["TotalPrice"] = df["Quantity"] * df["UnitPrice"]
print(f"\nTotalPrice column added. Sample values:\n{df[['Quantity', 'UnitPrice', 'TotalPrice']].head()}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Outlier Removal (IQR-based)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 4: REMOVING OUTLIERS (IQR METHOD)")
print("=" * 60)

rows_before_outlier = df.shape[0]

for col in ["Quantity", "UnitPrice"]:
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    before = df.shape[0]
    df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
    after = df.shape[0]
    print(f"\n  {col}:")
    print(f"    Q1={Q1:.2f}, Q3={Q3:.2f}, IQR={IQR:.2f}")
    print(f"    Bounds: [{lower_bound:.2f}, {upper_bound:.2f}]")
    print(f"    Rows removed: {before - after}")

rows_after_outlier = df.shape[0]
total_outliers_removed = rows_before_outlier - rows_after_outlier
print(f"\nTotal rows removed as outliers: {total_outliers_removed}")
print(f"Rows remaining after outlier removal: {rows_after_outlier}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — Scaling
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 5: SCALING FEATURES")
print("=" * 60)

scale_cols = ["Quantity", "UnitPrice", "TotalPrice"]

# StandardScaler
standard_scaler = StandardScaler()
df_standard = df.copy()
df_standard[scale_cols] = standard_scaler.fit_transform(df[scale_cols])

print("\n--- StandardScaler (first 5 rows of scaled columns) ---")
print(df_standard[scale_cols].head())

# MinMaxScaler
minmax_scaler = MinMaxScaler()
df_minmax = df.copy()
df_minmax[scale_cols] = minmax_scaler.fit_transform(df[scale_cols])

print("\n--- MinMaxScaler (first 5 rows of scaled columns) ---")
print(df_minmax[scale_cols].head())

# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — Final Summary
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 6: FINAL SUMMARY")
print("=" * 60)

print(f"""
  Rows before cleaning         : {rows_before_cleaning}
  Rows after cleaning          : {rows_after_cleaning}
  Total rows removed (cleaning): {rows_before_cleaning - rows_after_cleaning}
  Total outliers removed       : {total_outliers_removed}
  Final rows in df             : {df.shape[0]}

  Null counts after cleaning:
{df.isnull().sum().to_string()}

  Date range of dataset        : {df['InvoiceDate'].min().date()} to {df['InvoiceDate'].max().date()}
  Number of unique customers   : {df['CustomerID'].nunique()}
  Number of unique products    : {df['StockCode'].nunique()}
  Total revenue (TotalPrice)   : £{df['TotalPrice'].sum():,.2f}
""")

# ─────────────────────────────────────────────────────────────────────────────
# Save cleaned dataframe
# ─────────────────────────────────────────────────────────────────────────────
df.to_csv("df_clean.csv", index=False)
print("Cleaned dataframe saved as df_clean.csv")
print("=" * 60)
