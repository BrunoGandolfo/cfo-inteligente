# Test E2E 100 Preguntas — CFO Inteligente

**Fecha:** 2026-02-17 13:50:05
**Endpoint:** http://localhost:8001/api/cfo/ask
**Validaciones:** Dato vs BD + Narrativa vs Dato + Status HTTP

## 1. Estadísticas Generales

| Métrica | Valor |
|---------|-------|
| Total preguntas | 100 |
| **PASS** | **84** (84%) |
| **WARN** | **15** (15%) |
| **FAIL** | **1** (1%) |
| Tiempo promedio | 10.02s |
| Tiempo total | 1002.0s |

### Desglose por Método de Routing

| Método | Total | PASS | WARN | FAIL |
|--------|-------|------|------|------|
| claude | 15 | 15 | 0 | 0 |
| claude_chain_of_thought | 6 | 6 | 0 | 0 |
| claude_con_advertencias | 2 | 1 | 1 | 0 |
| claude_fallback_predefinido | 1 | 1 | 0 | 0 |
| desconocido | 1 | 0 | 0 | 1 |
| haiku_template_direct | 60 | 56 | 4 | 0 |
| haiku_template_direct_con_advertencias | 1 | 1 | 0 | 0 |
| haiku_template_direct_fallback_predefinido | 13 | 3 | 10 | 0 |
| query_fallback | 1 | 1 | 0 | 0 |

### Desglose por Categoría

| Categoría | Total | PASS | WARN | FAIL |
|-----------|-------|------|------|------|
| COMPUESTAS | 14 | 5 | 9 | 0 |
| DISTRIBUCIONES | 9 | 9 | 0 | 0 |
| GASTOS | 20 | 19 | 1 | 0 |
| INGRESOS | 19 | 19 | 0 | 0 |
| NINGUNO | 15 | 14 | 0 | 1 |
| RESUMEN | 14 | 9 | 5 | 0 |
| RETIROS | 9 | 9 | 0 | 0 |

## 2. Tabla Resumen (100 Preguntas)

| # | Pregunta | Método | Dato Sys | Dato Ctrl | V.Dato | V.Narrativa | Final |
|---|----------|--------|----------|-----------|--------|-------------|-------|
| 1 | ¿Cuánto facturamos en 2025? | haiku_template_direct | 893,075,002.92 | 893,075,002.92 | PASS | PASS | **PASS** |
| 2 | ¿Cuáles fueron los ingresos de enero 2025? | haiku_template_direct | 0 | 0 | PASS | PASS | **PASS** |
| 3 | ¿Cuánto facturamos este mes? | haiku_template_direct | 0 | 0 | PASS | PASS | **PASS** |
| 4 | Ingresos del área Jurídica en 2025 | haiku_template_direct | 180,031,288.20 | 180,031,288.20 | PASS | PASS | **PASS** |
| 5 | Ingresos en Mercedes este año | haiku_template_direct | 0 | 0 | PASS | PASS | **PASS** |
| 6 | ¿Quiénes son nuestros top 10 clientes? | haiku_template_direct_fallback_predefinido | (vacío) | (vacío) | PASS | PASS | **PASS** |
| 7 | ¿Cuántas operaciones de ingreso tuvimos este  | haiku_template_direct | 0 | 0 | PASS | PASS | **PASS** |
| 8 | ¿Cuál fue el ingreso más alto del año? | haiku_template_direct | (vacío) | 0 | PASS | PASS | **PASS** |
| 9 | Ingresos por trimestre de 2025 | haiku_template_direct | 893,075,002.92 | 893,075,002.92 | PASS | PASS | **PASS** |
| 10 | Evolución mensual de ingresos 2025 | claude_chain_of_thought | 893,075,002.92 | 893,075,002.92 | PASS | PASS | **PASS** |
| 11 | ¿Cuánto gastamos en 2025? | haiku_template_direct | 288,782,063.19 | 288,782,063.19 | PASS | PASS | **PASS** |
| 12 | Gastos del área Contable este año | haiku_template_direct | 0 | 0 | PASS | PASS | **PASS** |
| 13 | Gastos en Montevideo 2025 | haiku_template_direct | 138,506,029.64 | 138,506,029.64 | PASS | PASS | **PASS** |
| 14 | ¿Quiénes son los 10 proveedores a los que más | haiku_template_direct | (vacío) | (vacío) | PASS | PASS | **PASS** |
| 15 | ¿Cuánto gastamos en enero 2025? | claude | 0 | 0 | PASS | PASS | **PASS** |
| 16 | Promedio mensual de gastos este año | claude_chain_of_thought | 0 | 0 | PASS | PASS | **PASS** |
| 17 | ¿Cuál fue el gasto más alto del año? | haiku_template_direct | (vacío) | 0 | PASS | PASS | **PASS** |
| 18 | Gastos del área Administración este año | haiku_template_direct | 0 | 0 | PASS | PASS | **PASS** |
| 19 | Gastos por trimestre 2025 | haiku_template_direct | 288,782,063.19 | 288,782,063.19 | PASS | WARN | **WARN** |
| 20 | Gastos del área Otros Gastos este año | haiku_template_direct | 0 | 0 | PASS | PASS | **PASS** |
| 21 | ¿Cuánto retiramos este año? | haiku_template_direct | 0 | 0 | PASS | PASS | **PASS** |
| 22 | Retiros en Mercedes 2025 | haiku_template_direct | 4,585,278.39 | 4,585,278.39 | PASS | PASS | **PASS** |
| 23 | ¿Cuánto recibió Bruno en distribuciones este  | haiku_template_direct | 0 | 0 | PASS | PASS | **PASS** |
| 24 | Distribuciones por socio 2025 | haiku_template_direct | 22,975,209.00 | 22,975,209.00 | PASS | PASS | **PASS** |
| 25 | ¿Cuántas distribuciones hubo este año? | haiku_template_direct | 0 | 0 | PASS | PASS | **PASS** |
| 26 | Retiros por mes 2025 | haiku_template_direct | 7,443,005.67 | 7,443,005.67 | PASS | PASS | **PASS** |
| 27 | ¿Cuánto retiramos en dólares este año? | haiku_template_direct | 0 | 0 | PASS | PASS | **PASS** |
| 28 | Distribuciones totales del mes | haiku_template_direct | 0 | 0 | PASS | PASS | **PASS** |
| 29 | ¿Cuál es el resultado neto de 2025? | haiku_template_direct | 604,292,939.73 | 604,292,939.73 | PASS | PASS | **PASS** |
| 30 | ¿Cuál es nuestra rentabilidad este año? | claude | 0 | 0 | PASS | PASS | **PASS** |
| 31 | ¿Cuál es el área más rentable? | claude_con_advertencias | 564,341,276.26 | (vacío) | WARN | PASS | **WARN** |
| 32 | Resumen financiero de 2025 | haiku_template_direct_fallback_predefinido | 4,949,816,136.74 | 1,212,275,280.78 | PASS | WARN | **WARN** |
| 33 | Resultado por localidad este año | haiku_template_direct | (vacío) | (vacío) | PASS | PASS | **PASS** |
| 34 | ¿Cómo venimos este mes? | haiku_template_direct | 0 | (vacío) | WARN | PASS | **WARN** |
| 35 | Capital de trabajo actual | haiku_template_direct_fallback_predefinido | 2,240,266,413.56 | 2,240,266,413.56 | PASS | PASS | **PASS** |
| 36 | Flujo de caja de este mes | haiku_template_direct | 0 | 0 | PASS | PASS | **PASS** |
| 37 | Comparar 2024 vs 2025 | haiku_template_direct_fallback_predefinido | 16,086,454,087.51 | 3,865,680,128.24 | PASS | WARN | **WARN** |
| 38 | Comparar primer trimestre 2024 vs 2025 | haiku_template_direct_fallback_predefinido | 16,086,454,087.51 | 568,557,322.71 | PASS | WARN | **WARN** |
| 39 | Comparar Jurídica vs Contable | haiku_template_direct | (vacío) | (vacío) | PASS | PASS | **PASS** |
| 40 | Ingresos de enero 2024 vs enero 2025 | haiku_template_direct_fallback_predefinido | 215,056,467.90 | 215,056,467.90 | PASS | PASS | **PASS** |
| 41 | Informe ejecutivo 2025 | haiku_template_direct_fallback_predefinido | 4,949,816,136.74 | 1,212,275,280.78 | PASS | WARN | **WARN** |
| 42 | Comparación ejecutiva 2024 vs 2025 | haiku_template_direct_fallback_predefinido | 16,086,454,087.51 | 3,865,680,128.24 | PASS | WARN | **WARN** |
| 43 | Rentabilidad por área 2025 | haiku_template_direct | 893,075,002.92 | 893,075,002.92 | PASS | WARN | **WARN** |
| 44 | Rentabilidad global incluyendo todos los gast | claude | 0 | 0 | PASS | PASS | **PASS** |
| 45 | Resumen del primer semestre 2025 vs 2024 | haiku_template_direct_fallback_predefinido | 16,086,454,087.51 | 1,927,924,709.83 | PASS | WARN | **WARN** |
| 46 | ¿En qué meses los gastos superaron a los ingr | claude | claude | routing | PASS | PASS | **PASS** |
| 47 | ¿Cuál es el cliente que más creció porcentual | claude | claude | routing | PASS | PASS | **PASS** |
| 48 | ¿Qué porcentaje de los ingresos de Mercedes v | claude_fallback_predefinido | claude_fallback_predefinido | routing | PASS | PASS | **PASS** |
| 49 | Dame un análisis de la tendencia de rentabili | claude_chain_of_thought | claude_chain_of_thought | routing | PASS | PASS | **PASS** |
| 50 | ¿Cuántos clientes nuevos tuvimos en 2025 que  | claude | claude | routing | PASS | PASS | **PASS** |
| 51 | Ingresos totales de 2024 | haiku_template_direct | 2,159,898,267.98 | 2,159,898,267.98 | PASS | PASS | **PASS** |
| 52 | Ingresos del área Notarial en 2025 | haiku_template_direct | 181,860,868.39 | 181,860,868.39 | PASS | PASS | **PASS** |
| 53 | Ingresos en dólares de 2025 | haiku_template_direct | 22,475,081.70 | 22,475,081.70 | PASS | PASS | **PASS** |
| 54 | ¿Cuánto facturó el área Recuperación en 2024? | haiku_template_direct | 380,431,201.34 | 380,431,201.34 | PASS | PASS | **PASS** |
| 55 | Ingresos de Montevideo en 2024 | haiku_template_direct | 1,117,139,224.72 | 1,117,139,224.72 | PASS | PASS | **PASS** |
| 56 | Gastos totales de 2024 | haiku_template_direct | 431,908,068.76 | 431,908,068.76 | PASS | PASS | **PASS** |
| 57 | Gastos del área Jurídica en 2024 | haiku_template_direct | 66,281,236.24 | 66,281,236.24 | PASS | PASS | **PASS** |
| 58 | Gastos en dólares de 2024 | haiku_template_direct | 10,870,233.92 | 10,870,233.92 | PASS | PASS | **PASS** |
| 59 | ¿Cuánto gastamos el mes pasado? | haiku_template_direct_con_advertencias | (vacío) | 0 | PASS | PASS | **PASS** |
| 60 | Gastos de Mercedes en 2025 | haiku_template_direct | 150,276,033.55 | 150,276,033.55 | PASS | PASS | **PASS** |
| 61 | Retiros totales de 2024 | haiku_template_direct | 13,933,322.72 | 13,933,322.72 | PASS | PASS | **PASS** |
| 62 | Retiros en Montevideo 2025 | haiku_template_direct | 2,857,727.28 | 2,857,727.28 | PASS | PASS | **PASS** |
| 63 | Retiros por mes en 2024 | haiku_template_direct | 13,933,322.72 | 13,933,322.72 | PASS | PASS | **PASS** |
| 64 | ¿Cuánto recibió Agustina en distribuciones en | haiku_template_direct | 4,597,247.00 | 4,597,247.00 | PASS | PASS | **PASS** |
| 65 | Distribuciones totales de 2024 | haiku_template_direct | 47,665,188.00 | 47,665,188.00 | PASS | PASS | **PASS** |
| 66 | ¿Cuánto recibió Gonzalo en distribuciones en  | haiku_template_direct | 4,539,219.00 | 4,539,219.00 | PASS | PASS | **PASS** |
| 67 | Resultado neto de 2024 | haiku_template_direct | 1,727,990,199.22 | 1,727,990,199.22 | PASS | PASS | **PASS** |
| 68 | Rentabilidad del área Jurídica en 2025 | haiku_template_direct | 180,031,288.20 | 180,031,288.20 | PASS | PASS | **PASS** |
| 69 | ¿Cuál fue nuestro mejor mes de ingresos en 20 | haiku_template_direct | 893,075,002.92 | 234,504,796.47 | PASS | PASS | **PASS** |
| 70 | Resumen financiero de 2024 | haiku_template_direct_fallback_predefinido | 11,779,910,057.18 | 2,653,404,847.46 | PASS | WARN | **WARN** |
| 71 | Rentabilidad por área 2024 | haiku_template_direct | 2,159,898,267.98 | 420.52 | PASS | WARN | **WARN** |
| 72 | Comparar segundo trimestre 2024 vs 2025 | haiku_template_direct_fallback_predefinido | 16,086,454,087.51 | 1,359,367,387.12 | PASS | WARN | **WARN** |
| 73 | Comparar primer semestre 2024 vs 2025 | haiku_template_direct_fallback_predefinido | 16,086,454,087.51 | 1,927,924,709.83 | PASS | WARN | **WARN** |
| 74 | Informe ejecutivo 2024 | haiku_template_direct_fallback_predefinido | 11,779,910,057.18 | 2,653,404,847.46 | PASS | WARN | **WARN** |
| 75 | Comparar Notarial vs Recuperación | haiku_template_direct | (vacío) | (vacío) | PASS | PASS | **PASS** |
| 76 | Ingresos de Mercedes vs Montevideo en 2025 | haiku_template_direct | 462,276,334.40 | 893,075,002.92 | PASS | PASS | **PASS** |
| 77 | Evolución mensual de gastos 2024 | claude_chain_of_thought | 431,908,068.76 | 431,908,068.76 | PASS | PASS | **PASS** |
| 78 | Gastos del tercer trimestre de 2025 | claude | 142,132,987.80 | 142,132,987.80 | PASS | PASS | **PASS** |
| 79 | ¿Cuánto facturamos el trimestre pasado? | query_fallback | (vacío) | 0 | PASS | PASS | **PASS** |
| 80 | Ingresos del mes pasado | claude | 0 | 0 | PASS | PASS | **PASS** |
| 81 | Gastos del último semestre | claude | 51,771,663.57 | 51,771,663.57 | PASS | PASS | **PASS** |
| 82 | ¿Cuál fue el resultado neto del mes pasado? | haiku_template_direct | 0 | 0 | PASS | PASS | **PASS** |
| 83 | Retiros del último trimestre | haiku_template_direct | 0 | 0 | PASS | PASS | **PASS** |
| 84 | ¿Cuánto facturamos en dólares en 2024? | haiku_template_direct | 54,366,177.68 | 54,366,177.68 | PASS | PASS | **PASS** |
| 85 | Total de gastos en USD de 2024 | haiku_template_direct | 10,870,233.92 | 10,870,233.92 | PASS | PASS | **PASS** |
| 86 | Retiros en dólares de 2024 | haiku_template_direct | 13,933,322.72 | 13,933,322.72 | PASS | PASS | **PASS** |
| 87 | ¿Cuánto recibió Pancho en distribuciones en 2 | haiku_template_direct | 9,637,807.00 | 9,637,807.00 | PASS | PASS | **PASS** |
| 88 | ¿Cuánto recibió Viviana en distribuciones en  | haiku_template_direct | 4,653,477.00 | 4,653,477.00 | PASS | PASS | **PASS** |
| 89 | Ingresos del área Jurídica en Mercedes en 202 | haiku_template_direct | 84,673,610.42 | 84,673,610.42 | PASS | PASS | **PASS** |
| 90 | Gastos del área Contable en Montevideo en 202 | haiku_template_direct | 33,171,078.86 | 33,171,078.86 | PASS | PASS | **PASS** |
| 91 | ¿Cuál fue el mes con mayor margen de ganancia | claude | claude | routing | PASS | PASS | **PASS** |
| 92 | ¿Qué área tuvo el mayor crecimiento interanua | claude_chain_of_thought | claude_chain_of_thought | routing | PASS | PASS | **PASS** |
| 93 | ¿Cuántos proveedores representan el 80% de nu | claude | claude | routing | PASS | PASS | **PASS** |
| 94 | Ranking de socios por rentabilidad de las áre | claude | claude | routing | PASS | PASS | **PASS** |
| 95 | ¿En qué trimestre fue más eficiente la relaci | claude | claude | routing | PASS | PASS | **PASS** |
| 96 | ¿Cuál es la correlación entre retiros y resul | desconocido | desconocido | routing | PASS | PASS | **FAIL** |
| 97 | ¿Qué clientes dejaron de facturar en 2025 res | claude | claude | routing | PASS | PASS | **PASS** |
| 98 | ¿Cuál es el costo promedio por operación de c | claude_chain_of_thought | claude_chain_of_thought | routing | PASS | PASS | **PASS** |
| 99 | ¿Cuántas operaciones en USD representan más d | claude | claude | routing | PASS | PASS | **PASS** |
| 100 | ¿Cuál es la proporción de gastos fijos vs var | claude_con_advertencias | claude_con_advertencias | routing | PASS | PASS | **PASS** |

