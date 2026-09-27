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
Analizar la evolución de la solvencia bancaria en el Perú (medida con el **Ratio de Capital Global**) y su relación con la rentabilidad del patrimonio (**ROE**), el riesgo de crédito (**Cartera Atrasada**) y la escala de la entidad (**ln APR**), para 16 bancos de la banca múltiple entre **enero 2018 y diciembre 2025**.

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
- **Cobertura:** serie anual Perú, 2000–2021 (ratio de capital disponible hasta 2020)
- **Uso:** contexto de largo plazo del sistema bancario peruano; no entra al modelo de panel.
- **Script:** `codigo/01_extraccion_api.py`
- **Salida:** `datos_crudos/datos_crudos_2024200492K_bancomundial.csv`

### Vía 2 — Scraping programático (SBS Perú)
- **Fuente:** Superintendencia de Banca, Seguros y AFP (SBS) — Reportes estadísticos mensuales
- **URL:** `https://intranet2.sbs.gob.pe/estadistica/financiera/{año}/{Mes}/{reporte}-{mm}{año}.XLS`
  - **Reporte B-2402:** Ratio de Capital Global y Requerimiento de Patrimonio Efectivo / APR
  - **Reporte B-2201:** Balance General y Estado de Ganancias y Pérdidas (para cálculo de ROE)
  - **Reporte B-2362:** Morosidad según tipo y modalidad de crédito (Cartera Atrasada)
- **Cumplimiento ético y técnico:** pausa mínima de 1 segundo entre solicitudes y User-Agent identificatorio. Bitácora en `log_ejecucion.txt`.
- **Script:** `codigo/02_scraping_web.py`
- **Salidas:** archivos `.XLS` en `datos_crudos/sbs_ratio_capital_global/`, `datos_crudos/sbs_roe/` y `datos_crudos/sbs_cartera_atrasada/`

---

## Procesamiento y estandarización
- **Script:** `codigo/03_limpieza_datos.py`
- **Lectura por reporte:**
  1. **Ratio de Capital Global y APR (`B-2402`):** bancos en filas; columnas detectadas por texto; APR 2018-2020 = requerimiento total × 10.
  2. **ROE (`B-2201`):** $ROE = (U_m / m \times 12) / Patrimonio \times 100$, con $U_m$ el resultado neto acumulado al mes $m$.
  3. **Cartera Atrasada (`B-2362`):** bancos en columnas; fila *Total Créditos Directos*.
- **Homologación de nombres:** limpieza de notas al pie y unión de cambios de nombre (Continental → BBVA, Financiero → Pichincha, Azteca → Alfin, Banco de Comercio → BANCOM). Ver `incidencias_fuente.md`.
- **Selección de bancos:** 16 entidades de banca múltiple; se excluyen Banco Cencosud (salió en 2019) y Banco BCI Perú (entró en 2022).
- **Vacíos:** interpolación lineal intrabanco solo en huecos internos de hasta 3 meses; sin extrapolación.
- **Estructura final:** 1494 observaciones, 16 bancos, 96 meses (2018-01 a 2025-12); panel no balanceado; bancos con menos de 96 meses: Bank of China (54 meses).
- **Salidas:** `datos_procesados/datos_procesados_2024200492K.csv` y versión `.xlsx`.

---

## Diccionario de variables del panel

| Variable | Nombre en dataset | Tipo | Unidad de Medida | Descripción y Fuente SBS |
| :--- | :--- | :--- | :--- | :--- |
| **Solvencia (Y)** | `ratio_capital_global_pct` | Endógena | Porcentaje (%) | Patrimonio efectivo / APR. Reporte B-2402. |
| **Rentabilidad (X1)** | `roe_pct` | Exógena | Porcentaje (%) | Utilidad neta anualizada / Patrimonio $\times 100$. Reporte B-2201. |
| **Riesgo Crédito (X2)** | `cartera_atrasada_pct` | Exógena | Porcentaje (%) | Créditos atrasados / créditos directos totales. Reporte B-2362. |
| **Escala / Tamaño (X3)** | `apr_total_soles` / `ln_apr_total_soles` | Exógena (Control) | Miles de S/. / Logaritmo | Activos Ponderados por Riesgo Total. Reporte B-2402. |

---

