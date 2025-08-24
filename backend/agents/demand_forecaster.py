"""
Demand forecasting agent.

This module implements a simple probabilistic demand forecasting method
based on historical sales data. Given a specific SKU and site
combination, it loads sales history from a CSV file, aggregates demand
into a daily time series, and computes the mean and standard deviation
over a specified historical window. It then generates a forecast for
each future day in the horizon using those statistics.

The p50 (median) forecast is equal to the historical mean. Quantile
estimates p10 and p90 are derived from the mean and standard deviation
assuming a normal distribution. When historical variance is zero or
insufficient, the method falls back to simple heuristics.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Tuple, List, Dict


def load_sales_data(file_path: str) -> pd.DataFrame:
    """Load sales history from a CSV file.

    The CSV must contain at least the following columns: ``date``,
    ``sku_id``, ``site_id`` and ``qty``. Additional columns are ignored.

    Parameters
    ----------
    file_path : str
        Path to the CSV file with sales data.

    Returns
    -------
    pandas.DataFrame
        A DataFrame with raw sales history.
    """
    return pd.read_csv(file_path, parse_dates=["date"])


def _aggregate_daily_series(df: pd.DataFrame) -> pd.Series:
    """Aggregate raw sales records into a daily time series.

    Missing days are filled with zeros so that statistics are computed
    over a continuous time series.

    Parameters
    ----------
    df : pandas.DataFrame
        Filtered sales history for a single SKU and site. Must include
        a ``date`` index and a ``qty`` column.

    Returns
    -------
    pandas.Series
        Daily demand time series indexed by date.
    """
    # ensure date is index
    if df.index.name != "date":
        df = df.set_index("date")
    # reindex to a daily frequency
    daily_series = df["qty"].resample("D").sum().fillna(0)
    return daily_series


def forecast_demand(
    sales_data: pd.DataFrame,
    sku_id: str,
    site_id: str,
    history_window: int = 28,
    forecast_horizon: int = 14,
) -> Tuple[List[Dict[str, float]], float, float]:
    """Generate a probabilistic demand forecast for a specific SKU/site.

    The function filters the sales history for the given ``sku_id`` and
    ``site_id``, aggregates it into a daily time series, and computes
    the mean and standard deviation over the last ``history_window`` days.
    It then returns a list of dictionaries containing p10, p50 and p90
    forecasts for each day in the future horizon. Additionally, it
    returns the mean and standard deviation of daily demand used to
    generate the forecast.

    Parameters
    ----------
    sales_data : pandas.DataFrame
        The full sales history data set.
    sku_id : str
        SKU identifier.
    site_id : str
        Site identifier.
    history_window : int, optional
        Number of most recent days to use for computing statistics.
    forecast_horizon : int, optional
        Number of future days to forecast.

    Returns
    -------
    tuple
        A tuple containing: (1) a list of dictionaries with keys
        ``day``, ``p10``, ``p50`` and ``p90`` describing forecasts for
        each future day; (2) the mean daily demand; and (3) the standard
        deviation of daily demand.
    """
    # Filter data for the given SKU and site
    df = sales_data[(sales_data["sku_id"] == sku_id) & (sales_data["site_id"] == site_id)].copy()
    if df.empty:
        # If no history exists, return zeros
        predictions = [
            {"day": i + 1, "p10": 0.0, "p50": 0.0, "p90": 0.0}
            for i in range(forecast_horizon)
        ]
        return predictions, 0.0, 0.0

    # Aggregate into daily series
    series = _aggregate_daily_series(df)
    # Take last history_window days
    recent = series.tail(history_window)
    # Compute mean and standard deviation
    mean = recent.mean() if not recent.empty else 0.0
    std = recent.std(ddof=0) if len(recent) > 1 else 0.0

    # Prepare quantile predictions
    predictions: List[Dict[str, float]] = []
    # Use Z score for 10th and 90th percentile of a normal distribution
    z10 = -1.2815515655446004  # approximate z for 10% quantile
    z90 = 1.2815515655446004   # approximate z for 90% quantile
    for i in range(forecast_horizon):
        p50 = float(mean)
        if std > 0:
            p10 = float(max(0.0, mean + z10 * std))
            p90 = float(max(0.0, mean + z90 * std))
        else:
            # When standard deviation is zero, all quantiles equal the mean
            p10 = p50
            p90 = p50
        predictions.append({"day": i + 1, "p10": p10, "p50": p50, "p90": p90})

    return predictions, float(mean), float(std)
