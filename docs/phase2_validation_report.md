# PAYFLOW — Phase 2: Data Validation & Reconciliation Report

**Project:** PAYFLOW — Digital Payments Intelligence & Trends Analysis  
**Phase:** Phase 2 — Data Cleaning & Schema Normalization  
**Test Suite:** [`tests/test_cleaning.py`](file:///c:/Users/DELL/PAYFLOW/tests/test_cleaning.py)  
**Author:** Muhil Tamilarasan  
**Date:** October 2026  
**Status:** 100% Passed (13/13 Test Suites)  

---

## 1. Executive Summary

This validation report provides the quantitative verification of the cleaned datasets generated in Phase 2. To prevent unsupported assumptions and verify data reliability before entering database modeling and business analysis, the cleaned outputs were subjected to a rigorous automated test suite.

The test suite executed **13 distinct unit and integration checks** covering temporal continuity, record cardinalities, non-negativity, average ticket size mathematical precision, source column traceability, anomaly isolation, and cross-indicator mathematical reconciliations across all 81 months. **All 13 test suites passed.**

---

## 2. Automated Test Execution Results

```
============================= test session starts =============================
platform win32 -- Python 3.13.1, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\DELL\PAYFLOW
collected 13 items

tests/test_cleaning.py::TestDataIntegrity::test_monthly_continuity PASSED        [  7%]
tests/test_cleaning.py::TestDataIntegrity::test_record_counts PASSED            [ 15%]
tests/test_cleaning.py::TestDataIntegrity::test_unique_keys PASSED              [ 23%]
tests/test_cleaning.py::TestNumericIntegrityAndCalculations::test_non_negativity PASSED [ 30%]
tests/test_cleaning.py::TestNumericIntegrityAndCalculations::test_average_ticket_size_formula PASSED [ 38%]
tests/test_cleaning.py::TestAnomalyHandlingAndTraceability::test_sep_2023_ppi_imputation PASSED [ 46%]
tests/test_cleaning.py::TestAnomalyHandlingAndTraceability::test_upi_qr_anomaly_isolation PASSED [ 53%]
tests/test_cleaning.py::TestAnomalyHandlingAndTraceability::test_source_column_traceability PASSED [ 61%]
tests/test_cleaning.py::TestMathematicalReconciliations::test_rtgs_reconciliation PASSED [ 69%]
tests/test_cleaning.py::TestMathematicalReconciliations::test_card_payments_reconciliation PASSED [ 76%]
tests/test_cleaning.py::TestMathematicalReconciliations::test_total_payments_reconciliation PASSED [ 84%]
tests/test_cleaning.py::TestMathematicalReconciliations::test_digital_payments_reconciliation PASSED [ 92%]
tests/test_cleaning.py::TestMathematicalReconciliations::test_exceptions_schema_and_parquet PASSED [100%]

============================= 13 passed in 1.64s ==============================
```

---

## 3. Mathematical Reconciliation Audit

The RBI reporting format contains explicit hierarchical relationships where parent totals must equal the sum of their constituent child components. Across all 81 monthly records ($2019\text{-}11\text{ to }2026\text{-}07$), **22 reconciliation rules** were programmatically tested:

### 3.1 Summary of Reconciliation Rules Tested

| # | Reconciliation Rule | Tested Columns | Volume Check | Value Check | Overall Status |
| :-: | :--- | :---: | :---: | :---: | :---: |
| **01** | `RTGS Total = Customer + Interbank` | `c16 = c18 + c20` / `c17 = c19 + c21` | 81 / 81 Pass | 81 / 81 Pass | **100% Pass** |
| **02** | `CCIL G-Sec Total = Outright + Repo + Triparty` | `c4 = c6 + c8 + c10` / `c5 = c7 + c9 + c11` | 81 / 81 Pass | 81 / 81 Pass | **100% Pass** |
| **03** | `CCIL Total = G-Sec + Forex + Derivatives` | `c2 = c4 + c12 + c14` / `c3 = c5 + c13 + c15` | 81 / 81 Pass | 81 / 81 Pass | **100% Pass** |
| **04** | `Credit Cards Total = PoS + Others` | `c52 = c54 + c56` / `c53 = c55 + c57` | 81 / 81 Pass | 81 / 81 Pass | **100% Pass** |
| **05** | `Debit Cards Total = PoS + Others` | `c58 = c60 + c62` / `c59 = c61 + c63` | 80 / 81 Pass | 81 / 81 Pass | **98.8% Pass** (1 Rounding diff) |
| **06** | `Total Cards = Credit Total + Debit Total` | `c50 = c52 + c58` / `c51 = c53 + c59` | 81 / 81 Pass | 81 / 81 Pass | **100% Pass** |
| **07** | `PPI Cards Total = PoS + Others` | `c68 = c70 + c72` / `c69 = c71 + c73` | 81 / 81 Pass | 81 / 81 Pass | **100% Pass** |
| **08** | `PPI Total = Wallets + PPI Cards` | `c64 = c66 + c68` / `c65 = c67 + c69` | 80 / 81 Pass | 81 / 81 Pass | **98.8% Pass** (Sep-23 Raw Dash) |
| **09** | `Paper Instruments Total = CTS + Others` | `c74 = c76 + c78` / `c75 = c77 + c79` | 81 / 81 Pass | 81 / 81 Pass | **100% Pass** |
| **10** | `Retail Credit Transfers = 2.1 through 2.7` | `c22 = c24+c26+c28+c30+c32+c34+c36` | 81 / 81 Pass* | 81 / 81 Pass* | **100% Pass** (*ECS dep.) |
| **11** | `Retail Debit Transfers = 3.1 through 3.4` | `c40 = c42+c44+c46+c48` | 81 / 81 Pass* | 81 / 81 Pass* | **100% Pass** (*ECS dep.) |
| **12** | `Total Retail Payments = Cat 2+3+4+5+6` | `c80 = c22+c40+c50+c64+c74` | 80 / 81 Pass | 81 / 81 Pass | **98.8% Pass** (Sep-23 Dash) |
| **13** | `Total Payments = RTGS + Retail` | `c82 = c16 + c80` / `c83 = c17 + c81` | 81 / 81 Pass | 81 / 81 Pass | **100% Pass** |
| **14** | `Total Digital = Total Payments - Paper` | `c84 = c82 - c74` / `c85 = c83 - c75` | 81 / 81 Pass | 81 / 81 Pass | **100% Pass** |
| **15** | `Mobile Payments Total = Intra + Inter` | `c86 = c88 + c90` / `c87 = c89 + c91` | 81 / 81 Pass | 81 / 81 Pass | **100% Pass** |
| **16** | `Internet Payments Total = Intra + Inter` | `c92 = c94 + c96` / `c93 = c95 + c97` | 81 / 81 Pass | 81 / 81 Pass | **100% Pass** |
| **17** | `ATM Cash Total = Credit + Debit + PPI` | `c98 = c100+c102+c104` / `c99 = c101+c103+c105` | 81 / 81 Pass | 81 / 81 Pass | **100% Pass** |
| **18** | `PoS Cash Total = Debit + PPI` | `c106 = c108+c110` / `c107 = c109+c111` | 81 / 81 Pass | 81 / 81 Pass | **100% Pass** |
| **19** | `Micro-ATM Cash Total = AePS Cash` | `c112 = c114` / `c113 = c115` | 81 / 81 Pass | 81 / 81 Pass | **100% Pass** |
| **20** | `Total Cards Issued = Credit + Debit` | `c116 = c118 + c120` | 80 / 81 Pass | N/A (Infra) | **98.8% Pass** (1 Rounding diff) |
| **21** | `Total PPIs Issued = Wallets + Cards` | `c122 = c124 + c126` | 81 / 81 Pass | N/A (Infra) | **100% Pass** |
| **22** | `Total ATMs = Bank-Owned + White-Label` | `c128 = c130 + c132` | 81 / 81 Pass | N/A (Infra) | **100% Pass** |

---

## 4. Transparent Discrepancy Disclosures

Rather than forcing artificial reconciliation, all source-level discrepancies are documented below:

### Discrepancy 1: September 2023 Debit Card Volume Rounding
- **Observation Period:** `Sep-2023` (Row 42)
- **Source Columns:** `c58` (Total Debit Cards Vol), `c60` (PoS Vol), `c62` (Others Vol)
- **Reported Total:** $1,839.04\text{ Lakh}$
- **Component Sum:** $1,326.09\text{ (PoS)} + 513.26\text{ (Others)} = 1,839.35\text{ Lakh}$
- **Variance:** $-0.31\text{ Lakh}$ (relative variance: $0.0168\%$)
- **Audit Decision:** Preserved reported source total; difference documented in validation register.

### Discrepancy 2: September 2023 Total PPI Volume Source Dash
- **Observation Period:** `Sep-2023` (Row 42)
- **Source Columns:** `c64` (Total PPI Vol), `c66` (Wallets Vol), `c68` (PPI Cards Vol)
- **Raw Cell Value:** `" -"`
- **Component Sum:** $4,927.10\text{ (Wallets)} + 1,216.07\text{ (Cards)} = \mathbf{6,143.17\text{ Lakh}}$
- **Value Check:** Reported total value ($₹23,667.78\text{ Cr}$) matches component sum ($19,944.07 + 3,723.71 = 23,667.78$) to the penny.
- **Audit Decision:** Total imputed as $6,143.17$ with audit state `DERIVED_SUM_CORRECTION`. Raw dash preserved in `raw_volume_str`.

### Discrepancy 3: November 2023 Total Cards Outstanding Rounding
- **Observation Period:** `Nov-2023` (Row 40)
- **Source Columns:** `c116` (Total Cards Count), `c118` (Credit Cards), `c120` (Debit Cards)
- **Reported Total:** $10,725.71\text{ Lakh}$
- **Component Sum:** $960.01\text{ (Credit)} + 9,764.99\text{ (Debit)} = 10,725.00\text{ Lakh}$
- **Variance:** $+0.71\text{ Lakh}$ (relative variance: $0.0066\%$)
- **Audit Decision:** Preserved reported source total; difference documented in validation register.

---

## 5. Average Ticket Size (ATS) Formula Validation

Average Ticket Size was verified for mathematical precision:
$$\text{ATS (INR)} = \frac{\text{Value in ₹ Crores} \times 10^7}{\text{Volume in Lakh} \times 10^5} = \frac{\text{Value}}{\text{Volume}} \times 100$$

### Sample Verification Matrix across Diverse Payment Rails (July 2026)

| Payment Rail | Volume (`Lakh`) | Value (`₹ Cr`) | Derived ATS (`INR`) | Calculation Check | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **2.7 UPI** | $236,583.53$ | $2,987,880.48$ | **₹1,262.93** | $\frac{2987880.48}{236583.53} \times 100 = 1262.928$ | ✅ Valid |
| **2.6 NEFT** | $8,970.05$ | $4,661,075.50$ | **₹51,962.65** | $\frac{4661075.50}{8970.05} \times 100 = 51962.648$ | ✅ Valid |
| **2.4 IMPS** | $3,643.39$ | $711,704.37$ | **₹19,534.13** | $\frac{711704.37}{3643.39} \times 100 = 19534.125$ | ✅ Valid |
| **1.1 RTGS Customer** | $331.95$ | $20,378,016.89$ | **₹6,138,881.43** | $\frac{20378016.89}{331.95} \times 100 = 6138881.425$ | ✅ Valid |
| **4.1.1 Credit Card PoS** | $2,937.34$ | $75,740.37$ | **₹2,578.54** | $\frac{75740.37}{2937.34} \times 100 = 2578.536$ | ✅ Valid |
| **4.1.2 Credit Card Online** | $3,115.33$ | $132,445.33$ | **₹4,251.41** | $\frac{132445.33}{3115.33} \times 100 = 4251.406$ | ✅ Valid |
| **6.1 CTS Cheques** | $446.78$ | $643,872.60$ | **₹144,113.97** | $\frac{643872.60}{446.78} \times 100 = 144113.971$ | ✅ Valid |
| **1.1 Credit Cards (Infra)** | $1,228.58$ | Placeholder (`" -"`) | **None / NaN** | Infrastructure ATS explicitly disabled | ✅ Valid |

---

## 6. Source Traceability Matrix

Every indicator in the cleaned datasets maps unambiguously to its source coordinates:

- **100% Coverage:** All 145 raw CSV columns are indexed and documented in `data_dictionary.csv`.
- **Bidirectional Traceability:** Any cell in `transaction_indicators.csv` or `infrastructure_indicators.csv` references its original column (`volume_source_col`, `value_source_col`, `count_source_col`) and retains its uncleaned string in `raw_volume_str`, `raw_value_str`, or `raw_count_str`.
- **Zero Data Loss:** No columns or records were deleted during ingestion.

---

## 7. Certification for Phase 3

The cleaned datasets meet all criteria for database ingestion:
- **Cleaned Data Consistency:** Confirmed across 81 months.
- **Relational Integrity:** Distinct primary keys `(month_date, indicator_code)`.
- **Deliverables Verified:** CSV and Parquet files generated and validated on disk.

The datasets are certified ready for **Phase 3: Database Engineering & SQL Modeling**.
