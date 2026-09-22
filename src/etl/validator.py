from __future__ import annotations

import re
from typing import Any
import pandas as pd


def create_failure_record(
    rule_id: str,
    company_id: str | None,
    year: str | None,
    field: str,
    issue: str,
    severity: str,
    source_file: str,
    original_value: Any = None,
    corrected_value: Any = None,
    action: str = "FLAGGED",
) -> dict[str, Any]:
    """Helper function to create a standardized DQ validation failure dict."""
    return {
        "rule_id": rule_id,
        "company_id": company_id if pd.notna(company_id) else "N/A",
        "year": year if pd.notna(year) else "N/A",
        "field": field,
        "issue": issue,
        "severity": severity,
        "source_file": source_file,
        "original_value": str(original_value) if original_value is not None else "",
        "corrected_value": str(corrected_value) if corrected_value is not None else "",
        "action": action,
    }


def check_dq_01_pk_uniqueness(
    companies_df: pd.DataFrame, source_file: str = "companies.xlsx"
) -> list[dict[str, Any]]:
    """DQ-01: Primary Key uniqueness in companies."""
    failures = []
    pk_col = "id" if "id" in companies_df.columns else "company_id"
    if pk_col not in companies_df.columns:
        return failures

    duplicates = companies_df[companies_df[pk_col].duplicated(keep=False)]
    for _, row in duplicates.iterrows():
        failures.append(
            create_failure_record(
                rule_id="DQ-01",
                company_id=row.get(pk_col),
                year=None,
                field=pk_col,
                issue=f"Duplicate primary key in companies table: '{row.get(pk_col)}'",
                severity="CRITICAL",
                source_file=source_file,
                original_value=row.get(pk_col),
                action="FLAGGED",
            )
        )
    return failures


def check_dq_02_company_year_uniqueness(
    df: pd.DataFrame, table_name: str, source_file: str
) -> list[dict[str, Any]]:
    """DQ-02: No duplicate (company_id, year) in annual financial tables."""
    failures = []
    if "company_id" not in df.columns or "year" not in df.columns:
        return failures

    duplicates = df[df.duplicated(subset=["company_id", "year"], keep=False)]
    for _, row in duplicates.iterrows():
        failures.append(
            create_failure_record(
                rule_id="DQ-02",
                company_id=row.get("company_id"),
                year=row.get("year"),
                field="company_id,year",
                issue=f"Duplicate (company_id, year) key in {table_name}: ({row.get('company_id')}, {row.get('year')})",
                severity="CRITICAL",
                source_file=source_file,
                original_value=f"{row.get('company_id')}_{row.get('year')}",
                action="FLAGGED_DUPLICATE",
            )
        )
    return failures


def check_dq_03_foreign_key_integrity(
    child_df: pd.DataFrame,
    companies_df: pd.DataFrame,
    table_name: str,
    source_file: str,
) -> list[dict[str, Any]]:
    """DQ-03: Foreign key integrity (child company_id exists in companies.id)."""
    failures = []
    cid_col = "id" if "id" in companies_df.columns else "company_id"
    if "company_id" not in child_df.columns or cid_col not in companies_df.columns:
        return failures

    valid_cids = set(companies_df[cid_col].dropna())
    child_cids = child_df["company_id"].dropna()

    missing = child_df[~child_df["company_id"].isin(valid_cids)]
    for _, row in missing.iterrows():
        failures.append(
            create_failure_record(
                rule_id="DQ-03",
                company_id=row.get("company_id"),
                year=row.get("year"),
                field="company_id",
                issue=f"Orphan company_id '{row.get('company_id')}' in table '{table_name}' missing from companies master",
                severity="CRITICAL",
                source_file=source_file,
                original_value=row.get("company_id"),
                action="REJECTED_ORPHAN",
            )
        )
    return failures


def check_dq_04_balance_sheet_balance(
    bs_df: pd.DataFrame, source_file: str = "balancesheet.xlsx"
) -> list[dict[str, Any]]:
    """
    DQ-04: Balance Sheet Balance check.
    abs(total_assets - total_liabilities) / total_assets < 0.01
    """
    failures = []
    if "total_assets" not in bs_df.columns or "total_liabilities" not in bs_df.columns:
        return failures

    for _, row in bs_df.iterrows():
        ta = row.get("total_assets")
        tl = row.get("total_liabilities")
        if pd.notna(ta) and pd.notna(tl) and ta > 0:
            diff_ratio = abs(ta - tl) / ta
            if diff_ratio >= 0.01:
                failures.append(
                    create_failure_record(
                        rule_id="DQ-04",
                        company_id=row.get("company_id"),
                        year=row.get("year"),
                        field="total_assets,total_liabilities",
                        issue=f"Balance sheet imbalance: Assets ({ta}) vs Liabilities ({tl}), diff ratio {diff_ratio:.4f}",
                        severity="WARNING",
                        source_file=source_file,
                        original_value=f"Assets={ta}, Liab={tl}",
                        action="FLAGGED",
                    )
                )
    return failures


