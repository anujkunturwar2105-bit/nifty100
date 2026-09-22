"""
Page 08 - Annual Reports & Document Repository
Nifty 100 Financial Intelligence Platform
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.dashboard.utils.db import load_table

st.title("📑 Annual Reports & Document Repository")

docs_df = load_table("documents")

if docs_df.empty:
    st.warning("Document repository unavailable. Check documents dataset.")
    st.stop()

st.subheader("Document Repository Search")

cids = sorted(docs_df["company_id"].dropna().unique().tolist())
selected_cid = st.sidebar.selectbox("Filter by Company Ticker", ["All"] + cids)

if selected_cid != "All":
    filtered_docs = docs_df[docs_df["company_id"] == selected_cid]
else:
    filtered_docs = docs_df

st.dataframe(filtered_docs[["company_id", "year", "annual_report"]], use_container_width=True)

st.markdown("---")
st.subheader("Document Universe Coverage Status")
universe_path = ROOT / "output" / "document_universe_status.csv"
if universe_path.exists():
    univ_df = pd.read_csv(universe_path)
    st.dataframe(univ_df, use_container_width=True)
else:
    st.info("Universe status report file not generated.")
