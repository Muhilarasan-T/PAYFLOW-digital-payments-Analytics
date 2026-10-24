# PAYFLOW — Digital Payments Intelligence & Trends Analysis

[![Dataset: RBI Payment System Indicators](https://img.shields.io/badge/Data_Source-Reserve_Bank_of_India-1f425f.svg)](https://dbie.rbi.org.in/)
[![Time Horizon: Nov 2019 – Jul 2026](https://img.shields.io/badge/Time_Horizon-Nov_2019_--_Jul_2026_(81_Months)-orange.svg)](docs/dataset_audit.md)
[![Status: Phase 2 Completed](https://img.shields.io/badge/Project_Status-Phase_2_Completed-green.svg)](#project-roadmap)
[![Automated Tests](https://img.shields.io/badge/Tests-13%2F13_Passed_(pytest)-brightgreen.svg)](tests/test_cleaning.py)
[![Tech Stack](https://img.shields.io/badge/Tech_Stack-Python_|_Pandas_|_PyArrow_|_MySQL_|_Excel_|_Jupyter-blue.svg)](#tech-stack)

---

## 1. Project Overview

**PAYFLOW** is a professional, portfolio-grade Data Analytics project designed to investigate, model, and visualize the transformation of India's payment ecosystem from **November 2019 to July 2026**. 

Using authoritative monthly aggregate data published by the **Reserve Bank of India (RBI)**, PAYFLOW analyzes the structural shifts in macro payment settlement systems, the exponential adoption of the Unified Payments Interface (UPI), the evolution of credit versus debit card usage across Point of Sale (PoS) and e-commerce channels, the gradual phasing out of paper-based instruments (CTS cheques), and the expansion of digital acceptance infrastructures nationwide.

The project demonstrates an end-to-end analytics workflow: from forensic dataset auditing and automated tabular cleaning, to relational database modeling in MySQL, advanced exploratory data analysis in Python, statistical modeling, executive dashboard design in Excel, and publication-ready visualization storytelling.

---

## 2. Tech Stack

| Layer | Tools & Technologies | Purpose in PAYFLOW |
| :--- | :--- | :--- |
| **Language & Core Libraries** | Python 3.10+, Pandas, NumPy, PyArrow | Data ingestion, auditing, schema transformation, and feature engineering |
| **Testing & Quality Assurance** | Pytest (`tests/`) | Automated unit testing, reconciliation verification, and schema validation |
| **Relational Database** | MySQL 8.0+ / SQL | Relational schema design, normalization, staging tables, and analytical window queries |
| **Interactive Analytics** | Jupyter Notebook (`notebooks/`) | Step-by-step exploratory analysis, hypothesis validation, and reproducible pipelines |
| **Spreadsheet Modeling** | Microsoft Excel (`excel/`) | Executive summaries, automated pivot tables, KPI cards, and dynamic slicers |
| **Visualization & Reporting** | Matplotlib, Seaborn (`visuals/`) | Publication-quality time-series charts, area distributions, and correlation heatmaps |
| **Version Control & Docs** | Git, GitHub, Markdown (`docs/`) | Version history, documentation integrity, and reproducible portfolio presentation |

---

## 3. Dataset Attribution & Provenance

- **Data Source:** [Reserve Bank of India (RBI) Database on Indian Economy (DBIE)](https://dbie.rbi.org.in/)
- **Publication Table:** **Table No. 612: "Payment System Indicators" (New Format)**
- **Reporting Period:** **November 2019 (`Nov-2019`) to July 2026 (`Jul-2026`)** — exactly **81 continuous months**.
- **Nature of Data:** Official macro-level national monthly aggregates tracking transaction volume (in Lakh) and transaction value (in ₹ Crores) across retail and wholesale payment systems, alongside active payment infrastructure counts.
- **Raw File:** Preserved untouched at [`data/raw/612--payment-system-indicators--new-format.csv`](file:///c:/Users/DELL/PAYFLOW/data/raw/612--payment-system-indicators--new-format.csv).
- **Audit Documentation:** Detailed forensic inspection documented at [`docs/dataset_audit.md`](file:///c:/Users/DELL/PAYFLOW/docs/dataset_audit.md).

---

## 4. Project Directory Structure

```text
PAYFLOW/
├── .gitignore                      # Git exclusion rules for clean version control
├── README.md                       # Master project overview, architecture, and roadmap
├── data/
│   ├── raw/                        # Immutable, untouched source data files
│   │   └── 612--payment-system-indicators--new-format.csv
│   └── processed/                  # Normalized, analysis-ready datasets (CSV & Parquet)
│       ├── transaction_indicators.csv       # 57 payment rails, volumes, values, ticket sizes
│       ├── transaction_indicators.parquet   # High-performance columnar version
│       ├── infrastructure_indicators.csv    # 13 hardware touchpoint counts & audit flags
│       ├── infrastructure_indicators.parquet# High-performance columnar version
│       ├── data_dictionary.csv              # Full documentation of all 145 raw columns
│       ├── data_dictionary.parquet          # High-performance columnar version
│       ├── cleaning_exceptions.csv          # Register of all 36 flagged anomalies & imputations
│       └── cleaning_exceptions.parquet      # High-performance columnar version
├── src/                            # Production ETL and data engineering scripts
│   ├── __init__.py
│   ├── clean_data.py               # Automated ingestion, cleaning, and normalization pipeline
│   └── reconcile_check.py          # Standalone 22-rule reconciliation test script
├── tests/                          # Automated test suites for validation & quality assurance
│   ├── __init__.py
│   └── test_cleaning.py            # 13 pytest suites validating data integrity & math reconciliations
├── notebooks/                      # Jupyter notebooks for data cleaning, EDA, and modeling
├── sql/                            # MySQL DDL, schema definitions, and analytical queries
├── excel/                          # Excel workbooks, dynamic pivot models, and dashboards
├── visuals/                        # Exported high-resolution charts, figures, and plots
└── docs/                           # Documentation, data dictionaries, and audit reports
    ├── dataset_audit.md            # Comprehensive Phase 1 dataset audit report
    ├── phase2_cleaning_report.md   # Phase 2 cleaning methodology and anomaly resolutions
    └── phase2_validation_report.md # Phase 2 mathematical reconciliation & test audit report
```

---

## 5. Processed Datasets at a Glance (Phase 2 Outputs)

| Processed Dataset | Primary Records | Dimensions | File Formats | Description |
| :--- | :---: | :---: | :---: | :--- |
| **`transaction_indicators`** | **4,617 rows** ($57\text{ indicators} \times 81\text{ months}$) | 19 columns | CSV, Parquet | Monthly payment rail volume in Lakh, monetary value in ₹ Crores, and derived Average Ticket Size (ATS in INR). |
| **`infrastructure_indicators`** | **1,053 rows** ($13\text{ indicators} \times 81\text{ months}$) | 18 columns | CSV, Parquet | Monthly active infrastructure counts (Cards in force, ATMs, PoS terminals, QR codes) with audit columns and anomaly flags. |
| **`data_dictionary`** | **145 rows** (100% of raw source columns) | 16 columns | CSV, Parquet | Field-level catalog linking raw columns (`c1`–`c141`) to clean codes, hierarchy, units, and cleaning rules. |
| **`cleaning_exceptions`** | **36 rows** | 12 columns | CSV, Parquet | Forensic register of all anomalies: 1 derived PPI imputation (`Sep-2023`), 10 pre-launch QR months, and 25 displaced `c141` values. |

---

## 6. Key Business & Analytical Questions

PAYFLOW investigates realistic business intelligence questions grouped into eight distinct thematic domains:

1. **UPI Exponential Dominance:** How did UPI scale from 1.22 billion monthly transactions (39.7% of retail volume) in Nov-2019 to 23.66 billion transactions (87.0% of retail volume) in Jul-2026?
2. **Average Ticket Size (ATS) Polarization:** What is the ticket size trajectory of UPI ($\text{ATS} \approx ₹1,263$) versus NEFT ($\text{ATS} \approx ₹52,000$), IMPS ($\text{ATS} \approx ₹19,500$), and RTGS ($\text{ATS} \approx ₹6,140,000$)?
3. **Credit vs. Debit Card Usage Dynamics:** Why has debit card spending stalled despite $\sim 1.03\text{B}$ cards in force, while credit cards ($\sim 123\text{M}$ cards) generate superior transaction value driven by e-commerce adoption?
4. **The Decline of Paper Clearing (CTS):** At what rate is physical cheque volume declining, and why has the average cheque size doubled as retail users abandon paper for digital channels?
5. **Cash Withdrawal & ATM Utilization:** Are cash withdrawals at traditional ATMs declining, and what role are rural Micro-ATMs playing in cash-out accessibility?
6. **Merchant Acceptance Infrastructure:** How has the deployment of physical PoS terminals ($\sim 10\text{M}$) scaled compared to asset-light static UPI QR codes ($\sim 803\text{M}$)?
7. **Financial Inclusion Payment Rails:** What are the volume and value growth rates of Aadhaar Payment Bridge System (APBS) and AePS across rural banking corridors?
8. **Macroeconomic Shocks & Festive Seasonality:** How did payments contract during the April–May 2020 COVID-19 lockdown, and how pronounced are festive season surges in October–November and fiscal year-end surges in March?

---

## 7. Analytical Scope & Boundaries

To ensure rigorous data integrity and avoid speculative modeling, PAYFLOW enforces strict analytical boundaries:

### In-Scope
- Macroeconomic national trends in volume, value, market share, and ticket size.
- Channel comparison across digital, paper, card, mobile, and internet banking.
- Payment infrastructure growth ratios (PoS vs. QR, Bank ATMs vs. White Label ATMs).
- Seasonality and time-series growth rate analysis (MoM, YoY, CAGR).

### Out-of-Scope (Data Not Available in RBI Table 612)
- **Bank-Level Market Share:** No bank-specific dimensions (no SBI, HDFC, ICICI, etc.).
- **UPI P2P vs. P2M Split:** Reported as a combined national UPI figure.
- **Merchant Category Spend:** No Merchant Category Codes (MCC) or sector breakdowns (retail, travel, fuel).
- **Geographic / Regional Breakdown:** No state, city, or urban/rural tags.
- **Consumer Demographics:** No user age, gender, credit score, or account balance data.
- **Operational Failures / Latency:** Failed transactions, reversals, and chargebacks are excluded by RBI.

---

## 8. Project Roadmap

```
[Phase 1] Dataset Audit & Project Setup             [COMPLETED]
   ├── File inspection & integrity audit
   ├── Directory architecture setup
   ├── Comprehensive audit report (docs/dataset_audit.md)
   └── Initial project documentation (README.md)

[Phase 2] Data Cleaning & Schema Normalization     [COMPLETED]
   ├── Automated cleaning pipeline (src/clean_data.py)
   ├── Separation of transaction and infrastructure tables
   ├── Average ticket size derivation & anomaly resolutions
   ├── Export of CSV and Parquet deliverables in data/processed/
   ├── Automated test suite (tests/test_cleaning.py — 13/13 passed)
   └── Cleaning & validation reports (docs/phase2_cleaning_report.md)

[Phase 3] Database Engineering & SQL Modeling      [NEXT]
   ├── Design normalized MySQL star schema (Fact + Dimensions)
   ├── Create DDL scripts & ingestion pipeline in sql/
   └── Author complex SQL queries (CAGR, rolling averages, market share)

[Phase 4] Exploratory Data Analysis & Python Modeling
   ├── Statistical summaries & distribution analysis in Jupyter
   ├── Time-series decomposition & seasonality indexing
   └── Ticket-size correlation and growth trajectory modeling

[Phase 5] Data Visualization & Executive Reporting
   ├── Publication-quality Seaborn & Matplotlib figures in visuals/
   ├── Interactive Excel analytical dashboard with dynamic slicers in excel/
   └── Stakeholder-ready business intelligence presentation

[Phase 6] Synthesis & Portfolio Finalization
   ├── Executive summary report
   ├── Technical walkthrough & documentation wrap-up
   └── Repository polish for GitHub showcase
```

---

## 9. Reproducibility & Automated Verification

### Prerequisites
- Python 3.10+
- Git

### Execution Instructions
```bash
# 1. Run the end-to-end data cleaning and normalization pipeline
python src/clean_data.py

# 2. Run the automated test suite to verify data integrity
python -m pytest tests/test_cleaning.py -v
```

---

## 10. Author & Project Metadata
- **Project Lead:** PAYFLOW Data Analytics Team
- **Specialization:** Digital Payments, Financial Technology (FinTech), Business Intelligence
- **Repository License:** Open Source for Educational and Portfolio Purposes
