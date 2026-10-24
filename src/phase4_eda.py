"""
PAYFLOW — Phase 4: Exploratory Data Analysis & Analytical Visualizations
========================================================================
Author: PAYFLOW Data Analytics Team
Date: October 2026

This module provides reusable analytical functions, statistical aggregations,
and publication-quality chart generators investigating India's digital payments
transformation from November 2019 to July 2026.

Key Functions:
  - load_cleaned_data(): Loads transaction and infrastructure tables.
  - run_all_eda(): Executes complete statistical analysis and exports charts.
  - Chart generators for 9 publication-grade visual artifacts in visuals/phase4/.
"""

import os
from datetime import datetime
from typing import Dict, Tuple, List, Optional, Any
import pandas as pd
import numpy as np

import matplotlib
matplotlib.use("Agg")  # Non-interactive headless backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import seaborn as sns


# -----------------------------------------------------------------------------
# Global Styling Constants
# -----------------------------------------------------------------------------
PALETTE = {
    "primary": "#1A365D",      # Deep Navy
    "secondary": "#2B6CB0",    # Slate Blue
    "accent": "#DD6B20",       # Vibrant Amber
    "success": "#276749",      # Forest Green
    "danger": "#C53030",       # Deep Crimson
    "purple": "#6B46C1",       # Royal Purple
    "teal": "#2C7A7B",         # Deep Teal
    "dark": "#2D3748",         # Charcoal
    "light": "#EDF2F7",        # Soft Gray Background
    "grid": "#E2E8F0"          # Light Border/Grid
}

def apply_chart_style():
    """Applies clean, publication-grade styling to all figures."""
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
    plt.rcParams["axes.edgecolor"] = PALETTE["grid"]
    plt.rcParams["axes.linewidth"] = 0.8
    plt.rcParams["grid.color"] = PALETTE["grid"]
    plt.rcParams["grid.linestyle"] = "--"
    plt.rcParams["grid.alpha"] = 0.7
    plt.rcParams["figure.titlesize"] = 14
    plt.rcParams["figure.titleweight"] = "bold"
    plt.rcParams["axes.titlesize"] = 12
    plt.rcParams["axes.titleweight"] = "bold"
    plt.rcParams["axes.labelsize"] = 10
    plt.rcParams["axes.labelweight"] = "bold"
    plt.rcParams["xtick.labelsize"] = 9
    plt.rcParams["ytick.labelsize"] = 9
    plt.rcParams["legend.fontsize"] = 9
    plt.rcParams["figure.autolayout"] = True


# -----------------------------------------------------------------------------
# 1. Ingestion & Transformation Helpers
# -----------------------------------------------------------------------------

