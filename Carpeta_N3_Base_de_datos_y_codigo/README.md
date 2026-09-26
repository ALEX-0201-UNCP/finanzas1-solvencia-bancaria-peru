# Solvencia bancaria en el Perú: ratio de capital global, rentabilidad y riesgo de crédito (2018-2025)

**Nombres y apellidos:** Chancha Santiago Alex Omar  
**Código de matrícula:** 2024200492K  
**Curso:** Finanzas I (055D) — Ciclo V, Escuela Profesional de Economía, UNCP  
**Docente:** Dr. Ciro Iván Machacuay Meza  
**Tema N.º 9 del temario, Unidad I:** Solvencia bancaria en el Perú — ratio de capital global y activos ponderados por riesgo (APR)  
**Fecha de corte de extracción:** 2026-09-26  
**Repositorio GitHub:** https://github.com/ALEX-0201-UNCP/finanzas1-solvencia-bancaria-peru  

---

## Objetivo de la investigación
Analizar los determinantes econométricos y la evolución de la solvencia bancaria en el Perú (medida a través del **Ratio de Capital Global**) y su relación con la rentabilidad del patrimonio (**ROE**), el riesgo de crédito (**Cartera Atrasada / Morosidad**) y la escala de la entidad (**ln APR**), para el sistema de banca múltiple durante el periodo **enero 2018 – diciembre 2025 (96 meses)**.

---

## Fuentes de datos y estrategia de extracción

### Vía 1 — API (Banco Mundial, base GFDD)
- **Fuente:** World Bank Open Data — Global Financial Development Database (GFDD)
- **Endpoint base:** `https://api.worldbank.org/v2/country/PER/indicator/{codigo}`
- **Indicadores agregados extraídos:**
  - `GFDD.SI.05`: Bank regulatory capital to risk-weighted assets (%)
  - `GFDD.SI.03`: Bank capital to total assets (%)
  - `GFDD.SI.02`: Bank nonperforming loans to gross loans (%)
  - `GFDD.EI.05`: Bank return on assets (%)
  - `GFDD.EI.06`: Bank return on equity (%)
- **Cobertura:** Serie anual Perú (2000–2025)
- **Script:** `codigo/01_extraccion_api.py`
- **Salida:** `datos_crudos/datos_crudos_2024200492K_bancomundial.csv`

### Vía 2 — Scraping programático (SBS Perú)
- **Fuente:** Superintendencia de Banca, Seguros y AFP (SBS) — Reportes estadísticos mensuales
- **Estructura de endpoints consultados:**
  - **Reporte B-2402:** Ratio de Capital Global y Requerimiento de Patrimonio Efectivo / APR
  - **Reporte B-2201:** Balance General y Estado de Ganancias y Pérdidas (para cálculo de ROE)
  - **Reporte B-2362:** Morosidad según tipo y modalidad de crédito (Cartera Atrasada)
- **Cumplimiento ético y técnico:** Pausa mínima de 1 segundo entre solicitudes HTTP y User-Agent identificatorio. Bitácora de auditoría en `log_ejecucion.txt`.
- **Script:** `codigo/02_scraping_web.py`
- **Salidas:** Archivos `.XLS` organizados en:
  - `datos_crudos/sbs_ratio_capital_global/`
  - `datos_crudos/sbs_roe/`
  - `datos_crudos/sbs_cartera_atrasada/`

---

## Procesamiento, estandarización y completado estadístico
- **Script:** `codigo/03_limpieza_datos.py`
- **Lectura y procesamiento heterogéneo por reporte:**
  1. **Ratio de Capital Global y APR (`B-2402`):** Lectura de entidades en filas, ajuste dinámico por regulación Basilea III y conversión histórica a APR.
  2. **ROE (`B-2201`):** Anualización del flujo acumulado de Resultado Neto ($U_n / m \times 12$) sobre el Patrimonio del mes.
  3. **Cartera Atrasada (`B-2362`):** Lectura de entidades en columnas; extracción de la fila *Total Créditos Directos*.
