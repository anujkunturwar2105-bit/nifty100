"""
Page 03 - Quantitative Investment Screener
Nifty 100 Financial Intelligence Platform
"""

import io
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analytics.screener.engine import load_screener_config, run_screener

st.title("🔍 Quantitative Investment Screener")

st.sidebar.header("Screener Controls")

config = load_screener_config()
presets = config.get("presets", {})
preset_options = ["None"] + list(presets.keys())

selected_preset = st.sidebar.selectbox("Choose Preset Screener", preset_options)

st.sidebar.markdown("---")
st.sidebar.subheader("Custom KPI Filters")

roe_min = st.sidebar.slider("Min ROE %", 0.0, 40.0, 10.0, step=1.0)
opm_min = st.sidebar.slider("Min OPM %", 0.0, 50.0, 10.0, step=1.0)
de_max = st.sidebar.slider("Max Debt-to-Equity", 0.0, 3.0, 1.0, step=0.1)
fcf_min = st.sidebar.number_input("Min Free Cash Flow (Cr)", value=0.0)

custom_filters = {
    "roe_min": roe_min,
    "opm_min": opm_min,
    "debt_to_equity_max": de_max,
    "fcf_min": fcf_min,
}

preset_param = selected_preset if selected_preset != "None" else None
results_df = run_screener(preset=preset_param, custom_filters=custom_filters)

if selected_preset != "None" and selected_preset in presets:
    p_info = presets[selected_preset]
    st.info(f"**{p_info.get('name')}**: {p_info.get('description')}")

st.subheader(f"Screened Results ({len(results_df)} Companies Passed)")

if not results_df.empty:
    display_cols = [
        "company_id", "company_name", "return_on_equity_pct",
        "operating_profit_margin_pct", "debt_to_equity",
        "free_cash_flow_cr", "health_score", "broad_sector"
    ]
    disp = results_df[[c for c in display_cols if c in results_df.columns]]
    st.dataframe(disp, use_container_width=True)

    # Excel / CSV Export
    csv = disp.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Results to CSV",
        data=csv,
        file_name="screener_results.csv",
        mime="text/csv"
    )
else:
    st.warning("No companies match the selected criteria. Try adjusting filter sliders.")