## 3. Detalle de FAILs y WARNs

### Pregunta #19: Gastos por trimestre 2025
- **Veredicto Final:** WARN
- **Método:** haiku_template_direct
- **Status:** PASS — status=success
- **Dato vs BD:** PASS — SumSys=288,782,063.19 vs SumCtrl=288,782,063.19 | Rows: 3 vs 3
- **Narrativa vs Dato:** WARN — Dato=288,782,063, narrativa menciona: ['3', '49', '50', '3', '1,634']
- **Narrativa:** **Resumen Ejecutivo**
Los gastos del 2025 muestran un salto significativo del primer al segundo trimestre: de $8.001.039 a $138.648.036. El tercer trimestre alcanzó $142.132.988, manteniendo niveles similares al segundo.

**Detalle**
• Q1 2025: $8.001.039 (3%)
• Q2 2025: $138.648.036 (49%)
• Q3 2025: $142.132.988 (50%)

**Análisis**
El primer trimestre representa apenas el 3% del gasto acumulado, mientras que Q2 y Q3 concentran prácticamente todo el gasto del año con niveles similares entre sí. 
- **SQL Generado:**
```sql
SELECT EXTRACT(QUARTER FROM o.fecha)::INTEGER AS trimestre,
               COALESCE(SUM(o.total_pesificado), 0) AS total
        FROM operaciones o
        WHERE o.tipo_operacion = 'GASTO' AND o.deleted_at IS NULL
        AND EXTRACT(YEAR FROM o.fecha) = 2025
        GROUP BY EXTRACT(QUARTER FROM o.fecha)
        ORDER BY trimestre
```

### Pregunta #31: ¿Cuál es el área más rentable?
- **Veredicto Final:** WARN
- **Método:** claude_con_advertencias
- **Status:** PASS — status=success
- **Dato vs BD:** WARN — Sistema retornó 1 rows, control vacío
- **Narrativa vs Dato:** PASS — Cifra principal (564,341,276) encontrada en narrativa
- **Narrativa:** **Resumen Ejecutivo**
Con los datos disponibles, Administración es la única área con información de rentabilidad registrada, alcanzando $564.341.276 de resultado con una rentabilidad del 100%.

**Análisis**
Los datos muestran únicamente información de rentabilidad para el área de Administración, que presenta ingresos por $564.341.276 sin gastos asociados registrados, resultando en una rentabilidad perfecta. Esta situación puede indicar que los gastos del área están imputados a otras áreas o que 
- **SQL Generado:**
```sql
WITH datos AS (
    SELECT
        a.nombre AS area,
        SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) AS ingresos,
        SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END) AS gastos
    FROM operaciones o
    INNER JOIN areas a ON o.area_id = a.id
    WHERE o.tipo_operacion IN ('INGRESO', 'GASTO')
      AND o.deleted_at IS NULL
      AND a.nombre != 'Otros Gastos'
    GROUP BY a.nombre
)
SELECT area, ingresos, gastos, ingresos - gastos AS resultado,
    CASE WHEN ingresos > 0 THEN ROUND((ingresos - gastos) * 100.0 / ingresos, 2) ELSE 0 END AS rentabilidad_pct
FROM datos
ORDER BY rentabilidad_pct DESC
LIMIT 1
```

### Pregunta #32: Resumen financiero de 2025
- **Veredicto Final:** WARN
- **Método:** haiku_template_direct_fallback_predefinido
- **Status:** PASS — status=success
- **Dato vs BD:** PASS — Ambos retornan data (50 vs 4 rows)
- **Narrativa vs Dato:** WARN — Dato=4,949,816,137, narrativa menciona: ['30', '20', '20', '30', '20']
- **Narrativa:** **Resumen Ejecutivo**
Cerramos 2025 con una facturación de $893.075.003 y gastos por $288.782.063, generando un resultado bruto de $604.292.940. Recuperación lidera los ingresos con el 30,4% del total, seguida por Notarial (20,4%) y Jurídica (20,2%).

**Detalle**

*Ingresos por área:*
• Recuperación: $271.554.936 (30,4%)
• Notarial: $181.860.868 (20,4%)
• Jurídica: $180.031.288 (20,2%)
• Contable: $146.543.659 (16,4%)
• Administración: $113.084.251 (12,7%)

*Rentabilidad por área:*
• Administrac
- **SQL Generado:**
```sql
WITH 
-- SECCIÓN 1: TOTALES GENERALES
totales AS (
    SELECT 
        '01_TOTALES' AS seccion,
        'GENERAL' AS dimension,
        '2025' AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END), 0) AS distribuciones_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_dolarizado ELSE 0 END), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = 2025
),

-- SECCIÓN 2: POR ÁREA
por_area AS (
    SELECT 
        '02_POR_AREA' AS seccion,
        a.nombre AS dimension,
        '2025' AS periodo,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones o
    JOIN areas a ON a.id = o.area_id
    WHERE o.deleted_at IS NULL AND EXTRACT(YEAR FROM o.fecha) = 2025
    GROUP BY a.nombre
),

-- SECCIÓN 3: POR LOCALIDAD
por_localidad AS (
    SELECT 
        '03_POR_LOCALIDAD' AS seccion,
        localidad::TEXT AS dimension,
        '2025' AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = 2025
    GROUP BY localidad
),

-- SECCIÓN 4: POR MES
por_mes AS (
    SELECT 
        '04_POR_MES' AS seccion,
        TO_CHAR(fecha, 'MM-Mon') AS dimension,
        '2025' AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END), 0) AS distribuciones_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_dolarizado ELSE 0 END), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = 2025
    GROUP BY TO_CHAR(fecha, 'MM-Mon')
),

-- SECCIÓN 5: RETIROS DE LA EMPRESA (por localidad y moneda)
retiros_empresa AS (
    SELECT 
        '05_RETIROS_EMPRESA' AS seccion,
        localidad::TEXT || ' - ' || moneda_original::TEXT AS dimension,
        '2025' AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        COALESCE(SUM(total_pesificado), 0) AS retiros_uyu,
        COALESCE(SUM(total_dolarizado), 0) AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND tipo_operacion = 'RETIRO'
    AND EXTRACT(YEAR FROM fecha) = 2025
    GROUP BY localidad, moneda_original
),

-- SECCIÓN 6: DISTRIBUCIONES A SOCIOS
distribuciones_socios AS (
    SELECT 
        '06_DISTRIBUCIONES_SOCIOS' AS seccion,
        s.nombre || ' (' || dd.porcentaje || '%)' AS dimension,
        '2025' AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        COALESCE(SUM(dd.total_pesificado), 0) AS distribuciones_uyu,
        COALESCE(SUM(dd.total_dolarizado), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM distribuciones_detalle dd
    JOIN operaciones o ON o.id = dd.operacion_id
    JOIN socios s ON s.id = dd.socio_id
    WHERE o.deleted_at IS NULL AND EXTRACT(YEAR FROM o.fecha) = 2025
    GROUP BY s.nombre, dd.porcentaje
),

-- SECCIÓN 7: RENTABILIDAD POR ÁREA
rentabilidad_area AS (
    SELECT 
        '07_RENTABILIDAD_AREA' AS seccion,
        a.nombre || ' -> ' || 
        ROUND(
            CASE WHEN SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) > 0
            THEN ((SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) - 
                   SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END)) /
                  SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) * 100)
            ELSE 0 END
        , 1)::TEXT || '% rentabilidad' AS dimension,
        '2025' AS periodo,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones o
    JOIN areas a ON a.id = o.area_id
    WHERE o.deleted_at IS NULL 
    AND a.nombre != 'Otros Gastos'
    AND EXTRACT(YEAR FROM o.fecha) = 2025
    GROUP BY a.nombre
),

-- SECCIÓN 8: TOP 10 CLIENTES
top_clientes AS (
    SELECT 
        '08_TOP_CLIENTES' AS seccion,
        COALESCE(cliente, 'Sin especificar') AS dimension,
        '2025' AS periodo,
        COALESCE(SUM(total_pesificado), 0) AS ingresos_uyu,
        COALESCE(SUM(total_dolarizado), 0) AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND tipo_operacion = 'INGRESO'
    AND EXTRACT(YEAR FROM fecha) = 2025
    AND cliente IS NOT NULL AND cliente != ''
    GROUP BY cliente
    ORDER BY SUM(total_pesificado) DESC
    LIMIT 10
),

-- SECCIÓN 9: TOP 10 PROVEEDORES
top_proveedores AS (
    SELECT 
        '09_TOP_PROVEEDORES' AS seccion,
        COALESCE(proveedor, 'Sin especificar') AS dimension,
        '2025' AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        COALESCE(SUM(total_pesificado), 0) AS gastos_uyu,
        COALESCE(SUM(total_dolarizado), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND tipo_operacion = 'GASTO'
    AND EXTRACT(YEAR FROM fecha) = 2025
    AND proveedor IS NOT NULL AND proveedor != ''
    GROUP BY proveedor
    ORDER BY SUM(total_pesificado) DESC
    LIMIT 10
)

SELECT * FROM totales
UNION ALL SELECT * FROM por_area
UNION ALL SELECT * FROM por_localidad
UNION ALL SELECT * FROM por_mes
UNION ALL SELECT * FROM retiros_empresa
UNION ALL SELECT * FROM distribuciones_socios
UNION ALL SELECT * FROM rentabilidad_area
UNION ALL SELECT * FROM top_clientes
UNION ALL SELECT * FROM top_proveedores
ORDER BY seccion, dimension
```

