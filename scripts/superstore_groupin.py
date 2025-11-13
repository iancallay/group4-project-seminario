import pandas as pd
import locale


def _asegurar_derive_fecha(df, col_fecha="Order_Date"):
    """Crea columnas cod_anio, cod_mes, cod_dia, nom_mes, nom_dia si no existen."""
    df = df.copy()

    # Order_Date a datetime
    if col_fecha not in df.columns:
        raise ValueError(
            f"La columna '{col_fecha}' no existe en el DataFrame.")
    if not pd.api.types.is_datetime64_any_dtype(df[col_fecha]):
        df[col_fecha] = pd.to_datetime(df[col_fecha], errors="coerce")

    # Locale para nombres en español (si está disponible)
    try:
        locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")
    except:
        try:
            locale.setlocale(locale.LC_TIME, "es_ES")
        except:
            pass

    # Derivadas si faltan
    if "cod_anio" not in df.columns:
        df["cod_anio"] = df[col_fecha].dt.year.astype("Int64")
    if "cod_mes" not in df.columns:
        df["cod_mes"] = df[col_fecha].dt.month.astype("Int64")
    if "cod_dia" not in df.columns:
        df["cod_dia"] = df[col_fecha].dt.day.astype("Int64")
    if "nom_mes" not in df.columns:
        df["nom_mes"] = df[col_fecha].dt.strftime(
            "%B").str.capitalize().astype("string")
    if "nom_dia" not in df.columns:
        df["nom_dia"] = df[col_fecha].dt.strftime(
            "%A").str.capitalize().astype("string")

    # Soporte para trimestre / llaves compuestas
    df["trimestre"] = df[col_fecha].dt.quarter.astype("Int64")
    df["anio_trimestre"] = (df["cod_anio"].astype(
        "string") + "-Q" + df["trimestre"].astype("string"))
    df["anio_mes"] = df[col_fecha].dt.to_period(
        "M").astype(str)  # p.ej. 2014-01

    return df


def agrupar_ventas(df, nivel="semanal", por=["Region", "Category"], col_fecha="Order_Date"):
    """
    Agrupa las ventas por fecha y dimensiones adicionales.

    Parámetros
    ----------
    df : pd.DataFrame
    nivel : str
        'diario' | 'semanal' | 'mensual' | 'anio' | 'trimestre' |
        'anio_trimestre' | 'anio_mes' | 'nom_mes' | 'nom_dia'
    por : list[str]
        Columnas adicionales para agrupar.
    col_fecha : str
        Nombre de la columna de fecha.

    Retorna
    -------
    pd.DataFrame agrupado con métricas: Sales, Quantity, Profit, Discount_mean,
    Avg_Price, Profit_Margin.
    """
    df = _asegurar_derive_fecha(df.copy(), col_fecha)

    # Selección de llave temporal
    if nivel == "diario":
        key_time = pd.Grouper(key=col_fecha, freq="D")
    elif nivel == "semanal":
        # semana anclada a lunes
        key_time = pd.Grouper(key=col_fecha, freq="W-MON")
    elif nivel == "mensual":
        key_time = pd.Grouper(key=col_fecha, freq="M")
    elif nivel == "anio":
        key_time = "cod_anio"
    elif nivel == "trimestre":
        key_time = "trimestre"
    elif nivel == "anio_trimestre":
        key_time = "anio_trimestre"
    elif nivel == "anio_mes":
        key_time = "anio_mes"
    elif nivel == "nom_mes":
        key_time = "nom_mes"
    elif nivel == "nom_dia":
        key_time = "nom_dia"
    else:
        raise ValueError(
            "nivel inválido. Usa: 'diario','semanal','mensual','anio',"
            "'trimestre','anio_trimestre','anio_mes','nom_mes','nom_dia'"
        )

    # Validar columnas "por"
    por = [c for c in (por or []) if c in df.columns]

    # Agrupar
    agg_base = (
        df.groupby(por + [key_time])
          .agg(
              Sales=("Sales", "sum"),
              Quantity=("Quantity", "sum"),
              Profit=("Profit", "sum"),
              Discount_mean=("Discount", "mean"),
        )
        .reset_index()
    )

    # KPIs derivados
    agg_base["Avg_Price"] = (
        agg_base["Sales"] / agg_base["Quantity"]).replace([pd.NA, pd.NaT], 0)
    agg_base["Profit_Margin"] = (
        agg_base["Profit"] / agg_base["Sales"]).replace([pd.NA, pd.NaT], 0)

    # Ordenar por tiempo si corresponde
    if isinstance(key_time, pd.Grouper):
        agg_base = agg_base.sort_values(by=[col_fecha] + por)
    elif key_time in {"cod_anio", "trimestre", "cod_mes", "cod_dia"}:
        agg_base = agg_base.sort_values(by=[key_time] + por)
    elif key_time in {"anio_trimestre", "anio_mes"}:
        agg_base = agg_base.sort_values(by=[key_time] + por)
    # para 'nom_mes' / 'nom_dia' mantenemos el orden alfabético

    print(
        f"Datos agrupados por {por} con nivel '{nivel}'. Total filas: {len(agg_base)}")
    return agg_base
