"""
ETL Normalization and Deduplication Module
Nifty 100 Financial Intelligence Platform
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize DataFrame column names:
    - Strip leading/trailing whitespace
    - Convert to lowercase
    - Replace spaces, hyphens, slashes with underscores
    - Remove newlines and non-alphanumeric characters (except underscore)
    - Remove duplicate underscores
    - Map known column aliases
    """
    df = df.copy()
    new_cols = []
    alias_map = {
        "company_id": "company_id",
        "company_name": "company_name",
        "companyname": "company_name",
        "year": "year",
        "annual_report": "annual_report",
        "annualreport": "annual_report",
        "id": "id",
        "pros": "pros",
        "cons": "cons",
    }

    for col in df.columns:
        c_str = str(col).strip().lower()
        c_str = re.sub(r"[\r\n]+", "", c_str)
        c_str = re.sub(r"[\s\-\/\\]+", "_", c_str)
        c_str = re.sub(r"[^\w]", "", c_str)
        c_str = re.sub(r"_+", "_", c_str).strip("_")

        # Map alias if available
        c_mapped = alias_map.get(c_str, c_str)
        new_cols.append(c_mapped)

    df.columns = new_cols
    return df


def normalize_ticker(value: object) -> str | None:
    """
    Normalize ticker / company ID symbol.
    Rules:
    - Strip whitespace and convert to uppercase.
    - Reject empty or invalid lengths outside 2-12 characters.
    - Map confirmed source typos (e.g. AGTL -> ATGL).
    """
    if value is None or pd.isna(value):
        return None

    ticker = str(value).strip().upper()
    ticker = re.sub(r"\s+", "", ticker)

    if not ticker or ticker in ("NAN", "NONE", "NULL"):
        return None

    if not (2 <= len(ticker) <= 12):
        return None

    # Source typo corrections
    if ticker == "AGTL":
        ticker = "ATGL"

    return ticker


def normalize_year(value: object) -> str:
    """
    Normalize financial year / date field into YYYY-MM format.
    Handles:
    - Mar 2024, Mar-24, Mar-2024, Dec 2023, Dec-23, Jun-2014, Sep-2014
    - FY 2024, FY24, FY 24
    - 2014, 2024 -> 2024-03
    - TTM -> TTM
    Returns 'PARSE_ERROR' for invalid values.
    """
    if value is None or pd.isna(value):
        return "PARSE_ERROR"

    value_str = str(value).strip()

    if not value_str or value_str.upper() in ("NAN", "NONE", "NULL", ""):
        return "PARSE_ERROR"

    if value_str.upper() == "TTM":
        return "TTM"

    # YYYY-MM check
    if re.fullmatch(r"\d{4}-\d{2}", value_str):
        try:
            m = int(value_str.split("-")[1])
            if 1 <= m <= 12:
                return value_str
        except ValueError:
            pass

    # FY formats: FY 2024, FY24, FY 24
    match = re.fullmatch(r"FY\s*(\d{2,4})", value_str, re.IGNORECASE)
    if match:
        year_num = int(match.group(1))
        if year_num < 100:
            year_num += 2000
        return f"{year_num:04d}-03"

    # 4-digit year: 2024
    if re.fullmatch(r"\d{4}", value_str):
        year_num = int(value_str)
        if 1900 <= year_num <= 2100:
            return f"{year_num:04d}-03"

    # Standard date formats
    for fmt in (
        "%b-%y", "%b-%Y", "%B-%Y", "%b %y", "%B %y",
        "%b %Y", "%B %Y", "%Y-%b", "%Y-%B", "%d-%b-%Y", "%Y-%m-%d"
    ):
        try:
            dt = datetime.strptime(value_str, fmt)
            return dt.strftime("%Y-%m")
        except ValueError:
            pass

    # Fallback with pandas to_datetime
    try:
        dt = pd.to_datetime(value_str)
        if pd.notna(dt):
            return dt.strftime("%Y-%m")
    except Exception:
        pass

    return "PARSE_ERROR"


def normalize_doc_year(value: object) -> int | None:
    """
    Normalize document year to integer calendar year (e.g. 2024).
    """
    if value is None or pd.isna(value):
        return None
    val_str = str(value).strip()
    match = re.search(r"\b(19\d{2}|20\d{2})\b", val_str)
    if match:
        return int(match.group(1))
    return None


