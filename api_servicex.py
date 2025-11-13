
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from typing import Dict, Optional

# --- 1. Importaciones desde los NUEVOS módulos de 'src' ---
from src.data_processing import load_data, aggregate_sales
from src.sarima_model import get_sarima_forecast, run_backtest_sarima
from src.xgboost_model import get_xgboost_forecast, run_backtest_xgboost

# --- 2. Inicialización de la Aplicación y Carga de Datos ---
app = FastAPI(
    title="Retail Forecasting API",
    description="API para obtener pronósticos de ventas (SARIMA y XGBoost) filtrado por categoría, región y años.",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DF_RAW, STATUS = load_data()

if DF_RAW is None:
    print(f"FATAL ERROR: Datos no cargados. Razón: {STATUS}")
    CATEGORIES = []
    REGIONS = []
    YEARS = []
else:
    print("Datos cargados y preprocesados exitosamente.")
    CATEGORIES = ['All Categories'] + sorted(DF_RAW['Category'].unique().tolist())
    REGIONS = ['All Regions'] + sorted(DF_RAW['Region'].unique().tolist())
    # Asegurar tipo datetime y derivar años disponibles
    if not pd.api.types.is_datetime64_any_dtype(DF_RAW['Order_Date']):
        DF_RAW['Order_Date'] = pd.to_datetime(DF_RAW['Order_Date'], errors='coerce')
    YEARS = sorted(DF_RAW['Order_Date'].dropna().dt.year.unique().tolist())

# --- 2.b Helper de filtrado por rango de años ---
def filter_by_years(df: pd.DataFrame, start_year: Optional[int], end_year: Optional[int]) -> pd.DataFrame:
    """Filtra por rango de años usando la columna Order_Date. Si ambos son None, no filtra.
       Si solo uno viene, se utiliza el min/max disponible en los datos."""
    if df is None or df.empty:
        return df
    if not pd.api.types.is_datetime64_any_dtype(df['Order_Date']):
        df = df.copy()
        df['Order_Date'] = pd.to_datetime(df['Order_Date'], errors='coerce')

    if start_year is None and end_year is None:
        return df

    data_year_min = int(df['Order_Date'].dropna().dt.year.min())
    data_year_max = int(df['Order_Date'].dropna().dt.year.max())
    start = start_year if start_year is not None else data_year_min
    end = end_year if end_year is not None else data_year_max

    df_f = df[(df['Order_Date'].dt.year >= start) & (df['Order_Date'].dt.year <= end)]
    return df_f

# --- 3. Endpoints del API ---

@app.get("/")
def read_root():
    return {"message": "Welcome to the Retail Forecasting API. Access /docs for documentation."}

@app.get("/config/filters")
def get_filters():
    """Devuelve las listas de filtros para poblar los selectores del frontend (categorías, regiones y años)."""
    if DF_RAW is None:
        raise HTTPException(status_code=500, detail=f"Datos no cargados. Razón: {STATUS}")
    return {
        "categories": CATEGORIES,
        "regions": REGIONS,
        "years": YEARS,  # lista de años disponibles (int)
        "year_min": YEARS[0] if YEARS else None,
        "year_max": YEARS[-1] if YEARS else None
    }

@app.get("/sales/forecast", response_model=Dict)
def sales_forecast_endpoint(
    model_type: str = Query("sarima", description="El modelo a usar: 'sarima' o 'xgboost'"),
    category: str = Query("All Categories", description="Categoría del producto."),
    region: str = Query("All Regions", description="Región geográfica."),
    steps: int = Query(12, description="Número de meses a pronosticar."),
    start_year: Optional[int] = Query(None, description="Año inicial (opcional)."),
    end_year: Optional[int] = Query(None, description="Año final (opcional).")
):
    """
    Endpoint dinámico que genera un pronóstico futuro usando el modelo seleccionado.
    Permite filtrar por rango de años usando Order_Date.
    """
    if DF_RAW is None:
        raise HTTPException(status_code=500, detail=f"Error de carga de datos inicial: {STATUS}")

    # --- Filtrado por años (antes de agregar) ---
    df_filtered = filter_by_years(DF_RAW, start_year, end_year)
    if df_filtered.empty:
        raise HTTPException(status_code=404, detail=f"Sin datos para el rango de años solicitado.")

    # --- Agregación y validación ---
    ts_history, data_available = aggregate_sales(df=df_filtered, category=category, region=region)
    if not data_available or ts_history.empty:
        return {"status": "error", "message": f"No data found for {category}/{region} en el rango de años solicitado."}

    print(
        f"📅 Rango de fechas para {category}/{region} (años {start_year or 'min'}-{end_year or 'max'}):",
        ts_history.index.min(), "→", ts_history.index.max()
    )

    # --- Enrutador de modelo ---
    if model_type == "sarima":
        forecast_df, status = get_sarima_forecast(ts_history, steps)
    elif model_type == "xgboost":
        forecast_df, status = get_xgboost_forecast(ts_history, steps)
    else:
        raise HTTPException(status_code=400, detail="model_type debe ser 'sarima' o 'xgboost'")

    if status != "Success" or forecast_df is None:
        raise HTTPException(status_code=400, detail=f"Error en el modelo {model_type}: {status}")

    # --- Serialización JSON ---
    history_json = {
        "index": [i.strftime("%Y-%m-%d") for i in ts_history.index],
        "data": ts_history.values.tolist()
    }

    forecast_df.index = forecast_df.index.strftime('%Y-%m-%d')
    forecast_json = forecast_df.reset_index().rename(columns={'index': 'Date'}).to_dict(orient='records')

    return {
        "status": "success",
        "model_used": model_type,
        "year_range": {
            "start_year": start_year,
            "end_year": end_year
        },
        "history": history_json,
        "forecast": forecast_json
    }

@app.get("/sales/evaluation", response_model=Dict)
def sales_evaluation_endpoint(
    model_type: str = Query("sarima", description="El modelo a evaluar: 'sarima' o 'xgboost'"),
    category: str = Query("All Categories", description="Categoría del producto."),
    region: str = Query("All Regions", description="Región geográfica."),
    start_year: Optional[int] = Query(None, description="Año inicial (opcional)."),
    end_year: Optional[int] = Query(None, description="Año final (opcional).")
):
    """
    Realiza un backtest del modelo seleccionado y devuelve las métricas de error.
    Permite filtrar por rango de años usando Order_Date.
    """
    if DF_RAW is None:
        raise HTTPException(status_code=500, detail=f"Error de carga de datos inicial: {STATUS}")

    # --- Filtrado por años (antes de agregar) ---
    df_filtered = filter_by_years(DF_RAW, start_year, end_year)
    if df_filtered.empty:
        raise HTTPException(status_code=404, detail=f"Sin datos para el rango de años solicitado.")

    ts_history, data_available = aggregate_sales(df=df_filtered, category=category, region=region)
    if not data_available or ts_history.empty:
        return {"status": "error", "message": f"No data found for {category}/{region} en el rango de años solicitado."}

    # --- Enrutador de modelo ---
    if model_type == "sarima":
        metrics = run_backtest_sarima(ts_history, test_months=12)
    elif model_type == "xgboost":
        metrics = run_backtest_xgboost(ts_history, test_months=12)
    else:
        raise HTTPException(status_code=400, detail="model_type debe ser 'sarima' o 'xgboost'")

    if metrics.get("status") != "Success":
        raise HTTPException(status_code=400, detail=metrics.get("message", "Backtest error"))

    metrics["model_used"] = model_type
    metrics["year_range"] = {"start_year": start_year, "end_year": end_year}
    return metrics
