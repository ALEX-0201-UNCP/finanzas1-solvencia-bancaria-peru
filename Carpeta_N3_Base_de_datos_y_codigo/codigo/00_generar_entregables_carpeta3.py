# ============================================================================
# UNIVERSIDAD NACIONAL DEL CENTRO DEL PERÚ
# Generador integral de entregables para la Carpeta N°3 (Base de datos)
# Nombres y apellidos : Chancha Santiago Alex Omar
# Código de matrícula : 2024200492K
# ============================================================================

import os
import pandas as pd

def obtener_directorio_base():
    try:
        dir_actual = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        dir_actual = os.getcwd()
    if os.path.basename(dir_actual).lower() == "codigo":
        return os.path.dirname(dir_actual)
    return dir_actual

DIR_BASE = obtener_directorio_base()

print("====================================================================")
print("Generando entregables de la Carpeta N°3...")
print("====================================================================\n")

# ----------------------------------------------------------------------------
# 1. GENERACIÓN DE .env.example
# ----------------------------------------------------------------------------
ruta_env = os.path.join(DIR_BASE, ".env.example")
contenido_env = """# Configuración de variables de entorno (Ejemplo)
# Finanzas I - UNCP (Chancha Santiago Alex Omar - 2024200492K)

API_WORLD_BANK_URL=https://api.worldbank.org/v2/country/PER/indicator/
SBS_BASE_URL=https://www.sbs.gob.pe/app/stats_net/
USER_AGENT=UNCP_Finanzas1_Research_Bot/1.0
TIMEOUT_SECONDS=30
MAX_RETRIES=3
"""
with open(ruta_env, "w", encoding="utf-8") as f:
    f.write(contenido_env)
print(f"✅ Creado/Actualizado: {ruta_env}")


# ----------------------------------------------------------------------------
# 2. GENERACIÓN DE requirements.txt
# ----------------------------------------------------------------------------
ruta_req = os.path.join(DIR_BASE, "requirements.txt")
contenido_req = """# Entorno de ejecución Finanzas I - UNCP
# Chancha Santiago Alex Omar (2024200492K)

pandas>=2.0.0
numpy>=1.24.0
requests>=2.28.0
openpyxl>=3.1.0
matplotlib>=3.7.0
statsmodels>=0.14.0
linearmodels>=5.3
scipy>=1.10.0
"""
with open(ruta_req, "w", encoding="utf-8") as f:
    f.write(contenido_req)
print(f"✅ Creado/Actualizado: {ruta_req}")


# ----------------------------------------------------------------------------
# 3. GENERACIÓN DE incidencias_fuente.md
# ----------------------------------------------------------------------------
ruta_incidencias = os.path.join(DIR_BASE, "incidencias_fuente.md")
contenido_incidencias = """# Registro de Incidencias de Fuente y Trazabilidad

**Autor:** Chancha Santiago Alex Omar (Código: 2024200492K)  
**Proyecto:** Solvencia bancaria en el Perú (2018-2025)

## Summary de Incidencias Detectadas y Soluciones Aplicadas

1. **Ajuste Regulatorio Basilea III (Reporte SBS B-2402):**
   - *Incidencia:* Cambio en la estructura de presentación de cuentas y requerimientos a partir del proceso de implementación gradual de Basilea III en el sistema financiero peruano.
   - *Solución:* Detección dinámica de filas/columnas clave dentro del parser de pandas y estandarización a la variable de Activos Ponderados por Riesgo (APR) equivalente.

2. **Divergencia de Formato Institucional en SBS:**
   - *Incidencia:* Los reportes `B-2402` y `B-2201` presentan entidades bancarias organizadas en filas, mientras que el reporte de morosidad `B-2362` ubica a las entidades en columnas.
   - *Solución:* Procesamiento diferenciado mediante funciones específicas de trasposición y limpieza sintáctica por tipo de reporte en `03_limpieza_datos.py`.

3. **Flujos Acumulados vs. Variables de Stock (ROE en B-2201):**
   - *Incidencia:* La cuenta de Utilidad Neta en el Estado de Ganancias y Pérdidas se reporta como saldo acumulado en el año calendario ($m \in [1, 12]$).
   - *Solución:* Anualización exacta del flujo mensual ($U_{n, m} / m \times 12$) antes de calcular la razón sobre el Patrimonio para evitar sesgo de estacionalidad.

4. **Tratamiento de Vacíos Estadísticos (Panel Balanceado):**
   - *Incidencia:* Presencia eventual de celdas no reportadas en periodos específicos de transición de entidades de menor escala.
   - *Solución:* Interpolación lineal intrabanco sobre series temporales para garantizar un panel balanceado ($N \times T$) válido econométricamente.
"""
with open(ruta_incidencias, "w", encoding="utf-8") as f:
    f.write(contenido_incidencias)
