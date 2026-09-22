-- ============================================================
-- Nifty 100 Financial Intelligence Platform
-- Exploratory SQL Queries & Analytics
-- ============================================================

-- 1. Top 10 High ROE Companies
SELECT c.id, c.company_name, r.return_on_equity_pct, r.operating_profit_margin_pct
FROM companies c
JOIN financial_ratios_calc r ON c.id = r.company_id
WHERE r.year = '2024-03'
ORDER BY r.return_on_equity_pct DESC
LIMIT 10;

-- 2. Zero Debt Companies with Positive Free Cash Flow
SELECT c.id, c.company_name, r.debt_to_equity, r.free_cash_flow_cr
FROM companies c
JOIN financial_ratios_calc r ON c.id = r.company_id
WHERE r.year = '2024-03' AND r.debt_to_equity <= 0.05 AND r.free_cash_flow_cr > 0
ORDER BY r.free_cash_flow_cr DESC;

-- 3. Sector Median Profitability
SELECT s.broad_sector, COUNT(c.id) as company_count, AVG(r.return_on_equity_pct) as avg_roe
FROM companies c
JOIN sectors s ON c.id = s.company_id
JOIN financial_ratios_calc r ON c.id = r.company_id
WHERE r.year = '2024-03'
GROUP BY s.broad_sector
ORDER BY avg_roe DESC;
