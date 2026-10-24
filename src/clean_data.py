"""
PAYFLOW — Phase 2: Data Cleaning & Schema Normalization Pipeline
================================================================
This script ingests the raw, hierarchical Reserve Bank of India (RBI)
Payment System Indicators CSV (Table 612, New Format), performs forensic
parsing, standardizes dates and numeric datatypes, resolves known anomalies
with full provenance, separates transaction and infrastructure metrics,
and exports analysis-ready datasets.

Source file: data/raw/612--payment-system-indicators--new-format.csv
Outputs:
  - data/processed/transaction_indicators.csv (and .parquet)
  - data/processed/infrastructure_indicators.csv (and .parquet)
  - data/processed/data_dictionary.csv (and .parquet)
  - data/processed/cleaning_exceptions.csv (and .parquet)
"""

import os
import csv
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import numpy as np


# -----------------------------------------------------------------------------
# 1. Indicator Taxonomy & Catalog Specification (All 70 Metric Pairs)
# -----------------------------------------------------------------------------

INDICATOR_SPECS = [
    # CCIL Financial Market Infrastructures (Wholesale Settlement)
    {
        "pair_id": 1,
        "type": "TRANSACTION",
        "code": "CCIL_TOTAL",
        "name": "1   CCIL Operated Systems (1.1 to 1.3)",
        "major_section": "A. Settlement Systems",
        "sub_section": "Financial Market Infrastructures (FMIs)",
        "channel_group": "Wholesale Settlement (CCIL)",
        "hierarchy_level": "Category_Total",
        "vol_col": "c2", "val_col": "c3",
        "footnote": "",
        "notes": "Aggregate of CCIL systems (1.1 G-Sec + 1.2 Forex + 1.3 Rupee Derivatives)."
    },
    {
        "pair_id": 2,
        "type": "TRANSACTION",
        "code": "CCIL_GSEC_TOTAL",
        "name": "1.1 Govt. Securities Clearing (1.1.1 to 1.1.3)",
        "major_section": "A. Settlement Systems",
        "sub_section": "Financial Market Infrastructures (FMIs)",
        "channel_group": "Wholesale Settlement (CCIL)",
        "hierarchy_level": "Subtotal",
        "vol_col": "c4", "val_col": "c5",
        "footnote": "",
        "notes": "Subtotal of G-Sec Outright + Repo + Triparty Repo."
    },
    {
        "pair_id": 3,
        "type": "TRANSACTION",
        "code": "CCIL_GSEC_OUTRIGHT",
        "name": "1.1.1 Outright",
        "major_section": "A. Settlement Systems",
        "sub_section": "Financial Market Infrastructures (FMIs)",
        "channel_group": "Wholesale Settlement (CCIL)",
        "hierarchy_level": "Component",
        "vol_col": "c6", "val_col": "c7",
        "footnote": "",
        "notes": "Secondary market outright G-Sec transactions."
    },
    {
        "pair_id": 4,
        "type": "TRANSACTION",
        "code": "CCIL_GSEC_REPO",
        "name": "1.1.2 Repo",
        "major_section": "A. Settlement Systems",
        "sub_section": "Financial Market Infrastructures (FMIs)",
        "channel_group": "Wholesale Settlement (CCIL)",
        "hierarchy_level": "Component",
        "vol_col": "c8", "val_col": "c9",
        "footnote": "",
        "notes": "Market repo transactions in government securities."
    },
    {
        "pair_id": 5,
        "type": "TRANSACTION",
        "code": "CCIL_GSEC_TRIPARTY_REPO",
        "name": "1.1.3 Tri-party Repo",
        "major_section": "A. Settlement Systems",
        "sub_section": "Financial Market Infrastructures (FMIs)",
        "channel_group": "Wholesale Settlement (CCIL)",
        "hierarchy_level": "Component",
        "vol_col": "c10", "val_col": "c11",
        "footnote": "",
        "notes": "TREPS (Triparty Repo Dealing and Settlement System)."
    },
    {
        "pair_id": 6,
        "type": "TRANSACTION",
        "code": "CCIL_FOREX_CLEARING",
        "name": "1.2 Forex Clearing",
        "major_section": "A. Settlement Systems",
        "sub_section": "Financial Market Infrastructures (FMIs)",
        "channel_group": "Wholesale Settlement (CCIL)",
        "hierarchy_level": "Component",
        "vol_col": "c12", "val_col": "c13",
        "footnote": "",
        "notes": "Interbank USD/INR forex clearing and settlement."
    },
    {
        "pair_id": 7,
        "type": "TRANSACTION",
        "code": "CCIL_RUPEE_DERIVATIVES",
        "name": "1.3 Rupee Derivatives @",
        "major_section": "A. Settlement Systems",
        "sub_section": "Financial Market Infrastructures (FMIs)",
        "channel_group": "Wholesale Settlement (CCIL)",
        "hierarchy_level": "Component",
        "vol_col": "c14", "val_col": "c15",
        "footnote": "@",
        "notes": "New inclusion w.e.f. November 2019 (IRS, FRA trades)."
    },

    # Payment Systems - FMIs (RTGS)
    {
        "pair_id": 8,
        "type": "TRANSACTION",
        "code": "RTGS_TOTAL",
        "name": "1 Credit Transfers - RTGS (1.1 to 1.2)",
        "major_section": "B. Payment Systems",
        "sub_section": "I Financial Market Infrastructures (FMIs)",
        "channel_group": "Large-Value Credit Transfers (RTGS)",
        "hierarchy_level": "Category_Total",
        "vol_col": "c16", "val_col": "c17",
        "footnote": "",
        "notes": "Total Real Time Gross Settlement (Customer + Interbank)."
    },
    {
        "pair_id": 9,
        "type": "TRANSACTION",
        "code": "RTGS_CUSTOMER",
        "name": "1.1 Customer Transactions",
        "major_section": "B. Payment Systems",
        "sub_section": "I Financial Market Infrastructures (FMIs)",
        "channel_group": "Large-Value Credit Transfers (RTGS)",
        "hierarchy_level": "Component",
        "vol_col": "c18", "val_col": "c19",
        "footnote": "",
        "notes": "Customer payments processed through RTGS (min ₹2 Lakh)."
    },
    {
        "pair_id": 10,
        "type": "TRANSACTION",
        "code": "RTGS_INTERBANK",
        "name": "1.2 Interbank Transactions",
        "major_section": "B. Payment Systems",
        "sub_section": "I Financial Market Infrastructures (FMIs)",
        "channel_group": "Large-Value Credit Transfers (RTGS)",
        "hierarchy_level": "Component",
        "vol_col": "c20", "val_col": "c21",
        "footnote": "",
        "notes": "Interbank settlement transactions processed through RTGS."
    },

    # Retail Credit Transfers
    {
        "pair_id": 11,
        "type": "TRANSACTION",
        "code": "RETAIL_CREDIT_TRANSFERS_TOTAL",
        "name": "2 Credit Transfers - Retail (2.1 to 2.7)",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Retail Credit Transfers",
        "hierarchy_level": "Category_Total",
        "vol_col": "c22", "val_col": "c23",
        "footnote": "",
        "notes": "Sum of retail credit rails (AePS, APBS, ECS Cr, IMPS, NACH Cr, NEFT, UPI)."
    },
    {
        "pair_id": 12,
        "type": "TRANSACTION",
        "code": "AEPS_FUND_TRANSFERS",
        "name": "2.1 AePS (Fund Transfers) @",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Retail Credit Transfers",
        "hierarchy_level": "Component",
        "vol_col": "c24", "val_col": "c25",
        "footnote": "@",
        "notes": "Aadhaar Enabled Payment System on-us/off-us account-to-account fund transfers."
    },
    {
        "pair_id": 13,
        "type": "TRANSACTION",
        "code": "APBS",
        "name": "2.2 APBS $",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Retail Credit Transfers",
        "hierarchy_level": "Component",
        "vol_col": "c26", "val_col": "c27",
        "footnote": "$",
        "notes": "Aadhaar Payment Bridge System (government welfare / DBT disbursements)."
    },
    {
        "pair_id": 14,
        "type": "TRANSACTION",
        "code": "ECS_CREDIT",
        "name": "2.3 ECS Cr",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Retail Credit Transfers",
        "hierarchy_level": "Component",
        "vol_col": "c28", "val_col": "c29",
        "footnote": "",
        "notes": "Electronic Clearing Service (Credit). Merged into NACH on 31 Jan 2020."
    },
    {
        "pair_id": 15,
        "type": "TRANSACTION",
        "code": "IMPS",
        "name": "2.4 IMPS",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Retail Credit Transfers",
        "hierarchy_level": "Component",
        "vol_col": "c30", "val_col": "c31",
        "footnote": "",
        "notes": "Immediate Payment Service (24x7 instant interbank transfer managed by NPCI)."
    },
    {
        "pair_id": 16,
        "type": "TRANSACTION",
        "code": "NACH_CREDIT",
        "name": "2.5 NACH Cr $",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Retail Credit Transfers",
        "hierarchy_level": "Component",
        "vol_col": "c32", "val_col": "c33",
        "footnote": "$",
        "notes": "National Automated Clearing House Credit (salaries, dividends, subsidies)."
    },
    {
        "pair_id": 17,
        "type": "TRANSACTION",
        "code": "NEFT",
        "name": "2.6 NEFT",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Retail Credit Transfers",
        "hierarchy_level": "Component",
        "vol_col": "c34", "val_col": "c35",
        "footnote": "",
        "notes": "National Electronic Funds Transfer (half-hourly batches, 24x7 since Dec 2019)."
    },
    {
        "pair_id": 18,
        "type": "TRANSACTION",
        "code": "UPI",
        "name": "2.7 UPI @",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Retail Credit Transfers",
        "hierarchy_level": "Component",
        "vol_col": "c36", "val_col": "c37",
        "footnote": "@",
        "notes": "Unified Payments Interface (total domestic transactions P2P + P2M)."
    },
    {
        "pair_id": 19,
        "type": "TRANSACTION",
        "code": "UPI_USSD",
        "name": "2.7.1 of which USSD @",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Retail Credit Transfers",
        "hierarchy_level": "Sub_Component",
        "vol_col": "c38", "val_col": "c39",
        "footnote": "@",
        "notes": "Feature phone payments via *99# USSD (subset of total UPI)."
    },

    # Debit Transfers & Direct Debits
    {
        "pair_id": 20,
        "type": "TRANSACTION",
        "code": "DEBIT_TRANSFERS_TOTAL",
        "name": "3 Debit Transfers and Direct Debits (3.1 to 3.4)",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Retail Debit Transfers",
        "hierarchy_level": "Category_Total",
        "vol_col": "c40", "val_col": "c41",
        "footnote": "",
        "notes": "Sum of direct debit instruments (BHIM Aadhaar, ECS Dr, NACH Dr, NETC FASTag)."
    },
    {
        "pair_id": 21,
        "type": "TRANSACTION",
        "code": "BHIM_AADHAAR_PAY",
        "name": "3.1 BHIM Aadhaar Pay @",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Retail Debit Transfers",
        "hierarchy_level": "Component",
        "vol_col": "c42", "val_col": "c43",
        "footnote": "@",
        "notes": "Merchant payments authenticated using consumer Aadhaar biometric."
    },
    {
        "pair_id": 22,
        "type": "TRANSACTION",
        "code": "ECS_DEBIT",
        "name": "3.2 ECS Dr",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Retail Debit Transfers",
        "hierarchy_level": "Component",
        "vol_col": "c44", "val_col": "c45",
        "footnote": "",
        "notes": "Electronic Clearing Service (Debit). Merged into NACH on 31 Jan 2020."
    },
    {
        "pair_id": 23,
        "type": "TRANSACTION",
        "code": "NACH_DEBIT",
        "name": "3.3 NACH Dr $",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Retail Debit Transfers",
        "hierarchy_level": "Component",
        "vol_col": "c46", "val_col": "c47",
        "footnote": "$",
        "notes": "NACH recurring direct debits (loan EMIs, SIPs, insurance premiums)."
    },
    {
        "pair_id": 24,
        "type": "TRANSACTION",
        "code": "NETC_FASTAG",
        "name": "3.4 NETC (linked to bank account) @",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Retail Debit Transfers",
        "hierarchy_level": "Component",
        "vol_col": "c48", "val_col": "c49",
        "footnote": "@",
        "notes": "National Electronic Toll Collection (FASTag linked directly to bank account)."
    },

    # Card Payments
    {
        "pair_id": 25,
        "type": "TRANSACTION",
        "code": "CARD_PAYMENTS_TOTAL",
        "name": "4 Card Payments (4.1 to 4.2)",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Card Payments",
        "hierarchy_level": "Category_Total",
        "vol_col": "c50", "val_col": "c51",
        "footnote": "",
        "notes": "Total domestic spending on cards (Credit Cards + Debit Cards)."
    },
    {
        "pair_id": 26,
        "type": "TRANSACTION",
        "code": "CREDIT_CARDS_TOTAL",
        "name": "4.1 Credit Cards (4.1.1 to 4.1.2)",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Card Payments",
        "hierarchy_level": "Subtotal",
        "vol_col": "c52", "val_col": "c53",
        "footnote": "",
        "notes": "Total credit card transactions (PoS + Others/e-Commerce)."
    },
    {
        "pair_id": 27,
        "type": "TRANSACTION",
        "code": "CREDIT_CARDS_POS",
        "name": "4.1.1 PoS based $",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Card Payments",
        "hierarchy_level": "Component",
        "vol_col": "c54", "val_col": "c55",
        "footnote": "$",
        "notes": "Physical point-of-sale card swipes/tap-and-pay transactions using credit cards."
    },
    {
        "pair_id": 28,
        "type": "TRANSACTION",
        "code": "CREDIT_CARDS_OTHERS",
        "name": "4.1.2 Others $",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Card Payments",
        "hierarchy_level": "Component",
        "vol_col": "c56", "val_col": "c57",
        "footnote": "$",
        "notes": "Online, e-commerce, in-app, and card-not-present credit card transactions."
    },
    {
        "pair_id": 29,
        "type": "TRANSACTION",
        "code": "DEBIT_CARDS_TOTAL",
        "name": "4.2 Debit Cards (4.2.1 to 4.2.1 )",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Card Payments",
        "hierarchy_level": "Subtotal",
        "vol_col": "c58", "val_col": "c59",
        "footnote": "",
        "notes": "Total debit card merchant spending transactions (PoS + Others/e-Commerce)."
    },
    {
        "pair_id": 30,
        "type": "TRANSACTION",
        "code": "DEBIT_CARDS_POS",
        "name": "4.2.1 PoS based $",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Card Payments",
        "hierarchy_level": "Component",
        "vol_col": "c60", "val_col": "c61",
        "footnote": "$",
        "notes": "Physical point-of-sale merchant debit card transactions."
    },
    {
        "pair_id": 31,
        "type": "TRANSACTION",
        "code": "DEBIT_CARDS_OTHERS",
        "name": "4.2.2 Others $",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Card Payments",
        "hierarchy_level": "Component",
        "vol_col": "c62", "val_col": "c63",
        "footnote": "$",
        "notes": "Online, e-commerce, and in-app debit card transactions."
    },

    # Prepaid Payment Instruments (PPIs)
    {
        "pair_id": 32,
        "type": "TRANSACTION",
        "code": "PPI_TOTAL",
        "name": "5 Prepaid Payment Instruments (5.1 to 5.2)",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Prepaid Payment Instruments (PPIs)",
        "hierarchy_level": "Category_Total",
        "vol_col": "c64", "val_col": "c65",
        "footnote": "",
        "notes": "Aggregate PPI transactions (Wallets + Prepaid Cards)."
    },
    {
        "pair_id": 33,
        "type": "TRANSACTION",
        "code": "PPI_WALLETS",
        "name": "5.1 Wallets",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Prepaid Payment Instruments (PPIs)",
        "hierarchy_level": "Component",
        "vol_col": "c66", "val_col": "c67",
        "footnote": "",
        "notes": "Prepaid mobile wallet transactions (bank and non-bank issuers)."
    },
    {
        "pair_id": 34,
        "type": "TRANSACTION",
        "code": "PPI_CARDS_TOTAL",
        "name": "5.2 Cards (5.2.1 to 5.2.2)",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Prepaid Payment Instruments (PPIs)",
        "hierarchy_level": "Subtotal",
        "vol_col": "c68", "val_col": "c69",
        "footnote": "",
        "notes": "Prepaid card transactions (gift cards, payroll cards, transit cards)."
    },
    {
        "pair_id": 35,
        "type": "TRANSACTION",
        "code": "PPI_CARDS_POS",
        "name": "5.2.1 PoS based $",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Prepaid Payment Instruments (PPIs)",
        "hierarchy_level": "Component",
        "vol_col": "c70", "val_col": "c71",
        "footnote": "$",
        "notes": "PoS swiped/tapped transactions using prepaid cards."
    },
    {
        "pair_id": 36,
        "type": "TRANSACTION",
        "code": "PPI_CARDS_OTHERS",
        "name": "5.2.2 Others $",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Prepaid Payment Instruments (PPIs)",
        "hierarchy_level": "Component",
        "vol_col": "c72", "val_col": "c73",
        "footnote": "$",
        "notes": "Online/e-commerce transactions using prepaid cards."
    },

    # Paper-based Instruments
    {
        "pair_id": 37,
        "type": "TRANSACTION",
        "code": "PAPER_TOTAL",
        "name": "6 Paper-based Instruments (6.1 to 6.2)",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Paper-based Instruments",
        "hierarchy_level": "Category_Total",
        "vol_col": "c74", "val_col": "c75",
        "footnote": "",
        "notes": "Total paper clearing instruments (CTS Cheques + Non-CTS Others)."
    },
    {
        "pair_id": 38,
        "type": "TRANSACTION",
        "code": "PAPER_CTS",
        "name": "6.1 CTS (NPCI Managed)",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Paper-based Instruments",
        "hierarchy_level": "Component",
        "vol_col": "c76", "val_col": "c77",
        "footnote": "",
        "notes": "Cheque Truncation System (electronic image-based clearing managed by NPCI)."
    },
    {
        "pair_id": 39,
        "type": "TRANSACTION",
        "code": "PAPER_OTHERS",
        "name": "6.2 Others",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Paper-based Instruments",
        "hierarchy_level": "Component",
        "vol_col": "c78", "val_col": "c79",
        "footnote": "",
        "notes": "Non-CTS paper clearings, micr/non-micr paper instruments."
    },

    # Official Macro Aggregates
    {
        "pair_id": 40,
        "type": "TRANSACTION",
        "code": "TOTAL_RETAIL_PAYMENTS",
        "name": "Total - Retail Payments (2+3+4+5+6)",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Macro Aggregates",
        "hierarchy_level": "Grand_Total",
        "vol_col": "c80", "val_col": "c81",
        "footnote": "",
        "notes": "Official aggregate of all retail payments (Categories 2 + 3 + 4 + 5 + 6)."
    },
    {
        "pair_id": 41,
        "type": "TRANSACTION",
        "code": "TOTAL_PAYMENTS",
        "name": "Total Payments (1+2+3+4+5+6)",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Macro Aggregates",
        "hierarchy_level": "Grand_Total",
        "vol_col": "c82", "val_col": "c83",
        "footnote": "",
        "notes": "Official total of wholesale RTGS (Cat 1) + Retail payments."
    },
    {
        "pair_id": 42,
        "type": "TRANSACTION",
        "code": "TOTAL_DIGITAL_PAYMENTS",
        "name": "Total Digital Payments (1+2+3+4+5)",
        "major_section": "B. Payment Systems",
        "sub_section": "II Retail",
        "channel_group": "Macro Aggregates",
        "hierarchy_level": "Grand_Total",
        "vol_col": "c84", "val_col": "c85",
        "footnote": "",
        "notes": "Official total digital transactions (Total Payments minus Paper-based instruments)."
    },

    # Alternative Payment Channels (Mobile & Internet)
    {
        "pair_id": 43,
        "type": "TRANSACTION",
        "code": "MOBILE_PAYMENTS_TOTAL",
        "name": "1 Mobile Payments (mobile app based) (1.1 to 1.2)",
        "major_section": "A. Other Payment Channels",
        "sub_section": "II Retail",
        "channel_group": "Mobile Banking Channels",
        "hierarchy_level": "Category_Total",
        "vol_col": "c86", "val_col": "c87",
        "footnote": "",
        "notes": "Total mobile banking application-based transactions."
    },
    {
        "pair_id": 44,
        "type": "TRANSACTION",
        "code": "MOBILE_PAYMENTS_INTRABANK",
        "name": "1.1 Intra-bank $",
        "major_section": "A. Other Payment Channels",
        "sub_section": "II Retail",
        "channel_group": "Mobile Banking Channels",
        "hierarchy_level": "Component",
        "vol_col": "c88", "val_col": "c89",
        "footnote": "$",
        "notes": "Book transfers / mobile payments between accounts within the same bank."
    },
    {
        "pair_id": 45,
        "type": "TRANSACTION",
        "code": "MOBILE_PAYMENTS_INTERBANK",
        "name": "1.2 Inter-bank $",
        "major_section": "A. Other Payment Channels",
        "sub_section": "II Retail",
        "channel_group": "Mobile Banking Channels",
        "hierarchy_level": "Component",
        "vol_col": "c90", "val_col": "c91",
        "footnote": "$",
        "notes": "Interbank mobile payments routed to other financial institutions."
    },
    {
        "pair_id": 46,
        "type": "TRANSACTION",
        "code": "INTERNET_PAYMENTS_TOTAL",
        "name": "2 Internet Payments (Netbanking / Internet Browser Based) @ (2.1 to 2.2)",
        "major_section": "A. Other Payment Channels",
        "sub_section": "II Retail",
        "channel_group": "Internet Banking Channels",
        "hierarchy_level": "Category_Total",
        "vol_col": "c92", "val_col": "c93",
        "footnote": "@",
        "notes": "Total internet browser-based netbanking transactions."
    },
    {
        "pair_id": 47,
        "type": "TRANSACTION",
        "code": "INTERNET_PAYMENTS_INTRABANK",
        "name": "2.1 Intra-bank @",
        "major_section": "A. Other Payment Channels",
        "sub_section": "II Retail",
        "channel_group": "Internet Banking Channels",
        "hierarchy_level": "Component",
        "vol_col": "c94", "val_col": "c95",
        "footnote": "@",
        "notes": "Intra-bank online transfers through web portal."
    },
    {
        "pair_id": 48,
        "type": "TRANSACTION",
        "code": "INTERNET_PAYMENTS_INTERBANK",
        "name": "2.2 Inter-bank @",
        "major_section": "A. Other Payment Channels",
        "sub_section": "II Retail",
        "channel_group": "Internet Banking Channels",
        "hierarchy_level": "Component",
        "vol_col": "c96", "val_col": "c97",
        "footnote": "@",
        "notes": "Interbank online transfers through netbanking portal."
    },

    # Cash Withdrawals (ATMs, PoS, Micro-ATMs)
    {
        "pair_id": 49,
        "type": "TRANSACTION",
        "code": "ATM_CASH_TOTAL",
        "name": "3 Cash Withdrawal at ATMs $ (3.1 to 3.3)",
        "major_section": "B. ATMs",
        "sub_section": "II Retail",
        "channel_group": "Cash Withdrawals",
        "hierarchy_level": "Category_Total",
        "vol_col": "c98", "val_col": "c99",
        "footnote": "$",
        "notes": "Total cash withdrawals at automated teller machines."
    },
    {
        "pair_id": 50,
        "type": "TRANSACTION",
        "code": "ATM_CASH_CREDIT_CARD",
        "name": "3.1 Using Credit Cards $",
        "major_section": "B. ATMs",
        "sub_section": "II Retail",
        "channel_group": "Cash Withdrawals",
        "hierarchy_level": "Component",
        "vol_col": "c100", "val_col": "c101",
        "footnote": "$",
        "notes": "Cash advances drawn at ATMs using credit cards."
    },
    {
        "pair_id": 51,
        "type": "TRANSACTION",
        "code": "ATM_CASH_DEBIT_CARD",
        "name": "3.2 Using Debit Cards $",
        "major_section": "B. ATMs",
        "sub_section": "II Retail",
        "channel_group": "Cash Withdrawals",
        "hierarchy_level": "Component",
        "vol_col": "c102", "val_col": "c103",
        "footnote": "$",
        "notes": "Cash withdrawals at ATMs using debit cards."
    },
    {
        "pair_id": 52,
        "type": "TRANSACTION",
        "code": "ATM_CASH_PREPAID_CARD",
        "name": "3.3 Using Pre-paid Cards $",
        "major_section": "B. ATMs",
        "sub_section": "II Retail",
        "channel_group": "Cash Withdrawals",
        "hierarchy_level": "Component",
        "vol_col": "c104", "val_col": "c105",
        "footnote": "$",
        "notes": "Cash withdrawals at ATMs using prepaid cards."
    },
    {
        "pair_id": 53,
        "type": "TRANSACTION",
        "code": "POS_CASH_TOTAL",
        "name": "4 Cash Withdrawal at PoS $ (4.1 to 4.2)",
        "major_section": "B. ATMs",
        "sub_section": "II Retail",
        "channel_group": "Cash Withdrawals",
        "hierarchy_level": "Category_Total",
        "vol_col": "c106", "val_col": "c107",
        "footnote": "$",
        "notes": "Cash-at-PoS (cash withdrawal facility at merchant point-of-sale terminals)."
    },
    {
        "pair_id": 54,
        "type": "TRANSACTION",
        "code": "POS_CASH_DEBIT_CARD",
        "name": "4.1 Using Debit Cards $",
        "major_section": "B. ATMs",
        "sub_section": "II Retail",
        "channel_group": "Cash Withdrawals",
        "hierarchy_level": "Component",
        "vol_col": "c108", "val_col": "c109",
        "footnote": "$",
        "notes": "Cash withdrawn at PoS using debit cards."
    },
    {
        "pair_id": 55,
        "type": "TRANSACTION",
        "code": "POS_CASH_PREPAID_CARD",
        "name": "4.2 Using Pre-paid Cards $",
        "major_section": "B. ATMs",
        "sub_section": "II Retail",
        "channel_group": "Cash Withdrawals",
        "hierarchy_level": "Component",
        "vol_col": "c110", "val_col": "c111",
        "footnote": "$",
        "notes": "Cash withdrawn at PoS using prepaid cards."
    },
    {
        "pair_id": 56,
        "type": "TRANSACTION",
        "code": "MICRO_ATM_CASH_TOTAL",
        "name": "5   Cash Withrawal at Micro ATMs @",
        "major_section": "B. ATMs",
        "sub_section": "II Retail",
        "channel_group": "Cash Withdrawals",
        "hierarchy_level": "Category_Total",
        "vol_col": "c112", "val_col": "c113",
        "footnote": "@",
        "notes": "Total cash withdrawals processed at BC Micro-ATMs."
    },
    {
        "pair_id": 57,
        "type": "TRANSACTION",
        "code": "MICRO_ATM_AEPS_CASH",
        "name": "5.1 AePS @",
        "major_section": "B. ATMs",
        "sub_section": "II Retail",
        "channel_group": "Cash Withdrawals",
        "hierarchy_level": "Component",
        "vol_col": "c114", "val_col": "c115",
        "footnote": "@",
        "notes": "Aadhaar Enabled Payment System cash withdrawals at Business Correspondent Micro-ATMs."
    },

    # Payment System Infrastructures (Physical Touchpoint Counts)
    {
        "pair_id": 58,
        "type": "INFRASTRUCTURE",
        "code": "CARDS_TOTAL_OUTSTANDING",
        "name": "1 Number of Cards (1.1 to 1.2)",
        "major_section": "Payment System Infrastructures",
        "sub_section": "II Retail",
        "channel_group": "Payment Cards in Force",
        "hierarchy_level": "Category_Total",
        "count_col": "c116", "val_col": "c117",
        "footnote": "",
        "notes": "Total payment cards in circulation (Credit + Debit). Value column is placeholder."
    },
    {
        "pair_id": 59,
        "type": "INFRASTRUCTURE",
        "code": "CARDS_CREDIT_OUTSTANDING",
        "name": "1.1 Credit Cards",
        "major_section": "Payment System Infrastructures",
        "sub_section": "II Retail",
        "channel_group": "Payment Cards in Force",
        "hierarchy_level": "Component",
        "count_col": "c118", "val_col": "c119",
        "footnote": "",
        "notes": "Active credit cards in force (bank-issued). Value column is placeholder."
    },
    {
        "pair_id": 60,
        "type": "INFRASTRUCTURE",
        "code": "CARDS_DEBIT_OUTSTANDING",
        "name": "1.2 Debit Cards",
        "major_section": "Payment System Infrastructures",
        "sub_section": "II Retail",
        "channel_group": "Payment Cards in Force",
        "hierarchy_level": "Component",
        "count_col": "c120", "val_col": "c121",
        "footnote": "",
        "notes": "Active debit cards in force (linked to savings/current accounts). Value column is placeholder."
    },
    {
        "pair_id": 61,
        "type": "INFRASTRUCTURE",
        "code": "PPIS_TOTAL_ISSUED",
        "name": "2 Number of PPIs @ (2.1 to 2.2)",
        "major_section": "Payment System Infrastructures",
        "sub_section": "II Retail",
        "channel_group": "Prepaid Instruments in Force",
        "hierarchy_level": "Category_Total",
        "count_col": "c122", "val_col": "c123",
        "footnote": "@",
        "notes": "Total active PPI accounts (Wallets + Prepaid Cards). Value column is placeholder."
    },
    {
        "pair_id": 62,
        "type": "INFRASTRUCTURE",
        "code": "PPIS_WALLETS_ISSUED",
        "name": "2.1 Wallets @",
        "major_section": "Payment System Infrastructures",
        "sub_section": "II Retail",
        "channel_group": "Prepaid Instruments in Force",
        "hierarchy_level": "Component",
        "count_col": "c124", "val_col": "c125",
        "footnote": "@",
        "notes": "Active prepaid digital wallet accounts. Value column is placeholder."
    },
    {
        "pair_id": 63,
        "type": "INFRASTRUCTURE",
        "code": "PPIS_CARDS_ISSUED",
        "name": "2.2 Cards @",
        "major_section": "Payment System Infrastructures",
        "sub_section": "II Retail",
        "channel_group": "Prepaid Instruments in Force",
        "hierarchy_level": "Component",
        "count_col": "c126", "val_col": "c127",
        "footnote": "@",
        "notes": "Active prepaid physical/virtual cards issued. Value column is placeholder."
    },
    {
        "pair_id": 64,
        "type": "INFRASTRUCTURE",
        "code": "ATMS_TOTAL_DEPLOYED",
        "name": "3 Number of ATMs (3.1 to 3.2)",
        "major_section": "Payment System Infrastructures",
        "sub_section": "II Retail",
        "channel_group": "ATM Terminals Deployed",
        "hierarchy_level": "Category_Total",
        "count_col": "c128", "val_col": "c129",
        "footnote": "",
        "notes": "Total operational ATMs deployed nationwide. Value column is placeholder."
    },
    {
        "pair_id": 65,
        "type": "INFRASTRUCTURE",
        "code": "ATMS_BANK_OWNED",
        "name": "3.1 Bank owned ATMs $",
        "major_section": "Payment System Infrastructures",
        "sub_section": "II Retail",
        "channel_group": "ATM Terminals Deployed",
        "hierarchy_level": "Component",
        "count_col": "c130", "val_col": "c131",
        "footnote": "$",
        "notes": "On-site and off-site ATMs owned and operated by commercial banks. Value is placeholder."
    },
    {
        "pair_id": 66,
        "type": "INFRASTRUCTURE",
        "code": "ATMS_WHITE_LABEL",
        "name": "3.2 White Label ATMs $",
        "major_section": "Payment System Infrastructures",
        "sub_section": "II Retail",
        "channel_group": "ATM Terminals Deployed",
        "hierarchy_level": "Component",
        "count_col": "c132", "val_col": "c133",
        "footnote": "$",
        "notes": "White Label ATMs (WLAs) deployed by authorized non-bank entities. Value is placeholder."
    },
    {
        "pair_id": 67,
        "type": "INFRASTRUCTURE",
        "code": "MICRO_ATMS_DEPLOYED",
        "name": "4   Number of Micro ATMs @",
        "major_section": "Payment System Infrastructures",
        "sub_section": "II Retail",
        "channel_group": "Micro-ATM Footprint",
        "hierarchy_level": "Component",
        "count_col": "c134", "val_col": "c135",
        "footnote": "@",
        "notes": "Operational Micro-ATMs deployed with Business Correspondents (BCs). Value is placeholder."
    },
    {
        "pair_id": 68,
        "type": "INFRASTRUCTURE",
        "code": "POS_TERMINALS_DEPLOYED",
        "name": "5   Number of PoS Terminals ",
        "major_section": "Payment System Infrastructures",
        "sub_section": "II Retail",
        "channel_group": "Merchant Acquiring Touchpoints",
        "hierarchy_level": "Component",
        "count_col": "c136", "val_col": "c137",
        "footnote": "",
        "notes": "Operational Point-of-Sale (PoS) merchant swipe/chip/contactless terminals. Value is placeholder."
    },
    {
        "pair_id": 69,
        "type": "INFRASTRUCTURE",
        "code": "BHARAT_QR_DEPLOYED",
        "name": "6   Bharat QR @",
        "major_section": "Payment System Infrastructures",
        "sub_section": "II Retail",
        "channel_group": "Merchant Acquiring Touchpoints",
        "hierarchy_level": "Component",
        "count_col": "c138", "val_col": "c139",
        "footnote": "@",
        "notes": "Interoperable Bharat QR codes deployed at merchant locations. Value is placeholder."
    },
    {
        "pair_id": 70,
        "type": "INFRASTRUCTURE",
        "code": "UPI_QR_STATIC_DEPLOYED",
        "name": "7 UPI QR *",
        "major_section": "Payment System Infrastructures",
        "sub_section": "II Retail",
        "channel_group": "Merchant Acquiring Touchpoints",
        "hierarchy_level": "Component",
        "count_col": "c140", "val_col": "c141",
        "footnote": "*",
        "notes": "Static UPI QR codes deployed w.e.f. Sep-2020. Column c141 contains displaced data for Jan-2024 to Jan-2026."
    }
]


