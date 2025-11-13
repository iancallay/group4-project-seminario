from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict

from src.data_processing import load_data, aggregate_sales, list_years, kpis
from src.sarima_model import get_sarima_forecast, run_backtest_sarima
from src.xgboost_model import get_xgboost_forecast, run_backtest_xgboost

app = FastAPI(
    title="Retail Forecasting API",
    description="Pronósticos (SARIMA/XGBoost) y KPIs filtrados por categoría, región y año.",
    version="2.3.0"
)

# CORS abierto para pruebas locales
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carga de datos al iniciar
DF_RAW, STATUS = load_data()
if DF_RAW is None:
    print(f"[ERROR] {STATUS}")
else:
    print("[OK] Datos cargados.")
    CATEGORIES = ['All Categories'] + \
        sorted(DF_RAW['Category'].unique().tolist())
    REGIONS = ['All Regions'] + sorted(DF_RAW['Region'].unique().tolist())
    YEARS = ["All years"] + list_years(DF_RAW)

# Umbral mínimo de puntos para modelar/evaluar
MIN_POINTS = 24  # meses


@app.get("/health")
def health():
    """Health check sencillo para verificar que el servidor esté arriba."""
    if DF_RAW is None:
        raise HTTPException(
            status_code=500, detail=f"Datos no cargados: {STATUS}")
    return {"status": "ok", "detail": "API running"}


@app.get("/")
def root():
    return {"message": "Retail Forecasting API v2.3.0. Visita /docs para documentación."}


@app.get("/config/filters")
def get_filters():
    """Listas para poblar selectores del frontend."""
    if DF_RAW is None:
        raise HTTPException(
            status_code=500, detail=f"Error de carga de datos: {STATUS}")
    return {"categories": CATEGORIES, "regions": REGIONS, "years": YEARS}


@app.get("/sales/forecast", response_model=Dict)
def sales_forecast_endpoint(
    model_type: str = Query(
        "sarima", description="Modelos disponibles: sarima | xgboost"),
    category:   str = Query("All Categories"),
    region:     str = Query("All Regions"),
    year:       str = Query("All years"),
    steps:      int = Query(12, ge=1, le=60)
):
    """Genera pronóstico futuro usando el modelo seleccionado."""
    if DF_RAW is None:
        raise HTTPException(
            status_code=500, detail=f"Error de carga de datos: {STATUS}")

    ts_history, ok = aggregate_sales(DF_RAW, category, region, year)
    if not ok or len(ts_history) == 0:
        return {"status": "error", "message": f"Sin datos para {category}/{region}/{year}."}

    if len(ts_history) < MIN_POINTS:
        return {"status": "error", "message": f"Datos insuficientes: se requieren ≥{MIN_POINTS} meses y hay {len(ts_history)}."}

    # Selección de modelo
    if model_type == "sarima":
        forecast_df, status = get_sarima_forecast(ts_history, steps)
    elif model_type == "xgboost":
        forecast_df, status = get_xgboost_forecast(ts_history, steps)
    else:
        return {"status": "error", "message": "model_type debe ser 'sarima' o 'xgboost'."}

    if status != "Success" or forecast_df is None:
        return {"status": "error", "message": f"Error en el modelo {model_type}: {status}"}

    # Serialización
    history_json = {
        "index": [i.strftime("%Y-%m-%d") for i in ts_history.index],
        "data": ts_history.values.tolist()
    }
    forecast_df.index = forecast_df.index.strftime('%Y-%m-%d')
    forecast_json = (
        forecast_df.reset_index()
                   .rename(columns={'index': 'Date'})
                   .to_dict(orient='records')
    )

    return {"status": "success", "model_used": model_type, "history": history_json, "forecast": forecast_json}


@app.get("/sales/evaluation", response_model=Dict)
def sales_evaluation_endpoint(
    model_type: str = Query("sarima"),
    category:   str = Query("All Categories"),
    region:     str = Query("All Regions"),
    year:       str = Query("All years")
):
    """Backtest del modelo seleccionado y métricas de error."""
    if DF_RAW is None:
        raise HTTPException(
            status_code=500, detail=f"Error de carga de datos: {STATUS}")

    ts_history, ok = aggregate_sales(DF_RAW, category, region, year)
    if not ok or len(ts_history) == 0:
        return {"status": "error", "message": f"Sin datos para {category}/{region}/{year}."}

    if len(ts_history) < MIN_POINTS:
        return {"status": "error", "message": f"Datos insuficientes: se requieren ≥{MIN_POINTS} meses y hay {len(ts_history)}."}

    if model_type == "sarima":
        metrics = run_backtest_sarima(ts_history, test_months=12)
    elif model_type == "xgboost":
        metrics = run_backtest_xgboost(ts_history, test_months=12)
    else:
        return {"status": "error", "message": "model_type debe ser 'sarima' o 'xgboost'."}

    if metrics.get("status") != "Success":
        return {"status": "error", "message": metrics.get("message", "Error en backtest")}
    metrics["model_used"] = model_type
    return metrics


@app.get("/sales/kpis", response_model=Dict)
def sales_kpis_endpoint(
    category: str = Query("All Categories"),
    region:   str = Query("All Regions"),
    year:     str = Query("All years")
):
    """Devuelve KPIs: ventas totales, por región y por año (con filtros básicos)."""
    if DF_RAW is None:
        raise HTTPException(
            status_code=500, detail=f"Error de carga de datos: {STATUS}")
    results = kpis(DF_RAW, category=category, region=region, year=year)
    return {"status": "success", **results}
