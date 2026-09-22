"""
ETL Loader Pipeline for Nifty 100 Financial Intelligence Platform
Executes end-to-end data discovery, loading, normalization, deduplication, validation,
and insertion into SQLite data warehouse.
"""

import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import (
    CORE_FILES,
    DB_PATH,
    OUTPUT_DIR,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    SUPPORTING_DATA_DIR,
    SUPPORTING_FILES,
)
from src.etl.normaliser import (
    audit_and_resolve_ratio_duplicates,
    audit_documents_dataset,
    deduplicate_annual_records,
    detect_excel_header,
    normalize_columns,
    normalize_ticker,
    normalize_year,
    parse_analysis_dataset,
)
from src.etl.validator import validate_all_datasets

HEADER_INDICATORS = {
    "companies": ["id", "company_id", "company_name", "company logo"],
    "profitandloss": ["company_id", "year", "sales", "operating_profit"],
    "balancesheet": ["company_id", "year", "equity_capital", "borrowings", "total_assets"],
    "cashflow": ["company_id", "year", "operating_activity", "investing_activity"],
    "analysis": ["company_id", "compounded_sales_growth", "roe"],
    "documents": ["company_id", "year", "annual_report"],
    "prosandcons": ["company_id", "cons"],
    "sectors": ["company_id", "broad_sector", "sub_sector"],
    "stock_prices": ["company_id", "date", "close_price"],
    "market_cap": ["company_id", "year", "market_cap_crore", "pe_ratio"],
    "financial_ratios": ["company_id", "year", "net_profit_margin_pct", "return_on_equity_pct"],
    "peer_groups": ["peer_group_name", "company_id"],
}


def load_raw_excel(name: str, folder: Path, filename: str) -> pd.DataFrame:
    """Load Excel file with dynamic header detection."""
    path = folder / filename
    if not path.exists():
        print(f"Warning: File {filename} not found in {folder}")
        return pd.DataFrame()

    indicators = HEADER_INDICATORS.get(name, ["company_id", "id", "year"])
    header_row = detect_excel_header(path, indicators)

    try:
        df = pd.read_excel(path, header=header_row)
    except Exception as e:
        print(f"Error reading {path.name}: {e}")
        return pd.DataFrame()

    return df


