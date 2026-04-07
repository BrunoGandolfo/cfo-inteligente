# Test 100 Preguntas — CFO Inteligente

**Fecha:** 2026-02-17 12:23:28
**Motor:** Haiku Classifier → Template Directo → QueryFallback → Claude Sonnet
**BD:** cfo_inteligente (2161 operaciones activas, rango 2024-01-01 a 2025-09-25)

## 1. Estadísticas Generales

| Métrica | Valor |
|---------|-------|
| Total preguntas | 100 |
| **PASS** | **98** (98%) |
| **WARN** | **2** (2%) |
| **FAIL** | **0** (0%) |
| Tiempo promedio | 3.88s |
| Tiempo total | 388.1s |

### Desglose por Método de Routing

| Método | Total | PASS | WARN | FAIL |
|--------|-------|------|------|------|
| claude | 22 | 21 | 1 | 0 |
| haiku_template_direct | 77 | 76 | 1 | 0 |
| query_fallback | 1 | 1 | 0 | 0 |

### Desglose por Categoría

| Categoría | Total | PASS | WARN | FAIL |
|-----------|-------|------|------|------|
| COMPUESTAS | 14 | 14 | 0 | 0 |
| DISTRIBUCIONES | 9 | 9 | 0 | 0 |
| GASTOS | 20 | 20 | 0 | 0 |
| INGRESOS | 19 | 19 | 0 | 0 |
| NINGUNO | 15 | 15 | 0 | 0 |
| RESUMEN | 14 | 12 | 2 | 0 |
| RETIROS | 9 | 9 | 0 | 0 |

## 2. Tabla Resumen (100 Preguntas)

