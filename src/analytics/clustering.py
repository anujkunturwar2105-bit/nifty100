"""
Machine Learning Clustering Engine
Nifty 100 Financial Intelligence Platform

Applies KMeans clustering (5 clusters) using StandardScaler on financial features:
- ROE (%)
- D/E Ratio
- Operating Profit Margin (%)
- Net Profit Margin (%)
- Free Cash Flow (Cr)

Saves output to `cluster_labels.csv`, `cluster_profiles.csv`, and SQLite `clusters` table.
"""

import sqlite3
import sys
from pathlib import Path

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analytics.ratios import calculate_company_ratios
from src.config import DB_PATH, OUTPUT_DIR, PROCESSED_DATA_DIR


def run_kmeans_clustering(db_path: Path = DB_PATH, n_clusters: int = 5) -> pd.DataFrame:
    """Run KMeans clustering across available analytical companies."""
    ratios_df = calculate_company_ratios(db_path)
    if ratios_df.empty:
        return pd.DataFrame()

    latest = ratios_df.sort_values(by=["company_id", "year"]).groupby("company_id").last().reset_index()

    feature_cols = [
        "return_on_equity_pct",
        "debt_to_equity",
        "operating_profit_margin_pct",
        "net_profit_margin_pct",
        "free_cash_flow_cr",
    ]

    # Fill NaNs with column median
    cluster_data = latest[["company_id"] + feature_cols].copy()
    for col in feature_cols:
        med = cluster_data[col].median()
        cluster_data[col] = cluster_data[col].fillna(med if pd.notna(med) else 0.0)

    X = cluster_data[feature_cols].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X_scaled)

    cluster_data["cluster_label"] = cluster_labels

    # Descriptive names for clusters
    cluster_names = {
        0: "High Return Compounders",
        1: "Capital Intensive & High Leverage",
        2: "Stable Cash Generators",
        3: "Moderate Performers",
        4: "Low Margin / Turnaround",
    }
    cluster_data["cluster_name"] = cluster_data["cluster_label"].map(cluster_names)

    # Cluster Profiles (Centroids & Summaries)
    profiles = cluster_data.groupby(["cluster_label", "cluster_name"])[feature_cols].agg(["mean", "median", "count"]).reset_index()

    # Save output files
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    labels_df = cluster_data[["company_id", "cluster_label", "cluster_name"] + feature_cols]
    labels_df.to_csv(OUTPUT_DIR / "cluster_labels.csv", index=False)
    labels_df.to_csv(PROCESSED_DATA_DIR / "cluster_labels.csv", index=False)

    profiles.to_csv(OUTPUT_DIR / "cluster_profiles.csv", index=False)
    profiles.to_csv(PROCESSED_DATA_DIR / "cluster_profiles.csv", index=False)

    # Save to SQLite
    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM clusters;")
    db_labels = cluster_data[["company_id", "cluster_label", "cluster_name"]]
    db_labels.to_sql("clusters", conn, if_exists="append", index=False)
    conn.close()

    print(f"KMeans clustering complete: {len(labels_df)} companies assigned to {n_clusters} clusters.")
    return labels_df


if __name__ == "__main__":
    run_kmeans_clustering()
