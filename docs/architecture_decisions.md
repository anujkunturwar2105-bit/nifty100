# Architectural Decision Record (ADR) — Sprint 1

## ADR-01: Retention of All 12 Logical Datasets in SQLite Storage

### Status
Approved & Implemented.

### Context
The project specification enumerated 12 core and supporting Excel workbooks while making a passing reference to 10 SQLite tables in a separate section. Silently dropping two datasets (`prosandcons`, `peer_groups`, `analysis`, or `documents`) would cause permanent loss of downstream financial intelligence capability.

### Decision
We retain **all 12 logical tables** in the SQLite database (`data/nifty100.db`):
1. `companies`
2. `profitandloss`
3. `balancesheet`
4. `cashflow`
5. `analysis`
6. `documents`
7. `prosandcons`
8. `sectors`
9. `stock_prices`
10. `market_cap`
11. `financial_ratios`
12. `peer_groups`

---

## ADR-02: Deterministic Annual Record Deduplication Policy

### Status
Approved & Implemented.

### Context
Raw source files (e.g. `financial_ratios.xlsx`, `profitandloss.xlsx`) contain duplicate records sharing the same primary/unique key `(company_id, year)`. Blind deletion or random selection risks dropping populated financial values.

### Decision
We implement a multi-attribute deterministic scoring function:
1. **Primary Score**: Total count of non-null fields in the row.
2. **Secondary Score**: Total count of non-zero numeric values.
3. **Tertiary Score**: Original source row index (preserves first occurrence).

All rejected duplicate records are logged into `output/validation_failures.csv` with action `REJECTED_DUPLICATE` and summarized in `output/load_audit.csv`.

---

## ADR-03: Foreign Key Enforcement & Referential Integrity

### Status
Approved & Implemented.

### Context
SQLite disables foreign key constraint checking by default.

### Decision
All DDL table definitions declare explicit foreign keys referencing `companies(id)`. Every database connection enforces `PRAGMA foreign_keys = ON;` and every ETL run finishes with `PRAGMA foreign_key_check;` to guarantee 0 referential integrity violations.
