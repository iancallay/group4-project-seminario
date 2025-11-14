import os
import pandas as pd

# --- Rutas ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
# FILE_PATH = os.path.join(PROJECT_ROOT, 'data', 'US Superstore data.xls')
FILE_PATH = os.path.join(PROJECT_ROOT, 'data',
                         'processed', 'superstore_clean.csv')


def load_data():
    """Carga y preprocesa el dataset."""
    try:
        # df = pd.read_excel(FILE_PATH)
        df = pd.read_csv(FILE_PATH)
        df = df.copy()
        # Normaliza nombres de columnas (espacios y guiones)
        df.columns = df.columns.str.replace(' ', '_').str.replace('-', '_')
        # Normaliza fechas
        df['Order_Date'] = pd.to_datetime(df['Order_Date'])
        return df, "Success"
    except FileNotFoundError:
        return None, f"Archivo no encontrado: {FILE_PATH}"
    except Exception as e:
        return None, f"Error al cargar datos: {e}"


def list_years(df):
    """Lista de años disponibles en el dataset."""
    return sorted(df['Order_Date'].dt.year.unique().tolist())


def _apply_filters(df, category="All Categories", region="All Regions", year="All years"):
    """Aplica filtros básicos al dataframe."""
    dff = df.copy()
    if category != "All Categories":
        dff = dff[dff['Category'] == category]
    if region != "All Regions":
        dff = dff[dff['Region'] == region]
    if year != "All years":
        dff = dff[dff['Order_Date'].dt.year == int(year)]
    return dff


def aggregate_sales(df, category="All Categories", region="All Regions", year="All years"):
    """
    Filtra y agrega ventas a frecuencia mensual (MS: Month Start).
    Devuelve: (pd.Series, bool) -> serie mensual y bandera de éxito.
    """
    if df is None:
        return pd.Series(dtype='float64'), False

    dff = _apply_filters(df, category, region, year)
    if dff.empty:
        return pd.Series(dtype='float64'), False

    dff = dff.set_index('Order_Date')
    ts_monthly = dff['Sales'].resample('MS').sum()
    return ts_monthly, True


def kpis(df, category="All Categories", region="All Regions", year="All years"):
    """
    KPIs: ventas totales, por región y por año (con filtros básicos).
    Retorna dict con:
      - total_sales: float
      - by_region: [{Region, Sales}]
      - by_year: [{Year, Sales}]
    """
    if df is None:
        return {"total_sales": 0, "by_region": [], "by_year": []}

    dff = _apply_filters(df, category, region, year)
    if dff.empty:
        return {"total_sales": 0, "by_region": [], "by_year": []}

    total_sales = float(dff['Sales'].sum())

    by_region = (
        dff.groupby('Region', as_index=False)['Sales'].sum()
        .sort_values('Sales', ascending=False)
    )

    by_year = (
        dff.assign(Year=dff['Order_Date'].dt.year)
           .groupby('Year', as_index=False)['Sales'].sum()
           .sort_values('Year')
    )

    return {
        "total_sales": round(total_sales, 2),
        "by_region": by_region.to_dict(orient='records'),
        "by_year": by_year.to_dict(orient='records')
    }


def create_features_for_ml(ts_data):
    """
    Crea features tabulares a partir de una serie mensual:
      - month, quarter, year
      - lag_12
    Devuelve X (features) e y (target).
    """
    df = pd.DataFrame(ts_data.copy())
    df.columns = ['Sales']

    # Features calendario
    df['month'] = df.index.month
    df['quarter'] = df.index.quarter
    df['year'] = df.index.year

    # Rezago de 12 meses
    df['lag_12'] = df['Sales'].shift(12)

    # Completar NaN del lag de los primeros 12 puntos
    df = df.bfill()

    X = df.drop(columns=['Sales'])
    y = df['Sales']
    return X, y
