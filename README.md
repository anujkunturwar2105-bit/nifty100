# Nifty 100 Financial Intelligence Platform

A production-grade, end-to-end financial analytics platform built for the 92-company **Nifty 100 analytical universe**. The system provides ETL data ingestion, conflict quarantine auditing, an SQLite data warehouse, 50+ calculated financial KPIs, a 0–100 financial health score, quantitative stock screening, sector & peer analytics, ML clustering, an 8-page Streamlit dashboard, automated ReportLab PDF tearsheets, and 16 FastAPI REST endpoints.

---

## 🏛️ System Architecture

```
nifty100-platform/
├── config/
│   ├── screener_config.yaml    # Preset screener YAML definitions
│   ├── logging_config.yaml     # Logging configuration
│   └── .env.template           # Environment variable template
├── data/
│   ├── raw/                    # Read-only Excel datasets (7 Core files)
│   ├── supporting/             # Supporting Excel datasets (5 Supporting files)
│   ├── processed/              # Cleaned ETL CSV outputs
│   └── nifty100.db             # SQLite Data Warehouse (21 tables)
├── output/                     # Audit logs, conflicts, validation reports
├── reports/
│   ├── tearsheets/             # Generated 92 PDF company tearsheets
│   ├── sector/                 # Sector summary PDF reports
│   └── portfolio/              # Portfolio summary PDF reports
├── src/
│   ├── config.py               # Centralized configuration & pathlib Path setup
│   ├── etl/
│   │   ├── loader.py           # Idempotent ETL loader pipeline
│   │   ├── normaliser.py       # Header detection, ticker, date, conflict normalizer
│   │   ├── validator.py        # Data Quality (DQ) rule validator
│   │   └── schema.sql          # 21-table SQLite database schema definition
│   ├── analytics/
│   │   ├── ratios.py           # 50+ KPI Ratio Calculation Engine & Validation
│   │   ├── cagr.py             # Multi-year CAGR & turnaround calculation
│   │   ├── health_score.py     # 0-100 Deterministic Health Score Engine
│   │   ├── sector.py           # Sector medians & aggregations
│   │   ├── peer.py             # Peer group percentile rankings & radar data
│   │   ├── cashflow_kpis.py    # Cash flow intelligence & capital allocation
│   │   ├── clustering.py       # KMeans ML clustering (5 clusters)
│   │   ├── valuation.py        # Valuation metrics & z-score outlier detection
│   │   └── screener/
│   │       └── engine.py       # YAML preset & custom stock screener engine
│   ├── nlp/
│   │   └── pros_cons_generator.py # Quantitative rule-based pros/cons generator
│   ├── dashboard/
│   │   ├── app.py              # Main Streamlit Dashboard entry point
│   │   └── pages/              # 8 Interactive Streamlit analytics screens
│   ├── api/
│   │   └── main.py             # 16 RESTful FastAPI endpoints
│   └── reports/
│       ├── tearsheet.py        # ReportLab PDF Tearsheet generator
│       ├── sector_report.py    # Sector summary PDF generator
│       ├── portfolio_report.py # Portfolio PDF generator
│       └── screener_report.py  # Screener results PDF generator
├── tests/                      # Automated test suite (73 tests, 81% coverage)
├── Makefile                    # Standard developer commands
└── requirements.txt            # Python dependencies
```

---

## 📊 Datasets Overview

The system ingests and validates **12 datasets** without fabricating data:

### Core Datasets (`data/raw/`)
1. `companies.xlsx` - Master universe of 92 Nifty companies.
2. `profitandloss.xlsx` - Multi-year P&L statements (1,276 raw records).
3. `balancesheet.xlsx` - Multi-year Balance Sheets (1,312 raw records).
4. `cashflow.xlsx` - Multi-year Cash Flow statements (1,187 raw records).
5. `analysis.xlsx` - Partial CAGR strings (parsed into `analysis_parsed`).
6. `documents.xlsx` - Annual report document URLs (1,585 raw records).
7. `prosandcons.xlsx` - Qualitative raw pros & cons.

### Supporting Datasets (`data/supporting/`)
8. `sectors.xlsx` - 11 Broad sector & sub-sector mappings.
9. `stock_prices.xlsx` - Stock price histories.
10. `market_cap.xlsx` - Market cap & enterprise valuation ratios.
11. `financial_ratios.xlsx` - Reference dataset for KPI validation.
12. `peer_groups.xlsx` - 11 Industry peer group mappings.

