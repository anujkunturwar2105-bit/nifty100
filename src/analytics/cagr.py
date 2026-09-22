"""
CAGR Calculation Engine
Handles 1Y, 3Y, 5Y, and 10Y CAGR calculations with edge case handling
(negative base values, turnaround flags, zero division, missing periods).
"""

from typing import Any


def calculate_cagr(start_val: float | None, end_val: float | None, num_years: int) -> dict[str, Any]:
    """
    Calculate Compound Annual Growth Rate (CAGR) in percentage.

    Rules:
    - Return None for missing/null values or non-positive num_years.
    - If start_val <= 0 and end_val > 0: set cagr=None, turnaround_flag=True.
    - If start_val <= 0 and end_val <= 0: return cagr=None.
    - If start_val > 0 and end_val <= 0: return cagr = -100.0 or calculated percentage if formula applicable.
    - Standard formula: ((end_val / start_val) ** (1 / num_years) - 1) * 100
    """
    if start_val is None or end_val is None or num_years <= 0:
        return {"cagr": None, "turnaround_flag": False}

    try:
        start_val = float(start_val)
        end_val = float(end_val)
    except (ValueError, TypeError):
        return {"cagr": None, "turnaround_flag": False}

    # Turnaround case: negative/zero base to positive end value
    if start_val <= 0 and end_val > 0:
        return {"cagr": None, "turnaround_flag": True}

    if start_val <= 0 or end_val <= 0:
        return {"cagr": None, "turnaround_flag": False}

    try:
        cagr_val = ((end_val / start_val) ** (1.0 / num_years) - 1.0) * 100.0
        return {"cagr": round(cagr_val, 2), "turnaround_flag": False}
    except Exception:
        return {"cagr": None, "turnaround_flag": False}


def calculate_series_cagr(series: list[tuple[str, float]], years: int) -> dict[str, Any]:
    """
    Calculate CAGR from a sorted list of (year_str, float_val) tuples for a specified period.
    """
    if len(series) < 2:
        return {"cagr": None, "turnaround_flag": False}

    # Sort series by year ascending
    sorted_series = sorted(series, key=lambda x: str(x[0]))
    latest_year, latest_val = sorted_series[-1]

    # Find historical matching year
    target_idx = len(sorted_series) - 1 - years
    if target_idx < 0:
        return {"cagr": None, "turnaround_flag": False}

    start_year, start_val = sorted_series[target_idx]
    return calculate_cagr(start_val, latest_val, years)