### Pregunta #34: ¿Cómo venimos este mes?
- **Veredicto Final:** WARN
- **Método:** haiku_template_direct
- **Status:** PASS — status=success
- **Dato vs BD:** WARN — Sistema retornó 1 rows, control vacío
- **Narrativa vs Dato:** PASS — Dato=0, narrativa sin cifras grandes
- **Narrativa:** **Resumen Ejecutivo**
No se registraron ingresos, gastos ni resultados para febrero 2026.

**Análisis**
Con los datos disponibles no es posible determinar el desempeño del mes. Esto puede deberse a que las operaciones aún no fueron registradas en el sistema o que efectivamente no hubo movimientos facturados hasta la fecha.

¿Querés que consulte los datos del mes anterior o verificar si hay operaciones pendientes de registro?
- **SQL Generado:**
```sql
SELECT SUM(CASE WHEN tipo_operacion='INGRESO' THEN total_pesificado ELSE 0 END) AS ing,SUM(CASE WHEN tipo_operacion='GASTO' THEN total_pesificado ELSE 0 END) AS gas,SUM(CASE WHEN tipo_operacion='INGRESO' THEN total_pesificado ELSE 0 END)-SUM(CASE WHEN tipo_operacion='GASTO' THEN total_pesificado ELSE 0 END) AS res FROM operaciones WHERE deleted_at IS NULL AND DATE_TRUNC('month',fecha)=DATE_TRUNC('month',CURRENT_DATE)
```

### Pregunta #37: Comparar 2024 vs 2025
- **Veredicto Final:** WARN
- **Método:** haiku_template_direct_fallback_predefinido
- **Status:** PASS — status=success
- **Dato vs BD:** PASS — Ambos retornan data (85 vs 8 rows)
- **Narrativa vs Dato:** WARN — Dato=16,086,454,088, narrativa menciona: ['59', '33', '49', '59', '33']
- **Narrativa:** **Resumen Ejecutivo**
Los ingresos cayeron 58,6% entre 2024 y 2025: de $2.159.898.268 a $893.075.003. Los gastos se redujeron 33,1% y la cantidad de operaciones bajó 48,8%, pasando de 1.429 a 732 operaciones.

**Detalle**

| Métrica | 2024 | 2025 | Variación |
|---------|------|------|-----------|
| **Ingresos UYU** | $2.159.898.268 | $893.075.003 | -58,6% |
| **Gastos UYU** | $431.908.069 | $288.782.063 | -33,1% |
| **Retiros UYU** | $13.933.323 | $7.443.006 | -46,6% |
| **Distribuciones UYU** 
- **SQL Generado:**
```sql
WITH 
-- SECCIÓN 1: TOTALES POR AÑO
totales AS (
    SELECT 
        '01_TOTALES' AS seccion,
        'AÑO ' || EXTRACT(YEAR FROM fecha)::TEXT AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END), 0) AS distribuciones_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_dolarizado ELSE 0 END), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
    GROUP BY EXTRACT(YEAR FROM fecha)
),

-- SECCIÓN 2: POR ÁREA (cada área × cada año)
por_area AS (
    SELECT 
        '02_POR_AREA' AS seccion,
        a.nombre || ' (' || EXTRACT(YEAR FROM o.fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM o.fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones o
    JOIN areas a ON a.id = o.area_id
    WHERE o.deleted_at IS NULL AND EXTRACT(YEAR FROM o.fecha) IN (2024, 2025)
    GROUP BY a.nombre, EXTRACT(YEAR FROM o.fecha)
),

-- SECCIÓN 3: POR LOCALIDAD (cada localidad × cada año)
por_localidad AS (
    SELECT 
        '03_POR_LOCALIDAD' AS seccion,
        localidad::TEXT || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
    GROUP BY localidad, EXTRACT(YEAR FROM fecha)
),

-- SECCIÓN 4: POR MES (mes × año)
por_mes AS (
    SELECT 
        '04_POR_MES' AS seccion,
        TO_CHAR(fecha, 'Mon') || ' ' || EXTRACT(YEAR FROM fecha)::TEXT AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT || '-' || TO_CHAR(fecha, 'MM') AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END), 0) AS distribuciones_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_dolarizado ELSE 0 END), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
    GROUP BY EXTRACT(YEAR FROM fecha), TO_CHAR(fecha, 'MM'), TO_CHAR(fecha, 'Mon')
),

-- SECCIÓN 5: RETIROS DE LA EMPRESA (por localidad × moneda × año)
retiros_empresa AS (
    SELECT 
        '05_RETIROS_EMPRESA' AS seccion,
        localidad::TEXT || ' ' || moneda_original::TEXT || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        COALESCE(SUM(total_pesificado), 0) AS retiros_uyu,
        COALESCE(SUM(total_dolarizado), 0) AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND tipo_operacion = 'RETIRO'
    AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
    GROUP BY localidad, moneda_original, EXTRACT(YEAR FROM fecha)
),

-- SECCIÓN 6: DISTRIBUCIONES POR SOCIO (socio × año)
distribuciones_socios AS (
    SELECT 
        '06_DISTRIBUCIONES_SOCIOS' AS seccion,
        s.nombre || ' ' || dd.porcentaje || '% (' || EXTRACT(YEAR FROM o.fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM o.fecha)::TEXT AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        COALESCE(SUM(dd.total_pesificado), 0) AS distribuciones_uyu,
        COALESCE(SUM(dd.total_dolarizado), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM distribuciones_detalle dd
    JOIN operaciones o ON o.id = dd.operacion_id
    JOIN socios s ON s.id = dd.socio_id
    WHERE o.deleted_at IS NULL AND EXTRACT(YEAR FROM o.fecha) IN (2024, 2025)
    GROUP BY s.nombre, dd.porcentaje, EXTRACT(YEAR FROM o.fecha)
),

-- SECCIÓN 7: RENTABILIDAD POR ÁREA (área × año)
rentabilidad_area AS (
    SELECT 
        '07_RENTABILIDAD_AREA' AS seccion,
        a.nombre || ' (' || EXTRACT(YEAR FROM o.fecha)::TEXT || ') -> ' || 
        ROUND(
            CASE WHEN SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) > 0
            THEN ((SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) - 
                   SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END)) /
                  SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) * 100)
            ELSE 0 END
        , 1)::TEXT || '%' AS dimension,
        EXTRACT(YEAR FROM o.fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones o
    JOIN areas a ON a.id = o.area_id
    WHERE o.deleted_at IS NULL 
    AND a.nombre != 'Otros Gastos'
    AND EXTRACT(YEAR FROM o.fecha) IN (2024, 2025)
    GROUP BY a.nombre, EXTRACT(YEAR FROM o.fecha)
),

-- SECCIÓN 8: TOP 5 CLIENTES POR AÑO
top_clientes AS (
    SELECT seccion, dimension, periodo, ingresos_uyu, ingresos_usd, 
           gastos_uyu, gastos_usd, retiros_uyu, retiros_usd, 
           distribuciones_uyu, distribuciones_usd, cantidad_operaciones
    FROM (
        SELECT 
            '08_TOP_CLIENTES' AS seccion,
            COALESCE(cliente, 'Sin especificar') || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
            EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
            COALESCE(SUM(total_pesificado), 0) AS ingresos_uyu,
            COALESCE(SUM(total_dolarizado), 0) AS ingresos_usd,
            0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
            0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
            0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
            COUNT(*) AS cantidad_operaciones,
            ROW_NUMBER() OVER (PARTITION BY EXTRACT(YEAR FROM fecha) ORDER BY SUM(total_pesificado) DESC) AS rn
        FROM operaciones 
        WHERE deleted_at IS NULL 
        AND tipo_operacion = 'INGRESO'
        AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
        AND cliente IS NOT NULL AND cliente != ''
        GROUP BY cliente, EXTRACT(YEAR FROM fecha)
    ) t WHERE rn <= 5
),

-- SECCIÓN 9: TOP 5 PROVEEDORES POR AÑO
top_proveedores AS (
    SELECT seccion, dimension, periodo, ingresos_uyu, ingresos_usd, 
           gastos_uyu, gastos_usd, retiros_uyu, retiros_usd, 
           distribuciones_uyu, distribuciones_usd, cantidad_operaciones
    FROM (
        SELECT 
            '09_TOP_PROVEEDORES' AS seccion,
            COALESCE(proveedor, 'Sin especificar') || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
            EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
            0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
            COALESCE(SUM(total_pesificado), 0) AS gastos_uyu,
            COALESCE(SUM(total_dolarizado), 0) AS gastos_usd,
            0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
            0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
            COUNT(*) AS cantidad_operaciones,
            ROW_NUMBER() OVER (PARTITION BY EXTRACT(YEAR FROM fecha) ORDER BY SUM(total_pesificado) DESC) AS rn
        FROM operaciones 
        WHERE deleted_at IS NULL 
        AND tipo_operacion = 'GASTO'
        AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
        AND proveedor IS NOT NULL AND proveedor != ''
        GROUP BY proveedor, EXTRACT(YEAR FROM fecha)
    ) t WHERE rn <= 5
)

SELECT * FROM totales
UNION ALL SELECT * FROM por_area
UNION ALL SELECT * FROM por_localidad
UNION ALL SELECT * FROM por_mes
UNION ALL SELECT * FROM retiros_empresa
UNION ALL SELECT * FROM distribuciones_socios
UNION ALL SELECT * FROM rentabilidad_area
UNION ALL SELECT * FROM top_clientes
UNION ALL SELECT * FROM top_proveedores
ORDER BY seccion, periodo, dimension
```

### Pregunta #38: Comparar primer trimestre 2024 vs 2025
- **Veredicto Final:** WARN
- **Método:** haiku_template_direct_fallback_predefinido
- **Status:** PASS — status=success
- **Dato vs BD:** PASS — Ambos retornan data (85 vs 8 rows)
- **Narrativa vs Dato:** WARN — Dato=16,086,454,088, narrativa menciona: ['59', '30', '75', '66', '60']
- **Narrativa:** **Resumen Ejecutivo**
Los ingresos del primer trimestre 2025 alcanzaron $893.075.003, una caída del 58,6% respecto a los $2.159.898.268 del mismo período 2024. Recuperación lidera el crecimiento con $271.554.936 (30,4% del total), mientras que Administración registra la mayor contracción.

**Detalle**

