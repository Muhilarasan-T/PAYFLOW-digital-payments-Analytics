"""
PAYFLOW — Automated Data Integrity & Validation Test Suite
===========================================================
Tests dataset integrity, temporal continuity, indicator counts, schema types,
ticket size arithmetic, anomaly handling, source traceability, and mathematical
reconciliations against raw RBI source data.
"""

import os
import csv
from datetime import datetime
import pandas as pd
import numpy as np
import pytest

from src.clean_data import run_pipeline


@pytest.fixture(scope="module")
def pipeline_data():
    """Runs pipeline and loads all processed deliverables."""
    results = run_pipeline()
    return results


class TestDataIntegrity:
    """Verifies temporal continuity, row counts, and structural completeness."""
    
    def test_monthly_continuity(self, pipeline_data):
        df_trans = pipeline_data["df_transactions"]
        df_infra = pipeline_data["df_infrastructure"]
        
        dates_trans = sorted(df_trans["month_date"].unique())
        dates_infra = sorted(df_infra["month_date"].unique())
        
        assert len(dates_trans) == 81, f"Expected 81 unique months in transactions, got {len(dates_trans)}"
        assert len(dates_infra) == 81, f"Expected 81 unique months in infrastructure, got {len(dates_infra)}"
        assert dates_trans == dates_infra, "Transaction and infrastructure date sets must match"
        
        assert dates_trans[0] == "2019-11-01", f"Expected start date 2019-11-01, got {dates_trans[0]}"
        assert dates_trans[-1] == "2026-07-01", f"Expected end date 2026-07-01, got {dates_trans[-1]}"
        
        # Verify no calendar gaps
        dts = [datetime.strptime(d, "%Y-%m-01") for d in dates_trans]
        for i in range(len(dts) - 1):
            expected_next_year = dts[i].year + (1 if dts[i].month == 12 else 0)
            expected_next_month = 1 if dts[i].month == 12 else dts[i].month + 1
            actual_next = dts[i + 1]
            assert (actual_next.year == expected_next_year and actual_next.month == expected_next_month), \
                f"Gap detected between {dts[i].strftime('%Y-%m')} and {actual_next.strftime('%Y-%m')}"

    def test_record_counts(self, pipeline_data):
        df_trans = pipeline_data["df_transactions"]
        df_infra = pipeline_data["df_infrastructure"]
        df_dict = pipeline_data["df_data_dict"]
        df_exc = pipeline_data["df_exceptions"]
        
        # 57 transaction indicators * 81 months = 4617 rows
        assert len(df_trans) == 4617, f"Expected 4617 transaction rows, got {len(df_trans)}"
        assert len(df_trans["indicator_code"].unique()) == 57, "Expected exactly 57 transaction indicator codes"
        
        # 13 infrastructure indicators * 81 months = 1053 rows
        assert len(df_infra) == 1053, f"Expected 1053 infrastructure rows, got {len(df_infra)}"
        assert len(df_infra["indicator_code"].unique()) == 13, "Expected exactly 13 infrastructure indicator codes"
        
        # 145 raw columns documented in dictionary
        assert len(df_dict) == 145, f"Expected 145 dictionary columns, got {len(df_dict)}"
        
        # Exceptions logged
        assert len(df_exc) == 36, f"Expected 36 logged exceptions, got {len(df_exc)}"

    def test_unique_keys(self, pipeline_data):
        df_trans = pipeline_data["df_transactions"]
        df_infra = pipeline_data["df_infrastructure"]
        
        # Check uniqueness of primary key (month_date, indicator_code)
        dup_trans = df_trans.duplicated(subset=["month_date", "indicator_code"]).sum()
        assert dup_trans == 0, f"Found {dup_trans} duplicate (month_date, indicator_code) keys in transactions"
        
        dup_infra = df_infra.duplicated(subset=["month_date", "indicator_code"]).sum()
        assert dup_infra == 0, f"Found {dup_infra} duplicate (month_date, indicator_code) keys in infrastructure"


