# ============================================================================
# UNIVERSIDAD NACIONAL DEL CENTRO DEL PERÚ
# Generador integral de entregables para la Carpeta N°3 (Base de datos)
# Nombres y apellidos : Chancha Santiago Alex Omar
# Código de matrícula : 2024200492K
# ----------------------------------------------------------------------------
# 00_generar_entregables_carpeta3.py  (v3)
# Ejecutar AL FINAL (después de 03, 04 y 05): lee el panel procesado y los
# datos del Banco Mundial para que el README y el diccionario muestren cifras
# reales (n.º de bancos, observaciones, cobertura) y no valores escritos a mano.
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
RUTA_PANEL = os.path.join(DIR_BASE, "datos_procesados", "datos_procesados_2024200492K.csv")
RUTA_BM = os.path.join(DIR_BASE, "datos_crudos", "datos_crudos_2024200492K_bancomundial.csv")

print("====================================================================")
print("Generando entregables de la Carpeta N°3...")
print("====================================================================\n")

# ----------------------------------------------------------------------------
# 0. CIFRAS REALES DEL PANEL Y DEL BANCO MUNDIAL
# ----------------------------------------------------------------------------
if not os.path.exists(RUTA_PANEL):
    raise SystemExit(f"[ERROR] No existe {RUTA_PANEL}. Ejecuta antes 03_limpieza_datos.py.")

panel = pd.read_csv(RUTA_PANEL, encoding="utf-8-sig")
bancos = sorted(panel["banco"].unique())
N_BANCOS = len(bancos)
N_OBS = len(panel)
N_MESES = panel["fecha"].nunique()
FECHA_MIN = panel["fecha"].min()[:7]
FECHA_MAX = panel["fecha"].max()[:7]
LISTA_BANCOS = ", ".join(bancos)

meses_por_banco = panel.groupby("banco")["fecha"].nunique()
incompletos = meses_por_banco[meses_por_banco < N_MESES]
if incompletos.empty:
    TEXTO_BALANCE = "panel balanceado"
else:
    detalle = ", ".join(f"{b} ({m} meses)" for b, m in incompletos.items())
    TEXTO_BALANCE = f"panel no balanceado; bancos con menos de {N_MESES} meses: {detalle}"

if os.path.exists(RUTA_BM):
    bm = pd.read_csv(RUTA_BM)
    anios_con_ratio = bm.loc[bm["ratio_capital_global"].notna(), "anio"]
    COBERTURA_BM = (f"{int(bm['anio'].min())}–{int(bm['anio'].max())} "
                    f"(ratio de capital disponible hasta {int(anios_con_ratio.max())})")
else:
    COBERTURA_BM = "archivo no encontrado; ejecutar 01_extraccion_api.py"

print(f"Panel: {N_OBS} observaciones, {N_BANCOS} bancos, {N_MESES} meses ({FECHA_MIN} a {FECHA_MAX})")
print(f"Estructura: {TEXTO_BALANCE}")
print(f"Banco Mundial: {COBERTURA_BM}\n")


# ----------------------------------------------------------------------------
# 1. GENERACIÓN DE .env.example  (valores de referencia usados por los scripts)
# ----------------------------------------------------------------------------
ruta_env = os.path.join(DIR_BASE, ".env.example")
contenido_env = """# Parámetros de referencia de la extracción (los scripts los tienen fijos en
# el código; este archivo documenta los valores usados)
# Finanzas I - UNCP (Chancha Santiago Alex Omar - 2024200492K)

API_WORLD_BANK_URL=https://api.worldbank.org/v2/country/PER/indicator/
SBS_BASE_URL=https://intranet2.sbs.gob.pe/estadistica/financiera/
USER_AGENT=Mozilla/5.0 (investigacion academica UNCP - Finanzas I - Chancha Santiago Alex Omar)
TIMEOUT_SECONDS=30
PAUSA_ENTRE_SOLICITUDES_SEG=1
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
xlrd>=2.0.1
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
#    (string r"""...""" para que "\times" no se convierta en tabulación)
# ----------------------------------------------------------------------------
ruta_incidencias = os.path.join(DIR_BASE, "incidencias_fuente.md")
contenido_incidencias = r"""# Registro de Incidencias de Fuente y Trazabilidad

