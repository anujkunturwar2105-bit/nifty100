"""
Ratio Engine and Production Validation Module
Nifty 100 Financial Intelligence Platform

Computes 50+ Financial KPIs directly from authoritative raw financial statements
(P&L, Balance Sheet, Cash Flow) stored in SQLite data warehouse, and validates them
against reference dataset `financial_ratios`.
"""

import sqlite3
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analytics.cagr import calculate_series_cagr
from src.config import DB_PATH, OUTPUT_DIR


def safe_div(num: float | None, den: float | None, multiplier: float = 1.0) -> float | None:
    """Safe division returning None on zero division, null, or inf values."""
    if num is None or den is None or pd.isna(num) or pd.isna(den):
        return None
    try:
        num_f = float(num)
        den_f = float(den)
        if den_f == 0.0 or np.isinf(num_f) or np.isinf(den_f):
            return None
        res = (num_f / den_f) * multiplier
        if np.isnan(res) or np.isinf(res):
            return None
        return round(res, 4)
    except (ValueError, TypeError, ZeroDivisionError):
        return None


def calculate_company_ratios(db_path: Path = DB_PATH, force_recompute: bool = False) -> pd.DataFrame:
    """
    Compute 50+ Financial KPIs from raw P&L, BS, CF tables in SQLite database.
    Stores and caches in SQLite `financial_ratios_calc` for ultra-fast query performance.
    """
    conn = sqlite3.connect(db_path)

    # Check cache table
    if not force_recompute:
        try:
            cached_df = pd.read_sql_query("SELECT * FROM financial_ratios_calc", conn)
            if not cached_df.empty:
                conn.close()
                return cached_df
        except Exception:
            pass

    # Read raw tables
    pnl_df = pd.read_sql_query("SELECT * FROM profitandloss", conn)
    bs_df = pd.read_sql_query("SELECT * FROM balancesheet", conn)
    cf_df = pd.read_sql_query("SELECT * FROM cashflow", conn)
    try:
        mc_df = pd.read_sql_query("SELECT * FROM market_cap", conn)
    except Exception:
        mc_df = pd.DataFrame()

    conn.close()

    # Merge financial statements on (company_id, year)
    merged = pd.merge(pnl_df, bs_df, on=["company_id", "year"], how="outer", suffixes=("_pnl", "_bs"))
    merged = pd.merge(merged, cf_df, on=["company_id", "year"], how="outer", suffixes=("", "_cf"))

    if not mc_df.empty:
        merged = pd.merge(merged, mc_df, on=["company_id", "year"], how="left", suffixes=("", "_mc"))

    records = []

    # Process each company and year
    for idx, row in merged.iterrows():
        cid = row.get("company_id")
        yr = row.get("year")
        if not cid or not yr or yr == "PARSE_ERROR":
            continue

        sales = row.get("sales")
        expenses = row.get("expenses")
        op = row.get("operating_profit")
        other_inc = row.get("other_income") or 0.0
        interest = row.get("interest") or 0.0
        depr = row.get("depreciation") or 0.0
        pbt = row.get("profit_before_tax")
        tax_pct = row.get("tax_percentage") or 0.0
        np_profit = row.get("net_profit")
        eps = row.get("eps")
        div_payout = row.get("dividend_payout") or 0.0

        eq_cap = row.get("equity_capital") or 0.0
        reserves = row.get("reserves") or 0.0
        borrowings = row.get("borrowings") or 0.0
        other_liab = row.get("other_liabilities") or 0.0
        total_liab = row.get("total_liabilities") or 0.0
        fixed_assets = row.get("fixed_assets") or 0.0
        cwip = row.get("cwip") or 0.0
        investments = row.get("investments") or 0.0
        other_assets = row.get("other_asset") or 0.0
        total_assets = row.get("total_assets") or 0.0

        cfo = row.get("operating_activity") or 0.0
        cfi = row.get("investing_activity") or 0.0
        cff = row.get("financing_activity") or 0.0
        net_cf = row.get("net_cash_flow") or 0.0

        mcap = row.get("market_cap_crore")

        # Key aggregates
        net_worth = eq_cap + reserves
        ebit = (op or 0.0) + other_inc
        ebitda = ebit + depr
        capital_employed = total_assets - other_liab if total_assets else (net_worth + borrowings)
        capex = abs(cfi) if cfi < 0 else 0.0
        fcf = cfo - capex

        # 50+ KPIs calculation
        kpis = {
            "company_id": cid,
            "year": yr,

            # Profitability & Margins
            "net_profit_margin_pct": safe_div(np_profit, sales, 100.0),
            "operating_profit_margin_pct": safe_div(op, sales, 100.0),
            "ebit_margin_pct": safe_div(ebit, sales, 100.0),
            "ebitda_margin_pct": safe_div(ebitda, sales, 100.0),
            "pbt_margin_pct": safe_div(pbt, sales, 100.0),
            "cost_to_sales_pct": safe_div(expenses, sales, 100.0),

            # Return Metrics
            "return_on_equity_pct": safe_div(np_profit, net_worth, 100.0),
            "roce_pct": safe_div(ebit, capital_employed, 100.0),
            "return_on_assets_pct": safe_div(np_profit, total_assets, 100.0),
            "return_on_capital_employed_pct": safe_div(ebit, capital_employed, 100.0),
            "croic_pct": safe_div(cfo, capital_employed, 100.0),

            # Capital Structure & Solvency
            "debt_to_equity": safe_div(borrowings, net_worth),
            "interest_coverage": safe_div(ebit, interest),
            "debt_to_assets": safe_div(borrowings, total_assets),
            "debt_to_ebitda": safe_div(borrowings, ebitda),
            "equity_ratio": safe_div(net_worth, total_assets),
            "financial_leverage": safe_div(total_assets, net_worth),
            "total_debt_cr": borrowings,

            # Asset Efficiency & Turnover
            "asset_turnover": safe_div(sales, total_assets),
            "fixed_asset_turnover": safe_div(sales, fixed_assets),
            "working_capital_turnover": safe_div(sales, other_assets - other_liab),
            "capital_turnover": safe_div(sales, capital_employed),
            "investment_to_assets_pct": safe_div(investments, total_assets, 100.0),
            "cwip_to_fixed_assets_pct": safe_div(cwip, fixed_assets, 100.0),

            # Cash Flow Intelligence
            "cash_from_operations_cr": cfo,
            "free_cash_flow_cr": fcf,
            "capex_cr": capex,
            "cfo_to_pat": safe_div(cfo, np_profit),
            "fcf_conversion_pct": safe_div(fcf, np_profit, 100.0),
            "capex_intensity_pct": safe_div(capex, sales, 100.0),
            "cfo_to_debt": safe_div(cfo, borrowings),
            "net_cash_flow_cr": net_cf,

            # Per Share & Valuation Indicators
            "earnings_per_share": eps,
            "book_value_per_share": safe_div(net_worth, safe_div(np_profit, eps) if eps else None),
            "dividend_payout_ratio_pct": div_payout,
            "fcf_per_share": safe_div(fcf, safe_div(np_profit, eps) if eps else None),
            "cfo_per_share": safe_div(cfo, safe_div(np_profit, eps) if eps else None),
            "pe_ratio": safe_div(mcap, np_profit) if mcap else None,
            "pb_ratio": safe_div(mcap, net_worth) if mcap else None,
            "fcf_yield_pct": safe_div(fcf, mcap, 100.0) if mcap else None,

            # Raw Statement Values
            "sales_cr": sales,
            "expenses_cr": expenses,
            "operating_profit_cr": op,
            "other_income_cr": other_inc,
            "interest_cr": interest,
            "depreciation_cr": depr,
            "pbt_cr": pbt,
            "net_profit_cr": np_profit,
            "net_worth_cr": net_worth,
            "total_assets_cr": total_assets,
            "total_liabilities_cr": total_liab,
            "fixed_assets_cr": fixed_assets,
        }

        records.append(kpis)

    df_ratios = pd.DataFrame(records)

    # Save to SQLite table financial_ratios_calc
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("DELETE FROM financial_ratios_calc;")
        df_ratios.to_sql("financial_ratios_calc", conn, if_exists="append", index=False)
    except Exception as e:
        print(f"Warning: Failed to cache financial_ratios_calc to SQLite: {e}")
    finally:
        conn.close()

    return df_ratios


