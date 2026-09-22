"""
Financial Health Score Engine
Nifty 100 Financial Intelligence Platform

Computes a deterministic 0-100 score per company based on 5 weighted pillars:
1. Profitability (20%)
2. Returns (20%)
3. Leverage & Solvency (20%)
4. Cash Flow Quality (20%)
5. Growth Stability (20%)

Saves output into SQLite `health_scores` table.
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


def compute_health_scores(db_path: Path = DB_PATH) -> pd.DataFrame:
    """Compute deterministic health scores for all 92 Nifty companies."""
    ratios_df = calculate_company_ratios(db_path)
    if ratios_df.empty:
        return pd.DataFrame()

    # Get latest year record for each company
    ratios_df = ratios_df.sort_values(by=["company_id", "year"])
    latest_ratios = ratios_df.groupby("company_id").last().reset_index()

    health_records = []

    for idx, row in latest_ratios.iterrows():
        cid = row.get("company_id")
        yr = row.get("year")

        # 1. Profitability Pillar (0-20)
        npm = row.get("net_profit_margin_pct") or 0.0
        opm = row.get("operating_profit_margin_pct") or 0.0
        prof_score = 0.0
        if opm >= 20.0:
            prof_score += 10.0
        elif opm >= 12.0:
            prof_score += 7.0
        elif opm >= 5.0:
            prof_score += 4.0

        if npm >= 15.0:
            prof_score += 10.0
        elif npm >= 8.0:
            prof_score += 7.0
        elif npm >= 3.0:
            prof_score += 4.0

        # 2. Returns Pillar (0-20)
        roe = row.get("return_on_equity_pct") or 0.0
        roce = row.get("roce_pct") or 0.0
        ret_score = 0.0
        if roe >= 20.0:
            ret_score += 10.0
        elif roe >= 14.0:
            ret_score += 7.0
        elif roe >= 8.0:
            ret_score += 4.0

        if roce >= 20.0:
            ret_score += 10.0
        elif roce >= 14.0:
            ret_score += 7.0
        elif roce >= 8.0:
            ret_score += 4.0

        # 3. Leverage Pillar (0-20)
        de = row.get("debt_to_equity")
        ic = row.get("interest_coverage")
        lev_score = 0.0
        if de is not None:
            if de <= 0.1:
                lev_score += 10.0
            elif de <= 0.5:
                lev_score += 8.0
            elif de <= 1.0:
                lev_score += 5.0
            elif de <= 2.0:
                lev_score += 2.0
        else:
            lev_score += 8.0

        if ic is not None:
            if ic >= 10.0:
                lev_score += 10.0
            elif ic >= 5.0:
                lev_score += 7.0
            elif ic >= 2.0:
                lev_score += 4.0
        else:
            lev_score += 8.0

        # 4. Cash Flow Pillar (0-20)
        fcf = row.get("free_cash_flow_cr") or 0.0
        cfo_pat = row.get("cfo_to_pat") or 0.0
        cf_score = 0.0
        if fcf > 0:
            cf_score += 10.0
        elif fcf == 0:
            cf_score += 5.0

        if cfo_pat >= 1.0:
            cf_score += 10.0
        elif cfo_pat >= 0.7:
            cf_score += 7.0
        elif cfo_pat >= 0.4:
            cf_score += 4.0

        # 5. Growth & Stability Pillar (0-20)
        # Check sales & profit positive
        sales = row.get("sales_cr") or 0.0
        np_val = row.get("net_profit_cr") or 0.0
        growth_score = 0.0
        if sales > 0:
            growth_score += 10.0
        if np_val > 0:
            growth_score += 10.0

        total_score = min(100.0, round(prof_score + ret_score + lev_score + cf_score + growth_score, 1))

        if total_score >= 80:
            band = "EXCELLENT"
        elif total_score >= 65:
            band = "GOOD"
        elif total_score >= 50:
            band = "MODERATE"
        elif total_score >= 35:
            band = "WEAK"
        else:
            band = "DISTRESSED"

        health_records.append({
            "company_id": cid,
            "latest_year": yr,
            "score": total_score,
            "band": band,
            "profitability_score": prof_score,
            "returns_score": ret_score,
            "leverage_score": lev_score,
            "cashflow_score": cf_score,
            "growth_score": growth_score,
        })

    scores_df = pd.DataFrame(health_records)

    # Insert into SQLite
    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM health_scores;")
    scores_df.to_sql("health_scores", conn, if_exists="append", index=False)
    conn.close()

    print(f"Health score computation complete: {len(scores_df)} companies processed.")
    return scores_df


if __name__ == "__main__":
    compute_health_scores()