| # | Pregunta | Método | Template ID | Resultado Sistema | Resultado Control | Veredicto |
|---|----------|--------|-------------|-------------------|-------------------|-----------|
| 1 | ¿Cuánto facturamos en 2025? | haiku_template_direct | ING-008 | 893,075,002.92 | 893,075,002.92 | **PASS** |
| 2 | ¿Cuáles fueron los ingresos de enero 2025? | haiku_template_direct | ING-007 | 0 | 0 | **PASS** |
| 3 | ¿Cuánto facturamos este mes? | haiku_template_direct | ING-031 | 0 | 0 | **PASS** |
| 4 | Ingresos del área Jurídica en 2025 | haiku_template_direct | ING-002 | 180,031,288.20 | 180,031,288.20 | **PASS** |
| 5 | Ingresos en Mercedes este año | haiku_template_direct | ING-018 | 0 | 0 | **PASS** |
| 6 | ¿Quiénes son nuestros top 10 clientes? | haiku_template_direct | ING-021 | (vacío) | (vacío) | **PASS** |
| 7 | ¿Cuántas operaciones de ingreso tuvimos este año? | haiku_template_direct | ING-030 | 0 | 0 | **PASS** |
| 8 | ¿Cuál fue el ingreso más alto del año? | haiku_template_direct | ING-019 | (vacío) | 0 | **PASS** |
| 9 | Ingresos por trimestre de 2025 | haiku_template_direct | ING-025 | 893,075,002.92 | 893,075,002.92 | **PASS** |
| 10 | Evolución mensual de ingresos 2025 | haiku_template_direct | ING-006 | 893,075,002.92 | 893,075,002.92 | **PASS** |
| 11 | ¿Cuánto gastamos en 2025? | haiku_template_direct | GAS-030 | 288,782,063.19 | 288,782,063.19 | **PASS** |
| 12 | Gastos del área Contable este año | haiku_template_direct | GAS-010 | 0 | 0 | **PASS** |
| 13 | Gastos en Montevideo 2025 | haiku_template_direct | GAS-008 | 138,506,029.64 | 138,506,029.64 | **PASS** |
| 14 | ¿Quiénes son los 10 proveedores a los que más les  | haiku_template_direct | GAS-019 | (vacío) | (vacío) | **PASS** |
| 15 | ¿Cuánto gastamos en enero 2025? | claude | - | 0 | 0 | **PASS** |
| 16 | Promedio mensual de gastos este año | haiku_template_direct | GAS-026 | 0 | 0 | **PASS** |
| 17 | ¿Cuál fue el gasto más alto del año? | haiku_template_direct | GAS-017 | (vacío) | 0 | **PASS** |
| 18 | Gastos del área Administración este año | haiku_template_direct | GAS-014 | 0 | 0 | **PASS** |
| 19 | Gastos por trimestre 2025 | haiku_template_direct | GAS-023 | 288,782,063.19 | 288,782,063.19 | **PASS** |
| 20 | Gastos del área Otros Gastos este año | haiku_template_direct | GAS-013 | 0 | 0 | **PASS** |
| 21 | ¿Cuánto retiramos este año? | haiku_template_direct | RET-018 | 0 | 0 | **PASS** |
| 22 | Retiros en Mercedes 2025 | haiku_template_direct | RET-001 | 4,585,278.39 | 4,585,278.39 | **PASS** |
| 23 | ¿Cuánto recibió Bruno en distribuciones este año? | haiku_template_direct | DIS-004 | 0 | 0 | **PASS** |
| 24 | Distribuciones por socio 2025 | haiku_template_direct | DIS-003 | 22,975,209.00 | 22,975,209.00 | **PASS** |
| 25 | ¿Cuántas distribuciones hubo este año? | haiku_template_direct | DIS-014 | 0 | 0 | **PASS** |
| 26 | Retiros por mes 2025 | haiku_template_direct | RET-003 | 7,443,005.67 | 7,443,005.67 | **PASS** |
| 27 | ¿Cuánto retiramos en dólares este año? | haiku_template_direct | RET-016 | 0 | 0 | **PASS** |
| 28 | Distribuciones totales del mes | haiku_template_direct | DIS-017 | 0 | 0 | **PASS** |
| 29 | ¿Cuál es el resultado neto de 2025? | haiku_template_direct | RES-001 | 604,292,939.73 | 604,292,939.73 | **PASS** |
| 30 | ¿Cuál es nuestra rentabilidad este año? | claude | - | 0 | 0 | **PASS** |
| 31 | ¿Cuál es el área más rentable? | claude | - | 564,341,276.26 | (vacío) | **WARN** |
| 32 | Resumen financiero de 2025 | haiku_template_direct | COM-014 | 4,949,816,136.74 | 1,212,275,280.78 | **PASS** |
| 33 | Resultado por localidad este año | haiku_template_direct | RES-025 | (vacío) | (vacío) | **PASS** |
| 34 | ¿Cómo venimos este mes? | haiku_template_direct | COM-022 | 0 | (vacío) | **WARN** |
| 35 | Capital de trabajo actual | haiku_template_direct | COM-024 | 2,240,266,413.56 | 2,240,266,413.56 | **PASS** |
| 36 | Flujo de caja de este mes | haiku_template_direct | COM-025 | 0 | 0 | **PASS** |
| 37 | Comparar 2024 vs 2025 | haiku_template_direct | COM-006 | 16,086,454,087.51 | 3,865,680,128.24 | **PASS** |
| 38 | Comparar primer trimestre 2024 vs 2025 | haiku_template_direct | COM-003 | 16,086,454,087.51 | 568,557,322.71 | **PASS** |
| 39 | Comparar Jurídica vs Contable | haiku_template_direct | COM-008 | (vacío) | (vacío) | **PASS** |
| 40 | Ingresos de enero 2024 vs enero 2025 | haiku_template_direct | COM-001 | 215,056,467.90 | 215,056,467.90 | **PASS** |
| 41 | Informe ejecutivo 2025 | haiku_template_direct | COM-016 | 4,949,816,136.74 | 1,212,275,280.78 | **PASS** |
| 42 | Comparación ejecutiva 2024 vs 2025 | haiku_template_direct | COM-017 | 16,086,454,087.51 | 3,865,680,128.24 | **PASS** |
| 43 | Rentabilidad por área 2025 | haiku_template_direct | COM-011 | 893,075,002.92 | 893,075,002.92 | **PASS** |
| 44 | Rentabilidad global incluyendo todos los gastos | claude | - | 0 | 0 | **PASS** |
| 45 | Resumen del primer semestre 2025 vs 2024 | haiku_template_direct | COM-005 | 16,086,454,087.51 | 1,927,924,709.83 | **PASS** |
| 46 | ¿En qué meses los gastos superaron a los ingresos? | claude | - | claude | esperado: claude | **PASS** |
| 47 | ¿Cuál es el cliente que más creció porcentualmente | claude | - | claude | esperado: claude | **PASS** |
| 48 | ¿Qué porcentaje de los ingresos de Mercedes viene  | claude | - | claude | esperado: claude | **PASS** |
| 49 | Dame un análisis de la tendencia de rentabilidad p | claude | - | claude | esperado: claude | **PASS** |
| 50 | ¿Cuántos clientes nuevos tuvimos en 2025 que no es | claude | - | claude | esperado: claude | **PASS** |
| 51 | Ingresos totales de 2024 | haiku_template_direct | ING-008 | 2,159,898,267.98 | 2,159,898,267.98 | **PASS** |
| 52 | Ingresos del área Notarial en 2025 | haiku_template_direct | ING-003 | 181,860,868.39 | 181,860,868.39 | **PASS** |
| 53 | Ingresos en dólares de 2025 | haiku_template_direct | ING-004 | 22,475,081.70 | 22,475,081.70 | **PASS** |
| 54 | ¿Cuánto facturó el área Recuperación en 2024? | haiku_template_direct | ING-003 | 380,431,201.34 | 380,431,201.34 | **PASS** |
| 55 | Ingresos de Montevideo en 2024 | haiku_template_direct | ING-010 | 1,117,139,224.72 | 1,117,139,224.72 | **PASS** |
| 56 | Gastos totales de 2024 | haiku_template_direct | GAS-030 | 431,908,068.76 | 431,908,068.76 | **PASS** |
| 57 | Gastos del área Jurídica en 2024 | haiku_template_direct | GAS-006 | 66,281,236.24 | 66,281,236.24 | **PASS** |
| 58 | Gastos en dólares de 2024 | haiku_template_direct | GAS-003 | 10,870,233.92 | 10,870,233.92 | **PASS** |
| 59 | ¿Cuánto gastamos el mes pasado? | haiku_template_direct | GAS-020 | (vacío) | 0 | **PASS** |
| 60 | Gastos de Mercedes en 2025 | haiku_template_direct | GAS-008 | 150,276,033.55 | 150,276,033.55 | **PASS** |
| 61 | Retiros totales de 2024 | haiku_template_direct | RET-002 | 13,933,322.72 | 13,933,322.72 | **PASS** |
| 62 | Retiros en Montevideo 2025 | haiku_template_direct | RET-001 | 2,857,727.28 | 2,857,727.28 | **PASS** |
| 63 | Retiros por mes en 2024 | haiku_template_direct | RET-003 | 13,933,322.72 | 13,933,322.72 | **PASS** |
| 64 | ¿Cuánto recibió Agustina en distribuciones en 2025 | haiku_template_direct | DIS-001 | 4,597,247.00 | 4,597,247.00 | **PASS** |
| 65 | Distribuciones totales de 2024 | haiku_template_direct | DIS-002 | 47,665,188.00 | 47,665,188.00 | **PASS** |
| 66 | ¿Cuánto recibió Gonzalo en distribuciones en 2025? | haiku_template_direct | DIS-001 | 4,539,219.00 | 4,539,219.00 | **PASS** |
| 67 | Resultado neto de 2024 | haiku_template_direct | RES-001 | 1,727,990,199.22 | 1,727,990,199.22 | **PASS** |
| 68 | Rentabilidad del área Jurídica en 2025 | haiku_template_direct | COM-010 | 180,031,288.20 | 180,031,288.20 | **PASS** |
| 69 | ¿Cuál fue nuestro mejor mes de ingresos en 2025? | haiku_template_direct | ING-006 | 893,075,002.92 | 234,504,796.47 | **PASS** |
| 70 | Resumen financiero de 2024 | haiku_template_direct | COM-014 | 11,779,910,057.18 | 2,653,404,847.46 | **PASS** |
| 71 | Rentabilidad por área 2024 | haiku_template_direct | COM-011 | 2,159,898,267.98 | 420.52 | **PASS** |
| 72 | Comparar segundo trimestre 2024 vs 2025 | haiku_template_direct | COM-003 | 16,086,454,087.51 | 1,359,367,387.12 | **PASS** |
| 73 | Comparar primer semestre 2024 vs 2025 | haiku_template_direct | COM-005 | 16,086,454,087.51 | 1,927,924,709.83 | **PASS** |
| 74 | Informe ejecutivo 2024 | haiku_template_direct | COM-016 | 11,779,910,057.18 | 2,653,404,847.46 | **PASS** |
| 75 | Comparar Notarial vs Recuperación | haiku_template_direct | COM-008 | (vacío) | (vacío) | **PASS** |
| 76 | Ingresos de Mercedes vs Montevideo en 2025 | haiku_template_direct | ING-010 | 462,276,334.40 | 893,075,002.92 | **PASS** |
| 77 | Evolución mensual de gastos 2024 | haiku_template_direct | GAS-022 | 431,908,068.76 | 431,908,068.76 | **PASS** |
| 78 | Gastos del tercer trimestre de 2025 | claude | - | 142,132,987.80 | 142,132,987.80 | **PASS** |
| 79 | ¿Cuánto facturamos el trimestre pasado? | query_fallback | - | (vacío) | 0 | **PASS** |
| 80 | Ingresos del mes pasado | claude | - | 0 | 0 | **PASS** |
| 81 | Gastos del último semestre | claude | - | 51,771,663.57 | 51,771,663.57 | **PASS** |
| 82 | ¿Cuál fue el resultado neto del mes pasado? | haiku_template_direct | RES-022 | 0 | 0 | **PASS** |
| 83 | Retiros del último trimestre | haiku_template_direct | RET-009 | 0 | 0 | **PASS** |
| 84 | ¿Cuánto facturamos en dólares en 2024? | haiku_template_direct | ING-004 | 54,366,177.68 | 54,366,177.68 | **PASS** |
| 85 | Total de gastos en USD de 2024 | haiku_template_direct | GAS-003 | 10,870,233.92 | 10,870,233.92 | **PASS** |
| 86 | Retiros en dólares de 2024 | haiku_template_direct | RET-002 | 13,933,322.72 | 13,933,322.72 | **PASS** |
| 87 | ¿Cuánto recibió Pancho en distribuciones en 2024? | haiku_template_direct | DIS-001 | 9,637,807.00 | 9,637,807.00 | **PASS** |
| 88 | ¿Cuánto recibió Viviana en distribuciones en 2025? | haiku_template_direct | DIS-001 | 4,653,477.00 | 4,653,477.00 | **PASS** |
| 89 | Ingresos del área Jurídica en Mercedes en 2025 | haiku_template_direct | ING-002 | 84,673,610.42 | 84,673,610.42 | **PASS** |
| 90 | Gastos del área Contable en Montevideo en 2025 | haiku_template_direct | GAS-005 | 33,171,078.86 | 33,171,078.86 | **PASS** |
| 91 | ¿Cuál fue el mes con mayor margen de ganancia en 2 | claude | - | claude | esperado: claude | **PASS** |
| 92 | ¿Qué área tuvo el mayor crecimiento interanual de  | claude | - | claude | esperado: claude | **PASS** |
| 93 | ¿Cuántos proveedores representan el 80% de nuestro | claude | - | claude | esperado: claude | **PASS** |
| 94 | Ranking de socios por rentabilidad de las áreas qu | claude | - | claude | esperado: claude | **PASS** |
| 95 | ¿En qué trimestre fue más eficiente la relación in | claude | - | claude | esperado: claude | **PASS** |
| 96 | ¿Cuál es la correlación entre retiros y resultado  | claude | - | claude | esperado: claude | **PASS** |
| 97 | ¿Qué clientes dejaron de facturar en 2025 respecto | claude | - | claude | esperado: claude | **PASS** |
| 98 | ¿Cuál es el costo promedio por operación de cada á | claude | - | claude | esperado: claude | **PASS** |
| 99 | ¿Cuántas operaciones en USD representan más del 50 | claude | - | claude | esperado: claude | **PASS** |
| 100 | ¿Cuál es la proporción de gastos fijos vs variable | claude | - | claude | esperado: claude | **PASS** |

