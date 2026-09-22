"""
FastAPI REST Application
Nifty 100 Financial Intelligence Platform

Exposes 16 RESTful endpoints for company profiles, financial statements, ratios,
tearsheet PDFs, investment screener, sector analytics, peer comparison, and health checks.
"""

import sqlite3
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import FileResponse, JSONResponse

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analytics.screener.engine import run_screener
from src.config import DB_PATH, TEARSHEETS_DIR
from src.reports.tearsheet import generate_company_tearsheet

app = FastAPI(
    title="Nifty 100 Financial Intelligence API",
    version="1.0.0",
    description="Institutional-grade Financial Intelligence API for the Nifty 100 universe."
)


def get_db_connection():
    """Get SQLite database connection with error handling."""
    if not DB_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SQLite Data Warehouse unavailable. Run ETL pipeline first."
        )
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to connect to SQLite Data Warehouse."
        )


@app.get("/api/v1/health", summary="16. Health Check Endpoint")
def health_check():
    """Health check endpoint returning database and system status."""
    db_ok = DB_PATH.exists()
    return {
        "status": "HEALTHY" if db_ok else "UNHEALTHY",
        "database": str(DB_PATH),
        "database_exists": db_ok,
        "version": "1.0.0"
    }


@app.get("/api/v1/companies", summary="1. List All Companies")
def list_companies():
    """List all companies in the Nifty 100 analytical universe."""
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM companies ORDER BY id ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/v1/companies/{ticker}", summary="2. Get Company Profile")
def get_company_profile(ticker: str):
    """Get company profile and metadata by ticker."""
    ticker_clean = ticker.strip().upper()
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM companies WHERE id = ?", (ticker_clean,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Company '{ticker_clean}' not found.")
    return dict(row)


