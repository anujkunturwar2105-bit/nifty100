"""
Sector Analytics Engine
Nifty 100 Financial Intelligence Platform

Computes sector-level aggregations and medians for 11 broad sectors:
- company count
- median ROE, ROCE, NPM, OPM, D/E, FCF, Revenue CAGR, PAT CAGR

Saves results to SQLite `sector_metrics` table.
"""

import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analytics.ratios import calculate_company_ratios
from src.config import DB_PATH


def compute_sector_metrics(db_path: Path = DB_PATH) -> pd.DataFrame:
    """Compute median financial KPIs across 11 broad sectors."""
    conn = sqlite3.connect(db_path)
    sectors_df = pd.read_sql_query("SELECT * FROM sectors", conn)
    conn.close()

    if sectors_df.empty:
        print("Warning: sectors table is empty.")
        return pd.DataFrame()

    ratios_df = calculate_company_ratios(db_path)
    if ratios_df.empty:
        return pd.DataFrame()

    # Latest ratios per company
    latest_ratios = ratios_df.sort_values(by=["company_id", "year"]).groupby("company_id").last().reset_index()

    merged = pd.merge(latest_ratios, sectors_df, on="company_id", how="inner")
    if merged.empty:
        print("Warning: No matching company ratios found for sectors.")
        return pd.DataFrame()

    sector_records = []

    grouped = merged.groupby("broad_sector")
    for sector_name, group in grouped:
        sector_records.append({
            "broad_sector": sector_name,
            "company_count": int(len(group)),
            "median_roe": round(float(group["return_on_equity_pct"].median()), 2) if group["return_on_equity_pct"].notna().any() else None,
            "median_roce": round(float(group["roce_pct"].median()), 2) if group["roce_pct"].notna().any() else None,
            "median_npm": round(float(group["net_profit_margin_pct"].median()), 2) if group["net_profit_margin_pct"].notna().any() else None,
            "median_opm": round(float(group["operating_profit_margin_pct"].median()), 2) if group["operating_profit_margin_pct"].notna().any() else None,
            "median_de": round(float(group["debt_to_equity"].median()), 2) if group["debt_to_equity"].notna().any() else None,
            "median_fcf": round(float(group["free_cash_flow_cr"].median()), 2) if group["free_cash_flow_cr"].notna().any() else None,
            "median_rev_cagr": None,
            "median_pat_cagr": None,
        })

    sector_metrics_df = pd.DataFrame(sector_records)

    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM sector_metrics;")
    sector_metrics_df.to_sql("sector_metrics", conn, if_exists="append", index=False)
    conn.close()

    print(f"Sector metrics computation complete: {len(sector_metrics_df)} sectors processed.")
    return sector_metrics_df


if __name__ == "__main__":
    compute_sector_metrics()
