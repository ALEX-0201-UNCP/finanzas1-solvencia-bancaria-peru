# Registro de Incidencias de Fuente y Trazabilidad

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