*Ingresos por área - Q1 2024 vs Q1 2025:*
• Administración: $451.257.025 → $113.084.251 (-74,9%)
• Contable: $431.456.752 → $146.543.659 (-66,0%)
• Jurídica: $450.273.635 → $180.031.288 (-60,0%)
•
- **SQL Generado:**
```sql
WITH 
-- SECCIÓN 1: TOTALES POR AÑO
totales AS (
    SELECT 
        '01_TOTALES' AS seccion,
        'AÑO ' || EXTRACT(YEAR FROM fecha)::TEXT AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END), 0) AS distribuciones_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_dolarizado ELSE 0 END), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
    GROUP BY EXTRACT(YEAR FROM fecha)
),

-- SECCIÓN 2: POR ÁREA (cada área × cada año)
por_area AS (
    SELECT 
        '02_POR_AREA' AS seccion,
        a.nombre || ' (' || EXTRACT(YEAR FROM o.fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM o.fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones o
    JOIN areas a ON a.id = o.area_id
    WHERE o.deleted_at IS NULL AND EXTRACT(YEAR FROM o.fecha) IN (2024, 2025)
    GROUP BY a.nombre, EXTRACT(YEAR FROM o.fecha)
),

-- SECCIÓN 3: POR LOCALIDAD (cada localidad × cada año)
por_localidad AS (
    SELECT 
        '03_POR_LOCALIDAD' AS seccion,
        localidad::TEXT || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
    GROUP BY localidad, EXTRACT(YEAR FROM fecha)
),

-- SECCIÓN 4: POR MES (mes × año)
por_mes AS (
    SELECT 
        '04_POR_MES' AS seccion,
        TO_CHAR(fecha, 'Mon') || ' ' || EXTRACT(YEAR FROM fecha)::TEXT AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT || '-' || TO_CHAR(fecha, 'MM') AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END), 0) AS distribuciones_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_dolarizado ELSE 0 END), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
    GROUP BY EXTRACT(YEAR FROM fecha), TO_CHAR(fecha, 'MM'), TO_CHAR(fecha, 'Mon')
),

-- SECCIÓN 5: RETIROS DE LA EMPRESA (por localidad × moneda × año)
retiros_empresa AS (
    SELECT 
        '05_RETIROS_EMPRESA' AS seccion,
        localidad::TEXT || ' ' || moneda_original::TEXT || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        COALESCE(SUM(total_pesificado), 0) AS retiros_uyu,
        COALESCE(SUM(total_dolarizado), 0) AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND tipo_operacion = 'RETIRO'
    AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
    GROUP BY localidad, moneda_original, EXTRACT(YEAR FROM fecha)
),

-- SECCIÓN 6: DISTRIBUCIONES POR SOCIO (socio × año)
distribuciones_socios AS (
    SELECT 
        '06_DISTRIBUCIONES_SOCIOS' AS seccion,
        s.nombre || ' ' || dd.porcentaje || '% (' || EXTRACT(YEAR FROM o.fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM o.fecha)::TEXT AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        COALESCE(SUM(dd.total_pesificado), 0) AS distribuciones_uyu,
        COALESCE(SUM(dd.total_dolarizado), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM distribuciones_detalle dd
    JOIN operaciones o ON o.id = dd.operacion_id
    JOIN socios s ON s.id = dd.socio_id
    WHERE o.deleted_at IS NULL AND EXTRACT(YEAR FROM o.fecha) IN (2024, 2025)
    GROUP BY s.nombre, dd.porcentaje, EXTRACT(YEAR FROM o.fecha)
),

-- SECCIÓN 7: RENTABILIDAD POR ÁREA (área × año)
rentabilidad_area AS (
    SELECT 
        '07_RENTABILIDAD_AREA' AS seccion,
        a.nombre || ' (' || EXTRACT(YEAR FROM o.fecha)::TEXT || ') -> ' || 
        ROUND(
            CASE WHEN SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) > 0
            THEN ((SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) - 
                   SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END)) /
                  SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) * 100)
            ELSE 0 END
        , 1)::TEXT || '%' AS dimension,
        EXTRACT(YEAR FROM o.fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones o
    JOIN areas a ON a.id = o.area_id
    WHERE o.deleted_at IS NULL 
    AND a.nombre != 'Otros Gastos'
    AND EXTRACT(YEAR FROM o.fecha) IN (2024, 2025)
    GROUP BY a.nombre, EXTRACT(YEAR FROM o.fecha)
),

-- SECCIÓN 8: TOP 5 CLIENTES POR AÑO
top_clientes AS (
    SELECT seccion, dimension, periodo, ingresos_uyu, ingresos_usd, 
           gastos_uyu, gastos_usd, retiros_uyu, retiros_usd, 
           distribuciones_uyu, distribuciones_usd, cantidad_operaciones
    FROM (
        SELECT 
            '08_TOP_CLIENTES' AS seccion,
            COALESCE(cliente, 'Sin especificar') || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
            EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
            COALESCE(SUM(total_pesificado), 0) AS ingresos_uyu,
            COALESCE(SUM(total_dolarizado), 0) AS ingresos_usd,
            0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
            0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
            0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
            COUNT(*) AS cantidad_operaciones,
            ROW_NUMBER() OVER (PARTITION BY EXTRACT(YEAR FROM fecha) ORDER BY SUM(total_pesificado) DESC) AS rn
        FROM operaciones 
        WHERE deleted_at IS NULL 
        AND tipo_operacion = 'INGRESO'
        AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
        AND cliente IS NOT NULL AND cliente != ''
        GROUP BY cliente, EXTRACT(YEAR FROM fecha)
    ) t WHERE rn <= 5
),

-- SECCIÓN 9: TOP 5 PROVEEDORES POR AÑO
top_proveedores AS (
    SELECT seccion, dimension, periodo, ingresos_uyu, ingresos_usd, 
           gastos_uyu, gastos_usd, retiros_uyu, retiros_usd, 
           distribuciones_uyu, distribuciones_usd, cantidad_operaciones
    FROM (
        SELECT 
            '09_TOP_PROVEEDORES' AS seccion,
            COALESCE(proveedor, 'Sin especificar') || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
            EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
            0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
            COALESCE(SUM(total_pesificado), 0) AS gastos_uyu,
            COALESCE(SUM(total_dolarizado), 0) AS gastos_usd,
            0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
            0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
            COUNT(*) AS cantidad_operaciones,
            ROW_NUMBER() OVER (PARTITION BY EXTRACT(YEAR FROM fecha) ORDER BY SUM(total_pesificado) DESC) AS rn
        FROM operaciones 
        WHERE deleted_at IS NULL 
        AND tipo_operacion = 'GASTO'
        AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
        AND proveedor IS NOT NULL AND proveedor != ''
        GROUP BY proveedor, EXTRACT(YEAR FROM fecha)
    ) t WHERE rn <= 5
)

SELECT * FROM totales
UNION ALL SELECT * FROM por_area
UNION ALL SELECT * FROM por_localidad
UNION ALL SELECT * FROM por_mes
UNION ALL SELECT * FROM retiros_empresa
UNION ALL SELECT * FROM distribuciones_socios
UNION ALL SELECT * FROM rentabilidad_area
UNION ALL SELECT * FROM top_clientes
UNION ALL SELECT * FROM top_proveedores
ORDER BY seccion, periodo, dimension
```

### Pregunta #41: Informe ejecutivo 2025
- **Veredicto Final:** WARN
- **Método:** haiku_template_direct_fallback_predefinido
- **Status:** PASS — status=success
- **Dato vs BD:** PASS — Ambos retornan data (50 vs 4 rows)
- **Narrativa vs Dato:** WARN — Dato=4,949,816,137, narrativa menciona: ['68', '30', '20', '20', '30']
- **Narrativa:** **Resumen Ejecutivo**
Conexión Consultora cerró 2025 con una facturación de $893.075.003 (US$ 22.475.082) y un margen bruto del 67,7%. Recuperación lidera los ingresos con el 30,4% del total, seguida por Notarial (20,4%) y Jurídica (20,2%).

**Detalle**

**Facturación por área:**
• Recuperación: $271.554.936 (30,4%)
• Notarial: $181.860.868 (20,4%)
• Jurídica: $180.031.288 (20,2%)
• Contable: $146.543.659 (16,4%)
• Administración: $113.084.251 (12,7%)

**Rentabilidad por área:**
• Administración
- **SQL Generado:**
```sql
WITH 
-- SECCIÓN 1: TOTALES GENERALES
totales AS (
    SELECT 
        '01_TOTALES' AS seccion,
        'GENERAL' AS dimension,
        '2025' AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END), 0) AS distribuciones_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_dolarizado ELSE 0 END), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = 2025
),

-- SECCIÓN 2: POR ÁREA
por_area AS (
    SELECT 
        '02_POR_AREA' AS seccion,
        a.nombre AS dimension,
        '2025' AS periodo,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones o
    JOIN areas a ON a.id = o.area_id
    WHERE o.deleted_at IS NULL AND EXTRACT(YEAR FROM o.fecha) = 2025
    GROUP BY a.nombre
),

-- SECCIÓN 3: POR LOCALIDAD
por_localidad AS (
    SELECT 
        '03_POR_LOCALIDAD' AS seccion,
        localidad::TEXT AS dimension,
        '2025' AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = 2025
    GROUP BY localidad
),

-- SECCIÓN 4: POR MES
por_mes AS (
    SELECT 
        '04_POR_MES' AS seccion,
        TO_CHAR(fecha, 'MM-Mon') AS dimension,
        '2025' AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END), 0) AS distribuciones_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_dolarizado ELSE 0 END), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = 2025
    GROUP BY TO_CHAR(fecha, 'MM-Mon')
),

-- SECCIÓN 5: RETIROS DE LA EMPRESA (por localidad y moneda)
retiros_empresa AS (
    SELECT 
        '05_RETIROS_EMPRESA' AS seccion,
        localidad::TEXT || ' - ' || moneda_original::TEXT AS dimension,
        '2025' AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        COALESCE(SUM(total_pesificado), 0) AS retiros_uyu,
        COALESCE(SUM(total_dolarizado), 0) AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND tipo_operacion = 'RETIRO'
    AND EXTRACT(YEAR FROM fecha) = 2025
    GROUP BY localidad, moneda_original
),

-- SECCIÓN 6: DISTRIBUCIONES A SOCIOS
distribuciones_socios AS (
    SELECT 
        '06_DISTRIBUCIONES_SOCIOS' AS seccion,
        s.nombre || ' (' || dd.porcentaje || '%)' AS dimension,
        '2025' AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        COALESCE(SUM(dd.total_pesificado), 0) AS distribuciones_uyu,
        COALESCE(SUM(dd.total_dolarizado), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM distribuciones_detalle dd
    JOIN operaciones o ON o.id = dd.operacion_id
    JOIN socios s ON s.id = dd.socio_id
    WHERE o.deleted_at IS NULL AND EXTRACT(YEAR FROM o.fecha) = 2025
    GROUP BY s.nombre, dd.porcentaje
),

-- SECCIÓN 7: RENTABILIDAD POR ÁREA
rentabilidad_area AS (
    SELECT 
        '07_RENTABILIDAD_AREA' AS seccion,
        a.nombre || ' -> ' || 
        ROUND(
            CASE WHEN SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) > 0
            THEN ((SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) - 
                   SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END)) /
                  SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) * 100)
            ELSE 0 END
        , 1)::TEXT || '% rentabilidad' AS dimension,
        '2025' AS periodo,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones o
    JOIN areas a ON a.id = o.area_id
    WHERE o.deleted_at IS NULL 
    AND a.nombre != 'Otros Gastos'
    AND EXTRACT(YEAR FROM o.fecha) = 2025
    GROUP BY a.nombre
),

-- SECCIÓN 8: TOP 10 CLIENTES
top_clientes AS (
    SELECT 
        '08_TOP_CLIENTES' AS seccion,
        COALESCE(cliente, 'Sin especificar') AS dimension,
        '2025' AS periodo,
        COALESCE(SUM(total_pesificado), 0) AS ingresos_uyu,
        COALESCE(SUM(total_dolarizado), 0) AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND tipo_operacion = 'INGRESO'
    AND EXTRACT(YEAR FROM fecha) = 2025
    AND cliente IS NOT NULL AND cliente != ''
    GROUP BY cliente
    ORDER BY SUM(total_pesificado) DESC
    LIMIT 10
),

-- SECCIÓN 9: TOP 10 PROVEEDORES
top_proveedores AS (
    SELECT 
        '09_TOP_PROVEEDORES' AS seccion,
        COALESCE(proveedor, 'Sin especificar') AS dimension,
        '2025' AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        COALESCE(SUM(total_pesificado), 0) AS gastos_uyu,
        COALESCE(SUM(total_dolarizado), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND tipo_operacion = 'GASTO'
    AND EXTRACT(YEAR FROM fecha) = 2025
    AND proveedor IS NOT NULL AND proveedor != ''
    GROUP BY proveedor
    ORDER BY SUM(total_pesificado) DESC
    LIMIT 10
)

SELECT * FROM totales
UNION ALL SELECT * FROM por_area
UNION ALL SELECT * FROM por_localidad
UNION ALL SELECT * FROM por_mes
UNION ALL SELECT * FROM retiros_empresa
UNION ALL SELECT * FROM distribuciones_socios
UNION ALL SELECT * FROM rentabilidad_area
UNION ALL SELECT * FROM top_clientes
UNION ALL SELECT * FROM top_proveedores
ORDER BY seccion, dimension
```