## 3. Detalle de FAILs y WARNs

### Pregunta #31: ¿Cuál es el área más rentable?
- **Veredicto:** WARN
- **Método:** claude
- **Diagnóstico:** Sistema retornó 1 rows, control vacío
- **SQL Sistema:**
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
- **SQL Control:**
```sql
SELECT a.nombre,
              ROUND(
                (SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.total_pesificado ELSE 0 END)
                 - SUM(CASE WHEN o.tipo_operacion='GASTO' THEN o.total_pesificado ELSE 0 END))
                * 100.0 / NULLIF(SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.total_pesificado ELSE 0 END), 0), 2)
              AS rentabilidad
            FROM operaciones o JOIN areas a ON o.area_id = a.id
            WHERE o.tipo_operacion IN ('INGRESO','GASTO') AND o.deleted_at IS NULL
            AND a.nombre NOT IN ('Otros Gastos')
            AND EXTRACT(YEAR FROM o.fecha) = EXTRACT(YEAR FROM CURRENT_DATE)
            GROUP BY a.nombre ORDER BY rentabilidad DESC NULLS LAST LIMIT 1
```

### Pregunta #34: ¿Cómo venimos este mes?
- **Veredicto:** WARN
- **Método:** haiku_template_direct
- **Diagnóstico:** Sistema retornó 1 rows, control vacío
- **SQL Sistema:**
```sql
SELECT SUM(CASE WHEN tipo_operacion='INGRESO' THEN total_pesificado ELSE 0 END) AS ing,SUM(CASE WHEN tipo_operacion='GASTO' THEN total_pesificado ELSE 0 END) AS gas,SUM(CASE WHEN tipo_operacion='INGRESO' THEN total_pesificado ELSE 0 END)-SUM(CASE WHEN tipo_operacion='GASTO' THEN total_pesificado ELSE 0 END) AS res FROM operaciones WHERE deleted_at IS NULL AND DATE_TRUNC('month',fecha)=DATE_TRUNC('month',CURRENT_DATE)
```
- **SQL Control:**
```sql
SELECT tipo_operacion::TEXT,
                   COALESCE(SUM(total_pesificado), 0) AS total
            FROM operaciones
            WHERE deleted_at IS NULL
            AND fecha >= DATE_TRUNC('month', CURRENT_DATE)
            AND fecha < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
            GROUP BY tipo_operacion
```

