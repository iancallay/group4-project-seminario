import os
import subprocess
import time

# --- Configuración ---
HOST = "127.0.0.1"
PORT = 8000

# --- Asegurar variable PYTHONPATH ---
os.environ["PYTHONPATH"] = os.getcwd()

# --- Comando para FastAPI ---
api_cmd = f"uvicorn api_service:app --reload --host {HOST} --port {PORT}"

# --- Comando para Streamlit ---
streamlit_cmd = "streamlit run app.py"

# --- Ejecutar FastAPI en segundo plano ---
print(f"🚀 Iniciando FastAPI en http://{HOST}:{PORT} ...")
api_process = subprocess.Popen(api_cmd, shell=True)

# --- Esperar unos segundos ---
time.sleep(3)

# --- Ejecutar Streamlit ---
print("🚀 Iniciando Streamlit...")
subprocess.call(streamlit_cmd, shell=True)

# --- Cerrar FastAPI cuando Streamlit termine ---
api_process.terminate()