### Pregunta #42: Comparación ejecutiva 2024 vs 2025
- **Veredicto Final:** WARN
- **Método:** haiku_template_direct_fallback_predefinido
- **Status:** PASS — status=success
- **Dato vs BD:** PASS — Ambos retornan data (85 vs 8 rows)
- **Narrativa vs Dato:** WARN — Dato=16,086,454,088, narrativa menciona: ['59', '33', '80', '68', '59']
- **Narrativa:** **Resumen Ejecutivo**
Los ingresos cayeron 58,6% entre 2024 y 2025, pasando de $2.159.898.268 a $893.075.003. Los gastos se redujeron 33,1% y la rentabilidad general se deterioró del 80,0% al 67,7%.

**Detalle**

| Métrica | 2024 | 2025 | Variación |
|---------|------|------|-----------|
| **Ingresos** | $2.159.898.268 | $893.075.003 | -58,6% |
| **Gastos** | $431.908.069 | $288.782.063 | -33,1% |
| **Margen bruto** | $1.727.990.199 | $604.292.940 | -65,0% |
| **Rentabilidad** | 80,0% | 67,7% | 
- **SQL Generado:**
```sql
WITH 
-- SECCIÓN 1: TOTALES POR AÑO
totales AS (
    SELECT 
        '01_TOTALES' AS seccion,
        'AÑO ' || EXTRACT(YEAR FROM fecha)::TEXT AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END), 0) AS distribuciones_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_dolarizado ELSE 0 END), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
    GROUP BY EXTRACT(YEAR FROM fecha)
),

-- SECCIÓN 2: POR ÁREA (cada área × cada año)
por_area AS (
    SELECT 
        '02_POR_AREA' AS seccion,
        a.nombre || ' (' || EXTRACT(YEAR FROM o.fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM o.fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones o
    JOIN areas a ON a.id = o.area_id
    WHERE o.deleted_at IS NULL AND EXTRACT(YEAR FROM o.fecha) IN (2024, 2025)
    GROUP BY a.nombre, EXTRACT(YEAR FROM o.fecha)
),

-- SECCIÓN 3: POR LOCALIDAD (cada localidad × cada año)
por_localidad AS (
    SELECT 
        '03_POR_LOCALIDAD' AS seccion,
        localidad::TEXT || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
    GROUP BY localidad, EXTRACT(YEAR FROM fecha)
),

-- SECCIÓN 4: POR MES (mes × año)
por_mes AS (
    SELECT 
        '04_POR_MES' AS seccion,
        TO_CHAR(fecha, 'Mon') || ' ' || EXTRACT(YEAR FROM fecha)::TEXT AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT || '-' || TO_CHAR(fecha, 'MM') AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END), 0) AS distribuciones_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_dolarizado ELSE 0 END), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
    GROUP BY EXTRACT(YEAR FROM fecha), TO_CHAR(fecha, 'MM'), TO_CHAR(fecha, 'Mon')
),

-- SECCIÓN 5: RETIROS DE LA EMPRESA (por localidad × moneda × año)
retiros_empresa AS (
    SELECT 
        '05_RETIROS_EMPRESA' AS seccion,
        localidad::TEXT || ' ' || moneda_original::TEXT || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        COALESCE(SUM(total_pesificado), 0) AS retiros_uyu,
        COALESCE(SUM(total_dolarizado), 0) AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND tipo_operacion = 'RETIRO'
    AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
    GROUP BY localidad, moneda_original, EXTRACT(YEAR FROM fecha)
),

-- SECCIÓN 6: DISTRIBUCIONES POR SOCIO (socio × año)
distribuciones_socios AS (
    SELECT 
        '06_DISTRIBUCIONES_SOCIOS' AS seccion,
        s.nombre || ' ' || dd.porcentaje || '% (' || EXTRACT(YEAR FROM o.fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM o.fecha)::TEXT AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        COALESCE(SUM(dd.total_pesificado), 0) AS distribuciones_uyu,
        COALESCE(SUM(dd.total_dolarizado), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM distribuciones_detalle dd
    JOIN operaciones o ON o.id = dd.operacion_id
    JOIN socios s ON s.id = dd.socio_id
    WHERE o.deleted_at IS NULL AND EXTRACT(YEAR FROM o.fecha) IN (2024, 2025)
    GROUP BY s.nombre, dd.porcentaje, EXTRACT(YEAR FROM o.fecha)
),

-- SECCIÓN 7: RENTABILIDAD POR ÁREA (área × año)
rentabilidad_area AS (
    SELECT 
        '07_RENTABILIDAD_AREA' AS seccion,
        a.nombre || ' (' || EXTRACT(YEAR FROM o.fecha)::TEXT || ') -> ' || 
        ROUND(
            CASE WHEN SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) > 0
            THEN ((SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) - 
                   SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END)) /
                  SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) * 100)
            ELSE 0 END
        , 1)::TEXT || '%' AS dimension,
        EXTRACT(YEAR FROM o.fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones o
    JOIN areas a ON a.id = o.area_id
    WHERE o.deleted_at IS NULL 
    AND a.nombre != 'Otros Gastos'
    AND EXTRACT(YEAR FROM o.fecha) IN (2024, 2025)
    GROUP BY a.nombre, EXTRACT(YEAR FROM o.fecha)
),

-- SECCIÓN 8: TOP 5 CLIENTES POR AÑO
top_clientes AS (
    SELECT seccion, dimension, periodo, ingresos_uyu, ingresos_usd, 
           gastos_uyu, gastos_usd, retiros_uyu, retiros_usd, 
           distribuciones_uyu, distribuciones_usd, cantidad_operaciones
    FROM (
        SELECT 
            '08_TOP_CLIENTES' AS seccion,
            COALESCE(cliente, 'Sin especificar') || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
            EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
            COALESCE(SUM(total_pesificado), 0) AS ingresos_uyu,
            COALESCE(SUM(total_dolarizado), 0) AS ingresos_usd,
            0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
            0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
            0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
            COUNT(*) AS cantidad_operaciones,
            ROW_NUMBER() OVER (PARTITION BY EXTRACT(YEAR FROM fecha) ORDER BY SUM(total_pesificado) DESC) AS rn
        FROM operaciones 
        WHERE deleted_at IS NULL 
        AND tipo_operacion = 'INGRESO'
        AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
        AND cliente IS NOT NULL AND cliente != ''
        GROUP BY cliente, EXTRACT(YEAR FROM fecha)
    ) t WHERE rn <= 5
),

-- SECCIÓN 9: TOP 5 PROVEEDORES POR AÑO
top_proveedores AS (
    SELECT seccion, dimension, periodo, ingresos_uyu, ingresos_usd, 
           gastos_uyu, gastos_usd, retiros_uyu, retiros_usd, 
           distribuciones_uyu, distribuciones_usd, cantidad_operaciones
    FROM (
        SELECT 
            '09_TOP_PROVEEDORES' AS seccion,
            COALESCE(proveedor, 'Sin especificar') || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
            EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
            0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
            COALESCE(SUM(total_pesificado), 0) AS gastos_uyu,
            COALESCE(SUM(total_dolarizado), 0) AS gastos_usd,
            0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
            0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
            COUNT(*) AS cantidad_operaciones,
            ROW_NUMBER() OVER (PARTITION BY EXTRACT(YEAR FROM fecha) ORDER BY SUM(total_pesificado) DESC) AS rn
        FROM operaciones 
        WHERE deleted_at IS NULL 
        AND tipo_operacion = 'GASTO'
        AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
        AND proveedor IS NOT NULL AND proveedor != ''
        GROUP BY proveedor, EXTRACT(YEAR FROM fecha)
    ) t WHERE rn <= 5
)

SELECT * FROM totales
UNION ALL SELECT * FROM por_area
UNION ALL SELECT * FROM por_localidad
UNION ALL SELECT * FROM por_mes
UNION ALL SELECT * FROM retiros_empresa
UNION ALL SELECT * FROM distribuciones_socios
UNION ALL SELECT * FROM rentabilidad_area
UNION ALL SELECT * FROM top_clientes
UNION ALL SELECT * FROM top_proveedores
ORDER BY seccion, periodo, dimension
```

### Pregunta #43: Rentabilidad por área 2025
- **Veredicto Final:** WARN
- **Método:** haiku_template_direct
- **Status:** PASS — status=success
- **Dato vs BD:** PASS — Ambos retornan data (5 vs 5 rows)
- **Narrativa vs Dato:** WARN — Dato=893,075,003, narrativa menciona: ['271,600,000', '100', '80', '76', '60']
- **Narrativa:** **Resumen Ejecutivo**
Administración lidera la rentabilidad con 100%, seguida por Recuperación (79,6%) y Notarial (75,9%). Jurídica y Contable muestran márgenes más ajustados en torno al 60%.

**Detalle**
| Área | Ingresos | Gastos | Resultado | Rentabilidad |
|------|----------|---------|-----------|--------------|
| Administración | $113.084.251 | $0 | $113.084.251 | 100,0% |
| Recuperación | $271.554.936 | $55.360.874 | $216.194.062 | 79,6% |
| Notarial | $181.860.868 | $43.767.991 | $138.092
- **SQL Generado:**
```sql
SELECT 
    a.nombre AS area,
    COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos,
    COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos,
    COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) - 
    COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS resultado,
    CASE 
        WHEN SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) > 0 
        THEN ROUND(((SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) - 
                     SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END)) / 
                    SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END)) * 100, 2)
        ELSE 0 
    END AS rentabilidad_pct
FROM operaciones o
JOIN areas a ON a.id = o.area_id
WHERE o.deleted_at IS NULL 
AND a.nombre NOT IN ('Otros Gastos')
AND EXTRACT(YEAR FROM o.fecha) = 2025
GROUP BY a.nombre
ORDER BY rentabilidad_pct DESC
```

### Pregunta #45: Resumen del primer semestre 2025 vs 2024
- **Veredicto Final:** WARN
- **Método:** haiku_template_direct_fallback_predefinido
- **Status:** PASS — status=success
- **Dato vs BD:** PASS — Ambos retornan data (85 vs 8 rows)
- **Narrativa vs Dato:** WARN — Dato=16,086,454,088, narrativa menciona: ['59', '33', '29', '59', '60']
- **Narrativa:** **Resumen Ejecutivo**
La facturación del primer semestre 2025 alcanzó $893.075.003 (US$ 22.475.082), representando una caída del 58,6% respecto al mismo período de 2024 que totalizó $2.159.898.268 (US$ 54.366.178). Los gastos también se redujeron 33,1%, pasando de $431.908.069 a $288.782.063.

**Detalle**