## Modelación econométrica y diagnóstico
- **Script:** `codigo/04_analisis.py`
- **Tratamiento de extremos:** winsorización al percentil 1 y 99 del ROE y del ratio de capital (`salidas/nota_winsorizacion.txt`).
- **Modelos de panel:** Pooled OLS, Efectos Fijos por banco, Efectos Fijos de dos vías (banco + mes) y Efectos Aleatorios, con errores estándar robustos agrupados por banco.
- **Elección FE vs. RE:** test de Hausman clásico (covarianzas no robustas) y test de Mundlak robusto a clusters, que es el criterio de decisión.
- **Multicolinealidad:** VIF.
- **Productos en `/salidas`:**
  - `tabla1_estadisticas_descriptivas.csv` / `.xlsx`
  - `tabla2_matriz_correlacion.csv` / `.xlsx`
  - `tabla3_cobertura_panel.csv` / `.xlsx`
  - `tabla4_comparacion_modelos_panel.txt`
  - `tabla5_vif_multicolinealidad.csv` / `.xlsx`
  - `tabla6_test_hausman.txt` y `nota_winsorizacion.txt`
  - `figura1_evolucion_ratio_sistema.png` (ratio del sistema ponderado por APR y mediana) y `figura2` a `figura4` (dispersiones).

## Pruebas de robustez
- **Script:** `codigo/05_robustez.py`
- **Variantes del modelo de efectos fijos:** base, sin winsorizar, sin Bank of China, sin Alfin Banco, 2018–2022, 2023–2025 y sin 2020–2021, con errores estándar agrupados por banco.
- **Productos en `/salidas`:**
  - `tabla7_evolucion_anual.csv` / `.xlsx`
  - `tabla8_promedios_por_banco.csv` / `.xlsx`
  - `tabla9_robustez.csv` / `.xlsx` / `.txt`
  - `figura5_roe_cartera_evolucion.png`, `figura6_rcg_por_banco.png` y `figura7_robustez_cartera.png`

---

## Secuencia de ejecución

**Requisitos previos:** Python 3.12 o superior y conexión a internet (solo para los scripts 01 y 02). En Spyder, abrir cada script y ejecutarlo con F5 (Spyder usa la carpeta del script como directorio de trabajo).

1. Instalar las librerías (una sola vez), desde la carpeta `Carpeta_N3_Base_de_datos_y_codigo`: `pip install -r requirements.txt`
2. **Entrar a la carpeta `codigo`** (importante: los scripts deben ejecutarse desde ahí): `cd codigo`
3. Ejecutar los scripts en este orden:
   1. `python 01_extraccion_api.py` ➔ Descarga datos agregados del Banco Mundial.
   2. `python 02_scraping_web.py` ➔ Descarga los 3 reportes SBS en `/datos_crudos` (omite los ya descargados).
   3. `python 03_limpieza_datos.py` ➔ Construye el panel de 4 variables para los 16 bancos.
   4. `python 04_analisis.py` ➔ Tablas, figuras, modelos de panel y pruebas de especificación.
   5. `python 05_robustez.py` ➔ Evolución anual, promedios por banco, pruebas de robustez y figuras 5 a 7.
   6. `python 00_generar_entregables_carpeta3.py` ➔ Actualiza README (con el hash), diccionario, requirements e incidencias con las cifras del panel.

---

## Entorno de ejecución
- **Lenguaje:** Python 3.12+ (Spyder 6 / VS Code)
- **Librerías:** `pandas`, `numpy`, `matplotlib`, `statsmodels`, `linearmodels`, `scipy`, `openpyxl`, `xlrd`, `requests`.

---

## Verificación de integridad
- **Archivo de datos principal:** `datos_procesados/datos_procesados_2024200492K.csv`
- **Hash SHA-256:** `c60d178bff906b749008e322d2c140eb288ef025f8690f69e131e266b2da266b`
- **Cómo verificarlo:** en Windows, `certutil -hashfile datos_procesados\datos_procesados_2024200492K.csv SHA256`; en macOS/Linux, `shasum -a 256 datos_procesados/datos_procesados_2024200492K.csv`. Tras ejecutar `03_limpieza_datos.py` el hash debe coincidir.
- **Trazabilidad:** `log_ejecucion.txt` registra cada petición HTTP con fecha, URL y estado.