def check_dq_05_opm_cross_check(
    pnl_df: pd.DataFrame, source_file: str = "profitandloss.xlsx"
) -> list[dict[str, Any]]:
    """DQ-05: Operating Profit Margin (OPM %) cross-check."""
    failures = []
    opm_col = "operating_profit_margin_pct" if "operating_profit_margin_pct" in pnl_df.columns else "opm_pct"
    op_col = "operating_profit" if "operating_profit" in pnl_df.columns else None
    sales_col = "sales" if "sales" in pnl_df.columns else ("revenue" if "revenue" in pnl_df.columns else None)

    if not opm_col or not op_col or not sales_col:
        return failures

    for _, row in pnl_df.iterrows():
        reported_opm = row.get(opm_col)
        op = row.get(op_col)
        sales = row.get(sales_col)

        if pd.notna(reported_opm) and pd.notna(op) and pd.notna(sales) and sales > 0:
            calc_opm = (op / sales) * 100
            # Allow 5% tolerance due to roundings/other operating components
            if abs(reported_opm - calc_opm) > 5.0:
                failures.append(
                    create_failure_record(
                        rule_id="DQ-05",
                        company_id=row.get("company_id"),
                        year=row.get("year"),
                        field=opm_col,
                        issue=f"OPM mismatch: reported {reported_opm}%, calculated ({op}/{sales}) = {calc_opm:.2f}%",
                        severity="WARNING",
                        source_file=source_file,
                        original_value=reported_opm,
                        corrected_value=round(calc_opm, 2),
                        action="FLAGGED",
                    )
                )
    return failures


def check_dq_06_positive_sales(
    pnl_df: pd.DataFrame,
    companies_df: pd.DataFrame,
    source_file: str = "profitandloss.xlsx",
) -> list[dict[str, Any]]:
    """DQ-06: Positive sales for non-banking companies."""
    failures = []
    sales_col = "sales" if "sales" in pnl_df.columns else ("revenue" if "revenue" in pnl_df.columns else None)
    if not sales_col:
        return failures

    # Identify bank/financial companies if sector information exists
    bank_cids = set()
    if "sector" in companies_df.columns:
        bank_cids = set(
            companies_df[companies_df["sector"].str.contains("Bank|Financial", case=False, na=False)]["id"]
        )

    for _, row in pnl_df.iterrows():
        cid = row.get("company_id")
        sales = row.get(sales_col)
        if cid not in bank_cids and pd.notna(sales) and sales <= 0:
            failures.append(
                create_failure_record(
                    rule_id="DQ-06",
                    company_id=cid,
                    year=row.get("year"),
                    field=sales_col,
                    issue=f"Non-positive sales ({sales}) for non-banking company '{cid}'",
                    severity="WARNING",
                    source_file=source_file,
                    original_value=sales,
                    action="FLAGGED",
                )
            )
    return failures


def check_dq_07_normalized_year(
    df: pd.DataFrame, table_name: str, source_file: str
) -> list[dict[str, Any]]:
    """DQ-07: Year column matches normalized YYYY-MM format."""
    failures = []
    if "year" not in df.columns:
        return failures

    for _, row in df.iterrows():
        yr = str(row.get("year", ""))
        if yr == "TTM":
            continue
        if not re.fullmatch(r"\d{4}-\d{2}", yr):
            failures.append(
                create_failure_record(
                    rule_id="DQ-07",
                    company_id=row.get("company_id"),
                    year=row.get("year"),
                    field="year",
                    issue=f"Unnormalized/unparseable year format '{yr}' in table '{table_name}'",
                    severity="CRITICAL",
                    source_file=source_file,
                    original_value=yr,
                    action="FLAGGED_INVALID_DATE",
                )
            )
    return failures