*Facturación por área (2025 vs 2024):*
• Recuperación: $271.554.936 vs $380.431.201 (-28,6%)
• Notarial: $181.860.868 vs $446.479.655 (-59,3%)
• Jurídica: $180.031.288 vs $450.273.635 (-60,0%)
- **SQL Generado:**
```sql
WITH 
-- SECCIÓN 1: TOTALES POR AÑO
totales AS (
    SELECT 
        '01_TOTALES' AS seccion,
        'AÑO ' || EXTRACT(YEAR FROM fecha)::TEXT AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END), 0) AS distribuciones_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_dolarizado ELSE 0 END), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
    GROUP BY EXTRACT(YEAR FROM fecha)
),

-- SECCIÓN 2: POR ÁREA (cada área × cada año)
por_area AS (
    SELECT 
        '02_POR_AREA' AS seccion,
        a.nombre || ' (' || EXTRACT(YEAR FROM o.fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM o.fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones o
    JOIN areas a ON a.id = o.area_id
    WHERE o.deleted_at IS NULL AND EXTRACT(YEAR FROM o.fecha) IN (2024, 2025)
    GROUP BY a.nombre, EXTRACT(YEAR FROM o.fecha)
),

-- SECCIÓN 3: POR LOCALIDAD (cada localidad × cada año)
por_localidad AS (
    SELECT 
        '03_POR_LOCALIDAD' AS seccion,
        localidad::TEXT || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
    GROUP BY localidad, EXTRACT(YEAR FROM fecha)
),

-- SECCIÓN 4: POR MES (mes × año)
por_mes AS (
    SELECT 
        '04_POR_MES' AS seccion,
        TO_CHAR(fecha, 'Mon') || ' ' || EXTRACT(YEAR FROM fecha)::TEXT AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT || '-' || TO_CHAR(fecha, 'MM') AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END), 0) AS distribuciones_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_dolarizado ELSE 0 END), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
    GROUP BY EXTRACT(YEAR FROM fecha), TO_CHAR(fecha, 'MM'), TO_CHAR(fecha, 'Mon')
),

-- SECCIÓN 5: RETIROS DE LA EMPRESA (por localidad × moneda × año)
retiros_empresa AS (
    SELECT 
        '05_RETIROS_EMPRESA' AS seccion,
        localidad::TEXT || ' ' || moneda_original::TEXT || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        COALESCE(SUM(total_pesificado), 0) AS retiros_uyu,
        COALESCE(SUM(total_dolarizado), 0) AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND tipo_operacion = 'RETIRO'
    AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
    GROUP BY localidad, moneda_original, EXTRACT(YEAR FROM fecha)
),

-- SECCIÓN 6: DISTRIBUCIONES POR SOCIO (socio × año)
distribuciones_socios AS (
    SELECT 
        '06_DISTRIBUCIONES_SOCIOS' AS seccion,
        s.nombre || ' ' || dd.porcentaje || '% (' || EXTRACT(YEAR FROM o.fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM o.fecha)::TEXT AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        COALESCE(SUM(dd.total_pesificado), 0) AS distribuciones_uyu,
        COALESCE(SUM(dd.total_dolarizado), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM distribuciones_detalle dd
    JOIN operaciones o ON o.id = dd.operacion_id
    JOIN socios s ON s.id = dd.socio_id
    WHERE o.deleted_at IS NULL AND EXTRACT(YEAR FROM o.fecha) IN (2024, 2025)
    GROUP BY s.nombre, dd.porcentaje, EXTRACT(YEAR FROM o.fecha)
),

-- SECCIÓN 7: RENTABILIDAD POR ÁREA (área × año)
rentabilidad_area AS (
    SELECT 
        '07_RENTABILIDAD_AREA' AS seccion,
        a.nombre || ' (' || EXTRACT(YEAR FROM o.fecha)::TEXT || ') -> ' || 
        ROUND(
            CASE WHEN SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) > 0
            THEN ((SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) - 
                   SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END)) /
                  SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) * 100)
            ELSE 0 END
        , 1)::TEXT || '%' AS dimension,
        EXTRACT(YEAR FROM o.fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones o
    JOIN areas a ON a.id = o.area_id
    WHERE o.deleted_at IS NULL 
    AND a.nombre != 'Otros Gastos'
    AND EXTRACT(YEAR FROM o.fecha) IN (2024, 2025)
    GROUP BY a.nombre, EXTRACT(YEAR FROM o.fecha)
),

-- SECCIÓN 8: TOP 5 CLIENTES POR AÑO
top_clientes AS (
    SELECT seccion, dimension, periodo, ingresos_uyu, ingresos_usd, 
           gastos_uyu, gastos_usd, retiros_uyu, retiros_usd, 
           distribuciones_uyu, distribuciones_usd, cantidad_operaciones
    FROM (
        SELECT 
            '08_TOP_CLIENTES' AS seccion,
            COALESCE(cliente, 'Sin especificar') || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
            EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
            COALESCE(SUM(total_pesificado), 0) AS ingresos_uyu,
            COALESCE(SUM(total_dolarizado), 0) AS ingresos_usd,
            0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
            0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
            0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
            COUNT(*) AS cantidad_operaciones,
            ROW_NUMBER() OVER (PARTITION BY EXTRACT(YEAR FROM fecha) ORDER BY SUM(total_pesificado) DESC) AS rn
        FROM operaciones 
        WHERE deleted_at IS NULL 
        AND tipo_operacion = 'INGRESO'
        AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
        AND cliente IS NOT NULL AND cliente != ''
        GROUP BY cliente, EXTRACT(YEAR FROM fecha)
    ) t WHERE rn <= 5
),

-- SECCIÓN 9: TOP 5 PROVEEDORES POR AÑO
top_proveedores AS (
    SELECT seccion, dimension, periodo, ingresos_uyu, ingresos_usd, 
           gastos_uyu, gastos_usd, retiros_uyu, retiros_usd, 
           distribuciones_uyu, distribuciones_usd, cantidad_operaciones
    FROM (
        SELECT 
            '09_TOP_PROVEEDORES' AS seccion,
            COALESCE(proveedor, 'Sin especificar') || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
            EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
            0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
            COALESCE(SUM(total_pesificado), 0) AS gastos_uyu,
            COALESCE(SUM(total_dolarizado), 0) AS gastos_usd,
            0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
            0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
            COUNT(*) AS cantidad_operaciones,
            ROW_NUMBER() OVER (PARTITION BY EXTRACT(YEAR FROM fecha) ORDER BY SUM(total_pesificado) DESC) AS rn
        FROM operaciones 
        WHERE deleted_at IS NULL 
        AND tipo_operacion = 'GASTO'
        AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
        AND proveedor IS NOT NULL AND proveedor != ''
        GROUP BY proveedor, EXTRACT(YEAR FROM fecha)
    ) t WHERE rn <= 5
)

SELECT * FROM totales
UNION ALL SELECT * FROM por_area
UNION ALL SELECT * FROM por_localidad
UNION ALL SELECT * FROM por_mes
UNION ALL SELECT * FROM retiros_empresa
UNION ALL SELECT * FROM distribuciones_socios
UNION ALL SELECT * FROM rentabilidad_area
UNION ALL SELECT * FROM top_clientes
UNION ALL SELECT * FROM top_proveedores
ORDER BY seccion, periodo, dimension
```

### Pregunta #70: Resumen financiero de 2024
- **Veredicto Final:** WARN
- **Método:** haiku_template_direct_fallback_predefinido
- **Status:** PASS — status=success
- **Dato vs BD:** PASS — Ambos retornan data (55 vs 4 rows)
- **Narrativa vs Dato:** WARN — Dato=11,779,910,057, narrativa menciona: ['80', '77', '100', '21', '100']
- **Narrativa:** **Resumen Ejecutivo**
En 2024 facturamos $2.159.898.268 con gastos de $431.908.069, generando un margen bruto del 80,0%. Las cinco áreas operativas mantuvieron rentabilidades sólidas entre 76,7% y 100%, con distribuciones a socios por $47.665.188.

**Detalle**

**Facturación por área:**
• Administración: $451.257.025 (20,9%) - 100% rentabilidad
• Jurídica: $450.273.635 (20,8%) - 85,3% rentabilidad  
• Notarial: $446.479.655 (20,7%) - 80,8% rentabilidad
• Contable: $431.456.752 (20,0%) - 76,7% re
- **SQL Generado:**
```sql
WITH 
-- SECCIÓN 1: TOTALES GENERALES
totales AS (
    SELECT 
        '01_TOTALES' AS seccion,
        'GENERAL' AS dimension,
        '2024' AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END), 0) AS distribuciones_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_dolarizado ELSE 0 END), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = 2024
),

-- SECCIÓN 2: POR ÁREA
por_area AS (
    SELECT 
        '02_POR_AREA' AS seccion,
        a.nombre AS dimension,
        '2024' AS periodo,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones o
    JOIN areas a ON a.id = o.area_id
    WHERE o.deleted_at IS NULL AND EXTRACT(YEAR FROM o.fecha) = 2024
    GROUP BY a.nombre
),

-- SECCIÓN 3: POR LOCALIDAD
por_localidad AS (
    SELECT 
        '03_POR_LOCALIDAD' AS seccion,
        localidad::TEXT AS dimension,
        '2024' AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = 2024
    GROUP BY localidad
),

-- SECCIÓN 4: POR MES
por_mes AS (
    SELECT 
        '04_POR_MES' AS seccion,
        TO_CHAR(fecha, 'MM-Mon') AS dimension,
        '2024' AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END), 0) AS distribuciones_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_dolarizado ELSE 0 END), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = 2024
    GROUP BY TO_CHAR(fecha, 'MM-Mon')
),

-- SECCIÓN 5: RETIROS DE LA EMPRESA (por localidad y moneda)
retiros_empresa AS (
    SELECT 
        '05_RETIROS_EMPRESA' AS seccion,
        localidad::TEXT || ' - ' || moneda_original::TEXT AS dimension,
        '2024' AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        COALESCE(SUM(total_pesificado), 0) AS retiros_uyu,
        COALESCE(SUM(total_dolarizado), 0) AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND tipo_operacion = 'RETIRO'
    AND EXTRACT(YEAR FROM fecha) = 2024
    GROUP BY localidad, moneda_original
),

-- SECCIÓN 6: DISTRIBUCIONES A SOCIOS
distribuciones_socios AS (
    SELECT 
        '06_DISTRIBUCIONES_SOCIOS' AS seccion,
        s.nombre || ' (' || dd.porcentaje || '%)' AS dimension,
        '2024' AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        COALESCE(SUM(dd.total_pesificado), 0) AS distribuciones_uyu,
        COALESCE(SUM(dd.total_dolarizado), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM distribuciones_detalle dd
    JOIN operaciones o ON o.id = dd.operacion_id
    JOIN socios s ON s.id = dd.socio_id
    WHERE o.deleted_at IS NULL AND EXTRACT(YEAR FROM o.fecha) = 2024
    GROUP BY s.nombre, dd.porcentaje
),

-- SECCIÓN 7: RENTABILIDAD POR ÁREA
rentabilidad_area AS (
    SELECT 
        '07_RENTABILIDAD_AREA' AS seccion,
        a.nombre || ' -> ' || 
        ROUND(
            CASE WHEN SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) > 0
            THEN ((SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) - 
                   SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END)) /
                  SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) * 100)
            ELSE 0 END
        , 1)::TEXT || '% rentabilidad' AS dimension,
        '2024' AS periodo,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones o
    JOIN areas a ON a.id = o.area_id
    WHERE o.deleted_at IS NULL 
    AND a.nombre != 'Otros Gastos'
    AND EXTRACT(YEAR FROM o.fecha) = 2024
    GROUP BY a.nombre
),

-- SECCIÓN 8: TOP 10 CLIENTES
top_clientes AS (
    SELECT 
        '08_TOP_CLIENTES' AS seccion,
        COALESCE(cliente, 'Sin especificar') AS dimension,
        '2024' AS periodo,
        COALESCE(SUM(total_pesificado), 0) AS ingresos_uyu,
        COALESCE(SUM(total_dolarizado), 0) AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND tipo_operacion = 'INGRESO'
    AND EXTRACT(YEAR FROM fecha) = 2024
    AND cliente IS NOT NULL AND cliente != ''
    GROUP BY cliente
    ORDER BY SUM(total_pesificado) DESC
    LIMIT 10
),

-- SECCIÓN 9: TOP 10 PROVEEDORES
top_proveedores AS (
    SELECT 
        '09_TOP_PROVEEDORES' AS seccion,
        COALESCE(proveedor, 'Sin especificar') AS dimension,
        '2024' AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        COALESCE(SUM(total_pesificado), 0) AS gastos_uyu,
        COALESCE(SUM(total_dolarizado), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND tipo_operacion = 'GASTO'
    AND EXTRACT(YEAR FROM fecha) = 2024
    AND proveedor IS NOT NULL AND proveedor != ''
    GROUP BY proveedor
    ORDER BY SUM(total_pesificado) DESC
    LIMIT 10
)

SELECT * FROM totales
UNION ALL SELECT * FROM por_area
UNION ALL SELECT * FROM por_localidad
UNION ALL SELECT * FROM por_mes
UNION ALL SELECT * FROM retiros_empresa
UNION ALL SELECT * FROM distribuciones_socios
UNION ALL SELECT * FROM rentabilidad_area
UNION ALL SELECT * FROM top_clientes
UNION ALL SELECT * FROM top_proveedores
ORDER BY seccion, dimension
```

### Pregunta #71: Rentabilidad por área 2024
- **Veredicto Final:** WARN
- **Método:** haiku_template_direct
- **Status:** PASS — status=success
- **Dato vs BD:** PASS — Ambos retornan data (5 vs 5 rows)
- **Narrativa vs Dato:** WARN — Dato=2,159,898,268, narrativa menciona: ['100', '85', '77', '100', '85']
- **Narrativa:** **Resumen Ejecutivo**
Administración lidera la rentabilidad con 100% (sin gastos asignados), seguida por Jurídica con 85,3%. Contable presenta la menor rentabilidad operativa con 76,7%.

**Detalle**
• Administración: $451.257.025 resultado - 100,0% rentabilidad
• Jurídica: $383.992.398 resultado - 85,3% rentabilidad  
• Notarial: $360.911.770 resultado - 80,8% rentabilidad
• Recuperación: $295.713.690 resultado - 77,7% rentabilidad
• Contable: $330.820.211 resultado - 76,7% rentabilidad

