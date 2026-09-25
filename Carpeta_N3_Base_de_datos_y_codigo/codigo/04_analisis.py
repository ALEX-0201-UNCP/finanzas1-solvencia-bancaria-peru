# ============================================================================
# UNIVERSIDAD NACIONAL DEL CENTRO DEL PERÚ
# Facultad de Economía — Escuela Profesional de Economía
# Finanzas I (055D) — Ciclo V — Periodo 2026-II
# ----------------------------------------------------------------------------
# Nombres y apellidos : Chancha Santiago Alex Omar
# Código de matrícula : 2024200492K
# Tema N.º 9 (Unidad I): Solvencia bancaria en el Perú — ratio de capital
#                        global y activos ponderados por riesgo (APR)
# Fecha de extracción : 2026-09-24
# ----------------------------------------------------------------------------
# 04_analisis.py
#
# Genera tablas (.csv + .xlsx) y figuras (.png) en /salidas a partir del
# panel procesado y de la serie del Banco Mundial.
# ============================================================================

import os
import pandas as pd
import matplotlib.pyplot as plt

# ============================================================================
# 1. CONFIGURACIÓN DE RUTAS
# ============================================================================

def obtener_directorio_base():
    try:
        dir_actual = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        dir_actual = os.getcwd()
    if os.path.basename(dir_actual).lower() == "codigo":
        return os.path.dirname(dir_actual)
    return dir_actual


DIR_BASE = obtener_directorio_base()
RUTA_PANEL = os.path.join(DIR_BASE, "datos_procesados", "datos_procesados_2024200492K.csv")
RUTA_API = os.path.join(DIR_BASE, "datos_crudos", "datos_crudos_2024200492K_bancomundial.csv")
DIR_SALIDAS = os.path.join(DIR_BASE, "salidas")
os.makedirs(DIR_SALIDAS, exist_ok=True)

plt.rcParams["figure.dpi"] = 120
plt.rcParams["font.size"] = 10


def guardar_tabla(df, nombre_base, incluir_index=False):
    """Guarda un DataFrame en .csv (formato oficial exigido por la consigna,
    con encoding utf-8-sig para que Excel muestre bien las tildes) y también
    en .xlsx (para revisión cómoda, siempre ordenado en columnas)."""
    ruta_csv = os.path.join(DIR_SALIDAS, f"{nombre_base}.csv")
    ruta_xlsx = os.path.join(DIR_SALIDAS, f"{nombre_base}.xlsx")
    df.to_csv(ruta_csv, index=incluir_index, encoding="utf-8-sig")
    df.to_excel(ruta_xlsx, index=incluir_index)
    print(f"Guardado: {ruta_csv}")
    print(f"Guardado: {ruta_xlsx}")


# ============================================================================
# 2. CARGA DE DATOS
# ============================================================================

def cargar_panel():
    df = pd.read_csv(RUTA_PANEL, encoding="utf-8-sig")
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df


def cargar_api():
    if not os.path.exists(RUTA_API):
        print(f"[Aviso] No se encontró {RUTA_API}; se omite el análisis comparativo con el Banco Mundial.")
        return None
    return pd.read_csv(RUTA_API)


# ============================================================================
# 3. TABLA 1 — ESTADÍSTICAS DESCRIPTIVAS DEL RATIO DE CAPITAL GLOBAL
# ============================================================================

def tabla_estadisticas_descriptivas(df):
    resumen = df.groupby("fuente_dato")["ratio_capital_global_pct"].describe()
    resumen_general = df["ratio_capital_global_pct"].describe().to_frame("Todo el panel").T
    tabla = pd.concat([resumen_general, resumen]).round(2)
    tabla.index.name = "grupo"

    guardar_tabla(tabla, "tabla1_estadisticas_descriptivas", incluir_index=True)
    print("\n=== TABLA 1: Estadísticas descriptivas del Ratio de Capital Global (%) ===")
    print(tabla)
    return tabla


# ============================================================================
# 4. TABLA 2 — RANKING DE BANCOS (último periodo disponible)
# ============================================================================

def tabla_ranking_bancos(df):
    ultima_fecha = df["fecha"].max()
    df_ultimo = df[df["fecha"] == ultima_fecha].copy()
    df_ultimo = df_ultimo.sort_values("ratio_capital_global_pct", ascending=False)

    columnas_mostrar = ["banco", "ratio_capital_global_pct", "apr_total", "fuente_dato"]
    tabla = df_ultimo[columnas_mostrar].reset_index(drop=True)
    tabla.index = tabla.index + 1
    tabla.index.name = "posicion"
    tabla["ratio_capital_global_pct"] = tabla["ratio_capital_global_pct"].round(2)
    tabla["apr_total"] = tabla["apr_total"].round(0)

    guardar_tabla(tabla, "tabla2_ranking_bancos", incluir_index=True)
    print(f"\n=== TABLA 2: Ranking de bancos por Ratio de Capital Global — {ultima_fecha.strftime('%Y-%m')} ===")
    print(tabla)
    return tabla, ultima_fecha


# ============================================================================
# 5. FIGURA 1 — EVOLUCIÓN DEL RATIO DE CAPITAL GLOBAL DEL SISTEMA (2018-2025)
# ============================================================================