---

## 🛠️ Data Quality & Conflict Auditing

- **Header Detection**: Dynamic header detection searches first 10 rows to skip title/metadata rows automatically.
- **Ratio Conflict Resolution**: Conflicting duplicate records in `financial_ratios.xlsx` are quarantined into `output/data_quality_conflicts.csv` flagged as `DATA_CONFLICT` while ratio engine recomputes authoritative values directly from raw financial statements.
- **Document Universe Status**: Tracks companies inside vs outside the Nifty 92 analytical universe in `output/document_universe_status.csv`.
- **Validation Audit**: Generates `output/load_audit.csv`, `output/validation_failures.csv`, and `output/data_quality_summary.txt`.

---

## 🚀 Quickstart & Setup Commands

### Environment Setup (Windows / Linux)

```bash
# Clone or navigate to project directory
cd c:/Users/HP/Desktop/ne100

# Install dependencies
pip install -r requirements.txt
```

---

## ⚙️ Running Execution Pipeline (Step-by-Step)

### 1. Run Data Ingestion & ETL Loader
```bash
python -m src.etl.loader
```
*Loads Excel files, normalizes dates/tickers, quarantines conflicts, and builds `data/nifty100.db`.*

### 2. Run Ratio & Analytics Engines
```bash
python -m src.analytics.ratios
python -m src.analytics.health_score
python -m src.analytics.sector
python -m src.analytics.peer
python -m src.analytics.cashflow_kpis
python -m src.analytics.clustering
python -m src.analytics.valuation
python -m src.nlp.pros_cons_generator
```
*Computes 50+ KPIs, 0–100 health scores, sector medians, peer percentiles, capital allocation patterns, ML clusters, and z-score outliers.*

### 3. Generate PDF Reports
```bash
python -m src.reports.tearsheet
python -m src.reports.sector_report
python -m src.reports.portfolio_report
python -m src.reports.screener_report
```
*Generates 91 PDF company tearsheets in `reports/tearsheets/` and summary reports.*

### 4. Launch Streamlit Financial Dashboard (8 Screens)
```bash
streamlit run src/dashboard/app.py
```
*Opens interactive 8-page financial analytics dashboard in your browser at `http://localhost:8501`.*

### 5. Launch FastAPI REST Service (16 Endpoints)
```bash
uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```
*Exposes RESTful API at `http://127.0.0.1:8000/docs`.*

---

## 🧪 Running Automated Tests & Coverage

```bash
# Run 73 unit and integration tests
pytest -q

# Run test suite with statement coverage report (>=80% target)
pytest --cov=src --cov-report=term-missing
```

---

## 🌐 FastAPI Endpoints List (16 Endpoints)

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/health` | GET | System health & DB connection check |
| `/api/v1/companies` | GET | List all 92 companies |
| `/api/v1/companies/{ticker}` | GET | Get company profile & metadata |
| `/api/v1/companies/{ticker}/pl` | GET | Multi-year Profit & Loss statement |
| `/api/v1/companies/{ticker}/bs` | GET | Multi-year Balance Sheet |
| `/api/v1/companies/{ticker}/cashflow` | GET | Multi-year Cash Flow statement |
| `/api/v1/companies/{ticker}/ratios` | GET | 50+ calculated financial KPIs |
| `/api/v1/companies/{ticker}/tearsheet` | GET | Download PDF Tearsheet |
| `/api/v1/screener` | GET | Quantitative screener (Preset / Custom) |
| `/api/v1/sectors` | GET | Aggregated sector medians |
| `/api/v1/sectors/{sector}/companies` | GET | Sector constituent companies |
| `/api/v1/peers/{group_name}` | GET | Peer group constituents |
| `/api/v1/companies/{ticker}/peers/compare` | GET | Peer percentile radar data |
| `/api/v1/market-cap/{ticker}` | GET | Valuation & market cap data |
| `/api/v1/portfolio/stats` | GET | Nifty 100 universe portfolio stats |
| `/api/v1/companies/{ticker}/documents` | GET | Annual Report URLs & universe status |

---

## 🔧 Makefile Commands

```bash
make load        # Run ETL pipeline
make ratios      # Run all ratio & analytics engines
make reports     # Generate PDF reports
make test        # Run test suite & coverage
make dashboard   # Launch Streamlit dashboard
make api         # Launch FastAPI server
make all         # Run load + ratios + reports + test
```
