-- ============================================================
-- NIFTY 100 FINANCIAL INTELLIGENCE PLATFORM
-- SQLite Schema Definition (21 Logical Tables)
-- ============================================================

PRAGMA foreign_keys = ON;

-- 1. COMPANIES (Master Table)
CREATE TABLE IF NOT EXISTS companies (
    id TEXT PRIMARY KEY,
    company_logo TEXT,
    company_name TEXT,
    chart_link TEXT,
    about_company TEXT,
    website TEXT,
    nse_profile TEXT,
    bse_profile TEXT,
    face_value REAL,
    book_value REAL,
    roce_percentage REAL,
    roe_percentage REAL
);

-- 2. PROFIT AND LOSS
CREATE TABLE IF NOT EXISTS profitandloss (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    sales REAL,
    expenses REAL,
    operating_profit REAL,
    opm_percentage REAL,
    other_income REAL,
    interest REAL,
    depreciation REAL,
    profit_before_tax REAL,
    tax_percentage REAL,
    net_profit REAL,
    eps REAL,
    dividend_payout REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id, year)
);

-- 3. BALANCE SHEET
CREATE TABLE IF NOT EXISTS balancesheet (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    equity_capital REAL,
    reserves REAL,
    borrowings REAL,
    other_liabilities REAL,
    total_liabilities REAL,
    fixed_assets REAL,
    cwip REAL,
    investments REAL,
    other_asset REAL,
    total_assets REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id, year)
);

-- 4. CASH FLOW
CREATE TABLE IF NOT EXISTS cashflow (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    operating_activity REAL,
    investing_activity REAL,
    financing_activity REAL,
    net_cash_flow REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id, year)
);

-- 5. ANALYSIS (Raw)
CREATE TABLE IF NOT EXISTS analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    compounded_sales_growth TEXT,
    compounded_profit_growth TEXT,
    stock_price_cagr TEXT,
    roe TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 6. DOCUMENTS
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year INTEGER,
    annual_report TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 7. PROS AND CONS
CREATE TABLE IF NOT EXISTS prosandcons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    pros TEXT,
    cons TEXT,
    rule TEXT,
    metric_value REAL,
    threshold REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 8. SECTORS
CREATE TABLE IF NOT EXISTS sectors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    broad_sector TEXT,
    sub_sector TEXT,
    index_weight_pct REAL,
    market_cap_category TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 9. STOCK PRICES
CREATE TABLE IF NOT EXISTS stock_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    date TEXT NOT NULL,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume REAL,
    adjusted_close REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 10. MARKET CAP
CREATE TABLE IF NOT EXISTS market_cap (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    market_cap_crore REAL,
    enterprise_value_crore REAL,
    pe_ratio REAL,
    pb_ratio REAL,
    ev_ebitda REAL,
    dividend_yield_pct REAL,
    is_simulated INTEGER DEFAULT 0,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 11. FINANCIAL RATIOS (Reference Dataset)
CREATE TABLE IF NOT EXISTS financial_ratios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    net_profit_margin_pct REAL,
    operating_profit_margin_pct REAL,
    return_on_equity_pct REAL,
    debt_to_equity REAL,
    interest_coverage REAL,
    asset_turnover REAL,
    free_cash_flow_cr REAL,
    capex_cr REAL,
    earnings_per_share REAL,
    book_value_per_share REAL,
    dividend_payout_ratio_pct REAL,
    total_debt_cr REAL,
    cash_from_operations_cr REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id, year)
);

-- 12. PEER GROUPS
CREATE TABLE IF NOT EXISTS peer_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    peer_group_name TEXT,
    company_id TEXT NOT NULL,
    is_benchmark INTEGER,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 13. PEER PERCENTILES
CREATE TABLE IF NOT EXISTS peer_percentiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    peer_group_name TEXT,
    metric TEXT NOT NULL,
    value REAL,
    percentile REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 14. HEALTH SCORES
CREATE TABLE IF NOT EXISTS health_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL UNIQUE,
    latest_year TEXT,
    score REAL,
    band TEXT,
    profitability_score REAL,
    returns_score REAL,
    leverage_score REAL,
    cashflow_score REAL,
    growth_score REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 15. SECTOR METRICS
