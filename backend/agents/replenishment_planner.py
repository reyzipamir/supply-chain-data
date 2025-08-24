"""
Replenishment planning agent.

This module provides a simple policy for computing replenishment
quantities based on current inventory position, reorder points and
target base stock levels. The agent returns an order quantity
sufficient to raise the inventory position to the desired base stock
level when the position falls below the reorder point. Otherwise, it
returns zero.
"""

from __future__ import annotations

from typing import Union


def compute_replenishment(
    net_available: Union[int, float], reorder_point: Union[int, float], base_stock: Union[int, float]
) -> int:
    """Calculate the replenishment quantity.

    This function implements a simple order‑up‑to policy. When the net
    available inventory is below the reorder point, it orders enough
    units to reach the base stock level. Otherwise, no order is
    suggested.

    Parameters
    ----------
    net_available : int or float
        Current net available inventory (on hand plus on order minus
        backorders).
    reorder_point : int or float
        Reorder point (ROP). When inventory falls below this level,
        replenishment is triggered.
    base_stock : int or float
        Target base stock level. Orders bring the inventory position up
        to this level when triggered.

    Returns
    -------
    int
        Suggested order quantity. Always non‑negative and rounded to
        nearest integer.
    """
    # Determine whether reorder is needed
    if net_available < reorder_point:
        # Compute quantity needed to reach base stock
        order_qty = base_stock - net_available
        # Ensure non‑negative and round to nearest whole unit
        return int(max(0.0, round(order_qty)))
    else:
        return 0
