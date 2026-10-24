-- ============================================================================
-- PAYFLOW — Phase 3: Database Engineering & SQL Modeling
-- Script 02: Table Definitions (Star Schema DDL)
-- Database: payflow_db
-- Dialect: MySQL 8.0+
-- ============================================================================

USE payflow_db;

-- ----------------------------------------------------------------------------
-- Drop existing tables in reverse dependency order
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS audit_cleaning_exceptions;
DROP TABLE IF EXISTS fact_infrastructure_indicators;
DROP TABLE IF EXISTS fact_transaction_indicators;
DROP TABLE IF EXISTS dim_payment_instrument;
DROP TABLE IF EXISTS dim_date;

-- ----------------------------------------------------------------------------
-- 1. Dimension Table: Calendar & Fiscal Time Dimension
-- ----------------------------------------------------------------------------
CREATE TABLE dim_date (
    month_date          DATE NOT NULL,
    month_label         VARCHAR(10) NOT NULL,
    calendar_year       SMALLINT UNSIGNED NOT NULL,
    calendar_month      TINYINT UNSIGNED NOT NULL,
    month_name          VARCHAR(15) NOT NULL,
    calendar_quarter    VARCHAR(5) NOT NULL,
    fiscal_year         VARCHAR(15) NOT NULL,
    fiscal_quarter      VARCHAR(5) NOT NULL,
    is_leap_year        BOOLEAN NOT NULL DEFAULT FALSE,
    days_in_month       TINYINT UNSIGNED NOT NULL,
    
    PRIMARY KEY (month_date),
    UNIQUE KEY uq_dim_date_label (month_label),
    INDEX idx_dim_date_year_month (calendar_year, calendar_month),
    INDEX idx_dim_date_fiscal (fiscal_year, fiscal_quarter)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Month-level analytical date dimension supporting calendar and Indian fiscal (Apr-Mar) years';

-- ----------------------------------------------------------------------------
-- 2. Dimension Table: Payment Instrument & Acceptance Channel
-- ----------------------------------------------------------------------------
CREATE TABLE dim_payment_instrument (
    indicator_code      VARCHAR(50) NOT NULL,
    indicator_name      VARCHAR(120) NOT NULL,
    indicator_type      ENUM('TRANSACTION', 'INFRASTRUCTURE') NOT NULL,
    major_section       VARCHAR(60) NOT NULL,
    sub_section         VARCHAR(60) NOT NULL,
    channel_group       VARCHAR(60) NOT NULL,
    hierarchy_level     ENUM('Component', 'Sub_Component', 'Subtotal', 'Category_Total', 'Grand_Total') NOT NULL,
    volume_source_col   VARCHAR(10) DEFAULT NULL,
    value_source_col    VARCHAR(10) DEFAULT NULL,
    volume_unit         VARCHAR(40) NOT NULL,
    value_unit          VARCHAR(50) NOT NULL,
    ats_eligible        BOOLEAN NOT NULL DEFAULT FALSE,
    footnote_symbols    VARCHAR(10) DEFAULT NULL,
    notes               TEXT DEFAULT NULL,
    
    PRIMARY KEY (indicator_code),
    INDEX idx_dim_pi_type (indicator_type),
    INDEX idx_dim_pi_group (channel_group),
    INDEX idx_dim_pi_hierarchy (hierarchy_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Catalog of all 70 RBI payment rails, instruments, clearing systems, and infrastructure touchpoints';

-- ----------------------------------------------------------------------------
-- 3. Fact Table: Monthly Transaction Indicators (Volume, Value & ATS)
-- ----------------------------------------------------------------------------
CREATE TABLE fact_transaction_indicators (
    transaction_id      BIGINT UNSIGNED AUTO_INCREMENT,
    month_date          DATE NOT NULL,
    indicator_code      VARCHAR(50) NOT NULL,
    volume_lakh         DECIMAL(18, 2) DEFAULT NULL COMMENT 'Transaction volume in Lakh (100,000 txns)',
    value_inr_crore     DECIMAL(18, 2) DEFAULT NULL COMMENT 'Transaction value in Rupees Crores (₹ 10M INR)',
    avg_ticket_size_inr DECIMAL(18, 2) DEFAULT NULL COMMENT 'Derived Average Ticket Size = (Value in Cr / Vol in Lakh) * 100',
    volume_source_col   VARCHAR(10) NOT NULL,
    value_source_col    VARCHAR(10) NOT NULL,
    raw_volume_str      VARCHAR(50) DEFAULT NULL,
    raw_value_str       VARCHAR(50) DEFAULT NULL,
    data_status         VARCHAR(30) NOT NULL DEFAULT 'REPORTED' COMMENT 'REPORTED, DERIVED_SUM_CORRECTION, POST_DEPRECATION_NA',
    notes               TEXT DEFAULT NULL,
    
    PRIMARY KEY (transaction_id),
    UNIQUE KEY uq_fact_trans_month_ind (month_date, indicator_code),
    FOREIGN KEY fk_fact_trans_date (month_date) 
        REFERENCES dim_date (month_date) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY fk_fact_trans_ind (indicator_code) 
        REFERENCES dim_payment_instrument (indicator_code) ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX idx_fact_trans_code_date (indicator_code, month_date),
    INDEX idx_fact_trans_status (data_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Fact table capturing monthly transactional flows across 57 payment rails';

-- ----------------------------------------------------------------------------
-- 4. Fact Table: Monthly Infrastructure Indicators (Physical Touchpoint Counts)
-- ----------------------------------------------------------------------------
CREATE TABLE fact_infrastructure_indicators (
    infrastructure_id   BIGINT UNSIGNED AUTO_INCREMENT,
    month_date          DATE NOT NULL,
    indicator_code      VARCHAR(50) NOT NULL,
    count_lakh          DECIMAL(14, 2) DEFAULT NULL COMMENT 'Active touchpoint count in Lakhs',
    count_actual        BIGINT DEFAULT NULL COMMENT 'Actual touchpoint count in units = count_lakh * 100,000',
    count_source_col    VARCHAR(10) NOT NULL,
    value_source_col    VARCHAR(10) NOT NULL,
    raw_count_str       VARCHAR(50) DEFAULT NULL,
    raw_value_str       VARCHAR(50) DEFAULT NULL,
    anomaly_flag        VARCHAR(40) NOT NULL DEFAULT 'NONE' COMMENT 'NONE, PRE_LAUNCH_NOT_REPORTED, SUSPICIOUS_DISPLACED_VALUE',
    notes               TEXT DEFAULT NULL,
    
    PRIMARY KEY (infrastructure_id),
    UNIQUE KEY uq_fact_infra_month_ind (month_date, indicator_code),
    FOREIGN KEY fk_fact_infra_date (month_date) 
        REFERENCES dim_date (month_date) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY fk_fact_infra_ind (indicator_code) 
        REFERENCES dim_payment_instrument (indicator_code) ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX idx_fact_infra_code_date (indicator_code, month_date),
    INDEX idx_fact_infra_flag (anomaly_flag)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Fact table capturing physical merchant acceptance infrastructure and card footprints';

-- ----------------------------------------------------------------------------
-- 5. Audit Table: Forensic Cleaning Exceptions Register
-- ----------------------------------------------------------------------------
CREATE TABLE audit_cleaning_exceptions (
    exception_id        VARCHAR(20) NOT NULL,
    month_date          DATE NOT NULL,
    month_label         VARCHAR(10) NOT NULL,
    source_column       VARCHAR(10) NOT NULL,
    indicator_code      VARCHAR(50) NOT NULL,
    indicator_name      VARCHAR(120) NOT NULL,
    raw_value           VARCHAR(50) DEFAULT NULL,
    cleaned_value       DECIMAL(18, 2) DEFAULT NULL,
    exception_category  VARCHAR(40) NOT NULL,
    severity            VARCHAR(20) NOT NULL,
    resolution_applied  TEXT NOT NULL,
    audit_justification TEXT NOT NULL,
    
    PRIMARY KEY (exception_id),
    INDEX idx_audit_date (month_date),
    INDEX idx_audit_category (exception_category),
    INDEX idx_audit_severity (severity)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Forensic audit trail capturing all 36 anomalies, imputations, pre-launch flags, and displaced data';
