"""
Unit Tests for Health Score, Sector Analytics, Peer Engine, Cashflow, Screener, Clustering
"""

import pytest

from src.analytics.cashflow_kpis import classify_capital_allocation
from src.analytics.clustering import run_kmeans_clustering
from src.analytics.health_score import compute_health_scores
from src.analytics.peer import compute_peer_percentiles
from src.analytics.screener.engine import run_screener
from src.analytics.sector import compute_sector_metrics
from src.analytics.valuation import detect_sector_outliers


def test_health_score_execution():
    scores = compute_health_scores()
    assert not scores.empty
    assert "score" in scores.columns
    assert "band" in scores.columns
    assert scores["score"].between(0, 100).all()


def test_sector_metrics_execution():
    sec_df = compute_sector_metrics()
    assert not sec_df.empty
    assert "broad_sector" in sec_df.columns
    assert "company_count" in sec_df.columns


def test_peer_percentiles_execution():
    peer_df = compute_peer_percentiles()
    assert not peer_df.empty
    assert "percentile" in peer_df.columns
    assert peer_df["percentile"].between(0, 100).all()


def test_cashflow_kpis_execution():
    ca_df = classify_capital_allocation()
    assert not ca_df.empty
    assert "classification" in ca_df.columns
    assert "pattern" in ca_df.columns


def test_clustering_execution():
    cl_df = run_kmeans_clustering()
    assert not cl_df.empty
    assert "cluster_label" in cl_df.columns
    assert len(cl_df["cluster_label"].unique()) <= 5


def test_outlier_detection_execution():
    out_df = detect_sector_outliers()
    assert "z_score" in out_df.columns if not out_df.empty else True


def test_screener_execution():
    res_df = run_screener(preset="QUALITY")
    assert not res_df.empty
    assert "company_id" in res_df.columns
