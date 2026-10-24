-- ============================================================================
-- PAYFLOW — Database Engineering & SQL Modeling
-- Script 04: Data Quality Checks & Automated Validation Queries
-- Database: payflow_db
-- Dialect: MySQL 8.0+
-- ============================================================================

USE payflow_db;

-- ----------------------------------------------------------------------------
-- Check 1: Record Cardinality & Table Completeness
-- Verifies that loaded table row counts match expected source dimensions
-- ----------------------------------------------------------------------------
SELECT 
    'dim_date' AS table_name,
    COUNT(*) AS actual_rows,
    81 AS expected_rows,
    CASE WHEN COUNT(*) = 81 THEN 'PASS' ELSE 'FAIL' END AS check_status
FROM dim_date
UNION ALL
SELECT 
    'dim_payment_instrument',
    COUNT(*),
    70,
    CASE WHEN COUNT(*) = 70 THEN 'PASS' ELSE 'FAIL' END
FROM dim_payment_instrument
UNION ALL
SELECT 
    'fact_transaction_indicators',
    COUNT(*),
    4617,
    CASE WHEN COUNT(*) = 4617 THEN 'PASS' ELSE 'FAIL' END
FROM fact_transaction_indicators
UNION ALL
SELECT 
    'fact_infrastructure_indicators',
    COUNT(*),
    1053,
    CASE WHEN COUNT(*) = 1053 THEN 'PASS' ELSE 'FAIL' END
FROM fact_infrastructure_indicators
UNION ALL
SELECT 
    'audit_cleaning_exceptions',
    COUNT(*),
    36,
    CASE WHEN COUNT(*) = 36 THEN 'PASS' ELSE 'FAIL' END
FROM audit_cleaning_exceptions;

-- ----------------------------------------------------------------------------
-- Check 2: Temporal Span & Zero Calendar Gaps
-- Confirms continuous monthly coverage from Nov-2019 to Jul-2026
-- ----------------------------------------------------------------------------
SELECT 
    MIN(month_date) AS min_date,
    MAX(month_date) AS max_date,
    COUNT(DISTINCT month_date) AS total_distinct_months,
    TIMESTAMPDIFF(MONTH, MIN(month_date), MAX(month_date)) + 1 AS expected_consecutive_months,
    CASE 
        WHEN MIN(month_date) = '2019-11-01' 
         AND MAX(month_date) = '2026-07-01' 
         AND COUNT(DISTINCT month_date) = 81 
        THEN 'PASS' 
        ELSE 'FAIL' 
    END AS continuity_status
FROM dim_date;

-- ----------------------------------------------------------------------------
-- Check 3: Referential Integrity & Orphan Records
-- Verifies foreign keys link to valid parent dimensions
-- ----------------------------------------------------------------------------
SELECT 
    'fact_transaction_indicators -> dim_date' AS fk_relationship,
    COUNT(*) AS orphan_count,
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM fact_transaction_indicators f
LEFT JOIN dim_date d ON f.month_date = d.month_date
WHERE d.month_date IS NULL
UNION ALL
SELECT 
    'fact_transaction_indicators -> dim_payment_instrument',
    COUNT(*),
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM fact_transaction_indicators f
LEFT JOIN dim_payment_instrument p ON f.indicator_code = p.indicator_code
WHERE p.indicator_code IS NULL
UNION ALL
SELECT 
    'fact_infrastructure_indicators -> dim_date',
    COUNT(*),
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM fact_infrastructure_indicators f
LEFT JOIN dim_date d ON f.month_date = d.month_date
WHERE d.month_date IS NULL
UNION ALL
SELECT 
    'fact_infrastructure_indicators -> dim_payment_instrument',
    COUNT(*),
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM fact_infrastructure_indicators f
LEFT JOIN dim_payment_instrument p ON f.indicator_code = p.indicator_code
WHERE p.indicator_code IS NULL;

-- ----------------------------------------------------------------------------
-- Check 4: Non-Negativity & Domain Range Check
-- Verifies no volumes, values, ticket sizes, or counts are negative (< 0)
-- ----------------------------------------------------------------------------
SELECT 
    'Negative Volumes' AS anomaly_type,
    COUNT(*) AS violation_count,
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM fact_transaction_indicators
WHERE volume_lakh < 0.0
UNION ALL
SELECT 
    'Negative Values',
    COUNT(*),
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM fact_transaction_indicators
WHERE value_inr_crore < 0.0
UNION ALL
SELECT 
    'Negative Average Ticket Sizes',
    COUNT(*),
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM fact_transaction_indicators
WHERE avg_ticket_size_inr < 0.0
UNION ALL
SELECT 
    'Negative Infrastructure Counts',
    COUNT(*),
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM fact_infrastructure_indicators
WHERE count_lakh < 0.0;

-- ----------------------------------------------------------------------------
-- Check 5: Average Ticket Size (ATS) Formula Consistency
-- Validates: ATS = (Value in Cr / Volume in Lakh) * 100 within 0.02 INR
-- ----------------------------------------------------------------------------
SELECT 
    COUNT(*) AS total_ats_evaluated,
    MAX(ABS(avg_ticket_size_inr - ROUND((value_inr_crore / volume_lakh) * 100.0, 2))) AS max_deviation_inr,
    CASE 
        WHEN MAX(ABS(avg_ticket_size_inr - ROUND((value_inr_crore / volume_lakh) * 100.0, 2))) <= 0.02 
        THEN 'PASS' 
        ELSE 'FAIL' 
    END AS calculation_status
FROM fact_transaction_indicators
WHERE volume_lakh > 0.0 
  AND value_inr_crore IS NOT NULL;

