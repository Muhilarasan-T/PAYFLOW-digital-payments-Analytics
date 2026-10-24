"""
PAYFLOW — Database Loader & SQL Execution Engine
=================================================
Loads processed CSV datasets into MySQL (when credentials are provided)
and creates an embedded SQLite analytical database (data/processed/payflow.db)
for immediate query execution, validation testing, and result reporting.
"""

import os
import sqlite3
from datetime import datetime
import pandas as pd
import numpy as np

# Optional MySQL driver
try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False


def build_date_dimension(start_date: str = "2019-11-01", end_date: str = "2026-07-01") -> pd.DataFrame:
    """Generates the 81-month date dimension with calendar and Indian fiscal years."""
    date_range = pd.date_range(start=start_date, end=end_date, freq="MS")
    records = []
    
    for dt in date_range:
        y = dt.year
        m = dt.month
        month_date_str = dt.strftime("%Y-%m-01")
        month_label = dt.strftime("%b-%Y")
        month_name = dt.strftime("%B")
        cal_quarter = f"Q{(m - 1) // 3 + 1}"
        
        # Indian fiscal year: April to March
        if m >= 4:
            fiscal_year = f"FY {y}-{str(y + 1)[2:]}"
        else:
            fiscal_year = f"FY {y - 1}-{str(y)[2:]}"
            
        if m in [4, 5, 6]:
            fiscal_quarter = "Q1"
        elif m in [7, 8, 9]:
            fiscal_quarter = "Q2"
        elif m in [10, 11, 12]:
            fiscal_quarter = "Q3"
        else:
            fiscal_quarter = "Q4"
            
        is_leap = (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)
        days_in_m = pd.Period(dt, freq='M').days_in_month
        
        records.append({
            "month_date": month_date_str,
            "month_label": month_label,
            "calendar_year": y,
            "calendar_month": m,
            "month_name": month_name,
            "calendar_quarter": cal_quarter,
            "fiscal_year": fiscal_year,
            "fiscal_quarter": fiscal_quarter,
            "is_leap_year": 1 if is_leap else 0,
            "days_in_month": days_in_m
        })
        
    return pd.DataFrame(records)


def build_instrument_dimension(df_dict: pd.DataFrame, df_trans: pd.DataFrame, df_infra: pd.DataFrame) -> pd.DataFrame:
    """Extracts unique 70 payment rails and infrastructure touchpoints for dim_payment_instrument."""
    records = []
    
    # 57 transaction indicators
    trans_unique = df_trans.drop_duplicates(subset=["indicator_code"]).copy()
    for _, r in trans_unique.iterrows():
        records.append({
            "indicator_code": r["indicator_code"],
            "indicator_name": r["indicator_name"],
            "indicator_type": "TRANSACTION",
            "major_section": r["major_section"],
            "sub_section": r["sub_section"],
            "channel_group": r["channel_group"],
            "hierarchy_level": r["hierarchy_level"],
            "volume_source_col": r["volume_source_col"],
            "value_source_col": r["value_source_col"],
            "volume_unit": "Lakh (100,000 transactions)",
            "value_unit": "Rupees Crores (₹ 10,000,000 INR)",
            "ats_eligible": 1,
            "footnote_symbols": "@" if "@" in r["indicator_name"] else ("$" if "$" in r["indicator_name"] else ("*" if "*" in r["indicator_name"] else None)),
            "notes": r["notes"]
        })
        
    # 13 infrastructure indicators
    infra_unique = df_infra.drop_duplicates(subset=["indicator_code"]).copy()
    for _, r in infra_unique.iterrows():
        records.append({
            "indicator_code": r["indicator_code"],
            "indicator_name": r["indicator_name"],
            "indicator_type": "INFRASTRUCTURE",
            "major_section": r["major_section"],
            "sub_section": r["sub_section"],
            "channel_group": r["infra_category"],
            "hierarchy_level": r["hierarchy_level"],
            "volume_source_col": r["count_source_col"],
            "value_source_col": r["value_source_col"],
            "volume_unit": "Lakh (100,000 units)",
            "value_unit": "Rupees Crores (N/A for count)",
            "ats_eligible": 0,
            "footnote_symbols": "@" if "@" in r["indicator_name"] else ("$" if "$" in r["indicator_name"] else ("*" if "*" in r["indicator_name"] else None)),
            "notes": r["notes"]
        })
        
    return pd.DataFrame(records)