def check_dq_08_ticker_format(
    df: pd.DataFrame, table_name: str, source_file: str
) -> list[dict[str, Any]]:
    """DQ-08: Ticker normalization and length (2-12 uppercase chars)."""
    failures = []
    cid_col = "id" if "id" in df.columns else "company_id"
    if cid_col not in df.columns:
        return failures

    for _, row in df.iterrows():
        cid = str(row.get(cid_col, ""))
        if not cid or cid == "None" or cid == "nan":
            failures.append(
                create_failure_record(
                    rule_id="DQ-08",
                    company_id=row.get(cid_col),
                    year=row.get("year"),
                    field=cid_col,
                    issue=f"Missing or null company_id in table '{table_name}'",
                    severity="CRITICAL",
                    source_file=source_file,
                    original_value=row.get(cid_col),
                    action="FLAGGED_NULL_TICKER",
                )
            )
        elif not (2 <= len(cid) <= 12) or not cid.isupper() or not cid.isalnum():
            failures.append(
                create_failure_record(
                    rule_id="DQ-08",
                    company_id=row.get(cid_col),
                    year=row.get("year"),
                    field=cid_col,
                    issue=f"Invalid ticker format/length '{cid}' in table '{table_name}'",
                    severity="CRITICAL",
                    source_file=source_file,
                    original_value=row.get(cid_col),
                    action="FLAGGED_INVALID_TICKER",
                )
            )
    return failures


def check_dq_09_cash_flow_reconciliation(
    cf_df: pd.DataFrame, source_file: str = "cashflow.xlsx"
) -> list[dict[str, Any]]:
    """
    DQ-09: Cash flow reconciliation check.
    net_cash_flow ≈ CFO + CFI + CFF (tolerance = 10 Cr)
    """
    failures = []
    cfo_col = "operating_activity" if "operating_activity" in cf_df.columns else "cash_from_operating_activity"
    cfi_col = "investing_activity" if "investing_activity" in cf_df.columns else "cash_from_investing_activity"
    cff_col = "financing_activity" if "financing_activity" in cf_df.columns else "cash_from_financing_activity"
    net_col = "net_cash_flow" if "net_cash_flow" in cf_df.columns else None

    if not (cfo_col in cf_df.columns and cfi_col in cf_df.columns and cff_col in cf_df.columns):
        return failures

    for _, row in cf_df.iterrows():
        cfo = row.get(cfo_col, 0) or 0
        cfi = row.get(cfi_col, 0) or 0
        cff = row.get(cff_col, 0) or 0
        calc_net = cfo + cfi + cff

        if net_col and pd.notna(row.get(net_col)):
            rep_net = row.get(net_col)
            if abs(rep_net - calc_net) > 10.0:
                failures.append(
                    create_failure_record(
                        rule_id="DQ-09",
                        company_id=row.get("company_id"),
                        year=row.get("year"),
                        field="net_cash_flow",
                        issue=f"Cash flow mismatch: reported {rep_net} vs calculated (CFO+CFI+CFF = {calc_net:.2f})",
                        severity="WARNING",
                        source_file=source_file,
                        original_value=rep_net,
                        corrected_value=round(calc_net, 2),
                        action="FLAGGED",
                    )
                )
    return failures


def check_dq_10_fixed_assets_non_negative(
    bs_df: pd.DataFrame, source_file: str = "balancesheet.xlsx"
) -> list[dict[str, Any]]:
    """DQ-10: fixed_assets >= 0."""
    failures = []
    fa_col = "fixed_assets" if "fixed_assets" in bs_df.columns else None
    if not fa_col:
        return failures

    for _, row in bs_df.iterrows():
        fa = row.get(fa_col)
        if pd.notna(fa) and fa < 0:
            failures.append(
                create_failure_record(
                    rule_id="DQ-10",
                    company_id=row.get("company_id"),
                    year=row.get("year"),
                    field=fa_col,
                    issue=f"Negative fixed assets ({fa}) in balance sheet",
                    severity="WARNING",
                    source_file=source_file,
                    original_value=fa,
                    action="FLAGGED",
                )
            )
    return failures


def check_dq_11_tax_percentage_range(
    pnl_df: pd.DataFrame, source_file: str = "profitandloss.xlsx"
) -> list[dict[str, Any]]:
    """DQ-11: 0 <= tax_percentage <= 60."""
    failures = []
    tax_col = "tax_pct" if "tax_pct" in pnl_df.columns else ("tax_percentage" if "tax_percentage" in pnl_df.columns else None)
    if not tax_col:
        return failures

    for _, row in pnl_df.iterrows():
        tax = row.get(tax_col)
        if pd.notna(tax) and (tax < 0 or tax > 60):
            failures.append(
                create_failure_record(
                    rule_id="DQ-11",
                    company_id=row.get("company_id"),
                    year=row.get("year"),
                    field=tax_col,
                    issue=f"Tax percentage out of expected range [0, 60]: {tax}%",
                    severity="WARNING",
                    source_file=source_file,
                    original_value=tax,
                    action="FLAGGED",
                )
            )
    return failures


