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
# 05_analisis_econometrico.py
#
# Pregunta de investigación:
#   "Analizar la evolución de la solvencia bancaria en el Perú y su
#    relación con la rentabilidad y el riesgo de crédito."
#
# Modelo:
#   ratio_capital_global_pct_it = β0 + β1·roe_pct_it + β2·cartera_atrasada_pct_it
#                                  + β3·ln(apr_total_soles_it) + u_it
#
#   Y  (endógena)              : ratio_capital_global_pct   (solvencia)
#   X1 (exógena)                : roe_pct                    (rentabilidad)
#   X2 (exógena)                : cartera_atrasada_pct       (riesgo de crédito)
#   X3 (control de tamaño)      : ln(apr_total_soles)        (log del tamaño del
#                                  banco; se usa log porque el tamaño de los
#                                  bancos varía en varios órdenes de magnitud
#                                  — de Citibank/ICBC a BCP/BBVA — y el log
#                                  estabiliza esa dispersión, práctica estándar
#                                  para variables de tamaño en panel data)
#
# Qué hace este script:
#   1. Carga el panel balanceado banco x mes (2018-2025) generado por
#      03_limpieza_datos.py.
#   2. Tabla 1: estadística descriptiva de las 4 variables.
#   3. Tabla 2: matriz de correlación de Pearson.
#   4. Figura 1: evolución del ratio de capital global promedio del sistema.
#   5. Figuras 2-4: dispersión de la Y contra cada X, con línea de tendencia.
#   6. Regresión de panel data: Pooled OLS, Efectos Fijos (FE) y Efectos
#      Aleatorios (RE), con errores estándar robustos agrupados por banco
#      (cluster por entidad), y Test de Hausman para decidir entre FE y RE.
#   7. VIF (factor de inflación de varianza) para descartar multicolinealidad.
#
# Requiere: pandas, numpy, matplotlib, statsmodels, linearmodels
#   pip install pandas numpy matplotlib statsmodels linearmodels
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
        "    pip install statsmodels linearmodels scipy\n\n"
        f"Detalle del error: {error}\n"
    )
 
 
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
DIR_SALIDAS = os.path.join(DIR_BASE, "salidas")
os.makedirs(DIR_SALIDAS, exist_ok=True)
 
plt.rcParams["figure.dpi"] = 120
plt.rcParams["font.size"] = 10
 
VARIABLE_Y = "ratio_capital_global_pct"
VARIABLES_X = ["roe_pct", "cartera_atrasada_pct", "ln_apr_total_soles"]
 
 
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
            f"¿Es el CSV generado por 03_limpieza_datos.py (v3)?"
        )
 
    df["ln_apr_total_soles"] = np.log(df["apr_total_soles"])
 
    df = df.sort_values(["banco", "fecha"]).reset_index(drop=True)
    return df
 
 
def a_panel_indexado(df):
    """Convierte el DataFrame plano a MultiIndex (banco, fecha), formato
    que exige linearmodels para tratar los datos como panel data."""
    df_panel = df.set_index(["banco", "fecha"])
    return df_panel
 
 
# ============================================================================
# 3. TABLA 1 — ESTADÍSTICA DESCRIPTIVA
# ============================================================================
 
def tabla_estadisticas_descriptivas(df):
    columnas = [VARIABLE_Y, "roe_pct", "cartera_atrasada_pct", "apr_total_soles"]
    tabla = df[columnas].describe().T.round(2)
    tabla.columns = ["n", "media", "desv_estandar", "minimo", "p25", "mediana", "p75", "maximo"]
    tabla.index = [
        "Ratio de Capital Global (%)",
        "ROE anualizado (%)",
        "Cartera Atrasada (%)",
        "APR total (miles de S/.)",
    ]
    tabla.index.name = "variable"
 
    guardar_tabla(tabla, "tabla1_estadisticas_descriptivas")
    print("\n=== TABLA 1: Estadística descriptiva (panel completo, 2018-2025) ===")
    print(tabla)
    return tabla
 
 
# ============================================================================
# 4. TABLA 2 — MATRIZ DE CORRELACIÓN
# ============================================================================
 
