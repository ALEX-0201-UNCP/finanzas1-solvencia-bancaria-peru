# Nombres y apellidos: Chancha Santiago Alex Omar
# Código de matrícula: 2024200492K
# Tema N.º 9: Solvencia bancaria en el Perú — ratio de capital global y APR
# Fecha de extracción: 2026-09-26
#
# 02_scraping_web.py  (v2)
# Cambios respecto a v1:
#   - Marzo usa la abreviatura "ma" (la SBS NO usa "mr"; con "mr" los 8 marzos
#     daban HTTP 404 y el panel quedaba con 88 meses en lugar de 96).
#   - Rutas absolutas a partir de la carpeta del proyecto: el script funciona
#     sin importar desde qué carpeta se ejecute.
#   - Si un archivo ya existe en datos_crudos, no se vuelve a descargar
#     (al re-ejecutar solo se piden los meses que faltan).

import requests
import os
import time

headers = {"User-Agent": "Mozilla/5.0 (investigacion academica UNCP - Finanzas I - Chancha Santiago Alex Omar)"}

# Nombre de carpeta y abreviatura de archivo por mes, tal como usa la SBS
MESES = {
    1: ("Enero", "en"), 2: ("Febrero", "fe"), 3: ("Marzo", "ma"),
    4: ("Abril", "ab"), 5: ("Mayo", "my"), 6: ("Junio", "jn"),
    7: ("Julio", "jl"), 8: ("Agosto", "ag"), 9: ("Setiembre", "se"),
    10: ("Octubre", "oc"), 11: ("Noviembre", "no"), 12: ("Diciembre", "di"),
}


def obtener_directorio_base():
    """Carpeta base del proyecto (un nivel arriba de /codigo)."""
    try:
        dir_actual = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        dir_actual = os.getcwd()
    if os.path.basename(dir_actual).lower() == "codigo":
        return os.path.dirname(dir_actual)
    return dir_actual


DIR_BASE = obtener_directorio_base()
RUTA_LOG = os.path.join(DIR_BASE, "log_ejecucion.txt")

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


def descargar_reporte(codigo_reporte: str, carpeta_destino: str, nombre_variable: str):
    """Descarga los 96 meses de un reporte de la SBS dado su código (ej. 'B-2402').
    Los archivos que ya existen localmente se conservan y no se vuelven a pedir."""
    os.makedirs(carpeta_destino, exist_ok=True)
    exitosos, fallidos, ya_existentes = 0, 0, 0

    with open(RUTA_LOG, "a", encoding="utf-8") as log:
        for anio, mes in meses_a_descargar:
            nombre_carpeta, abrev = MESES[mes]
            nombre_archivo = f"{codigo_reporte}-{abrev}{anio}.XLS"
            url = f"https://intranet2.sbs.gob.pe/estadistica/financiera/{anio}/{nombre_carpeta}/{nombre_archivo}"
            ruta_local = os.path.join(carpeta_destino, nombre_archivo)

            if os.path.exists(ruta_local) and os.path.getsize(ruta_local) > 1000:
                ya_existentes += 1
                continue

            try:
                resp = requests.get(url, headers=headers, timeout=30)
                if resp.status_code == 200 and len(resp.content) > 1000:
                    with open(ruta_local, "wb") as f:
                        f.write(resp.content)
                    print(f"OK  [{nombre_variable}] {anio}-{mes:02d} | HTTP {resp.status_code} | {len(resp.content)} bytes")
                    log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {url} | HTTP {resp.status_code} | OK\n")
                    exitosos += 1
                else:
                    print(f"FALLO [{nombre_variable}] {anio}-{mes:02d} | HTTP {resp.status_code}")
                    log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {url} | HTTP {resp.status_code} | FALLO\n")
                    fallidos += 1
            except Exception as e:
                print(f"ERROR [{nombre_variable}] {anio}-{mes:02d} | {e}")
                log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {url} | ERROR: {e}\n")
                fallidos += 1

            time.sleep(1)  # pausa mínima obligatoria entre solicitudes

    print(f"\n[{nombre_variable}] {exitosos} descargados ahora, {ya_existentes} ya existían, "
          f"{fallidos} fallidos (de {total_meses} meses).\n")
    return exitosos, fallidos


# ============================================================
# REPORTE 1: Ratio de Capital Global y APR
# ============================================================
descargar_reporte(
    codigo_reporte="B-2402",
    carpeta_destino=os.path.join(DIR_BASE, "datos_crudos", "sbs_ratio_capital_global"),
    nombre_variable="Ratio de Capital Global / APR",
)

# ============================================================
# REPORTE 2: Balance General y Estado de Ganancias y Pérdidas -> ROE
# ============================================================
descargar_reporte(
    codigo_reporte="B-2201",
    carpeta_destino=os.path.join(DIR_BASE, "datos_crudos", "sbs_roe"),
    nombre_variable="ROE (Estado de Ganancias y Pérdidas)",
)

# ============================================================
# REPORTE 3: Morosidad según tipo y modalidad de crédito -> Cartera Atrasada
# ============================================================
descargar_reporte(
    codigo_reporte="B-2362",
    carpeta_destino=os.path.join(DIR_BASE, "datos_crudos", "sbs_cartera_atrasada"),
    nombre_variable="Cartera Atrasada (Morosidad por tipo y modalidad)",
)