- **Completado de periodos y balanceo de panel:** Relleno de vacíos mediante **interpolación lineal intrabanco** autorizada para consolidar un panel balanceado.
- **Estructura final del dataset:** Panel balanceado ($N \times T$, banco $\times$ mes, 2018-01 a 2025-12).
- **Salidas guardadas:** `datos_procesados/datos_procesados_2024200492K.csv` y versión `.xlsx`.

---

## Diccionario de variables del panel

| Variable | Nombre en dataset | Tipo | Unidad de Medida | Descripción y Fuente SBS |
| :--- | :--- | :--- | :--- | :--- |
| **Solvencia (Y)** | `ratio_capital_global_pct` | Endógena | Porcentaje (%) | Patrimonio efectivo / APR. Reporte B-2402. |
| **Rentabilidad (X1)** | `roe_pct` | Exógena | Porcentaje (%) | (Utilidad Neta anualizada / Patrimonio) $\times 100$. Reporte B-2201. |
| **Riesgo Crédito (X2)** | `cartera_atrasada_pct` | Exógena | Porcentaje (%) | Morosidad sobre créditos directos totales. Reporte B-2362. |
| **Escala / Tamaño (X3)** | `apr_total_soles` / `ln_apr_total_soles` | Exógena (Control) | Miles de S/. / Logaritmo | Activos Ponderados por Riesgo Total. Reporte B-2402. |

---

## Modelación econométrica y diagnóstico
- **Script:** `codigo/05_analisis_econometrico.py`
- **Modelos de datos de panel estimados:**
  - **Pooled OLS**, **Efectos Fijos (FE)** y **Efectos Aleatorios (RE)** con errores estándar robustos agrupados por banco (`cov_type=clustered`).
  - **Prueba de Hausman:** Evaluada sobre la diferencia de matrices de covarianza de los estimadores para elegir de forma rigurosa entre FE y RE.
  - **Diagnóstico de multicolinealidad:** Cálculo del **VIF** (Factor de Inflación de Varianza).
- **Productos generados en `/salidas`:**
  - `tabla1_estadisticas_descriptivas.csv` / `.xlsx`
  - `tabla2_matriz_correlacion.csv` / `.xlsx`
  - `tabla4_comparacion_modelos_panel.txt`
  - `tabla5_vif_multicolinealidad.csv` / `.xlsx`
  - `tabla6_test_hausman.txt`
  - Salidas gráficas PNG (`figura1` a `figura4`) de evolución del sistema y dispersiones con líneas de tendencia.

---

## Secuencia de ejecución
Para reproducir la totalidad del trabajo desde cero, ejecute los scripts en el siguiente orden:
1. `python codigo/01_extraccion_api.py` ➔ Descarga datos macro del Banco Mundial.
2. `python codigo/02_scraping_web.py` ➔ Descarga los 3 reportes SBS (`B-2402`, `B-2201`, `B-2362`) en `/datos_crudos`.
3. `python codigo/03_limpieza_datos.py` ➔ Procesa y consolida el panel balanceado de 4 variables.
4. `python codigo/05_analisis_econometrico.py` ➔ Ejecuta los modelos econométricos (Pooled OLS, FE, RE), VIF, test de Hausman y gráficos.
5. `python codigo/00_generar_entregables_carpeta3.py` ➔ Genera/actualiza todos los archivos de documentación de la Carpeta N°3.

---

## Entorno de ejecución
- **Lenguaje:** Python 3.12+ (Spyder 6 / VS Code)
- **Librerías principales:** `pandas`, `numpy`, `matplotlib`, `statsmodels`, `linearmodels`, `scipy`, `openpyxl`, `requests`.

---

## Verificación de integridad
- **Archivo de datos principal:** `datos_procesados/datos_procesados_2024200492K.csv`
- **Trazabilidad:** Verificada en `log_ejecucion.txt` con registro completo de peticiones HTTP, estado y tiempos de descarga.