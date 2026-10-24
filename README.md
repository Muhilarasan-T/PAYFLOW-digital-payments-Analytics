# PAYFLOW — Digital Payments Intelligence & Trends Analysis

[![Dataset: RBI Payment System Indicators](https://img.shields.io/badge/Data_Source-Reserve_Bank_of_India-1f425f.svg)](https://dbie.rbi.org.in/)
[![Time Horizon: Nov 2019 – Jul 2026](https://img.shields.io/badge/Time_Horizon-Nov_2019_--_Jul_2026_(81_Months)-orange.svg)](docs/dataset_audit.md)
[![Status: Phase 1 Completed](https://img.shields.io/badge/Project_Status-Phase_1_Completed-green.svg)](#project-roadmap)
[![Tech Stack](https://img.shields.io/badge/Tech_Stack-Python_|_MySQL_|_Excel_|_Jupyter_|_Seaborn-blue.svg)](#tech-stack)

---

## 1. Project Overview

**PAYFLOW** is a professional, portfolio-grade Data Analytics project designed to investigate, model, and visualize the transformation of India's payment ecosystem from **November 2019 to July 2026**. 

Using authoritative monthly aggregate data published by the **Reserve Bank of India (RBI)**, PAYFLOW analyzes the structural shifts in macro payment settlement systems, the exponential adoption of the Unified Payments Interface (UPI), the evolution of credit versus debit card usage across Point of Sale (PoS) and e-commerce channels, the gradual phasing out of paper-based instruments (CTS cheques), and the expansion of digital acceptance infrastructures nationwide.

The project demonstrates an end-to-end analytics workflow: from forensic dataset auditing and automated tabular cleaning, to relational database modeling in MySQL, advanced exploratory data analysis in Python, statistical modeling, executive dashboard design in Excel, and publication-ready visualization storytelling.

---

## 2. Tech Stack

| Layer | Tools & Technologies | Purpose in PAYFLOW |
| :--- | :--- | :--- |
| **Language & Core Libraries** | Python 3.10+, Pandas, NumPy | Data ingestion, auditing, schema transformation, and feature engineering |
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
│   └── processed/                  # Cleaned, normalized, and transformed analytical outputs
│       └── .gitkeep
├── notebooks/                      # Jupyter notebooks for data cleaning, EDA, and modeling
│       └── .gitkeep
├── sql/                            # MySQL DDL, schema definitions, and analytical queries
│       └── .gitkeep
├── excel/                          # Excel workbooks, dynamic pivot models, and dashboards
│       └── .gitkeep
├── visuals/                        # Exported high-resolution charts, figures, and plots
│       └── .gitkeep
└── docs/                           # Documentation, data dictionaries, and audit reports
    ├── dataset_audit.md            # Comprehensive Phase 1 dataset audit report
    └── run_audit.py                # Standalone forensic validation script
```

---

## 5. Dataset Summary at a Glance

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PAYFLOW DATASET AT A GLANCE                     │
├──────────────────────────────┬─────────────────────────────────────────┤
│ Metric                       │ Value                                   │
├──────────────────────────────┼─────────────────────────────────────────┤
│ Raw Matrix Dimensions        │ 94 rows × 145 columns                   │
│ Data Time-Series Records     │ 81 consecutive months                   │
│ Time Range                   │ November 2019 – July 2026               │
│ Distinct Metric Pairs        │ 70 pairs (Volume in Lakh + Value in Cr) │
│ Header Hierarchy Levels      │ 4 tiers (Section > Sub > Instrument > Unit)│
│ Cell Population (Data Rows)  │ 11,340 cells evaluated                  │
│ Empty Cells                  │ 0 (100% complete)                       │
│ Numeric Float Values         │ 9,844 cells (86.8%)                     │
│ Dash Placeholders (" -")     │ 1,105 cells (9.7% — Infrastructure/ECS) │
│ Numeric Zeros                │ 391 cells (3.5%)                        │
│ Duplicate Records            │ 0 (100% unique monthly timeline)        │
└──────────────────────────────┴─────────────────────────────────────────┘
```

---

## 6. Key Business & Analytical Questions

PAYFLOW investigates realistic business intelligence questions grouped into eight distinct thematic domains:

1. **UPI Exponential Dominance:** How did UPI scale from 1.22 billion monthly transactions (39.7% of retail volume) in Nov-2019 to 23.66 billion transactions (87.0% of retail volume) in Jul-2026?
2. **Average Ticket Size (ATS) Polarization:** What is the ticket size trajectory of UPI ($\text{ATS} \approx ₹1,263$) versus NEFT ($\text{ATS} \approx ₹52,000$), IMPS ($\text{ATS} \approx ₹19,500$), and RTGS ($\text{ATS} \approx ₹6,140,000$)?
3. **Credit vs. Debit Card Usage Dynamics:** Why has debit card spending stagnated despite ~1.03 billion active cards, while credit cards (~123 million cards) generate superior transaction value driven by e-commerce adoption?
4. **The Decline of Paper Clearing (CTS):** At what rate is physical cheque volume declining, and why has the average cheque size doubled as retail users abandon paper for digital channels?
5. **Cash Withdrawal & ATM Utilization:** Are cash withdrawals at traditional ATMs declining, and what role are rural Micro-ATMs playing in cash-out accessibility?
6. **Merchant Acceptance Infrastructure:** How has the deployment of physical PoS terminals (~10 million) compared against the explosion of low-cost static UPI QR codes (~803 million)?
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

[Phase 2] Data Cleaning & Schema Transformation     [NEXT]
   ├── Unpivot wide layout into clean relational tidy table
   ├── Parse ISO dates (YYYY-MM-01) & standardize numeric fields
   ├── Resolve data anomalies (Sep-2023 PPI imputation, infrastructure value drops)
   └── Export to Parquet and CSV in data/processed/

[Phase 3] Database Engineering & SQL Modeling
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

## 9. Reproducibility & How to Run

### Prerequisites
- Python 3.10+
- Git

### Setup Instructions
```bash
# 1. Clone or navigate to the repository
cd PAYFLOW

# 2. Verify raw dataset presence
python -c "import os; print('Dataset exists:', os.path.exists('data/raw/612--payment-system-indicators--new-format.csv'))"

# 3. Run the automated forensic audit script
python docs/run_audit.py
```

---

## 10. Author & Project Metadata
- **Project Lead:** PAYFLOW Data Analytics Team
- **Specialization:** Digital Payments, Financial Technology (FinTech), Business Intelligence
- **Repository License:** Open Source for Educational and Portfolio Purposes
