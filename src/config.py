"""
Configuration Module for Nifty 100 Financial Intelligence Platform
Centralizes path definitions, environment settings, and database configurations.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Dynamic Project Root Detection
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Load environment variables if .env exists
ENV_PATH = PROJECT_ROOT / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)

# Path Definitions
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
SUPPORTING_DATA_DIR = DATA_DIR / "supporting"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DB_PATH = DATA_DIR / "nifty100.db"

CONFIG_DIR = PROJECT_ROOT / "config"
OUTPUT_DIR = PROJECT_ROOT / "output"
REPORTS_DIR = PROJECT_ROOT / "reports"
TEARSHEETS_DIR = REPORTS_DIR / "tearsheets"
SECTOR_REPORTS_DIR = REPORTS_DIR / "sector"
PORTFOLIO_REPORTS_DIR = REPORTS_DIR / "portfolio"
RADAR_CHARTS_DIR = REPORTS_DIR / "radar_charts"

# Ensure essential output directories exist
for path in [
    DATA_DIR,
    RAW_DATA_DIR,
    SUPPORTING_DATA_DIR,
    PROCESSED_DATA_DIR,
    OUTPUT_DIR,
    REPORTS_DIR,
    TEARSHEETS_DIR,
    SECTOR_REPORTS_DIR,
    PORTFOLIO_REPORTS_DIR,
    RADAR_CHARTS_DIR,
]:
    path.mkdir(parents=True, exist_ok=True)

# Environment variables with fallbacks
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

# Core Data Files
CORE_FILES = {
    "companies": "companies.xlsx",
    "profitandloss": "profitandloss.xlsx",
    "balancesheet": "balancesheet.xlsx",
    "cashflow": "cashflow.xlsx",
    "analysis": "analysis.xlsx",
    "documents": "documents.xlsx",
    "prosandcons": "prosandcons.xlsx",
}

# Supporting Data Files
SUPPORTING_FILES = {
    "sectors": "sectors.xlsx",
    "stock_prices": "stock_prices.xlsx",
    "market_cap": "market_cap.xlsx",
    "financial_ratios": "financial_ratios.xlsx",
    "peer_groups": "peer_groups.xlsx",
}