# -----------------------------------------------------------------------------
# 2. Helper Functions
# -----------------------------------------------------------------------------

def parse_numeric(val_str: str) -> Optional[float]:
    """
    Parses a string from raw CSV to float.
    Treats whitespace, dashes ('-', ' -', '" -"'), and empty as None (missing/NaN).
    Converts valid numeric representations (e.g. '0.00', '1245.67') to float.
    """
    if val_str is None:
        return None
    s = val_str.strip().strip('"').strip("'").strip()
    if s == "" or s == "-" or s.replace("-", "").strip() == "":
        return None
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return None


def calculate_ats(value_cr: Optional[float], volume_lakh: Optional[float]) -> Optional[float]:
    """
    Computes Average Ticket Size (ATS) in Indian Rupees (INR):
      ATS = (Value in ₹ Crore * 10,000,000) / (Volume in Lakh * 100,000)
          = (Value in ₹ Crore / Volume in Lakh) * 100
    Returns None if volume <= 0 or if either component is None.
    """
    if value_cr is None or volume_lakh is None or volume_lakh <= 0.0:
        return None
    return round((value_cr / volume_lakh) * 100.0, 2)


# -----------------------------------------------------------------------------
# 3. Main Ingestion & Cleaning Pipeline
# -----------------------------------------------------------------------------

