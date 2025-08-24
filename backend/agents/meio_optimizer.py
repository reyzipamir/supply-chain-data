"""
Multi‑echelon inventory optimization (MEIO) agent.

This module provides a simple yet extensible function to determine
safety stock, reorder points and base stock levels given demand
statistics, lead time parameters and a target cycle service level.

The implementation assumes a normal approximation of demand during the
lead time and uses common formulas from inventory theory:

* Demand during lead time mean: μ_LT = μ_D * LT_mean
* Demand during lead time std:  σ_LT = sqrt(LT_mean * σ_D^2 + μ_D^2 * σ_LT^2)
* Safety stock: SS = z(target CSL) * σ_LT
* Reorder point: ROP = μ_LT + SS
* Base stock level: BS = ROP + μ_LT  (simplified; actual base stock
  depends on review period and pipeline inventory)

The z‑values for common service levels are provided; otherwise a
reasonable default is chosen. Users may override the z table via the
``z_values`` argument.
"""

from __future__ import annotations

from typing import Dict, Optional
import numpy as np


# Predefined z‑scores for selected service levels (cycle service level)
Z_VALUES: Dict[float, float] = {
    0.50: 0.0,
    0.60: 0.2533471,
    0.70: 0.5244005,
    0.80: 0.8416212,
    0.85: 1.0364334,
    0.90: 1.2815516,
    0.95: 1.6448536,
    0.98: 2.0537489,
    0.99: 2.3263479,
}


def optimize_inventory(
    mean_demand_per_day: float,
    std_demand_per_day: float,
    lead_time_mean: float,
    lead_time_std: float,
    target_csl: float,
    z_values: Optional[Dict[float, float]] = None,
) -> Dict[str, float]:
    """Compute safety stock, reorder point and base stock levels.

    Parameters
    ----------
    mean_demand_per_day : float
        Estimated mean daily demand.
    std_demand_per_day : float
        Estimated standard deviation of daily demand.
    lead_time_mean : float
        Average replenishment lead time in days.
    lead_time_std : float
        Standard deviation of replenishment lead time in days.
    target_csl : float
        Target cycle service level (e.g. 0.95 for 95%).
    z_values : dict, optional
        Optional lookup for z‑scores keyed by service level. If not
        provided, the module default ``Z_VALUES`` is used.

    Returns
    -------
    dict
        A dictionary with keys ``mu_lt``, ``sigma_lt``, ``safety_stock``,
        ``reorder_point`` and ``base_stock``.
    """
    if z_values is None:
        z_values = Z_VALUES
    # Compute mean and std of demand during lead time
    mu_lt = mean_demand_per_day * lead_time_mean
    sigma_lt = np.sqrt(
        lead_time_mean * (std_demand_per_day ** 2) + (mean_demand_per_day ** 2) * (lead_time_std ** 2)
    )
    # Get z score for target service level; default to 1.28 (~90%) if not found
    z = z_values.get(round(target_csl, 2), 1.2815516)
    safety_stock = z * sigma_lt
    reorder_point = mu_lt + safety_stock
    # Simplistic base stock: reorder point plus average demand over lead time
    base_stock = reorder_point + mu_lt
    return {
        "mu_lt": float(mu_lt),
        "sigma_lt": float(sigma_lt),
        "safety_stock": float(safety_stock),
        "reorder_point": float(reorder_point),
        "base_stock": float(base_stock),
    }
