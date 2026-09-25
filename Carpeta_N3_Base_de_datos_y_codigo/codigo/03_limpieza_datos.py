# ============================================================================
# UNIVERSIDAD NACIONAL DEL CENTRO DEL PERÚ
# Facultad de Economía — Escuela Profesional de Economía
# Finanzas I (055D) — Ciclo V — Periodo 2026-II
# ----------------------------------------------------------------------------
# Nombres y apellidos : Chancha Santiago Alex Omar
# Código de matrícula : 2024200492K
# Tema N.º 9 (Unidad I): Solvencia bancaria en el Perú — ratio de capital
#                     global y activos ponderados por riesgo (APR)
# Fecha de extracción : 2026-09-24
# ----------------------------------------------------------------------------
# 03_limpieza_datos.py
#
# Qué hace este script:
#   1. Lee los 88 reportes mensuales (.XLS) descargados de la SBS mediante
#      descarga programática (ver 02_scraping_web.py).
#   2. Detecta automáticamente la columna correcta de cada variable buscando
#      el texto del encabezado (no la posición fija), porque la SBS usó dos
#      formatos distintos de reporte a lo largo del periodo 2018-2025.
#   3. Consolida todo en un panel banco x mes.
#   4. Completa los meses sin reporte disponible mediante interpolación
#      lineal, tal como autorizó el docente del curso.
#   5. Guarda el resultado en datos_procesados/datos_procesados_2024200492K.csv
# ============================================================================

import os
import glob
import pandas as pd


# ============================================================================
# 1. CONFIGURACIÓN DE RUTAS
# ============================================================================

def obtener_directorio_base():
    """Detecta la carpeta base del proyecto (un nivel arriba de /codigo),
    para que el script funcione sin importar desde dónde se ejecute."""
    try:
        dir_actual = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        dir_actual = os.getcwd()
    if os.path.basename(dir_actual).lower() == "codigo":
        return os.path.dirname(dir_actual)
    return dir_actual


DIR_BASE = obtener_directorio_base()
DIR_SBS = os.path.join(DIR_BASE, "datos_crudos", "sbs_ratio_capital_global")
RUTA_SALIDA = os.path.join(DIR_BASE, "datos_procesados", "datos_procesados_2024200492K.csv")

RANGO_FECHAS = pd.date_range(start="2018-01-31", end="2025-12-31", freq="ME")  # 96 meses
MIN_MESES_POR_BANCO = 12  # bancos con menos datos reales que esto se excluyen del panel

COLUMNAS_NUMERICAS = [
    "apr_total",
    "ratio_capital_global_pct",
    "patrimonio_efectivo_nivel1_apr_pct",
    "capital_ordinario_nivel1_apr_pct",
    "patrimonio_efectivo_estimado",
]


# ============================================================================
# 2. FUNCIONES AUXILIARES DE LECTURA Y CONVERSIÓN
# ============================================================================

def convertir_a_float(valor):
    """Convierte un valor de celda de Excel a float, tolerando comas de
    miles y celdas vacías. Devuelve None si no se puede convertir."""
    if pd.isna(valor):
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip().replace(",", "")
    try:
        return float(texto)
    except ValueError:
        return None


def texto_combinado_columna(df_raw, columna, fila_empresas):
    """Une el texto de las filas de encabezado de una columna en un solo
    string. Es necesario porque la SBS a veces parte un título en dos filas."""
    fila_inicio = max(0, fila_empresas - 5)
    texto = ""
    for fila in range(fila_inicio, fila_empresas + 1):
        valor = df_raw.iloc[fila, columna]
        if pd.notna(valor):
            texto += str(valor).upper()
    return texto.replace(" ", "")


def encontrar_columna(df_raw, fila_empresas, texto_buscado):
    """Ubica el índice de columna cuyo encabezado combinado contiene el
    texto buscado por CONTENIDO, no por posición fija."""
    texto_norm = texto_buscado.upper().replace(" ", "")
    for columna in range(df_raw.shape[1]):
        if texto_norm in texto_combinado_columna(df_raw, columna, fila_empresas):
            return columna
    return None


