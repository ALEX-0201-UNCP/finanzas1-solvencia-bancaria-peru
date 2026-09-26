# ============================================================================
# UNIVERSIDAD NACIONAL DEL CENTRO DEL PERÚ
# Facultad de Economía — Escuela Profesional de Economía
# Finanzas I (055D) — Ciclo V — Periodo 2026-II
# ----------------------------------------------------------------------------
# Nombres y apellidos : Chancha Santiago Alex Omar
# Código de matrícula : 2024200492K
# Tema N.º 9 (Unidad I): Solvencia bancaria en el Perú — ratio de capital
#                        global y activos ponderados por riesgo (APR)
# ----------------------------------------------------------------------------
# 03_limpieza_datos.py  (v3 — ROE y Cartera Atrasada extraídos y validados
# contra archivos reales de la SBS)
#
# Panel final: banco x mes, 2018-01 a 2025-12 (96 meses = 8 años), con
# EXACTAMENTE estas 4 variables del modelo (nada más):
#
#   ratio_capital_global_pct   Endógena (Y)                  %
#   roe_pct                    Exógena                       %
#   cartera_atrasada_pct       Exógena (riesgo de crédito)   %
#   apr_total_soles            Exógena (control de tamaño)   Miles de S/.
#
# ----------------------------------------------------------------------------
# CÓMO SE OBTIENE CADA VARIABLE (documentado porque cada reporte SBS tiene
# una estructura de hoja distinta):
#
# 1) ratio_capital_global_pct y apr_total_soles
#    Reporte "Ratio de Capital Global / APR". Bancos en FILAS, bajo el
#    encabezado 'EMPRESAS'. Se detecta la columna por el texto del título
#    (no por posición fija), porque la SBS cambió el formato del reporte
#    más de una vez entre 2018 y 2025.
#
# 2) roe_pct
#    Este reporte en realidad es "Balance General" (hoja 1) + "Estado de
#    Ganancias y Pérdidas" (hoja 2) — la SBS NO publica un % de ROE ya
#    calculado en este archivo. Se construye así:
#
#        ROE anualizado (%) = (Resultado Neto del Ejercicio acumulado
#                               ÷ N° de meses transcurridos del año × 12)
#                              ÷ Patrimonio del mismo mes × 100
#
#    Esta es la fórmula de anualización simple de un flujo acumulado (el
#    Estado de Ganancias y Pérdidas de la SBS se reinicia cada enero).
#    *** Si tu curso exige otra definición (p.ej. patrimonio PROMEDIO de
#    12 meses en el denominador), avísame y se ajusta en una sola función. ***
#    Los bancos van en BLOQUES DE COLUMNAS (MN / ME / TOTAL); se usa la
#    columna TOTAL de cada bloque.
#
# 3) cartera_atrasada_pct
#    Reporte "Morosidad según tipo y modalidad de crédito". Bancos en
#    COLUMNAS (una sola columna por banco, sin bloques MN/ME/TOTAL). Se usa
#    la fila 'Total Créditos Directos', que es la morosidad total del banco
#    agregando todos los tipos de crédito (no se usa el desagregado por
#    tipo, que también viene en el archivo pero no se pidió).
#
# 4) Cruce entre las 3 fuentes
#    Los 3 reportes escriben el nombre del banco de forma distinta
#    ("Banco Continental" vs "B. Continental", sufijos como "(con
#    sucursales en el exterior)", filas de total del sistema). Se normaliza
#    el nombre antes de cruzar. Esto NO resuelve cambios de nombre de la
#    propia entidad en el tiempo (p.ej. Continental -> BBVA); si el conteo
#    final de bancos no cuadra, hay que revisar la lista impresa al final
#    y completar MAPEO_MANUAL_BANCOS.
# ============================================================================

import os
import re
import glob
import pandas as pd


# ============================================================================
# 1. CONFIGURACIÓN
# ============================================================================

def obtener_directorio_base():
    """Detecta la carpeta base del proyecto (un nivel arriba de /codigo)."""
    try:
        dir_actual = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        dir_actual = os.getcwd()
    if os.path.basename(dir_actual).lower() == "codigo":
        return os.path.dirname(dir_actual)
    return dir_actual


