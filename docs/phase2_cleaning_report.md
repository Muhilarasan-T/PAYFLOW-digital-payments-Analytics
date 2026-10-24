# PAYFLOW — Phase 2: Data Cleaning & Schema Normalization Report

**Project:** PAYFLOW — Digital Payments Intelligence & Trends Analysis  
**Phase:** Phase 2 — Data Cleaning & Schema Normalization  
**Pipeline Script:** [`src/clean_data.py`](file:///c:/Users/DELL/PAYFLOW/src/clean_data.py)  
**Author:** PAYFLOW Data Analytics Team  
**Date:** October 2026  
**Status:** Completed & Validated  

---

## 1. Executive Summary

Phase 2 transforms the Reserve Bank of India (RBI) Payment System Indicators from an immutable, multi-tier hierarchical spreadsheet export into **analysis-ready, normalized relational datasets**. 

The pipeline guarantees strict source traceability, enforces explicit data type conversions, separates incompatible metric types (transaction flows vs. physical infrastructure touchpoints), provides mathematical ticket size derivation, programmatically investigates and documents data anomalies without silent alterations, and exports both CSV and high-performance Apache Parquet formats.

```
┌────────────────────────────────────────────────────────────────────────┐
│                      PHASE 2 TRANSFORMATION FLOW                       │
├───────────────────────────────┬────────────────────────────────────────┤
│ Source Input                  │ data/raw/612--payment-system-indicators│
│                               │ --new-format.csv (94 rows × 145 cols)  │
├───────────────────────────────┼────────────────────────────────────────┤
│ Pipeline Execution            │ src/clean_data.py                      │
├───────────────────────────────┼────────────────────────────────────────┤
│ Primary Analysis Datasets     │ • data/processed/transaction_indicators│
│                               │   (4,617 rows × 19 columns)            │
│                               │ • data/processed/infrastructure_       │
│                               │   indicators.csv (1,053 rows × 18 cols)│
├───────────────────────────────┼────────────────────────────────────────┤
│ Governance & Audit Artifacts  │ • data/processed/data_dictionary.csv   │
│                               │   (145 rows × 16 columns)              │
│                               │ • data/processed/cleaning_exceptions   │
│                               │   .csv (36 rows × 12 columns)          │
├───────────────────────────────┼────────────────────────────────────────┤
│ Performance Engine            │ Apache Parquet exports generated       │
│                               │ alongside standard CSV files           │
└───────────────────────────────┴────────────────────────────────────────┘
```

---

## 2. Source Ingestion & Structural Normalization

### 2.1 File Preservation
The original dataset [`data/raw/612--payment-system-indicators--new-format.csv`](file:///c:/Users/DELL/PAYFLOW/data/raw/612--payment-system-indicators--new-format.csv) remains **100% byte-for-byte immutable**. The transformation pipeline in [`src/clean_data.py`](file:///c:/Users/DELL/PAYFLOW/src/clean_data.py) operates entirely as a non-destructive reader that extracts raw tokens and writes cleanly to `data/processed/`.

### 2.2 Boundary Identification
The pipeline programmatically demarcates the 94 lines into functional zones:
- **Rows 1–3 (row_no 1 to 3):** File-level metadata, blank padding, and report header (`Payment System Indicators`).
- **Rows 4–7 (row_no 4 to 7):** Hierarchical headers:
  - Row 4: Major Section (`A. Settlement Systems`, `B. Payment Systems`, etc.)
  - Row 5: Sub-section (`FMIs`, `II Retail`)
  - Row 6: Instrument / Channel Indicator Name
  - Row 7: Metric and Unit (`Volume (Lakh)`, `Value( Rupees Crores )`)
- **Rows 8–88 (row_no 8 to 88):** Exactly 81 consecutive monthly time-series records.
- **Rows 89–93 (row_no 89 to 93):** Regulatory footnotes, symbol keys (`@`, `$`, `*`), and methodological notes.

### 2.3 Temporal Normalization
Raw string labels in column `c1` (e.g., `Jul-2026`, `Jun-2026`, down to `Nov-2019`) are parsed into first-day-of-month ISO dates (`YYYY-MM-01`). For analytical convenience, calendar dimensions `year` (int) and `month` (int) are explicitly generated.

---

## 3. Numeric Standardization & Missing-Value Policy

A core tenet of Phase 2 is avoiding synthetic data generation and never equating missingness with zero.

| Raw Source Representation | Cleaned Numeric Representation | Data Status Flag | Treatment Rationale |
| :--- | :---: | :--- | :--- |
| **Standard float** (e.g. `"236583.53"`) | `236583.53` (`float64`) | `REPORTED` | Clean numeric value; stripped of commas and whitespace. |
| **Genuine zero** (e.g. `"0.00"`) | `0.0` (`float64`) | `REPORTED` | Preserved as numeric zero; signifies genuine zero activity. |
| **Dash placeholder** (`" -"`, `"-"`) | `NaN` / `None` | `NOT_REPORTED` | Source indicated unrecorded, unavailable, or non-tracked metric. |
| **Deprecated Rail Dash** (ECS post-Jan 2020) | `NaN` / `None` | `POST_DEPRECATION_NA` | Deprecated per Footnote 2 (merged into NACH). |
| **Pre-Launch Dash** (UPI QR pre-Sep 2020) | `NaN` / `None` | `PRE_LAUNCH_NOT_REPORTED`| Officially commenced tracking in Sep-2020 per Footnote 1 (`*`). |
| **Anomalous Missing Total** (Sep-2023 PPI Vol) | `6143.17` (`float64`) | `DERIVED_SUM_CORRECTION` | Arithmetic and structure justify imputation from components. |

---

## 4. Incompatible Metric Separation

To eliminate structural confusion between transaction flows and physical equipment counts, the pipeline partitions indicators into two separate schema tables:

### 4.1 Transaction Indicators (`data/processed/transaction_indicators.csv`)
- **Scope:** 57 distinct payment rails, settlement systems, card categories, paper instruments, and official macro aggregates.
- **Dimensions:**
  - `month_date`: Standard ISO date (`YYYY-MM-01`)
  - `month_label`: Original month string (`MMM-YYYY`)
  - `year`, `month`: Temporal integers
  - `indicator_code`: Unique uppercase snake_case identifier (e.g. `UPI`, `NEFT`, `RTGS_CUSTOMER`, `CREDIT_CARDS_POS`)
  - `indicator_name`: Official RBI title (e.g. `2.7 UPI @`)
  - `major_section`, `sub_section`, `channel_group`: Three-tier organizational taxonomy
  - `hierarchy_level`: `Component`, `Subtotal`, `Category_Total`, `Grand_Total`
  - `volume_lakh`: Transaction count in Lakhs ($1\text{ Lakh} = 100,000$ txns)
  - `value_inr_crore`: Monetary spend in ₹ Crores ($1\text{ Crore} = ₹10,000,000$ INR)
  - `avg_ticket_size_inr`: Average transaction size in INR:
    $$\text{ATS (INR)} = \frac{\text{Value in ₹ Crores} \times 10,000,000}{\text{Volume in Lakh} \times 100,000} = \frac{\text{Value in ₹ Crores}}{\text{Volume in Lakh}} \times 100$$
  - `volume_source_col`, `value_source_col`: Exact raw columns (e.g. `c36`, `c37`)
  - `raw_volume_str`, `raw_value_str`: Raw cell text preserved for auditability
  - `data_status`: Audit state (`REPORTED`, `DERIVED_SUM_CORRECTION`, `POST_DEPRECATION_NA`)
  - `notes`: Specific context or regulatory notes
- **Volume:** $57\text{ indicators} \times 81\text{ months} = \mathbf{4,617\text{ rows}}$.

### 4.2 Infrastructure Indicators (`data/processed/infrastructure_indicators.csv`)
- **Scope:** 13 physical hardware touchpoints, card issuances, and merchant acceptance QR codes.
- **Dimensions:**
  - `month_date`, `month_label`, `year`, `month`
  - `indicator_code`: e.g. `CARDS_CREDIT_OUTSTANDING`, `ATMS_BANK_OWNED`, `POS_TERMINALS_DEPLOYED`, `UPI_QR_STATIC_DEPLOYED`
  - `indicator_name`: Official RBI title
  - `major_section`, `sub_section`, `infra_category`
  - `hierarchy_level`: `Component`, `Category_Total`
  - `count_lakh`: Active units in Lakhs
  - `count_actual`: Total discrete units ($\text{count\_lakh} \times 100,000$)
  - `count_source_col`, `value_source_col`: Raw column coordinates
  - `raw_count_str`: Raw count text
  - `raw_value_str`: Raw text from the redundant "Value" column
  - `anomaly_flag`: `NONE`, `PRE_LAUNCH_NOT_REPORTED`, `SUSPICIOUS_DISPLACED_VALUE`
  - `notes`: Detailed context
- **Volume:** $13\text{ indicators} \times 81\text{ months} = \mathbf{1,053\text{ rows}}$.
- **Constraint Compliance:** Average ticket size is strictly **omitted** from infrastructure indicators. Infrastructure counts are never conflated with transaction volumes.

---

## 5. Forensic Anomaly Investigations & Resolutions

### Anomaly 1: Displaced Numeric Data in Column `c141` (UPI QR Value)
- **Investigation:**  
  Column `c141` represents the "Value (Rupees Crores)" column adjacent to `c140` (`7 UPI QR *`). For physical infrastructure touchpoints, monetary transaction value is not applicable, and all other 12 infrastructure value columns (`c117` to `c139`) contain `" -"` or `0.00`.  
  However, from **January 2024 to January 2026 (25 consecutive months)**, non-zero values appear in `c141` (e.g., `3,379.94` in Jan-2024, scaling to `7,574.12` in Jan-2026).
- **Forensic Findings:**  
  1. The numbers are of the exact order of magnitude of the UPI QR counts (`c140`), but with a consistent positive delta ($+160$ to $+200$ Lakh).
  2. Prior to Jan-2024, `c141` contains `" -"`; after Jan-2026, it reverts to `" -"` / `0.00`.
  3. No source note defines a rupee value for QR code stickers.
  4. The numbers represent either an uncorrected column displacement, next-month revised count, or dynamic QR deployment in upstream RBI data.
- **Resolution Applied:**  
  - **No silent deletion or shifting:** The raw string is preserved in `raw_value_str`.
  - The record is flagged with `anomaly_flag = "SUSPICIOUS_DISPLACED_VALUE"`.
  - Column `c141` is excluded from count metrics in `infrastructure_indicators.csv`.
  - All 25 affected months are logged with `severity = "HIGH"` in `cleaning_exceptions.csv`.

### Anomaly 2: September 2023 Total PPI Volume Omission (`c64`)
- **Investigation:**  
  In `Sep-2023`, `c64` (`5 Prepaid Payment Instruments (5.1 to 5.2)`) contains `" -"`, while reported value `c65 = 23,667.78` is fully populated.
- **Forensic Findings:**  
  1. Component 5.1 (Wallets, `c66`): Volume = $4,927.10$ Lakh, Value = $₹19,944.07$ Cr.
  2. Component 5.2 (Cards, `c68`): Volume = $1,216.07$ Lakh, Value = $₹3,723.71$ Cr.
  3. Reported Total Value matches component sum exactly:
     $$19,944.07 + 3,723.71 = 23,667.78\text{ (Exact match to c65)}$$
  4. In all other 80 months, `c64` equals $c66 + c68$ without exception.
- **Resolution Applied:**  
  - Imputation is mathematically and structurally justified:
    $$\text{Imputed Volume} = 4,927.10 + 1,216.07 = \mathbf{6,143.17\text{ Lakh}}$$
  - Both original (`" -"`) and corrected (`6143.17`) values are captured in `transaction_indicators.csv`.
  - The record is marked with `data_status = "DERIVED_SUM_CORRECTION"`.
  - Full audit justification logged in `cleaning_exceptions.csv`.

### Anomaly 3: Deprecated ECS Lineage (`c28`, `c29`, `c44`, `c45`)
- **Investigation:**  
  Per Footnote 2, ECS Credit and Debit were merged into NACH on January 31, 2020. Post-January 2020, cells are `" -"` or `0.00`.
- **Resolution Applied:**  
  - For months after Jan-2020, missing values are set to `NaN` and flagged with `POST_DEPRECATION_NA`.
  - Genuine data for Nov-2019 to Jan-2020 is preserved as `REPORTED`.

### Anomaly 4: Delayed Launch of Static UPI QR (`c140`)
- **Investigation:**  
  Footnote 1 (`*`) confirms static UPI QR tracking began in September 2020.
- **Resolution Applied:**  
  - The preceding 10 months (Nov-2019 to Aug-2020) are preserved as `NaN` (not zero) and assigned `anomaly_flag = "PRE_LAUNCH_NOT_REPORTED"`.
  - Documented as 10 distinct records in `cleaning_exceptions.csv`.

---

## 6. Output Deliverables Directory

All deliverables have been generated in [`data/processed/`](file:///c:/Users/DELL/PAYFLOW/data/processed/):

| File Path | Format | Records | Columns | Purpose |
| :--- | :---: | :---: | :---: | :--- |
| [`data/processed/transaction_indicators.csv`](file:///c:/Users/DELL/PAYFLOW/data/processed/transaction_indicators.csv) | CSV | 4,617 | 19 | Normalized monthly transaction volume, value, and average ticket size. |
| [`data/processed/transaction_indicators.parquet`](file:///c:/Users/DELL/PAYFLOW/data/processed/transaction_indicators.parquet) | Parquet | 4,617 | 19 | High-performance columnar version. |
| [`data/processed/infrastructure_indicators.csv`](file:///c:/Users/DELL/PAYFLOW/data/processed/infrastructure_indicators.csv) | CSV | 1,053 | 18 | Monthly physical touchpoint counts with audit values and anomaly flags. |
| [`data/processed/infrastructure_indicators.parquet`](file:///c:/Users/DELL/PAYFLOW/data/processed/infrastructure_indicators.parquet) | Parquet | 1,053 | 18 | High-performance columnar version. |
| [`data/processed/data_dictionary.csv`](file:///c:/Users/DELL/PAYFLOW/data/processed/data_dictionary.csv) | CSV | 145 | 16 | Complete field-level data dictionary for all raw source columns. |
| [`data/processed/data_dictionary.parquet`](file:///c:/Users/DELL/PAYFLOW/data/processed/data_dictionary.parquet) | Parquet | 145 | 16 | Columnar version of data dictionary. |
| [`data/processed/cleaning_exceptions.csv`](file:///c:/Users/DELL/PAYFLOW/data/processed/cleaning_exceptions.csv) | CSV | 36 | 12 | Comprehensive register of all anomalies, imputations, and displaced values. |
| [`data/processed/cleaning_exceptions.parquet`](file:///c:/Users/DELL/PAYFLOW/data/processed/cleaning_exceptions.parquet) | Parquet | 36 | 12 | Columnar version of cleaning exceptions register. |

---

## 7. Automated Test & Validation Summary

A standalone test suite [`tests/test_cleaning.py`](file:///c:/Users/DELL/PAYFLOW/tests/test_cleaning.py) was executed using `pytest`. All **13 unit and integration test suites passed** with zero failures:

1. `test_monthly_continuity`: Confirms 81 unique months, start `2019-11-01`, end `2026-07-01`, zero gaps.
2. `test_record_counts`: Confirms 4,617 transaction rows, 1,053 infrastructure rows, 145 dictionary columns, 36 exceptions.
3. `test_unique_keys`: Confirms zero duplicate `(month_date, indicator_code)` composite keys.
4. `test_non_negativity`: Confirms zero negative numbers across all volume, value, and count fields.
5. `test_average_ticket_size_formula`: Confirms ATS strictly equals $\frac{\text{Value}}{\text{Volume}} \times 100$ within $0.01$ INR tolerance.
6. `test_sep_2023_ppi_imputation`: Validates imputation of $6,143.17$ Lakh and preservation of raw `" -"`.
7. `test_upi_qr_anomaly_isolation`: Validates 10 pre-launch months and 25 displaced `c141` months.
8. `test_source_column_traceability`: Confirms 100% of indicators trace to valid raw CSV columns.
9. `test_rtgs_reconciliation`: Confirms $\text{RTGS Total} = \text{Customer} + \text{Interbank}$ ($100\%$ pass).
10. `test_card_payments_reconciliation`: Confirms $\text{Total Cards} = \text{Credit} + \text{Debit}$ ($100\%$ pass).
11. `test_total_payments_reconciliation`: Confirms $\text{Total Payments} = \text{RTGS} + \text{Retail}$ ($100\%$ pass).
12. `test_digital_payments_reconciliation`: Confirms $\text{Digital Payments} = \text{Total Payments} - \text{Paper}$ ($100\%$ pass).
13. `test_exceptions_schema_and_parquet`: Confirms full schema adherence and CSV/Parquet parity.

Detailed mathematical verification tables and discrepancy disclosures are documented in [`docs/phase2_validation_report.md`](file:///c:/Users/DELL/PAYFLOW/docs/phase2_validation_report.md).
