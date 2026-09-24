# Nombres y apellidos: Chancha Santiago Alex Omar
# Código de matrícula: 2024200492K
# Tema N.º 9: Solvencia bancaria en el Perú — ratio de capital global y APR
# Fecha de extracción: 2026-09-23

import requests
import os
import time

headers = {"User-Agent": "Mozilla/5.0 (investigacion academica UNCP - Finanzas I - Chancha Santiago Alex Omar)"}

# Nombre completo de carpeta y abreviatura de archivo por mes, tal como usa la SBS
MESES = {
    1: ("Enero", "en"), 2: ("Febrero", "fe"), 3: ("Marzo", "mr"),
    4: ("Abril", "ab"), 5: ("Mayo", "my"), 6: ("Junio", "jn"),
    7: ("Julio", "jl"), 8: ("Agosto", "ag"), 9: ("Setiembre", "se"),
    10: ("Octubre", "oc"), 11: ("Noviembre", "no"), 12: ("Diciembre", "di"),
}

CARPETA_DATOS_CRUDOS = "../datos_crudos/sbs_ratio_capital_global"
os.makedirs(CARPETA_DATOS_CRUDOS, exist_ok=True)

CARPETA_LOG = "../log_ejecucion.txt"

# Últimos 96 meses (8 años) contados hacia atrás desde diciembre 2025
ANIO_FIN, MES_FIN = 2025, 12
total_meses = 96

meses_a_descargar = []
anio, mes = ANIO_FIN, MES_FIN
for _ in range(total_meses):
    meses_a_descargar.append((anio, mes))
    mes -= 1
    if mes == 0:
        mes = 12
        anio -= 1

exitosos, fallidos = 0, 0

with open(CARPETA_LOG, "a", encoding="utf-8") as log:
    for anio, mes in meses_a_descargar:
        nombre_carpeta, abrev = MESES[mes]
        url = f"https://intranet2.sbs.gob.pe/estadistica/financiera/{anio}/{nombre_carpeta}/B-2402-{abrev}{anio}.XLS"
        nombre_archivo = f"B-2402-{abrev}{anio}.XLS"
        ruta_local = os.path.join(CARPETA_DATOS_CRUDOS, nombre_archivo)

        try:
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code == 200 and len(resp.content) > 1000:
                with open(ruta_local, "wb") as f:
                    f.write(resp.content)
                print(f"OK  {anio}-{mes:02d} | HTTP {resp.status_code} | {len(resp.content)} bytes")
                log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {url} | HTTP {resp.status_code} | OK\n")
                exitosos += 1
            else:
                print(f"FALLO {anio}-{mes:02d} | HTTP {resp.status_code}")
                log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {url} | HTTP {resp.status_code} | FALLO\n")
                fallidos += 1
        except Exception as e:
            print(f"ERROR {anio}-{mes:02d} | {e}")
            log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {url} | ERROR: {e}\n")
            fallidos += 1

        time.sleep(1)  # pausa mínima obligatoria entre solicitudes

print(f"\nTotal: {exitosos} descargas exitosas, {fallidos} fallidas de {total_meses} intentadas.")