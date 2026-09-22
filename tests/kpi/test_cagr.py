"""
Unit Tests for CAGR Calculations
"""

import pytest

from src.analytics.cagr import calculate_cagr, calculate_series_cagr


def test_calculate_cagr_standard():
    res = calculate_cagr(100.0, 207.36, 4)
    assert res["cagr"] == 20.0
    assert res["turnaround_flag"] is False


def test_calculate_cagr_turnaround():
    res = calculate_cagr(-50.0, 100.0, 3)
    assert res["cagr"] is None
    assert res["turnaround_flag"] is True


def test_calculate_cagr_zero_or_negative_both():
    res = calculate_cagr(-50.0, -10.0, 3)
    assert res["cagr"] is None
    assert res["turnaround_flag"] is False


def test_calculate_series_cagr():
    series = [("2020", 100.0), ("2021", 110.0), ("2022", 121.0), ("2023", 133.1)]
    res = calculate_series_cagr(series, 3)
    assert res["cagr"] == 10.0
