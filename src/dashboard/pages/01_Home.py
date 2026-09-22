"""
Page 01 - Home & Universe Overview
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

st.title("🌐 Nifty 100 Universe Overview")
st.markdown("### Executive Dashboard & Universe Metrics")

companies_df = load_table("companies")
sectors_df = load_table("sectors")
health_df = load_table("health_scores")
ratios_df = load_table("financial_ratios_calc")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Companies", len(companies_df) if not companies_df.empty else 92)

with col2:
    st.metric("Broad Sectors", len(sectors_df["broad_sector"].unique()) if not sectors_df.empty else 11)

with col3:
    avg_hs = round(float(health_df["score"].mean()), 1) if not health_df.empty else "N/A"
    st.metric("Avg Health Score", f"{avg_hs} / 100")

with col4:
    ex_count = sum(1 for b in health_df["band"] if b == "EXCELLENT") if not health_df.empty else "N/A"
    st.metric("Excellent Health (>=80)", ex_count)

st.markdown("---")

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Sector Breakdown")
    if not sectors_df.empty:
        sec_counts = sectors_df["broad_sector"].value_counts().reset_index()
        sec_counts.columns = ["Sector", "Count"]
        fig_sec = px.pie(sec_counts, values="Count", names="Sector", hole=0.4, color_discrete_sequence=px.colors.qualitative.Bold)
        st.plotly_chart(fig_sec, use_container_width=True)
    else:
        st.info("Sector data loading...")

with col_b:
    st.subheader("Financial Health Band Distribution")
    if not health_df.empty:
        band_counts = health_df["band"].value_counts().reset_index()
        band_counts.columns = ["Band", "Count"]
        fig_band = px.bar(band_counts, x="Band", y="Count", color="Band", color_discrete_sequence=px.colors.sequential.Teal)
        st.plotly_chart(fig_band, use_container_width=True)
    else:
        st.info("Health score data loading...")

st.markdown("---")
st.subheader("Data Quality & Pipeline Summary")
summary_path = ROOT / "output" / "data_quality_summary.txt"
if summary_path.exists():
    with open(summary_path, "r") as f:
        st.code(f.read(), language="text")
else:
    st.info("Run `python -m src.etl.loader` to generate data quality summary.")
