# Deliverables Master Tracker
**Nifty 100 Financial Intelligence Platform**

| ID | Sprint | Deliverable | Original Location | Package Location | Status | Verification Method |
|---|---|---|---|---|---|---|
| **D-01** | Sprint 1 | SQLite Data Warehouse (`nifty100.db`) | `data/nifty100.db` | `PROJECT_DELIVERABLES/D-01_Database/nifty100.db` | **DONE** | SQLite schema & row count check (22 tables) |
| **D-02** | Sprint 1 | ETL Load Audit Log (`load_audit.csv`) | `output/load_audit.csv` | `PROJECT_DELIVERABLES/D-02_Load_Audit/load_audit.csv` | **DONE** | 1,063 dataset load records verified |
| **D-03** | Sprint 1 | Validation Failures (`validation_failures.csv`) | `output/validation_failures.csv` | `PROJECT_DELIVERABLES/D-03_Validation_Failures/validation_failures.csv` | **DONE** | Data quality issue tracking log verified |
| **D-04** | Sprint 1 | Exploratory SQL (`exploratory_queries.sql`) | `notebooks/exploratory_queries.sql` | `PROJECT_DELIVERABLES/D-04_Exploratory_SQL/exploratory_queries.sql` | **DONE** | SQL script syntax execution against SQLite |
| **D-05** | Sprint 2 | Financial Ratios Table (`financial_ratios`) | `data/nifty100.db → financial_ratios_calc` | `PROJECT_DELIVERABLES/D-05_Financial_Ratios/financial_ratios_summary.csv` | **DONE** | 50+ calculated financial KPIs verified |
| **D-06** | Sprint 2 | Capital Allocation (`capital_allocation.csv`) | `output/capital_allocation.csv` | `PROJECT_DELIVERABLES/D-06_Capital_Allocation/capital_allocation.csv` | **DONE** | 1,063 CFO/CFI/CFF sign pattern classifications |
| **D-07** | Sprint 3 | Screener Output (`screener_output.xlsx`) | `output/screener_output.xlsx` | `PROJECT_DELIVERABLES/D-07_Screener_Output/screener_output.xlsx` | **DONE** | Multi-tab workbook (6 presets verified) |
| **D-08** | Sprint 3 | Screener Config (`screener_config.yaml`) | `config/screener_config.yaml` | `PROJECT_DELIVERABLES/D-08_Screener_Config/screener_config.yaml` | **DONE** | YAML preset rules configuration verified |
| **D-09** | Sprint 3 | Peer Comparison (`peer_comparison.xlsx`) | `output/peer_comparison.xlsx` | `PROJECT_DELIVERABLES/D-09_Peer_Comparison/peer_comparison.xlsx` | **DONE** | Peer group percentiles & rankings matrix |
| **D-10** | Sprint 3 | 92 Radar Charts (`reports/radar_charts/`) | `reports/radar_charts/` | `PROJECT_DELIVERABLES/D-10_Radar_Charts/` | **DONE** | 92 individual company PNG radar charts verified |
| **D-11** | Sprint 4 | Streamlit Dashboard (8 Screens) | `src/dashboard/app.py` | `PROJECT_DELIVERABLES/D-11_Streamlit_Dashboard/` | **DONE** | Interactive web app verified on localhost:8501 |
| **D-12** | Sprint 4 | Valuation Summary (`valuation_summary.xlsx`) | `output/valuation_summary.xlsx` | `PROJECT_DELIVERABLES/D-12_Valuation_Summary/valuation_summary.xlsx` | **DONE** | Market cap & sector z-score outliers |
| **D-13** | Sprint 5 | Cashflow Intelligence (`cashflow_intelligence.xlsx`) | `output/cashflow_intelligence.xlsx` | `PROJECT_DELIVERABLES/D-13_Cashflow_Intelligence/cashflow_intelligence.xlsx` | **DONE** | FCF conversion & CapEx coverage analysis |
| **D-14** | Sprint 5 | Pros & Cons (`pros_cons_generated.csv`) | `output/pros_cons_generated.csv` | `PROJECT_DELIVERABLES/D-14_Pros_Cons/pros_cons_generated.csv` | **DONE** | Rule-based financial pros and cons list |
| **D-15** | Sprint 5 | Analysis Parsed (`analysis_parsed.csv`) | `output/analysis_parsed.csv` | `PROJECT_DELIVERABLES/D-15_Analysis_Parsed/analysis_parsed.csv` | **DONE** | Structured CAGR string parser output |
| **D-16** | Sprint 5 | 92 Company Tearsheets (`reports/tearsheets/`) | `reports/tearsheets/` | `PROJECT_DELIVERABLES/D-16_Company_Tearsheets/` | **DONE** | 92 ReportLab PDF company tearsheets verified |
| **D-17** | Sprint 5 | 11 Sector Reports (`reports/sector/`) | `reports/sector/` | `PROJECT_DELIVERABLES/D-17_Sector_Reports/` | **DONE** | 11 individual sector summary PDF reports |
| **D-18** | Sprint 5 | Portfolio Summary PDF (`reports/portfolio/`) | `reports/portfolio/Nifty100_Portfolio_Summary.pdf` | `PROJECT_DELIVERABLES/D-18_Portfolio_Summary/Nifty100_Portfolio_Summary.pdf` | **DONE** | Executive portfolio overview PDF verified |
| **D-19** | Sprint 6 | Cluster Labels (`cluster_labels.csv`) | `output/cluster_labels.csv` | `PROJECT_DELIVERABLES/D-19_Cluster_Labels/cluster_labels.csv` | **DONE** | KMeans 5-cluster ML assignments verified |
| **D-20** | Sprint 6 | FastAPI Server (16 Endpoints) | `src/api/main.py` | `PROJECT_DELIVERABLES/D-20_FastAPI/` | **DONE** | 16 RESTful API endpoints verified on localhost:8000 |
| **D-21** | Sprint 6 | Pytest HTML Report (`pytest_report.html`) | `reports/pytest_report.html` | `PROJECT_DELIVERABLES/D-21_Pytest_Report/pytest_report.html` | **DONE** | Automated test suite execution (73/73 passed) |
| **D-22** | Sprint 6 | Analyst Guide PDF (`docs/analyst_guide.pdf`) | `docs/analyst_guide.pdf` | `PROJECT_DELIVERABLES/D-22_Analyst_Guide/analyst_guide.pdf` | **DONE** | PDF Financial Analyst Platform Guide verified |
| **D-23** | Sprint 6 | Acceptance Checklist (`acceptance_checklist.pdf`) | `docs/acceptance_checklist.pdf` | `PROJECT_DELIVERABLES/D-23_Acceptance_Checklist/acceptance_checklist.pdf` | **DONE** | PDF Project Acceptance & Sign-off Checklist |
