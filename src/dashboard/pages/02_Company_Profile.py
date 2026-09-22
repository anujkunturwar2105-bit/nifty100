"""
Page 02 - Company Profile & Deep Dive
Nifty 100 Financial Intelligence Platform
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.dashboard.utils.db import load_companies_master, load_company_financials
from src.reports.tearsheet import generate_company_tearsheet

st.title("🏢 Company Profile & Deep Dive")

companies_df = load_companies_master()

if companies_df.empty:
    st.error("No companies found in database. Run ETL loader first.")
    st.stop()

tickers = companies_df["id"].tolist()
selected_ticker = st.sidebar.selectbox("Select Company Ticker", tickers, index=0)

data = load_company_financials(selected_ticker)

pnl = data["pnl"]
bs = data["bs"]
cf = data["cf"]
ratios = data["ratios"]
health = data["health"]
pc = data["pc"]

comp_row = companies_df[companies_df["id"] == selected_ticker].iloc[0]

st.subheader(f"{comp_row.get('company_name', selected_ticker)} ({selected_ticker})")

col1, col2, col3, col4, col5 = st.columns(5)

latest_ratios = ratios.iloc[-1].to_dict() if not ratios.empty else {}

with col1:
    st.metric("ROE %", f"{latest_ratios.get('return_on_equity_pct', 'N/A')}%" if latest_ratios.get('return_on_equity_pct') else "N/A")

with col2:
    st.metric("ROCE %", f"{latest_ratios.get('roce_pct', 'N/A')}%" if latest_ratios.get('roce_pct') else "N/A")

with col3:
    st.metric("OPM %", f"{latest_ratios.get('operating_profit_margin_pct', 'N/A')}%" if latest_ratios.get('operating_profit_margin_pct') else "N/A")

with col4:
    st.metric("D/E Ratio", f"{latest_ratios.get('debt_to_equity', 'N/A')}" if latest_ratios.get('debt_to_equity') else "N/A")

with col5:
    hs_val = health.iloc[0]["score"] if not health.empty else "N/A"
    hs_band = health.iloc[0]["band"] if not health.empty else "N/A"
    st.metric("Health Score", f"{hs_val} ({hs_band})")

st.markdown("---")

# PDF Tearsheet Download Button
pdf_path = generate_company_tearsheet(selected_ticker)
if pdf_path and pdf_path.exists():
    with open(pdf_path, "rb") as f:
        st.download_button(
            label=f"📄 Download {selected_ticker} PDF Tearsheet",
            data=f,
            file_name=f"{selected_ticker}_Tearsheet.pdf",
            mime="application/pdf"
        )

st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Profit & Loss", "Balance Sheet", "Cash Flow", "KPI Ratios", "Pros & Cons"])

with tab1:
    st.dataframe(pnl, use_container_width=True)

with tab2:
    st.dataframe(bs, use_container_width=True)

with tab3:
    st.dataframe(cf, use_container_width=True)

with tab4:
    st.dataframe(ratios, use_container_width=True)

with tab5:
    if not pc.empty:
        st.success(f"**Strengths (Pros):**\n\n{pc.iloc[0].get('pros', 'N/A')}")
        st.warning(f"**Concerns (Cons):**\n\n{pc.iloc[0].get('cons', 'N/A')}")
    else:
        st.info("No pros and cons recorded.")
