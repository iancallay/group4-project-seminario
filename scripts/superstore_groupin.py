import pandas as pd

def agrupar_ventas(df, nivel="semanal", por=["Region", "Category"]):
    """
    Agrupa las ventas del dataset Superstore por fecha y otras dimensiones (ej. categoría, región).

    Parámetros:
    -----------
    df : pd.DataFrame
        DataFrame limpio con columna 'Order_Date' en formato datetime.
    nivel : str
        Nivel de frecuencia temporal ('diario', 'semanal', 'mensual').
    por : list
        Columnas adicionales por las que se desea agrupar (ej. ['Category', 'Region']).

    Retorna:
    --------
    df_group : pd.DataFrame
        DataFrame agrupado con columnas: fecha, sumas de ventas, cantidad, profit, etc.
    """
    df = df.copy()

    # Validar que la columna 'Order_Date' exista y sea datetime
    if "Order_Date" not in df.columns:
        raise ValueError("La columna 'Order_Date' no existe en el DataFrame.")
    if not pd.api.types.is_datetime64_any_dtype(df["Order_Date"]):
        df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")

    # Seleccionar frecuencia temporal
    if nivel == "diario":
        freq = "D"
    elif nivel == "semanal":
        freq = "W"
    elif nivel == "mensual":
        freq = "M"
    else:
        raise ValueError("El parámetro 'nivel' debe ser: 'diario', 'semanal' o 'mensual'.")

    # Agrupar por fecha + columnas adicionales
    df_group = (
        df.groupby(por + [pd.Grouper(key="Order_Date", freq=freq)])
        .agg({
            "Sales": "sum",
            "Quantity": "sum",
            "Profit": "sum",
            "Discount": "mean"
        })
        .reset_index()
        .sort_values(by="Order_Date")
    )

    print(f"Datos agrupados por {por} con frecuencia {nivel}. Total filas: {len(df_group)}")
    return df_group