DIR_BASE = obtener_directorio_base()

# --- AJUSTAR SI TU 02_scraping_web.py GUARDÓ LAS CARPETAS CON OTRO NOMBRE ---
DIR_RATIO_CAPITAL = os.path.join(DIR_BASE, "datos_crudos", "sbs_ratio_capital_global")
DIR_ROE = os.path.join(DIR_BASE, "datos_crudos", "sbs_roe")
DIR_CARTERA = os.path.join(DIR_BASE, "datos_crudos", "sbs_cartera_atrasada")

RUTA_SALIDA_CSV = os.path.join(DIR_BASE, "datos_procesados", "datos_procesados_2024200492K.csv")
RUTA_SALIDA_XLSX = os.path.join(DIR_BASE, "datos_procesados", "datos_procesados_2024200492K.xlsx")

RANGO_FECHAS = pd.date_range(start="2018-01-31", end="2025-12-31", freq="ME")  # 96 meses = 8 años
MIN_MESES_POR_BANCO = 12  # bancos con menos datos reales que esto se excluyen del panel

# Si al correr el script ves que un banco quedó partido en dos nombres
# distintos (típicamente por un cambio de marca, ej. Continental -> BBVA),
# agrégalo aquí como {"nombre_como_aparece": "nombre_final_deseado"}.
MAPEO_MANUAL_BANCOS = {
    # "Banco Continental": "BBVA Perú",
}

# Filas/columnas de agregados del sistema (no son un banco individual):
# se excluyen de los 3 reportes.
PATRONES_EXCLUIR_NOMBRE = ["TOTAL", "SUCURSALES EN EL EXTERIOR", "SUCURSALES EN EL \nEXTERIOR"]


# ============================================================================
# 2. UTILIDADES GENERALES
# ============================================================================

def convertir_a_float(valor):
    """Convierte una celda a float, tolerando comas de miles, guiones (sin
    dato) y celdas vacías. Devuelve None si no se puede convertir."""
    if pd.isna(valor):
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip().replace(",", "")
    if texto in ("", "-", "nan"):
        return None
    try:
        return float(texto)
    except ValueError:
        return None


def normalizar_nombre_banco(nombre):
    """Normaliza el nombre de un banco para poder cruzar los 3 reportes
    SBS, que usan formatos de texto distintos entre sí."""
    n = str(nombre).strip()
    n = n.replace("\n", " ")
    n = re.sub(r"\(.*?\)", "", n)              # quita "(con sucursales...)"
    n = re.sub(r"^B\.\s*", "Banco ", n)         # "B. Continental" -> "Banco Continental"
    n = re.sub(r"\s+", " ", n).strip()
    n = MAPEO_MANUAL_BANCOS.get(n, n)
    return n


def es_nombre_excluible(nombre):
    """True si el 'nombre' corresponde a un total del sistema o a una fila
    duplicada de sucursales en el exterior, no a un banco individual."""
    nombre_up = str(nombre).upper().replace("\n", " ")
    return any(patron in nombre_up for patron in PATRONES_EXCLUIR_NOMBRE)


def encontrar_fecha_reporte(df_raw, max_filas=6):
    """Ubica la fecha del reporte en las primeras filas, columna A."""
    for r in range(min(max_filas, len(df_raw))):
        fecha_parseada = pd.to_datetime(str(df_raw.iloc[r, 0]), errors="coerce")
        if not pd.isna(fecha_parseada):
            return fecha_parseada.strftime("%Y-%m-%d")
    return None


# ============================================================================
# 3A. EXTRACCIÓN — RATIO DE CAPITAL GLOBAL / APR  (bancos en FILAS)
# ============================================================================

def texto_combinado_columna(df_raw, columna, fila_empresas):
    fila_inicio = max(0, fila_empresas - 5)
    texto = ""
    for fila in range(fila_inicio, fila_empresas + 1):
        valor = df_raw.iloc[fila, columna]
        if pd.notna(valor):
            texto += str(valor).upper()
    return texto.replace(" ", "")