def encontrar_columna_apr_total(df_raw, fila_empresas):
    """Ubica la columna del APR total, adaptándose a los formatos de la SBS."""
    columna_grupo = encontrar_columna(df_raw, fila_empresas, "PONDERADOSPORRIESGO")
    fila_formula = fila_empresas + 1

    if columna_grupo is not None:
        for columna in range(columna_grupo, df_raw.shape[1]):
            formula = str(df_raw.iloc[fila_formula, columna]) if fila_formula < len(df_raw) else ""
            if "=" in formula and formula.count("+") >= 2:
                return columna, False

    # Formato antiguo: primera fórmula de suma total que aparezca
    for columna in range(df_raw.shape[1]):
        formula = str(df_raw.iloc[fila_formula, columna]) if fila_formula < len(df_raw) else ""
        if "=" in formula and formula.count("+") >= 2:
            return columna, True

    return None, False


# ============================================================================
# 3. EXTRACCIÓN DE UN ARCHIVO INDIVIDUAL DE LA SBS
# ============================================================================

def extraer_datos_de_archivo(ruta_archivo):
    """Procesa un archivo .XLS de la SBS y devuelve una lista de diccionarios."""
    df_raw = pd.read_excel(ruta_archivo, sheet_name=0, header=None)

    # --- Ubica la fila de encabezado "EMPRESAS" ---
    fila_empresas = next(
        (r for r in range(min(15, len(df_raw)))
         if str(df_raw.iloc[r, 0]).strip().upper() == "EMPRESAS"),
        None
    )
    if fila_empresas is None:
        raise ValueError("no se encontró la fila de encabezado 'EMPRESAS'")

    # --- Ubica la fecha de corte del reporte ---
    fecha_str = None
    for r in range(min(6, len(df_raw))):
        fecha_parseada = pd.to_datetime(str(df_raw.iloc[r, 0]), errors="coerce")
        if not pd.isna(fecha_parseada):
            fecha_str = fecha_parseada.strftime("%Y-%m-%d")
            break
    if not fecha_str:
        raise ValueError("no se encontró la fecha del reporte")

    # --- Ubica las columnas necesarias ---
    col_apr_total, requiere_x10 = encontrar_columna_apr_total(df_raw, fila_empresas)
    col_ratio_global = encontrar_columna(df_raw, fila_empresas, "RATIODECAPITALGLOBAL")
    col_patrimonio_pct = encontrar_columna(df_raw, fila_empresas, "PATRIMONIOEFECTIVODENIVEL")
    col_capital_ord_pct = encontrar_columna(df_raw, fila_empresas, "CAPITALORDINARIO")

    if col_apr_total is None or col_ratio_global is None:
        raise ValueError("faltan columnas obligatorias (APR total o Ratio de Capital Global)")

    # --- Recorre cada fila de banco hasta llegar al total del sistema ---
    registros_del_mes = []
    for idx in range(fila_empresas + 3, len(df_raw)):
        nombre_banco = str(df_raw.iloc[idx, 0]).strip()

        if not nombre_banco or nombre_banco.lower() == "nan":
            continue
        if any(palabra in nombre_banco.upper() for palabra in ["TOTAL", "SISTEMA", "FUENTE", "NOTA"]):
            break

        apr_crudo = convertir_a_float(df_raw.iloc[idx, col_apr_total])
        apr_total = apr_crudo * 10 if (requiere_x10 and apr_crudo is not None) else apr_crudo
        ratio_global = convertir_a_float(df_raw.iloc[idx, col_ratio_global])

        if apr_total is None or ratio_global is None:
            continue

        patrimonio_pct = convertir_a_float(df_raw.iloc[idx, col_patrimonio_pct]) if col_patrimonio_pct else None
        capital_ord_pct = convertir_a_float(df_raw.iloc[idx, col_capital_ord_pct]) if col_capital_ord_pct else None

        registros_del_mes.append({
            "fecha": fecha_str,
            "banco": nombre_banco,
            "apr_total": apr_total,
            "ratio_capital_global_pct": ratio_global,
            "patrimonio_efectivo_nivel1_apr_pct": patrimonio_pct,
            "capital_ordinario_nivel1_apr_pct": capital_ord_pct,
            "patrimonio_efectivo_estimado": (ratio_global / 100) * apr_total,
        })

    return registros_del_mes


