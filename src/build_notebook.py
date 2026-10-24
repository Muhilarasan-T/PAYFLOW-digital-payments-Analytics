"""
PAYFLOW — Programmatic Jupyter Notebook Builder
Builds notebooks/phase4_exploratory_data_analysis.ipynb using nbformat v4.
"""

import nbformat as nbf

nb = nbf.v4.new_notebook()

cells = []

# Title & Metadata
cells.append(nbf.v4.new_markdown_cell("""# PAYFLOW — Phase 4: Exploratory Data Analysis & Insight Discovery

**Project:** PAYFLOW — Digital Payments Intelligence & Trends Analysis  
**Phase:** Phase 4 — Exploratory Data Analysis & Python Modeling  
**Primary Dataset:** Reserve Bank of India (RBI) Payment System Indicators (Nov 2019 – Jul 2026)  
**Author:** PAYFLOW Data Analytics Team  
**Date:** October 2026  

---

## 1. Executive Summary & Objective

The objective of Phase 4 is to perform a rigorous, forensic Exploratory Data Analysis (EDA) on India's payment systems from **November 2019 to July 2026 (81 consecutive months)** using the cleaned and normalized datasets generated in Phase 2.

This notebook analyzes:
1. **Data Profiling & Quality Audit:** Validating completeness, temporal continuity, and anomaly exclusions.
2. **Payment Adoption & Market Share:** Quantifying UPI's expansion in volume ($39.7\% \to 86.8\%$) and value ($6.2\% \to 30.3\%$).
3. **Volume vs. Value vs. Ticket Size:** Analyzing ticket-size polarization across micro-retail (UPI), mid-tier (IMPS), bulk corporate (NEFT), and wholesale (RTGS) rails.
4. **Channel Growth & Seasonality:** Calculating MoM and YoY momentum, fiscal surges (March), and festive quarters (Oct–Nov).
5. **Card Payments & E-Commerce:** Analyzing the credit-to-debit divergence and e-commerce penetration ($62.8\%$ online share for credit cards).
6. **Acceptance Infrastructure & Cash Displacement:** Examining the $80:1$ multiplier of QR codes over PoS machines, and the plateauing of ATM cash withdrawals.
"""))

# Cell 2: Imports & Environment Setup
cells.append(nbf.v4.new_code_cell("""import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import seaborn as sns

from src.phase4_eda import (
    load_cleaned_data,
    get_upi_retail_share,
    get_annual_summary,
    get_rail_ats_comparison,
    get_card_spend_divergence,
    get_infrastructure_trajectory,
    get_cash_vs_digital,
    apply_chart_style
)

apply_chart_style()
print("Libraries imported and styling applied successfully.")
"""))

# Cell 3: Data Ingestion & Profiling
cells.append(nbf.v4.new_markdown_cell("""---
## 2. Data Profile & Temporal Coverage

We load the four processed deliverables from Phase 2:
- `data/processed/transaction_indicators.csv` (4,617 rows, 57 indicators)
- `data/processed/infrastructure_indicators.csv` (1,053 rows, 13 indicators)
- `data/processed/data_dictionary.csv` (145 columns documented)
- `data/processed/cleaning_exceptions.csv` (36 anomalies registered)
"""))

cells.append(nbf.v4.new_code_cell("""df_trans, df_infra, df_dict, df_exc = load_cleaned_data()

print(f"Transaction Indicators:    {df_trans.shape[0]:,} rows, {df_trans.shape[1]} columns")
print(f"Infrastructure Indicators: {df_infra.shape[0]:,} rows, {df_infra.shape[1]} columns")
print(f"Data Dictionary Records:   {df_dict.shape[0]:,} rows, {df_dict.shape[1]} columns")
print(f"Documented Exceptions:     {df_exc.shape[0]:,} rows, {df_exc.shape[1]} columns")

min_date = df_trans['month_date'].min().strftime('%Y-%m-%d')
max_date = df_trans['month_date'].max().strftime('%Y-%m-%d')
distinct_months = df_trans['month_date'].nunique()
print(f"Temporal Span:             {min_date} to {max_date} ({distinct_months} consecutive months)")
"""))

