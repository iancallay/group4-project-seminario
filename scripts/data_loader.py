import pandas as pd
# TODO For file path operations without needing to import additional libraries in different environments Windows, Linus ux, MacOS
import os 

# TODO ruta absoluta de la carpeta donde esta el script (../script)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# TODO ruta absoluta de la carpeta data (../data)
DATA_PATH = os.path.join(SCRIPT_DIR, '..', 'data', "US_Superstore_data.xls")

# TODO crear la funcion load_data
def cargar_datos_excel(path):
    print(f"Cargando datos desde {path}...")
    
    try:
        df = pd.read_excel(path)
        print("Datos cargados exitosamente.")
        return df
    except FileNotFoundError:
        print(f"Error: El archivo en la ruta {path} no fue encontrado.")
        return None
    except Exception as e:
        print(f"Error al cargar los datos: {e}")
        return None