@app.get("/api/v1/companies/{ticker}/pl", summary="3. Get Profit & Loss Statement")
def get_pnl(ticker: str):
    """Get historical Profit & Loss statement for a company."""
    ticker_clean = ticker.strip().upper()
    conn = get_db_connection()
    # Check ticker validity
    comp = conn.execute("SELECT id FROM companies WHERE id = ?", (ticker_clean,)).fetchone()
    if not comp:
        conn.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Company '{ticker_clean}' not found.")

    rows = conn.execute("SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year ASC", (ticker_clean,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/v1/companies/{ticker}/bs", summary="4. Get Balance Sheet")
def get_balance_sheet(ticker: str):
    """Get historical Balance Sheet for a company."""
    ticker_clean = ticker.strip().upper()
    conn = get_db_connection()
    comp = conn.execute("SELECT id FROM companies WHERE id = ?", (ticker_clean,)).fetchone()
    if not comp:
        conn.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Company '{ticker_clean}' not found.")

    rows = conn.execute("SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year ASC", (ticker_clean,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/v1/companies/{ticker}/cashflow", summary="5. Get Cash Flow Statement")
def get_cash_flow(ticker: str):
    """Get historical Cash Flow statement for a company."""
    ticker_clean = ticker.strip().upper()
    conn = get_db_connection()
    comp = conn.execute("SELECT id FROM companies WHERE id = ?", (ticker_clean,)).fetchone()
    if not comp:
        conn.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Company '{ticker_clean}' not found.")

    rows = conn.execute("SELECT * FROM cashflow WHERE company_id = ? ORDER BY year ASC", (ticker_clean,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/v1/companies/{ticker}/ratios", summary="6. Get Financial KPIs & Ratios")
def get_company_ratios(ticker: str):
    """Get 50+ calculated financial KPIs and ratios for a company."""
    ticker_clean = ticker.strip().upper()
    conn = get_db_connection()
    comp = conn.execute("SELECT id FROM companies WHERE id = ?", (ticker_clean,)).fetchone()
    if not comp:
        conn.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Company '{ticker_clean}' not found.")

    rows = conn.execute("SELECT * FROM financial_ratios_calc WHERE company_id = ? ORDER BY year ASC", (ticker_clean,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/v1/companies/{ticker}/tearsheet", summary="7. Download PDF Tearsheet")
def download_tearsheet(ticker: str):
    """Download PDF financial tearsheet for a company."""
    ticker_clean = ticker.strip().upper()
    pdf_path = TEARSHEETS_DIR / f"{ticker_clean}_Tearsheet.pdf"
    if not pdf_path.exists():
        pdf_path = generate_company_tearsheet(ticker_clean)

    if not pdf_path or not pdf_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tearsheet for '{ticker_clean}' could not be generated.")

    return FileResponse(path=str(pdf_path), filename=f"{ticker_clean}_Tearsheet.pdf", media_type="application/pdf")


@app.get("/api/v1/screener", summary="8. Investment Screener Endpoint")
def screener_endpoint(
    preset: str | None = Query(None, description="Preset name: QUALITY, VALUE, GROWTH, DIVIDEND, MOMENTUM, DEBT_FREE"),
    min_roe: float | None = Query(None, description="Minimum ROE %"),
    max_debt_equity: float | None = Query(None, description="Maximum Debt-to-Equity ratio")
):
    """Screen companies based on preset or custom KPI criteria."""
    custom = {}
    if min_roe is not None:
        custom["roe_min"] = min_roe
    if max_debt_equity is not None:
        custom["debt_to_equity_max"] = max_debt_equity

    res_df = run_screener(preset=preset, custom_filters=custom)
    return res_df.to_dict(orient="records")


@app.get("/api/v1/sectors", summary="9. Get All Sector Medians")
def list_sectors():
    """Get aggregated median metrics across 11 broad sectors."""
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM sector_metrics ORDER BY company_count DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/v1/sectors/{sector}/companies", summary="10. Get Sector Constituent Companies")
def get_sector_companies(sector: str):
    """Get constituent companies for a specific sector."""
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM sectors WHERE broad_sector LIKE ? ORDER BY company_id ASC", (f"%{sector}%",)).fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sector '{sector}' not found.")
    return [dict(r) for r in rows]


@app.get("/api/v1/peers/{group_name}", summary="11. Get Peer Group Constituents")
def get_peer_group(group_name: str):
    """Get constituents of a peer group."""
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM peer_groups WHERE peer_group_name LIKE ?", (f"%{group_name}%",)).fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Peer group '{group_name}' not found.")
    return [dict(r) for r in rows]


@app.get("/api/v1/companies/{ticker}/peers/compare", summary="12. Peer Comparison Metrics")
def compare_company_peers(ticker: str):
    """Get peer group percentile rankings for radar chart plotting."""
    ticker_clean = ticker.strip().upper()
    conn = get_db_connection()
    comp = conn.execute("SELECT id FROM companies WHERE id = ?", (ticker_clean,)).fetchone()
    if not comp:
        conn.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Company '{ticker_clean}' not found.")

    rows = conn.execute("SELECT * FROM peer_percentiles WHERE company_id = ?", (ticker_clean,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/v1/market-cap/{ticker}", summary="13. Get Market Cap Data")
def get_market_cap(ticker: str):
    """Get market cap and valuation metrics for a company."""
    ticker_clean = ticker.strip().upper()
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM market_cap WHERE company_id = ? ORDER BY year ASC", (ticker_clean,)).fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Market cap data for '{ticker_clean}' not found.")
    return [dict(r) for r in rows]


@app.get("/api/v1/portfolio/stats", summary="14. Portfolio Universe Stats")
def get_portfolio_stats():
    """Get overall Nifty 100 portfolio universe statistics."""
    conn = get_db_connection()
    n_companies = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    avg_score = conn.execute("SELECT AVG(score) FROM health_scores").fetchone()[0]
    conn.close()
    return {
        "total_companies": n_companies,
        "average_health_score": round(float(avg_score), 1) if avg_score else 0.0,
        "dataset_universe": "Nifty 100 Analytical Universe (92 Companies)"
    }


@app.get("/api/v1/companies/{ticker}/documents", summary="15. Get Company Annual Reports")
def get_company_documents(ticker: str):
    """Get annual report document links for a company."""
    ticker_clean = ticker.strip().upper()
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM documents WHERE company_id = ? ORDER BY year DESC", (ticker_clean,)).fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No annual report documents found for '{ticker_clean}'.")
    return [dict(r) for r in rows]
