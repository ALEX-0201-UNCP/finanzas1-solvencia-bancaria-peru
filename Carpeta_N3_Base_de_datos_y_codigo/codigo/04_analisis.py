# ============================================================================
# UNIVERSIDAD NACIONAL DEL CENTRO DEL PERÚ
# Facultad de Economía — Escuela Profesional de Economía
# Finanzas I (055D) — Ciclo V — Periodo 2026-II
# ----------------------------------------------------------------------------
# Nombres y apellidos : Chancha Santiago Alex Omar
# Código de matrícula : 2024200492K
# Tema N.º 9 (Unidad I): Solvencia bancaria en el Perú — ratio de capital
#                       global y activos ponderados por riesgo (APR)
# Fecha de extracción : 2026-09-24
# ----------------------------------------------------------------------------
# 04_analisis.py
#
# Qué hace este script:
#   1. Carga el panel de datos procesado (datos_procesados_2024200492K.csv).
#   2. Filtra los bancos pertenecientes al sistema bancario comercial.
#   3. Estima los modelos de Efectos Fijos (FE) y Efectos Aleatorios (RE).
#   4. Realiza la prueba de Hausman para la selección econométrica del modelo.
#   5. Exporta los reportes estadísticos a la carpeta /salidas.
# ============================================================================

import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
from linearmodels.panel import PanelOLS, RandomEffects
from scipy import stats

# ============================================================================
# 1. CONFIGURACIÓN DE RUTAS
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
RUTA_PANEL = os.path.join(DIR_BASE, "datos_procesados", "datos_procesados_2024200492K.csv")
DIR_SALIDAS = os.path.join(DIR_BASE, "salidas")

os.makedirs(DIR_SALIDAS, exist_ok=True)

print("-> Cargando el panel de datos procesado...")
df = pd.read_csv(RUTA_PANEL)

# ============================================================================
# 2. FILTRADO EXCLUSIVO DE LOS BANCOS MÚLTIPLES
# ============================================================================

BANCOS_OBJETIVO = [
    "BBVA", "CRÉDITO", "CREDITO", "INTERBANK", "SCOTIABANK", "BIF", "BANBIF",
    "PICHINCHA", "GNB", "FALABELLA", "RIPLEY", "SANTANDER", "ALFIN", "AZTECA",
    "COMMERZBANK", "ICBC", "BANK OF CHINA", "MIBANCO"
]

patron_bancos = "|".join(BANCOS_OBJETIVO)
df = df[df["banco"].str.upper().str.contains(patron_bancos, na=False)].copy()

print(f"-> Entidades identificadas en la muestra ({df['banco'].nunique()} entidades):")
for banco in sorted(df["banco"].unique()):
    print(f"   - {banco}")

# ============================================================================
# 3. PREPARACIÓN DEL PANEL DE DATOS
# ============================================================================

df["fecha"] = pd.to_datetime(df["fecha"])
df = df.set_index(["banco", "fecha"])

# Variable Endógena (Dependiente)
y = df["ratio_capital_global_pct"]

# Variables Exógenas (Independientes)
X = df[[
    "patrimonio_efectivo_nivel1_apr_pct",
    "capital_ordinario_nivel1_apr_pct",
    "apr_total"
]]
X = sm.add_constant(X)

print(f"\nTotal de observaciones utilizadas en el modelo econométrico: {len(df)}")

# ============================================================================
# 4. ESTIMACIÓN: MODELO DE EFECTOS FIJOS (WITHIN)
# ============================================================================

print("\n" + "=" * 60)
print("=== ESTIMACIÓN: MODELO DE EFECTOS FIJOS ===")
print("=" * 60)
modelo_fe = PanelOLS(y, X, entity_effects=True, time_effects=False)
resultado_fe = modelo_fe.fit(cov_type="robust")
print(resultado_fe)

ruta_salida_fe = os.path.join(DIR_SALIDAS, "resultado_efectos_fijos.txt")
with open(ruta_salida_fe, "w", encoding="utf-8") as f:
    f.write(str(resultado_fe))

# ============================================================================
# 5. ESTIMACIÓN: MODELO DE EFECTOS ALEATORIOS
# ============================================================================

print("\n" + "=" * 60)
print("=== ESTIMACIÓN: MODELO DE EFECTOS ALEATORIOS ===")
print("=" * 60)
modelo_re = RandomEffects(y, X)
resultado_re = modelo_re.fit()
print(resultado_re)

ruta_salida_re = os.path.join(DIR_SALIDAS, "resultado_efectos_aleatorios.txt")
with open(ruta_salida_re, "w", encoding="utf-8") as f:
    f.write(str(resultado_re))

# ============================================================================
# 6. PRUEBA DE HAUSMAN (DECISIÓN ENTRE FE Y RE)
# ============================================================================

print("\n" + "=" * 60)
print("=== PRUEBA DE HAUSMAN ===")
print("=" * 60)

b_fe = resultado_fe.params
b_re = resultado_re.params

comunes = b_fe.index.intersection(b_re.index)
b_diff = b_fe[comunes] - b_re[comunes]

cov_fe = resultado_fe.cov.loc[comunes, comunes]
cov_re = resultado_re.cov.loc[comunes, comunes]

diff_cov = cov_fe - cov_re
stat_hausman = b_diff.dot(np.linalg.pinv(diff_cov)).dot(b_diff)
grados_libertad = len(comunes)
p_valor_hausman = 1 - stats.chi2.cdf(stat_hausman, grados_libertad)

print(f"Estadístico de Chi-cuadrado de Hausman: {stat_hausman:.4f}")
print(f"Grados de libertad: {grados_libertad}")
print(f"P-valor: {p_valor_hausman:.4f}")

if p_valor_hausman < 0.05:
    resumen_hausman = "Resultado: Se rechaza H0 (p-valor < 0.05). El modelo de EFECTOS FIJOS es el adecuado."
else:
    resumen_hausman = "Resultado: No se rechaza H0 (p-valor >= 0.05). El modelo de EFECTOS ALEATORIOS es preferido."

print(f"\n-> {resumen_hausman}")

# Guardar reporte completo de la Prueba de Hausman
ruta_salida_hausman = os.path.join(DIR_SALIDAS, "resultado_prueba_hausman.txt")
with open(ruta_salida_hausman, "w", encoding="utf-8") as f:
    f.write("=== PRUEBA DE HAUSMAN ===\n")
    f.write(f"Estadistico Chi2 : {stat_hausman:.4f}\n")
    f.write(f"Grados libertad  : {grados_libertad}\n")
    f.write(f"P-valor          : {p_valor_hausman:.4f}\n\n")
    f.write(f"{resumen_hausman}\n")

print("\n" + "=" * 60)
print("¡Análisis econométrico finalizado! Resultados guardados en /salidas.")
print("=" * 60)