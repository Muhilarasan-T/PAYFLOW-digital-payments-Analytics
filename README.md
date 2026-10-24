# PAYFLOW — Digital Payments Intelligence & Trends Analysis

[![Dataset: RBI Payment System Indicators](https://img.shields.io/badge/Data_Source-Reserve_Bank_of_India-1f425f.svg)](https://dbie.rbi.org.in/)
[![Time Horizon: Nov 2019 – Jul 2026](https://img.shields.io/badge/Time_Horizon-Nov_2019_--_Jul_2026_(81_Months)-orange.svg)](docs/dataset_audit.md)
[![Status: Phase 4 Completed](https://img.shields.io/badge/Project_Status-Phase_4_Completed-green.svg)](#project-roadmap)
[![Database: MySQL 8.0 Star Schema](https://img.shields.io/badge/Database-MySQL_8.0_Star_Schema-blue.svg)](sql/02_create_tables.sql)
[![Automated Tests](https://img.shields.io/badge/Tests-21%2F21_Passed_(pytest)-brightgreen.svg)](tests/test_phase4_eda.py)

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
| **Relational Database & SQL** | MySQL 8.0+ / SQLite (`sql/`) | Normalized Star Schema, DDL constraints, window queries, and CTE aggregations |
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
│   └── processed/                  # Normalized, analysis-ready datasets (CSV, Parquet, DB)
│       ├── transaction_indicators.csv       # 57 payment rails, volumes, values, ticket sizes
│       ├── transaction_indicators.parquet   # High-performance columnar version
│       ├── infrastructure_indicators.csv    # 13 hardware touchpoint counts & audit flags
│       ├── infrastructure_indicators.parquet# High-performance columnar version
│       ├── data_dictionary.csv              # Full documentation of all 145 raw columns
│       ├── data_dictionary.parquet          # High-performance columnar version
│       ├── cleaning_exceptions.csv          # Register of all 36 flagged anomalies & imputations
│       ├── cleaning_exceptions.parquet      # High-performance columnar version
│       └── payflow.db                       # Embedded SQLite analytical mirror database
├── src/                            # Production ETL, database loader, and EDA analysis scripts
│   ├── __init__.py
│   ├── clean_data.py               # Automated ingestion, cleaning, and normalization pipeline
│   ├── reconcile_check.py          # Standalone 22-rule reconciliation test script
│   ├── load_data_to_mysql.py       # Star Schema loader for MySQL and analytical database
│   ├── run_analysis_queries.py     # SQL query execution and results harvesting engine
│   ├── phase4_eda.py               # Exploratory data analysis, statistical modeling & chart generation
│   └── build_notebook.py           # Programmatic builder for reproducible Jupyter Notebook
├── sql/                            # Production MySQL 8.0 DDL, loaders, and queries
│   ├── 01_create_database.sql      # Database creation and utf8mb4 collation setup
│   ├── 02_create_tables.sql        # Star schema DDL with keys, constraints, and indexes
│   ├── 03_load_data.sql            # CTE date generator & LOAD DATA LOCAL INFILE scripts
│   ├── 04_data_quality_checks.sql  # 7 automated data-quality and reconciliation checks
│   └── 05_business_analysis.sql    # 10 advanced business intelligence SQL queries
├── tests/                          # Automated test suites for validation & quality assurance
│   ├── __init__.py
│   ├── test_cleaning.py            # 13 pytest suites validating data integrity & math reconciliations
│   └── test_phase4_eda.py          # 8 pytest suites validating EDA aggregations, ratios & consistency
├── notebooks/                      # Jupyter notebooks for data cleaning, EDA, and modeling
│   └── phase4_exploratory_data_analysis.ipynb # 11-stage comprehensive reproducible EDA notebook
├── excel/                          # Excel workbooks, dynamic pivot models, and dashboards
├── visuals/                        # Exported high-resolution charts, figures, and plots
│   └── phase4/                     # 9 publication-grade 300 DPI exploratory analysis figures
└── docs/                           # Documentation, data dictionaries, and audit reports
    ├── dataset_audit.md            # Comprehensive Phase 1 dataset audit report
    ├── phase2_cleaning_report.md   # Phase 2 cleaning methodology and anomaly resolutions
    ├── phase2_validation_report.md # Phase 2 mathematical reconciliation & test audit report
    ├── phase3_database_report.md   # Phase 3 database architecture, SQL queries, and results
    └── phase4_eda_report.md        # Phase 4 exploratory data analysis & statistical findings report
```

---

## 5. Database Schema & SQL Architecture (Phase 3)

The database layer implements an analytical **Star Schema** optimized for high-performance aggregations and window analytics:

```
                            ┌────────────────────────┐
                            │        dim_date        │
                            ├────────────────────────┤
                            │ PK: month_date (DATE)  │
                            │ month_label (Nov-2019) │
                            │ calendar_year (2019)   │
                            │ calendar_month (1-12)  │
                            │ fiscal_year (FY 24-25) │
                            │ fiscal_quarter (Q1-Q4) │
                            │ days_in_month (28-31)  │
                            └───────────┬────────────┘
                                        │ 1:N
                     ┌──────────────────┴──────────────────┐
                     │ 1:N                                 │ 1:N
        ┌────────────▼─────────────┐          ┌────────────▼─────────────┐
        │fact_transaction_indicat..│          │fact_infrastructure_indic..│
        ├──────────────────────────┤          ├──────────────────────────┤
        │ PK: transaction_id       │          │ PK: infrastructure_id    │
        │ FK: month_date           │          │ FK: month_date           │
        │ FK: indicator_code       │          │ FK: indicator_code       │
        │ volume_lakh (DECIMAL)    │          │ count_lakh (DECIMAL)     │
        │ value_inr_crore (DECIMAL)│          │ count_actual (BIGINT)    │
        │ avg_ticket_size_inr (DEC)│          │ count_source_col (c140)  │
        │ volume_source_col (c36)  │          │ value_source_col (c141)  │
        │ value_source_col (c37)   │          │ raw_count_str (VARCHAR)  │
        │ raw_volume_str (VARCHAR) │          │ raw_value_str (VARCHAR)  │
        │ raw_value_str (VARCHAR)  │          │ anomaly_flag (VARCHAR)   │
        │ data_status (REPORTED)   │          └────────────▲─────────────┘
        └────────────▲─────────────┘                       │ 1:N
                     │ 1:N                                 │
                     └──────────────────┬──────────────────┘
                                        │ 1:N
                        ┌───────────────┴───────────────┐
                        │    dim_payment_instrument     │
                        ├───────────────────────────────┤
                        │ PK: indicator_code (VARCHAR)  │
                        │ indicator_name (UPI, NEFT)    │
                        │ indicator_type (TXN / INFRA)  │
                        │ major_section (Payment Systems│
                        │ sub_section (II Retail)       │
                        │ channel_group (Credit Transfer│
                        │ hierarchy_level (Component)   │
                        │ volume_source_col / val_col   │
                        │ ats_eligible (BOOLEAN)        │
                        └───────────────────────────────┘
```

### Table Cardinality Overview
- **`dim_date`**: 81 rows (continuous monthly timeline from Nov-2019 to Jul-2026).
- **`dim_payment_instrument`**: 70 rows (57 transaction rails + 13 physical touchpoints).
- **`fact_transaction_indicators`**: 4,617 rows ($57 \times 81$, zero missing primary keys).
- **`fact_infrastructure_indicators`**: 1,053 rows ($13 \times 81$, touchpoint counts & audit strings).
- **`audit_cleaning_exceptions`**: 36 rows (complete audit trail of all anomalies and imputations).

---

## 6. Key Business Intelligence Findings from SQL Analysis

| Business Analysis Domain | Core SQL Techniques Used | Key Verified Empirical Finding |
| :--- | :--- | :--- |
| **1. Monthly UPI Scale** | CTEs, `LAG() OVER`, Metric Scaling | In July 2026, UPI processed **23.66 Billion transactions** valued at **₹29.88 Trillion INR** ($\text{ATS} \approx ₹1,263$). March features regular $+10\%\text{--}11\%$ fiscal year-end surges. |
| **2. UPI Retail Market Share** | Conditional Aggregations, Ratios | UPI retail volume share expanded from **39.7% in 2019** to **86.8% in 2026**. UPI value share grew from **6.2% to 30.3%**. |
| **3. Growth Momentum Across Rails** | Window `LAG(1m)`, `LAG(12m)` | Credit card volume grew **+24.5% YoY** and UPI grew **+21.5% YoY** in Jul-2026; Debit card volume fell **-9.4% YoY** and IMPS fell **-24.4% YoY**. |
| **4. Average Ticket Size (ATS)** | Cross-Instrument Pivots, Ratio Math | UPI ATS stabilized at **₹1,260–₹1,300** (micro-payments); IMPS doubled from **₹8,350 to ₹19,161** (mid-value transfers); NEFT stabilized at **₹50,000–₹52,000** (B2B); RTGS averaged **₹6.1 Million INR**. |
| **5. Credit vs. Debit Cards** | Channel Slicing, Conditional Aggregations | Credit card spend exploded from ₹6.4T (2020) to **₹23.95T (2025)** driven by **62% e-commerce**; Debit card spend dropped from ₹6.6T to ₹4.4T. Credit-to-Debit spend ratio surged from **0.97x to 5.46x**. |
| **6. Paper Cheques Demise** | Dual-Axis Time Series, Volume/Value Ratios | Digital payments reached **99.98% volume share** and **98.0% value share**. While cheque volume halved, average cheque size doubled from **₹74,425 to ₹144,834**, confining cheques to high-value B2B/real estate. |
| **7. Merchant Infrastructure** | Touchpoint Pivots, QR-to-PoS Ratio | Physical PoS terminals expanded from 4.4M (2020) to **10.0M (2026)**; static UPI QR codes exploded from zero to **803 Million codes**—an **80:1 ratio**. |
| **8. Cash vs. Digital Dynamics** | Displacement Ratios, ATS Calculations | ATM cash withdrawals peaked in 2022 (₹32.9T) and declined to ₹29.0T (2025). The cash-out to digital payment ratio fell from **2.38% to 0.78%**, while average withdrawal size rose from **₹4,707 to ₹5,507**. |
| **9. Growth Leaders Ranking** | Multi-Year Baselines, `DENSE_RANK()` | Top growth: **UPI (+1,427.4%)**, Mobile Banking (+1,156.6%), PPI PoS (+1,023.0%). Declining: ECS Credit (-100%), PoS Cash Debit (-99.8%), Debit Online (-84.8%). |
| **10. Forensic Anomaly Audit** | Severity Grouping, `GROUP_CONCAT()` | 25 displaced figures in column `c141` isolated; 10 pre-launch QR months flagged; 1 derived imputation for Sep-2023 PPI Volume documented. |

---

## 7. Project Roadmap

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

[Phase 3] Database Engineering & SQL Modeling      [COMPLETED]
   ├── Design normalized MySQL Star Schema (Fact + Dimensions)
   ├── Author DDL, loader, and QC scripts in sql/
   ├── Companion Python loader (src/load_data_to_mysql.py)
   ├── Execution of 10 advanced analytical business queries
   └── Phase 3 database engineering report (docs/phase3_database_report.md)

[Phase 4] Exploratory Data Analysis & Python Modeling [COMPLETED]
   ├── 11-stage EDA pipeline in Jupyter (notebooks/phase4_exploratory_data_analysis.ipynb)
   ├── 9 publication-grade 300 DPI visualizations (visuals/phase4/)
   ├── Statistical decomposition, ATS polarization, card inversion & seasonality modeling
   ├── Automated unit test suite (tests/test_phase4_eda.py — 8/8 passed, 21/21 total)
   └── Comprehensive Phase 4 analytical report (docs/phase4_eda_report.md)

[Phase 5] Data Visualization & Executive Reporting   [NEXT]
   ├── Interactive Excel analytical dashboard with dynamic slicers in excel/
   ├── Executive summary workbook with automated KPIs and pivot models
   └── Presentation-ready visual storytelling assets

[Phase 6] Synthesis & Portfolio Finalization
   ├── Executive summary report
   ├── Technical walkthrough & documentation wrap-up
   └── Repository polish for GitHub showcase
```

---

## 8. Reproducibility & Database Execution

### Prerequisites
- Python 3.10+
- MySQL 8.0+ (Optional; embedded analytical database engine included)

### Database Setup Instructions
```bash
# 1. Run the end-to-end data cleaning pipeline (Phase 2)
python src/clean_data.py

# 2. Run the automated data integrity test suite
python -m pytest tests/test_cleaning.py -v

# 3. Populate database and execute the Star Schema loader
python src/load_data_to_mysql.py

# 4. Execute all 10 analytical business queries
python src/run_analysis_queries.py

# 5. Direct MySQL 8.0 Command-Line Execution:
mysql -u root -p payflow_db < sql/01_create_database.sql
mysql -u root -p payflow_db < sql/02_create_tables.sql
mysql -u root -p payflow_db < sql/03_load_data.sql
mysql -u root -p payflow_db < sql/04_data_quality_checks.sql
mysql -u root -p payflow_db < sql/05_business_analysis.sql
```

---

## 9. Author & Project Metadata
- **Project Lead:** PAYFLOW Data Analytics Team
- **Specialization:** Digital Payments, Financial Technology (FinTech), Database Engineering & Business Intelligence
- **Repository License:** Open Source for Educational and Portfolio Purposes