def load_cleaned_data(data_dir: str = "data/processed") -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Loads all four Phase 2 deliverables and parses date columns."""
    trans_path = os.path.join(data_dir, "transaction_indicators.csv")
    infra_path = os.path.join(data_dir, "infrastructure_indicators.csv")
    dict_path = os.path.join(data_dir, "data_dictionary.csv")
    exc_path = os.path.join(data_dir, "cleaning_exceptions.csv")

    for p in [trans_path, infra_path, dict_path, exc_path]:
        if not os.path.exists(p):
            raise FileNotFoundError(f"Required processed file missing: {p}")

    df_trans = pd.read_csv(trans_path)
    df_infra = pd.read_csv(infra_path)
    df_dict = pd.read_csv(dict_path)
    df_exc = pd.read_csv(exc_path)

    df_trans["month_date"] = pd.to_datetime(df_trans["month_date"])
    df_infra["month_date"] = pd.to_datetime(df_infra["month_date"])
    df_exc["month_date"] = pd.to_datetime(df_exc["month_date"])

    return df_trans, df_infra, df_dict, df_exc


# -----------------------------------------------------------------------------
# 2. Analytical Metric Generators
# -----------------------------------------------------------------------------

def get_upi_retail_share(df_trans: pd.DataFrame) -> pd.DataFrame:
    """Computes monthly and annual UPI volume and value share of retail payments."""
    piv_vol = df_trans.pivot(index="month_date", columns="indicator_code", values="volume_lakh")
    piv_val = df_trans.pivot(index="month_date", columns="indicator_code", values="value_inr_crore")

    df_share = pd.DataFrame(index=piv_vol.index)
    df_share["upi_vol_lakh"] = piv_vol["UPI"]
    df_share["retail_vol_lakh"] = piv_vol["TOTAL_RETAIL_PAYMENTS"]
    df_share["upi_val_crore"] = piv_val["UPI"]
    df_share["retail_val_crore"] = piv_val["TOTAL_RETAIL_PAYMENTS"]

    df_share["upi_vol_billion"] = df_share["upi_vol_lakh"] / 10000.0
    df_share["retail_vol_billion"] = df_share["retail_vol_lakh"] / 10000.0
    df_share["upi_val_trillion"] = df_share["upi_val_crore"] / 100000.0
    df_share["retail_val_trillion"] = df_share["retail_val_crore"] / 100000.0

    df_share["upi_vol_share_pct"] = (df_share["upi_vol_lakh"] / df_share["retail_vol_lakh"]) * 100.0
    df_share["upi_val_share_pct"] = (df_share["upi_val_crore"] / df_share["retail_val_crore"]) * 100.0
    df_share["upi_ats_inr"] = (df_share["upi_val_crore"] / df_share["upi_vol_lakh"]) * 100.0

    return df_share.reset_index()


def get_annual_summary(df_trans: pd.DataFrame) -> pd.DataFrame:
    """Aggregates metrics by calendar year, explicitly annotating partial year 2026."""
    df_share = get_upi_retail_share(df_trans)
    df_share["year"] = df_share["month_date"].dt.year

    ann = df_share.groupby("year").agg({
        "month_date": "count",
        "upi_vol_billion": "sum",
        "retail_vol_billion": "sum",
        "upi_val_trillion": "sum",
        "retail_val_trillion": "sum"
    }).rename(columns={"month_date": "months_observed"})

    ann["upi_vol_share_pct"] = (ann["upi_vol_billion"] / ann["retail_vol_billion"]) * 100.0
    ann["upi_val_share_pct"] = (ann["upi_val_trillion"] / ann["retail_val_trillion"]) * 100.0
    ann["period_qualification"] = ann.index.map(
        lambda y: "Full Year (12M)" if y in range(2020, 2026) else ("Partial Year (2M - Nov/Dec)" if y == 2019 else "Partial Year (7M - Jan-Jul)")
    )
    return ann.reset_index()


def get_rail_ats_comparison(df_trans: pd.DataFrame) -> pd.DataFrame:
    """Extracts Average Ticket Size (ATS) trajectory across payment rails."""
    rails = ["UPI", "IMPS", "NEFT", "RTGS_CUSTOMER", "CREDIT_CARDS_TOTAL", "DEBIT_CARDS_TOTAL", "PAPER_CTS"]
    sub = df_trans[df_trans["indicator_code"].isin(rails)].copy()
    piv_ats = sub.pivot(index="month_date", columns="indicator_code", values="avg_ticket_size_inr")
    return piv_ats.reset_index()


def get_card_spend_divergence(df_trans: pd.DataFrame) -> pd.DataFrame:
    """Analyzes Credit vs Debit Card spend across PoS and e-Commerce."""
    card_codes = ["CREDIT_CARDS_POS", "CREDIT_CARDS_OTHERS", "DEBIT_CARDS_POS", "DEBIT_CARDS_OTHERS"]
    sub = df_trans[df_trans["indicator_code"].isin(card_codes)].copy()
    piv_val = sub.pivot(index="month_date", columns="indicator_code", values="value_inr_crore")

    df_cards = pd.DataFrame(index=piv_val.index)
    df_cards["cc_pos_val_cr"] = piv_val["CREDIT_CARDS_POS"]
    df_cards["cc_ecom_val_cr"] = piv_val["CREDIT_CARDS_OTHERS"]
    df_cards["cc_total_val_cr"] = df_cards["cc_pos_val_cr"] + df_cards["cc_ecom_val_cr"]

    df_cards["dc_pos_val_cr"] = piv_val["DEBIT_CARDS_POS"]
    df_cards["dc_ecom_val_cr"] = piv_val["DEBIT_CARDS_OTHERS"]
    df_cards["dc_total_val_cr"] = df_cards["dc_pos_val_cr"] + df_cards["dc_ecom_val_cr"]

    df_cards["cc_ecom_share_pct"] = (df_cards["cc_ecom_val_cr"] / df_cards["cc_total_val_cr"]) * 100.0
    df_cards["dc_ecom_share_pct"] = (df_cards["dc_ecom_val_cr"] / df_cards["dc_total_val_cr"]) * 100.0
    df_cards["credit_to_debit_ratio"] = df_cards["cc_total_val_cr"] / df_cards["dc_total_val_cr"]

    return df_cards.reset_index()


def get_infrastructure_trajectory(df_infra: pd.DataFrame) -> pd.DataFrame:
    """Extracts merchant acceptance points and equipment touchpoints."""
    infra_codes = ["POS_TERMINALS_DEPLOYED", "BHARAT_QR_DEPLOYED", "UPI_QR_STATIC_DEPLOYED", 
                   "ATMS_TOTAL_DEPLOYED", "MICRO_ATMS_DEPLOYED"]
    sub = df_infra[df_infra["indicator_code"].isin(infra_codes)].copy()
    piv_cnt = sub.pivot(index="month_date", columns="indicator_code", values="count_lakh")
    
    df_out = pd.DataFrame(index=piv_cnt.index)
    df_out["pos_terminals_lakh"] = piv_cnt["POS_TERMINALS_DEPLOYED"]
    df_out["bharat_qr_lakh"] = piv_cnt["BHARAT_QR_DEPLOYED"]
    df_out["upi_qr_static_lakh"] = piv_cnt["UPI_QR_STATIC_DEPLOYED"]
    df_out["atms_total_lakh"] = piv_cnt["ATMS_TOTAL_DEPLOYED"]
    df_out["micro_atms_lakh"] = piv_cnt["MICRO_ATMS_DEPLOYED"]

    df_out["qr_to_pos_ratio"] = df_out["upi_qr_static_lakh"] / df_out["pos_terminals_lakh"]
    return df_out.reset_index()


def get_cash_vs_digital(df_trans: pd.DataFrame) -> pd.DataFrame:
    """Analyzes ATM cash withdrawals against total digital payments."""
    codes = ["ATM_CASH_TOTAL", "MICRO_ATM_CASH_TOTAL", "TOTAL_DIGITAL_PAYMENTS"]
    sub = df_trans[df_trans["indicator_code"].isin(codes)].copy()
    piv_val = sub.pivot(index="month_date", columns="indicator_code", values="value_inr_crore")
    piv_vol = sub.pivot(index="month_date", columns="indicator_code", values="volume_lakh")

    df_cash = pd.DataFrame(index=piv_val.index)
    df_cash["atm_cash_val_cr"] = piv_val["ATM_CASH_TOTAL"]
    df_cash["atm_cash_vol_lakh"] = piv_vol["ATM_CASH_TOTAL"]
    df_cash["digital_val_cr"] = piv_val["TOTAL_DIGITAL_PAYMENTS"]
    df_cash["micro_atm_val_cr"] = piv_val["MICRO_ATM_CASH_TOTAL"]

    df_cash["atm_cash_to_digital_pct"] = (df_cash["atm_cash_val_cr"] / df_cash["digital_val_cr"]) * 100.0
    df_cash["avg_atm_withdrawal_inr"] = (df_cash["atm_cash_val_cr"] / df_cash["atm_cash_vol_lakh"]) * 100.0

    return df_cash.reset_index()


# -----------------------------------------------------------------------------
# 3. Publication-Grade Visualization Generators (visuals/phase4/)
# -----------------------------------------------------------------------------

def plot_01_upi_share(df_share: pd.DataFrame, out_path: str):
    """Chart 1: UPI Volume and Value Share of Total Retail Payments."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    # Volume Share
    ax1.plot(df_share["month_date"], df_share["upi_vol_share_pct"], color=PALETTE["primary"], lw=2.5, label="UPI Volume Share (%)")
    ax1.fill_between(df_share["month_date"], df_share["upi_vol_share_pct"], color=PALETTE["secondary"], alpha=0.15)
    ax1.axhline(50, color=PALETTE["dark"], ls=":", lw=1, alpha=0.6)
    ax1.text(df_share["month_date"].iloc[12], 52, "50% Volume Mark (Late 2020)", fontsize=8.5, color=PALETTE["dark"])
    ax1.scatter([df_share["month_date"].iloc[-1]], [df_share["upi_vol_share_pct"].iloc[-1]], color=PALETTE["accent"], s=45, zorder=5)
    ax1.annotate(f"{df_share['upi_vol_share_pct'].iloc[-1]:.1f}% (Jul-2026)", 
                 (df_share["month_date"].iloc[-1], df_share["upi_vol_share_pct"].iloc[-1]),
                 textcoords="offset points", xytext=(-70, -15), fontsize=8.5, weight="bold", color=PALETTE["primary"])
    ax1.set_ylabel("Volume Share (%)")
    ax1.set_title("A. UPI Penetration in Retail Payment Volume (Lakh Transactions)", loc="left", fontsize=11)
    ax1.set_ylim(30, 95)
    ax1.legend(loc="upper left")

    # Value Share
    ax2.plot(df_share["month_date"], df_share["upi_val_share_pct"], color=PALETTE["accent"], lw=2.5, label="UPI Value Share (%)")
    ax2.fill_between(df_share["month_date"], df_share["upi_val_share_pct"], color=PALETTE["accent"], alpha=0.15)
    ax2.scatter([df_share["month_date"].iloc[-1]], [df_share["upi_val_share_pct"].iloc[-1]], color=PALETTE["primary"], s=45, zorder=5)
    ax2.annotate(f"{df_share['upi_val_share_pct'].iloc[-1]:.1f}% (Jul-2026)", 
                 (df_share["month_date"].iloc[-1], df_share["upi_val_share_pct"].iloc[-1]),
                 textcoords="offset points", xytext=(-65, 10), fontsize=8.5, weight="bold", color=PALETTE["accent"])
    ax2.set_ylabel("Value Share (%)")
    ax2.set_title("B. UPI Penetration in Retail Payment Value (INR Crores)", loc="left", fontsize=11)
    ax2.set_ylim(0, 35)
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax2.legend(loc="upper left")

    fig.suptitle("PAYFLOW — UPI Retail Payments Market Share Trajectory (2019–2026)", fontsize=13, weight="bold", y=0.99)
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Exported: {out_path}")


