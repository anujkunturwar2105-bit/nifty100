"""
Page 06 - Sector Analytics & Cross-Sector Comparison
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

st.title("🏭 Sector Analytics & Medians")

sector_metrics_df = load_table("sector_metrics")
sectors_df = load_table("sectors")

if sector_metrics_df.empty:
    st.warning("Sector metrics unavailable. Run sector analytics engine.")
    st.stop()

st.subheader("11 Broad Sectors Aggregated Medians")
st.dataframe(sector_metrics_df, use_container_width=True)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Median ROE % by Sector")
    fig1 = px.bar(sector_metrics_df, x="broad_sector", y="median_roe", color="median_roe", color_continuous_scale="Viridis")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Median OPM % by Sector")
    fig2 = px.bar(sector_metrics_df, x="broad_sector", y="median_opm", color="median_opm", color_continuous_scale="Plasma")
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")
st.subheader("Sector Constituents Lookup")
if not sectors_df.empty:
    sel_sec = st.selectbox("Select Broad Sector", sorted(sectors_df["broad_sector"].unique().tolist()))
    constituents = sectors_df[sectors_df["broad_sector"] == sel_sec]
    st.dataframe(constituents[["company_id", "sub_sector", "index_weight_pct", "market_cap_category"]], use_container_width=True)
