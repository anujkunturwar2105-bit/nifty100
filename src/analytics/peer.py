"""
Peer Comparison Engine
Nifty 100 Financial Intelligence Platform

Calculates percentile rankings within peer groups for radar chart visualizations.
Saves results into SQLite `peer_percentiles` table.
"""

import sqlite3
import sys
from pathlib import Path

import pandas as pd
from scipy.stats import percentileofscore

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analytics.ratios import calculate_company_ratios
from src.config import DB_PATH


def compute_peer_percentiles(db_path: Path = DB_PATH) -> pd.DataFrame:
    """Compute percentile rankings within peer groups."""
    conn = sqlite3.connect(db_path)
    peer_df = pd.read_sql_query("SELECT * FROM peer_groups", conn)
    conn.close()

    if peer_df.empty:
        print("Warning: peer_groups table is empty.")
        return pd.DataFrame()

    ratios_df = calculate_company_ratios(db_path)
    if ratios_df.empty:
        return pd.DataFrame()

    latest_ratios = ratios_df.sort_values(by=["company_id", "year"]).groupby("company_id").last().reset_index()
    merged = pd.merge(latest_ratios, peer_df, on="company_id", how="inner")

    metrics_list = [
        ("return_on_equity_pct", "ROE"),
        ("roce_pct", "ROCE"),
        ("net_profit_margin_pct", "NPM"),
        ("operating_profit_margin_pct", "OPM"),
        ("debt_to_equity", "D/E"),
        ("free_cash_flow_cr", "FCF"),
    ]

    records = []
    groups = merged.groupby("peer_group_name")

    for group_name, group in groups:
        if len(group) == 0:
            continue
        for metric_col, metric_label in metrics_list:
            vals = group[metric_col].dropna().values
            if len(vals) == 0:
                continue

            for _, row in group.iterrows():
                cid = row.get("company_id")
                val = row.get(metric_col)
                if pd.notna(val):
                    pct = round(float(percentileofscore(vals, float(val), kind="weak")), 1)
                    records.append({
                        "company_id": cid,
                        "peer_group_name": group_name,
                        "metric": metric_label,
                        "value": round(float(val), 2),
                        "percentile": pct,
                    })

    percentiles_df = pd.DataFrame(records)

    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM peer_percentiles;")
    if not percentiles_df.empty:
        percentiles_df.to_sql("peer_percentiles", conn, if_exists="append", index=False)
    conn.close()

    print(f"Peer percentiles computation complete: {len(percentiles_df)} records created.")
    return percentiles_df


if __name__ == "__main__":
    compute_peer_percentiles()