def run_production_ratio_validation(
    computed_df: pd.DataFrame,
    db_path: Path = DB_PATH,
    tolerance_pct: float = 2.0
) -> pd.DataFrame:
    """
    Section 23 Production Data Validation:
    Compare calculated KPI values against reference financial_ratios dataset in SQLite.
    Outputs output/ratio_validation.csv.
    """
    conn = sqlite3.connect(db_path)
    ref_df = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    conn.close()

    if ref_df.empty or computed_df.empty:
        return pd.DataFrame()

    merged = pd.merge(
        computed_df, ref_df,
        on=["company_id", "year"],
        how="inner",
        suffixes=("_calc", "_ref")
    )

    metrics_to_compare = [
        ("net_profit_margin_pct", "net_profit_margin_pct"),
        ("operating_profit_margin_pct", "operating_profit_margin_pct"),
        ("return_on_equity_pct", "return_on_equity_pct"),
        ("debt_to_equity", "debt_to_equity"),
        ("interest_coverage", "interest_coverage"),
        ("asset_turnover", "asset_turnover"),
        ("free_cash_flow_cr", "free_cash_flow_cr"),
        ("capex_cr", "capex_cr"),
        ("earnings_per_share", "earnings_per_share"),
        ("book_value_per_share", "book_value_per_share"),
        ("dividend_payout_ratio_pct", "dividend_payout_ratio_pct"),
        ("total_debt_cr", "total_debt_cr"),
        ("cash_from_operations_cr", "cash_from_operations_cr"),
    ]

    val_records = []

    for _, row in merged.iterrows():
        cid = row.get("company_id")
        yr = row.get("year")

        for calc_col, ref_col in metrics_to_compare:
            calc_val = row.get(f"{calc_col}_calc") if f"{calc_col}_calc" in row else row.get(calc_col)
            ref_val = row.get(f"{ref_col}_ref") if f"{ref_col}_ref" in row else row.get(ref_col)

            if pd.notna(calc_val) and pd.notna(ref_val):
                calc_val = float(calc_val)
                ref_val = float(ref_val)

                abs_diff = abs(calc_val - ref_val)
                pct_diff = (abs_diff / abs(ref_val) * 100.0) if ref_val != 0 else 0.0
                status = "PASS" if (pct_diff <= tolerance_pct or abs_diff <= 0.05) else "MISMATCH"

                val_records.append({
                    "company_id": cid,
                    "year": yr,
                    "metric": calc_col,
                    "computed_value": round(calc_val, 4),
                    "reference_value": round(ref_val, 4),
                    "absolute_difference": round(abs_diff, 4),
                    "percentage_difference": round(pct_diff, 2),
                    "status": status,
                })

    val_df = pd.DataFrame(val_records)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    val_df.to_csv(OUTPUT_DIR / "ratio_validation.csv", index=False)
    print(f"Production Ratio Validation saved to: {OUTPUT_DIR / 'ratio_validation.csv'}")

    return val_df


if __name__ == "__main__":
    df_calc = calculate_company_ratios(force_recompute=True)
    print(f"Calculated {len(df_calc)} ratio records with {len(df_calc.columns)} fields.")
    val_res = run_production_ratio_validation(df_calc)
    if not val_res.empty:
        pass_count = sum(1 for s in val_res["status"] if s == "PASS")
        print(f"Ratio Validation Pass Rate: {pass_count}/{len(val_res)} ({pass_count/len(val_res)*100:.1f}%)")