**Autor:** Chancha Santiago Alex Omar (Código: 2024200492K)  
**Proyecto:** Solvencia bancaria en el Perú (2018-2025)

## Incidencias detectadas y soluciones aplicadas

1. **Abreviatura de marzo en las URL de la SBS:**
   - *Incidencia:* La SBS nombra los archivos de marzo con "ma" (p. ej. `B-2402-ma2024.XLS`). La primera versión del scraper usaba "mr" y los 8 meses de marzo devolvían HTTP 404.
   - *Solución:* Se corrigió la abreviatura en `02_scraping_web.py` y se re-ejecutó la descarga (solo se piden los archivos faltantes).

2. **Formatos de archivo distintos:**
   - *Incidencia:* Los reportes B-2402 y B-2362 son Excel 97-2003 (`.xls` binario) y el B-2201 es Excel 2007+, aunque todos usan la extensión `.XLS`.
   - *Solución:* Se requieren `xlrd` y `openpyxl`; pandas elige el lector según el contenido del archivo.

3. **Ajuste Regulatorio Basilea III (Reporte SBS B-2402):**
   - *Incidencia:* Hasta 2020 el reporte no publica el APR total, solo el requerimiento de patrimonio efectivo; desde 2021 publica directamente el APR.
   - *Solución:* Detección de columnas por texto (no por posición). Para 2018-2020, APR = requerimiento total $\times 10$ (identidad con el mínimo de 10 %).

4. **Divergencia de Formato Institucional en SBS:**
   - *Incidencia:* B-2402 presenta bancos en filas, B-2201 en bloques de columnas (MN / ME / TOTAL) y B-2362 en columnas simples.
   - *Solución:* Una función de lectura específica por reporte en `03_limpieza_datos.py`.

5. **Nombres de entidades no homogéneos:**
   - *Incidencia:* Llamadas de nota al pie pegadas al nombre (`*`, `**`, `1/`, `3/`) y cambios de nombre de una misma entidad: Banco Continental → Banco BBVA Perú, Banco Financiero → Banco Pichincha, Banco Azteca Perú → Alfin Banco, Banco de Comercio → BANCOM.
   - *Solución:* Limpieza de notas al pie con expresión regular y tabla `MAPEO_MANUAL_BANCOS` que une cada entidad bajo su nombre vigente.

6. **Etiqueta distinta de la fila de morosidad total (B-2362):**
   - *Incidencia:* En 2020 y enero 2021 la fila se titula "Total Créditos Directo (En Miles S/)" en lugar de "Total Créditos Directos"; el valor sigue siendo el ratio en %.
   - *Solución:* Búsqueda de la fila con la expresión regular `TOTAL CR[EÉ]DITOS DIRECTO`.

7. **Flujos Acumulados vs. Variables de Stock (ROE en B-2201):**
   - *Incidencia:* El Resultado Neto del Ejercicio es acumulado en el año calendario ($m \in [1, 12]$).
   - *Solución:* Anualización $ROE_{i,t} = \dfrac{U_{i,m} / m \times 12}{Patrimonio_{i,t}} \times 100$.

8. **Selección de bancos, entradas y salidas del sistema:**
   - *Incidencia:* Durante 2018-2025 algunas entidades entran o salen del sistema. Banco Cencosud salió en 2019 y Banco BCI Perú entró en 2022. Bank of China inició operaciones en 2020 y no registró créditos hasta julio de 2021, por lo que no tiene morosidad antes de esa fecha.
   - *Solución:* El estudio se limita a 16 bancos (lista `BANCOS_ESTUDIO`), excluyendo Cencosud y BCI Perú. No se inventan datos para meses en que un banco no operaba: Bank of China entra al panel desde 2021-07 (panel no balanceado). La interpolación lineal intrabanco se aplica solo a huecos internos de hasta 3 meses seguidos, sin extrapolar.