def check_dq_12_dividend_payout(
    pnl_df: pd.DataFrame, source_file: str = "profitandloss.xlsx"
) -> list[dict[str, Any]]:
    """DQ-12: dividend_payout <= 200."""
    failures = []
    div_col = "dividend_payout_pct" if "dividend_payout_pct" in pnl_df.columns else ("dividend_payout" if "dividend_payout" in pnl_df.columns else None)
    if not div_col:
        return failures

    for _, row in pnl_df.iterrows():
        div = row.get(div_col)
        if pd.notna(div) and div > 200:
            failures.append(
                create_failure_record(
                    rule_id="DQ-12",
                    company_id=row.get("company_id"),
                    year=row.get("year"),
                    field=div_col,
                    issue=f"Dividend payout ratio exceeds threshold 200%: {div}%",
                    severity="WARNING",
                    source_file=source_file,
                    original_value=div,
                    action="FLAGGED",
                )
            )
    return failures


def check_dq_13_annual_report_url(
    docs_df: pd.DataFrame, source_file: str = "documents.xlsx"
) -> list[dict[str, Any]]:
    """DQ-13: Annual report URL validation (syntactic check without dropping records on 404)."""
    failures = []
    url_col = "Annual_Report" if "Annual_Report" in docs_df.columns else ("url" if "url" in docs_df.columns else None)
    if not url_col:
        return failures

    for _, row in docs_df.iterrows():
        url = str(row.get(url_col, ""))
        if pd.isna(row.get(url_col)) or not url or url.strip() == "":
            continue
        if not (url.startswith("http://") or url.startswith("https://") or url.startswith("www.")):
            failures.append(
                create_failure_record(
                    rule_id="DQ-13",
                    company_id=row.get("company_id"),
                    year=row.get("Year") or row.get("year"),
                    field=url_col,
                    issue=f"Malformed Annual Report URL format: '{url}'",
                    severity="INFO",
                    source_file=source_file,
                    original_value=url,
                    action="FLAGGED_URL_SYNTAX",
                )
            )
    return failures


def check_dq_14_eps_sign_consistency(
    pnl_df: pd.DataFrame, source_file: str = "profitandloss.xlsx"
) -> list[dict[str, Any]]:
    """DQ-14: EPS sign consistency with Net Profit."""
    failures = []
    np_col = "net_profit" if "net_profit" in pnl_df.columns else None
    eps_col = "eps_in_rs" if "eps_in_rs" in pnl_df.columns else ("earnings_per_share" if "earnings_per_share" in pnl_df.columns else None)

    if not np_col or not eps_col:
        return failures

    for _, row in pnl_df.iterrows():
        np_val = row.get(np_col)
        eps_val = row.get(eps_col)

        if pd.notna(np_val) and pd.notna(eps_val):
            if (np_val > 0 and eps_val < 0) or (np_val < 0 and eps_val > 0):
                failures.append(
                    create_failure_record(
                        rule_id="DQ-14",
                        company_id=row.get("company_id"),
                        year=row.get("year"),
                        field=eps_col,
                        issue=f"EPS sign mismatch with Net Profit: Net Profit={np_val}, EPS={eps_val}",
                        severity="WARNING",
                        source_file=source_file,
                        original_value=eps_val,
                        action="FLAGGED",
                    )
                )
    return failures


def check_dq_15_assets_liabilities_info(
    bs_df: pd.DataFrame, source_file: str = "balancesheet.xlsx"
) -> list[dict[str, Any]]:
    """DQ-15: Assets/liabilities balance informational check."""
    failures = []
    if "total_assets" not in bs_df.columns or "total_liabilities" not in bs_df.columns:
        return failures

    for _, row in bs_df.iterrows():
        ta = row.get("total_assets")
        tl = row.get("total_liabilities")
        if pd.notna(ta) and pd.notna(tl) and ta != tl:
            failures.append(
                create_failure_record(
                    rule_id="DQ-15",
                    company_id=row.get("company_id"),
                    year=row.get("year"),
                    field="total_assets,total_liabilities",
                    issue=f"Informational: Assets ({ta}) != Liabilities ({tl}), delta = {abs(ta - tl):.2f}",
                    severity="INFO",
                    source_file=source_file,
                    original_value=f"TA={ta}, TL={tl}",
                    action="INFO_ONLY",
                )
            )
    return failures


