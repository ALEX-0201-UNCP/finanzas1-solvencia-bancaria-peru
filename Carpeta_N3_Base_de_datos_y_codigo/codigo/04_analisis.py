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
# 04_analisis.py  (v2)
#
# Pregunta de investigación:
#   "Analizar la evolución de la solvencia bancaria en el Perú y su
#    relación con la rentabilidad y el riesgo de crédito."
#
# Modelo:
#   ratio_capital_global_pct_it = β0 + β1·roe_pct_it + β2·cartera_atrasada_pct_it
#                                  + β3·ln(apr_total_soles_it) + u_it
#
# Cambios respecto a v1:
#   - Trabaja con panel NO balanceado (cada banco solo en los meses en que
#     operó), tal como lo entrega 03_limpieza_datos.py v4.
#   - Winsorización al 1 % y 99 % del ROE y del ratio de capital: bancos con
#     patrimonio casi nulo (p. ej. Alfin en 2021-2022) generan ROE de miles
#     de por ciento que, sin tratar, dominan las estimaciones.
#   - Tabla 3 (nueva): cobertura del panel por banco.
#   - Figura 1: ratio del sistema ponderado por APR (= Σ patrimonio efectivo
#     / Σ APR), que es como la SBS calcula el ratio agregado, más la mediana.
#   - Se añade Efectos Fijos de dos vías (banco + mes).
#   - Test de Hausman corregido: se calcula con covarianzas NO robustas
#     (única forma en que el test es válido) y se complementa con el test de
#     Mundlak robusto a clusters, que es el que decide el modelo.
#
# Requiere: pandas, numpy, matplotlib, statsmodels, linearmodels, scipy
# ============================================================================

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

try:
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    from statsmodels.tools.tools import add_constant
    from linearmodels.panel import PooledOLS, PanelOLS, RandomEffects, compare
    from scipy import stats as sp_stats
except ImportError as error:
    sys.exit(
        "\n[ERROR] Falta instalar una librería necesaria para el análisis "
        "econométrico.\nCorre en tu terminal:\n\n"
        "    pip install -r requirements.txt\n\n"
        f"Detalle del error: {error}\n"
    )


# ============================================================================
# 1. CONFIGURACIÓN
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
DIR_SALIDAS = os.path.join(DIR_BASE, "salidas")
os.makedirs(DIR_SALIDAS, exist_ok=True)

plt.rcParams["figure.dpi"] = 120
plt.rcParams["font.size"] = 10

VARIABLE_Y = "ratio_capital_global_pct"
VARIABLES_X = ["roe_pct", "cartera_atrasada_pct", "ln_apr_total_soles"]

# Winsorización: los valores por debajo del percentil 1 y por encima del 99
# se reemplazan por esos percentiles. Poner False para estimar sin tratar.
WINSORIZAR = True
PERCENTILES_WINSOR = (0.01, 0.99)
VARIABLES_WINSOR = ["ratio_capital_global_pct", "roe_pct"]

ETIQUETAS = {
    "ratio_capital_global_pct": "Ratio de Capital Global (%)",
    "roe_pct": "ROE anualizado (%)",
    "cartera_atrasada_pct": "Cartera Atrasada (%)",
    "apr_total_soles": "APR total (miles de S/.)",
    "ln_apr_total_soles": "ln(APR total)",
}


def guardar_tabla(df, nombre_base, incluir_index=True):
    ruta_csv = os.path.join(DIR_SALIDAS, f"{nombre_base}.csv")
    ruta_xlsx = os.path.join(DIR_SALIDAS, f"{nombre_base}.xlsx")
    df.to_csv(ruta_csv, index=incluir_index, encoding="utf-8-sig")
    df.to_excel(ruta_xlsx, index=incluir_index)
    print(f"Guardado: {ruta_csv}")
    print(f"Guardado: {ruta_xlsx}")


def guardar_texto(texto, nombre_base):
    ruta = os.path.join(DIR_SALIDAS, f"{nombre_base}.txt")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(texto)
    print(f"Guardado: {ruta}")


# ============================================================================
# 2. CARGA Y PREPARACIÓN DEL PANEL
# ============================================================================

def cargar_panel():
    df = pd.read_csv(RUTA_PANEL, encoding="utf-8-sig")
    df["fecha"] = pd.to_datetime(df["fecha"])

    columnas_esperadas = {"banco", "fecha", "ratio_capital_global_pct",
                          "roe_pct", "cartera_atrasada_pct", "apr_total_soles"}
    faltantes = columnas_esperadas - set(df.columns)
    if faltantes:
        raise ValueError(
            f"Al panel le faltan columnas esperadas: {faltantes}. "
            f"¿Es el CSV generado por 03_limpieza_datos.py?"
        )

    df["ln_apr_total_soles"] = np.log(df["apr_total_soles"])
    df = df.sort_values(["banco", "fecha"]).reset_index(drop=True)
    return df


