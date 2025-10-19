#%%
import pandas as pd
# TODO For file path operations without needing to import additional libraries in different environments Windows, Linus ux, MacOS
import os 

# TODO ruta absoluta de la carpeta donde esta el script (../script)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# TODO ruta absoluta de la carpeta data (../data)
DATA_PATH = os.path.join(SCRIPT_DIR, '..', 'data', "US_0Superstore_data.xls")

# TODO crear la funcion load_data
def cargar_datos(path):
    print(f"Cargando datos desde {path}...")
    
    try:
        df = pd.read_excel(path)
        print("Datos cargados exitosamente.")
        return df
    except FileNotFoundError:
        print(f"Error: El archivo en la ruta {path} no fue encontrado.")
        print("Asegurate de tener el arvchivo en la carpeta 'data'.")
        print("También puedes verifica que la ruta sea la correcta.")  
        return None
    except Exception as e:
        print(f"Error al cargar los datos: {e}")
        return None

# TODO Este archivo se esta ejecutando directamente por el usuario o esta siendo importado por otro script?
if __name__ == "__main__":        
    print(f"Ejecutando el script desde: {SCRIPT_DIR}")
    dataframe_matriz = cargar_datos(DATA_PATH)
    if dataframe_matriz is not None:
        print("\nPrimeras filas del DataFrame cargado:")
        print(dataframe_matriz.head())
        print("\nInformación del DataFrame:")
        dataframe_matriz.info()
# %%
