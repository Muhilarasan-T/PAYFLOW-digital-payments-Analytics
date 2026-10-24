-- ============================================================================
-- PAYFLOW — Database Engineering & SQL Modeling
-- Script 05: Analytical Business Queries (10 Strategic Domains)
-- Database: payflow_db
-- Dialect: MySQL 8.0+
-- Concepts Used: Common Table Expressions (CTEs), Window Functions (LAG, LEAD,
--                SUM OVER, AVG OVER, DENSE_RANK), Conditional Aggregation,
--                Date Dimensions, and Ratio Calculations.
-- ============================================================================

USE payflow_db;

-- ============================================================================
-- Business Query 1: Monthly UPI Transaction Volume and Value Trends
-- Examines the longitudinal trajectory of UPI, calculating Volume in Billions,
-- Value in ₹ Trillions, derived ticket size, and Month-over-Month (MoM) growth.
-- ============================================================================
WITH upi_monthly AS (
    SELECT 
        d.month_date,
        d.month_label,
        d.calendar_year,
        f.volume_lakh,
        f.value_inr_crore,
        f.avg_ticket_size_inr,
        -- Conversions to standard business units:
        -- 1 Lakh = 100,000 => 10,000 Lakh = 1 Billion transactions
        ROUND(f.volume_lakh / 10000.0, 3) AS volume_billion_txns,
        -- 1 Crore = 10 Million => 100,000 Crore = 1 Trillion INR
        ROUND(f.value_inr_crore / 100000.0, 3) AS value_trillion_inr,
        -- Window function to obtain previous month values
        LAG(f.volume_lakh) OVER (ORDER BY d.month_date) AS prev_month_vol,
        LAG(f.value_inr_crore) OVER (ORDER BY d.month_date) AS prev_month_val
    FROM fact_transaction_indicators f
    JOIN dim_date d ON f.month_date = d.month_date
    WHERE f.indicator_code = 'UPI'
)
SELECT 
    month_date,
    month_label,
    volume_billion_txns,
    value_trillion_inr,
    avg_ticket_size_inr,
    ROUND(((volume_lakh - prev_month_vol) / NULLIF(prev_month_vol, 0)) * 100.0, 2) AS mom_volume_growth_pct,
    ROUND(((value_inr_crore - prev_month_val) / NULLIF(prev_month_val, 0)) * 100.0, 2) AS mom_value_growth_pct
FROM upi_monthly
ORDER BY month_date DESC;


-- ============================================================================
-- Business Query 2: UPI Share of Retail Payment Volume & Value Over Time
-- Quantifies UPI's cannibalization and dominance of total retail payments,
-- tracking annual volume and value penetration from 2019 to 2026.
-- ============================================================================
WITH retail_vs_upi AS (
    SELECT 
        d.calendar_year,
        d.month_date,
        MAX(CASE WHEN f.indicator_code = 'UPI' THEN f.volume_lakh END) AS upi_vol,
        MAX(CASE WHEN f.indicator_code = 'TOTAL_RETAIL_PAYMENTS' THEN f.volume_lakh END) AS retail_vol,
        MAX(CASE WHEN f.indicator_code = 'UPI' THEN f.value_inr_crore END) AS upi_val,
        MAX(CASE WHEN f.indicator_code = 'TOTAL_RETAIL_PAYMENTS' THEN f.value_inr_crore END) AS retail_val
    FROM fact_transaction_indicators f
    JOIN dim_date d ON f.month_date = d.month_date
    WHERE f.indicator_code IN ('UPI', 'TOTAL_RETAIL_PAYMENTS')
    GROUP BY d.calendar_year, d.month_date
)
SELECT 
    calendar_year,
    COUNT(month_date) AS months_observed,
    ROUND(SUM(upi_vol) / 10000.0, 2) AS annual_upi_vol_billions,
    ROUND(SUM(retail_vol) / 10000.0, 2) AS annual_retail_vol_billions,
    ROUND((SUM(upi_vol) / NULLIF(SUM(retail_vol), 0)) * 100.0, 2) AS upi_volume_share_pct,
    ROUND(SUM(upi_val) / 100000.0, 2) AS annual_upi_val_trillions,
    ROUND(SUM(retail_val) / 100000.0, 2) AS annual_retail_val_trillions,
    ROUND((SUM(upi_val) / NULLIF(SUM(retail_val), 0)) * 100.0, 2) AS upi_value_share_pct