def encontrar_columna_por_texto(df_raw, fila_empresas, textos_buscados):
    if isinstance(textos_buscados, str):
        textos_buscados = [textos_buscados]
    textos_norm = [t.upper().replace(" ", "") for t in textos_buscados]
    for columna in range(df_raw.shape[1]):
        texto_col = texto_combinado_columna(df_raw, columna, fila_empresas)
        if any(t in texto_col for t in textos_norm):
            return columna
    return None


def encontrar_columna_apr_total(df_raw, fila_empresas):
    """El APR total se reportó de 2 formas según la época:
      - 2021-2025: columna directa 'Activos y Contingentes Ponderados por
        Riesgo Total'.
      - 2018-2020: solo existe el 'Requerimiento Total' de patrimonio
        efectivo -> APR = Requerimiento x 10 (identidad Ratio = 10%)."""
    columna_grupo = encontrar_columna_por_texto(df_raw, fila_empresas, "PONDERADOSPORRIESGO")
    fila_formula = fila_empresas + 1

    if columna_grupo is not None:
        for columna in range(columna_grupo, df_raw.shape[1]):
            formula = str(df_raw.iloc[fila_formula, columna]) if fila_formula < len(df_raw) else ""
            if "=" in formula and formula.count("+") >= 2:
                return columna, False

    for columna in range(df_raw.shape[1]):
        formula = str(df_raw.iloc[fila_formula, columna]) if fila_formula < len(df_raw) else ""
        if "=" in formula and formula.count("+") >= 2:
            return columna, True

    return None, False


def extraer_ratio_capital_global(ruta_archivo):
    df_raw = pd.read_excel(ruta_archivo, sheet_name=0, header=None)

    fila_empresas = next(
        (r for r in range(min(15, len(df_raw)))
         if str(df_raw.iloc[r, 0]).strip().upper() == "EMPRESAS"),
        None
    )
    if fila_empresas is None:
        raise ValueError("no se encontró la fila de encabezado 'EMPRESAS'")

    fecha_str = encontrar_fecha_reporte(df_raw)
    if not fecha_str:
        raise ValueError("no se encontró la fecha del reporte")

    col_apr_total, requiere_x10 = encontrar_columna_apr_total(df_raw, fila_empresas)
    col_ratio_global = encontrar_columna_por_texto(df_raw, fila_empresas, "RATIODECAPITALGLOBAL")

    if col_apr_total is None or col_ratio_global is None:
        raise ValueError("faltan columnas obligatorias (APR total o Ratio de Capital Global)")

    registros = []
    for idx in range(fila_empresas + 3, len(df_raw)):
        nombre_crudo = str(df_raw.iloc[idx, 0]).strip()
        if not nombre_crudo or nombre_crudo.lower() == "nan":
            continue
        if any(p in nombre_crudo.upper() for p in ["TOTAL", "SISTEMA", "FUENTE", "NOTA"]):
            break

        apr_crudo = convertir_a_float(df_raw.iloc[idx, col_apr_total])
        apr_total_soles = apr_crudo * 10 if (requiere_x10 and apr_crudo is not None) else apr_crudo
        ratio_global = convertir_a_float(df_raw.iloc[idx, col_ratio_global])

        if apr_total_soles is None or ratio_global is None:
            continue

        registros.append({
            "fecha": fecha_str,
            "banco": normalizar_nombre_banco(nombre_crudo),
            "ratio_capital_global_pct": ratio_global,
            "apr_total_soles": apr_total_soles,
        })
    return registros


# ============================================================================
# 3B. EXTRACCIÓN — ROE  (bancos en BLOQUES DE COLUMNAS: MN / ME / TOTAL)
#     Fuente: hoja 1 = Balance General (PATRIMONIO),
#             hoja 2 = Estado de Ganancias y Pérdidas (RESULTADO NETO)
# ============================================================================

def encontrar_fila_por_etiqueta_exacta(df_raw, etiqueta):
    etiqueta_norm = etiqueta.strip().upper()
    for r in range(len(df_raw)):
        if str(df_raw.iloc[r, 0]).strip().upper() == etiqueta_norm:
            return r
    return None


