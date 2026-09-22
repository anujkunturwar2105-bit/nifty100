# FastAPI REST Endpoints Verification (16 Endpoints)

| # | HTTP Method | Endpoint | Description | Verification Status | Response Status |
|---|---|---|---|---|---|
| 1 | GET | `/health` | System Health Check | PASS | `200 OK` |
| 2 | GET | `/api/companies` | List all 92 companies | PASS | `200 OK` |
| 3 | GET | `/api/companies/{company_id}` | Company Master Metadata | PASS | `200 OK` |
| 4 | GET | `/api/ratios/{company_id}` | Pre-calculated Ratios & KPIs | PASS | `200 OK` |
| 5 | GET | `/api/financials/{company_id}` | P&L, BS, CF Statements | PASS | `200 OK` |
| 6 | GET | `/api/health-score/{company_id}`| 0-100 Score & Grade | PASS | `200 OK` |
| 7 | GET | `/api/screener` | Quantitative Screener API | PASS | `200 OK` |
| 8 | GET | `/api/peer-comparison/{company_id}`| Peer Group Ranks | PASS | `200 OK` |
| 9 | GET | `/api/capital-allocation/{company_id}`| CFO/CFI/CFF Pattern | PASS | `200 OK` |
| 10 | GET | `/api/clusters` | ML Financial Clusters | PASS | `200 OK` |
| 11 | GET | `/api/valuation/{company_id}` | Valuation & EV metrics | PASS | `200 OK` |
| 12 | GET | `/api/cashflow/{company_id}` | Cash flow & FCF metrics | PASS | `200 OK` |
| 13 | GET | `/api/pros-cons/{company_id}` | Rule-based Pros & Cons | PASS | `200 OK` |
| 14 | GET | `/api/cagr/{company_id}` | Sales & Profit CAGRs | PASS | `200 OK` |
| 15 | GET | `/api/sectors` | Sector Aggregates List | PASS | `200 OK` |
| 16 | GET | `/api/reports/download/{type}/{id}`| Report File Downloader | PASS | `200 OK` |

**Overall Verification**: All 16 API endpoints verified functioning with zero errors.
