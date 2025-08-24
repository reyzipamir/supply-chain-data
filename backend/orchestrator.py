"""
Pipeline orchestrator for the supply chain multi‑agent system.

This module provides a simple function that demonstrates how to
compose the individual agents exposed by the API into a complete
decision pipeline. In a real production scenario, this could be
implemented within a workflow engine or scheduled job. Here, it uses
HTTP requests to call the FastAPI endpoints sequentially.

Usage::

    from backend.orchestrator import run_pipeline

    result = run_pipeline(
        base_url="http://localhost:8000",
        sku_id="SKU1",
        site_id="STORE1",
        lead_time_mean=7.0,
        lead_time_std=2.0,
        target_csl=0.95,
        net_available=500,
    )

    print(result)
"""

from __future__ import annotations

import requests
from typing import Dict, Any


def run_pipeline(
    base_url: str,
    sku_id: str,
    site_id: str,
    lead_time_mean: float,
    lead_time_std: float,
    target_csl: float,
    net_available: float,
    history_window: int = 28,
    forecast_horizon: int = 14,
) -> Dict[str, Any]:
    """Execute the full forecast → MEIO → replenish pipeline via API calls.

    Parameters
    ----------
    base_url : str
        Base URL of the running API server (e.g. ``http://localhost:8000``).
    sku_id : str
        SKU identifier.
    site_id : str
        Site identifier.
    lead_time_mean : float
        Mean lead time in days.
    lead_time_std : float
        Standard deviation of lead time.
    target_csl : float
        Target cycle service level (0 < CSL < 1).
    net_available : float
        Current net available inventory.
    history_window : int, optional
        Number of days of history to use in forecasting.
    forecast_horizon : int, optional
        Number of days to forecast.

    Returns
    -------
    dict
        A dictionary containing the intermediate results from each agent and
        the final replenishment suggestion.
    """
    # Step 1: Forecast demand
    forecast_payload = {
        "sku_id": sku_id,
        "site_id": site_id,
        "history_window": history_window,
        "forecast_horizon": forecast_horizon,
    }
    forecast_resp = requests.post(f"{base_url}/forecast", json=forecast_payload)
    forecast_resp.raise_for_status()
    forecast_data = forecast_resp.json()

    # Step 2: Optimize inventory
    meio_payload = {
        "mean_demand_per_day": forecast_data["mean_demand_per_day"],
        "std_demand_per_day": forecast_data["std_demand_per_day"],
        "lead_time_mean": lead_time_mean,
        "lead_time_std": lead_time_std,
        "target_csl": target_csl,
    }
    meio_resp = requests.post(f"{base_url}/meio/optimize", json=meio_payload)
    meio_resp.raise_for_status()
    meio_data = meio_resp.json()

    # Step 3: Compute replenishment
    replenish_payload = {
        "net_available": net_available,
        "reorder_point": meio_data["reorder_point"],
        "base_stock": meio_data["base_stock"],
    }
    repl_resp = requests.post(f"{base_url}/replenish", json=replenish_payload)
    repl_resp.raise_for_status()
    repl_data = repl_resp.json()

    return {
        "forecast": forecast_data,
        "meio": meio_data,
        "replenishment": repl_data,
    }