print(f"✅ Creado/Actualizado: {ruta_incidencias}")


# ----------------------------------------------------------------------------
# 4. GENERACIÓN DE diccionario_variables.xlsx / .csv
# ----------------------------------------------------------------------------
datos_diccionario = [
    {
        "Variable Dataset": "banco",
        "Nombre Formal": "Entidad Bancaria",
        "Tipo": "Cualitativa / Identificador",
        "Unidad de Medida": "Texto",
        "Fuente": "SBS Perú",
        "Descripción": "Nombre estandarizado de la institución de banca múltiple."
    },
    {
        "Variable Dataset": "fecha",
        "Nombre Formal": "Periodo Mensual",
        "Tipo": "Temporal / Identificador",
        "Unidad de Medida": "YYYY-MM-DD",
        "Fuente": "SBS Perú",
        "Descripción": "Fecha correspondiente al último día del mes evaluado (2018-01 a 2025-12)."
    },
    {
        "Variable Dataset": "ratio_capital_global_pct",
        "Nombre Formal": "Ratio de Capital Global",
        "Tipo": "Endógena (Y)",
        "Unidad de Medida": "Porcentaje (%)",
        "Fuente": "SBS Reporte B-2402",
        "Descripción": "Patrimonio Efectivo / APR. Métrica regulatoria principal de solvencia bancaria."
    },
    {
        "Variable Dataset": "roe_pct",
        "Nombre Formal": "Rentabilidad del Patrimonio (ROE)",
        "Tipo": "Exógena (X1)",
        "Unidad de Medida": "Porcentaje (%)",
        "Fuente": "SBS Reporte B-2201",
        "Descripción": "(Utilidad Neta Anualizada / Patrimonio) * 100. Métrica de rentabilidad bancaria."
    },
    {
        "Variable Dataset": "cartera_atrasada_pct",
        "Nombre Formal": "Ratio de Cartera Atrasada",
        "Tipo": "Exógena (X2)",
        "Unidad de Medida": "Porcentaje (%)",
        "Fuente": "SBS Reporte B-2362",
        "Descripción": "Total Créditos Atrasados / Total Créditos Directos. Métrica de riesgo de crédito."
    },
    {
        "Variable Dataset": "apr_total_soles",
        "Nombre Formal": "Activos Ponderados por Riesgo (APR)",
        "Tipo": "Exógena / Control (X3)",
        "Unidad de Medida": "Miles de S/.",
        "Fuente": "SBS Reporte B-2402",
        "Descripción": "Suma total de activos y contingentes ponderados por riesgo del banco."
    },
    {
        "Variable Dataset": "ln_apr_total_soles",
        "Nombre Formal": "Logaritmo del Tamaño del Banco",
        "Tipo": "Exógena / Control (X3)",
        "Unidad de Medida": "Logaritmo natural",
        "Fuente": "Transformación propia",
        "Descripción": "ln(apr_total_soles). Escala operativa del banco para controlar heterogeneidad."
    },
    {
    "Variable Dataset": "banco",
    "Nombre Formal": "Entidad Bancaria de Banca Múltiple",
    "Tipo": "Cualitativa / Identificador",
    "Unidad de Medida": "Texto",
    "Fuente": "SBS Perú (Reportes B-2402, B-2201, B-2362)",
    "Descripción": "Nombre estandarizado de las 16 instituciones de banca múltiple evaluadas en el Perú (BCP, BBVA, Interbank, Scotiabank, BanBif, Pichincha, Mibanco, GNB, Falabella, Ripley, Bancom, Alfin, Citibank, ICBC, Santander, Bank of China)."
}
]


df_diccionario = pd.DataFrame(datos_diccionario)
ruta_dicc_xlsx = os.path.join(DIR_BASE, "diccionario_variables.xlsx")
ruta_dicc_csv = os.path.join(DIR_BASE, "diccionario_variables.csv")

df_diccionario.to_excel(ruta_dicc_xlsx, index=False)
df_diccionario.to_csv(ruta_dicc_csv, index=False, encoding="utf-8-sig")
print(f"✅ Creado/Actualizado: {ruta_dicc_xlsx}")
print(f"✅ Creado/Actualizado: {ruta_dicc_csv}")


