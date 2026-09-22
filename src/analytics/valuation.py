"""
Valuation Analytics and Outlier Detection Engine
Nifty 100 Financial Intelligence Platform

Calculates sector-relative z-scores (|z| > 3) for key metrics and outputs `outlier_report.csv`.
Manages valuation ratios and handles simulated vs real dataset tagging.
"""

import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analytics.ratios import calculate_company_ratios
from src.config import DB_PATH, OUTPUT_DIR, PROCESSED_DATA_DIR


def detect_sector_outliers(db_path: Path = DB_PATH, threshold_z: float = 3.0) -> pd.DataFrame:
    """
    Calculate sector-relative z-score per company metric.
    Flags outliers where abs(z) > threshold_z (default 3.0).
    Saves to `outlier_report.csv` and SQLite `outliers` table.
    """
    conn = sqlite3.connect(db_path)
    sectors_df = pd.read_sql_query("SELECT * FROM sectors", conn)
    conn.close()

    if sectors_df.empty:
        return pd.DataFrame()

    ratios_df = calculate_company_ratios(db_path)
    if ratios_df.empty:
        return pd.DataFrame()

    latest = ratios_df.sort_values(by=["company_id", "year"]).groupby("company_id").last().reset_index()
    merged = pd.merge(latest, sectors_df, on="company_id", how="inner")

    metrics_to_check = [
        "return_on_equity_pct",
        "operating_profit_margin_pct",
        "net_profit_margin_pct",
        "debt_to_equity",
        "interest_coverage",
        "free_cash_flow_cr",
    ]

    outlier_records = []

    grouped = merged.groupby("broad_sector")
    for sector_name, group in grouped:
        if len(group) < 3:
            continue

        for metric in metrics_to_check:
            vals = group[metric].dropna()
            if len(vals) < 3:
                continue

            mean_val = vals.mean()
            std_val = vals.std()

            if std_val == 0 or pd.isna(std_val):
                continue

            for idx, row in group.iterrows():
                cid = row.get("company_id")
                val = row.get(metric)
                if pd.notna(val):
                    val_f = float(val)
                    z = (val_f - mean_val) / std_val

                    if abs(z) >= threshold_z:
                        outlier_records.append({
                            "company_id": cid,
                            "broad_sector": sector_name,
                            "metric": metric,
                            "value": round(val_f, 2),
                            "sector_mean": round(float(mean_val), 2),
                            "sector_std": round(float(std_val), 2),
                            "z_score": round(float(z), 2),
                        })

    outliers_df = pd.DataFrame(outlier_records)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    outliers_df.to_csv(OUTPUT_DIR / "outlier_report.csv", index=False)
    outliers_df.to_csv(PROCESSED_DATA_DIR / "outlier_report.csv", index=False)

    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM outliers;")
    outliers_df.to_sql("outliers", conn, if_exists="append", index=False)
    conn.close()

    print(f"Outlier detection complete: {len(outliers_df)} sector-relative outliers flagged.")
    return outliers_df


if __name__ == "__main__":
    detect_sector_outliers()