**Análi
- **SQL Generado:**
```sql
SELECT 
    a.nombre AS area,
    COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos,
    COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos,
    COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) - 
    COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS resultado,
    CASE 
        WHEN SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) > 0 
        THEN ROUND(((SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) - 
                     SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END)) / 
                    SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END)) * 100, 2)
        ELSE 0 
    END AS rentabilidad_pct
FROM operaciones o
JOIN areas a ON a.id = o.area_id
WHERE o.deleted_at IS NULL 
AND a.nombre NOT IN ('Otros Gastos')
AND EXTRACT(YEAR FROM o.fecha) = 2024
GROUP BY a.nombre
ORDER BY rentabilidad_pct DESC
```

### Pregunta #72: Comparar segundo trimestre 2024 vs 2025
- **Veredicto Final:** WARN
- **Método:** haiku_template_direct_fallback_predefinido
- **Status:** PASS — status=success
- **Dato vs BD:** PASS — Ambos retornan data (85 vs 8 rows)
- **Narrativa vs Dato:** WARN — Dato=16,086,454,088, narrativa menciona: ['0', '5', '2', '528,756,456', '528,163,888']
- **Narrativa:** **Resumen Ejecutivo**
Los datos disponibles muestran información anual completa para 2024 y 2025, pero no incluyen el desglose específico del segundo trimestre (abril-junio) para realizar la comparación solicitada. Con los datos mensuales disponibles, podemos extraer que en Q2 2024 facturamos $528.756.456 versus $528.163.888 en Q2 2025, prácticamente sin variación.

**Detalle**
**Segundo Trimestre 2024 (Abr-Jun):**
• Ingresos: $528.756.456
• Gastos: $132.263.297
• Resultado bruto: $396.493.159


- **SQL Generado:**
```sql
WITH 
-- SECCIÓN 1: TOTALES POR AÑO
totales AS (
    SELECT 
        '01_TOTALES' AS seccion,
        'AÑO ' || EXTRACT(YEAR FROM fecha)::TEXT AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END), 0) AS distribuciones_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_dolarizado ELSE 0 END), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
    GROUP BY EXTRACT(YEAR FROM fecha)
),

-- SECCIÓN 2: POR ÁREA (cada área × cada año)
por_area AS (
    SELECT 
        '02_POR_AREA' AS seccion,
        a.nombre || ' (' || EXTRACT(YEAR FROM o.fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM o.fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones o
    JOIN areas a ON a.id = o.area_id
    WHERE o.deleted_at IS NULL AND EXTRACT(YEAR FROM o.fecha) IN (2024, 2025)
    GROUP BY a.nombre, EXTRACT(YEAR FROM o.fecha)
),

-- SECCIÓN 3: POR LOCALIDAD (cada localidad × cada año)
por_localidad AS (
    SELECT 
        '03_POR_LOCALIDAD' AS seccion,
        localidad::TEXT || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
    GROUP BY localidad, EXTRACT(YEAR FROM fecha)
),

-- SECCIÓN 4: POR MES (mes × año)
por_mes AS (
    SELECT 
        '04_POR_MES' AS seccion,
        TO_CHAR(fecha, 'Mon') || ' ' || EXTRACT(YEAR FROM fecha)::TEXT AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT || '-' || TO_CHAR(fecha, 'MM') AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END), 0) AS distribuciones_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_dolarizado ELSE 0 END), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
    GROUP BY EXTRACT(YEAR FROM fecha), TO_CHAR(fecha, 'MM'), TO_CHAR(fecha, 'Mon')
),

-- SECCIÓN 5: RETIROS DE LA EMPRESA (por localidad × moneda × año)
retiros_empresa AS (
    SELECT 
        '05_RETIROS_EMPRESA' AS seccion,
        localidad::TEXT || ' ' || moneda_original::TEXT || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        COALESCE(SUM(total_pesificado), 0) AS retiros_uyu,
        COALESCE(SUM(total_dolarizado), 0) AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND tipo_operacion = 'RETIRO'
    AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
    GROUP BY localidad, moneda_original, EXTRACT(YEAR FROM fecha)
),

-- SECCIÓN 6: DISTRIBUCIONES POR SOCIO (socio × año)
distribuciones_socios AS (
    SELECT 
        '06_DISTRIBUCIONES_SOCIOS' AS seccion,
        s.nombre || ' ' || dd.porcentaje || '% (' || EXTRACT(YEAR FROM o.fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM o.fecha)::TEXT AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        COALESCE(SUM(dd.total_pesificado), 0) AS distribuciones_uyu,
        COALESCE(SUM(dd.total_dolarizado), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM distribuciones_detalle dd
    JOIN operaciones o ON o.id = dd.operacion_id
    JOIN socios s ON s.id = dd.socio_id
    WHERE o.deleted_at IS NULL AND EXTRACT(YEAR FROM o.fecha) IN (2024, 2025)
    GROUP BY s.nombre, dd.porcentaje, EXTRACT(YEAR FROM o.fecha)
),

-- SECCIÓN 7: RENTABILIDAD POR ÁREA (área × año)
rentabilidad_area AS (
    SELECT 
        '07_RENTABILIDAD_AREA' AS seccion,
        a.nombre || ' (' || EXTRACT(YEAR FROM o.fecha)::TEXT || ') -> ' || 
        ROUND(
            CASE WHEN SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) > 0
            THEN ((SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) - 
                   SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END)) /
                  SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) * 100)
            ELSE 0 END
        , 1)::TEXT || '%' AS dimension,
        EXTRACT(YEAR FROM o.fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones o
    JOIN areas a ON a.id = o.area_id
    WHERE o.deleted_at IS NULL 
    AND a.nombre != 'Otros Gastos'
    AND EXTRACT(YEAR FROM o.fecha) IN (2024, 2025)
    GROUP BY a.nombre, EXTRACT(YEAR FROM o.fecha)
),

-- SECCIÓN 8: TOP 5 CLIENTES POR AÑO
top_clientes AS (
    SELECT seccion, dimension, periodo, ingresos_uyu, ingresos_usd, 
           gastos_uyu, gastos_usd, retiros_uyu, retiros_usd, 
           distribuciones_uyu, distribuciones_usd, cantidad_operaciones
    FROM (
        SELECT 
            '08_TOP_CLIENTES' AS seccion,
            COALESCE(cliente, 'Sin especificar') || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
            EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
            COALESCE(SUM(total_pesificado), 0) AS ingresos_uyu,
            COALESCE(SUM(total_dolarizado), 0) AS ingresos_usd,
            0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
            0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
            0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
            COUNT(*) AS cantidad_operaciones,
            ROW_NUMBER() OVER (PARTITION BY EXTRACT(YEAR FROM fecha) ORDER BY SUM(total_pesificado) DESC) AS rn
        FROM operaciones 
        WHERE deleted_at IS NULL 
        AND tipo_operacion = 'INGRESO'
        AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
        AND cliente IS NOT NULL AND cliente != ''
        GROUP BY cliente, EXTRACT(YEAR FROM fecha)
    ) t WHERE rn <= 5
),

-- SECCIÓN 9: TOP 5 PROVEEDORES POR AÑO
top_proveedores AS (
    SELECT seccion, dimension, periodo, ingresos_uyu, ingresos_usd, 
           gastos_uyu, gastos_usd, retiros_uyu, retiros_usd, 
           distribuciones_uyu, distribuciones_usd, cantidad_operaciones
    FROM (
        SELECT 
            '09_TOP_PROVEEDORES' AS seccion,
            COALESCE(proveedor, 'Sin especificar') || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
            EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
            0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
            COALESCE(SUM(total_pesificado), 0) AS gastos_uyu,
            COALESCE(SUM(total_dolarizado), 0) AS gastos_usd,
            0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
            0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
            COUNT(*) AS cantidad_operaciones,
            ROW_NUMBER() OVER (PARTITION BY EXTRACT(YEAR FROM fecha) ORDER BY SUM(total_pesificado) DESC) AS rn
        FROM operaciones 
        WHERE deleted_at IS NULL 
        AND tipo_operacion = 'GASTO'
        AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
        AND proveedor IS NOT NULL AND proveedor != ''
        GROUP BY proveedor, EXTRACT(YEAR FROM fecha)
    ) t WHERE rn <= 5
)

SELECT * FROM totales
UNION ALL SELECT * FROM por_area
UNION ALL SELECT * FROM por_localidad
UNION ALL SELECT * FROM por_mes
UNION ALL SELECT * FROM retiros_empresa
UNION ALL SELECT * FROM distribuciones_socios
UNION ALL SELECT * FROM rentabilidad_area
UNION ALL SELECT * FROM top_clientes
UNION ALL SELECT * FROM top_proveedores
ORDER BY seccion, periodo, dimension
```

### Pregunta #73: Comparar primer semestre 2024 vs 2025
- **Veredicto Final:** WARN
- **Método:** haiku_template_direct_fallback_predefinido
- **Status:** PASS — status=success
- **Dato vs BD:** PASS — Ambos retornan data (85 vs 8 rows)
- **Narrativa vs Dato:** WARN — Dato=16,086,454,088, narrativa menciona: ['59', '75', '66', '60', '59']
- **Narrativa:** **Resumen Ejecutivo**
Los ingresos del primer semestre cayeron 58,6% entre 2024 y 2025: de $964.258.641 a $529.192.889. Recuperación es la única área que creció, mientras que todas las demás retrocedieron significativamente.

**Detalle**