def check_dq_16_company_coverage(
    datasets: dict[str, pd.DataFrame]
) -> list[dict[str, Any]]:
    """DQ-16: Minimum 5 years of P&L, BS, and CF coverage per company."""
    failures = []
    companies_df = datasets.get("companies")
    if companies_df is None:
        return failures

    cid_col = "id" if "id" in companies_df.columns else "company_id"
    all_companies = set(companies_df[cid_col].dropna())

    financial_tables = ["profitandloss", "balancesheet", "cashflow"]

    for table_name in financial_tables:
        df = datasets.get(table_name)
        if df is None or "company_id" not in df.columns or "year" not in df.columns:
            continue

        valid_df = df[df["year"] != "PARSE_ERROR"]
        counts = valid_df.groupby("company_id")["year"].nunique()

        for cid in sorted(all_companies):
            yrs_count = counts.get(cid, 0)
            if yrs_count < 5:
                failures.append(
                    create_failure_record(
                        rule_id="DQ-16",
                        company_id=cid,
                        year=None,
                        field="year_coverage",
                        issue=f"Company '{cid}' has only {yrs_count} years of data in {table_name} (minimum required: 5)",
                        severity="WARNING",
                        source_file=f"{table_name}.xlsx",
                        original_value=yrs_count,
                        action="FLAGGED_LOW_COVERAGE",
                    )
                )
    return failures


def validate_all_datasets(
    datasets: dict[str, pd.DataFrame]
) -> list[dict[str, Any]]:
    """Run all DQ rules across core and supporting datasets."""
    all_failures: list[dict[str, Any]] = []

    companies_df = datasets.get("companies", pd.DataFrame())

    # DQ-01
    if not companies_df.empty:
        all_failures.extend(check_dq_01_pk_uniqueness(companies_df))

    # DQ-02 & DQ-03 & DQ-07 & DQ-08 across all tables
    table_file_map = {
        "companies": "companies.xlsx",
        "profitandloss": "profitandloss.xlsx",
        "balancesheet": "balancesheet.xlsx",
        "cashflow": "cashflow.xlsx",
        "analysis": "analysis.xlsx",
        "documents": "documents.xlsx",
        "prosandcons": "prosandcons.xlsx",
        "sectors": "sectors.xlsx",
        "stock_prices": "stock_prices.xlsx",
        "market_cap": "market_cap.xlsx",
        "financial_ratios": "financial_ratios.xlsx",
        "peer_groups": "peer_groups.xlsx",
    }

    for name, df in datasets.items():
        if df is None or df.empty:
            continue
        src = table_file_map.get(name, f"{name}.xlsx")

        # DQ-08
        all_failures.extend(check_dq_08_ticker_format(df, name, src))

        # DQ-07
        all_failures.extend(check_dq_07_normalized_year(df, name, src))

        # DQ-03 (except companies table itself)
        if name != "companies" and not companies_df.empty:
            all_failures.extend(
                check_dq_03_foreign_key_integrity(df, companies_df, name, src)
            )

    # Specific DQ rules
    if "balancesheet" in datasets:
        all_failures.extend(check_dq_04_balance_sheet_balance(datasets["balancesheet"]))
        all_failures.extend(check_dq_10_fixed_assets_non_negative(datasets["balancesheet"]))
        all_failures.extend(check_dq_15_assets_liabilities_info(datasets["balancesheet"]))

    if "profitandloss" in datasets:
        all_failures.extend(check_dq_05_opm_cross_check(datasets["profitandloss"]))
        if not companies_df.empty:
            all_failures.extend(check_dq_06_positive_sales(datasets["profitandloss"], companies_df))
        all_failures.extend(check_dq_11_tax_percentage_range(datasets["profitandloss"]))
        all_failures.extend(check_dq_12_dividend_payout(datasets["profitandloss"]))
        all_failures.extend(check_dq_14_eps_sign_consistency(datasets["profitandloss"]))

    if "cashflow" in datasets:
        all_failures.extend(check_dq_09_cash_flow_reconciliation(datasets["cashflow"]))

    if "documents" in datasets:
        all_failures.extend(check_dq_13_annual_report_url(datasets["documents"]))

    # DQ-16
    all_failures.extend(check_dq_16_company_coverage(datasets))

    return all_failures