def fila_encabezado_bancos_mas_cercana(df_raw, fila_objetivo):
    """Busca hacia arriba, desde fila_objetivo, la fila más cercana cuyo
    renglón siguiente tenga el patrón MN / ME / TOTAL (encabezado de
    bloques de banco en Balance General / Ganancias y Pérdidas)."""
    for r in range(fila_objetivo - 1, -1, -1):
        fila_sig = r + 1
        if fila_sig >= len(df_raw):
            continue
        valores = [str(df_raw.iloc[fila_sig, c]).strip().upper() for c in range(min(6, df_raw.shape[1]))]
        if "MN" in valores and "TOTAL" in valores:
            return r
    return None


def encontrar_bloques_bancos(df_raw, fila_nombres_banco):
    """Devuelve {nombre_banco: columna_TOTAL}, recorriendo bloques de 4
    columnas (MN, ME, TOTAL, separador). La columna 0 nunca es un banco:
    ahí va la etiqueta de la partida contable (ej. 'Pasivo')."""
    bloques = {}
    c = 1
    ncols = df_raw.shape[1]
    while c < ncols:
        valor = df_raw.iloc[fila_nombres_banco, c]
        if pd.notna(valor) and str(valor).strip():
            nombre_normalizado = normalizar_nombre_banco(str(valor).strip())
            col_total = c + 2
            if col_total < ncols and not es_nombre_excluible(nombre_normalizado):
                bloques[nombre_normalizado] = col_total
            c += 4
        else:
            c += 1
    return bloques


def extraer_roe(ruta_archivo):
    df_balance = pd.read_excel(ruta_archivo, sheet_name=0, header=None)
    df_ganancias = pd.read_excel(ruta_archivo, sheet_name=1, header=None)

    fecha_str = encontrar_fecha_reporte(df_balance)
    if not fecha_str:
        raise ValueError("no se encontró la fecha del reporte")
    mes_reporte = pd.to_datetime(fecha_str).month

    fila_patrimonio = encontrar_fila_por_etiqueta_exacta(df_balance, "PATRIMONIO")
    if fila_patrimonio is None:
        raise ValueError("no se encontró la fila 'PATRIMONIO' en el Balance General")
    fila_hdr_patrimonio = fila_encabezado_bancos_mas_cercana(df_balance, fila_patrimonio)
    if fila_hdr_patrimonio is None:
        raise ValueError("no se encontró el encabezado de bancos para PATRIMONIO")
    bloques_patrimonio = encontrar_bloques_bancos(df_balance, fila_hdr_patrimonio)

    fila_resultado = encontrar_fila_por_etiqueta_exacta(df_ganancias, "RESULTADO NETO DEL EJERCICIO")
    if fila_resultado is None:
        raise ValueError("no se encontró 'RESULTADO NETO DEL EJERCICIO' en Ganancias y Pérdidas")
    fila_hdr_resultado = fila_encabezado_bancos_mas_cercana(df_ganancias, fila_resultado)
    if fila_hdr_resultado is None:
        raise ValueError("no se encontró el encabezado de bancos para RESULTADO NETO")
    bloques_resultado = encontrar_bloques_bancos(df_ganancias, fila_hdr_resultado)

    registros = []
    bancos_comunes = set(bloques_patrimonio) & set(bloques_resultado)
    for banco in bancos_comunes:
        patrimonio = convertir_a_float(df_balance.iloc[fila_patrimonio, bloques_patrimonio[banco]])
        resultado_acumulado = convertir_a_float(df_ganancias.iloc[fila_resultado, bloques_resultado[banco]])

        if patrimonio is None or resultado_acumulado is None or patrimonio == 0:
            continue

        resultado_anualizado = resultado_acumulado / mes_reporte * 12
        roe_pct = (resultado_anualizado / patrimonio) * 100

        registros.append({
            "fecha": fecha_str,
            "banco": banco,
            "roe_pct": roe_pct,
        })
    return registros


# ============================================================================
# 3C. EXTRACCIÓN — CARTERA ATRASADA  (bancos en COLUMNAS, una por banco)
# ============================================================================