def tabla_matriz_correlacion(df):
    columnas = [VARIABLE_Y, "roe_pct", "cartera_atrasada_pct", "apr_total_soles"]
    etiquetas = ["Ratio Capital Global", "ROE", "Cartera Atrasada", "APR total"]
    matriz = df[columnas].corr(method="pearson").round(3)
    matriz.index = etiquetas
    matriz.columns = etiquetas
 
    guardar_tabla(matriz, "tabla2_matriz_correlacion")
    print("\n=== TABLA 2: Matriz de correlación de Pearson ===")
    print(matriz)
    return matriz
 
 
# ============================================================================
# 5. FIGURA 1 — EVOLUCIÓN DEL SISTEMA
# ============================================================================
 
def figura_evolucion_sistema(df):
    serie_mensual = df.groupby("fecha")[VARIABLE_Y].mean()
 
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
# 6. FIGURAS 2-4 — DISPERSIÓN Y vs. CADA X
# ============================================================================
 
def figura_dispersión(df, variable_x, etiqueta_x, nombre_archivo, titulo):
    x = df[variable_x].values
    y = df[VARIABLE_Y].values
 
    plt.figure(figsize=(7, 5.5))
    plt.scatter(x, y, s=18, alpha=0.4, color="#1f4e79", edgecolors="none")
 
    coef = np.polyfit(x, y, 1)
    x_linea = np.linspace(x.min(), x.max(), 100)
    plt.plot(x_linea, np.polyval(coef, x_linea), color="red", linewidth=1.5,
              label=f"Tendencia lineal (pendiente = {coef[0]:.3f})")
 
    plt.title(titulo)
    plt.xlabel(etiqueta_x)
    plt.ylabel("Ratio de Capital Global (%)")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    ruta = os.path.join(DIR_SALIDAS, nombre_archivo)
    plt.savefig(ruta)
    plt.close()
    print(f"Figura guardada en: {ruta}")
 
 
def figuras_dispersión_todas(df):
    figura_dispersión(df, "roe_pct", "ROE anualizado (%)",
                       "figura2_roe_vs_solvencia.png",
                       "Rentabilidad (ROE) vs. Solvencia (Ratio de Capital Global)")
    figura_dispersión(df, "cartera_atrasada_pct", "Cartera Atrasada (%)",
                       "figura3_morosidad_vs_solvencia.png",
                       "Riesgo de Crédito (Cartera Atrasada) vs. Solvencia")
    figura_dispersión(df, "ln_apr_total_soles", "ln(APR total, miles de S/.)",
                       "figura4_tamano_vs_solvencia.png",
                       "Tamaño del Banco (ln APR) vs. Solvencia")
 
 
# ============================================================================
# 7. REGRESIÓN DE PANEL DATA: POOLED OLS, EFECTOS FIJOS, EFECTOS ALEATORIOS
# ============================================================================
 
def correr_modelos_panel(df_panel):
    y = df_panel[VARIABLE_Y]
    X = add_constant(df_panel[VARIABLES_X])
 
    print("\nEstimando Pooled OLS...")
    modelo_pooled = PooledOLS(y, X).fit(cov_type="clustered", cluster_entity=True)
 
    print("Estimando Efectos Fijos (entidad)...")
    modelo_fe = PanelOLS(y, X, entity_effects=True, drop_absorbed=True).fit(
        cov_type="clustered", cluster_entity=True
    )
 
    print("Estimando Efectos Aleatorios...")
    modelo_re = RandomEffects(y, X).fit(cov_type="clustered", cluster_entity=True)
 
    return modelo_pooled, modelo_fe, modelo_re
 
 
