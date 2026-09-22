"""
Unit Tests for ETL Normalizer Module
"""

import pandas as pd
import pytest

from src.etl.normaliser import (
    audit_and_resolve_ratio_duplicates,
    audit_documents_dataset,
    deduplicate_annual_records,
    normalize_columns,
    normalize_doc_year,
    normalize_ticker,
    normalize_year,
    parse_analysis_dataset,
)


def test_normalize_ticker():
    assert normalize_ticker(" tcs ") == "TCS"
    assert normalize_ticker("hdfcbank") == "HDFCBANK"
    assert normalize_ticker("agtl") == "ATGL"
    assert normalize_ticker(None) is None
    assert normalize_ticker("A") is None
    assert normalize_ticker("A" * 15) is None


def test_normalize_year():
    assert normalize_year("Mar-24") == "2024-03"
    assert normalize_year("Dec 2023") == "2023-12"
    assert normalize_year("2024") == "2024-03"
    assert normalize_year("FY 2024") == "2024-03"
    assert normalize_year("TTM") == "TTM"
    assert normalize_year("InvalidDate") == "PARSE_ERROR"


def test_normalize_columns():
    df = pd.DataFrame(columns=["Company ID ", "Year\n", "Annual Report", "OPM %"])
    norm_df = normalize_columns(df)
    assert list(norm_df.columns) == ["company_id", "year", "annual_report", "opm"]


def test_normalize_doc_year():
    assert normalize_doc_year("2024") == 2024
    assert normalize_doc_year("Annual Report FY 2023-24") == 2023
    assert normalize_doc_year("None") is None


def test_deduplicate_annual_records():
    df = pd.DataFrame([
        {"company_id": "TCS", "year": "2024-03", "sales": 100, "np": 20},
        {"company_id": "TCS", "year": "2024-03", "sales": 100, "np": None},
    ])
    dedup, logs, failures = deduplicate_annual_records(df, "profitandloss", "pnl.xlsx")
    assert len(dedup) == 1
    assert dedup.iloc[0]["np"] == 20


def test_audit_ratio_duplicates():
    df = pd.DataFrame([
        {"company_id": "INFY", "year": "2024-03", "roe": 25.0},
        {"company_id": "INFY", "year": "2024-03", "roe": 26.0},
    ])
    clean, conflicts, audit = audit_and_resolve_ratio_duplicates(df)
    assert len(clean) == 1
    assert len(conflicts) == 1


def test_audit_documents():
    df = pd.DataFrame([
        {"company_id": "TCS", "Year": "2024", "Annual_Report": "http://tcs.com/ar2024.pdf"},
        {"company_id": "TCS", "Year": "2024", "Annual_Report": None},
    ])
    clean, audit, status = audit_documents_dataset(df, {"TCS"})
    assert len(clean) == 1
    col_name = "annual_report" if "annual_report" in clean.columns else "Annual_Report"
    assert clean.iloc[0][col_name] == "http://tcs.com/ar2024.pdf"


def test_parse_analysis_dataset():
    df = pd.DataFrame([
        {"company_id": "TCS", "compounded_sales_growth": "10 Years: 12%  5 Years: 10%  3 Years: 14%"},
    ])
    parsed, failures = parse_analysis_dataset(df)
    assert len(parsed) == 3
    assert parsed.iloc[0]["value_pct"] == 12.0