def extraer_cartera_atrasada(ruta_archivo):
    df_raw = pd.read_excel(ruta_archivo, sheet_name=0, header=None)

    fecha_str = encontrar_fecha_reporte(df_raw)
    if not fecha_str:
        raise ValueError("no se encontró la fecha del reporte")

    fila_bancos = next(
        (r for r in range(min(10, len(df_raw)))
         if str(df_raw.iloc[r, 0]).strip().upper() == "CONCEPTO"),
        None
    )
    if fila_bancos is None:
        raise ValueError("no se encontró la fila de encabezado 'Concepto'")

    fila_total = next(
        (r for r in range(len(df_raw))
         if str(df_raw.iloc[r, 0]).strip().upper().startswith("TOTAL CRÉDITOS DIRECTOS")
         or str(df_raw.iloc[r, 0]).strip().upper().startswith("TOTAL CREDITOS DIRECTOS")),
        None
    )
    if fila_total is None:
        raise ValueError("no se encontró la fila 'Total Créditos Directos'")

    registros = []
    for columna in range(1, df_raw.shape[1]):
        nombre_crudo = str(df_raw.iloc[fila_bancos, columna]).strip()
        if not nombre_crudo or nombre_crudo.lower() == "nan":
            continue
        nombre_normalizado = normalizar_nombre_banco(nombre_crudo)
        if es_nombre_excluible(nombre_normalizado):
            continue

        cartera_pct = convertir_a_float(df_raw.iloc[fila_total, columna])
        if cartera_pct is None:
            continue

        registros.append({
            "fecha": fecha_str,
            "banco": nombre_normalizado,
            "cartera_atrasada_pct": cartera_pct,
        })
    return registros


# ============================================================================
# 4. CONSTRUCCIÓN DE PANEL POR INDICADOR (extracción + interpolación)
# ============================================================================

def extraer_panel_indicador(directorio, funcion_extraccion, nombre_indicador):
    archivos = sorted(glob.glob(os.path.join(directorio, "*.xls*")))
    print(f"\n[{nombre_indicador}] Archivos encontrados: {len(archivos)}")

    registros_totales = []
    archivos_con_error = []

    for archivo in archivos:
        nombre = os.path.basename(archivo)
        try:
            registros = funcion_extraccion(archivo)
            registros_totales.extend(registros)
        except Exception as error:
            archivos_con_error.append((nombre, str(error)))

    df = pd.DataFrame(registros_totales)
    if not df.empty:
        df = df.drop_duplicates(subset=["fecha", "banco"]).reset_index(drop=True)

    print(f"[{nombre_indicador}] Observaciones reales extraídas: {len(df)}")
    print(f"[{nombre_indicador}] Archivos con error: {len(archivos_con_error)} de {len(archivos)}")
    if archivos_con_error:
        for nombre, motivo in archivos_con_error[:5]:
            print(f"   - {nombre}: {motivo}")
        if len(archivos_con_error) > 5:
            print(f"   ... y {len(archivos_con_error) - 5} más")
    if not df.empty:
        print(f"[{nombre_indicador}] Bancos detectados ({df['banco'].nunique()}): "
              f"{sorted(df['banco'].unique())}")

    return df, archivos_con_error


def completar_indicador_con_interpolacion(df_indicador, columnas_numericas, rango_fechas, min_meses):
    """Reindexa el panel de UN indicador para cubrir el rango completo de
    meses y rellena huecos por banco mediante interpolación lineal
    (autorizado por el docente del curso)."""
    df = df_indicador.copy()
    df["fecha"] = pd.to_datetime(df["fecha"])

    conteo_por_banco = df["banco"].value_counts()
    bancos_validos = conteo_por_banco[conteo_por_banco >= min_meses].index

    paneles_por_banco = []
    for banco in bancos_validos:
        df_banco = (
            df[df["banco"] == banco]
            .drop_duplicates(subset="fecha")
            .set_index("fecha")
            .reindex(rango_fechas)
        )
        df_banco["banco"] = banco
        for columna in columnas_numericas:
            df_banco[columna] = df_banco[columna].interpolate(method="linear", limit_direction="both")
        paneles_por_banco.append(df_banco)

    if not paneles_por_banco:
        return pd.DataFrame(columns=["fecha", "banco"] + columnas_numericas)

    df_final = pd.concat(paneles_por_banco).reset_index().rename(columns={"index": "fecha"})
    return df_final


