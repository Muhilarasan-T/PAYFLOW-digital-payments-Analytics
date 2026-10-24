-- ============================================================================
-- PAYFLOW — Phase 3: Database Engineering & SQL Modeling
-- Script 03: Data Loading Script
-- Database: payflow_db
-- Dialect: MySQL 8.0+
-- ============================================================================

USE payflow_db;

-- ----------------------------------------------------------------------------
-- Instructions for Loading:
-- Option A: Execute automated Python loader (Recommended):
--           python src/load_data_to_mysql.py
--
-- Option B: Using MySQL LOAD DATA LOCAL INFILE:
--           Ensure local_infile is enabled: SET GLOBAL local_infile = 1;
--           Connect via: mysql --local-infile=1 -u root -p payflow_db
-- ----------------------------------------------------------------------------

-- Enable local file loading for this session
SET GLOBAL local_infile = 1;

-- ----------------------------------------------------------------------------
-- Step 1: Populate dim_date (81 consecutive months: Nov-2019 to Jul-2026)
-- Generated deterministically via recursive CTE
-- ----------------------------------------------------------------------------
INSERT INTO dim_date (
    month_date,
    month_label,
    calendar_year,
    calendar_month,
    month_name,
    calendar_quarter,
    fiscal_year,
    fiscal_quarter,
    is_leap_year,
    days_in_month
)
WITH RECURSIVE date_series AS (
    SELECT CAST('2019-11-01' AS DATE) AS dt
    UNION ALL
    SELECT DATE_ADD(dt, INTERVAL 1 MONTH)
    FROM date_series
    WHERE dt < '2026-07-01'
)
SELECT 
    dt AS month_date,
    DATE_FORMAT(dt, '%b-%Y') AS month_label,
    YEAR(dt) AS calendar_year,
    MONTH(dt) AS calendar_month,
    MONTHNAME(dt) AS month_name,
    CONCAT('Q', QUARTER(dt)) AS calendar_quarter,
    -- Indian Fiscal Year runs April 1 to March 31
    CASE 
        WHEN MONTH(dt) >= 4 THEN CONCAT('FY ', YEAR(dt), '-', SUBSTRING(CAST(YEAR(dt) + 1 AS CHAR), 3, 2))
        ELSE CONCAT('FY ', YEAR(dt) - 1, '-', SUBSTRING(CAST(YEAR(dt) AS CHAR), 3, 2))
    END AS fiscal_year,
    CASE 
        WHEN MONTH(dt) IN (4, 5, 6) THEN 'Q1'
        WHEN MONTH(dt) IN (7, 8, 9) THEN 'Q2'
        WHEN MONTH(dt) IN (10, 11, 12) THEN 'Q3'
        ELSE 'Q4'
    END AS fiscal_quarter,
    CASE 
        WHEN (YEAR(dt) % 4 = 0 AND YEAR(dt) % 100 != 0) OR (YEAR(dt) % 400 = 0) THEN TRUE 
        ELSE FALSE 
    END AS is_leap_year,
    DAY(LAST_DAY(dt)) AS days_in_month
FROM date_series;

-- ----------------------------------------------------------------------------
-- Step 2: Populate dim_payment_instrument from data_dictionary.csv
-- ----------------------------------------------------------------------------
-- When using Python loader (src/load_data_to_mysql.py), this is automated.
-- For manual MySQL LOAD DATA INFILE:
/*
LOAD DATA LOCAL INFILE 'data/processed/data_dictionary.csv'
INTO TABLE dim_payment_instrument
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(@column_id, @column_index, @indicator_code, @indicator_name, @indicator_type, 
 @major_section, @sub_section, @channel_group, @hierarchy_level, @metric_type, 
 @unit_of_measurement, @ats_eligible, @footnote_symbols, @source_header_raw, 
 @cleaning_action, @known_anomalies)
SET 
    indicator_code = SUBSTRING_INDEX(@indicator_code, '_VOL', 1),
    indicator_name = @indicator_name,
    indicator_type = @indicator_type,
    major_section = @major_section,
    sub_section = @sub_section,
    channel_group = @channel_group,
    hierarchy_level = @hierarchy_level,
    volume_unit = @unit_of_measurement,
    value_unit = @unit_of_measurement,
    ats_eligible = IF(@ats_eligible = 'True', 1, 0),
    footnote_symbols = NULLIF(@footnote_symbols, ''),
    notes = @cleaning_action;
*/

-- ----------------------------------------------------------------------------
-- Step 3: Populate fact_transaction_indicators
-- ----------------------------------------------------------------------------
/*
LOAD DATA LOCAL INFILE 'data/processed/transaction_indicators.csv'
INTO TABLE fact_transaction_indicators
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(month_date, @month_label, @year, @month, indicator_code, @indicator_name,
 @major_section, @sub_section, @channel_group, @hierarchy_level, 
 @volume_lakh, @value_inr_crore, @avg_ticket_size_inr, 
 volume_source_col, value_source_col, raw_volume_str, raw_value_str, 
 data_status, @notes)
SET 
    volume_lakh = NULLIF(@volume_lakh, ''),
    value_inr_crore = NULLIF(@value_inr_crore, ''),
    avg_ticket_size_inr = NULLIF(@avg_ticket_size_inr, ''),
    notes = NULLIF(@notes, '');
*/

-- ----------------------------------------------------------------------------
-- Step 4: Populate fact_infrastructure_indicators
-- ----------------------------------------------------------------------------
/*
LOAD DATA LOCAL INFILE 'data/processed/infrastructure_indicators.csv'
INTO TABLE fact_infrastructure_indicators
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(month_date, @month_label, @year, @month, indicator_code, @indicator_name,
 @major_section, @sub_section, @infra_category, @hierarchy_level, 
 @count_lakh, @count_actual, count_source_col, value_source_col, 
 raw_count_str, raw_value_str, anomaly_flag, @notes)
SET 
    count_lakh = NULLIF(@count_lakh, ''),
    count_actual = NULLIF(@count_actual, ''),
    notes = NULLIF(@notes, '');
*/

-- ----------------------------------------------------------------------------
-- Step 5: Populate audit_cleaning_exceptions
-- ----------------------------------------------------------------------------
/*
LOAD DATA LOCAL INFILE 'data/processed/cleaning_exceptions.csv'
INTO TABLE audit_cleaning_exceptions
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(exception_id, month_date, month_label, source_column, indicator_code, 
 indicator_name, raw_value, @cleaned_value, exception_category, severity, 
 resolution_applied, audit_justification)
SET 
    cleaned_value = NULLIF(@cleaned_value, '');
*/
