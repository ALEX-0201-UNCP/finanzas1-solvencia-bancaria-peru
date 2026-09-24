# Nombres y apellidos: Chancha Santiago Alex Omar
# Código de matrícula: 2024200492K
# Tema N.º 9: Solvencia bancaria en el Perú — ratio de capital global y APR
# Fecha de extracción: 2026-09-23

import requests
import pandas as pd
import os

FECHA_INICIO = 2000
FECHA_CORTE = 2025
PAIS = "PER"
INDICADOR = "GFDD.SI.05"  # Bank regulatory capital to risk-weighted assets (%)

# Ruta relativa: sube un nivel desde /codigo hasta /Carpeta_N3..., y entra a /datos_crudos
CARPETA_DATOS_CRUDOS = "../datos_crudos"
os.makedirs(CARPETA_DATOS_CRUDOS, exist_ok=True)

url = f"https://api.worldbank.org/v2/country/{PAIS}/indicator/{INDICADOR}"
params = {"format": "json", "date": f"{FECHA_INICIO}:{FECHA_CORTE}", "per_page": 100}

resp = requests.get(url, params=params, timeout=30)
resp.raise_for_status()
data = resp.json()[1]

df = pd.DataFrame([{
    "pais": d["country"]["value"],
    "anio": d["date"],
    "ratio_capital_global_bm": d["value"]
} for d in data])

ruta_salida = os.path.join(CARPETA_DATOS_CRUDOS, "datos_crudos_2024200492K_bancomundial.csv")
df.to_csv(ruta_salida, index=False)

print(f"Filas descargadas: {len(df)} | Código HTTP: {resp.status_code}")
print(f"Archivo guardado en: {os.path.abspath(ruta_salida)}")
print(df.head(10))