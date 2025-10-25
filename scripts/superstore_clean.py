import pandas as pd


# TODO Función para verificar valores nulos en el DataFrame

def verificar_nulos(df):
    """
    Verifica y muestra la cantidad de valores nulos por columna.

    Parámetros:
    df (pd.DataFrame): DataFrame a verificar.

    Retorna:
    pd.DataFrame con el conteo y el porcentaje de nulos por columna.
    Se deberá ejecutar la impresión de las columnas que tienen nulos
    dependiendo del resultado retornado.
    """
    total_nulos = df.isnull().sum()
    porcentaje_nulos = (total_nulos / len(df)) * 100

    resumen = pd.DataFrame({
        'Total Nulos': total_nulos,
        'Porcentaje (%)': porcentaje_nulos.round(2)
    })

    # Mostrar solo columnas que tengan algún nulo
    resumen = resumen[resumen['Total Nulos'] > 0].sort_values(
        by='Total Nulos', ascending=False)

    if resumen.empty:
        print("No se encontraron valores nulos en el DataFrame.")
    else:
        print("Se encontraron valores nulos en las siguientes columnas:")
    return resumen


# TODO Función para renombrar columnas del DataFrame

def renombrar_columnas(df, nuevos_nombres):
    """
    Renombra columnas del DataFrame según un diccionario de equivalencias.

    Parámetros:
    df (pd.DataFrame): DataFrame original.
    nuevos_nombres (dict): Diccionario con formato {'columna_actual': 'nuevo_nombre'}.

    Retorna:
    pd.DataFrame con las columnas renombradas.
    """
    df = df.copy()
    df.rename(columns=nuevos_nombres, inplace=True)
    print("Columnas renombradas correctamente.")
    print("Nuevas columnas:", df.columns.tolist())
    return df


# TODO Función para convertir a mayúsculas el texto de columnas específicas
def convertir_a_mayusculas(df):
    """
    Convierte a mayúsculas el texto de las columnas indicadas.

    Parámetros:
    df (pd.DataFrame): DataFrame con los datos.
    columnas (list): Lista con los nombres de las columnas a transformar.

    Retorna:
    pd.DataFrame con las columnas convertidas a mayúsculas.
    """
    df = df.copy()
    texto_cols = df.select_dtypes(include=["object", "string"]).columns
    for col in texto_cols:
        df[col] = df[col].astype(str).str.strip().str.replace(
            r"\s+", " ", regex=True).str.upper()
    print(f"Se convirtieron a mayúsculas las columnas: {list(texto_cols)}")
    print(df.head(3))
    return df


# TODO Función para ordenar y formatear una columna de fecha
def ordenar_y_formatear_fecha(df, columna_fecha):
    """
    Ordena un DataFrame por una columna de fecha y la convierte al formato 'YYYY-MM-DD'.

    Parámetros:
    df (pd.DataFrame): DataFrame que contiene la columna de fecha.
    columna_fecha (str): Nombre de la columna de fecha a ordenar.

    Retorna:
    pd.DataFrame: DataFrame ordenado y con la fecha formateada como texto.
    """
    df = df.copy()

    # Verificar que la columna exista
    print(f"Verificando si la columna '{columna_fecha}' existe en el DataFrame.")
    if columna_fecha not in df.columns:
        raise ValueError(
            f"La columna '{columna_fecha}' no existe en el DataFrame.")

    # Convertir a datetime si aún no lo es
    if not pd.api.types.is_datetime64_any_dtype(df[columna_fecha]):
        df[columna_fecha] = pd.to_datetime(
            df[columna_fecha], errors="coerce", dayfirst=True)

    # Ordenar por la fecha
    df = df.sort_values(by=columna_fecha, ascending=True)

    # Crear una versión formateada Y-M-d (año-mes-día)
    df[columna_fecha] = df[columna_fecha].dt.strftime("%Y-%m-%d")
    print(f"Columna '{columna_fecha}' ordenada y formateada correctamente.")

    return df.reset_index(drop=True)
