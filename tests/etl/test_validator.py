import pandas as pd
import pytest

from src.etl.validator import (
    check_dq_01_pk_uniqueness,
    check_dq_02_company_year_uniqueness,
    check_dq_03_foreign_key_integrity,
    check_dq_04_balance_sheet_balance,
    check_dq_05_opm_cross_check,
    check_dq_08_ticker_format,
    check_dq_09_cash_flow_reconciliation,
)


def test_check_dq_01_pk_uniqueness():
    companies_df = pd.DataFrame([
        {"id": "TCS", "company_name": "Tata Consultancy Services"},
        {"id": "TCS", "company_name": "TCS Duplicate"}, # Duplicate PK
    ])

    failures = check_dq_01_pk_uniqueness(companies_df)
    assert len(failures) == 2
    assert failures[0]["rule_id"] == "DQ-01"
    assert failures[0]["severity"] == "CRITICAL"


def test_check_dq_03_foreign_key_integrity():
    companies_df = pd.DataFrame([
        {"id": "TCS"},
        {"id": "INFY"},
    ])

    child_df = pd.DataFrame([
        {"company_id": "TCS", "year": "2023-03"},
        {"company_id": "ORPHAN_COMPANY", "year": "2023-03"}, # Missing FK
    ])

    failures = check_dq_03_foreign_key_integrity(child_df, companies_df, "profitandloss", "profitandloss.xlsx")
    assert len(failures) == 1
    assert failures[0]["rule_id"] == "DQ-03"
    assert failures[0]["company_id"] == "ORPHAN_COMPANY"


def test_check_dq_04_balance_sheet_balance():
    bs_df = pd.DataFrame([
        {"company_id": "TCS", "year": "2023-03", "total_assets": 1000, "total_liabilities": 1000},
        {"company_id": "INFY", "year": "2023-03", "total_assets": 1000, "total_liabilities": 800}, # Imbalance ratio 0.2
    ])

    failures = check_dq_04_balance_sheet_balance(bs_df)
    assert len(failures) == 1
    assert failures[0]["rule_id"] == "DQ-04"
    assert failures[0]["company_id"] == "INFY"


def test_check_dq_08_ticker_format():
    df = pd.DataFrame([
        {"id": "TCS"},
        {"id": "invalid_ticker_length_too_long"},
    ])

    failures = check_dq_08_ticker_format(df, "companies", "companies.xlsx")
    assert len(failures) == 1
    assert failures[0]["rule_id"] == "DQ-08"