CREATE TABLE IF NOT EXISTS sector_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    broad_sector TEXT NOT NULL UNIQUE,
    company_count INTEGER,
    median_roe REAL,
    median_roce REAL,
    median_npm REAL,
    median_opm REAL,
    median_de REAL,
    median_fcf REAL,
    median_rev_cagr REAL,
    median_pat_cagr REAL
);

-- 16. CAPITAL ALLOCATION
CREATE TABLE IF NOT EXISTS capital_allocation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    cfo_sign INTEGER,
    cfi_sign INTEGER,
    cff_sign INTEGER,
    pattern TEXT,
    classification TEXT,
    capex_intensity REAL,
    fcf_conversion REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 17. DATA QUALITY ISSUES
CREATE TABLE IF NOT EXISTS data_quality_issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id TEXT,
    company_id TEXT,
    year TEXT,
    field TEXT,
    issue TEXT,
    severity TEXT,
    source_file TEXT,
    original_value TEXT,
    corrected_value TEXT,
    action TEXT
);

-- 18. ANALYSIS PARSED
CREATE TABLE IF NOT EXISTS analysis_parsed (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    metric TEXT NOT NULL,
    period TEXT NOT NULL,
    value_pct REAL,
    raw_text TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 19. CLUSTERS
CREATE TABLE IF NOT EXISTS clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL UNIQUE,
    cluster_label INTEGER,
    cluster_name TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 20. OUTLIERS
CREATE TABLE IF NOT EXISTS outliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    broad_sector TEXT,
    metric TEXT NOT NULL,
    value REAL,
    sector_mean REAL,
    sector_std REAL,
    z_score REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 21. FINANCIAL RATIOS CALCULATED (Fast Cache Table)
CREATE TABLE IF NOT EXISTS financial_ratios_calc (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    net_profit_margin_pct REAL,
    operating_profit_margin_pct REAL,
    ebit_margin_pct REAL,
    ebitda_margin_pct REAL,
    pbt_margin_pct REAL,
    cost_to_sales_pct REAL,
    return_on_equity_pct REAL,
    roce_pct REAL,
    return_on_assets_pct REAL,
    return_on_capital_employed_pct REAL,
    croic_pct REAL,
    debt_to_equity REAL,
    interest_coverage REAL,
    debt_to_assets REAL,
    debt_to_ebitda REAL,
    equity_ratio REAL,
    financial_leverage REAL,
    total_debt_cr REAL,
    asset_turnover REAL,
    fixed_asset_turnover REAL,
    working_capital_turnover REAL,
    capital_turnover REAL,
    investment_to_assets_pct REAL,
    cwip_to_fixed_assets_pct REAL,
    cash_from_operations_cr REAL,
    free_cash_flow_cr REAL,
    capex_cr REAL,
    cfo_to_pat REAL,
    fcf_conversion_pct REAL,
    capex_intensity_pct REAL,
    cfo_to_debt REAL,
    net_cash_flow_cr REAL,
    earnings_per_share REAL,
    book_value_per_share REAL,
    dividend_payout_ratio_pct REAL,
    fcf_per_share REAL,
    cfo_per_share REAL,
    pe_ratio REAL,
    pb_ratio REAL,
    fcf_yield_pct REAL,
    sales_cr REAL,
    expenses_cr REAL,
    operating_profit_cr REAL,
    other_income_cr REAL,
    interest_cr REAL,
    depreciation_cr REAL,
    pbt_cr REAL,
    net_profit_cr REAL,
    net_worth_cr REAL,
    total_assets_cr REAL,
    total_liabilities_cr REAL,
    fixed_assets_cr REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id, year)
);

-- Indexes for query performance
CREATE INDEX IF NOT EXISTS idx_pnl_cid_yr ON profitandloss(company_id, year);
CREATE INDEX IF NOT EXISTS idx_bs_cid_yr ON balancesheet(company_id, year);
CREATE INDEX IF NOT EXISTS idx_cf_cid_yr ON cashflow(company_id, year);
CREATE INDEX IF NOT EXISTS idx_ratios_cid_yr ON financial_ratios(company_id, year);
CREATE INDEX IF NOT EXISTS idx_ratios_calc_cid_yr ON financial_ratios_calc(company_id, year);
CREATE INDEX IF NOT EXISTS idx_stock_prices_cid_date ON stock_prices(company_id, date);
