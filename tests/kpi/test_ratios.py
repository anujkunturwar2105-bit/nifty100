"""
Unit Tests for Ratio Engine and Validation
"""

import pandas as pd
import pytest

from src.analytics.ratios import calculate_company_ratios, run_production_ratio_validation, safe_div


def test_safe_div():
    assert safe_div(100, 20) == 5.0
    assert safe_div(100, 0) is None
    assert safe_div(None, 5) is None
    assert safe_div(10, None) is None
    assert safe_div(50, 100, 100.0) == 50.0


def test_calculate_company_ratios():
    ratios_df = calculate_company_ratios()
    assert not ratios_df.empty
    assert "return_on_equity_pct" in ratios_df.columns
    assert "operating_profit_margin_pct" in ratios_df.columns
    assert "debt_to_equity" in ratios_df.columns
    assert "free_cash_flow_cr" in ratios_df.columns


def test_production_ratio_validation():
    ratios_df = calculate_company_ratios()
    val_df = run_production_ratio_validation(ratios_df)
    assert not val_df.empty
    assert "status" in val_df.columns
    pass_rate = (val_df["status"] == "PASS").mean()
    assert pass_rate >= 0.70
