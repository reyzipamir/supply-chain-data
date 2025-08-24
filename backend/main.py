"""
FastAPI application for the supply chain multi‑agent system.

This module exposes a set of REST endpoints that wrap the individual
agent functions. It allows external clients (e.g. UI layers or
orchestrators) to request demand forecasts, inventory optimization
parameters and replenishment suggestions.

The server expects the sales history CSV (``sales_history.csv``) to be
present in the working directory. Other master data such as lead time
statistics or service level targets can be supplied via API payloads.

To run the server in development mode:

.. code-block:: bash

    uvicorn backend.main:app --reload --port 8000

The endpoints are self‑describing thanks to FastAPI's automatic OpenAPI
documentation available at ``/docs``.
"""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Dict

from .agents import load_sales_data, forecast_demand, optimize_inventory, compute_replenishment


app = FastAPI(title="Supply Chain Multi‑Agent API", version="0.1.0")

# Constants
SALES_HISTORY_FILE = "sales_history.csv"


class ForecastRequest(BaseModel):
    """Request model for the forecasting endpoint."""
    sku_id: str = Field(..., description="SKU identifier")
    site_id: str = Field(..., description="Site identifier (e.g. store or DC)")
    history_window: int = Field(28, ge=1, description="Number of days of history to use")
    forecast_horizon: int = Field(14, ge=1, description="Number of future days to predict")


class ForecastResponse(BaseModel):
    """Response model for the forecasting endpoint."""
    sku_id: str
    site_id: str
    mean_demand_per_day: float
    std_demand_per_day: float
    predictions: List[Dict[str, float]]


class MEIORequest(BaseModel):
    """Request model for the MEIO optimization endpoint."""
    mean_demand_per_day: float = Field(..., ge=0.0, description="Mean daily demand")
    std_demand_per_day: float = Field(..., ge=0.0, description="Std of daily demand")
    lead_time_mean: float = Field(..., gt=0.0, description="Mean lead time in days")
    lead_time_std: float = Field(..., ge=0.0, description="Standard deviation of lead time")
    target_csl: float = Field(..., gt=0.0, lt=1.0, description="Target cycle service level (0 < CSL < 1)")


class MEIOResponse(BaseModel):
    """Response model for the MEIO optimization endpoint."""
    mu_lt: float
    sigma_lt: float
    safety_stock: float
    reorder_point: float
    base_stock: float


class ReplenishRequest(BaseModel):
    """Request model for the replenishment endpoint."""
    net_available: float = Field(..., description="Current net available inventory")
    reorder_point: float = Field(..., ge=0.0, description="Reorder point")
    base_stock: float = Field(..., ge=0.0, description="Base stock level")


class ReplenishResponse(BaseModel):
    """Response model for the replenishment endpoint."""
    order_quantity: int


@app.get("/")
def read_root() -> Dict[str, str]:
    """Health check endpoint. Returns a simple status message."""
    return {"status": "ok"}


@app.post("/forecast", response_model=ForecastResponse)
def forecast(request: ForecastRequest) -> ForecastResponse:
    """Generate probabilistic demand forecasts for a SKU and site.

    The server loads the sales history from a CSV file, filters it
    according to the requested SKU and site, and delegates computation to
    the forecasting agent. The response includes the mean and standard
    deviation of daily demand and per‑day p10/p50/p90 forecasts.
    """
    sales_data = load_sales_data(SALES_HISTORY_FILE)
    predictions, mean, std = forecast_demand(
        sales_data,
        request.sku_id,
        request.site_id,
        request.history_window,
        request.forecast_horizon,
    )
    return ForecastResponse(
        sku_id=request.sku_id,
        site_id=request.site_id,
        mean_demand_per_day=mean,
        std_demand_per_day=std,
        predictions=predictions,
    )


@app.post("/meio/optimize", response_model=MEIOResponse)
def meio_optimize(request: MEIORequest) -> MEIOResponse:
    """Compute MEIO parameters for a given demand and lead time profile."""
    result = optimize_inventory(
        request.mean_demand_per_day,
        request.std_demand_per_day,
        request.lead_time_mean,
        request.lead_time_std,
        request.target_csl,
    )
    return MEIOResponse(**result)


@app.post("/replenish", response_model=ReplenishResponse)
def replenish(request: ReplenishRequest) -> ReplenishResponse:
    """Suggest a replenishment order quantity based on inventory position."""
    qty = compute_replenishment(
        request.net_available,
        request.reorder_point,
        request.base_stock,
    )
    return ReplenishResponse(order_quantity=qty)