FROM retail_vs_upi
GROUP BY calendar_year
ORDER BY calendar_year ASC;


-- ============================================================================
-- Business Query 3: Month-over-Month (MoM) and Year-over-Year (YoY) Growth
-- Computes MoM and 12-month YoY volume growth across key retail payment rails
-- (UPI, NEFT, IMPS, Credit Cards, Debit Cards).
-- ============================================================================
WITH rail_timeseries AS (
    SELECT 
        d.month_date,
        d.month_label,
        f.indicator_code,
        f.volume_lakh,
        -- 1-month lag for MoM
        LAG(f.volume_lakh, 1) OVER (
            PARTITION BY f.indicator_code ORDER BY d.month_date
        ) AS vol_lag_1m,
        -- 12-month lag for YoY
        LAG(f.volume_lakh, 12) OVER (
            PARTITION BY f.indicator_code ORDER BY d.month_date
        ) AS vol_lag_12m
    FROM fact_transaction_indicators f
    JOIN dim_date d ON f.month_date = d.month_date
    WHERE f.indicator_code IN ('UPI', 'NEFT', 'IMPS', 'CREDIT_CARDS_TOTAL', 'DEBIT_CARDS_TOTAL')
)
SELECT 
    month_date,
    month_label,
    indicator_code,
    volume_lakh,
    ROUND(((volume_lakh - vol_lag_1m) / NULLIF(vol_lag_1m, 0)) * 100.0, 2) AS mom_growth_pct,
    ROUND(((volume_lakh - vol_lag_12m) / NULLIF(vol_lag_12m, 0)) * 100.0, 2) AS yoy_growth_pct
FROM rail_timeseries
WHERE vol_lag_12m IS NOT NULL
ORDER BY month_date DESC, indicator_code ASC;


-- ============================================================================
-- Business Query 4: Average Ticket Size (ATS) Across Payment Rails
-- Compares the ticket size trajectories of retail micro-payments (UPI),
-- instant commercial transfers (IMPS), bulk commercial transfers (NEFT),
-- and wholesale settlements (RTGS Customer).
-- ============================================================================
SELECT 
    d.calendar_year,
    -- UPI Average Ticket Size
    ROUND(SUM(CASE WHEN f.indicator_code = 'UPI' THEN f.value_inr_crore ELSE 0 END) * 100.0 / 
          NULLIF(SUM(CASE WHEN f.indicator_code = 'UPI' THEN f.volume_lakh ELSE 0 END), 0), 2) AS upi_ats_inr,
    -- IMPS Average Ticket Size
    ROUND(SUM(CASE WHEN f.indicator_code = 'IMPS' THEN f.value_inr_crore ELSE 0 END) * 100.0 / 
          NULLIF(SUM(CASE WHEN f.indicator_code = 'IMPS' THEN f.volume_lakh ELSE 0 END), 0), 2) AS imps_ats_inr,
    -- NEFT Average Ticket Size
    ROUND(SUM(CASE WHEN f.indicator_code = 'NEFT' THEN f.value_inr_crore ELSE 0 END) * 100.0 / 
          NULLIF(SUM(CASE WHEN f.indicator_code = 'NEFT' THEN f.volume_lakh ELSE 0 END), 0), 2) AS neft_ats_inr,
    -- RTGS Customer Average Ticket Size
    ROUND(SUM(CASE WHEN f.indicator_code = 'RTGS_CUSTOMER' THEN f.value_inr_crore ELSE 0 END) * 100.0 / 
          NULLIF(SUM(CASE WHEN f.indicator_code = 'RTGS_CUSTOMER' THEN f.volume_lakh ELSE 0 END), 0), 2) AS rtgs_customer_ats_inr
FROM fact_transaction_indicators f
JOIN dim_date d ON f.month_date = d.month_date
WHERE f.indicator_code IN ('UPI', 'IMPS', 'NEFT', 'RTGS_CUSTOMER')
GROUP BY d.calendar_year
ORDER BY d.calendar_year ASC;