def run_etl_pipeline() -> dict[str, Any]:
    """Execute complete production ETL pipeline."""
    start_time = time.time()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    print("==================================================")
    print("      NIFTY 100 ETL PIPELINE EXECUTION           ")
    print("==================================================")

    # 1. Discover & Load Core Datasets
    raw_dfs = {}
    for name, filename in CORE_FILES.items():
        df = load_raw_excel(name, RAW_DATA_DIR, filename)
        raw_dfs[name] = df
        print(f"Loaded Core raw dataset '{name:15s}': {len(df):>6} rows.")

    # Discover & Load Supporting Datasets
    supporting_dfs = {}
    for name, filename in SUPPORTING_FILES.items():
        df = load_raw_excel(name, SUPPORTING_DATA_DIR, filename)
        supporting_dfs[name] = df
        print(f"Loaded Supporting raw dataset '{name:15s}': {len(df):>6} rows.")

    all_raw = {**raw_dfs, **supporting_dfs}

    # 2. Normalize Master Companies Table First
    companies_df = all_raw["companies"]
    companies_clean = normalize_columns(companies_df)

    if "id" in companies_clean.columns:
        companies_clean["id"] = companies_clean["id"].apply(normalize_ticker)
    elif "company_id" in companies_clean.columns:
        companies_clean["id"] = companies_clean["company_id"].apply(normalize_ticker)

    companies_clean = companies_clean[companies_clean["id"].notna()].drop_duplicates(subset=["id"]).reset_index(drop=True)
    nifty92_ids = set(companies_clean["id"])

    processed_datasets = {"companies": companies_clean}
    all_validation_failures = []
    ratio_conflicts_df = pd.DataFrame()
    ratio_audit_df = pd.DataFrame()
    doc_audit_df = pd.DataFrame()
    doc_universe_df = pd.DataFrame()
    analysis_parsed_df = pd.DataFrame()
    analysis_failures_df = pd.DataFrame()

    # 3. Process each remaining dataset
    for name, raw_df in all_raw.items():
        if name == "companies" or raw_df.empty:
            continue

        src_file = CORE_FILES.get(name) or SUPPORTING_FILES.get(name, f"{name}.xlsx")
        df_norm = normalize_columns(raw_df)

        # Normalize ticker / company_id
        if "company_id" in df_norm.columns:
            df_norm["company_id"] = df_norm["company_id"].apply(normalize_ticker)

        # Special processing for documents dataset (Section 7)
        if name == "documents":
            clean_docs, doc_audit_df, doc_universe_df = audit_documents_dataset(df_norm, nifty92_ids)
            # Filter for Nifty92 Analytical Universe in DB insertion table
            clean_docs_nifty = clean_docs[clean_docs["company_id"].isin(nifty92_ids)].reset_index(drop=True)
            processed_datasets["documents"] = clean_docs_nifty
            continue

        # Filter orphan foreign keys for analysis tables
        if "company_id" in df_norm.columns:
            df_norm = df_norm[df_norm["company_id"].isin(nifty92_ids)].copy()

        # Normalize year
        if "year" in df_norm.columns:
            df_norm["year"] = df_norm["year"].apply(normalize_year)
            df_norm = df_norm[df_norm["year"] != "PARSE_ERROR"].copy()

        # Special processing for financial ratios (Section 6)
        if name == "financial_ratios":
            clean_ratios, ratio_conflicts_df, ratio_audit_df = audit_and_resolve_ratio_duplicates(df_norm)
            processed_datasets["financial_ratios"] = clean_ratios
            continue

        # Special processing for analysis dataset (Section 8)
        if name == "analysis":
            analysis_parsed_df, analysis_failures_df = parse_analysis_dataset(df_norm)
            processed_datasets["analysis"] = df_norm
            continue

        # General annual table deduplication
        if name in ("profitandloss", "balancesheet", "cashflow", "market_cap"):
            df_final, dup_logs, dup_failures = deduplicate_annual_records(df_norm, name, src_file)
            all_validation_failures.extend(dup_failures)
        else:
            df_final = df_norm

        processed_datasets[name] = df_final

    if not analysis_parsed_df.empty:
        processed_datasets["analysis_parsed"] = analysis_parsed_df

    # 4. DQ Validation
    dq_failures = validate_all_datasets(processed_datasets)
    all_validation_failures.extend(dq_failures)

    # 5. Populate Audit Log
    audit_records = []
    file_mapping = {**CORE_FILES, **SUPPORTING_FILES}

    for name, raw_df in all_raw.items():
        src_file = file_mapping.get(name, f"{name}.xlsx")
        df_final = processed_datasets.get(name, pd.DataFrame())
        rows_in = len(raw_df)
        rows_out = len(df_final)

        file_failures = [f for f in all_validation_failures if f.get("source_file") == src_file]
        crit_count = sum(1 for f in file_failures if f.get("severity") == "CRITICAL")
        warn_count = sum(1 for f in file_failures if f.get("severity") == "WARNING")

        audit_records.append({
            "table": name,
            "source_file": src_file,
            "rows_in": rows_in,
            "rows_out": rows_out,
            "rejected": max(0, rows_in - rows_out),
            "warnings": warn_count,
            "critical_failures": crit_count,
            "timestamp": datetime.now().isoformat(),
            "status": "SUCCESS" if crit_count == 0 else "COMPLETED_WITH_WARNINGS",
        })

    # 6. Database Insertion (SQLite Data Warehouse)
    schema_sql_path = ROOT / "src" / "etl" / "schema.sql"
    with open(schema_sql_path, "r") as f:
        schema_sql = f.read()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")

    # Drop existing tables cleanly for idempotency
    tables_to_drop = [
        "outliers", "clusters", "analysis_parsed", "data_quality_issues",
        "capital_allocation", "sector_metrics", "health_scores", "peer_percentiles",
        "peer_groups", "financial_ratios", "market_cap", "stock_prices",
        "sectors", "prosandcons", "documents", "analysis", "cashflow",
        "balancesheet", "profitandloss", "companies"
    ]
    for tbl in tables_to_drop:
        conn.execute(f"DROP TABLE IF EXISTS {tbl};")

    conn.executescript(schema_sql)

    for name, df in processed_datasets.items():
        if df.empty:
            continue
        df_to_insert = df.copy()
        # Drop auto-increment 'id' column if present in dataframe so SQLite handles autoincrement PKs
        if "id" in df_to_insert.columns and name != "companies":
            df_to_insert = df_to_insert.drop(columns=["id"])

        try:
            df_to_insert.to_sql(name, conn, if_exists="append", index=False)
            print(f"SQLite -> Loaded table '{name:20s}': {len(df_to_insert):>6} rows.")
        except Exception as e:
            print(f"Error loading table '{name}' into SQLite: {e}")

    # Check Foreign Keys
    fk_violations = conn.execute("PRAGMA foreign_key_check;").fetchall()
    conn.close()

    print(f"\nSQLite Foreign Key Violations: {len(fk_violations)}")

    # 7. Write Audit and Data Quality Reports
    audit_df = pd.DataFrame(audit_records)
    audit_df.to_csv(OUTPUT_DIR / "load_audit.csv", index=False)
    audit_df.to_csv(PROCESSED_DATA_DIR / "load_audit.csv", index=False)

    failures_df = pd.DataFrame(all_validation_failures)
    if failures_df.empty:
        failures_df = pd.DataFrame(columns=[
            "rule_id", "company_id", "year", "field", "issue", "severity",
            "source_file", "original_value", "corrected_value", "action"
        ])
    failures_df.to_csv(OUTPUT_DIR / "validation_failures.csv", index=False)
    failures_df.to_csv(PROCESSED_DATA_DIR / "validation_failures.csv", index=False)

    if not ratio_conflicts_df.empty:
        ratio_conflicts_df.to_csv(OUTPUT_DIR / "data_quality_conflicts.csv", index=False)
        ratio_conflicts_df.to_csv(PROCESSED_DATA_DIR / "data_quality_conflicts.csv", index=False)

    if not ratio_audit_df.empty:
        ratio_audit_df.to_csv(OUTPUT_DIR / "ratio_duplicate_audit.csv", index=False)

    if not doc_audit_df.empty:
        doc_audit_df.to_csv(OUTPUT_DIR / "documents_duplicate_audit.csv", index=False)

    if not doc_universe_df.empty:
        doc_universe_df.to_csv(OUTPUT_DIR / "document_universe_status.csv", index=False)

    if not analysis_failures_df.empty:
        analysis_failures_df.to_csv(OUTPUT_DIR / "analysis_parse_failures.csv", index=False)

    # Summary TXT
    summary_txt = f"""==================================================
NIFTY 100 PLATFORM DATA QUALITY SUMMARY
Generated: {datetime.now().isoformat()}
==================================================

Source File Performance:
--------------------------------------------------
"""
    for rec in audit_records:
        summary_txt += f"Source: {rec['source_file']:25s} | In: {rec['rows_in']:5d} | Out: {rec['rows_out']:5d} | Warnings: {rec['warnings']:3d} | Critical: {rec['critical_failures']:3d}\n"

    summary_txt += f"""
Data Quality Highlights:
--------------------------------------------------
- Master Companies Universe: {len(companies_clean)} companies
- Ratio Conflict Records: {len(ratio_conflicts_df)}
- Document Duplicate Audit Logs: {len(doc_audit_df)}
- Parsed Analysis CAGR Records: {len(analysis_parsed_df)}
- Total Validation Issues Flagged: {len(failures_df)}
- SQLite Foreign Key Violations: {len(fk_violations)}

Status: PIPELINE COMPLETE
==================================================
"""
    with open(OUTPUT_DIR / "data_quality_summary.txt", "w") as f:
        f.write(summary_txt)

    elapsed = round(time.time() - start_time, 2)
    print(f"\n=== SPRINT 1 ETL COMPLETED IN {elapsed}s ===")
    print(f"Data Quality Summary written to: {OUTPUT_DIR / 'data_quality_summary.txt'}")

    return {
        "processed_datasets": processed_datasets,
        "audit_df": audit_df,
        "failures_df": failures_df,
        "ratio_conflicts_df": ratio_conflicts_df,
        "fk_violations": fk_violations,
    }


if __name__ == "__main__":
    run_etl_pipeline()