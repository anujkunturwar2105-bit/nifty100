"""
Page 04 - Peer Group Comparison & Percentile Radar
Nifty 100 Financial Intelligence Platform
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.dashboard.utils.charts import create_radar_chart
from src.dashboard.utils.db import load_table

st.title("🎯 Peer Group Comparison & Radar Analytics")

peer_df = load_table("peer_groups")
percentiles_df = load_table("peer_percentiles")
ratios_df = load_table("financial_ratios_calc")

if peer_df.empty or percentiles_df.empty:
    st.warning("Peer data unavailable. Run analytics engine.")
    st.stop()

groups = sorted(peer_df["peer_group_name"].unique().tolist())
selected_group = st.sidebar.selectbox("Select Peer Group", groups)

group_peers = peer_df[peer_df["peer_group_name"] == selected_group]
peer_cids = group_peers["company_id"].tolist()

selected_company = st.sidebar.selectbox("Select Benchmark Company", peer_cids)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader(f"Radar Percentile Profile: {selected_company}")
    fig_radar = create_radar_chart(percentiles_df, selected_company, selected_group)
    st.plotly_chart(fig_radar, use_container_width=True)

with col2:
    st.subheader(f"Peer Group Metric Percentiles")
    pct_filtered = percentiles_df[percentiles_df["peer_group_name"] == selected_group]
    pivot = pct_filtered.pivot(index="company_id", columns="metric", values="percentile").reset_index()
    st.dataframe(pivot, use_container_width=True)

st.markdown("---")
st.subheader("Side-by-Side Financial Ratios")
if not ratios_df.empty:
    latest = ratios_df.sort_values(by=["company_id", "year"]).groupby("company_id").last().reset_index()
    peer_ratios = latest[latest["company_id"].isin(peer_cids)]
    cols_to_show = ["company_id", "year", "return_on_equity_pct", "roce_pct", "operating_profit_margin_pct", "debt_to_equity", "free_cash_flow_cr"]
    disp = peer_ratios[[c for c in cols_to_show if c in peer_ratios.columns]]
    st.dataframe(disp, use_container_width=True)