def plot_02_monthly_upi_trends(df_share: pd.DataFrame, out_path: str):
    """Chart 2: Monthly UPI Volume (Billions) and Value (₹ Trillions)."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    # Volume (Billions)
    ax1.plot(df_share["month_date"], df_share["upi_vol_billion"], color=PALETTE["secondary"], lw=2.2, label="Monthly Volume (Billion Txns)")
    ax1.scatter([df_share["month_date"].iloc[-1]], [df_share["upi_vol_billion"].iloc[-1]], color=PALETTE["accent"], s=45, zorder=5)
    ax1.annotate(f"{df_share['upi_vol_billion'].iloc[-1]:.2f}B (Jul-2026)", 
                 (df_share["month_date"].iloc[-1], df_share["upi_vol_billion"].iloc[-1]),
                 textcoords="offset points", xytext=(-70, -15), fontsize=8.5, weight="bold")
    # Annotate COVID lockdown drop
    ax1.annotate("COVID-19 Lockdown\n(Apr-2020: 0.99B)", xy=(pd.to_datetime("2020-04-01"), 0.99),
                 xytext=(pd.to_datetime("2020-07-01"), 5.0),
                 arrowprops=dict(arrowstyle="->", color=PALETTE["danger"], lw=1.2),
                 fontsize=8, color=PALETTE["danger"], weight="bold")
    ax1.set_ylabel("Transactions (Billions)")
    ax1.set_title("A. Monthly UPI Transaction Volume", loc="left", fontsize=11)
    ax1.set_ylim(0, 26)
    ax1.legend(loc="upper left")

    # Value (₹ Trillions)
    ax2.plot(df_share["month_date"], df_share["upi_val_trillion"], color=PALETTE["success"], lw=2.2, label="Monthly Value (₹ Trillion INR)")
    ax2.scatter([df_share["month_date"].iloc[-1]], [df_share["upi_val_trillion"].iloc[-1]], color=PALETTE["primary"], s=45, zorder=5)
    ax2.annotate(f"₹{df_share['upi_val_trillion'].iloc[-1]:.2f}T (Jul-2026)", 
                 (df_share["month_date"].iloc[-1], df_share["upi_val_trillion"].iloc[-1]),
                 textcoords="offset points", xytext=(-70, 10), fontsize=8.5, weight="bold")
    ax2.set_ylabel("Spending Value (₹ Trillion)")
    ax2.set_title("B. Monthly UPI Transaction Value", loc="left", fontsize=11)
    ax2.set_ylim(0, 35)
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax2.legend(loc="upper left")

    fig.suptitle("PAYFLOW — Absolute UPI Volume and Value Expansion (Nov-2019 to Jul-2026)", fontsize=13, weight="bold", y=0.99)
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Exported: {out_path}")


def plot_03_ats_comparison(df_ats: pd.DataFrame, out_path: str):
    """Chart 3: Average Ticket Size (ATS) Across Key Payment Rails (Log Scale)."""
    fig, ax = plt.subplots(figsize=(10, 6))

    colors = {
        "RTGS_CUSTOMER": PALETTE["danger"],
        "NEFT": PALETTE["purple"],
        "PAPER_CTS": PALETTE["dark"],
        "IMPS": PALETTE["teal"],
        "CREDIT_CARDS_TOTAL": PALETTE["accent"],
        "DEBIT_CARDS_TOTAL": PALETTE["secondary"],
        "UPI": PALETTE["success"]
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

    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Exported: {out_path}")


def plot_04_digital_composition(df_trans: pd.DataFrame, out_path: str):
    """Chart 4: Retail Digital Payment Volume Composition Stacked Area Chart."""
    piv = df_trans.pivot(index="month_date", columns="indicator_code", values="volume_lakh")

    # Select constituent retail components
    comp_df = pd.DataFrame(index=piv.index)
    comp_df["UPI"] = piv["UPI"] / 10000.0
    comp_df["Cards (Credit+Debit)"] = (piv["CREDIT_CARDS_TOTAL"] + piv["DEBIT_CARDS_TOTAL"]) / 10000.0
    comp_df["IMPS"] = piv["IMPS"] / 10000.0
    comp_df["NEFT"] = piv["NEFT"] / 10000.0
    comp_df["Direct Debits (NACH+NETC)"] = (piv["NACH_DEBIT"] + piv["NETC_FASTAG"]) / 10000.0
    comp_df["PPIs (Wallets+Cards)"] = piv["PPI_TOTAL"] / 10000.0

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # 1. Absolute Stacked Volume
    stack_cols = ["UPI", "Cards (Credit+Debit)", "IMPS", "NEFT", "Direct Debits (NACH+NETC)", "PPIs (Wallets+Cards)"]
    palette_list = [PALETTE["primary"], PALETTE["accent"], PALETTE["teal"], PALETTE["purple"], PALETTE["secondary"], PALETTE["dark"]]
    ax1.stackplot(comp_df.index, [comp_df[c] for c in stack_cols], labels=stack_cols, colors=palette_list, alpha=0.85)
    ax1.set_ylabel("Monthly Volume (Billion Txns)")
    ax1.set_title("A. Absolute Monthly Retail Payment Volume Composition", loc="left", fontsize=11)
    ax1.legend(loc="upper left", fontsize=8.5)

    # 2. 100% Percentage Share Stacked
    pct_df = comp_df[stack_cols].div(comp_df[stack_cols].sum(axis=1), axis=0) * 100.0
    ax2.stackplot(pct_df.index, [pct_df[c] for c in stack_cols], labels=stack_cols, colors=palette_list, alpha=0.85)
    ax2.set_ylabel("Volume Share (%)")
    ax2.set_title("B. Relative Retail Volume Share (% of Digital Retail Total)", loc="left", fontsize=11)
    ax2.set_ylim(0, 100)
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    fig.suptitle("PAYFLOW — Structural Transformation of Indian Retail Digital Payments", fontsize=13, weight="bold", y=0.99)
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Exported: {out_path}")


def plot_05_card_trends(df_cards: pd.DataFrame, out_path: str):
    """Chart 5: Credit vs Debit Card Spending Divergence & e-Commerce Share."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Panel 1: Monthly Total Spending Value
    ax1.plot(df_cards["month_date"], df_cards["cc_total_val_cr"] / 1000.0, color=PALETTE["accent"], lw=2.2, label="Credit Card Spend (₹ '000 Cr)")
    ax1.plot(df_cards["month_date"], df_cards["dc_total_val_cr"] / 1000.0, color=PALETTE["secondary"], lw=2.2, label="Debit Card Spend (₹ '000 Cr)")
    ax1.set_ylabel("Monthly Spend (₹ Thousand Crores)")
    ax1.set_title("A. Monthly Card Spending Value (₹ Thousand Cr)", loc="left", fontsize=11)
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax1.legend(loc="upper left")

    # Panel 2: e-Commerce Share of Card Spend
    ax2.plot(df_cards["month_date"], df_cards["cc_ecom_share_pct"], color=PALETTE["accent"], lw=2.2, label="Credit Card e-Com Share (%)")
    ax2.plot(df_cards["month_date"], df_cards["dc_ecom_share_pct"], color=PALETTE["secondary"], lw=2.2, label="Debit Card e-Com Share (%)")
    ax2.set_ylabel("Online / e-Commerce Share (%)")
    ax2.set_title("B. Online vs In-Store PoS Spending Share (%)", loc="left", fontsize=11)
    ax2.set_ylim(20, 75)
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax2.legend(loc="lower right")

    fig.suptitle("PAYFLOW — Credit Card vs. Debit Card Usage & Channel Divergence", fontsize=13, weight="bold", y=1.02)
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Exported: {out_path}")


