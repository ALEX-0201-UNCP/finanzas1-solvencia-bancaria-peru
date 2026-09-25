# Solvencia bancaria en el Perú: ratio de capital global y activos ponderados por riesgo

**Nombres y apellidos:** Chancha Santiago Alex Omar
**Código de matrícula:** 2024200492K
**Curso:** Finanzas I (055D) — Ciclo V, Escuela Profesional de Economía, UNCP
**Docente:** Dr. Ciro Iván Machacuay Meza
**Tema N.º 9 del temario, Unidad I**
**Fecha de corte de extracción:** 2026-09-24
**Repositorio GitHub:** https://github.com/ALEX-0201-UNCP/finanzas1-solvencia-bancaria-peru

## Objetivo del artículo
Analizar la evolución de la solvencia bancaria en el Perú (ratio de capital global y
activos ponderados por riesgo) y su relación con la rentabilidad y el riesgo de crédito
del sistema de banca múltiple, para el periodo enero 2018 – diciembre 2025 (96 meses).

## Fuentes de datos y endpoints

### Vía 1 — API (Banco Mundial, base GFDD)
- **Fuente:** World Bank Open Data — Global Financial Development Database (GFDD)
- **Endpoint base:** `https://api.worldbank.org/v2/country/PER/indicator/{codigo}`
- **Indicadores extraídos:**
  - `GFDD.SI.05` — Bank regulatory capital to risk-weighted assets (%)
  - `GFDD.SI.03` — Bank capital to total assets (%)
  - `GFDD.SI.02` — Bank nonperforming loans to gross loans (%)
  - `GFDD.EI.05` — Bank return on assets (%)
  - `GFDD.EI.06` — Bank return on equity (%)
- **Cobertura:** Perú, serie anual 2000–2025 (agregado nacional)
- **Script:** `codigo/01_extraccion_api.py`
- **Salida:** `datos_crudos/datos_crudos_2024200492K_bancomundial.csv`

### Vía 2 — Descarga programática (SBS)
- **Fuente:** Superintendencia de Banca, Seguros y AFP (SBS) — "Requerimiento de
  Patrimonio Efectivo y Ratio de Capital Global" (reporte B-2402)
- **URL base:** `https://intranet2.sbs.gob.pe/estadistica/financiera/{año}/{Mes}/B-2402-{abrev}{año}.XLS`
- **Robots.txt verificado el 23/09/2026:** no se encontró archivo publicado en
  `intranet2.sbs.gob.pe`; sin restricciones declaradas para la ruta utilizada.
- **Cobertura:** 96 meses solicitados (enero 2018 – diciembre 2025); 88 de 96 archivos
  descargados exitosamente (8 no disponibles en el servidor, ver `log_ejecucion.txt`)
- **Pausa entre solicitudes:** 1 segundo | **User-Agent identificado:** sí
- **Script:** `codigo/02_scraping_web.py`
- **Salida:** `datos_crudos/sbs_ratio_capital_global/*.XLS` (88 archivos)

## Procesamiento y completado estadístico
- **Script:** `codigo/03_limpieza_datos.py`
- De los 88 archivos SBS descargados, se extrajeron 1,451 observaciones reales
  (banco x mes), reconociendo automáticamente dos formatos distintos usados por la
  SBS a lo largo del periodo:
  - Formato 2018-2020: APR total derivado de "Requerimiento Total de Patrimonio
    Efectivo" mediante la fórmula APR = Requerimiento_total x 10.
  - Formato 2021-2025 (post-Basilea III): APR total leído directamente de la
    columna "Activos y Contingentes Ponderados por Riesgo Total".
- **Completado de periodos faltantes:** autorizado expresamente por el docente del
  curso. Los meses sin reporte disponible en la fuente oficial se completaron
  mediante **interpolación lineal** por banco.
- **Panel final:** 2,112 observaciones · 22 bancos · 96 meses (enero 2018 - diciembre
  2025). De ellas, **1,419 (67.2%) son datos originales de la SBS** y **693 (32.8%)
  son valores interpolados**, identificados explícitamente en la columna
  `fuente_dato` de `datos_procesados_2024200492K.csv` (SBS_original / interpolado).
- **Salida:** `datos_procesados/datos_procesados_2024200492K.csv`

## Análisis
- **Script:** `codigo/04_analisis.py`
- Genera las tablas y figuras del artículo a partir del archivo procesado,
  guardadas en /salidas.

## Diccionario de variables
Ver `diccionario_variables.xlsx` (o .md) para la definición, unidad de medida,
frecuencia y fuente exacta de cada variable.

## Orden de ejecución
1. codigo/01_extraccion_api.py       -> genera datos_crudos_2024200492K_bancomundial.csv
2. codigo/02_scraping_web.py         -> genera 88 archivos .XLS en datos_crudos/sbs_ratio_capital_global/
3. codigo/03_limpieza_datos.py       -> genera datos_procesados_2024200492K.csv
4. codigo/04_analisis.py             -> genera tablas y figuras en /salidas

## Entorno de ejecución
- **Lenguaje:** Python 3.12.11 | packaged by conda-forge | (main, Jun 4 2025, 14:29:09) [MSC v.1943 64 bit (AMD64)]
- **IDE:** Spyder 6 (entorno Conda: spyder-runtime)
- **Librerías y versiones:** ver requirements.txt

## Verificación de integridad
- **Archivo verificado:** `datos_procesados/datos_procesados_2024200492K.csv`
- **Hash SHA-256:** f22e4bc5e45ea4f5973de6c1408b6bd9566e4987a757a63c397aa9c18607e05c
- Este hash corresponde al archivo tal como fue entregado; una reejecución posterior
  del script 03 puede generar un hash distinto si la fuente (SBS) revisó datos hacia
  atrás, lo cual no invalida el trabajo (numeral 2.4.5 de la consigna), siempre que
  el log_ejecucion.txt acredite fecha y hora de la extracción original.

## Semilla aleatoria
No aplica — este trabajo no emplea simulación de Monte Carlo ni remuestreo.

## Incidencias de fuente
Ninguna incidencia de bloqueo. Ver incidencias_fuente.md si se documentara alguna
en el futuro.
