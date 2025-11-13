import streamlit as st
import requests
import os

# ===========================
# API CONFIG
# ===========================

API_URL = st.secrets.get(
    "API_URL",
    os.getenv("API_URL", "http://127.0.0.1:8000")
)

st.caption(f"Backend API: {API_URL}")

# Helpers


def api_get(path, **kwargs):
    res = requests.get(f"{API_URL}{path}", **kwargs)
    res.raise_for_status()
    return res.json()


def api_post(path, **kwargs):
    res = requests.post(f"{API_URL}{path}", **kwargs)
    res.raise_for_status()
    return res.json()

# ===========================
# UI
# ===========================


st.title("📊 Dashboard de Planificación de Demanda v3.0")

# Load filters
try:
    filters = api_get("/config/filters")
    categories = filters["categories"]
    regions = filters["regions"]
    years = filters["years"]
except Exception as e:
    st.error(f"No se pudo cargar filtros desde el API: {e}")
    st.stop()

modelo = st.radio("Modelo de Pronóstico:", ["SARIMA", "XGBoost"])
categoria = st.selectbox("Categoría", ["All"] + categories)
region = st.selectbox("Región", ["All"] + regions)
anio = st.selectbox("Año", ["All"] + years)
horizon = st.slider("Horizonte (meses)", 1, 24, 12)

if st.button("Generar Pronóstico"):
    try:
        data = api_get(
            "/forecast",
            params={
                "category": categoria,
                "region": region,
                "model": modelo.lower(),
                "horizon": horizon
            }
        )
        st.success("Pronóstico generado correctamente")
        st.json(data)
    except Exception as e:
        st.error(f"Error al consultar pronóstico: {e}")
