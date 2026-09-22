import pandas as pd
import pytest

from src.etl.normaliser import (
    deduplicate_annual_records,
    normalize_ticker,
    normalize_year,
)

# ============================================================
# normalize_year() unit tests
# ============================================================

@pytest.mark.parametrize(
    "input_val, expected",
    [
        ("Dec 2012", "2012-12"),
        ("Mar 2014", "2014-03"),
        ("Mar-13", "2013-03"),
        ("Dec-12", "2012-12"),
        ("Jun-23", "2023-06"),
        ("Sep-24", "2024-09"),
        ("2024", "2024-03"),
        ("2023", "2023-03"),
        ("FY 2024", "2024-03"),
        ("FY24", "2024-03"),
        ("2012-12", "2012-12"),
        ("March 2014", "2014-03"),
        ("December 2012", "2012-12"),
        ("TTM", "TTM"),
        ("", "PARSE_ERROR"),
        (None, "PARSE_ERROR"),
        ("invalid-year", "PARSE_ERROR"),
        ("abc", "PARSE_ERROR"),
        ("not a date", "PARSE_ERROR"),
    ],
)
def test_normalize_year(input_val, expected):
    assert normalize_year(input_val) == expected


# ============================================================
# normalize_ticker() unit tests
# ============================================================

@pytest.mark.parametrize(
    "input_val, expected",
    [
        ("TCS", "TCS"),
        (" tcs ", "TCS"),
        ("tcs", "TCS"),
        ("hdfcbank", "HDFCBANK"),
        (" HDFCBANK ", "HDFCBANK"),
        ("ABB", "ABB"),
        ("Reliance", "RELIANCE"),
        ("INFY", "INFY"),
        ("AGTL", "ATGL"),  # Source typo correction
        ("A", None),        # Length < 2
        ("VERYLONGTICKERNAME", None), # Length > 12
        ("", None),
        (" ", None),
        (None, None),
    ],
)
def test_normalize_ticker(input_val, expected):
    assert normalize_ticker(input_val) == expected


# ============================================================
# deduplicate_annual_records() unit tests
# ============================================================

def test_deduplicate_annual_records():
    df = pd.DataFrame([
        {"company_id": "TCS", "year": "2023-03", "sales": 100, "net_profit": 20},
        {"company_id": "TCS", "year": "2023-03", "sales": 100, "net_profit": None}, # Duplicate with NaN
        {"company_id": "INFY", "year": "2023-03", "sales": 80, "net_profit": 15},
    ])

    dedup_df, logs, failures = deduplicate_annual_records(df, "profitandloss", "profitandloss.xlsx")

    assert len(dedup_df) == 2
    assert len(logs) == 1
    assert logs[0]["duplicate_count"] == 2
    assert logs[0]["rejected_count"] == 1
    assert len(failures) == 1
    assert failures[0]["rule_id"] == "DQ-02"
