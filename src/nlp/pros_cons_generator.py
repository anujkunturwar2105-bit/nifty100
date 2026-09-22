"""
Rule-Based NLP Pros and Cons Generator Engine
Nifty 100 Financial Intelligence Platform

Generates deterministic, measurable pros and cons derived directly from quantitative KPIs.
Saves output into SQLite `prosandcons` table.
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


def generate_company_pros_cons(db_path: Path = DB_PATH) -> pd.DataFrame:
    """Generate rule-based quantitative pros and cons for all 92 companies."""
    ratios_df = calculate_company_ratios(db_path)
    if ratios_df.empty:
        return pd.DataFrame()

    latest = ratios_df.sort_values(by=["company_id", "year"]).groupby("company_id").last().reset_index()

    # Load raw pros and cons if existing
    conn = sqlite3.connect(db_path)
    try:
        raw_pc = pd.read_sql_query("SELECT company_id, pros, cons FROM prosandcons", conn)
    except Exception:
        raw_pc = pd.DataFrame()
    conn.close()

    raw_pc_dict = {}
    if not raw_pc.empty:
        for _, r in raw_pc.iterrows():
            cid = r.get("company_id")
            if cid:
                raw_pc_dict[cid] = {"pros": r.get("pros"), "cons": r.get("cons")}

    records = []

    for idx, row in latest.iterrows():
        cid = row.get("company_id")
        roe = row.get("return_on_equity_pct")
        opm = row.get("operating_profit_margin_pct")
        de = row.get("debt_to_equity")
        ic = row.get("interest_coverage")
        fcf = row.get("free_cash_flow_cr")
        div_payout = row.get("dividend_payout_ratio_pct")

        pros_list = []
        cons_list = []

        # Add raw text if available for company
        if cid in raw_pc_dict:
            p_raw = raw_pc_dict[cid].get("pros")
            c_raw = raw_pc_dict[cid].get("cons")
            if p_raw and pd.notna(p_raw):
                pros_list.append(str(p_raw))
            if c_raw and pd.notna(c_raw):
                cons_list.append(str(c_raw))

        # Metric-driven rules
        if roe is not None and roe >= 20.0:
            pros_list.append(f"Company has a high Return on Equity (ROE: {roe:.1f}%)")

        if opm is not None and opm >= 20.0:
            pros_list.append(f"Company maintains strong Operating Profit Margin (OPM: {opm:.1f}%)")

        if de is not None and de <= 0.05:
            pros_list.append("Company is virtually debt-free (D/E <= 0.05)")

        if ic is not None and ic >= 10.0:
            pros_list.append(f"Strong interest coverage ratio ({ic:.1f}x)")

        if fcf is not None and fcf > 0:
            pros_list.append(f"Company generates positive Free Cash Flow (FCF: Rs.{fcf:.1f} Cr)")

        if div_payout is not None and div_payout >= 20.0:
            pros_list.append(f"Company maintains healthy dividend payout ratio ({div_payout:.1f}%)")

        if de is not None and de >= 1.5:
            cons_list.append(f"High financial leverage with Debt-to-Equity of {de:.2f}")

        if ic is not None and ic < 2.0:
            cons_list.append(f"Low interest coverage ratio ({ic:.1f}x)")

        if fcf is not None and fcf < 0:
            cons_list.append(f"Negative Free Cash Flow of Rs.{fcf:.1f} Cr")

        if opm is not None and opm < 8.0:
            cons_list.append(f"Low Operating Profit Margin of {opm:.1f}%")

        pros_str = " | ".join(pros_list) if pros_list else "Maintaining stable financial performance."
        cons_str = " | ".join(cons_list) if cons_list else "No significant financial concerns flagged."

        records.append({
            "company_id": cid,
            "pros": pros_str,
            "cons": cons_str,
            "rule": "QUANTITATIVE_KPI_RULES",
            "metric_value": roe if roe is not None else 0.0,
            "threshold": 20.0,
        })

    pc_df = pd.DataFrame(records)

    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM prosandcons;")
    pc_df.to_sql("prosandcons", conn, if_exists="append", index=False)
    conn.close()

    print(f"NLP Pros & Cons generated for {len(pc_df)} companies.")
    return pc_df


if __name__ == "__main__":
    generate_company_pros_cons()