# Cell 4: Annual UPI Share Table
cells.append(nbf.v4.new_markdown_cell("""---
## 3. UPI Adoption & Retail Payment Market Share

We evaluate UPI's growth against total retail payments across all 81 months.
> **Note on Partial Years:** 2019 contains 2 months (Nov–Dec); 2026 contains 7 months (Jan–Jul). Direct comparisons with complete 12-month calendar years are explicitly qualified.
"""))

cells.append(nbf.v4.new_code_cell("""df_share = get_upi_retail_share(df_trans)
df_ann = get_annual_summary(df_trans)

cols_to_show = ["year", "months_observed", "period_qualification", 
                "annual_upi_vol_billions", "annual_retail_vol_billions", "upi_vol_share_pct",
                "annual_upi_val_trillions", "annual_retail_val_trillions", "upi_val_share_pct"]

df_ann[cols_to_show].round(2)
"""))

# Cell 5: Chart 1
cells.append(nbf.v4.new_markdown_cell("""### Chart 1: UPI Volume & Value Share Trajectory
The chart below highlights how UPI surpassed 50% volume share in late 2020 and crossed 85% by 2025.
"""))

cells.append(nbf.v4.new_code_cell("""fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

ax1.plot(df_share["month_date"], df_share["upi_vol_share_pct"], color="#1A365D", lw=2.5, label="UPI Volume Share (%)")
ax1.fill_between(df_share["month_date"], df_share["upi_vol_share_pct"], color="#2B6CB0", alpha=0.15)
ax1.axhline(50, color="#2D3748", ls=":", lw=1, alpha=0.6)
ax1.text(df_share["month_date"].iloc[12], 52, "50% Volume Mark (Late 2020)", fontsize=8.5, color="#2D3748")
ax1.set_ylabel("Volume Share (%)")
ax1.set_title("A. UPI Penetration in Retail Payment Volume (Lakh Transactions)", loc="left", fontsize=11, weight="bold")
ax1.set_ylim(30, 95)
ax1.legend(loc="upper left")

ax2.plot(df_share["month_date"], df_share["upi_val_share_pct"], color="#DD6B20", lw=2.5, label="UPI Value Share (%)")
ax2.fill_between(df_share["month_date"], df_share["upi_val_share_pct"], color="#DD6B20", alpha=0.15)
ax2.set_ylabel("Value Share (%)")
ax2.set_title("B. UPI Penetration in Retail Payment Value (INR Crores)", loc="left", fontsize=11, weight="bold")
ax2.set_ylim(0, 35)
ax2.xaxis.set_major_locator(mdates.YearLocator())
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax2.legend(loc="upper left")

fig.suptitle("PAYFLOW — UPI Retail Payments Market Share Trajectory (2019–2026)", fontsize=13, weight="bold", y=0.99)
plt.show()
"""))

# Cell 6: Average Ticket Size Analysis
cells.append(nbf.v4.new_markdown_cell("""---
## 4. Payment Rail Segmentation by Average Ticket Size (ATS)

Average Ticket Size (ATS) reveals how payment rails serve distinct economic use cases:
$$\\text{ATS (INR)} = \\frac{\\text{Value in ₹ Crores} \\times 10^7}{\\text{Volume in Lakh} \\times 10^5} = \\frac{\\text{Value}}{\\text{Volume}} \\times 100$$
"""))