def winsorizar(df):
    """Recorta las colas de las variables indicadas y registra cuántas
    observaciones se modificaron (para reportarlo en el artículo)."""
    df = df.copy()
    lineas = [f"Winsorización al percentil {PERCENTILES_WINSOR[0]*100:.0f} y "
              f"{PERCENTILES_WINSOR[1]*100:.0f} (panel completo)"]
    for columna in VARIABLES_WINSOR:
        inferior, superior = df[columna].quantile(list(PERCENTILES_WINSOR))
        recortadas = int(((df[columna] < inferior) | (df[columna] > superior)).sum())
        df[columna] = df[columna].clip(lower=inferior, upper=superior)
        lineas.append(f"  {columna}: límites [{inferior:.2f}, {superior:.2f}], "
                      f"{recortadas} observaciones recortadas")
    texto = "\n".join(lineas) + "\n"
    print("\n" + texto)
    guardar_texto(texto, "nota_winsorizacion")
    return df


def a_panel_indexado(df):
    """MultiIndex (banco, fecha), formato que exige linearmodels."""
    return df.set_index(["banco", "fecha"])


# ============================================================================
# 3. TABLAS DESCRIPTIVAS
# ============================================================================

def tabla_estadisticas_descriptivas(df):
    columnas = [VARIABLE_Y, "roe_pct", "cartera_atrasada_pct", "apr_total_soles"]
    tabla = df[columnas].describe().T.round(2)
    tabla.columns = ["n", "media", "desv_estandar", "minimo", "p25", "mediana", "p75", "maximo"]
    tabla.index = [ETIQUETAS[c] for c in columnas]
    tabla.index.name = "variable"

    guardar_tabla(tabla, "tabla1_estadisticas_descriptivas")
    print("\n=== TABLA 1: Estadística descriptiva ===")
    print(tabla)
    return tabla


def tabla_matriz_correlacion(df):
    columnas = [VARIABLE_Y, "roe_pct", "cartera_atrasada_pct", "ln_apr_total_soles"]
    etiquetas = ["Ratio Capital Global", "ROE", "Cartera Atrasada", "ln(APR)"]
    matriz = df[columnas].corr(method="pearson").round(3)
    matriz.index = etiquetas
    matriz.columns = etiquetas

    guardar_tabla(matriz, "tabla2_matriz_correlacion")
    print("\n=== TABLA 2: Matriz de correlación de Pearson ===")
    print(matriz)
    return matriz


def tabla_cobertura_panel(df):
    tabla = df.groupby("banco")["fecha"].agg(meses="count", desde="min", hasta="max")
    tabla["desde"] = tabla["desde"].dt.strftime("%Y-%m")
    tabla["hasta"] = tabla["hasta"].dt.strftime("%Y-%m")
    tabla = tabla.sort_values("meses", ascending=False)

    guardar_tabla(tabla, "tabla3_cobertura_panel")
    print("\n=== TABLA 3: Cobertura del panel por banco (panel no balanceado) ===")
    print(tabla)
    print(f"Total: {len(df)} observaciones, {df['banco'].nunique()} bancos, "
          f"{df['fecha'].nunique()} meses")
    return tabla


# ============================================================================
# 4. FIGURAS
# ============================================================================

def figura_evolucion_sistema(df):
    df = df.copy()
    # Ratio agregado del sistema = Σ patrimonio efectivo / Σ APR.
    # Como ratio = PE / APR × 100, PE = ratio × APR / 100.
    df["patrimonio_efectivo"] = df[VARIABLE_Y] * df["apr_total_soles"] / 100
    agregado = df.groupby("fecha")[["patrimonio_efectivo", "apr_total_soles"]].sum()
    ratio_sistema = agregado["patrimonio_efectivo"] / agregado["apr_total_soles"] * 100
    mediana = df.groupby("fecha")[VARIABLE_Y].median()

    plt.figure(figsize=(10, 5))
    plt.plot(ratio_sistema.index, ratio_sistema.values, linewidth=1.8, color="#1f4e79",
             label="Sistema (ponderado por APR)")
    plt.plot(mediana.index, mediana.values, linewidth=1.2, color="#7f9fbf", linestyle="-.",
             label="Mediana entre bancos")
    plt.axhline(y=10, color="red", linestyle="--", linewidth=1, label="Referencia: 10%")
    plt.title("Evolución del Ratio de Capital Global\nSistema de Banca Múltiple del Perú (2018-2025)")
    plt.xlabel("Fecha")
    plt.ylabel("Ratio de Capital Global (%)")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    ruta = os.path.join(DIR_SALIDAS, "figura1_evolucion_ratio_sistema.png")
    plt.savefig(ruta)
    plt.close()
    print(f"\nFigura 1 guardada en: {ruta}")