*Ingresos por área - Primer semestre:*
• **Administración**: $225.628.513 (2024) vs $56.542.125 (2025) → -75,0%
• **Contable**: $215.728.376 (2024) vs $73.271.830 (2025) → -66,0%
• **Jurídica**: $225.136.817 (2024) vs $90.015.644 (2025) → -60,0%
• **Notarial**:
- **SQL Generado:**
```sql
WITH 
-- SECCIÓN 1: TOTALES POR AÑO
totales AS (
    SELECT 
        '01_TOTALES' AS seccion,
        'AÑO ' || EXTRACT(YEAR FROM fecha)::TEXT AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END), 0) AS distribuciones_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_dolarizado ELSE 0 END), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
    GROUP BY EXTRACT(YEAR FROM fecha)
),

-- SECCIÓN 2: POR ÁREA (cada área × cada año)
por_area AS (
    SELECT 
        '02_POR_AREA' AS seccion,
        a.nombre || ' (' || EXTRACT(YEAR FROM o.fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM o.fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones o
    JOIN areas a ON a.id = o.area_id
    WHERE o.deleted_at IS NULL AND EXTRACT(YEAR FROM o.fecha) IN (2024, 2025)
    GROUP BY a.nombre, EXTRACT(YEAR FROM o.fecha)
),

-- SECCIÓN 3: POR LOCALIDAD (cada localidad × cada año)
por_localidad AS (
    SELECT 
        '03_POR_LOCALIDAD' AS seccion,
        localidad::TEXT || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
    GROUP BY localidad, EXTRACT(YEAR FROM fecha)
),

-- SECCIÓN 4: POR MES (mes × año)
por_mes AS (
    SELECT 
        '04_POR_MES' AS seccion,
        TO_CHAR(fecha, 'Mon') || ' ' || EXTRACT(YEAR FROM fecha)::TEXT AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT || '-' || TO_CHAR(fecha, 'MM') AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END), 0) AS distribuciones_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_dolarizado ELSE 0 END), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
    GROUP BY EXTRACT(YEAR FROM fecha), TO_CHAR(fecha, 'MM'), TO_CHAR(fecha, 'Mon')
),

-- SECCIÓN 5: RETIROS DE LA EMPRESA (por localidad × moneda × año)
retiros_empresa AS (
    SELECT 
        '05_RETIROS_EMPRESA' AS seccion,
        localidad::TEXT || ' ' || moneda_original::TEXT || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        COALESCE(SUM(total_pesificado), 0) AS retiros_uyu,
        COALESCE(SUM(total_dolarizado), 0) AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND tipo_operacion = 'RETIRO'
    AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
    GROUP BY localidad, moneda_original, EXTRACT(YEAR FROM fecha)
),

-- SECCIÓN 6: DISTRIBUCIONES POR SOCIO (socio × año)
distribuciones_socios AS (
    SELECT 
        '06_DISTRIBUCIONES_SOCIOS' AS seccion,
        s.nombre || ' ' || dd.porcentaje || '% (' || EXTRACT(YEAR FROM o.fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM o.fecha)::TEXT AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        COALESCE(SUM(dd.total_pesificado), 0) AS distribuciones_uyu,
        COALESCE(SUM(dd.total_dolarizado), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM distribuciones_detalle dd
    JOIN operaciones o ON o.id = dd.operacion_id
    JOIN socios s ON s.id = dd.socio_id
    WHERE o.deleted_at IS NULL AND EXTRACT(YEAR FROM o.fecha) IN (2024, 2025)
    GROUP BY s.nombre, dd.porcentaje, EXTRACT(YEAR FROM o.fecha)
),

-- SECCIÓN 7: RENTABILIDAD POR ÁREA (área × año)
rentabilidad_area AS (
    SELECT 
        '07_RENTABILIDAD_AREA' AS seccion,
        a.nombre || ' (' || EXTRACT(YEAR FROM o.fecha)::TEXT || ') -> ' || 
        ROUND(
            CASE WHEN SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) > 0
            THEN ((SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) - 
                   SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END)) /
                  SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) * 100)
            ELSE 0 END
        , 1)::TEXT || '%' AS dimension,
        EXTRACT(YEAR FROM o.fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones o
    JOIN areas a ON a.id = o.area_id
    WHERE o.deleted_at IS NULL 
    AND a.nombre != 'Otros Gastos'
    AND EXTRACT(YEAR FROM o.fecha) IN (2024, 2025)
    GROUP BY a.nombre, EXTRACT(YEAR FROM o.fecha)
),

-- SECCIÓN 8: TOP 5 CLIENTES POR AÑO
top_clientes AS (
    SELECT seccion, dimension, periodo, ingresos_uyu, ingresos_usd, 
           gastos_uyu, gastos_usd, retiros_uyu, retiros_usd, 
           distribuciones_uyu, distribuciones_usd, cantidad_operaciones
    FROM (
        SELECT 
            '08_TOP_CLIENTES' AS seccion,
            COALESCE(cliente, 'Sin especificar') || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
            EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
            COALESCE(SUM(total_pesificado), 0) AS ingresos_uyu,
            COALESCE(SUM(total_dolarizado), 0) AS ingresos_usd,
            0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
            0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
            0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
            COUNT(*) AS cantidad_operaciones,
            ROW_NUMBER() OVER (PARTITION BY EXTRACT(YEAR FROM fecha) ORDER BY SUM(total_pesificado) DESC) AS rn
        FROM operaciones 
        WHERE deleted_at IS NULL 
        AND tipo_operacion = 'INGRESO'
        AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
        AND cliente IS NOT NULL AND cliente != ''
        GROUP BY cliente, EXTRACT(YEAR FROM fecha)
    ) t WHERE rn <= 5
),

-- SECCIÓN 9: TOP 5 PROVEEDORES POR AÑO
top_proveedores AS (
    SELECT seccion, dimension, periodo, ingresos_uyu, ingresos_usd, 
           gastos_uyu, gastos_usd, retiros_uyu, retiros_usd, 
           distribuciones_uyu, distribuciones_usd, cantidad_operaciones
    FROM (
        SELECT 
            '09_TOP_PROVEEDORES' AS seccion,
            COALESCE(proveedor, 'Sin especificar') || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
            EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
            0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
            COALESCE(SUM(total_pesificado), 0) AS gastos_uyu,
            COALESCE(SUM(total_dolarizado), 0) AS gastos_usd,
            0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
            0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
            COUNT(*) AS cantidad_operaciones,
            ROW_NUMBER() OVER (PARTITION BY EXTRACT(YEAR FROM fecha) ORDER BY SUM(total_pesificado) DESC) AS rn
        FROM operaciones 
        WHERE deleted_at IS NULL 
        AND tipo_operacion = 'GASTO'
        AND EXTRACT(YEAR FROM fecha) IN (2024, 2025)
        AND proveedor IS NOT NULL AND proveedor != ''
        GROUP BY proveedor, EXTRACT(YEAR FROM fecha)
    ) t WHERE rn <= 5
)

SELECT * FROM totales
UNION ALL SELECT * FROM por_area
UNION ALL SELECT * FROM por_localidad
UNION ALL SELECT * FROM por_mes
UNION ALL SELECT * FROM retiros_empresa
UNION ALL SELECT * FROM distribuciones_socios
UNION ALL SELECT * FROM rentabilidad_area
UNION ALL SELECT * FROM top_clientes
UNION ALL SELECT * FROM top_proveedores
ORDER BY seccion, periodo, dimension
```

### Pregunta #74: Informe ejecutivo 2024
- **Veredicto Final:** WARN
- **Método:** haiku_template_direct_fallback_predefinido
- **Status:** PASS — status=success
- **Dato vs BD:** PASS — Ambos retornan data (55 vs 4 rows)
- **Narrativa vs Dato:** WARN — Dato=11,779,910,057, narrativa menciona: ['2,100,000,000', '80', '76', '100', '21']
- **Narrativa:** **Resumen Ejecutivo**
Conexión Consultora cerró 2024 con una facturación de $2.159.898.268 y un margen operativo del 80,0%. Las cinco áreas de negocio mostraron rentabilidades superiores al 76%, con Administración liderando al 100% y distribuciones a socios por $47.665.188.

**Detalle**

**Facturación por Área:**
• Administración: $451.257.025 (20,9%) - 100,0% rentabilidad
• Jurídica: $450.273.635 (20,8%) - 85,3% rentabilidad  
• Notarial: $446.479.655 (20,7%) - 80,8% rentabilidad
• Contable: $4
- **SQL Generado:**
```sql
WITH 
-- SECCIÓN 1: TOTALES GENERALES
totales AS (
    SELECT 
        '01_TOTALES' AS seccion,
        'GENERAL' AS dimension,
        '2024' AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END), 0) AS distribuciones_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_dolarizado ELSE 0 END), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = 2024
),

-- SECCIÓN 2: POR ÁREA
por_area AS (
    SELECT 
        '02_POR_AREA' AS seccion,
        a.nombre AS dimension,
        '2024' AS periodo,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones o
    JOIN areas a ON a.id = o.area_id
    WHERE o.deleted_at IS NULL AND EXTRACT(YEAR FROM o.fecha) = 2024
    GROUP BY a.nombre
),

-- SECCIÓN 3: POR LOCALIDAD
por_localidad AS (
    SELECT 
        '03_POR_LOCALIDAD' AS seccion,
        localidad::TEXT AS dimension,
        '2024' AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = 2024
    GROUP BY localidad
),

-- SECCIÓN 4: POR MES
por_mes AS (
    SELECT 
        '04_POR_MES' AS seccion,
        TO_CHAR(fecha, 'MM-Mon') AS dimension,
        '2024' AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END), 0) AS distribuciones_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_dolarizado ELSE 0 END), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = 2024
    GROUP BY TO_CHAR(fecha, 'MM-Mon')
),

-- SECCIÓN 5: RETIROS DE LA EMPRESA (por localidad y moneda)
retiros_empresa AS (
    SELECT 
        '05_RETIROS_EMPRESA' AS seccion,
        localidad::TEXT || ' - ' || moneda_original::TEXT AS dimension,
        '2024' AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        COALESCE(SUM(total_pesificado), 0) AS retiros_uyu,
        COALESCE(SUM(total_dolarizado), 0) AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND tipo_operacion = 'RETIRO'
    AND EXTRACT(YEAR FROM fecha) = 2024
    GROUP BY localidad, moneda_original
),

-- SECCIÓN 6: DISTRIBUCIONES A SOCIOS
distribuciones_socios AS (
    SELECT 
        '06_DISTRIBUCIONES_SOCIOS' AS seccion,
        s.nombre || ' (' || dd.porcentaje || '%)' AS dimension,
        '2024' AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        COALESCE(SUM(dd.total_pesificado), 0) AS distribuciones_uyu,
        COALESCE(SUM(dd.total_dolarizado), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM distribuciones_detalle dd
    JOIN operaciones o ON o.id = dd.operacion_id
    JOIN socios s ON s.id = dd.socio_id
    WHERE o.deleted_at IS NULL AND EXTRACT(YEAR FROM o.fecha) = 2024
    GROUP BY s.nombre, dd.porcentaje
),

-- SECCIÓN 7: RENTABILIDAD POR ÁREA
rentabilidad_area AS (
    SELECT 
        '07_RENTABILIDAD_AREA' AS seccion,
        a.nombre || ' -> ' || 
        ROUND(
            CASE WHEN SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) > 0
            THEN ((SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) - 
                   SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END)) /
                  SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) * 100)
            ELSE 0 END
        , 1)::TEXT || '% rentabilidad' AS dimension,
        '2024' AS periodo,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones o
    JOIN areas a ON a.id = o.area_id
    WHERE o.deleted_at IS NULL 
    AND a.nombre != 'Otros Gastos'
    AND EXTRACT(YEAR FROM o.fecha) = 2024
    GROUP BY a.nombre
),

-- SECCIÓN 8: TOP 10 CLIENTES
top_clientes AS (
    SELECT 
        '08_TOP_CLIENTES' AS seccion,
        COALESCE(cliente, 'Sin especificar') AS dimension,
        '2024' AS periodo,
        COALESCE(SUM(total_pesificado), 0) AS ingresos_uyu,
        COALESCE(SUM(total_dolarizado), 0) AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND tipo_operacion = 'INGRESO'
    AND EXTRACT(YEAR FROM fecha) = 2024
    AND cliente IS NOT NULL AND cliente != ''
    GROUP BY cliente
    ORDER BY SUM(total_pesificado) DESC
    LIMIT 10
),

-- SECCIÓN 9: TOP 10 PROVEEDORES
top_proveedores AS (
    SELECT 
        '09_TOP_PROVEEDORES' AS seccion,
        COALESCE(proveedor, 'Sin especificar') AS dimension,
        '2024' AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        COALESCE(SUM(total_pesificado), 0) AS gastos_uyu,
        COALESCE(SUM(total_dolarizado), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND tipo_operacion = 'GASTO'
    AND EXTRACT(YEAR FROM fecha) = 2024
    AND proveedor IS NOT NULL AND proveedor != ''
    GROUP BY proveedor
    ORDER BY SUM(total_pesificado) DESC
    LIMIT 10
)

SELECT * FROM totales
UNION ALL SELECT * FROM por_area
UNION ALL SELECT * FROM por_localidad
UNION ALL SELECT * FROM por_mes
UNION ALL SELECT * FROM retiros_empresa
UNION ALL SELECT * FROM distribuciones_socios
UNION ALL SELECT * FROM rentabilidad_area
UNION ALL SELECT * FROM top_clientes
UNION ALL SELECT * FROM top_proveedores
ORDER BY seccion, dimension
```

### Pregunta #96: ¿Cuál es la correlación entre retiros y resultado neto mensual?
- **Veredicto Final:** FAIL
- **Método:** desconocido
- **Status:** FAIL — status=error: 
- **Dato vs BD:** PASS — Routing — validación solo de status/narrativa
- **Narrativa vs Dato:** PASS — Narrativa presente
- **Narrativa:** No pude obtener datos. Error: (psycopg2.errors.GroupingError) aggregate function calls cannot contain window function calls
LINE 20:         SUM((resultado_neto - AVG(resultado_neto) OVER()) * ...
                                       ^

[SQL: WITH datos_mensuales AS (
    SELECT 
        EXTRACT(YEAR FROM fecha) AS anio,
        EXTRACT(MONTH FROM fecha) AS mes,
        SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END) -
        SUM(CASE WHEN tipo_operacion = 'GASTO' T
- **SQL Generado:**
```sql
WITH datos_mensuales AS (
    SELECT 
        EXTRACT(YEAR FROM fecha) AS anio,
        EXTRACT(MONTH FROM fecha) AS mes,
        SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END) -
        SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END) AS resultado_neto,
        SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END) AS retiros
    FROM operaciones
    WHERE deleted_at IS NULL
    GROUP BY EXTRACT(YEAR FROM fecha), EXTRACT(MONTH FROM fecha)
    HAVING SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END) -
           SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END) IS NOT NULL
       AND SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END) IS NOT NULL
),
estadisticas AS (
    SELECT 
        COUNT(*) AS n,
        AVG(resultado_neto) AS media_resultado,
        AVG(retiros) AS media_retiros,
        SUM((resultado_neto - AVG(resultado_neto) OVER()) * (retiros - AVG(retiros) OVER())) AS suma_productos,
        SQRT(SUM(POWER(resultado_neto - AVG(resultado_neto) OVER(), 2))) AS desv_resultado,
        SQRT(SUM(POWER(retiros - AVG(retiros) OVER(), 2))) AS desv_retiros
    FROM datos_mensuales
)
SELECT 
    ROUND(
        CASE 
            WHEN desv_resultado * desv_retiros > 0 
            THEN suma_productos / (desv_resultado * desv_retiros)
            ELSE 0 
        END, 4
    ) AS correlacion_pearson,
    n AS meses_analizados,
    ROUND(media_resultado, 2) AS resultado_neto_promedio,
    ROUND(media_retiros, 2) AS retiros_promedio
FROM estadisticas
```
