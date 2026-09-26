# Registro de Incidencias de Fuente y Trazabilidad

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
   - *Solución:* Anualización exacta del flujo mensual ($U_{n, m} / m 	imes 12$) antes de calcular la razón sobre el Patrimonio para evitar sesgo de estacionalidad.

4. **Tratamiento de Vacíos Estadísticos (Panel Balanceado):**
   - *Incidencia:* Presencia eventual de celdas no reportadas en periodos específicos de transición de entidades de menor escala.
   - *Solución:* Interpolación lineal intrabanco sobre series temporales para garantizar un panel balanceado ($N 	imes T$) válido econométricamente.
