"""
Cash Flow Intelligence & Capital Allocation Module
Nifty 100 Financial Intelligence Platform

Classifies CFO/CFI/CFF sign patterns into capital allocation strategies:
- Organic Expansion (+ / - / -)
- Debt-Funded Expansion (+ / - / +)
- Restructuring / Liquidation (- / + / +)
- Financial Distress (- / - / +)
- Cash Generation (+ / + / -)

Computes CapEx intensity, FCF conversion, and distress indicators.
Saves results into SQLite `capital_allocation` table and `output/capital_allocation.csv`.
"""

import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import DB_PATH, OUTPUT_DIR, PROCESSED_DATA_DIR


def classify_capital_allocation(db_path: Path = DB_PATH) -> pd.DataFrame:
    """Classify CFO/CFI/CFF sign patterns across all historical years."""
    conn = sqlite3.connect(db_path)
    cf_df = pd.read_sql_query("SELECT * FROM cashflow", conn)
    pnl_df = pd.read_sql_query("SELECT * FROM profitandloss", conn)
    conn.close()

    if cf_df.empty:
        print("Warning: cashflow table is empty.")
        return pd.DataFrame()

    merged = pd.merge(cf_df, pnl_df, on=["company_id", "year"], how="left")

    records = []

    for idx, row in merged.iterrows():
        cid = row.get("company_id")
        yr = row.get("year")
        cfo = row.get("operating_activity") or 0.0
        cfi = row.get("investing_activity") or 0.0
        cff = row.get("financing_activity") or 0.0
        sales = row.get("sales") or 0.0
        np_profit = row.get("net_profit") or 0.0

        cfo_sign = 1 if cfo > 0 else (-1 if cfo < 0 else 0)
        cfi_sign = 1 if cfi > 0 else (-1 if cfi < 0 else 0)
        cff_sign = 1 if cff > 0 else (-1 if cff < 0 else 0)

        pattern = f"{'+' if cfo_sign>0 else ('-' if cfo_sign<0 else '0')} / {'+' if cfi_sign>0 else ('-' if cfi_sign<0 else '0')} / {'+' if cff_sign>0 else ('-' if cff_sign<0 else '0')}"

        # Strategic Classification based on sign patterns
        if cfo_sign > 0 and cfi_sign < 0 and cff_sign < 0:
            classification = "Organic Expansion & Deleveraging"
        elif cfo_sign > 0 and cfi_sign < 0 and cff_sign > 0:
            classification = "Debt/Equity Funded Expansion"
        elif cfo_sign > 0 and cfi_sign > 0 and cff_sign < 0:
            classification = "Divestment & Capital Return"
        elif cfo_sign < 0 and cff_sign > 0:
            classification = "Financial Distress / External Funding Dependency"
        else:
            classification = "Balanced Capital Transition"

        capex = abs(cfi) if cfi < 0 else 0.0
        fcf = cfo - capex
        capex_intensity = round((capex / sales * 100.0), 2) if sales > 0 else None
        fcf_conversion = round((fcf / np_profit * 100.0), 2) if np_profit > 0 else None

        records.append({
            "company_id": cid,
            "year": yr,
            "cfo_sign": cfo_sign,
            "cfi_sign": cfi_sign,
            "cff_sign": cff_sign,
            "pattern": pattern,
            "classification": classification,
            "capex_intensity": capex_intensity,
            "fcf_conversion": fcf_conversion,
        })

    alloc_df = pd.DataFrame(records)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    alloc_df.to_csv(OUTPUT_DIR / "capital_allocation.csv", index=False)
    alloc_df.to_csv(PROCESSED_DATA_DIR / "capital_allocation.csv", index=False)

    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM capital_allocation;")
    alloc_df.to_sql("capital_allocation", conn, if_exists="append", index=False)
    conn.close()

    print(f"Capital allocation classification complete: {len(alloc_df)} records.")
    return alloc_df


if __name__ == "__main__":
    classify_capital_allocation()