def figura_dispersion(df, variable_x, nombre_archivo, titulo):
    x = df[variable_x].values
    y = df[VARIABLE_Y].values

    plt.figure(figsize=(7, 5.5))
    plt.scatter(x, y, s=18, alpha=0.4, color="#1f4e79", edgecolors="none")

    coef = np.polyfit(x, y, 1)
    x_linea = np.linspace(x.min(), x.max(), 100)
    plt.plot(x_linea, np.polyval(coef, x_linea), color="red", linewidth=1.5,
             label=f"Tendencia lineal (pendiente = {coef[0]:.3f})")

    plt.title(titulo)
    plt.xlabel(ETIQUETAS[variable_x])
    plt.ylabel(ETIQUETAS[VARIABLE_Y])
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    ruta = os.path.join(DIR_SALIDAS, nombre_archivo)
    plt.savefig(ruta)
    plt.close()
    print(f"Figura guardada en: {ruta}")


def figuras_dispersion_todas(df):
    figura_dispersion(df, "roe_pct", "figura2_roe_vs_solvencia.png",
                      "Rentabilidad (ROE) vs. Solvencia (Ratio de Capital Global)")
    figura_dispersion(df, "cartera_atrasada_pct", "figura3_morosidad_vs_solvencia.png",
                      "Riesgo de Crédito (Cartera Atrasada) vs. Solvencia")
    figura_dispersion(df, "ln_apr_total_soles", "figura4_tamano_vs_solvencia.png",
                      "Tamaño del Banco (ln APR) vs. Solvencia")


# ============================================================================
# 5. MODELOS DE PANEL
# ============================================================================

def correr_modelos_panel(df_panel):
    y = df_panel[VARIABLE_Y]
    X = add_constant(df_panel[VARIABLES_X])

    print("\nEstimando Pooled OLS...")
    modelo_pooled = PooledOLS(y, X).fit(cov_type="clustered", cluster_entity=True)

    print("Estimando Efectos Fijos (banco)...")
    modelo_fe = PanelOLS(y, X, entity_effects=True, drop_absorbed=True).fit(
        cov_type="clustered", cluster_entity=True
    )

    print("Estimando Efectos Fijos de dos vías (banco + mes)...")
    modelo_fe2 = PanelOLS(y, X, entity_effects=True, time_effects=True, drop_absorbed=True).fit(
        cov_type="clustered", cluster_entity=True
    )

    print("Estimando Efectos Aleatorios...")
    modelo_re = RandomEffects(y, X).fit(cov_type="clustered", cluster_entity=True)

    return modelo_pooled, modelo_fe, modelo_fe2, modelo_re


def tabla_comparacion_modelos(modelos):
    comparacion = compare(modelos, precision="std_errors", stars=True)
    texto = str(comparacion)
    texto += ("\nErrores estándar robustos agrupados por banco entre paréntesis. "
              "* p<0.10, ** p<0.05, *** p<0.01\n")
    guardar_texto(texto, "tabla4_comparacion_modelos_panel")
    print("\n=== TABLA 4: Comparación de modelos de panel ===")
    print(texto)
    return comparacion


def prueba_hausman_clasica(df_panel):
    """Hausman clásico. Solo es válido con covarianzas NO robustas (bajo H0,
    RE debe ser eficiente), por eso se re-estiman FE y RE sin cluster.
    H0: efectos individuales no correlacionados con los regresores (RE)."""
    y = df_panel[VARIABLE_Y]
    X = add_constant(df_panel[VARIABLES_X])
    fe = PanelOLS(y, X, entity_effects=True, drop_absorbed=True).fit(cov_type="unadjusted")
    re = RandomEffects(y, X).fit(cov_type="unadjusted")

    parametros = [p for p in VARIABLES_X if p in fe.params.index and p in re.params.index]
    diferencia = (fe.params[parametros] - re.params[parametros]).values
    cov_diferencia = (fe.cov.loc[parametros, parametros] - re.cov.loc[parametros, parametros]).values

    estadistico = float(diferencia @ np.linalg.pinv(cov_diferencia) @ diferencia)
    gl = len(parametros)
    p_valor = float(sp_stats.chi2.sf(estadistico, gl)) if estadistico >= 0 else float("nan")
    return estadistico, gl, p_valor