# ============================================================================
# 5. FUSIÓN DE LOS 3 PANELES EN EL PANEL FINAL (SOLO LAS 4 VARIABLES)
# ============================================================================

def construir_panel_final():
    df_capital_crudo, _ = extraer_panel_indicador(
        DIR_RATIO_CAPITAL, extraer_ratio_capital_global, "Ratio de Capital Global / APR"
    )
    df_capital = completar_indicador_con_interpolacion(
        df_capital_crudo, ["ratio_capital_global_pct", "apr_total_soles"],
        RANGO_FECHAS, MIN_MESES_POR_BANCO,
    )

    df_roe_crudo, _ = extraer_panel_indicador(DIR_ROE, extraer_roe, "ROE")
    df_roe = completar_indicador_con_interpolacion(
        df_roe_crudo, ["roe_pct"], RANGO_FECHAS, MIN_MESES_POR_BANCO,
    )

    df_cartera_crudo, _ = extraer_panel_indicador(DIR_CARTERA, extraer_cartera_atrasada, "Cartera Atrasada")
    df_cartera = completar_indicador_con_interpolacion(
        df_cartera_crudo, ["cartera_atrasada_pct"], RANGO_FECHAS, MIN_MESES_POR_BANCO,
    )

    # Fusión por (banco, fecha). 'inner' = solo se conservan los bancos que
    # tienen datos suficientes en las 3 fuentes a la vez.
    df_final = (
        df_capital
        .merge(df_roe, on=["banco", "fecha"], how="inner")
        .merge(df_cartera, on=["banco", "fecha"], how="inner")
    )

    # SOLO estas 6 columnas en el resultado: banco y fecha (identificadores
    # de panel) + las 4 variables del modelo. Nada más.
    df_final = df_final[[
        "banco", "fecha",
        "ratio_capital_global_pct", "roe_pct", "cartera_atrasada_pct", "apr_total_soles",
    ]]
    df_final = df_final.dropna()
    df_final["fecha"] = df_final["fecha"].dt.strftime("%Y-%m-%d")
    df_final = df_final.sort_values(["banco", "fecha"]).reset_index(drop=True)

    return df_final


# ============================================================================
# 6. RESUMEN FINAL EN CONSOLA
# ============================================================================

def imprimir_resumen(df_final, ruta_csv, ruta_xlsx):
    print("\n" + "=" * 70)
    print("PANEL FINAL — datos_procesados_2024200492K")
    print("=" * 70)
    print(f"Observaciones totales : {len(df_final)}")
    print(f"Bancos incluidos ({df_final['banco'].nunique()}): {sorted(df_final['banco'].unique())}")
    print(f"Meses cubiertos       : {df_final['fecha'].nunique()} "
          f"({df_final['fecha'].min()} a {df_final['fecha'].max()})")
    print(f"Columnas              : {list(df_final.columns)}")
    print(f"CSV guardado en       : {ruta_csv}")
    print(f"XLSX guardado en      : {ruta_xlsx}")
    print("=" * 70)
    print("\nPrimeras filas:")
    print(df_final.head(10))


# ============================================================================
# 7. PROGRAMA PRINCIPAL
# ============================================================================

def main():
    df_final = construir_panel_final()

    if df_final.empty:
        print("\n[ERROR CRÍTICO] El panel final quedó vacío. Revisa los mensajes de "
              "error de cada indicador arriba (nombres de carpeta DIR_ROE / "
              "DIR_CARTERA, o algún cambio de formato no contemplado).")
        return

    os.makedirs(os.path.dirname(RUTA_SALIDA_CSV), exist_ok=True)
    df_final.to_csv(RUTA_SALIDA_CSV, index=False, encoding="utf-8-sig")
    df_final.to_excel(RUTA_SALIDA_XLSX, index=False)

    imprimir_resumen(df_final, RUTA_SALIDA_CSV, RUTA_SALIDA_XLSX)


if __name__ == "__main__":
    main()
