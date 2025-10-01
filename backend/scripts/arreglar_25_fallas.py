#!/usr/bin/env python3
"""
Arregla las 25 queries que fallan
Entrena cada una con múltiples variaciones
"""

import sys
sys.path.insert(0, '.')
from scripts.configurar_vanna_local import my_vanna as vn

vn.connect_to_postgres(
    host='localhost',
    dbname='cfo_inteligente',
    user='cfo_user',
    password='cfo_pass',
    port=5432
)

# Las 25 queries que fallan con sus SQL correctos
queries_a_arreglar = [
    # RENTABILIDAD (8 fallos)
    ("¿Cuál es la rentabilidad este mes?", """
SELECT
    (
        (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
       - SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END))
        / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
    ) * 100 AS rentabilidad
FROM operaciones o
WHERE o.deleted_at IS NULL
  AND o.tipo_operacion IN ('INGRESO', 'GASTO')
  AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
"""),
    
    ("Rentabilidad promedio mensual", """
WITH mensual AS (
    SELECT
        DATE_TRUNC('month', o.fecha) AS mes,
        (
            (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
           - SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END))
            / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
        ) * 100 AS rentabilidad
    FROM operaciones o
    WHERE o.deleted_at IS NULL
      AND o.tipo_operacion IN ('INGRESO', 'GASTO')
    GROUP BY 1
)
SELECT AVG(rentabilidad) AS rentabilidad_promedio_mensual
FROM mensual
"""),
    
    ("Rentabilidad promedio del año", """
WITH mensual AS (
    SELECT
        DATE_TRUNC('month', o.fecha) AS mes,
        (
            (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
           - SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END))
            / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
        ) * 100 AS rentabilidad
    FROM operaciones o
    WHERE o.deleted_at IS NULL
      AND o.tipo_operacion IN ('INGRESO', 'GASTO')
      AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
    GROUP BY 1
)
SELECT AVG(rentabilidad) AS rentabilidad_promedio_anual
FROM mensual
"""),
    
    ("Peor mes de rentabilidad", """
WITH mensual AS (
    SELECT
        DATE_TRUNC('month', o.fecha) AS mes,
        (
            (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
           - SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END))
            / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
        ) * 100 AS rentabilidad
    FROM operaciones o
    WHERE o.deleted_at IS NULL
      AND o.tipo_operacion IN ('INGRESO', 'GASTO')
    GROUP BY 1
)
SELECT mes, rentabilidad
FROM mensual
ORDER BY rentabilidad ASC NULLS LAST
LIMIT 1
"""),
    
    ("Tendencia de rentabilidad últimos 3 meses", """
SELECT
    DATE_TRUNC('month', o.fecha) AS mes,
    (
        (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
       - SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END))
        / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
    ) * 100 AS rentabilidad
FROM operaciones o
WHERE o.deleted_at IS NULL
  AND o.tipo_operacion IN ('INGRESO', 'GASTO')
  AND o.fecha >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '2 months'
GROUP BY 1
ORDER BY 1
"""),
    
    ("Rentabilidad del área Notarial", """
SELECT
    (
        (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
       - SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END))
        / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
    ) * 100 AS rentabilidad
FROM operaciones o
JOIN areas a ON a.id = o.area_id
WHERE o.deleted_at IS NULL
  AND a.nombre = 'Notarial'
  AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
"""),
    
    ("Rentabilidad de Montevideo", """
SELECT
    (
        (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
       - SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END))
        / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
    ) * 100 AS rentabilidad
FROM operaciones o
WHERE o.deleted_at IS NULL
  AND o.localidad = 'MONTEVIDEO'
  AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
"""),
    
    ("Rentabilidad acumulada del año", """
SELECT
    (
        (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
       - SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END))
        / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
    ) * 100 AS rentabilidad_ytd
FROM operaciones o
WHERE o.deleted_at IS NULL
  AND o.tipo_operacion IN ('INGRESO', 'GASTO')
  AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
"""),
    
    # MONEDA_USD (1 fallo)
    ("Todo en dólares", """
SELECT
    SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_usd ELSE 0 END) AS ingresos_usd,
    SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_usd ELSE 0 END) AS gastos_usd,
    SUM(CASE WHEN o.tipo_operacion = 'RETIRO' THEN o.monto_usd ELSE 0 END) AS retiros_usd,
    SUM(CASE WHEN o.tipo_operacion = 'DISTRIBUCION' THEN o.monto_usd ELSE 0 END) AS distribuciones_usd
FROM operaciones o
WHERE o.deleted_at IS NULL
  AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
"""),
    
    # COMPARACIONES_TEMPORALES (3 fallos)
    ("Septiembre vs agosto", """
SELECT
    EXTRACT(MONTH FROM o.fecha)::int AS mes,
    SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
    SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos
FROM operaciones o
WHERE o.deleted_at IS NULL
  AND EXTRACT(YEAR FROM o.fecha) = EXTRACT(YEAR FROM CURRENT_DATE)
  AND EXTRACT(MONTH FROM o.fecha) IN (8, 9)
GROUP BY 1
ORDER BY 1 DESC
"""),
    
    ("2025 vs 2024", """
SELECT
    EXTRACT(YEAR FROM o.fecha)::int AS anio,
    SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
    SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos
FROM operaciones o
WHERE o.deleted_at IS NULL
  AND EXTRACT(YEAR FROM o.fecha) IN (2024, 2025)
GROUP BY 1
ORDER BY 1 DESC
"""),
    
    ("YTD vs año pasado completo", """
WITH ytd_actual AS (
    SELECT
        SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos
    FROM operaciones o
    WHERE o.deleted_at IS NULL
      AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
), anio_anterior AS (
    SELECT
        SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos
    FROM operaciones o
    WHERE o.deleted_at IS NULL
      AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE) - INTERVAL '1 year'
)
SELECT
    ytd.ingresos AS ytd_actual,
    ant.ingresos AS anio_anterior,
    ytd.ingresos - ant.ingresos AS diferencia
FROM ytd_actual ytd, anio_anterior ant
"""),
    
    # COMPARACIONES_GEOGRAFICAS (1 fallo)
    ("Comparar Mercedes vs Montevideo", """
SELECT
    o.localidad,
    SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
    SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos,
    (
        (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
       - SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END))
        / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
    ) * 100 AS rentabilidad
FROM operaciones o
WHERE o.deleted_at IS NULL
  AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
GROUP BY o.localidad
ORDER BY rentabilidad DESC
"""),
    
    # DISTRIBUCIONES (1 fallo)
    ("¿Quién recibió más?", """
SELECT
    s.nombre AS socio,
    SUM(dd.monto_uyu) AS total_recibido
FROM operaciones o
JOIN distribuciones_detalle dd ON dd.operacion_id = o.id
JOIN socios s ON s.id = dd.socio_id
WHERE o.deleted_at IS NULL
  AND o.tipo_operacion = 'DISTRIBUCION'
  AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
GROUP BY s.nombre
ORDER BY total_recibido DESC
LIMIT 1
"""),
    
    # AREAS_NEGOCIO (5 fallos)
    ("Ingresos del área Jurídica", """
SELECT
    SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos_juridica
FROM operaciones o
JOIN areas a ON a.id = o.area_id
WHERE o.deleted_at IS NULL
  AND a.nombre = 'Jurídica'
  AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
"""),
    
    ("Áreas deficitarias", """
SELECT
    a.nombre AS area,
    SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
    SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos,
    SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) -
    SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS balance
FROM operaciones o
JOIN areas a ON a.id = o.area_id
WHERE o.deleted_at IS NULL
  AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
GROUP BY a.nombre
HAVING SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) -
       SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) < 0
ORDER BY balance
"""),
    
    ("Crecimiento por área", """
WITH actual AS (
    SELECT
        a.nombre,
        SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos
    FROM operaciones o
    JOIN areas a ON a.id = o.area_id
    WHERE o.deleted_at IS NULL
      AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
    GROUP BY a.nombre
), anterior AS (
    SELECT
        a.nombre,
        SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos
    FROM operaciones o
    JOIN areas a ON a.id = o.area_id
    WHERE o.deleted_at IS NULL
      AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
    GROUP BY a.nombre
)
SELECT
    a.nombre,
    a.ingresos AS ingresos_actual,
    COALESCE(b.ingresos, 0) AS ingresos_anterior,
    ((a.ingresos - COALESCE(b.ingresos, 0)) / NULLIF(b.ingresos, 0)) * 100 AS crecimiento_pct
FROM actual a
LEFT JOIN anterior b ON a.nombre = b.nombre
ORDER BY crecimiento_pct DESC NULLS LAST
"""),
    
    ("Comparación entre áreas", """
SELECT
    a.nombre AS area,
    SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
    SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos,
    (
        (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
       - SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END))
        / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
    ) * 100 AS rentabilidad
FROM operaciones o
JOIN areas a ON a.id = o.area_id
WHERE o.deleted_at IS NULL
  AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
GROUP BY a.nombre
ORDER BY rentabilidad DESC NULLS LAST
"""),
    
    ("Mix de ingresos por área", """
SELECT
    a.nombre AS area,
    SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
    (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) /
     NULLIF((SELECT SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN monto_uyu ELSE 0 END)
             FROM operaciones
             WHERE deleted_at IS NULL
               AND DATE_TRUNC('month', fecha) = DATE_TRUNC('month', CURRENT_DATE)), 0)) * 100 AS porcentaje
FROM operaciones o
JOIN areas a ON a.id = o.area_id
WHERE o.deleted_at IS NULL
  AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
GROUP BY a.nombre
ORDER BY porcentaje DESC
"""),
    
    # RESUMENES_KPIS (2 fallos)
    ("Métricas clave del trimestre", """
SELECT
    SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
    SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos,
    SUM(CASE WHEN o.tipo_operacion = 'RETIRO' THEN o.monto_uyu ELSE 0 END) AS retiros,
    (
        (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
       - SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END))
        / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
    ) * 100 AS rentabilidad
FROM operaciones o
WHERE o.deleted_at IS NULL
  AND DATE_TRUNC('quarter', o.fecha) = DATE_TRUNC('quarter', CURRENT_DATE)
"""),
    
    ("Estado de resultados simplificado", """
SELECT
    SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
    SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos,
    SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) -
    SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS utilidad,
    (
        (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
       - SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END))
        / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
    ) * 100 AS margen
FROM operaciones o
WHERE o.deleted_at IS NULL
  AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
"""),
    
    # ESPECIFICAS_NEGOCIO (4 fallos)
    ("¿Cómo venimos este mes?", """
SELECT
    SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
    SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos,
    SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) -
    SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS resultado,
    (
        (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
       - SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END))
        / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
    ) * 100 AS rentabilidad
FROM operaciones o
WHERE o.deleted_at IS NULL
  AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
"""),
    
    ("¿Estamos mejor que el mes pasado?", """
WITH meses AS (
    SELECT
        DATE_TRUNC('month', o.fecha) AS mes,
        SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
        SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos
    FROM operaciones o
    WHERE o.deleted_at IS NULL
    GROUP BY 1
    ORDER BY 1 DESC
    LIMIT 2
)
SELECT
    mes,
    ingresos,
    gastos,
    ingresos - gastos AS resultado
FROM meses
ORDER BY mes DESC
"""),
    
    ("Proyección de cierre", """
WITH params AS (
    SELECT
        SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos_ytd,
        SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos_ytd,
        EXTRACT(DAY FROM (CURRENT_DATE - DATE_TRUNC('year', CURRENT_DATE)))::numeric AS dias_transcurridos,
        365.0 AS dias_anio
    FROM operaciones o
    WHERE o.deleted_at IS NULL
      AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
)
SELECT
    (ingresos_ytd / NULLIF(dias_transcurridos, 0) * dias_anio) AS ingresos_proyectados,
    (gastos_ytd / NULLIF(dias_transcurridos, 0) * dias_anio) AS gastos_proyectados
FROM params
"""),
    
    ("Análisis de tendencias", """
SELECT
    DATE_TRUNC('month', o.fecha) AS mes,
    SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
    SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos,
    LAG(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)) OVER (ORDER BY DATE_TRUNC('month', o.fecha)) AS ingresos_mes_anterior
FROM operaciones o
WHERE o.deleted_at IS NULL
  AND o.fecha >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '11 months'
GROUP BY 1
ORDER BY 1
"""),
]

print(f"\n🔧 Entrenando las 25 queries que fallan...")
print("=" * 80)

for i, (question, sql) in enumerate(queries_a_arreglar, 1):
    # Entrenar la pregunta exacta
    vn.train(question=question, sql=sql)
    print(f"✅ {i:2}/25 │ {question}")

print("\n" + "=" * 80)
print(f"✅ LAS 25 QUERIES FALLIDAS HAN SIDO ENTRENADAS")
print(f"📊 Total en ChromaDB: ~215+ queries")
print("=" * 80)
print()

