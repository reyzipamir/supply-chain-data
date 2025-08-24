"""
Streamlit user interface for the supply chain multi‑agent system.

This simple Streamlit app allows an end user to interact with the
underlying FastAPI services. It provides inputs for selecting a SKU
and site, entering lead time statistics and service level targets, and
specifying current inventory. Upon submitting the form, the app
invokes the forecast, inventory optimization and replenishment APIs in
sequence and displays the results.

To run the app locally, first start the FastAPI server (see
``backend/main.py``). Then, from the repository root directory:

.. code-block:: bash

    streamlit run frontend/streamlit_app.py
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import requests


# Base URL of the API server. When deploying, update this accordingly.
BASE_URL = st.secrets.get("api_base_url", "http://localhost:8000")

# Load sales history to populate select boxes
@st.cache_data
def load_sales_history(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def run_ui():
    st.set_page_config(page_title="Supply Chain Agent Demo", layout="wide")
    st.title("Supply Chain Multi‑Agent Demo")

    # Sidebar for inputs
    st.sidebar.header("Parameters")

    # Load data
    sales_history = load_sales_history("sales_history.csv")
    sku_options = sales_history["sku_id"].unique().tolist()
    site_options = sales_history["site_id"].unique().tolist()

    sku_id = st.sidebar.selectbox("Select SKU", sku_options)
    site_id = st.sidebar.selectbox("Select Site", site_options)
    lead_time_mean = st.sidebar.number_input(
        "Lead time mean (days)", min_value=0.1, value=7.0, step=0.1
    )
    lead_time_std = st.sidebar.number_input(
        "Lead time std (days)", min_value=0.0, value=2.0, step=0.1
    )
    target_csl = st.sidebar.slider(
        "Target cycle service level", min_value=0.5, max_value=0.99, value=0.9, step=0.01
    )
    net_available = st.sidebar.number_input(
        "Current net available inventory", min_value=0.0, value=500.0, step=1.0
    )

    if st.sidebar.button("Run pipeline"):
        # Compose payloads and call API
        with st.spinner("Running agents..."):
            forecast_resp = requests.post(
                f"{BASE_URL}/forecast",
                json={
                    "sku_id": sku_id,
                    "site_id": site_id,
                },
                timeout=30,
            )
            if forecast_resp.status_code != 200:
                st.error(f"Forecast request failed: {forecast_resp.text}")
                return
            forecast_data = forecast_resp.json()
            meio_resp = requests.post(
                f"{BASE_URL}/meio/optimize",
                json={
                    "mean_demand_per_day": forecast_data["mean_demand_per_day"],
                    "std_demand_per_day": forecast_data["std_demand_per_day"],
                    "lead_time_mean": lead_time_mean,
                    "lead_time_std": lead_time_std,
                    "target_csl": target_csl,
                },
                timeout=30,
            )
            if meio_resp.status_code != 200:
                st.error(f"MEIO request failed: {meio_resp.text}")
                return
            meio_data = meio_resp.json()
            replenish_resp = requests.post(
                f"{BASE_URL}/replenish",
                json={
                    "net_available": net_available,
                    "reorder_point": meio_data["reorder_point"],
                    "base_stock": meio_data["base_stock"],
                },
                timeout=30,
            )
            if replenish_resp.status_code != 200:
                st.error(f"Replenishment request failed: {replenish_resp.text}")
                return
            repl_data = replenish_resp.json()

        # Display results
        st.subheader("Demand Forecast (next period)")
        st.json(forecast_data)

        st.subheader("MEIO Optimization Result")
        st.json(meio_data)

        st.subheader("Replenishment Suggestion")
        st.json(repl_data)

    # Show raw data tab
    st.subheader("Sales History Snapshot")
    st.dataframe(sales_history.head(50))


if __name__ == "__main__":
    run_ui()
