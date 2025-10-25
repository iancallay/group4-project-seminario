import pandas as pd

def preparar_datos_para_analisis(df):
    """
    Filtra las columnas más útiles del dataset Superstore y 
    deja el DataFrame listo para análisis o modelos predictivos.

    Parámetros:
    -----------
    df : pd.DataFrame
        DataFrame original con todas las columnas del dataset Superstore.

    Retorna:
    --------
    df_modelo : pd.DataFrame
        DataFrame con las columnas más relevantes para análisis de ventas.
    """

    # Columnas relevantes para análisis de ventas y pronóstico
    columnas_utiles = [
        "Order_Date",
        "Category",
        "Sub_Category",
        "Region",
        "State",
        "City",
        "Sales",
        "Profit",
        "Quantity",
        "Discount"
    ]

    # 🔹 Verificar qué columnas existen realmente en el DataFrame
    columnas_existentes = [col for col in columnas_utiles if col in df.columns]
    columnas_faltantes = [
        col for col in columnas_utiles if col not in df.columns]

    if columnas_faltantes:
        print(
            f"Advertencia: No se encontraron las columnas {columnas_faltantes} en el DataFrame original.")
    else:
        print("Todas las columnas útiles están presentes.")

    # 🔹 Crear el DataFrame con solo las columnas necesarias
    df_modelo = df[columnas_existentes].copy()

    # 🔹 Convertir fechas al tipo datetime (por si vienen como texto)
    if "Order_Date" in df_modelo.columns:
        df_modelo["Order_Date"] = pd.to_datetime(
            df_modelo["Order_Date"], errors="coerce")

    # 🔹 Eliminar filas con fechas o ventas nulas (no sirven para pronóstico)
    df_modelo = df_modelo.dropna(subset=["Order_Date", "Sales"])

    # 🔹 Asegurar tipos correctos
    numericas = ["Sales", "Profit", "Quantity", "Discount"]
    for col in numericas:
        if col in df_modelo.columns:
            df_modelo[col] = pd.to_numeric(df_modelo[col], errors="coerce")

    print(
        f"Dataset preparado: {df_modelo.shape[0]} filas × {df_modelo.shape[1]} columnas útiles.\n")
    return df_modelo