def figura_evolucion_sistema(df):
    serie_mensual = df.groupby("fecha")["ratio_capital_global_pct"].mean()

    plt.figure(figsize=(10, 5))
    plt.plot(serie_mensual.index, serie_mensual.values, linewidth=1.8, color="#1f4e79")
    plt.axhline(y=10, color="red", linestyle="--", linewidth=1, label="Mínimo regulatorio SBS (10%)")
    plt.title("Evolución del Ratio de Capital Global promedio\nSistema de Banca Múltiple del Perú (2018-2025)")
    plt.xlabel("Fecha")
    plt.ylabel("Ratio de Capital Global (%)")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    ruta = os.path.join(DIR_SALIDAS, "figura1_evolucion_ratio_sistema.png")
    plt.savefig(ruta)
    plt.close()
    print(f"\nFigura 1 guardada en: {ruta}")


# ============================================================================
# 6. FIGURA 2 — RANKING DE BANCOS (barras horizontales)
# ============================================================================

def figura_ranking_bancos(tabla_ranking, ultima_fecha):
    tabla_grafico = tabla_ranking.sort_values("ratio_capital_global_pct")
    colores = ["#c0392b" if f == "interpolado" else "#1f4e79" for f in tabla_grafico["fuente_dato"]]

    plt.figure(figsize=(9, 8))
    plt.barh(tabla_grafico["banco"], tabla_grafico["ratio_capital_global_pct"], color=colores)
    plt.axvline(x=10, color="red", linestyle="--", linewidth=1, label="Mínimo regulatorio SBS (10%)")
    plt.title(f"Ratio de Capital Global por banco — {ultima_fecha.strftime('%Y-%m')}")
    plt.xlabel("Ratio de Capital Global (%)")
    plt.legend()
    plt.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    ruta = os.path.join(DIR_SALIDAS, "figura2_ranking_bancos.png")
    plt.savefig(ruta)
    plt.close()
    print(f"Figura 2 guardada en: {ruta}")


# ============================================================================
# 7. FIGURA 3 — DISPERSIÓN: TAMAÑO DEL BANCO (APR) vs. RATIO DE CAPITAL GLOBAL
# ============================================================================

def figura_dispersión_apr_vs_ratio(df):
    ultima_fecha = df["fecha"].max()
    df_ultimo = df[df["fecha"] == ultima_fecha]

    plt.figure(figsize=(8, 6))
    plt.scatter(df_ultimo["apr_total"], df_ultimo["ratio_capital_global_pct"],
                s=60, alpha=0.7, color="#1f4e79", edgecolors="black")
    for _, fila in df_ultimo.iterrows():
        plt.annotate(fila["banco"].split("(")[0].strip()[:15],
                     (fila["apr_total"], fila["ratio_capital_global_pct"]),
                     fontsize=7, alpha=0.8, xytext=(3, 3), textcoords="offset points")
    plt.xscale("log")
    plt.title(f"Tamaño del banco (APR, escala log) vs. Ratio de Capital Global\n{ultima_fecha.strftime('%Y-%m')}")
    plt.xlabel("Activos Ponderados por Riesgo — APR (escala logarítmica)")
    plt.ylabel("Ratio de Capital Global (%)")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    ruta = os.path.join(DIR_SALIDAS, "figura3_apr_vs_ratio.png")
    plt.savefig(ruta)
    plt.close()
    print(f"Figura 3 guardada en: {ruta}")


# ============================================================================
# 8. TABLA 3 — COMPARACIÓN CON EL PROMEDIO REGIONAL/MUNDIAL (Banco Mundial)
# ============================================================================

def tabla_comparacion_banco_mundial(df_panel, df_api):
    if df_api is None:
        return None

    df_api = df_api.copy()
    df_panel_anual = df_panel.copy()
    df_panel_anual["anio"] = df_panel_anual["fecha"].dt.year
    promedio_anual_sbs = df_panel_anual.groupby("anio")["ratio_capital_global_pct"].mean().reset_index()
    promedio_anual_sbs.columns = ["anio", "ratio_capital_global_pct_SBS_promedio"]

    tabla = pd.merge(promedio_anual_sbs, df_api, on="anio", how="inner").round(2)

    guardar_tabla(tabla, "tabla3_comparacion_banco_mundial", incluir_index=False)
    print("\n=== TABLA 3: Comparación panel SBS (promedio anual) vs. indicador Banco Mundial ===")
    print(tabla)
    return tabla


# ============================================================================
# 9. PROGRAMA PRINCIPAL
# ============================================================================

def main():
    print("Cargando datos procesados...")
    df_panel = cargar_panel()
    df_api = cargar_api()

    print(f"Panel cargado: {len(df_panel)} observaciones, {df_panel['banco'].nunique()} bancos, "
          f"{df_panel['fecha'].nunique()} meses.\n")

    tabla_estadisticas_descriptivas(df_panel)
    tabla_ranking, ultima_fecha = tabla_ranking_bancos(df_panel)
    figura_evolucion_sistema(df_panel)
    figura_ranking_bancos(tabla_ranking, ultima_fecha)
    figura_dispersión_apr_vs_ratio(df_panel)
    tabla_comparacion_banco_mundial(df_panel, df_api)

    print(f"\n{'='*60}")
    print(f"Análisis completo. Todos los archivos guardados en: {DIR_SALIDAS}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()