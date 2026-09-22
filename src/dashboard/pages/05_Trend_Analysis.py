"""
Page 05 - Trend Analysis & Multi-Year Growth
Nifty 100 Financial Intelligence Platform
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.dashboard.utils.charts import create_multi_metric_trend_chart
from src.dashboard.utils.db import load_companies_master, load_company_financials, load_table

st.title("📊 Multi-Year Trend Analysis")

companies_df = load_companies_master()
if companies_df.empty:
    st.stop()

tickers = companies_df["id"].tolist()
selected_ticker = st.sidebar.selectbox("Select Company Ticker", tickers)

fin_data = load_company_financials(selected_ticker)
pnl = fin_data["pnl"]
ratios = fin_data["ratios"]

st.subheader(f"Multi-Year Financial Trends: {selected_ticker}")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Sales & Net Profit Trajectory (Cr)")
    fig1 = create_multi_metric_trend_chart(pnl, selected_ticker, [("sales", "Sales"), ("net_profit", "Net Profit"), ("operating_profit", "Operating Profit")])
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Margin & Return Trends (%)")
    fig2 = create_multi_metric_trend_chart(ratios, selected_ticker, [("return_on_equity_pct", "ROE %"), ("roce_pct", "ROCE %"), ("operating_profit_margin_pct", "OPM %")])
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")
st.subheader("Parsed CAGR Summary (from Analysis Dataset)")
parsed_df = load_table("analysis_parsed")
if not parsed_df.empty:
    c_parsed = parsed_df[parsed_df["company_id"] == selected_ticker]
    if not c_parsed.empty:
        st.dataframe(c_parsed[["metric", "period", "value_pct", "raw_text"]], use_container_width=True)
    else:
        st.info("No parsed CAGR records for this company.")
else:
    st.info("Analysis CAGR dataset not populated.")
