# TODO libreria os para compatibilidad de rutas entre sistemas operativos
import os

# TODO libreria sys para manejo de rutas de importacion de modulos
import sys
import pandas as pd

from scripts.data_loader import DATA_PATH, cargar_datos_excel
from scripts.superstore_clean import (
    convertir_a_mayusculas,
    ordenar_y_formatear_fecha,
    renombrar_columnas,
    verificar_nulos,
    agregar_columnas_fecha
)

from scripts.superstore_saving import guardar_datos_limpios
from scripts.superstore_preparation import preparar_datos_para_analisis
from scripts.superstore_groupin import agrupar_ventas
# -----------------------------------------------------------
# Importar módulos del proyecto
# -----------------------------------------------------------
# Agregar la carpeta "scripts" al path para poder importar desde allí

sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

# Importar tus módulos

# -----------------------------------------------------------
# Configuración de rutas
# -----------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "processed", "superstore_clean.csv")
columnas_actuales = {
    "Row ID": "Row_Id",
    "Order ID": "Order_Id",
    "Order Date": "Order_Date",
    "Ship Date": "Ship_Date",
    "Ship Mode": "Ship_Mode",
    "Customer ID": "Customer_Id",
    "Customer Name": "Customer_Name",
    "Segment": "Segment",
    "Country": "Country",
    "City": "City",
    "State": "State",
    "Postal Code": "Postal_Code",
    "Region": "Region",
    "Product ID": "Product_Id",
    "Category": "Category",
    "Sub-Category": "Sub_Category",
    "Product Name": "Product_Name",
    "Sales": "Sales",
    "Quantity": "Quantity",
    "Discount": "Discount",
    "Profit": "Profit"
}

if __name__ == "__main__":
    # Cargar los datos
    print("Cargando datos {DATA_PATH} ...")
    df_superstore = cargar_datos_excel(DATA_PATH)

    # Verificar valores nulos
    resumen_nulos = verificar_nulos(df_superstore)
    print(resumen_nulos)
    
    # Renombrar columnas
    print("Renombrando columnas para evitar espacios ...")
    df_superstore_renamed = renombrar_columnas(df_superstore, columnas_actuales)
    # print(df_superstore.columns)
    
    # Convertir a mayúsculas el texto de todas las columnas de tipo texto
    df_superstore_upper = convertir_a_mayusculas(df_superstore_renamed)
    
    # Ordenar y formatear la columna de fecha 'Order_Date'
    df_superstore_order_date = ordenar_y_formatear_fecha(df_superstore_upper, 'Order_Date')
    
    df_agregar_columnas = agregar_columnas_fecha(df_superstore_order_date, columna_fecha="Order_Date")

    
    df_final = preparar_datos_para_analisis(df_agregar_columnas)
    print(df_final.columns)
    
    
    df_grouped = agrupar_ventas(df_final, nivel="mensual", por=["Region", "Category"])
    print(df_grouped.head(5))
    
    # Guardar los datos limpios
    guardar_datos_limpios(df_final, OUTPUT_PATH)