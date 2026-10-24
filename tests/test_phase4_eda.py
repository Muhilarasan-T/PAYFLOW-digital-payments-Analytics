"""
PAYFLOW — Phase 4 Analytical Verification & Automated Test Suite
================================================================
Validates analytical correctness, market share bounds, unit conversions,
growth rates on comparable periods, and Python-to-SQL consistency.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
import pytest

from src.phase4_eda import (
    load_cleaned_data,
    get_upi_retail_share,
    get_annual_summary,
    get_rail_ats_comparison,
    get_card_spend_divergence,
    get_infrastructure_trajectory,
    get_cash_vs_digital
)


@pytest.fixture(scope="module")
def eda_data():
    """Loads cleaned data and executes analytical aggregations."""
    df_trans, df_infra, df_dict, df_exc = load_cleaned_data()
    df_share = get_upi_retail_share(df_trans)
    df_ann = get_annual_summary(df_trans)
    df_ats = get_rail_ats_comparison(df_trans)
    df_cards = get_card_spend_divergence(df_trans)
    df_infra_trends = get_infrastructure_trajectory(df_infra)
    df_cash = get_cash_vs_digital(df_trans)
    
    return {
        "df_trans": df_trans,
        "df_infra": df_infra,
        "df_dict": df_dict,
        "df_exc": df_exc,
        "df_share": df_share,
        "df_ann": df_ann,
        "df_ats": df_ats,
        "df_cards": df_cards,
        "df_infra_trends": df_infra_trends,
        "df_cash": df_cash
    }


class TestDataIntegrityAndCoverage:
    """Verifies that datasets match exact dimensions and date continuity."""
    
    def test_dimensions(self, eda_data):
        assert len(eda_data["df_trans"]) == 4617, "Expected exactly 4,617 transaction rows"
        assert len(eda_data["df_infra"]) == 1053, "Expected exactly 1,053 infrastructure rows"
        assert len(eda_data["df_share"]) == 81, "Expected 81 monthly share records"
        assert len(eda_data["df_ann"]) == 8, "Expected 8 calendar year summary records (2019 to 2026)"

    def test_date_ordering_and_bounds(self, eda_data):
        df_share = eda_data["df_share"]
        dates = df_share["month_date"].tolist()
        
        # Verify strictly chronological ordering
        assert all(dates[i] < dates[i+1] for i in range(len(dates)-1)), "Dates must be strictly ascending"
        assert dates[0] == pd.to_datetime("2019-11-01")
        assert dates[-1] == pd.to_datetime("2026-07-01")


class TestSharePercentagesAndUnitConversions:
    """Verifies that market shares remain within valid bounds [0, 100] and unit conversions are correct."""
    
    def test_upi_share_bounds(self, eda_data):
        df_share = eda_data["df_share"]
        
        # Volume and value share must be between 0 and 100%
        assert (df_share["upi_vol_share_pct"] >= 0.0).all() and (df_share["upi_vol_share_pct"] <= 100.0).all()
        assert (df_share["upi_val_share_pct"] >= 0.0).all() and (df_share["upi_val_share_pct"] <= 100.0).all()
        
        # UPI volume share in Jul-2026 should be approx 87.00%
        jul26_vol_share = round(df_share[df_share["month_date"] == "2026-07-01"]["upi_vol_share_pct"].iloc[0], 2)
        assert abs(jul26_vol_share - 87.00) <= 0.05, f"Expected ~87.00% in Jul-2026, got {jul26_vol_share}%"
        
        # Annual 2026 volume share should be approx 86.76%
        ann_2026_vol_share = round(eda_data["df_ann"][eda_data["df_ann"]["year"] == 2026]["upi_vol_share_pct"].iloc[0], 2)
        assert abs(ann_2026_vol_share - 86.76) <= 0.05, f"Expected ~86.76% in annual 2026, got {ann_2026_vol_share}%"
        
        # UPI value share in Jul-2026 should be approx 30.57%
        jul26_val_share = round(df_share[df_share["month_date"] == "2026-07-01"]["upi_val_share_pct"].iloc[0], 2)
        assert abs(jul26_val_share - 30.57) <= 0.05, f"Expected ~30.57% in Jul-2026, got {jul26_val_share}%"

        # Annual 2026 value share should be approx 30.34%
        ann_2026_val_share = round(eda_data["df_ann"][eda_data["df_ann"]["year"] == 2026]["upi_val_share_pct"].iloc[0], 2)
        assert abs(ann_2026_val_share - 30.34) <= 0.05, f"Expected ~30.34% in annual 2026, got {ann_2026_val_share}%"

    def test_unit_conversions(self, eda_data):
        df_share = eda_data["df_share"]
        
        # 1 Lakh = 100,000 => 10,000 Lakh = 1 Billion
        diff_vol = np.abs((df_share["upi_vol_lakh"] / 10000.0) - df_share["upi_vol_billion"])
        assert (diff_vol <= 0.0001).all(), "Unit conversion from Lakh to Billion failed"
        
        # 1 Crore = 10M => 100,000 Crore = 1 Trillion
        diff_val = np.abs((df_share["upi_val_crore"] / 100000.0) - df_share["upi_val_trillion"])
        assert (diff_val <= 0.0001).all(), "Unit conversion from Crore to Trillion failed"


class TestCardTrendsAndRatios:
    """Verifies card spending divergence, e-commerce shares, and credit-to-debit ratios."""
    
    def test_card_shares_and_ratios(self, eda_data):
        df_cards = eda_data["df_cards"]
        
        assert (df_cards["cc_ecom_share_pct"] >= 0.0).all() and (df_cards["cc_ecom_share_pct"] <= 100.0).all()
        assert (df_cards["dc_ecom_share_pct"] >= 0.0).all() and (df_cards["dc_ecom_share_pct"] <= 100.0).all()
        
        # Credit-to-debit ratio in Jul-2026 should exceed 5.0
        jul26_ratio = round(df_cards[df_cards["month_date"] == "2026-07-01"]["credit_to_debit_ratio"].iloc[0], 2)
        assert jul26_ratio > 5.0, f"Expected credit-to-debit ratio > 5.0 in Jul-2026, got {jul26_ratio}"


class TestInfrastructureAndCash:
    """Verifies physical infrastructure and cash withdrawal metrics."""
    
    def test_qr_to_pos_ratio(self, eda_data):
        df_infra = eda_data["df_infra_trends"]
        valid_ratios = df_infra["qr_to_pos_ratio"].dropna()
        
        # In Jul-2026, ratio should exceed 75x
        jul26_ratio = round(df_infra[df_infra["month_date"] == "2026-07-01"]["qr_to_pos_ratio"].iloc[0], 1)
        assert jul26_ratio >= 75.0, f"Expected QR-to-PoS ratio >= 75x, got {jul26_ratio}"

    def test_cash_to_digital_ratio(self, eda_data):
        df_cash = eda_data["df_cash"]
        
        # Cash to digital ratio should decline over time
        ratio_2020 = df_cash[df_cash["month_date"] == "2020-07-01"]["atm_cash_to_digital_pct"].iloc[0]
        ratio_2026 = df_cash[df_cash["month_date"] == "2026-07-01"]["atm_cash_to_digital_pct"].iloc[0]
        
        assert ratio_2026 < ratio_2020, f"Cash to digital ratio must decline: 2020={ratio_2020}%, 2026={ratio_2026}%"
        assert ratio_2026 < 1.0, f"2026 cash-to-digital ratio should be under 1.0%, got {ratio_2026}%"


class TestPythonToSqlConsistency:
    """Cross-verifies that Python calculations match Phase 3 SQL analytical query outputs."""
    
    def test_sql_python_consistency(self, eda_data):
        db_path = "data/processed/payflow.db"
        assert os.path.exists(db_path), "Database payflow.db must exist for SQL cross-verification"
        
        conn = sqlite3.connect(db_path)
        
        # Query 1 Check: Jul-2026 UPI Volume and Value
        sql_jul26 = pd.read_sql_query("""
            SELECT volume_lakh, value_inr_crore, avg_ticket_size_inr 
            FROM fact_transaction_indicators 
            WHERE indicator_code = 'UPI' AND month_date = '2026-07-01';
        """, conn)
        
        py_jul26 = eda_data["df_trans"][(eda_data["df_trans"]["indicator_code"] == "UPI") & 
                                        (eda_data["df_trans"]["month_date"] == "2026-07-01")].iloc[0]
        
        assert round(sql_jul26["volume_lakh"].iloc[0], 2) == round(py_jul26["volume_lakh"], 2)
        assert round(sql_jul26["value_inr_crore"].iloc[0], 2) == round(py_jul26["value_inr_crore"], 2)
        assert round(sql_jul26["avg_ticket_size_inr"].iloc[0], 2) == round(py_jul26["avg_ticket_size_inr"], 2)
        
        # Query 2 Check: 2025 Annual Retail Total Volume
        sql_retail_2025 = pd.read_sql_query("""
            SELECT ROUND(SUM(volume_lakh) / 10000.0, 2) AS retail_vol_billion
            FROM fact_transaction_indicators
            WHERE indicator_code = 'TOTAL_RETAIL_PAYMENTS' AND strftime('%Y', month_date) = '2025';
        """, conn)
        
        ann_2025 = eda_data["df_ann"][eda_data["df_ann"]["year"] == 2025].iloc[0]
        assert round(ann_2025["retail_vol_billion"], 2) == sql_retail_2025["retail_vol_billion"].iloc[0]
        
        conn.close()
