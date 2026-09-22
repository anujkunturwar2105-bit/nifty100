"""
Page 07 - Capital Allocation & Cash Flow Intelligence
Nifty 100 Financial Intelligence Platform
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.dashboard.utils.db import load_table

st.title("💸 Capital Allocation & Cash Flow Intelligence")

alloc_df = load_table("capital_allocation")

if alloc_df.empty:
    st.warning("Capital allocation data unavailable. Run cashflow analytics engine.")
    st.stop()

st.subheader("Strategy Classification Overview")
summary = alloc_df["classification"].value_counts().reset_index()
summary.columns = ["Strategic Pattern", "Count"]

fig = px.pie(summary, values="Count", names="Strategic Pattern", hole=0.4, color_discrete_sequence=px.colors.qualitative.Dark2)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader("Company Capital Allocation Records")

tickers = sorted(alloc_df["company_id"].unique().tolist())
selected_cid = st.selectbox("Select Company Ticker", tickers)

comp_alloc = alloc_df[alloc_df["company_id"] == selected_cid]
st.dataframe(comp_alloc[["year", "pattern", "classification", "capex_intensity", "fcf_conversion"]], use_container_width=True)