class TestNumericIntegrityAndCalculations:
    """Verifies numeric types, non-negativity, and Average Ticket Size calculations."""
    
    def test_non_negativity(self, pipeline_data):
        df_trans = pipeline_data["df_transactions"]
        df_infra = pipeline_data["df_infrastructure"]
        
        for col in ["volume_lakh", "value_inr_crore", "avg_ticket_size_inr"]:
            valid_vals = df_trans[col].dropna()
            assert (valid_vals >= 0.0).all(), f"Found negative values in transaction column {col}"
            
        for col in ["count_lakh", "count_actual"]:
            valid_vals = df_infra[col].dropna()
            assert (valid_vals >= 0.0).all(), f"Found negative values in infrastructure column {col}"

    def test_average_ticket_size_formula(self, pipeline_data):
        df_trans = pipeline_data["df_transactions"]
        
        # Select rows where both volume and value are present and volume > 0
        valid_rows = df_trans[df_trans["volume_lakh"].notna() & 
                              df_trans["value_inr_crore"].notna() & 
                              (df_trans["volume_lakh"] > 0)].copy()
        
        expected_ats = np.round((valid_rows["value_inr_crore"] / valid_rows["volume_lakh"]) * 100.0, 2)
        diff = np.abs(valid_rows["avg_ticket_size_inr"] - expected_ats)
        
        assert (diff <= 0.01).all(), f"Max ATS deviation exceeds 0.01 INR: {diff.max()}"
        
        # Where volume is NaN, ATS must be NaN
        nan_vol_rows = df_trans[df_trans["volume_lakh"].isna()]
        assert nan_vol_rows["avg_ticket_size_inr"].isna().all(), "ATS must be NaN when volume is NaN"


class TestAnomalyHandlingAndTraceability:
    """Tests proper isolation and documentation of known anomalies and column provenance."""
    
    def test_sep_2023_ppi_imputation(self, pipeline_data):
        df_trans = pipeline_data["df_transactions"]
        
        sep_ppi = df_trans[(df_trans["month_date"] == "2023-09-01") & 
                           (df_trans["indicator_code"] == "PPI_TOTAL")].iloc[0]
        
        assert sep_ppi["raw_volume_str"] in ["-", " -"], "Raw volume string must preserve source dash placeholder"
        assert sep_ppi["data_status"] == "DERIVED_SUM_CORRECTION", "Status must reflect derived sum correction"
        assert sep_ppi["volume_lakh"] == 6143.17, f"Expected imputed volume 6143.17, got {sep_ppi['volume_lakh']}"
        assert sep_ppi["value_inr_crore"] == 23667.78, "Reported value must remain untouched"

    def test_upi_qr_anomaly_isolation(self, pipeline_data):
        df_infra = pipeline_data["df_infrastructure"]
        
        qr_df = df_infra[df_infra["indicator_code"] == "UPI_QR_STATIC_DEPLOYED"]
        
        # Pre-launch (Nov-2019 to Aug-2020: 10 months)
        pre_launch = qr_df[qr_df["month_date"] < "2020-09-01"]
        assert len(pre_launch) == 10, f"Expected 10 pre-launch months, got {len(pre_launch)}"
        assert pre_launch["count_lakh"].isna().all(), "Pre-launch UPI QR counts must be NaN"
        assert (pre_launch["anomaly_flag"] == "PRE_LAUNCH_NOT_REPORTED").all()
        
        # Displaced c141 values (Jan-2024 to Jan-2026: 25 months)
        displaced = qr_df[(qr_df["month_date"] >= "2024-01-01") & (qr_df["month_date"] <= "2026-01-01")]
        assert len(displaced) == 25, f"Expected 25 displaced months, got {len(displaced)}"
        assert (displaced["anomaly_flag"] == "SUSPICIOUS_DISPLACED_VALUE").all()
        # Verify raw values are preserved
        assert displaced["raw_value_str"].notna().all()
        assert not (displaced["raw_value_str"].isin([" -", "-", "0.00", ""])).any()

    def test_source_column_traceability(self, pipeline_data):
        df_trans = pipeline_data["df_transactions"]
        df_dict = pipeline_data["df_data_dict"]
        
        valid_cols = set(df_dict["column_id"])
        
        for col in df_trans["volume_source_col"].unique():
            assert col in valid_cols, f"Invalid volume source column: {col}"
        for col in df_trans["value_source_col"].unique():
            assert col in valid_cols, f"Invalid value source column: {col}"