def load_to_sqlite(db_path: str = "data/processed/payflow.db") -> sqlite3.Connection:
    """Creates local SQLite database with full Star Schema for immediate verification."""
    print(f"\n[SQLite] Initializing analytical database at: {db_path}")
    
    # Read processed CSVs
    df_trans = pd.read_csv("data/processed/transaction_indicators.csv")
    df_infra = pd.read_csv("data/processed/infrastructure_indicators.csv")
    df_dict = pd.read_csv("data/processed/data_dictionary.csv")
    df_exc = pd.read_csv("data/processed/cleaning_exceptions.csv")
    
    # Build dimensions
    df_dim_date = build_date_dimension()
    df_dim_instrument = build_instrument_dimension(df_dict, df_trans, df_infra)
    
    # Connect
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Drop existing
    cur.execute("DROP TABLE IF EXISTS audit_cleaning_exceptions;")
    cur.execute("DROP TABLE IF EXISTS fact_infrastructure_indicators;")
    cur.execute("DROP TABLE IF EXISTS fact_transaction_indicators;")
    cur.execute("DROP TABLE IF EXISTS dim_payment_instrument;")
    cur.execute("DROP TABLE IF EXISTS dim_date;")
    
    # DDL
    cur.execute("""
    CREATE TABLE dim_date (
        month_date TEXT PRIMARY KEY,
        month_label TEXT NOT NULL,
        calendar_year INTEGER NOT NULL,
        calendar_month INTEGER NOT NULL,
        month_name TEXT NOT NULL,
        calendar_quarter TEXT NOT NULL,
        fiscal_year TEXT NOT NULL,
        fiscal_quarter TEXT NOT NULL,
        is_leap_year INTEGER NOT NULL,
        days_in_month INTEGER NOT NULL
    );
    """)
    
    cur.execute("""
    CREATE TABLE dim_payment_instrument (
        indicator_code TEXT PRIMARY KEY,
        indicator_name TEXT NOT NULL,
        indicator_type TEXT NOT NULL,
        major_section TEXT NOT NULL,
        sub_section TEXT NOT NULL,
        channel_group TEXT NOT NULL,
        hierarchy_level TEXT NOT NULL,
        volume_source_col TEXT,
        value_source_col TEXT,
        volume_unit TEXT NOT NULL,
        value_unit TEXT NOT NULL,
        ats_eligible INTEGER NOT NULL,
        footnote_symbols TEXT,
        notes TEXT
    );
    """)
    
    cur.execute("""
    CREATE TABLE fact_transaction_indicators (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        month_date TEXT NOT NULL,
        indicator_code TEXT NOT NULL,
        volume_lakh REAL,
        value_inr_crore REAL,
        avg_ticket_size_inr REAL,
        volume_source_col TEXT NOT NULL,
        value_source_col TEXT NOT NULL,
        raw_volume_str TEXT,
        raw_value_str TEXT,
        data_status TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (month_date) REFERENCES dim_date(month_date),
        FOREIGN KEY (indicator_code) REFERENCES dim_payment_instrument(indicator_code)
    );
    """)
    
    cur.execute("""
    CREATE TABLE fact_infrastructure_indicators (
        infrastructure_id INTEGER PRIMARY KEY AUTOINCREMENT,
        month_date TEXT NOT NULL,
        indicator_code TEXT NOT NULL,
        count_lakh REAL,
        count_actual INTEGER,
        count_source_col TEXT NOT NULL,
        value_source_col TEXT NOT NULL,
        raw_count_str TEXT,
        raw_value_str TEXT,
        anomaly_flag TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (month_date) REFERENCES dim_date(month_date),
        FOREIGN KEY (indicator_code) REFERENCES dim_payment_instrument(indicator_code)
    );
    """)
    
    cur.execute("""
    CREATE TABLE audit_cleaning_exceptions (
        exception_id TEXT PRIMARY KEY,
        month_date TEXT NOT NULL,
        month_label TEXT NOT NULL,
        source_column TEXT NOT NULL,
        indicator_code TEXT NOT NULL,
        indicator_name TEXT NOT NULL,
        raw_value TEXT,
        cleaned_value REAL,
        exception_category TEXT NOT NULL,
        severity TEXT NOT NULL,
        resolution_applied TEXT NOT NULL,
        audit_justification TEXT NOT NULL
    );
    """)
    
    # Load Data
    df_dim_date.to_sql("dim_date", conn, if_exists="append", index=False)
    df_dim_instrument.to_sql("dim_payment_instrument", conn, if_exists="append", index=False)
    
    # Select exact columns for facts
    fact_trans_cols = ["month_date", "indicator_code", "volume_lakh", "value_inr_crore", 
                       "avg_ticket_size_inr", "volume_source_col", "value_source_col", 
                       "raw_volume_str", "raw_value_str", "data_status", "notes"]
    df_trans[fact_trans_cols].to_sql("fact_transaction_indicators", conn, if_exists="append", index=False)
    
    fact_infra_cols = ["month_date", "indicator_code", "count_lakh", "count_actual", 
                       "count_source_col", "value_source_col", "raw_count_str", 
                       "raw_value_str", "anomaly_flag", "notes"]
    df_infra[fact_infra_cols].to_sql("fact_infrastructure_indicators", conn, if_exists="append", index=False)
    
    df_exc.to_sql("audit_cleaning_exceptions", conn, if_exists="append", index=False)
    
    conn.commit()
    print("[SQLite] Successfully populated all 5 tables:")
    for tbl in ["dim_date", "dim_payment_instrument", "fact_transaction_indicators", 
                "fact_infrastructure_indicators", "audit_cleaning_exceptions"]:
        cur.execute(f"SELECT COUNT(*) FROM {tbl};")
        cnt = cur.fetchone()[0]
        print(f"  • {tbl}: {cnt} rows")
        
    return conn


def try_mysql_load() -> bool:
    """Attempts to connect to MySQL if configured in environment."""
    host = os.environ.get("MYSQL_HOST", "localhost")
    user = os.environ.get("MYSQL_USER", "root")
    password = os.environ.get("MYSQL_PASSWORD", "")
    port = int(os.environ.get("MYSQL_PORT", 3306))
    database = os.environ.get("MYSQL_DATABASE", "payflow_db")
    
    if not MYSQL_AVAILABLE:
        print("[MySQL] mysql-connector not installed.")
        return False
        
    try:
        # First connect without database to run create database
        conn = mysql.connector.connect(host=host, user=user, password=password, port=port)
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.database = database
        print(f"[MySQL] Connected to MySQL instance on {host}:{port}, database '{database}'.")
        return True
    except Exception as e:
        print(f"[MySQL] Connection test: MySQL instance is password-protected or unconfigured ({e}).")
        return False


if __name__ == "__main__":
    sqlite_conn = load_to_sqlite()
    mysql_success = try_mysql_load()
    if not mysql_success:
        print("[Notice] Using local analytical database for query verification. MySQL scripts saved in sql/.")