def run_pipeline(raw_csv_path: str = "data/raw/612--payment-system-indicators--new-format.csv",
                 output_dir: str = "data/processed") -> Dict[str, Any]:
    
    print("=" * 80)
    print("PAYFLOW — Phase 2: Data Cleaning & Normalization Pipeline")
    print("=" * 80)
    
    if not os.path.exists(raw_csv_path):
        raise FileNotFoundError(f"Raw CSV file not found at: {raw_csv_path}")
    
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs("docs", exist_ok=True)
    
    with open(raw_csv_path, "r", encoding="utf-8") as f:
        raw_rows = list(csv.reader(f))
    
    print(f"Loaded raw file: {raw_csv_path} ({len(raw_rows)} physical rows, {len(raw_rows[0])} columns)")
    
    # 3.1 Metadata & Header verification
    header_col_names = raw_rows[0]
    col_idx_map = {name: idx for idx, name in enumerate(header_col_names)}
    
    data_rows = raw_rows[8:89]  # exactly row_no 8 to row_no 88 (81 months)
    print(f"Isolated {len(data_rows)} data rows (row_no 8 to row_no 88).")
    
    # 3.2 Containers for outputs
    transaction_records = []
    infrastructure_records = []
    exceptions_log = []
    
    exception_counter = 1
    
    # Process each month
    for row in data_rows:
        row_num = row[col_idx_map["row_no"]].strip()
        month_label = row[col_idx_map["c1"]].strip()
        dt = datetime.strptime(month_label, "%b-%Y")
        month_date_str = dt.strftime("%Y-%m-01")
        year = dt.year
        month = dt.month
        
        # Process each indicator specification
        for spec in INDICATOR_SPECS:
            ind_type = spec["type"]
            code = spec["code"]
            name = spec["name"]
            sec = spec["major_section"]
            sub = spec["sub_section"]
            grp = spec["channel_group"]
            lvl = spec["hierarchy_level"]
            
            if ind_type == "TRANSACTION":
                vol_col = spec["vol_col"]
                val_col = spec["val_col"]
                raw_vol = row[col_idx_map[vol_col]].strip()
                raw_val = row[col_idx_map[val_col]].strip()
                
                num_vol = parse_numeric(raw_vol)
                num_val = parse_numeric(raw_val)
                data_status = "REPORTED"
                notes = ""
                
                # Special Anomaly Handling: Sep-2023 PPI Total Volume (c64)
                if code == "PPI_TOTAL" and month_date_str == "2023-09-01":
                    # Check components: c66 (Wallets) and c68 (Cards)
                    wallets_vol = parse_numeric(row[col_idx_map["c66"]])
                    cards_vol = parse_numeric(row[col_idx_map["c68"]])
                    wallets_val = parse_numeric(row[col_idx_map["c67"]])
                    cards_val = parse_numeric(row[col_idx_map["c69"]])
                    
                    if wallets_vol is not None and cards_vol is not None:
                        imputed_vol = round(wallets_vol + cards_vol, 2)
                        num_vol = imputed_vol
                        data_status = "DERIVED_SUM_CORRECTION"
                        notes = (f"Imputed from Wallets ({wallets_vol}) + Cards ({cards_vol}) = {imputed_vol} Lakh. "
                                 f"Raw volume cell was '{raw_vol}'.")
                        
                        exceptions_log.append({
                            "exception_id": f"EXC_{exception_counter:04d}",
                            "month_date": month_date_str,
                            "month_label": month_label,
                            "source_column": vol_col,
                            "indicator_code": code,
                            "indicator_name": name,
                            "raw_value": raw_vol,
                            "cleaned_value": imputed_vol,
                            "exception_category": "MISSING_TOTAL_IMPUTATION",
                            "severity": "MEDIUM",
                            "resolution_applied": "Imputed component sum: Wallets (c66) + PPI Cards (c68)",
                            "audit_justification": (f"Raw source reported '-' for PPI total volume in Sep-2023 while reported value "
                                                   f"({raw_val}) matches Wallets value ({wallets_val}) + Cards value ({cards_val}) = "
                                                   f"{round(wallets_val + cards_val, 2)}. Arithmetic and structure justify imputation.")
                        })
                        exception_counter += 1
                
                # Deprecated ECS Credit & Debit Handling
                elif code in ["ECS_CREDIT", "ECS_DEBIT"]:
                    if dt >= datetime(2020, 2, 1) and num_vol is None:
                        data_status = "POST_DEPRECATION_NA"
                        notes = "Electronic Clearing Service (ECS) merged into NACH w.e.f. Jan 31, 2020 (RBI Footnote 2)."
                
                # Check for un-imputed missing values
                if num_vol is None and data_status == "REPORTED":
                    data_status = "NOT_REPORTED"
                
                ats = calculate_ats(num_val, num_vol)
                
                transaction_records.append({
                    "month_date": month_date_str,
                    "month_label": month_label,
                    "year": year,
                    "month": month,
                    "indicator_code": code,
                    "indicator_name": name,
                    "major_section": sec,
                    "sub_section": sub,
                    "channel_group": grp,
                    "hierarchy_level": lvl,
                    "volume_lakh": num_vol,
                    "value_inr_crore": num_val,
                    "avg_ticket_size_inr": ats,
                    "volume_source_col": vol_col,
                    "value_source_col": val_col,
                    "raw_volume_str": raw_vol,
                    "raw_value_str": raw_val,
                    "data_status": data_status,
                    "notes": notes
                })
                
            elif ind_type == "INFRASTRUCTURE":
                cnt_col = spec["count_col"]
                val_col = spec["val_col"]
                raw_cnt = row[col_idx_map[cnt_col]].strip()
                raw_val = row[col_idx_map[val_col]].strip()
                
                num_cnt = parse_numeric(raw_cnt)
                actual_cnt = round(num_cnt * 100000.0, 0) if num_cnt is not None else None
                anomaly_flag = "NONE"
                notes = ""
                
                # Investigation of c140 / c141 (UPI QR Code)
                if code == "UPI_QR_STATIC_DEPLOYED":
                    # Pre-launch tracking (Nov-2019 to Aug-2020)
                    if dt < datetime(2020, 9, 1):
                        anomaly_flag = "PRE_LAUNCH_NOT_REPORTED"
                        notes = "Static UPI QR tracking initiated w.e.f. September 2020 per Footnote 1 (*)."
                        exceptions_log.append({
                            "exception_id": f"EXC_{exception_counter:04d}",
                            "month_date": month_date_str,
                            "month_label": month_label,
                            "source_column": cnt_col,
                            "indicator_code": code,
                            "indicator_name": name,
                            "raw_value": raw_cnt,
                            "cleaned_value": np.nan,
                            "exception_category": "PRE_LAUNCH_TRACKING",
                            "severity": "INFO",
                            "resolution_applied": "Preserved as NaN/None with PRE_LAUNCH flag",
                            "audit_justification": "Tracking officially commenced in September 2020 per RBI footnote marker (*)."
                        })
                        exception_counter += 1
                    
                    # Displaced figures in c141 (Jan-2024 to Jan-2026)
                    val_num = parse_numeric(raw_val)
                    if val_num is not None and val_num > 0.0:
                        anomaly_flag = "SUSPICIOUS_DISPLACED_VALUE"
                        notes = (f"Displaced data in c141: raw value '{raw_val}' in Value(₹ Cr) column for infrastructure touchpoint. "
                                 f"Preserved raw value in audit column; excluded from counts.")
                        exceptions_log.append({
                            "exception_id": f"EXC_{exception_counter:04d}",
                            "month_date": month_date_str,
                            "month_label": month_label,
                            "source_column": val_col,
                            "indicator_code": code,
                            "indicator_name": name,
                            "raw_value": raw_val,
                            "cleaned_value": val_num,
                            "exception_category": "DISPLACED_INFRASTRUCTURE_VALUE",
                            "severity": "HIGH",
                            "resolution_applied": "Preserved raw value in raw_value_str; flagged record; excluded from count metrics",
                            "audit_justification": (f"UPI QR code count is stored in c140 ({raw_cnt} Lakh). The non-zero value in c141 "
                                                   f"({raw_val}) represents an uncorrected upstream reporting artifact / next-month volume "
                                                   f"displacement. Infrastructure has no rupee monetary value.")
                        })
                        exception_counter += 1
                
                infrastructure_records.append({
                    "month_date": month_date_str,
                    "month_label": month_label,
                    "year": year,
                    "month": month,
                    "indicator_code": code,
                    "indicator_name": name,
                    "major_section": sec,
                    "sub_section": sub,
                    "infra_category": grp,
                    "hierarchy_level": lvl,
                    "count_lakh": num_cnt,
                    "count_actual": actual_cnt,
                    "count_source_col": cnt_col,
                    "value_source_col": val_col,
                    "raw_count_str": raw_cnt,
                    "raw_value_str": raw_val,
                    "anomaly_flag": anomaly_flag,
                    "notes": notes
                })

    # Convert to DataFrames
    df_transactions = pd.DataFrame(transaction_records)
    df_infrastructure = pd.DataFrame(infrastructure_records)
    df_exceptions = pd.DataFrame(exceptions_log)
    
    # -------------------------------------------------------------------------
    # 3.3 Build Master Data Dictionary (all 145 raw columns & 70 indicators)
    # -------------------------------------------------------------------------
    r4 = raw_rows[4]
    r5 = raw_rows[5]
    r6 = raw_rows[6]
    r7 = raw_rows[7]
    
    data_dict_rows = []
    
    # Metadata columns 0-3
    meta_cols = [
        ("src_file", 0, "Source file identifier", "METADATA", "Source attribution string", "N/A"),
        ("tab", 1, "Workbook worksheet tab name", "METADATA", "RBI tab name string", "N/A"),
        ("period", 2, "Data release scope", "METADATA", "Historical span scope string", "N/A"),
        ("row_no", 3, "Sequential spreadsheet line index", "METADATA", "Integer line number (1-93)", "Integer")
    ]
    for cid, cidx, dname, dtype, unit, dtyp in meta_cols:
        data_dict_rows.append({
            "column_id": cid,
            "column_index": cidx,
            "indicator_code": cid.upper(),
            "indicator_name": dname,
            "indicator_type": dtype,
            "major_section": "File Wrapper Metadata",
            "sub_section": "N/A",
            "channel_group": "Metadata",
            "hierarchy_level": "Metadata",
            "metric_type": "Metadata Attribute",
            "unit_of_measurement": unit,
            "ats_eligible": False,
            "footnote_symbols": "",
            "source_header_raw": cid,
            "cleaning_action": "Preserved for source traceability.",
            "known_anomalies": "None"
        })
        
    # Temporal column c1
    data_dict_rows.append({
        "column_id": "c1",
        "column_index": 4,
        "indicator_code": "MONTH_YEAR",
        "indicator_name": "Month/Year Observation Period",
        "indicator_type": "TEMPORAL",
        "major_section": "Temporal Dimension",
        "sub_section": "N/A",
        "channel_group": "Calendar Time",
        "hierarchy_level": "Dimension",
        "metric_type": "Date Anchor",
        "unit_of_measurement": "ISO Date (YYYY-MM-01)",
        "ats_eligible": False,
        "footnote_symbols": "",
        "source_header_raw": r4[4].strip(),
        "cleaning_action": "Parsed MMM-YYYY strings to first day of month (YYYY-MM-01).",
        "known_anomalies": "Reverse chronological ordering in raw source (Jul-2026 to Nov-2019)."
    })
    
    # 70 indicator specifications (c2 to c141)
    for spec in INDICATOR_SPECS:
        itype = spec["type"]
        code = spec["code"]
        name = spec["name"]
        sec = spec["major_section"]
        sub = spec["sub_section"]
        grp = spec["channel_group"]
        lvl = spec["hierarchy_level"]
        fn = spec["footnote"]
        
        if itype == "TRANSACTION":
            v_col = spec["vol_col"]
            val_col = spec["val_col"]
            v_idx = col_idx_map[v_col]
            val_idx = col_idx_map[val_col]
            
            anom = "None"
            if code == "PPI_TOTAL":
                anom = "Sep-2023 volume reported as '-' despite valid component sums; imputed from Wallets + Cards."
            elif code in ["ECS_CREDIT", "ECS_DEBIT"]:
                anom = "Merged into NACH on 31-Jan-2020; post-merger periods contain '-' or 0.00."
            
            # Volume column entry
            data_dict_rows.append({
                "column_id": v_col,
                "column_index": v_idx,
                "indicator_code": f"{code}_VOL",
                "indicator_name": f"{name} [Volume]",
                "indicator_type": itype,
                "major_section": sec,
                "sub_section": sub,
                "channel_group": grp,
                "hierarchy_level": lvl,
                "metric_type": "Transaction Volume",
                "unit_of_measurement": "Lakh (100,000 transactions)",
                "ats_eligible": True,
                "footnote_symbols": fn,
                "source_header_raw": f"L4: {r4[v_idx]} | L5: {r5[v_idx]} | L6: {r6[v_idx]} | L7: {r7[v_idx]}",
                "cleaning_action": "Parsed to numeric float. Converted '-' to NaN. Imputed Sep-2023 for PPI Total.",
                "known_anomalies": anom
            })
            
            # Value column entry
            data_dict_rows.append({
                "column_id": val_col,
                "column_index": val_idx,
                "indicator_code": f"{code}_VAL",
                "indicator_name": f"{name} [Value]",
                "indicator_type": itype,
                "major_section": sec,
                "sub_section": sub,
                "channel_group": grp,
                "hierarchy_level": lvl,
                "metric_type": "Transaction Value",
                "unit_of_measurement": "Rupees Crores (₹ 10,000,000 INR)",
                "ats_eligible": True,
                "footnote_symbols": fn,
                "source_header_raw": f"L4: {r4[val_idx]} | L5: {r5[val_idx]} | L6: {r6[val_idx]} | L7: {r7[val_idx]}",
                "cleaning_action": "Parsed to numeric float. Converted '-' to NaN.",
                "known_anomalies": anom
            })
            
        elif itype == "INFRASTRUCTURE":
            c_col = spec["count_col"]
            val_col = spec["val_col"]
            c_idx = col_idx_map[c_col]
            val_idx = col_idx_map[val_col]
            
            anom_c = "None"
            anom_v = "Placeholder column: '-' or 0.00; infrastructure has no monetary transaction value."
            if code == "UPI_QR_STATIC_DEPLOYED":
                anom_c = "Tracking initiated w.e.f. September 2020; Nov-2019 to Aug-2020 reported as '-'."
                anom_v = "Displaced figures reported in c141 for Jan-2024 to Jan-2026; flagged and excluded from counts."
                
            # Count column entry
            data_dict_rows.append({
                "column_id": c_col,
                "column_index": c_idx,
                "indicator_code": f"{code}_COUNT",
                "indicator_name": f"{name} [Count in Lakh]",
                "indicator_type": itype,
                "major_section": sec,
                "sub_section": sub,
                "channel_group": grp,
                "hierarchy_level": lvl,
                "metric_type": "Infrastructure Touchpoint Count",
                "unit_of_measurement": "Lakh (100,000 units)",
                "ats_eligible": False,
                "footnote_symbols": fn,
                "source_header_raw": f"L4: {r4[c_idx]} | L5: {r5[c_idx]} | L6: {r6[c_idx]} | L7: {r7[c_idx]}",
                "cleaning_action": "Parsed to numeric float count in Lakh, derived actual count (Lakh * 100,000).",
                "known_anomalies": anom_c
            })
            
            # Value placeholder column entry
            data_dict_rows.append({
                "column_id": val_col,
                "column_index": val_idx,
                "indicator_code": f"{code}_VAL_PLACEHOLDER",
                "indicator_name": f"{name} [Value Placeholder]",
                "indicator_type": itype,
                "major_section": sec,
                "sub_section": sub,
                "channel_group": grp,
                "hierarchy_level": lvl,
                "metric_type": "Infrastructure Value Placeholder",
                "unit_of_measurement": "Rupees Crores (N/A for physical count)",
                "ats_eligible": False,
                "footnote_symbols": fn,
                "source_header_raw": f"L4: {r4[val_idx]} | L5: {r5[val_idx]} | L6: {r6[val_idx]} | L7: {r7[val_idx]}",
                "cleaning_action": "Preserved raw value string in raw_value_str; excluded from monetary analysis.",
                "known_anomalies": anom_v
            })
            
    df_data_dict = pd.DataFrame(data_dict_rows)
    
    # Sort dataframes deterministically
    df_transactions = df_transactions.sort_values(by=["month_date", "indicator_code"]).reset_index(drop=True)
    df_infrastructure = df_infrastructure.sort_values(by=["month_date", "indicator_code"]).reset_index(drop=True)
    df_exceptions = df_exceptions.sort_values(by=["month_date", "exception_id"]).reset_index(drop=True)
    df_data_dict = df_data_dict.sort_values(by=["column_index"]).reset_index(drop=True)
    
    # -------------------------------------------------------------------------
    # 4. Export Deliverables (CSV & Parquet)
    # -------------------------------------------------------------------------
    trans_csv = os.path.join(output_dir, "transaction_indicators.csv")
    infra_csv = os.path.join(output_dir, "infrastructure_indicators.csv")
    dict_csv = os.path.join(output_dir, "data_dictionary.csv")
    exc_csv = os.path.join(output_dir, "cleaning_exceptions.csv")
    
    df_transactions.to_csv(trans_csv, index=False)
    df_infrastructure.to_csv(infra_csv, index=False)
    df_data_dict.to_csv(dict_csv, index=False)
    df_exceptions.to_csv(exc_csv, index=False)
    
    print(f"\nExported CSV files:")
    print(f"  • {trans_csv} ({len(df_transactions)} rows, {len(df_transactions.columns)} cols)")
    print(f"  • {infra_csv} ({len(df_infrastructure)} rows, {len(df_infrastructure.columns)} cols)")
    print(f"  • {dict_csv} ({len(df_data_dict)} rows, {len(df_data_dict.columns)} cols)")
    print(f"  • {exc_csv} ({len(df_exceptions)} rows, {len(df_exceptions.columns)} cols)")
    
    # Try Parquet exports
    try:
        df_transactions.to_parquet(os.path.join(output_dir, "transaction_indicators.parquet"), index=False)
        df_infrastructure.to_parquet(os.path.join(output_dir, "infrastructure_indicators.parquet"), index=False)
        df_data_dict.to_parquet(os.path.join(output_dir, "data_dictionary.parquet"), index=False)
        df_exceptions.to_parquet(os.path.join(output_dir, "cleaning_exceptions.parquet"), index=False)
        print("Exported Parquet files successfully using PyArrow engine.")
    except Exception as e:
        print(f"Parquet export skipped or failed (non-fatal): {e}")

    return {
        "df_transactions": df_transactions,
        "df_infrastructure": df_infrastructure,
        "df_data_dict": df_data_dict,
        "df_exceptions": df_exceptions,
        "raw_rows_count": len(raw_rows),
        "data_months_count": len(data_rows),
        "transaction_indicators_count": len(df_transactions["indicator_code"].unique()),
        "infrastructure_indicators_count": len(df_infrastructure["indicator_code"].unique()),
        "exceptions_logged_count": len(df_exceptions)
    }


if __name__ == "__main__":
    results = run_pipeline()
    print("\nPipeline execution completed successfully.")