def plot_06_infrastructure_growth(df_infra_trends: pd.DataFrame, out_path: str):
    """Chart 6: Acceptance Infrastructure Scaling: PoS Terminals vs Static UPI QR."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Panel 1: Touchpoint counts in Lakhs
    ax1.plot(df_infra_trends["month_date"], df_infra_trends["pos_terminals_lakh"], color=PALETTE["primary"], lw=2.2, label="PoS Terminals (Lakh)")
    ax1.plot(df_infra_trends["month_date"], df_infra_trends["bharat_qr_lakh"], color=PALETTE["teal"], lw=2.0, label="Bharat QR (Lakh)")
    ax1.plot(df_infra_trends["month_date"], df_infra_trends["upi_qr_static_lakh"], color=PALETTE["accent"], lw=2.2, label="Static UPI QR (Lakh)")
    ax1.set_ylabel("Active Touchpoints (Lakh = 100k Units)")
    ax1.set_title("A. Merchant Touchpoint Footprint (Lakhs)", loc="left", fontsize=11)
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax1.legend(loc="upper left")

    # Panel 2: Ratio of QR Codes to PoS Terminals
    valid_ratio = df_infra_trends.dropna(subset=["qr_to_pos_ratio"])
    ax2.plot(valid_ratio["month_date"], valid_ratio["qr_to_pos_ratio"], color=PALETTE["purple"], lw=2.5, label="QR Codes per PoS Terminal")
    ax2.scatter([valid_ratio["month_date"].iloc[-1]], [valid_ratio["qr_to_pos_ratio"].iloc[-1]], color=PALETTE["danger"], s=45, zorder=5)
    ax2.annotate(f"{valid_ratio['qr_to_pos_ratio'].iloc[-1]:.1f}x (Jul-2026)", 
                 (valid_ratio["month_date"].iloc[-1], valid_ratio["qr_to_pos_ratio"].iloc[-1]),
                 textcoords="offset points", xytext=(-65, -15), fontsize=8.5, weight="bold")
    ax2.set_ylabel("Multiple (QR / PoS)")
    ax2.set_title("B. QR Code Multiplier Relative to PoS Machines", loc="left", fontsize=11)
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax2.legend(loc="upper left")

    fig.suptitle("PAYFLOW — Asset-Heavy PoS Machines vs. Asset-Light QR Acceptance Expansion", fontsize=13, weight="bold", y=1.02)
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Exported: {out_path}")


def plot_07_cash_vs_digital(df_cash: pd.DataFrame, out_path: str):
    """Chart 7: ATM Cash Withdrawals vs Digital Payment Trends."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Panel 1: ATM Cash Withdrawal Value vs Digital Payments Value (₹ Trillion)
    ax1.plot(df_cash["month_date"], df_cash["digital_val_cr"] / 100000.0, color=PALETTE["primary"], lw=2.2, label="Total Digital Payments (₹ Trillion)")
    ax1.plot(df_cash["month_date"], df_cash["atm_cash_val_cr"] / 100000.0, color=PALETTE["accent"], lw=2.2, label="ATM Cash Withdrawals (₹ Trillion)")
    ax1.set_ylabel("Monthly Value (₹ Trillion INR)")
    ax1.set_title("A. Digital Payments vs. ATM Cash Out Value (₹ Trillion)", loc="left", fontsize=11)
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax1.legend(loc="upper left")

    # Panel 2: Ratio of ATM Cash Withdrawals to Digital Payments Value (%)
    ax2.plot(df_cash["month_date"], df_cash["atm_cash_to_digital_pct"], color=PALETTE["danger"], lw=2.2, label="Cash Withdrawal / Digital Ratio (%)")
    ax2.scatter([df_cash["month_date"].iloc[-1]], [df_cash["atm_cash_to_digital_pct"].iloc[-1]], color=PALETTE["primary"], s=45, zorder=5)
    ax2.annotate(f"{df_cash['atm_cash_to_digital_pct'].iloc[-1]:.2f}% (Jul-2026)", 
                 (df_cash["month_date"].iloc[-1], df_cash["atm_cash_to_digital_pct"].iloc[-1]),
                 textcoords="offset points", xytext=(-65, 12), fontsize=8.5, weight="bold")
    ax2.set_ylabel("Ratio (%)")
    ax2.set_title("B. ATM Cash-to-Digital Payment Spending Ratio (%)", loc="left", fontsize=11)
    ax2.set_ylim(0, 3.0)
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax2.legend(loc="upper right")

    fig.suptitle("PAYFLOW — ATM Cash Withdrawal Dynamics & Digital Displacement", fontsize=13, weight="bold", y=1.02)
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Exported: {out_path}")