def extraer_panel_completo(directorio_sbs):
    """Recorre todos los archivos .XLS de la SBS y consolida sus registros."""
    archivos = sorted(glob.glob(os.path.join(directorio_sbs, "*.xls*")))
    print(f"Archivos encontrados en la carpeta SBS: {len(archivos)}")

    todos_los_registros = []
    archivos_con_error = []

    for archivo in archivos:
        nombre = os.path.basename(archivo)
        try:
            registros = extraer_datos_de_archivo(archivo)
            todos_los_registros.extend(registros)
        except Exception as error:
            archivos_con_error.append((nombre, str(error)))

    df_panel = pd.DataFrame(todos_los_registros)
    if not df_panel.empty:
        df_panel = df_panel.drop_duplicates(subset=["fecha", "banco"]).reset_index(drop=True)

    print(f"Observaciones reales extraídas : {len(df_panel)}")
    print(f"Archivos con error             : {len(archivos_con_error)} de {len(archivos)}")

    return df_panel, archivos_con_error


# ============================================================================
# 4. COMPLETADO ESTADÍSTICO DE PERIODOS FALTANTES
# ============================================================================

def completar_panel_con_interpolacion(df_panel, rango_fechas, columnas_numericas, min_meses):
    """Reindexa el panel y rellena los huecos por banco mediante interpolación lineal."""
    df_panel = df_panel.copy()
    df_panel["fecha"] = pd.to_datetime(df_panel["fecha"])
    df_panel["fuente_dato"] = "SBS_original"

    conteo_por_banco = df_panel["banco"].value_counts()
    bancos_validos = conteo_por_banco[conteo_por_banco >= min_meses].index

    paneles_por_banco = []
    for banco in bancos_validos:
        df_banco = (
            df_panel[df_panel["banco"] == banco]
            .drop_duplicates(subset="fecha")
            .set_index("fecha")
            .reindex(rango_fechas)
        )
        df_banco["banco"] = banco

        fila_es_nueva = df_banco["fuente_dato"].isna()

        for columna in columnas_numericas:
            df_banco[columna] = df_banco[columna].interpolate(method="linear", limit_direction="both")

        df_banco.loc[fila_es_nueva, "fuente_dato"] = "interpolado"
        df_banco["fuente_dato"] = df_banco["fuente_dato"].fillna("interpolado")

        paneles_por_banco.append(df_banco)

    df_final = pd.concat(paneles_por_banco).reset_index().rename(columns={"index": "fecha"})
    df_final = df_final.dropna(subset=["ratio_capital_global_pct"])

    df_final["fecha"] = df_final["fecha"].dt.strftime("%Y-%m-%d")

    return df_final


# ============================================================================
# 5. RESUMEN FINAL EN CONSOLA
# ============================================================================

def imprimir_resumen(df_final, ruta_salida):
    n_total = len(df_final)

    print("\n" + "=" * 60)
    print("PANEL FINAL — datos_procesados_2024200492K.csv")
    print("=" * 60)
    print(f"Observaciones totales : {n_total}")
    print(f"Bancos incluidos      : {df_final['banco'].nunique()}")
    print(f"Meses cubiertos       : {df_final['fecha'].nunique()}")
    print(f"Guardado en           : {ruta_salida}")
    print("=" * 60)
    print("\nPrimeras filas:")
    print(df_final.head(10))


# ============================================================================
# 6. PROGRAMA PRINCIPAL
# ============================================================================

def main():
    df_panel, _ = extraer_panel_completo(DIR_SBS)

    if df_panel.empty:
        print("\n[ERROR CRÍTICO] No se extrajo ningún dato. Revisa la carpeta de archivos SBS.")
        return

    df_final = completar_panel_con_interpolacion(
        df_panel, RANGO_FECHAS, COLUMNAS_NUMERICAS, MIN_MESES_POR_BANCO
    )

    # --- ELIMINAR LA COLUMNA 'fuente_dato' ANTES DE EXPORTAR ---
    df_final = df_final.drop(columns=["fuente_dato"], errors="ignore")

    os.makedirs(os.path.dirname(RUTA_SALIDA), exist_ok=True)
    
    # Guardar versión oficial en CSV
    df_final.to_csv(RUTA_SALIDA, index=False, encoding="utf-8-sig")

    # Guardar también versión en Excel (.xlsx) sin la columna fuente_dato
    RUTA_SALIDA_XLSX = RUTA_SALIDA.replace(".csv", ".xlsx")
    df_final.to_excel(RUTA_SALIDA_XLSX, index=False)
    print(f"También guardado como Excel en: {RUTA_SALIDA_XLSX}")

    imprimir_resumen(df_final, RUTA_SALIDA)


if __name__ == "__main__":
    main()