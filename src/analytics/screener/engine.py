"""
Investment Screener Engine
Nifty 100 Financial Intelligence Platform

Supports predefined screener presets (QUALITY, VALUE, GROWTH, DIVIDEND, MOMENTUM, DEBT_FREE)
and custom multi-criteria filtering. Used centrally by Streamlit dashboard and FastAPI endpoints.
"""

import sqlite3
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analytics.health_score import compute_health_scores
from src.analytics.ratios import calculate_company_ratios
from src.config import CONFIG_DIR, DB_PATH

SCREENER_CONFIG_PATH = CONFIG_DIR / "screener_config.yaml"


def load_screener_config() -> dict[str, Any]:
    """Load preset screener definitions from YAML config."""
    if not SCREENER_CONFIG_PATH.exists():
        return {}
    with open(SCREENER_CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def run_screener(
    preset: str | None = None,
    custom_filters: dict[str, Any] | None = None,
    db_path: Path = DB_PATH
) -> pd.DataFrame:
    """
    Run screener on Nifty 100 analytical universe.

    Args:
    - preset: Preset name (e.g. 'QUALITY', 'VALUE', 'GROWTH', 'DIVIDEND', 'MOMENTUM', 'DEBT_FREE')
    - custom_filters: Dict of filter criteria (e.g. {'roe_min': 15, 'debt_to_equity_max': 0.5})

    Returns:
    - DataFrame of screened companies with metrics and scores.
    """
    # Get latest ratios
    ratios_df = calculate_company_ratios(db_path)
    if ratios_df.empty:
        return pd.DataFrame()

    latest_ratios = ratios_df.sort_values(by=["company_id", "year"]).groupby("company_id").last().reset_index()

    # Load master company info & sectors & health scores
    conn = sqlite3.connect(db_path)
    companies_df = pd.read_sql_query("SELECT id as company_id, company_name FROM companies", conn)
    sectors_df = pd.read_sql_query("SELECT company_id, broad_sector, sub_sector FROM sectors", conn)
    health_df = pd.read_sql_query("SELECT company_id, score as health_score, band as health_band FROM health_scores", conn)
    conn.close()

    df = pd.merge(companies_df, latest_ratios, on="company_id", how="inner")
    if not sectors_df.empty:
        df = pd.merge(df, sectors_df, on="company_id", how="left")
    if not health_df.empty:
        df = pd.merge(df, health_df, on="company_id", how="left")

    # Combine preset and custom filters
    filters = {}
    cfg = load_screener_config()
    presets = cfg.get("presets", {})

    if preset and preset.upper() in presets:
        filters.update(presets[preset.upper()].get("filters", {}))

    if custom_filters:
        filters.update(custom_filters)

    # Apply filters iteratively
    filtered = df.copy()

    if "roe_min" in filters:
        filtered = filtered[filtered["return_on_equity_pct"] >= filters["roe_min"]]

    if "roe_max" in filters:
        filtered = filtered[filtered["return_on_equity_pct"] <= filters["roe_max"]]

    if "opm_min" in filters:
        filtered = filtered[filtered["operating_profit_margin_pct"] >= filters["opm_min"]]

    if "npm_min" in filters:
        filtered = filtered[filtered["net_profit_margin_pct"] >= filters["npm_min"]]

    if "debt_to_equity_max" in filters:
        filtered = filtered[(filtered["debt_to_equity"].isna()) | (filtered["debt_to_equity"] <= filters["debt_to_equity_max"])]

    if "fcf_min" in filters:
        filtered = filtered[filtered["free_cash_flow_cr"] >= filters["fcf_min"]]

    if "health_score_min" in filters:
        filtered = filtered[filtered["health_score"] >= filters["health_score_min"]]

    if "pe_max" in filters and "pe_ratio" in filtered.columns:
        filtered = filtered[(filtered["pe_ratio"].notna()) & (filtered["pe_ratio"] <= filters["pe_max"])]

    if "sector" in filters and "broad_sector" in filtered.columns:
        filtered = filtered[filtered["broad_sector"] == filters["sector"]]

    filtered = filtered.sort_values(by="return_on_equity_pct", ascending=False).reset_index(drop=True)
    return filtered


if __name__ == "__main__":
    compute_health_scores()
    res = run_screener(preset="QUALITY")
    print(f"QUALITY preset screener returned {len(res)} companies.")
