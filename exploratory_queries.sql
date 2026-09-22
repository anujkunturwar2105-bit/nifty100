-- ============================================================
-- NIFTY 100 FINANCIAL INTELLIGENCE PLATFORM
-- Exploratory SQL Queries (Sprint 1)
-- ============================================================

-- 1. Total companies in master table
SELECT COUNT(*) AS total_companies FROM companies;

-- 2. Total rows per table across all 12 tables
SELECT 'companies' AS table_name, COUNT(*) AS row_count FROM companies
UNION ALL SELECT 'profitandloss', COUNT(*) FROM profitandloss
UNION ALL SELECT 'balancesheet', COUNT(*) FROM balancesheet
UNION ALL SELECT 'cashflow', COUNT(*) FROM cashflow
UNION ALL SELECT 'analysis', COUNT(*) FROM analysis
UNION ALL SELECT 'documents', COUNT(*) FROM documents
UNION ALL SELECT 'prosandcons', COUNT(*) FROM prosandcons
UNION ALL SELECT 'sectors', COUNT(*) FROM sectors
UNION ALL SELECT 'stock_prices', COUNT(*) FROM stock_prices
UNION ALL SELECT 'market_cap', COUNT(*) FROM market_cap
UNION ALL SELECT 'financial_ratios', COUNT(*) FROM financial_ratios
UNION ALL SELECT 'peer_groups', COUNT(*) FROM peer_groups;

-- 3. Null count analysis in companies table
SELECT 
    COUNT(*) AS total_records,
    SUM(CASE WHEN website IS NULL THEN 1 ELSE 0 END) AS missing_website,
    SUM(CASE WHEN bse_profile IS NULL THEN 1 ELSE 0 END) AS missing_bse,
    SUM(CASE WHEN nse_profile IS NULL THEN 1 ELSE 0 END) AS missing_nse,
    SUM(CASE WHEN roce_percentage IS NULL THEN 1 ELSE 0 END) AS missing_roce,
    SUM(CASE WHEN roe_percentage IS NULL THEN 1 ELSE 0 END) AS missing_roe
FROM companies;

-- 4. Financial year distribution in P&L
SELECT year, COUNT(*) AS company_count
FROM profitandloss
GROUP BY year
ORDER BY year DESC;

-- 5. Company coverage summary (years of data per company in P&L)
SELECT company_id, COUNT(DISTINCT year) AS pnl_years_count
FROM profitandloss
GROUP BY company_id
ORDER BY pnl_years_count ASC;

-- 6. Duplicate key verification (should be 0 after deduplication)
SELECT company_id, year, COUNT(*) AS dup_count
FROM profitandloss
GROUP BY company_id, year
HAVING COUNT(*) > 1;

-- 7. Missing financial years check (companies with < 5 years of P&L)
SELECT c.id, c.company_name, COUNT(p.year) AS years_available
FROM companies c
LEFT JOIN profitandloss p ON c.id = p.company_id
GROUP BY c.id, c.company_name
HAVING COUNT(p.year) < 5;

-- 8. P&L coverage details by company
SELECT company_id, MIN(year) AS start_year, MAX(year) AS end_year, COUNT(year) AS total_years
FROM profitandloss
GROUP BY company_id
ORDER BY total_years DESC;

-- 9. Balance sheet coverage details by company
SELECT company_id, MIN(year) AS start_year, MAX(year) AS end_year, COUNT(year) AS total_years
FROM balancesheet
GROUP BY company_id
ORDER BY total_years DESC;

-- 10. Cash flow coverage details by company
SELECT company_id, MIN(year) AS start_year, MAX(year) AS end_year, COUNT(year) AS total_years
FROM cashflow
GROUP BY company_id
ORDER BY total_years DESC;

-- 11. Sector breakdown and company counts
SELECT broad_sector, COUNT(company_id) AS company_count
FROM sectors
GROUP BY broad_sector
ORDER BY company_count DESC;

-- 12. Latest financial year and metrics per company
SELECT p1.company_id, c.company_name, p1.year AS latest_year, p1.sales, p1.net_profit, p1.opm_percentage
FROM profitandloss p1
JOIN (
    SELECT company_id, MAX(year) AS max_yr
    FROM profitandloss
    GROUP BY company_id
) p2 ON p1.company_id = p2.company_id AND p1.year = p2.max_yr
JOIN companies c ON p1.company_id = c.id
ORDER BY p1.sales DESC;