-- ============================================================================
-- Business Query 5: Credit Card vs. Debit Card Usage (PoS vs. e-Commerce)
-- Analyzes the divergence between in-store physical swiping (PoS) and
-- online/e-commerce card spending, showing e-commerce penetration.
-- ============================================================================
WITH card_channel_breakdown AS (
    SELECT 
        d.calendar_year,
        d.fiscal_year,
        -- Credit Card Spend (₹ Cr)
        SUM(CASE WHEN f.indicator_code = 'CREDIT_CARDS_POS' THEN f.value_inr_crore ELSE 0 END) AS cc_pos_val,
        SUM(CASE WHEN f.indicator_code = 'CREDIT_CARDS_OTHERS' THEN f.value_inr_crore ELSE 0 END) AS cc_ecom_val,
        -- Debit Card Spend (₹ Cr)
        SUM(CASE WHEN f.indicator_code = 'DEBIT_CARDS_POS' THEN f.value_inr_crore ELSE 0 END) AS dc_pos_val,
        SUM(CASE WHEN f.indicator_code = 'DEBIT_CARDS_OTHERS' THEN f.value_inr_crore ELSE 0 END) AS dc_ecom_val
    FROM fact_transaction_indicators f
    JOIN dim_date d ON f.month_date = d.month_date
    WHERE f.indicator_code IN ('CREDIT_CARDS_POS', 'CREDIT_CARDS_OTHERS', 'DEBIT_CARDS_POS', 'DEBIT_CARDS_OTHERS')
    GROUP BY d.calendar_year, d.fiscal_year
)
SELECT 
    calendar_year,
    fiscal_year,
    ROUND(cc_pos_val, 2) AS credit_card_pos_val_cr,
    ROUND(cc_ecom_val, 2) AS credit_card_ecom_val_cr,
    ROUND((cc_ecom_val / NULLIF(cc_pos_val + cc_ecom_val, 0)) * 100.0, 2) AS credit_card_ecom_share_pct,
    ROUND(dc_pos_val, 2) AS debit_card_pos_val_cr,
    ROUND(dc_ecom_val, 2) AS debit_card_ecom_val_cr,
    ROUND((dc_ecom_val / NULLIF(dc_pos_val + dc_ecom_val, 0)) * 100.0, 2) AS debit_card_ecom_share_pct,
    ROUND((cc_pos_val + cc_ecom_val) / NULLIF(dc_pos_val + dc_ecom_val, 0), 2) AS credit_to_debit_spend_ratio
FROM card_channel_breakdown
ORDER BY calendar_year ASC;


-- ============================================================================
-- Business Query 6: Digital Payments vs. Paper-Based Clearing (CTS Cheques)
-- Tracks the displacement of physical cheques by electronic payment rails
-- and reveals the counter-intuitive rise in average cheque value.
-- ============================================================================
WITH digital_vs_paper AS (
    SELECT 
        d.calendar_year,
        SUM(CASE WHEN f.indicator_code = 'TOTAL_DIGITAL_PAYMENTS' THEN f.volume_lakh ELSE 0 END) AS digital_vol,
        SUM(CASE WHEN f.indicator_code = 'TOTAL_DIGITAL_PAYMENTS' THEN f.value_inr_crore ELSE 0 END) AS digital_val,
        SUM(CASE WHEN f.indicator_code = 'PAPER_CTS' THEN f.volume_lakh ELSE 0 END) AS cheque_vol,
        SUM(CASE WHEN f.indicator_code = 'PAPER_CTS' THEN f.value_inr_crore ELSE 0 END) AS cheque_val
    FROM fact_transaction_indicators f
    JOIN dim_date d ON f.month_date = d.month_date
    WHERE f.indicator_code IN ('TOTAL_DIGITAL_PAYMENTS', 'PAPER_CTS')
    GROUP BY d.calendar_year
)
SELECT 
    calendar_year,
    ROUND(digital_vol / 10000.0, 2) AS digital_volume_billions,
    ROUND(cheque_vol / 100.0, 2) AS cheque_volume_crores,
    ROUND((digital_vol / NULLIF(digital_vol + cheque_vol, 0)) * 100.0, 3) AS digital_volume_share_pct,
    ROUND(digital_val / 100000.0, 2) AS digital_value_trillions,
    ROUND(cheque_val / 100000.0, 2) AS cheque_value_trillions,
    ROUND((digital_val / NULLIF(digital_val + cheque_val, 0)) * 100.0, 2) AS digital_value_share_pct,
    ROUND((cheque_val * 100.0) / NULLIF(cheque_vol, 0), 2) AS avg_cheque_size_inr