cells.append(nbf.v4.new_code_cell("""df_ats = get_rail_ats_comparison(df_trans)

# Sample ticket sizes in July 2026 vs November 2019
jul26 = df_ats[df_ats["month_date"] == "2026-07-01"].iloc[0]
nov19 = df_ats[df_ats["month_date"] == "2019-11-01"].iloc[0]

ats_compare = pd.DataFrame({
    "Payment Rail": ["UPI", "Debit Cards", "Credit Cards", "IMPS", "NEFT", "CTS Cheques", "RTGS Customer"],
    "Nov-2019 ATS (INR)": [nov19["UPI"], nov19["DEBIT_CARDS_TOTAL"], nov19["CREDIT_CARDS_TOTAL"], 
                           nov19["IMPS"], nov19["NEFT"], nov19["PAPER_CTS"], nov19["RTGS_CUSTOMER"]],
    "Jul-2026 ATS (INR)": [jul26["UPI"], jul26["DEBIT_CARDS_TOTAL"], jul26["CREDIT_CARDS_TOTAL"], 
                           jul26["IMPS"], jul26["NEFT"], jul26["PAPER_CTS"], jul26["RTGS_CUSTOMER"]]
})
ats_compare["Change (%)"] = ((ats_compare["Jul-2026 ATS (INR)"] - ats_compare["Nov-2019 ATS (INR)"]) / ats_compare["Nov-2019 ATS (INR)"]) * 100.0
ats_compare.round(2)
"""))

# Cell 7: Chart 3
cells.append(nbf.v4.new_markdown_cell("""### Chart 3: Payment Rail Average Ticket Size Comparison (Log Scale)
"""))

cells.append(nbf.v4.new_code_cell("""fig, ax = plt.subplots(figsize=(10, 6))

colors = {
    "RTGS_CUSTOMER": "#C53030",
    "NEFT": "#6B46C1",
    "PAPER_CTS": "#2D3748",
    "IMPS": "#2C7A7B",
    "CREDIT_CARDS_TOTAL": "#DD6B20",
    "DEBIT_CARDS_TOTAL": "#2B6CB0",
    "UPI": "#276749"
}
labels = {
    "RTGS_CUSTOMER": "RTGS Customer (~₹6M)",
    "NEFT": "NEFT (~₹52,000)",
    "PAPER_CTS": "CTS Cheques (~₹144,000)",
    "IMPS": "IMPS (~₹19,500)",
    "CREDIT_CARDS_TOTAL": "Credit Cards (~₹3,400)",
    "DEBIT_CARDS_TOTAL": "Debit Cards (~₹2,400)",
    "UPI": "UPI (~₹1,260)"
}

for rail, col in colors.items():
    if rail in df_ats.columns:
        ax.plot(df_ats["month_date"], df_ats[rail], label=labels[rail], color=col, lw=2.2 if rail in ["UPI", "NEFT"] else 1.8)

ax.set_yscale("log")
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"₹{int(y):,}"))
ax.set_ylabel("Average Ticket Size (INR) — Logarithmic Scale")
ax.set_title("PAYFLOW — Payment Rail Use-Case Polarization by Ticket Size (2019–2026)", fontsize=13, weight="bold")
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=True)
plt.show()
"""))

# Cell 8: Card Payments Divergence
cells.append(nbf.v4.new_markdown_cell("""---
## 5. Card Payments: Credit vs. Debit & E-Commerce Penetration

We examine how credit cards overtook debit cards in transaction value, and how e-commerce (card-not-present) became the dominant credit card channel.
"""))

cells.append(nbf.v4.new_code_cell("""df_cards = get_card_spend_divergence(df_trans)

df_cards["year"] = df_cards["month_date"].dt.year
card_annual = df_cards.groupby("year").agg({
    "cc_total_val_cr": "sum",
    "dc_total_val_cr": "sum",
    "cc_ecom_val_cr": "sum",
    "dc_ecom_val_cr": "sum"
})
card_annual["cc_ecom_share_pct"] = (card_annual["cc_ecom_val_cr"] / card_annual["cc_total_val_cr"]) * 100.0
card_annual["dc_ecom_share_pct"] = (card_annual["dc_ecom_val_cr"] / card_annual["dc_total_val_cr"]) * 100.0
card_annual["credit_to_debit_ratio"] = card_annual["cc_total_val_cr"] / card_annual["dc_total_val_cr"]

card_annual[["cc_total_val_cr", "dc_total_val_cr", "cc_ecom_share_pct", "dc_ecom_share_pct", "credit_to_debit_ratio"]].round(2)
"""))