# ----------------------------------------------------------------------------
# 5. GENERACIÓN DE README.md
# ----------------------------------------------------------------------------
lineas_readme = [
    "# Solvencia bancaria en el Perú: ratio de capital global, rentabilidad y riesgo de crédito (2018-2025)",
    "",
    "**Nombres y apellidos:** Chancha Santiago Alex Omar  ",
    "**Código de matrícula:** 2024200492K  ",
    "**Curso:** Finanzas I (055D) — Ciclo V, Escuela Profesional de Economía, UNCP  ",
    "**Docente:** Dr. Ciro Iván Machacuay Meza  ",
    "**Tema N.º 9 del temario, Unidad I:** Solvencia bancaria en el Perú — ratio de capital global y activos ponderados por riesgo (APR)  ",
    "**Fecha de corte de extracción:** 2026-09-26  ",
    "**Repositorio GitHub:** https://github.com/ALEX-0201-UNCP/finanzas1-solvencia-bancaria-peru  ",
    "",
    "---",
    "",
    "## Objetivo de la investigación",
    "Analizar los determinantes econométricos y la evolución de la solvencia bancaria en el Perú (medida a través del **Ratio de Capital Global**) y su relación con la rentabilidad del patrimonio (**ROE**), el riesgo de crédito (**Cartera Atrasada / Morosidad**) y la escala de la entidad (**ln APR**), para el sistema de banca múltiple durante el periodo **enero 2018 – diciembre 2025 (96 meses)**.",
    "",
    "---",
    "",
    "## Fuentes de datos y estrategia de extracción",
    "",
    "### Vía 1 — API (Banco Mundial, base GFDD)",
    "- **Fuente:** World Bank Open Data — Global Financial Development Database (GFDD)",
    "- **Endpoint base:** `https://api.worldbank.org/v2/country/PER/indicator/{codigo}`",
    "- **Indicadores agregados extraídos:**",
    "  - `GFDD.SI.05`: Bank regulatory capital to risk-weighted assets (%)",
    "  - `GFDD.SI.03`: Bank capital to total assets (%)",
    "  - `GFDD.SI.02`: Bank nonperforming loans to gross loans (%)",
    "  - `GFDD.EI.05`: Bank return on assets (%)",
    "  - `GFDD.EI.06`: Bank return on equity (%)",
    "- **Cobertura:** Serie anual Perú (2000–2025)",
    "- **Script:** `codigo/01_extraccion_api.py`",
    "- **Salida:** `datos_crudos/datos_crudos_2024200492K_bancomundial.csv`",
    "",
    "### Vía 2 — Scraping programático (SBS Perú)",
    "- **Fuente:** Superintendencia de Banca, Seguros y AFP (SBS) — Reportes estadísticos mensuales",
    "- **Estructura de endpoints consultados:**",
    "  - **Reporte B-2402:** Ratio de Capital Global y Requerimiento de Patrimonio Efectivo / APR",
    "  - **Reporte B-2201:** Balance General y Estado de Ganancias y Pérdidas (para cálculo de ROE)",
    "  - **Reporte B-2362:** Morosidad según tipo y modalidad de crédito (Cartera Atrasada)",
    "- **Cumplimiento ético y técnico:** Pausa mínima de 1 segundo entre solicitudes HTTP y User-Agent identificatorio. Bitácora de auditoría en `log_ejecucion.txt`.",
    "- **Script:** `codigo/02_scraping_web.py`",
    "- **Salidas:** Archivos `.XLS` organizados en:",
    "  - `datos_crudos/sbs_ratio_capital_global/`",
    "  - `datos_crudos/sbs_roe/`",
    "  - `datos_crudos/sbs_cartera_atrasada/`",
    "",
    "---",
    "",
    "## Procesamiento, estandarización y completado estadístico",
    "- **Script:** `codigo/03_limpieza_datos.py`",
    "- **Lectura y procesamiento heterogéneo por reporte:**",
    "  1. **Ratio de Capital Global y APR (`B-2402`):** Lectura de entidades en filas, ajuste dinámico por regulación Basilea III y conversión histórica a APR.",
    "  2. **ROE (`B-2201`):** Anualización del flujo acumulado de Resultado Neto ($U_n / m \\times 12$) sobre el Patrimonio del mes.",
    "  3. **Cartera Atrasada (`B-2362`):** Lectura de entidades en columnas; extracción de la fila *Total Créditos Directos*.",
    "- **Completado de periodos y balanceo de panel:** Relleno de vacíos mediante **interpolación lineal intrabanco** autorizada para consolidar un panel balanceado.",
    "- **Estructura final del dataset:** Panel balanceado ($N \\times T$, banco $\\times$ mes, 2018-01 a 2025-12).",
    "- **Salidas guardadas:** `datos_procesados/datos_procesados_2024200492K.csv` y versión `.xlsx`.",
    "",
    "---",
    "",
    "## Diccionario de variables del panel",
    "",
    "| Variable | Nombre en dataset | Tipo | Unidad de Medida | Descripción y Fuente SBS |",
    "| :--- | :--- | :--- | :--- | :--- |",
    "| **Solvencia (Y)** | `ratio_capital_global_pct` | Endógena | Porcentaje (%) | Patrimonio efectivo / APR. Reporte B-2402. |",
    "| **Rentabilidad (X1)** | `roe_pct` | Exógena | Porcentaje (%) | (Utilidad Neta anualizada / Patrimonio) $\\times 100$. Reporte B-2201. |",
    "| **Riesgo Crédito (X2)** | `cartera_atrasada_pct` | Exógena | Porcentaje (%) | Morosidad sobre créditos directos totales. Reporte B-2362. |",
    "| **Escala / Tamaño (X3)** | `apr_total_soles` / `ln_apr_total_soles` | Exógena (Control) | Miles de S/. / Logaritmo | Activos Ponderados por Riesgo Total. Reporte B-2402. |",
    "",
    "---",
    "",
    "## Modelación econométrica y diagnóstico",
    "- **Script:** `codigo/05_analisis_econometrico.py`",
    "- **Modelos de datos de panel estimados:**",
    "  - **Pooled OLS**, **Efectos Fijos (FE)** y **Efectos Aleatorios (RE)** con errores estándar robustos agrupados por banco (`cov_type=clustered`).",
    "  - **Prueba de Hausman:** Evaluada sobre la diferencia de matrices de covarianza de los estimadores para elegir de forma rigurosa entre FE y RE.",
    "  - **Diagnóstico de multicolinealidad:** Cálculo del **VIF** (Factor de Inflación de Varianza).",
    "- **Productos generados en `/salidas`:**",
    "  - `tabla1_estadisticas_descriptivas.csv` / `.xlsx`",
    "  - `tabla2_matriz_correlacion.csv` / `.xlsx`",
    "  - `tabla4_comparacion_modelos_panel.txt`",
    "  - `tabla5_vif_multicolinealidad.csv` / `.xlsx`",
    "  - `tabla6_test_hausman.txt`",
    "  - Salidas gráficas PNG (`figura1` a `figura4`) de evolución del sistema y dispersiones con líneas de tendencia.",
    "",
    "---",
    "",
    "## Secuencia de ejecución",
    "Para reproducir la totalidad del trabajo desde cero, ejecute los scripts en el siguiente orden:",
    "1. `python codigo/01_extraccion_api.py` ➔ Descarga datos macro del Banco Mundial.",
    "2. `python codigo/02_scraping_web.py` ➔ Descarga los 3 reportes SBS (`B-2402`, `B-2201`, `B-2362`) en `/datos_crudos`.",
    "3. `python codigo/03_limpieza_datos.py` ➔ Procesa y consolida el panel balanceado de 4 variables.",
    "4. `python codigo/05_analisis_econometrico.py` ➔ Ejecuta los modelos econométricos (Pooled OLS, FE, RE), VIF, test de Hausman y gráficos.",
    "5. `python codigo/00_generar_entregables_carpeta3.py` ➔ Genera/actualiza todos los archivos de documentación de la Carpeta N°3.",
    "",
    "---",
    "",
    "## Entorno de ejecución",
    "- **Lenguaje:** Python 3.12+ (Spyder 6 / VS Code)",
    "- **Librerías principales:** `pandas`, `numpy`, `matplotlib`, `statsmodels`, `linearmodels`, `scipy`, `openpyxl`, `requests`.",
    "",
    "---",
    "",
    "## Verificación de integridad",
    "- **Archivo de datos principal:** `datos_procesados/datos_procesados_2024200492K.csv`",
    "- **Trazabilidad:** Verificada en `log_ejecucion.txt` con registro completo de peticiones HTTP, estado y tiempos de descarga."
]

ruta_readme = os.path.join(DIR_BASE, "README.md")
with open(ruta_readme, "w", encoding="utf-8") as f:
    f.write("\n".join(lineas_readme))
print(f"✅ Creado/Actualizado: {ruta_readme}")

print("\n====================================================================")
print("¡Todos los entregables para la Carpeta N°3 se han creado con éxito!")
print("====================================================================")