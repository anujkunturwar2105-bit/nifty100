"""
Main Entry Point - Streamlit Financial Analytics Platform
Nifty 100 Financial Intelligence Platform
"""

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Page configuration
st.set_page_config(
    page_title="Nifty 100 Financial Intelligence Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.title("📈 Nifty 100 Intelligence")
st.sidebar.markdown("---")
st.sidebar.info("Select a page from the sidebar navigation above to explore analytics.")

# Main landing intro if executed directly
st.title("Nifty 100 Financial Intelligence Platform")
st.markdown("### Production-Grade Financial Analytics & Quantitative Screening")
st.markdown("""
Welcome to the **Nifty 100 Financial Intelligence Platform**. This application provides institutional-grade analytical tools for analyzing the 92-company Nifty 100 universe:

- **50+ Financial KPIs** calculated directly from authoritative raw financial statements.
- **0–100 Financial Health Score** evaluating profitability, returns, leverage, cash flow, and growth.
- **Preset & Custom Screener** for finding Quality, Value, Growth, and Dividend compounders.
- **Peer Comparison & Radar Charts** with sector percentile rankings.
- **Cash Flow Intelligence & Capital Allocation** classifying organic expansion, debt funding, and distress.
- **Annual Document Repository** linking annual reports and universe status.
- **ReportLab PDF Tearsheets & FastAPI REST API integration.**
""")

st.markdown("---")
st.success("Platform initialization complete. All SQLite datasets, ratio engines, and reports are fully loaded.")