# Cell 9: Acceptance Infrastructure
cells.append(nbf.v4.new_markdown_cell("""---
## 6. Physical Infrastructure & QR Code Multiplication

Comparison of capital-intensive Point-of-Sale (PoS) machines versus low-cost static UPI QR codes.
"""))

cells.append(nbf.v4.new_code_cell("""df_infra_trends = get_infrastructure_trajectory(df_infra)

# March fiscal year-end snapshots
march_snaps = df_infra_trends[df_infra_trends["month_date"].dt.month == 3].copy()
march_snaps["year"] = march_snaps["month_date"].dt.year
march_snaps[["year", "pos_terminals_lakh", "bharat_qr_lakh", "upi_qr_static_lakh", "qr_to_pos_ratio"]].round(2)
"""))

# Cell 10: Cash vs Digital
cells.append(nbf.v4.new_markdown_cell("""---
## 7. Cash Withdrawals vs. Total Digital Payment Growth

ATM cash withdrawals plateaued while digital payments multiplied, causing the cash-to-digital ratio to drop from $2.38\%$ in 2020 to $0.78\%$ in 2026.
"""))

cells.append(nbf.v4.new_code_cell("""df_cash = get_cash_vs_digital(df_trans)

df_cash["year"] = df_cash["month_date"].dt.year
cash_ann = df_cash.groupby("year").agg({
    "atm_cash_val_cr": "sum",
    "digital_val_cr": "sum",
    "atm_cash_vol_lakh": "sum"
})
cash_ann["cash_to_digital_pct"] = (cash_ann["atm_cash_val_cr"] / cash_ann["digital_val_cr"]) * 100.0
cash_ann["avg_atm_withdrawal_inr"] = (cash_ann["atm_cash_val_cr"] * 100.0) / cash_ann["atm_cash_vol_lakh"]
cash_ann[["atm_cash_val_cr", "digital_val_cr", "cash_to_digital_pct", "avg_atm_withdrawal_inr"]].round(2)
"""))

# Cell 11: Validation vs Phase 3 SQL Results
cells.append(nbf.v4.new_markdown_cell("""---
## 8. Python-to-SQL Cross-Verification

We cross-verify Python calculations against Phase 3 MySQL query results to guarantee mathematical reproducibility.
"""))

cells.append(nbf.v4.new_code_cell("""import sqlite3

conn = sqlite3.connect("data/processed/payflow.db")

sql_upi_2025 = pd.read_sql_query(\"\"\"
SELECT 
    ROUND(SUM(volume_lakh) / 10000.0, 2) AS sql_vol_billion,
    ROUND(SUM(value_inr_crore) / 100000.0, 2) AS sql_val_trillion
FROM fact_transaction_indicators
WHERE indicator_code = 'UPI' AND strftime('%Y', month_date) = '2025';
\"\"\", conn)

py_upi_2025_vol = round(df_share[df_share["month_date"].dt.year == 2025]["upi_vol_billion"].sum(), 2)
py_upi_2025_val = round(df_share[df_share["month_date"].dt.year == 2025]["upi_val_trillion"].sum(), 2)

print(f"2025 UPI Volume: SQL={sql_upi_2025['sql_vol_billion'].iloc[0]}B | Python={py_upi_2025_vol}B | Match: {sql_upi_2025['sql_vol_billion'].iloc[0] == py_upi_2025_vol}")
print(f"2025 UPI Value:  SQL=₹{sql_upi_2025['sql_val_trillion'].iloc[0]}T | Python=₹{py_upi_2025_val}T | Match: {sql_upi_2025['sql_val_trillion'].iloc[0] == py_upi_2025_val}")

assert sql_upi_2025['sql_vol_billion'].iloc[0] == py_upi_2025_vol
assert sql_upi_2025['sql_val_trillion'].iloc[0] == py_upi_2025_val
print("All SQL-to-Python cross-checks passed with 100% precision.")
"""))

nb.cells = cells

with open("notebooks/phase4_exploratory_data_analysis.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print("Created notebooks/phase4_exploratory_data_analysis.ipynb successfully.")