-- ----------------------------------------------------------------------------
-- Check 6: Mathematical Reconciliations (Selected Key Totals)
-- Compares reported parent aggregates against component sums across all 81 months
-- ----------------------------------------------------------------------------
WITH monthly_reconciliation AS (
    SELECT 
        month_date,
        -- RTGS Total vs Customer + Interbank
        MAX(CASE WHEN indicator_code = 'RTGS_TOTAL' THEN volume_lakh END) AS rtgs_vol,
        SUM(CASE WHEN indicator_code IN ('RTGS_CUSTOMER', 'RTGS_INTERBANK') THEN volume_lakh ELSE 0 END) AS rtgs_vol_sum,
        MAX(CASE WHEN indicator_code = 'RTGS_TOTAL' THEN value_inr_crore END) AS rtgs_val,
        SUM(CASE WHEN indicator_code IN ('RTGS_CUSTOMER', 'RTGS_INTERBANK') THEN value_inr_crore ELSE 0 END) AS rtgs_val_sum,
        
        -- Card Payments Total vs Credit Total + Debit Total
        MAX(CASE WHEN indicator_code = 'CARD_PAYMENTS_TOTAL' THEN volume_lakh END) AS cards_vol,
        SUM(CASE WHEN indicator_code IN ('CREDIT_CARDS_TOTAL', 'DEBIT_CARDS_TOTAL') THEN volume_lakh ELSE 0 END) AS cards_vol_sum,
        
        -- Total Payments vs RTGS + Retail Payments
        MAX(CASE WHEN indicator_code = 'TOTAL_PAYMENTS' THEN volume_lakh END) AS tot_pay_vol,
        MAX(CASE WHEN indicator_code = 'RTGS_TOTAL' THEN volume_lakh END) + 
        MAX(CASE WHEN indicator_code = 'TOTAL_RETAIL_PAYMENTS' THEN volume_lakh END) AS tot_pay_vol_sum,
        
        -- Total Digital Payments vs Total Payments - Paper
        MAX(CASE WHEN indicator_code = 'TOTAL_DIGITAL_PAYMENTS' THEN volume_lakh END) AS digital_vol,
        MAX(CASE WHEN indicator_code = 'TOTAL_PAYMENTS' THEN volume_lakh END) - 
        MAX(CASE WHEN indicator_code = 'PAPER_TOTAL' THEN volume_lakh END) AS digital_vol_sum
    FROM fact_transaction_indicators
    GROUP BY month_date
)
SELECT 
    'RTGS Volume = Customer + Interbank' AS rule_name,
    COUNT(*) AS total_months_checked,
    SUM(CASE WHEN ABS(rtgs_vol - rtgs_vol_sum) <= 0.05 THEN 1 ELSE 0 END) AS passing_months,
    MAX(ABS(rtgs_vol - rtgs_vol_sum)) AS max_diff,
    CASE WHEN MIN(CASE WHEN ABS(rtgs_vol - rtgs_vol_sum) <= 0.05 THEN 1 ELSE 0 END) = 1 THEN 'PASS' ELSE 'FAIL' END AS status
FROM monthly_reconciliation
UNION ALL
SELECT 
    'RTGS Value = Customer + Interbank',
    COUNT(*),
    SUM(CASE WHEN ABS(rtgs_val - rtgs_val_sum) <= 0.05 THEN 1 ELSE 0 END),
    MAX(ABS(rtgs_val - rtgs_val_sum)),
    CASE WHEN MIN(CASE WHEN ABS(rtgs_val - rtgs_val_sum) <= 0.05 THEN 1 ELSE 0 END) = 1 THEN 'PASS' ELSE 'FAIL' END
FROM monthly_reconciliation
UNION ALL
SELECT 
    'Total Cards Volume = Credit Total + Debit Total',
    COUNT(*),
    SUM(CASE WHEN ABS(cards_vol - cards_vol_sum) <= 0.05 THEN 1 ELSE 0 END),
    MAX(ABS(cards_vol - cards_vol_sum)),
    CASE WHEN MIN(CASE WHEN ABS(cards_vol - cards_vol_sum) <= 0.05 THEN 1 ELSE 0 END) = 1 THEN 'PASS' ELSE 'FAIL' END
FROM monthly_reconciliation
UNION ALL
SELECT 
    'Total Payments Volume = RTGS + Retail Payments',
    COUNT(*),
    SUM(CASE WHEN ABS(tot_pay_vol - tot_pay_vol_sum) <= 0.05 THEN 1 ELSE 0 END),
    MAX(ABS(tot_pay_vol - tot_pay_vol_sum)),
    CASE WHEN MIN(CASE WHEN ABS(tot_pay_vol - tot_pay_vol_sum) <= 0.05 THEN 1 ELSE 0 END) = 1 THEN 'PASS' ELSE 'FAIL' END
FROM monthly_reconciliation
UNION ALL
SELECT 
    'Total Digital Volume = Total Payments - Paper Total',
    COUNT(*),
    SUM(CASE WHEN ABS(digital_vol - digital_vol_sum) <= 0.05 THEN 1 ELSE 0 END),
    MAX(ABS(digital_vol - digital_vol_sum)),
    CASE WHEN MIN(CASE WHEN ABS(digital_vol - digital_vol_sum) <= 0.05 THEN 1 ELSE 0 END) = 1 THEN 'PASS' ELSE 'FAIL' END
FROM monthly_reconciliation;

-- ----------------------------------------------------------------------------
-- Check 7: Anomaly & Exception Flag Audit
-- Confirms that anomalies logged in audit_cleaning_exceptions are represented
-- ----------------------------------------------------------------------------
SELECT 
    exception_category,
    severity,
    COUNT(*) AS logged_exception_count
FROM audit_cleaning_exceptions
GROUP BY exception_category, severity
ORDER BY logged_exception_count DESC;