def plot_08_growth_leaders_decliners(df_trans: pd.DataFrame, df_dict: pd.DataFrame, out_path: str):
    """Chart 8: Component Growth Leaders vs Decliners (Baseline vs Latest 12M)."""
    base_mask = (df_trans["month_date"] >= "2019-11-01") & (df_trans["month_date"] <= "2020-10-01")
    latest_mask = (df_trans["month_date"] >= "2025-08-01") & (df_trans["month_date"] <= "2026-07-01")

    base_avg = df_trans[base_mask].groupby("indicator_code")["volume_lakh"].mean()
    latest_avg = df_trans[latest_mask].groupby("indicator_code")["volume_lakh"].mean()

    # Filter component level indicators only
    comp_codes = df_dict[df_dict["hierarchy_level"].isin(["Component", "Sub_Component"])]["indicator_code"].str.replace("_VOL", "").unique()

    growth_records = []
    for code in comp_codes:
        if code in base_avg and code in latest_avg:
            b = base_avg[code]
            l = latest_avg[code]
            if b > 0.05: # avoid division by near-zero artifact
                g_pct = ((l - b) / b) * 100.0
                name_series = df_dict[df_dict["indicator_code"] == f"{code}_VOL"]["indicator_name"]
                name = name_series.iloc[0].split("[Volume]")[0].strip() if len(name_series) > 0 else code
                growth_records.append({"code": code, "name": name, "baseline": b, "latest": l, "growth_pct": g_pct})

    df_g = pd.DataFrame(growth_records).sort_values(by="growth_pct", ascending=True)

    # Top 5 and Bottom 5
    top5 = df_g.tail(5)
    bottom5 = df_g.head(5)
    plot_df = pd.concat([bottom5, top5])

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = [PALETTE["danger"] if g < 0 else PALETTE["success"] for g in plot_df["growth_pct"]]

    y_pos = np.arange(len(plot_df))
    bars = ax.barh(y_pos, plot_df["growth_pct"], color=colors, height=0.65)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(plot_df["name"], fontsize=8.5)
    ax.axvline(0, color=PALETTE["dark"], lw=0.8, ls="--")

    for bar, g in zip(bars, plot_df["growth_pct"]):
        offset = 15 if g >= 0 else -15
        ha = "left" if g >= 0 else "right"
        ax.annotate(f"{g:+.1f}%", 
                    (bar.get_width(), bar.get_y() + bar.get_height() / 2),
                    textcoords="offset points", xytext=(offset, -3),
                    ha=ha, va="center", fontsize=8, weight="bold")

    ax.set_xlabel("Volume Growth Rate (%) [Nov-2019/Oct-2020 vs. Aug-2025/Jul-2026]")
    ax.set_title("PAYFLOW — Top Growth vs. Declining Payment Rails (Component Level)", fontsize=13, weight="bold")
    ax.set_xlim(-150, 1650)

    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Exported: {out_path}")


