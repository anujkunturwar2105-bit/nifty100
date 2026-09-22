"""
Integration Tests for FastAPI REST Endpoints
"""

import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from src.analytics.health_score import compute_health_scores
from src.analytics.sector import compute_sector_metrics
from src.api.main import app
from src.config import DB_PATH

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_analytical_tables():
    """Ensure analytical tables are populated for API tests."""
    conn = sqlite3.connect(DB_PATH)
    sec_count = conn.execute("SELECT COUNT(*) FROM sector_metrics").fetchone()[0]
    conn.close()

    if sec_count == 0:
        compute_health_scores(DB_PATH)
        compute_sector_metrics(DB_PATH)


def test_health_endpoint():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "HEALTHY"


def test_list_companies():
    res = client.get("/api/v1/companies")
    assert res.status_code == 200
    assert len(res.json()) >= 90


def test_get_company_profile():
    res = client.get("/api/v1/companies/TCS")
    assert res.status_code == 200
    assert res.json()["id"] == "TCS"

    res_404 = client.get("/api/v1/companies/UNKNOWN_TICKER_123")
    assert res_404.status_code == 404


def test_get_company_pnl():
    res = client.get("/api/v1/companies/TCS/pl")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_get_company_bs():
    res = client.get("/api/v1/companies/TCS/bs")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_get_company_cashflow():
    res = client.get("/api/v1/companies/TCS/cashflow")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_get_company_ratios():
    res = client.get("/api/v1/companies/TCS/ratios")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_screener_endpoint():
    res = client.get("/api/v1/screener?preset=QUALITY")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_sectors_endpoint():
    res = client.get("/api/v1/sectors")
    assert res.status_code == 200
    assert len(res.json()) >= 10


def test_portfolio_stats():
    res = client.get("/api/v1/portfolio/stats")
    assert res.status_code == 200
    assert "total_companies" in res.json()


def test_documents_endpoint():
    res = client.get("/api/v1/companies/TCS/documents")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
