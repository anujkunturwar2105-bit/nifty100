import sqlite3
import pandas as pd
import pytest

from src.etl.loader import run_etl_pipeline, DB_PATH, OUTPUT_DIR


def test_etl_pipeline_execution():
    """Verify that the full ETL pipeline executes and generates required outputs."""
    res = run_etl_pipeline()

    assert "processed_datasets" in res
    assert "audit_df" in res
    assert "failures_df" in res
    assert res["fk_violations"] == []

    # Verify SQLite DB tables
    assert DB_PATH.exists()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    
    tables_query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    tables = set(row[0] for row in conn.execute(tables_query).fetchall())

    expected_tables = {
        "companies", "profitandloss", "balancesheet", "cashflow",
        "analysis", "documents", "prosandcons", "sectors",
        "stock_prices", "market_cap", "financial_ratios", "peer_groups"
    }

    assert expected_tables.issubset(tables)

    # Verify foreign key check passes
    fk_check = conn.execute("PRAGMA foreign_key_check;").fetchall()
    conn.close()
    assert fk_check == []

    # Verify output CSV files
    assert (OUTPUT_DIR / "load_audit.csv").exists()
    assert (OUTPUT_DIR / "validation_failures.csv").exists()


def test_etl_pipeline_idempotency():
    """Verify that running the pipeline multiple times maintains consistent row counts."""
    run_etl_pipeline()

    conn = sqlite3.connect(DB_PATH)
    count1 = conn.execute("SELECT COUNT(*) FROM companies;").fetchone()[0]
    conn.close()

    # Second run
    run_etl_pipeline()

    conn = sqlite3.connect(DB_PATH)
    count2 = conn.execute("SELECT COUNT(*) FROM companies;").fetchone()[0]
    conn.close()

    assert count1 == count2
    assert count1 == 92