def plot_09_seasonality_and_covid(df_share: pd.DataFrame, out_path: str):
    """Chart 9: MoM Seasonality Indexing and COVID-19 Shock Analysis."""
    df_share = df_share.copy()
    df_share["month_num"] = df_share["month_date"].dt.month
    df_share["mom_vol_growth"] = df_share["upi_vol_lakh"].pct_change() * 100.0

    # Group average MoM growth by calendar month (excluding 2020 lockdown shock)
    normal_years = df_share[df_share["month_date"].dt.year.isin([2021, 2022, 2023, 2024, 2025])]
    seasonality = normal_years.groupby("month_num")["mom_vol_growth"].mean()
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(month_names, seasonality.values, color=PALETTE["secondary"], width=0.6)

    # Highlight March and October/November
    for idx, (bar, m_val) in enumerate(zip(bars, seasonality.values)):
        if idx == 2: # March
            bar.set_color(PALETTE["accent"])
            ax.annotate("Fiscal Year-End\nSurge (+9.8%)", (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                        xytext=(0, 7), textcoords="offset points", ha="center", fontsize=8, weight="bold", color=PALETTE["accent"])
        elif idx in [9, 11]: # October, December
            bar.set_color(PALETTE["success"])
        elif idx == 1: # February (28 days)
            bar.set_color(PALETTE["danger"])
            ax.annotate("Fewer Days\n(-5.4%)", (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                        xytext=(0, -18), textcoords="offset points", ha="center", fontsize=8, weight="bold", color=PALETTE["danger"])

    ax.axhline(0, color=PALETTE["dark"], lw=0.8, ls="--")
    ax.set_ylabel("Average MoM Volume Growth Rate (%) [2021–2025]")
    ax.set_title("PAYFLOW — UPI Seasonality Index: Fiscal Surges vs. Calendar Effects", fontsize=13, weight="bold")

    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Exported: {out_path}")


# -----------------------------------------------------------------------------
# 4. Master Orchestration Routine
# -----------------------------------------------------------------------------

def run_all_eda(visuals_dir: str = "visuals/phase4") -> Dict[str, Any]:
    """Orchestrates complete analytical workflow and saves all 9 visual artifacts."""
    print("=" * 80)
    print("PAYFLOW — Phase 4: Exploratory Data Analysis Pipeline")
    print("=" * 80)

    os.makedirs(visuals_dir, exist_ok=True)
    apply_chart_style()

    df_trans, df_infra, df_dict, df_exc = load_cleaned_data()
    print(f"Loaded Cleaned Data: {len(df_trans)} transaction rows, {len(df_infra)} infrastructure rows.")

    # Metric datasets
    df_share = get_upi_retail_share(df_trans)
    df_ann = get_annual_summary(df_trans)
    df_ats = get_rail_ats_comparison(df_trans)
    df_cards = get_card_spend_divergence(df_trans)
    df_infra_trends = get_infrastructure_trajectory(df_infra)
    df_cash = get_cash_vs_digital(df_trans)

    # Generate Visuals
    print("\nGenerating Publication-Quality Charts in visuals/phase4/:")
    plot_01_upi_share(df_share, os.path.join(visuals_dir, "01_upi_volume_value_share.png"))
    plot_02_monthly_upi_trends(df_share, os.path.join(visuals_dir, "02_monthly_upi_trends.png"))
    plot_03_ats_comparison(df_ats, os.path.join(visuals_dir, "03_payment_rail_ats_comparison.png"))
    plot_04_digital_composition(df_trans, os.path.join(visuals_dir, "04_digital_payment_composition.png"))
    plot_05_card_trends(df_cards, os.path.join(visuals_dir, "05_credit_vs_debit_card_trends.png"))
    plot_06_infrastructure_growth(df_infra_trends, os.path.join(visuals_dir, "06_acceptance_infrastructure_growth.png"))
    plot_07_cash_vs_digital(df_cash, os.path.join(visuals_dir, "07_atm_cash_vs_digital_growth.png"))
    plot_08_growth_leaders_decliners(df_trans, df_dict, os.path.join(visuals_dir, "08_rail_growth_leaders_and_decliners.png"))
    plot_09_seasonality_and_covid(df_share, os.path.join(visuals_dir, "09_festive_and_fiscal_seasonality.png"))

    print("\nAll 9 charts successfully exported.")

    return {
        "df_share": df_share,
        "df_ann": df_ann,
        "df_ats": df_ats,
        "df_cards": df_cards,
        "df_infra_trends": df_infra_trends,
        "df_cash": df_cash,
        "charts_generated": 9
    }


if __name__ == "__main__":
    res = run_all_eda()
    print("EDA pipeline execution complete.")