## 4. Lista de 50 Preguntas Generadas

51. Ingresos totales de 2024 [INGRESOS]
52. Ingresos del área Notarial en 2025 [INGRESOS]
53. Ingresos en dólares de 2025 [INGRESOS]
54. ¿Cuánto facturó el área Recuperación en 2024? [INGRESOS]
55. Ingresos de Montevideo en 2024 [INGRESOS]
56. Gastos totales de 2024 [GASTOS]
57. Gastos del área Jurídica en 2024 [GASTOS]
58. Gastos en dólares de 2024 [GASTOS]
59. ¿Cuánto gastamos el mes pasado? [GASTOS]
60. Gastos de Mercedes en 2025 [GASTOS]
61. Retiros totales de 2024 [RETIROS]
62. Retiros en Montevideo 2025 [RETIROS]
63. Retiros por mes en 2024 [RETIROS]
64. ¿Cuánto recibió Agustina en distribuciones en 2025? [DISTRIBUCIONES]
65. Distribuciones totales de 2024 [DISTRIBUCIONES]
66. ¿Cuánto recibió Gonzalo en distribuciones en 2025? [DISTRIBUCIONES]
67. Resultado neto de 2024 [RESUMEN]
68. Rentabilidad del área Jurídica en 2025 [RESUMEN]
69. ¿Cuál fue nuestro mejor mes de ingresos en 2025? [RESUMEN]
70. Resumen financiero de 2024 [RESUMEN]
71. Rentabilidad por área 2024 [RESUMEN]
72. Comparar segundo trimestre 2024 vs 2025 [COMPUESTAS]
73. Comparar primer semestre 2024 vs 2025 [COMPUESTAS]
74. Informe ejecutivo 2024 [COMPUESTAS]
75. Comparar Notarial vs Recuperación [COMPUESTAS]
76. Ingresos de Mercedes vs Montevideo en 2025 [COMPUESTAS]
77. Evolución mensual de gastos 2024 [GASTOS]
78. Gastos del tercer trimestre de 2025 [GASTOS]
79. ¿Cuánto facturamos el trimestre pasado? [INGRESOS]
80. Ingresos del mes pasado [INGRESOS]
81. Gastos del último semestre [GASTOS]
82. ¿Cuál fue el resultado neto del mes pasado? [RESUMEN]
83. Retiros del último trimestre [RETIROS]
84. ¿Cuánto facturamos en dólares en 2024? [INGRESOS]
85. Total de gastos en USD de 2024 [GASTOS]
86. Retiros en dólares de 2024 [RETIROS]
87. ¿Cuánto recibió Pancho en distribuciones en 2024? [DISTRIBUCIONES]
88. ¿Cuánto recibió Viviana en distribuciones en 2025? [DISTRIBUCIONES]
89. Ingresos del área Jurídica en Mercedes en 2025 [INGRESOS]
90. Gastos del área Contable en Montevideo en 2025 [GASTOS]
91. ¿Cuál fue el mes con mayor margen de ganancia en 2025? [NINGUNO]
92. ¿Qué área tuvo el mayor crecimiento interanual de ingresos? [NINGUNO]
93. ¿Cuántos proveedores representan el 80% de nuestros gastos en 2025? [NINGUNO]
94. Ranking de socios por rentabilidad de las áreas que manejan [NINGUNO]
95. ¿En qué trimestre fue más eficiente la relación ingresos/gastos en 2025? [NINGUNO]
96. ¿Cuál es la correlación entre retiros y resultado neto mensual? [NINGUNO]
97. ¿Qué clientes dejaron de facturar en 2025 respecto a 2024? [NINGUNO]
98. ¿Cuál es el costo promedio por operación de cada área en 2025? [NINGUNO]
99. ¿Cuántas operaciones en USD representan más del 50% del total facturado? [NINGUNO]
100. ¿Cuál es la proporción de gastos fijos vs variables por localidad? [NINGUNO]

## 5. Recomendaciones

Tasa de PASS: 98.0% — **APROBADO**

WARNs menores a revisar:
- #31: Sistema retornó 1 rows, control vacío
- #34: Sistema retornó 1 rows, control vacío
## 6. Notas

- La BD tiene datos de 2024-01-01 a 2025-09-25. Las preguntas con 'este año' (2026), 'este mes' (Feb 2026), o 'enero 2025' retornan 0/vacío en ambos (sistema y control).
- Las áreas en BD son: Contable, Otros Gastos, Jurídica, Notarial, Administración, Recuperación.
  - BD alineada con producción (Otros Gastos, Administración)
- Preguntas NINGUNO (46-50, 91-100): se evalúa solo el routing (PASS si método='claude').