class TestMathematicalReconciliations:
    """Verifies that key component sums reconcile with reported totals."""
    
    def test_rtgs_reconciliation(self, pipeline_data):
        df_trans = pipeline_data["df_transactions"]
        
        piv = df_trans.pivot(index="month_date", columns="indicator_code", values="volume_lakh")
        piv_val = df_trans.pivot(index="month_date", columns="indicator_code", values="value_inr_crore")
        
        vol_diff = np.abs(piv["RTGS_TOTAL"] - (piv["RTGS_CUSTOMER"] + piv["RTGS_INTERBANK"]))
        val_diff = np.abs(piv_val["RTGS_TOTAL"] - (piv_val["RTGS_CUSTOMER"] + piv_val["RTGS_INTERBANK"]))
        
        assert (vol_diff <= 0.05).all(), f"RTGS volume reconciliation failed. Max diff: {vol_diff.max()}"
        assert (val_diff <= 0.05).all(), f"RTGS value reconciliation failed. Max diff: {val_diff.max()}"

    def test_card_payments_reconciliation(self, pipeline_data):
        df_trans = pipeline_data["df_transactions"]
        
        piv = df_trans.pivot(index="month_date", columns="indicator_code", values="volume_lakh")
        piv_val = df_trans.pivot(index="month_date", columns="indicator_code", values="value_inr_crore")
        
        # Total Cards = Credit Cards Total + Debit Cards Total
        vol_diff = np.abs(piv["CARD_PAYMENTS_TOTAL"] - (piv["CREDIT_CARDS_TOTAL"] + piv["DEBIT_CARDS_TOTAL"]))
        val_diff = np.abs(piv_val["CARD_PAYMENTS_TOTAL"] - (piv_val["CREDIT_CARDS_TOTAL"] + piv_val["DEBIT_CARDS_TOTAL"]))
        
        assert (vol_diff <= 0.05).all(), f"Total card volume reconciliation failed. Max diff: {vol_diff.max()}"
        assert (val_diff <= 0.05).all(), f"Total card value reconciliation failed. Max diff: {val_diff.max()}"

    def test_total_payments_reconciliation(self, pipeline_data):
        df_trans = pipeline_data["df_transactions"]
        
        piv = df_trans.pivot(index="month_date", columns="indicator_code", values="volume_lakh")
        piv_val = df_trans.pivot(index="month_date", columns="indicator_code", values="value_inr_crore")
        
        # Total Payments = RTGS Total + Retail Payments Total
        vol_diff = np.abs(piv["TOTAL_PAYMENTS"] - (piv["RTGS_TOTAL"] + piv["TOTAL_RETAIL_PAYMENTS"]))
        val_diff = np.abs(piv_val["TOTAL_PAYMENTS"] - (piv_val["RTGS_TOTAL"] + piv_val["TOTAL_RETAIL_PAYMENTS"]))
        
        assert (vol_diff <= 0.05).all(), f"Total payments volume reconciliation failed. Max diff: {vol_diff.max()}"
        assert (val_diff <= 0.05).all(), f"Total payments value reconciliation failed. Max diff: {val_diff.max()}"

    def test_digital_payments_reconciliation(self, pipeline_data):
        df_trans = pipeline_data["df_transactions"]
        
        piv = df_trans.pivot(index="month_date", columns="indicator_code", values="volume_lakh")
        piv_val = df_trans.pivot(index="month_date", columns="indicator_code", values="value_inr_crore")
        
        # Total Digital Payments = Total Payments - Paper-based Instruments
        vol_diff = np.abs(piv["TOTAL_DIGITAL_PAYMENTS"] - (piv["TOTAL_PAYMENTS"] - piv["PAPER_TOTAL"]))
        val_diff = np.abs(piv_val["TOTAL_DIGITAL_PAYMENTS"] - (piv_val["TOTAL_PAYMENTS"] - piv_val["PAPER_TOTAL"]))
        
        assert (vol_diff <= 0.05).all(), f"Total digital volume reconciliation failed. Max diff: {vol_diff.max()}"
        assert (val_diff <= 0.05).all(), f"Total digital value reconciliation failed. Max diff: {val_diff.max()}"

    def test_exceptions_schema_and_parquet(self, pipeline_data):
        df_exc = pipeline_data["df_exceptions"]
        
        required_cols = ["exception_id", "month_date", "month_label", "source_column", 
                         "indicator_code", "indicator_name", "raw_value", "cleaned_value", 
                         "exception_category", "severity", "resolution_applied", "audit_justification"]
        
        for c in required_cols:
            assert c in df_exc.columns, f"Missing required column {c} in cleaning_exceptions"
            
        # Check Parquet parity
        trans_parquet = pd.read_parquet("data/processed/transaction_indicators.parquet")
        infra_parquet = pd.read_parquet("data/processed/infrastructure_indicators.parquet")
        
        assert len(trans_parquet) == 4617, "Parquet transaction count must match CSV"
        assert len(infra_parquet) == 1053, "Parquet infrastructure count must match CSV"

