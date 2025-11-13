from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from typing import Dict

# Importar tus módulos
from src.data_processing import load_data, aggregate_sales
from src.sarima_model import get_sarima_forecast, run_backtest_sarima
from src.xgboost_model import get_xgboost_forecast, run_backtest_xgboost

app = FastAPI(
    title="Retail Forecasting API",
    description="API para pronósticos de ventas usando SARIMA y XGBoost",
    version="3.0.0"
)

# CORS para streamlit.app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Puedes restringir luego a tu dominio streamlit.app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar datos una vez
DF_RAW, STATUS = load_data()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/config/filters")
def config_filters():
    if DF_RAW is None:
        raise HTTPException(500, "Data not loaded")

    return {
        "categories": sorted(DF_RAW["Category"].dropna().unique().tolist()),
        "regions": sorted(DF_RAW["Region"].dropna().unique().tolist()),
        "years": sorted(DF_RAW["Order_Date"].dt.year.dropna().unique().tolist())
    }


@app.get("/forecast")
def forecast_api(
    category: str,
    region: str,
    model: str = "sarima",
    horizon: int = 12
):
    if DF_RAW is None:
        raise HTTPException(500, "Data not loaded")

    df_filtered = aggregate_sales(DF_RAW, category, region)

    if model == "sarima":
        forecast = get_sarima_forecast(df_filtered, horizon)
    else:
        forecast = get_xgboost_forecast(df_filtered, horizon)

    return {"forecast": forecast}