def prueba_mundlak(df_panel):
    """Test de Mundlak (versión robusta del Hausman): se agregan a RE las
    medias por banco de cada regresor. Si esas medias son conjuntamente
    significativas (Wald con covarianza clustered), los efectos individuales
    están correlacionados con los regresores -> Efectos Fijos."""
    medias = df_panel[VARIABLES_X].groupby(level="banco").transform("mean")
    medias.columns = [f"media_{c}" for c in VARIABLES_X]
    X = add_constant(pd.concat([df_panel[VARIABLES_X], medias], axis=1))
    modelo = RandomEffects(df_panel[VARIABLE_Y], X).fit(cov_type="clustered", cluster_entity=True)

    nombres = list(medias.columns)
    b = modelo.params[nombres].values
    V = modelo.cov.loc[nombres, nombres].values
    estadistico = float(b @ np.linalg.pinv(V) @ b)
    gl = len(nombres)
    p_valor = float(sp_stats.chi2.sf(estadistico, gl))
    return estadistico, gl, p_valor


def reporte_pruebas_especificacion(df_panel):
    h_est, h_gl, h_p = prueba_hausman_clasica(df_panel)
    m_est, m_gl, m_p = prueba_mundlak(df_panel)
    modelo = "Efectos Fijos" if m_p < 0.05 else "Efectos Aleatorios"

    lineas = [
        "Pruebas de especificación: Efectos Fijos vs. Efectos Aleatorios",
        "",
        "1) Hausman clásico (covarianzas no robustas)",
        f"   Estadístico chi2 = {h_est:.4f} | g.l. = {h_gl} | p-valor = "
        + (f"{h_p:.4f}" if not np.isnan(h_p) else "no definido"),
    ]
    if h_est < 0:
        lineas.append("   Nota: estadístico negativo; la diferencia de covarianzas no es "
                      "definida positiva y el test clásico no es concluyente.")
    lineas += [
        "",
        "2) Mundlak robusto a clusters por banco (criterio de decisión)",
        "   H0: las medias por banco de los regresores no son significativas (RE consistente)",
        f"   Estadístico Wald chi2 = {m_est:.4f} | g.l. = {m_gl} | p-valor = {m_p:.4f}",
        "",
        f"Conclusión: modelo recomendado = {modelo}",
    ]
    texto = "\n".join(lineas) + "\n"
    guardar_texto(texto, "tabla6_test_hausman")
    print("\n=== TABLA 6: Pruebas de especificación ===")
    print(texto)
    return modelo


# ============================================================================
# 6. DIAGNÓSTICO DE MULTICOLINEALIDAD — VIF
# ============================================================================

def tabla_vif(df):
    X = add_constant(df[VARIABLES_X])
    vif_valores = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
    tabla = pd.DataFrame({"variable": X.columns, "VIF": vif_valores}).round(2)
    tabla = tabla[tabla["variable"] != "const"].reset_index(drop=True)

    guardar_tabla(tabla, "tabla5_vif_multicolinealidad", incluir_index=False)
    print("\n=== TABLA 5: Factor de Inflación de Varianza (VIF) ===")
    print(tabla)
    print("Regla práctica: VIF > 10 sugiere multicolinealidad problemática entre regresores.")
    return tabla


# ============================================================================
# 7. PROGRAMA PRINCIPAL
# ============================================================================

def main():
    print("Cargando panel procesado...")
    df = cargar_panel()
    print(f"Panel cargado: {len(df)} observaciones, {df['banco'].nunique()} bancos, "
          f"{df['fecha'].nunique()} meses ({df['fecha'].min().strftime('%Y-%m')} a "
          f"{df['fecha'].max().strftime('%Y-%m')}).")

    if WINSORIZAR:
        df = winsorizar(df)

    tabla_estadisticas_descriptivas(df)
    tabla_matriz_correlacion(df)
    tabla_cobertura_panel(df)
    figura_evolucion_sistema(df)
    figuras_dispersion_todas(df)

    df_panel = a_panel_indexado(df)
    pooled, fe, fe2, re = correr_modelos_panel(df_panel)
    tabla_comparacion_modelos({
        "Pooled OLS": pooled,
        "EF (banco)": fe,
        "EF (banco + mes)": fe2,
        "Efectos Aleatorios": re,
    })
    reporte_pruebas_especificacion(df_panel)
    tabla_vif(df)

    print(f"\n{'='*70}")
    print(f"Análisis completo. Todos los archivos guardados en: {DIR_SALIDAS}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()