FROM digital_vs_paper
ORDER BY calendar_year ASC;


-- ============================================================================
-- Business Query 7: Merchant Acceptance Infrastructure Growth
-- Examines physical merchant touchpoints (PoS terminals) versus low-cost
-- interoperable QR codes (Bharat QR and Static UPI QR).
-- ============================================================================
SELECT 
    d.month_date,
    d.month_label,
    MAX(CASE WHEN f.indicator_code = 'POS_TERMINALS_DEPLOYED' THEN f.count_lakh END) AS pos_terminals_lakh,
    MAX(CASE WHEN f.indicator_code = 'BHARAT_QR_DEPLOYED' THEN f.count_lakh END) AS bharat_qr_lakh,
    MAX(CASE WHEN f.indicator_code = 'UPI_QR_STATIC_DEPLOYED' THEN f.count_lakh END) AS upi_qr_static_lakh,
    -- Ratio of UPI QR codes to physical PoS terminals
    ROUND(MAX(CASE WHEN f.indicator_code = 'UPI_QR_STATIC_DEPLOYED' THEN f.count_lakh END) / 
          NULLIF(MAX(CASE WHEN f.indicator_code = 'POS_TERMINALS_DEPLOYED' THEN f.count_lakh END), 0), 2) AS qr_to_pos_ratio
FROM fact_infrastructure_indicators f
JOIN dim_date d ON f.month_date = d.month_date
WHERE f.indicator_code IN ('POS_TERMINALS_DEPLOYED', 'BHARAT_QR_DEPLOYED', 'UPI_QR_STATIC_DEPLOYED')
  AND d.calendar_month = 3 -- Snapshot at fiscal year-end (March)
GROUP BY d.month_date, d.month_label
ORDER BY d.month_date ASC;


-- ============================================================================
-- Business Query 8: ATM Cash Withdrawals vs. Digital Payment Growth
-- Compares monthly cash-out at ATMs against digital payments to measure
-- currency substitution and cash displacement across India.
-- ============================================================================
WITH cash_vs_digital AS (
    SELECT 
        d.calendar_year,
        SUM(CASE WHEN f.indicator_code = 'ATM_CASH_TOTAL' THEN f.volume_lakh ELSE 0 END) AS atm_cash_vol,
        SUM(CASE WHEN f.indicator_code = 'ATM_CASH_TOTAL' THEN f.value_inr_crore ELSE 0 END) AS atm_cash_val,
        SUM(CASE WHEN f.indicator_code = 'MICRO_ATM_CASH_TOTAL' THEN f.volume_lakh ELSE 0 END) AS micro_atm_vol,
        SUM(CASE WHEN f.indicator_code = 'MICRO_ATM_CASH_TOTAL' THEN f.value_inr_crore ELSE 0 END) AS micro_atm_val,
        SUM(CASE WHEN f.indicator_code = 'TOTAL_DIGITAL_PAYMENTS' THEN f.value_inr_crore ELSE 0 END) AS digital_val
    FROM fact_transaction_indicators f
    JOIN dim_date d ON f.month_date = d.month_date
    WHERE f.indicator_code IN ('ATM_CASH_TOTAL', 'MICRO_ATM_CASH_TOTAL', 'TOTAL_DIGITAL_PAYMENTS')
    GROUP BY d.calendar_year
)
SELECT 
    calendar_year,
    ROUND(atm_cash_vol / 100.0, 2) AS atm_cash_withdrawals_crores,
    ROUND(atm_cash_val / 100000.0, 2) AS atm_cash_val_trillions,
    ROUND(micro_atm_vol / 100.0, 2) AS micro_atm_withdrawals_crores,
    ROUND(micro_atm_val / 100000.0, 2) AS micro_atm_val_trillions,
    ROUND(digital_val / 100000.0, 2) AS digital_payments_val_trillions,
    -- Ratio of cash-out to total digital payments
    ROUND((atm_cash_val / NULLIF(digital_val, 0)) * 100.0, 2) AS atm_cash_to_digital_val_pct,
    -- Average ticket size of ATM withdrawal
    ROUND((atm_cash_val * 100.0) / NULLIF(atm_cash_vol, 0), 2) AS avg_atm_withdrawal_size_inr