def prueba_hausman(modelo_fe, modelo_re):
    """Test de Hausman manual (linearmodels no lo trae incorporado):
    H0: los efectos individuales NO están correlacionados con los
        regresores -> Efectos Aleatorios es eficiente y consistente.
    H1: sí están correlacionados -> solo Efectos Fijos es consistente.
    Si p-valor < 0.05, se rechaza H0 y se debe reportar el modelo de
    Efectos Fijos."""
    # Se excluye 'const': en Efectos Fijos el intercepto queda absorbido por
    # los efectos de cada banco y no es comparable con el de Efectos
    # Aleatorios, por lo que el test se hace solo sobre las pendientes.
    parametros_comunes = [p for p in modelo_fe.params.index
                           if p in modelo_re.params.index and p != "const"]
 
    b_fe = modelo_fe.params[parametros_comunes]
    b_re = modelo_re.params[parametros_comunes]
    cov_fe = modelo_fe.cov.loc[parametros_comunes, parametros_comunes]
    cov_re = modelo_re.cov.loc[parametros_comunes, parametros_comunes]
 
    diferencia = (b_fe - b_re).values
    cov_diferencia = (cov_fe - cov_re).values
 
    try:
        inv_cov_diferencia = np.linalg.inv(cov_diferencia)
    except np.linalg.LinAlgError:
        inv_cov_diferencia = np.linalg.pinv(cov_diferencia)
 
    estadistico = float(diferencia.T @ inv_cov_diferencia @ diferencia)
    grados_libertad = len(parametros_comunes)
    p_valor = float(1 - sp_stats.chi2.cdf(estadistico, grados_libertad))
 
    return estadistico, grados_libertad, p_valor
 
 
def tabla_comparacion_modelos(modelo_pooled, modelo_fe, modelo_re):
    comparacion = compare(
        {"Pooled OLS": modelo_pooled, "Efectos Fijos": modelo_fe, "Efectos Aleatorios": modelo_re}
    )
    texto_comparacion = str(comparacion)
    guardar_texto(texto_comparacion, "tabla4_comparacion_modelos_panel")
    print("\n=== TABLA 4: Comparación Pooled OLS vs. Efectos Fijos vs. Efectos Aleatorios ===")
    print(texto_comparacion)
    return comparacion
 
 
# ============================================================================
# 8. DIAGNÓSTICO DE MULTICOLINEALIDAD — VIF
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
# 9. PROGRAMA PRINCIPAL
# ============================================================================
 
def main():
    print("Cargando panel procesado...")
    df = cargar_panel()
    print(f"Panel cargado: {len(df)} observaciones, {df['banco'].nunique()} bancos, "
          f"{df['fecha'].nunique()} meses ({df['fecha'].min().strftime('%Y-%m')} a "
          f"{df['fecha'].max().strftime('%Y-%m')}).\n")
 
    tabla_estadisticas_descriptivas(df)
    tabla_matriz_correlacion(df)
    figura_evolucion_sistema(df)
    figuras_dispersión_todas(df)
 
    df_panel = a_panel_indexado(df)
    modelo_pooled, modelo_fe, modelo_re = correr_modelos_panel(df_panel)
    tabla_comparacion_modelos(modelo_pooled, modelo_fe, modelo_re)
 
    estadistico, gl, p_valor = prueba_hausman(modelo_fe, modelo_re)
    print("\n=== TEST DE HAUSMAN (Efectos Fijos vs. Efectos Aleatorios) ===")
    print(f"Estadístico chi2 = {estadistico:.4f}  |  g.l. = {gl}  |  p-valor = {p_valor:.4f}")
    if p_valor < 0.05:
        print("=> p-valor < 0.05: se RECHAZA H0. El modelo consistente y apropiado "
              "para reportar en el artículo es EFECTOS FIJOS.")
    else:
        print("=> p-valor >= 0.05: NO se rechaza H0. El modelo más eficiente y "
              "apropiado para reportar en el artículo es EFECTOS ALEATORIOS.")
 
    texto_hausman = (
        f"Test de Hausman (Efectos Fijos vs. Efectos Aleatorios)\n"
        f"Estadistico chi2 = {estadistico:.4f}\n"
        f"Grados de libertad = {gl}\n"
        f"p-valor = {p_valor:.4f}\n"
        f"Conclusion: modelo recomendado = "
        f"{'Efectos Fijos' if p_valor < 0.05 else 'Efectos Aleatorios'}\n"
    )
    guardar_texto(texto_hausman, "tabla6_test_hausman")
 
    tabla_vif(df)
 
    print(f"\n{'='*70}")
    print(f"Análisis completo. Todos los archivos guardados en: {DIR_SALIDAS}")
    print(f"{'='*70}")
 
 
if __name__ == "__main__":
    main()
 