9. **Valores extremos de ROE y ratio de capital:**
   - *Incidencia:* Entidades con patrimonio casi nulo (Alfin Banco 2021-2022) generan ROE de miles de por ciento; bancos recién creados tienen ratios de capital muy altos por su APR pequeño.
   - *Solución:* Winsorización al percentil 1 y 99 de ambas variables en `04_analisis.py` (detalle en `salidas/nota_winsorizacion.txt`).

10. **Sensibilidad de los resultados a la muestra:**
   - *Incidencia:* Los valores extremos de Alfin Banco, la entrada tardía de Bank of China, la pandemia y la reforma de Basilea III de 2023 podrían condicionar los coeficientes estimados.
   - *Solución:* El script `05_robustez.py` reestima el modelo de efectos fijos sin winsorizar, sin Bank of China, sin Alfin Banco, por subperiodos (2018-2022 y 2023-2025) y sin 2020-2021 (detalle en `salidas/tabla9_robustez.txt`).
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
        "Nombre Formal": "Entidad Bancaria de Banca Múltiple",
        "Tipo": "Cualitativa / Identificador",
        "Unidad de Medida": "Texto",
        "Fuente": "SBS Perú (Reportes B-2402, B-2201, B-2362)",
        "Descripción": f"Nombre estandarizado de las {N_BANCOS} entidades del panel: {LISTA_BANCOS}.",
    },
    {
        "Variable Dataset": "fecha",
        "Nombre Formal": "Periodo Mensual",
        "Tipo": "Temporal / Identificador",
        "Unidad de Medida": "YYYY-MM-DD",
        "Fuente": "SBS Perú",
        "Descripción": f"Último día del mes evaluado ({FECHA_MIN} a {FECHA_MAX}).",
    },
    {
        "Variable Dataset": "ratio_capital_global_pct",
        "Nombre Formal": "Ratio de Capital Global",
        "Tipo": "Endógena (Y)",
        "Unidad de Medida": "Porcentaje (%)",
        "Fuente": "SBS Reporte B-2402",
        "Descripción": "Patrimonio Efectivo / APR. Métrica regulatoria principal de solvencia bancaria.",
    },
    {
        "Variable Dataset": "roe_pct",
        "Nombre Formal": "Rentabilidad del Patrimonio (ROE)",
        "Tipo": "Exógena (X1)",
        "Unidad de Medida": "Porcentaje (%)",
        "Fuente": "SBS Reporte B-2201",
        "Descripción": "(Resultado neto acumulado / meses transcurridos × 12) / Patrimonio × 100.",
    },
    {
        "Variable Dataset": "cartera_atrasada_pct",
        "Nombre Formal": "Ratio de Cartera Atrasada",
        "Tipo": "Exógena (X2)",
        "Unidad de Medida": "Porcentaje (%)",
        "Fuente": "SBS Reporte B-2362",
        "Descripción": "Créditos atrasados / Créditos directos totales (fila 'Total Créditos Directos').",
    },
    {
        "Variable Dataset": "apr_total_soles",
        "Nombre Formal": "Activos Ponderados por Riesgo (APR)",
        "Tipo": "Exógena / Control (X3)",
        "Unidad de Medida": "Miles de S/.",
        "Fuente": "SBS Reporte B-2402",
        "Descripción": "Activos y contingentes ponderados por riesgo total (2018-2020: requerimiento total × 10).",
    },
    {
        "Variable Dataset": "ln_apr_total_soles",
        "Nombre Formal": "Logaritmo del Tamaño del Banco",
        "Tipo": "Exógena / Control (X3)",
        "Unidad de Medida": "Logaritmo natural",
        "Fuente": "Transformación propia (04_analisis.py y 05_robustez.py)",
        "Descripción": "ln(apr_total_soles). Escala del banco para controlar heterogeneidad.",
    },
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
    f"Analizar la evolución de la solvencia bancaria en el Perú (medida con el **Ratio de Capital Global**) y su relación con la rentabilidad del patrimonio (**ROE**), el riesgo de crédito (**Cartera Atrasada**) y la escala de la entidad (**ln APR**), para {N_BANCOS} bancos de la banca múltiple entre **enero 2018 y diciembre 2025**.",
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
    f"- **Cobertura:** serie anual Perú, {COBERTURA_BM}",
    "- **Uso:** contexto de largo plazo del sistema bancario peruano; no entra al modelo de panel.",
    "- **Script:** `codigo/01_extraccion_api.py`",
    "- **Salida:** `datos_crudos/datos_crudos_2024200492K_bancomundial.csv`",
    "",
    "### Vía 2 — Scraping programático (SBS Perú)",
    "- **Fuente:** Superintendencia de Banca, Seguros y AFP (SBS) — Reportes estadísticos mensuales",
    "- **URL:** `https://intranet2.sbs.gob.pe/estadistica/financiera/{año}/{Mes}/{reporte}-{mm}{año}.XLS`",
    "  - **Reporte B-2402:** Ratio de Capital Global y Requerimiento de Patrimonio Efectivo / APR",
    "  - **Reporte B-2201:** Balance General y Estado de Ganancias y Pérdidas (para cálculo de ROE)",
    "  - **Reporte B-2362:** Morosidad según tipo y modalidad de crédito (Cartera Atrasada)",
    "- **Cumplimiento ético y técnico:** pausa mínima de 1 segundo entre solicitudes y User-Agent identificatorio. Bitácora en `log_ejecucion.txt`.",
    "- **Script:** `codigo/02_scraping_web.py`",
    "- **Salidas:** archivos `.XLS` en `datos_crudos/sbs_ratio_capital_global/`, `datos_crudos/sbs_roe/` y `datos_crudos/sbs_cartera_atrasada/`",
    "",
    "---",
    "",
    "## Procesamiento y estandarización",
    "- **Script:** `codigo/03_limpieza_datos.py`",
    "- **Lectura por reporte:**",
    "  1. **Ratio de Capital Global y APR (`B-2402`):** bancos en filas; columnas detectadas por texto; APR 2018-2020 = requerimiento total × 10.",
    "  2. **ROE (`B-2201`):** $ROE = (U_m / m \\times 12) / Patrimonio \\times 100$, con $U_m$ el resultado neto acumulado al mes $m$.",
    "  3. **Cartera Atrasada (`B-2362`):** bancos en columnas; fila *Total Créditos Directos*.",
    "- **Homologación de nombres:** limpieza de notas al pie y unión de cambios de nombre (Continental → BBVA, Financiero → Pichincha, Azteca → Alfin, Banco de Comercio → BANCOM). Ver `incidencias_fuente.md`.",
    "- **Selección de bancos:** 16 entidades de banca múltiple; se excluyen Banco Cencosud (salió en 2019) y Banco BCI Perú (entró en 2022).",
    "- **Vacíos:** interpolación lineal intrabanco solo en huecos internos de hasta 3 meses; sin extrapolación.",
    f"- **Estructura final:** {N_OBS} observaciones, {N_BANCOS} bancos, {N_MESES} meses ({FECHA_MIN} a {FECHA_MAX}); {TEXTO_BALANCE}.",
    "- **Salidas:** `datos_procesados/datos_procesados_2024200492K.csv` y versión `.xlsx`.",
    "",
    "---",
    "",
    "## Diccionario de variables del panel",
    "",
    "| Variable | Nombre en dataset | Tipo | Unidad de Medida | Descripción y Fuente SBS |",
    "| :--- | :--- | :--- | :--- | :--- |",
    "| **Solvencia (Y)** | `ratio_capital_global_pct` | Endógena | Porcentaje (%) | Patrimonio efectivo / APR. Reporte B-2402. |",
    "| **Rentabilidad (X1)** | `roe_pct` | Exógena | Porcentaje (%) | Utilidad neta anualizada / Patrimonio $\\times 100$. Reporte B-2201. |",
    "| **Riesgo Crédito (X2)** | `cartera_atrasada_pct` | Exógena | Porcentaje (%) | Créditos atrasados / créditos directos totales. Reporte B-2362. |",
    "| **Escala / Tamaño (X3)** | `apr_total_soles` / `ln_apr_total_soles` | Exógena (Control) | Miles de S/. / Logaritmo | Activos Ponderados por Riesgo Total. Reporte B-2402. |",
    "",
    "---",
    "",
    "## Modelación econométrica y diagnóstico",
    "- **Script:** `codigo/04_analisis.py`",
    "- **Tratamiento de extremos:** winsorización al percentil 1 y 99 del ROE y del ratio de capital (`salidas/nota_winsorizacion.txt`).",
    "- **Modelos de panel:** Pooled OLS, Efectos Fijos por banco, Efectos Fijos de dos vías (banco + mes) y Efectos Aleatorios, con errores estándar robustos agrupados por banco.",
    "- **Elección FE vs. RE:** test de Hausman clásico (covarianzas no robustas) y test de Mundlak robusto a clusters, que es el criterio de decisión.",
    "- **Multicolinealidad:** VIF.",
    "- **Productos en `/salidas`:**",
    "  - `tabla1_estadisticas_descriptivas.csv` / `.xlsx`",
    "  - `tabla2_matriz_correlacion.csv` / `.xlsx`",
    "  - `tabla3_cobertura_panel.csv` / `.xlsx`",
    "  - `tabla4_comparacion_modelos_panel.txt`",
    "  - `tabla5_vif_multicolinealidad.csv` / `.xlsx`",
    "  - `tabla6_test_hausman.txt` y `nota_winsorizacion.txt`",
    "  - `figura1_evolucion_ratio_sistema.png` (ratio del sistema ponderado por APR y mediana) y `figura2` a `figura4` (dispersiones).",
    "",
    "## Pruebas de robustez",
    "- **Script:** `codigo/05_robustez.py`",
    "- **Variantes del modelo de efectos fijos:** base, sin winsorizar, sin Bank of China, sin Alfin Banco, 2018–2022, 2023–2025 y sin 2020–2021, con errores estándar agrupados por banco.",
    "- **Productos en `/salidas`:**",
    "  - `tabla7_evolucion_anual.csv` / `.xlsx`",
    "  - `tabla8_promedios_por_banco.csv` / `.xlsx`",
    "  - `tabla9_robustez.csv` / `.xlsx` / `.txt`",
    "  - `figura5_roe_cartera_evolucion.png`, `figura6_rcg_por_banco.png` y `figura7_robustez_cartera.png`",
    "",
    "---",
    "",
    "## Secuencia de ejecución",
    "Instalar dependencias con `pip install -r requirements.txt` y ejecutar en este orden:",
    "1. `python codigo/01_extraccion_api.py` ➔ Descarga datos agregados del Banco Mundial.",
    "2. `python codigo/02_scraping_web.py` ➔ Descarga los 3 reportes SBS en `/datos_crudos` (omite los ya descargados).",
    "3. `python codigo/03_limpieza_datos.py` ➔ Construye el panel de 4 variables para los 16 bancos.",
    "4. `python codigo/04_analisis.py` ➔ Tablas, figuras, modelos de panel y pruebas de especificación.",
    "5. `python codigo/05_robustez.py` ➔ Evolución anual, promedios por banco, pruebas de robustez y figuras 5 a 7.",
    "6. `python codigo/00_generar_entregables_carpeta3.py` ➔ Actualiza README, diccionario, requirements e incidencias con las cifras del panel.",
    "",
    "---",
    "",
    "## Entorno de ejecución",
    "- **Lenguaje:** Python 3.12+ (Spyder 6 / VS Code)",
    "- **Librerías:** `pandas`, `numpy`, `matplotlib`, `statsmodels`, `linearmodels`, `scipy`, `openpyxl`, `xlrd`, `requests`.",
    "",
    "---",
    "",
    "## Verificación de integridad",
    "- **Archivo de datos principal:** `datos_procesados/datos_procesados_2024200492K.csv`",
    "- **Trazabilidad:** `log_ejecucion.txt` registra cada petición HTTP con fecha, URL y estado.",
    "",
]

ruta_readme = os.path.join(DIR_BASE, "README.md")
with open(ruta_readme, "w", encoding="utf-8") as f:
    f.write("\n".join(lineas_readme))
print(f"✅ Creado/Actualizado: {ruta_readme}")

print("\n====================================================================")
print("¡Todos los entregables para la Carpeta N°3 se han creado con éxito!")
print("====================================================================")