FROM cash_vs_digital
ORDER BY calendar_year ASC;


-- ============================================================================
-- Business Query 9: Fastest Growing vs. Declining Payment Instruments
-- Ranks all transaction rails by percentage volume expansion comparing
-- baseline (Nov-2019 to Oct-2020) vs latest 12 months (Aug-2025 to Jul-2026).
-- ============================================================================
WITH baseline_period AS (
    SELECT 
        indicator_code,
        AVG(volume_lakh) AS avg_vol_baseline
    FROM fact_transaction_indicators
    WHERE month_date BETWEEN '2019-11-01' AND '2020-10-01'
    GROUP BY indicator_code
),
latest_period AS (
    SELECT 
        indicator_code,
        AVG(volume_lakh) AS avg_vol_latest
    FROM fact_transaction_indicators
    WHERE month_date BETWEEN '2025-08-01' AND '2026-07-01'
    GROUP BY indicator_code
),
growth_rankings AS (
    SELECT 
        p.indicator_name,
        p.channel_group,
        p.hierarchy_level,
        ROUND(b.avg_vol_baseline, 2) AS baseline_monthly_vol_lakh,
        ROUND(l.avg_vol_latest, 2) AS latest_monthly_vol_lakh,
        ROUND(((l.avg_vol_latest - b.avg_vol_baseline) / NULLIF(b.avg_vol_baseline, 0)) * 100.0, 2) AS total_growth_pct,
        DENSE_RANK() OVER (ORDER BY ((l.avg_vol_latest - b.avg_vol_baseline) / NULLIF(b.avg_vol_baseline, 0)) DESC) AS growth_rank_desc,
        DENSE_RANK() OVER (ORDER BY ((l.avg_vol_latest - b.avg_vol_baseline) / NULLIF(b.avg_vol_baseline, 0)) ASC) AS decline_rank_asc
    FROM dim_payment_instrument p
    JOIN baseline_period b ON p.indicator_code = b.indicator_code
    JOIN latest_period l ON p.indicator_code = l.indicator_code
    WHERE p.hierarchy_level IN ('Component', 'Sub_Component')
      AND b.avg_vol_baseline > 0
)
SELECT 
    indicator_name,
    channel_group,
    baseline_monthly_vol_lakh,
    latest_monthly_vol_lakh,
    total_growth_pct,
    CASE 
        WHEN growth_rank_desc <= 5 THEN CONCAT('Top Growth #', growth_rank_desc)
        WHEN decline_rank_asc <= 5 THEN CONCAT('Lagging/Declining #', decline_rank_asc)
        ELSE 'Mid-Tier'
    END AS growth_tier
FROM growth_rankings
WHERE growth_rank_desc <= 5 OR decline_rank_asc <= 5
ORDER BY total_growth_pct DESC;


-- ============================================================================
-- Business Query 10: Data Quality & Forensic Anomaly Summary
-- Aggregates all documented exceptions, imputations, and displaced figures
-- by category, affected columns, and severity level.
-- ============================================================================
SELECT 
    exception_category,
    severity,
    COUNT(*) AS total_occurrences,
    MIN(month_date) AS earliest_impact_date,
    MAX(month_date) AS latest_impact_date,
    GROUP_CONCAT(DISTINCT source_column ORDER BY source_column SEPARATOR ', ') AS affected_columns,
    MAX(audit_justification) AS sample_justification
FROM audit_cleaning_exceptions
GROUP BY exception_category, severity
ORDER BY total_occurrences DESC;
