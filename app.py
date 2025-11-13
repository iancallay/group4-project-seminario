import os
import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Demand Planning Dashboard v2.3",
                   page_icon="🚀", layout="wide")

# Permite cambiar puerto del API con variable de entorno API_URL; por defecto 127.0.0.1:8000
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# ---------- Utilidades API ----------


@st.cache_data(ttl=600)
def get_filters():
    try:
        r = requests.get(f"{API_URL}/config/filters", timeout=10)
        r.raise_for_status()
        data = r.json()
        return data["categories"], data["regions"], data["years"]
    except Exception as e:
        st.error(f"No se pudo cargar filtros desde el API: {e}")
        return ["All Categories"], ["All Regions"], ["All years"]


def get_forecast(model_type, category, region, year, steps):
    params = dict(model_type=model_type, category=category,
                  region=region, year=year, steps=steps)
    try:
        r = requests.get(f"{API_URL}/sales/forecast",
                         params=params, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Error consultando /sales/forecast: {e}")
        return None


@st.cache_data(ttl=600)
def get_eval(model_type, category, region, year):
    params = dict(model_type=model_type, category=category,
                  region=region, year=year)
    try:
        r = requests.get(f"{API_URL}/sales/evaluation",
                         params=params, timeout=20)
        r.raise_for_status()
        return r.json()
    except:
        return None


@st.cache_data(ttl=600)
def get_kpis(category, region, year):
    params = dict(category=category, region=region, year=year)
    try:
        r = requests.get(f"{API_URL}/sales/kpis", params=params, timeout=20)
        r.raise_for_status()
        return r.json()
    except:
        return None


# ---------- UI ----------
st.title("🚀 Dashboard de Planificación de Demanda v2.3")
st.caption(f"API: {API_URL}")
st.markdown(
    "Comparativa **SARIMA vs XGBoost** y visualización de **KPIs**. Filtros: *Categoría, Región, Año*.")

# Botón para probar salud del API
colh1, colh2 = st.columns([1, 3])
if colh1.button("Probar API /health"):
    try:
        r = requests.get(f"{API_URL}/health", timeout=5)
        if r.ok:
            st.success(r.json())
        else:
            st.warning(f"Health respondió: {r.status_code}")
    except Exception as e:
        st.error(f"No se pudo contactar al API: {e}")

st.sidebar.header("Filtros")
CATEGORIES, REGIONS, YEARS = get_filters()

model = st.sidebar.radio(
    "Modelo:",
    ['sarima', 'xgboost'],
    format_func=lambda x: "SARIMA (Estadístico)" if x == 'sarima' else "XGBoost (Machine Learning)"
)
category = st.sidebar.selectbox('Categoría:', CATEGORIES, index=0)
region = st.sidebar.selectbox('Región:', REGIONS, index=0)
year = st.sidebar.selectbox('Año:', YEARS, index=0)
steps = st.sidebar.slider('Horizonte (Meses):', 6, 36, 12, 1)

tab_forecast, tab_kpis = st.tabs(["📈 Pronóstico", "📊 KPIs"])

with tab_forecast:
    if st.button("Generar Pronóstico"):
        with st.spinner("Generando..."):
            ev = get_eval(model, category, region, year)
            res = get_forecast(model, category, region, year, steps)

        st.subheader(
            f"Precisión del Modelo: {'SARIMA' if model == 'sarima' else 'XGBoost'}")
        st.caption("Backtest sobre los últimos 12 meses del histórico filtrado")
        if ev:
            if ev.get("status") == "Success":
                c1, c2 = st.columns(2)
                c1.metric(
                    "MAPE", f"{ev['mape']:.2f} %", help="Error promedio porcentual (más bajo, mejor)")
                c2.metric(
                    "RMSE", f"$ {ev['rmse']:,.2f}", help="Error cuadrático medio (más bajo, mejor)")
            else:
                st.warning(
                    ev.get("message", "Datos insuficientes o no disponibles."))
        else:
            st.info("No fue posible calcular métricas (¿datos insuficientes?).")

        if res:
            if res.get("status") == "success":
                hist = pd.DataFrame(res["history"])
                hist['Date'] = pd.to_datetime(hist['index'])
                hist = hist.set_index('Date').rename(
                    columns={'data': 'Ventas Históricas'})

                fc = pd.DataFrame(res["forecast"])
                fc['Date'] = pd.to_datetime(fc['Date'])
                fc = fc.set_index('Date').rename(
                    columns={'Sales Forecast': 'Pronóstico'})

                st.subheader("Serie Temporal")
                st.line_chart(
                    pd.concat([hist['Ventas Históricas'], fc['Pronóstico']], axis=1))

                st.subheader("Tabla del Pronóstico (primeros 12 meses)")
                st.dataframe(
                    pd.DataFrame(res["forecast"]).head(12).style.format({
                        'Sales Forecast': '${:,.2f}',
                        'Lower Bound': '${:,.2f}',
                        'Upper Bound': '${:,.2f}'
                    }, na_rep='-')
                )
            else:
                st.warning(
                    res.get("message", "No se pudo generar el pronóstico."))
        else:
            st.error("Error desconocido al consultar el pronóstico.")
    else:
        st.info("Selecciona filtros y haz clic en **Generar Pronóstico**.")

with tab_kpis:
    st.subheader("Indicadores Clave")
    k = get_kpis(category, region, year)
    if not k or k.get("status") != "success":
        st.warning("No fue posible obtener KPIs con los filtros actuales.")
    else:
        c1, _, _ = st.columns(3)
        c1.metric("Ventas Totales", f"$ {k['total_sales']:,.2f}")

        st.markdown("### Ventas por Región")
        df_r = pd.DataFrame(k["by_region"])
        if not df_r.empty:
            st.bar_chart(df_r.set_index("Region").rename(
                columns={'Sales': 'Ventas ($)'}))
            st.dataframe(df_r.rename(columns={'Sales': 'Ventas ($)'}).style.format(
                {'Ventas ($)': '${:,.2f}'}))
        else:
            st.info("Sin datos por región.")

        st.markdown("### Ventas por Año")
        df_y = pd.DataFrame(k["by_year"])
        if not df_y.empty:
            df_y = df_y.rename(
                columns={'Sales': 'Ventas', 'Year': 'Año'}).set_index('Año')
            st.bar_chart(df_y)
            st.dataframe(df_y.style.format({'Ventas': '${:,.2f}'}))
        else:
            st.info("Sin datos por año.")
