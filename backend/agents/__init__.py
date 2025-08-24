"""
Agent subpackage.

This subpackage contains functional implementations for the individual
agents used in the supply chain planning system. Each agent encapsulates
the core logic for its respective task:

* demand_forecaster: generates probabilistic demand forecasts based on
  historical sales data.
* meio_optimizer: computes optimal safety stock, reorder points and
  base stock levels under a target service level.
* replenishment_planner: determines order quantities required to
  replenish inventory when current stock falls below the reorder point.

The functions here are pure and stateless. They take primitive inputs
and return dictionary outputs so they can easily be consumed by APIs
and higher‑level orchestration code.
"""

from .demand_forecaster import load_sales_data, forecast_demand  # noqa: F401
from .meio_optimizer import optimize_inventory  # noqa: F401
from .replenishment_planner import compute_replenishment  # noqa: F401
