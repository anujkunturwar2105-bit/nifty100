"""
Streamlit Database Utility Module
Nifty 100 Financial Intelligence Platform
"""

import sqlite3
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import DB_PATH


@st.cache_data(ttl=600)
def get_db_connection(db_path: Path = DB_PATH):
    """Return sqlite3 connection."""
    return sqlite3.connect(db_path)


@st.cache_data(ttl=600)
def load_companies_master(db_path: Path = DB_PATH) -> pd.DataFrame:
    """Load companies master list."""
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM companies ORDER BY id ASC", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def load_table(table_name: str, db_path: Path = DB_PATH) -> pd.DataFrame:
    """Load an entire SQLite table into a DataFrame."""
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()
    return df


@st.cache_data(ttl=600)
def load_company_financials(ticker: str, db_path: Path = DB_PATH) -> dict[str, pd.DataFrame]:
    """Load P&L, BS, CashFlow, Ratios, HealthScore, ProsCons for a given company."""
    conn = sqlite3.connect(db_path)
    pnl = pd.read_sql_query("SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year ASC", conn, params=(ticker,))
    bs = pd.read_sql_query("SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year ASC", conn, params=(ticker,))
    cf = pd.read_sql_query("SELECT * FROM cashflow WHERE company_id = ? ORDER BY year ASC", conn, params=(ticker,))
    ratios = pd.read_sql_query("SELECT * FROM financial_ratios_calc WHERE company_id = ? ORDER BY year ASC", conn, params=(ticker,))
    health = pd.read_sql_query("SELECT * FROM health_scores WHERE company_id = ?", conn, params=(ticker,))
    pc = pd.read_sql_query("SELECT * FROM prosandcons WHERE company_id = ?", conn, params=(ticker,))
    conn.close()

    return {
        "pnl": pnl,
        "bs": bs,
        "cf": cf,
        "ratios": ratios,
        "health": health,
        "pc": pc,
    }
