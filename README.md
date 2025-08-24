# Supply Chain Multi‑Agent System

This repository contains a sample implementation of a multi‑agent supply
chain planning system. It accompanies the synthetic data sets provided
in the root of the project and demonstrates how to build a simple
production‑ready architecture using Python.

## Components

### Data

The repository includes several CSV files (`sales_history.csv`,
`lead_time_history.csv`, etc.) that describe a hypothetical supply
chain. These files can be used to test the agents and serve as
templates for integrating real data.

### Backend (FastAPI)

The `backend/` directory implements a RESTful API using FastAPI. The
API exposes three endpoints:

| Endpoint                | Description                                               |
|------------------------|-----------------------------------------------------------|
| `POST /forecast`       | Generates probabilistic demand forecasts for a SKU/site   |
| `POST /meio/optimize`  | Computes safety stock, reorder point and base stock levels|
| `POST /replenish`      | Suggests replenishment quantity given current inventory   |

Each endpoint accepts a JSON payload and returns a structured
response. See the Pydantic models defined in `backend/main.py` for
detailed schemas. FastAPI automatically generates interactive API docs
at `/docs` when the server is running.

To run the API locally:

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

Ensure that the CSV files are located in the working directory so that
the forecasting agent can load sales history. The API reads
`sales_history.csv` by default.

### Orchestrator

The `backend/orchestrator.py` module illustrates how to compose the
individual agents into an end‑to‑end decision pipeline via HTTP calls.
It is a simple example; in a full production environment this logic
could reside in a scheduler, workflow engine or be invoked from a UI.

### Frontend (Streamlit)

The `frontend/` directory contains a minimal Streamlit application
(`streamlit_app.py`) that acts as a user interface. It allows users to
select a SKU and site, specify lead time parameters and service level
targets, and then trigger the pipeline. The results of the forecast,
MEIO calculation and replenishment suggestion are displayed on the
page. To run the UI, first start the backend and then run:

```bash
streamlit run frontend/streamlit_app.py
```

You can customise the `BASE_URL` in the app via Streamlit secrets to
point at a remote API endpoint.

## Extending the System

While this project demonstrates a basic architecture, it is designed
for extensibility. Potential enhancements include:

* Integrating more sophisticated forecasting models (e.g. machine
  learning or causal inference) in `backend/agents/demand_forecaster.py`.
* Implementing optimisation models using OR tools or MILP in
  `backend/agents/meio_optimizer.py`.
* Adding authentication, caching or database persistence to the API.
* Building a richer front‑end with data visualisations and dashboards.

## License

This project is provided for demonstration purposes without any
warranty. You are free to adapt it for your own needs.
