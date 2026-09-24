# Nombres y apellidos: Chancha Santiago Alex Omar
# Código de matrícula: 2024200492K
# Tema N.º 9: Solvencia bancaria en el Perú — ratio de capital global y APR
# Fecha de extracción: 2026-09-23

import requests
import pandas as pd
import os
import time

FECHA_INICIO = 2000
FECHA_CORTE = 2025
PAIS = "PER"

# Indicadores GFDD (Global Financial Development Database, Banco Mundial)
INDICADORES = {
    "GFDD.SI.05": "ratio_capital_global",        # Bank regulatory capital to risk-weighted assets (%)
    "GFDD.SI.03": "capital_sobre_activos",        # Bank capital to total assets (%) -> proxy de patrimonio efectivo
    "GFDD.SI.02": "cartera_atrasada",             # Bank nonperforming loans to gross loans (%)
    "GFDD.EI.05": "roa",                          # Bank return on assets (%)
    "GFDD.EI.06": "roe",                          # Bank return on equity (%)
}

CARPETA_DATOS_CRUDOS = "../datos_crudos"
os.makedirs(CARPETA_DATOS_CRUDOS, exist_ok=True)

df_final = None

for codigo, nombre_col in INDICADORES.items():
    url = f"https://api.worldbank.org/v2/country/{PAIS}/indicator/{codigo}"
    params = {"format": "json", "date": f"{FECHA_INICIO}:{FECHA_CORTE}", "per_page": 100}

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()[1]

    df_temp = pd.DataFrame([{
        "anio": d["date"],
        nombre_col: d["value"]
    } for d in data])

    print(f"{codigo} ({nombre_col}): {len(df_temp)} filas | HTTP {resp.status_code}")

    if df_final is None:
        df_final = df_temp
    else:
        df_final = df_final.merge(df_temp, on="anio", how="outer")

    time.sleep(1)  # pausa entre solicitudes

df_final["pais"] = "Perú"
df_final = df_final.sort_values("anio").reset_index(drop=True)

ruta_salida = os.path.join(CARPETA_DATOS_CRUDOS, "datos_crudos_2024200492K_bancomundial.csv")
df_final.to_csv(ruta_salida, index=False)

print(f"\nArchivo guardado en: {os.path.abspath(ruta_salida)}")
print(df_final.head(10))