def detect_excel_header(path: Path, expected_indicators: list[str], max_rows: int = 10) -> int:
    """
    Dynamically detect the header row of an Excel file by reading the first max_rows
    and checking which row contains expected column indicators while skipping metadata rows.
    Returns the 0-indexed row number. Defaults to 0 if not found.
    """
    if not path.exists():
        return 0

    for r in range(max_rows):
        try:
            df_test = pd.read_excel(path, nrows=1, header=r)
            cols = [str(c).strip().lower() for c in df_test.columns]
            unnamed_count = sum(1 for c in cols if c.startswith("unnamed"))
            if unnamed_count > len(cols) / 2:
                continue

            matches = sum(1 for ind in expected_indicators if any(ind.lower() in col for col in cols))
            if matches >= 1:
                return r
        except Exception:
            continue

    return 0


def deduplicate_annual_records(
    df: pd.DataFrame,
    table_name: str,
    source_file: str,
) -> tuple[pd.DataFrame, list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Perform deterministic annual deduplication on (company_id, year).
    Returns:
    - deduplicated_df: DataFrame with unique (company_id, year)
    - duplicate_logs: List of log records for audit logging
    - failure_records: List of DQ failure records for rejected duplicates
    """
    if "company_id" not in df.columns or "year" not in df.columns:
        return df.copy(), [], []

    df_copy = df.copy()
    duplicate_logs: list[dict[str, Any]] = []
    failure_records: list[dict[str, Any]] = []

    dup_mask = df_copy.duplicated(subset=["company_id", "year"], keep=False)
    if not dup_mask.any():
        return df_copy, duplicate_logs, failure_records

    dup_groups = df_copy[dup_mask].groupby(["company_id", "year"])
    surviving_indices: list[int] = []

    for (cid, yr), group in dup_groups:
        count = len(group)
        scores = []
        for idx, row in group.iterrows():
            non_nulls = row.notna().sum()
            non_zeros = sum(
                1 for v in row.values
                if isinstance(v, (int, float)) and pd.notna(v) and v != 0
            )
            scores.append((non_nulls, non_zeros, -idx, idx))

        scores.sort(key=lambda s: (s[0], s[1], s[2]), reverse=True)
        winner_idx = scores[0][3]

        for idx, row in group.iterrows():
            if idx == winner_idx:
                surviving_indices.append(idx)
            else:
                failure_records.append({
                    "rule_id": "DQ-02",
                    "company_id": cid,
                    "year": yr,
                    "field": "company_id,year",
                    "issue": f"Duplicate record rejected during deterministic deduplication (group size={count})",
                    "severity": "WARNING",
                    "source_file": source_file,
                    "original_value": f"Row {idx}",
                    "corrected_value": f"Preserved Row {winner_idx}",
                    "action": "REJECTED_DUPLICATE",
                })

        duplicate_logs.append({
            "table": table_name,
            "source_file": source_file,
            "company_id": cid,
            "year": yr,
            "duplicate_count": count,
            "surviving_row_idx": winner_idx,
            "rejected_count": count - 1,
        })

    non_dup_indices = df_copy[~dup_mask].index
    all_keep_indices = sorted(list(non_dup_indices) + surviving_indices)
    dedup_df = df_copy.loc[all_keep_indices].reset_index(drop=True)

    return dedup_df, duplicate_logs, failure_records


def audit_and_resolve_ratio_duplicates(
    df: pd.DataFrame,
    raw_statement_df: pd.DataFrame | None = None
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Section 6 Data Quality Handling for financial_ratios.xlsx:
    1. Group by (company_id, year).
    2. Identify exact duplicates vs conflicting duplicates.
    3. For exact duplicates: retain one.
    4. For conflicting duplicates: recompute or retain deterministic record and quarantine in conflicts.
    """
    if "company_id" not in df.columns or "year" not in df.columns:
        return df, pd.DataFrame(), pd.DataFrame()

    df_copy = df.copy()
    dup_mask = df_copy.duplicated(subset=["company_id", "year"], keep=False)

    if not dup_mask.any():
        return df_copy, pd.DataFrame(), pd.DataFrame()

    conflicts_list = []
    audit_list = []
    keep_indices = []

    non_dup_df = df_copy[~dup_mask]
    keep_indices.extend(non_dup_df.index.tolist())

    dup_groups = df_copy[dup_mask].groupby(["company_id", "year"])

    for (cid, yr), group in dup_groups:
        source_indices = group.index.tolist()
        subset_cols = [c for c in group.columns if c not in ("id",)]
        group_no_id = group[subset_cols]
        is_exact = group_no_id.drop_duplicates().shape[0] == 1

        if is_exact:
            winner_idx = source_indices[0]
            keep_indices.append(winner_idx)
            audit_list.append({
                "company_id": cid,
                "year": yr,
                "conflict_type": "EXACT_DUPLICATE",
                "source_rows": str(source_indices),
                "fields_different": "NONE",
                "resolution": "RETAINED_FIRST_EXACT",
                "resolution_reason": f"Exact duplicate across all {len(subset_cols)} fields.",
            })
        else:
            diff_fields = []
            for col in subset_cols:
                if group[col].nunique(dropna=False) > 1:
                    diff_fields.append(col)

            diff_str = ",".join(diff_fields)

            scores = []
            for idx, row in group.iterrows():
                non_nulls = row.notna().sum()
                non_zeros = sum(1 for v in row.values if isinstance(v, (int, float)) and pd.notna(v) and v != 0)
                scores.append((non_nulls, non_zeros, -idx, idx))
            scores.sort(key=lambda s: (s[0], s[1], s[2]), reverse=True)
            winner_idx = scores[0][3]
            keep_indices.append(winner_idx)

            conflict_record = {
                "company_id": cid,
                "year": yr,
                "conflict_type": "DATA_CONFLICT",
                "source_rows": str(source_indices),
                "fields_different": diff_str,
                "resolution": f"RETAINED_DETERMINISTIC_ROW_{winner_idx}",
                "resolution_reason": "Highest non-null and non-zero attribute count.",
            }
            conflicts_list.append(conflict_record)
            audit_list.append(conflict_record)

    clean_df = df_copy.loc[sorted(keep_indices)].reset_index(drop=True)
    conflicts_df = pd.DataFrame(conflicts_list)
    audit_df = pd.DataFrame(audit_list)

    return clean_df, conflicts_df, audit_df


def audit_documents_dataset(df: pd.DataFrame, nifty92_ids: set[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Section 7 Document Data Issue Normalization.
    """
    df_copy = normalize_columns(df)
    if "company_id" in df_copy.columns:
        df_copy["company_id"] = df_copy["company_id"].apply(normalize_ticker)
    if "year" in df_copy.columns:
        df_copy["year"] = df_copy["year"].apply(normalize_doc_year)
    elif "Year" in df_copy.columns:
        df_copy["year"] = df_copy["Year"].apply(normalize_doc_year)

    df_copy = df_copy[df_copy["company_id"].notna()].copy()

    dup_audit = []
    keep_indices = []

    dup_mask = df_copy.duplicated(subset=["company_id", "year"], keep=False)
    non_dup = df_copy[~dup_mask]
    keep_indices.extend(non_dup.index.tolist())

    if dup_mask.any():
        groups = df_copy[dup_mask].groupby(["company_id", "year"])
        for (cid, yr), group in groups:
            scores = []
            for idx, row in group.iterrows():
                url = str(row.get("annual_report", "")).strip()
                has_url = 1 if (url and url.lower() not in ("nan", "none", "")) else 0
                scores.append((has_url, len(url), -idx, idx))
            scores.sort(key=lambda s: (s[0], s[1], s[2]), reverse=True)
            winner_idx = scores[0][3]
            keep_indices.append(winner_idx)

            dup_audit.append({
                "company_id": cid,
                "year": yr,
                "total_records": len(group),
                "retained_row_idx": winner_idx,
                "retained_url": group.loc[winner_idx].get("annual_report"),
                "action": "DEDUPLICATED_DOCUMENTS",
            })

    clean_df = df_copy.loc[sorted(keep_indices)].reset_index(drop=True)

    all_doc_cids = sorted(list(set(clean_df["company_id"].dropna())))
    universe_status = []
    for cid in all_doc_cids:
        in_nifty = cid in nifty92_ids
        universe_status.append({
            "company_id": cid,
            "in_nifty92": in_nifty,
            "reason": "Included in Nifty 92 Universe" if in_nifty else "Document company outside Nifty 92 analytical universe",
        })

    return clean_df, pd.DataFrame(dup_audit), pd.DataFrame(universe_status)


def parse_analysis_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Section 8 Analysis Dataset Parsing.
    """
    parsed_rows = []
    failures = []

    pattern = re.compile(r"(10\s*Years|5\s*Years|3\s*Years|TTM|Last\s*Year):\s*(-?\d+(?:\.\d+)?)\s*%", re.IGNORECASE)
    metric_cols = [c for c in df.columns if c not in ("id", "company_id")]

    for idx, row in df.iterrows():
        cid = normalize_ticker(row.get("company_id"))
        if not cid:
            continue

        for col in metric_cols:
            val_str = str(row.get(col, "")).strip()
            if not val_str or val_str.lower() in ("nan", "none"):
                continue

            matches = pattern.findall(val_str)
            if matches:
                for period_str, val_pct_str in matches:
                    parsed_rows.append({
                        "company_id": cid,
                        "metric": col,
                        "period": period_str.strip(),
                        "value_pct": float(val_pct_str),
                        "raw_text": val_str,
                    })
            else:
                failures.append({
                    "company_id": cid,
                    "metric": col,
                    "raw_text": val_str,
                    "reason": "Pattern match failed for period:value% regex",
                })

    return pd.DataFrame(parsed_rows), pd.DataFrame(failures)