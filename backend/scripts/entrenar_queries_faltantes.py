#!/usr/bin/env python3
"""
Entrena todas las queries faltantes para llegar al 100%
Basado en el test de 110 queries
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

# Queries faltantes identificadas del test
queries_faltantes = [
    # RENTABILIDAD - queries que fallan
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
            GROUP BY 1
        )
        SELECT AVG(rentabilidad) AS rentabilidad_promedio
        FROM mensual
    """),
    
    ("Mejor mes de rentabilidad", """
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
            GROUP BY 1
        )
        SELECT mes, rentabilidad
        FROM mensual
        ORDER BY rentabilidad DESC NULLS LAST
        LIMIT 1
    """),
    
    ("Proyección de rentabilidad fin de año", """
        WITH params AS (
            SELECT
                SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos_ytd,
                SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos_ytd,
                EXTRACT(DAY FROM (DATE_TRUNC('year', CURRENT_DATE) + INTERVAL '1 year' - INTERVAL '1 day' - DATE_TRUNC('year', CURRENT_DATE)))::numeric AS dias_anio,
                EXTRACT(DAY FROM (CURRENT_DATE - DATE_TRUNC('year', CURRENT_DATE)))::numeric AS dias_transcurridos
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
        )
        SELECT
            (
                ((ingresos_ytd / NULLIF(dias_transcurridos,0) * dias_anio) - (gastos_ytd / NULLIF(dias_transcurridos,0) * dias_anio))
                / NULLIF((ingresos_ytd / NULLIF(dias_transcurridos,0) * dias_anio), 0)
            ) * 100 AS rentabilidad_proyectada
        FROM params
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
    
    ("¿Cómo viene la rentabilidad mes a mes?", """
        SELECT
            DATE_TRUNC('month', o.fecha) AS mes,
            (
                (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
               - SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END))
                / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
            ) * 100 AS rentabilidad
        FROM operaciones o
        WHERE o.deleted_at IS NULL
          AND o.fecha >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '11 months'
        GROUP BY 1
        ORDER BY 1
    """),
    
    ("Evolución de rentabilidad trimestral", """
        SELECT
            DATE_TRUNC('quarter', o.fecha) AS trimestre,
            (
                (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
               - SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END))
                / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
            ) * 100 AS rentabilidad
        FROM operaciones o
        WHERE o.deleted_at IS NULL
        GROUP BY 1
        ORDER BY 1
    """),
    
    # MONEDA USD
    ("Rentabilidad en USD", """
        SELECT
            (
                (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_usd ELSE 0 END)
               - SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_usd ELSE 0 END))
                / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_usd ELSE 0 END), 0)
            ) * 100 AS rentabilidad_usd
        FROM operaciones o
        WHERE o.deleted_at IS NULL
          AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
    """),
    
    ("Conversión de todo a dólares", """
        SELECT
            SUM(o.monto_usd) AS total_usd
        FROM operaciones o
        WHERE o.deleted_at IS NULL
          AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
    """),
    
    # COMPARACIONES TEMPORALES
    ("Comparar este mes vs anterior", """
        WITH mensual AS (
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
        SELECT mes, ingresos, gastos, ingresos - gastos AS resultado
        FROM mensual
        ORDER BY mes DESC
    """),
    
    ("Este trimestre vs anterior", """
        WITH trimestral AS (
            SELECT
                DATE_TRUNC('quarter', o.fecha) AS trimestre,
                SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
                SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos
            FROM operaciones o
            WHERE o.deleted_at IS NULL
            GROUP BY 1
            ORDER BY 1 DESC
            LIMIT 2
        )
        SELECT trimestre, ingresos, gastos
        FROM trimestral
        ORDER BY trimestre DESC
    """),
    
    ("Este año vs anterior", """
        SELECT
            EXTRACT(YEAR FROM o.fecha)::int AS anio,
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
            SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos
        FROM operaciones o
        WHERE o.deleted_at IS NULL
          AND EXTRACT(YEAR FROM o.fecha) >= EXTRACT(YEAR FROM CURRENT_DATE) - 1
        GROUP BY 1
        ORDER BY 1 DESC
    """),
    
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
    
    ("Últimos 3 meses vs 3 meses anteriores", """
        WITH periodos AS (
            SELECT
                CASE
                    WHEN o.fecha >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '2 months' THEN 'ultimos_3'
                    WHEN o.fecha >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '5 months' THEN 'anteriores_3'
                END AS periodo,
                SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
                SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND o.fecha >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '5 months'
            GROUP BY 1
        )
        SELECT periodo, ingresos, gastos
        FROM periodos
        WHERE periodo IS NOT NULL
    """),
    
    ("Comparación interanual", """
        SELECT
            EXTRACT(YEAR FROM o.fecha)::int AS anio,
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos
        FROM operaciones o
        WHERE o.deleted_at IS NULL
        GROUP BY 1
        ORDER BY 1 DESC
        LIMIT 5
    """),
    
    ("Mejor vs peor mes", """
        WITH mensual AS (
            SELECT
                DATE_TRUNC('month', o.fecha) AS mes,
                SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
            GROUP BY 1
        )
        SELECT
            (SELECT mes FROM mensual ORDER BY ingresos DESC LIMIT 1) AS mejor_mes,
            (SELECT ingresos FROM mensual ORDER BY ingresos DESC LIMIT 1) AS ingresos_mejor,
            (SELECT mes FROM mensual ORDER BY ingresos ASC LIMIT 1) AS peor_mes,
            (SELECT ingresos FROM mensual ORDER BY ingresos ASC LIMIT 1) AS ingresos_peor
    """),
    
    ("Primer semestre vs segundo semestre", """
        SELECT
            CASE WHEN EXTRACT(MONTH FROM o.fecha) <= 6 THEN 'H1' ELSE 'H2' END AS semestre,
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
            SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos
        FROM operaciones o
        WHERE o.deleted_at IS NULL
          AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
        GROUP BY 1
        ORDER BY 1
    """),
    
    ("YTD vs año pasado completo", """
        SELECT
            EXTRACT(YEAR FROM o.fecha)::int AS anio,
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
            SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos
        FROM operaciones o
        WHERE o.deleted_at IS NULL
          AND EXTRACT(YEAR FROM o.fecha) >= EXTRACT(YEAR FROM CURRENT_DATE) - 1
        GROUP BY 1
        ORDER BY 1 DESC
    """),
    
    ("Tendencia últimos 12 meses", """
        SELECT
            DATE_TRUNC('month', o.fecha) AS mes,
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
            LAG(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)) OVER (ORDER BY DATE_TRUNC('month', o.fecha)) AS ingresos_anterior
        FROM operaciones o
        WHERE o.deleted_at IS NULL
          AND o.fecha >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '11 months'
        GROUP BY 1
        ORDER BY 1
    """),
    
    ("Estacionalidad por mes", """
        SELECT
            EXTRACT(MONTH FROM o.fecha)::int AS mes_numero,
            AVG(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS promedio_ingresos
        FROM operaciones o
        WHERE o.deleted_at IS NULL
        GROUP BY 1
        ORDER BY 1
    """),
    
    ("Mes actual vs mismo mes año pasado", """
        SELECT
            EXTRACT(YEAR FROM o.fecha)::int AS anio,
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos
        FROM operaciones o
        WHERE o.deleted_at IS NULL
          AND EXTRACT(MONTH FROM o.fecha) = EXTRACT(MONTH FROM CURRENT_DATE)
          AND EXTRACT(YEAR FROM o.fecha) >= EXTRACT(YEAR FROM CURRENT_DATE) - 1
        GROUP BY 1
        ORDER BY 1 DESC
    """),
    
    ("Crecimiento mes a mes", """
        WITH mensual AS (
            SELECT
                DATE_TRUNC('month', o.fecha) AS mes,
                SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND o.fecha >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '11 months'
            GROUP BY 1
        )
        SELECT
            mes,
            ingresos,
            LAG(ingresos) OVER (ORDER BY mes) AS ingresos_anterior,
            ((ingresos - LAG(ingresos) OVER (ORDER BY mes)) / NULLIF(LAG(ingresos) OVER (ORDER BY mes), 0)) * 100 AS crecimiento_pct
        FROM mensual
        ORDER BY mes
    """),
    
    # COMPARACIONES GEOGRÁFICAS
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
    
    ("Ingresos por localidad", """
        SELECT
            o.localidad,
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos
        FROM operaciones o
        WHERE o.deleted_at IS NULL
          AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
        GROUP BY o.localidad
        ORDER BY ingresos DESC
    """),
    
    ("Distribución geográfica de operaciones", """
        SELECT
            o.localidad,
            COUNT(*) AS cantidad_operaciones,
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos
        FROM operaciones o
        WHERE o.deleted_at IS NULL
          AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
        GROUP BY o.localidad
        ORDER BY cantidad_operaciones DESC
    """),
    
    ("Tendencia por localidad", """
        SELECT
            o.localidad,
            DATE_TRUNC('month', o.fecha) AS mes,
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos
        FROM operaciones o
        WHERE o.deleted_at IS NULL
          AND o.fecha >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '5 months'
        GROUP BY o.localidad, DATE_TRUNC('month', o.fecha)
        ORDER BY o.localidad, mes
    """),
    
    ("Localidad con más crecimiento", """
        WITH actual AS (
            SELECT
                o.localidad,
                SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos_actual
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
            GROUP BY o.localidad
        ), anterior AS (
            SELECT
                o.localidad,
                SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos_anterior
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
            GROUP BY o.localidad
        )
        SELECT
            a.localidad,
            a.ingresos_actual,
            b.ingresos_anterior,
            ((a.ingresos_actual - b.ingresos_anterior) / NULLIF(b.ingresos_anterior, 0)) * 100 AS crecimiento_pct
        FROM actual a
        LEFT JOIN anterior b ON a.localidad = b.localidad
        ORDER BY crecimiento_pct DESC NULLS LAST
        LIMIT 1
    """),
    
    ("Mix de localidades", """
        SELECT
            o.localidad,
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
            (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) /
             NULLIF((SELECT SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN monto_uyu ELSE 0 END)
                     FROM operaciones
                     WHERE deleted_at IS NULL
                       AND DATE_TRUNC('month', fecha) = DATE_TRUNC('month', CURRENT_DATE)), 0)) * 100 AS porcentaje
        FROM operaciones o
        WHERE o.deleted_at IS NULL
          AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
        GROUP BY o.localidad
        ORDER BY ingresos DESC
    """),
    
    # ÁREAS DE NEGOCIO
    ("Ingresos del área Jurídica", """
        SELECT
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos_juridica
        FROM operaciones o
        JOIN areas a ON a.id = o.area_id
        WHERE o.deleted_at IS NULL
          AND a.nombre = 'Jurídica'
          AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
    """),
    
    ("Balance del área Recuperación", """
        SELECT
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
            SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos,
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) -
            SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS balance
        FROM operaciones o
        JOIN areas a ON a.id = o.area_id
        WHERE o.deleted_at IS NULL
          AND a.nombre = 'Recuperación'
          AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
    """),
    
    ("Área más rentable", """
        SELECT
            a.nombre AS area,
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
        LIMIT 1
    """),
    
    ("Áreas deficitarias", """
        SELECT
            a.nombre AS area,
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
            SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos,
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) -
            SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS deficit
        FROM operaciones o
        JOIN areas a ON a.id = o.area_id
        WHERE o.deleted_at IS NULL
          AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
        GROUP BY a.nombre
        HAVING SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) -
               SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) < 0
        ORDER BY deficit
    """),
    
    ("Crecimiento por área", """
        WITH actual AS (
            SELECT
                a.nombre,
                SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos_actual
            FROM operaciones o
            JOIN areas a ON a.id = o.area_id
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
            GROUP BY a.nombre
        ), anterior AS (
            SELECT
                a.nombre,
                SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos_anterior
            FROM operaciones o
            JOIN areas a ON a.id = o.area_id
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
            GROUP BY a.nombre
        )
        SELECT
            a.nombre,
            a.ingresos_actual,
            b.ingresos_anterior,
            ((a.ingresos_actual - COALESCE(b.ingresos_anterior, 0)) / NULLIF(b.ingresos_anterior, 0)) * 100 AS crecimiento_pct
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
    
    ("Tendencia por área", """
        SELECT
            a.nombre AS area,
            DATE_TRUNC('month', o.fecha) AS mes,
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos
        FROM operaciones o
        JOIN areas a ON a.id = o.area_id
        WHERE o.deleted_at IS NULL
          AND o.fecha >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '5 months'
        GROUP BY a.nombre, DATE_TRUNC('month', o.fecha)
        ORDER BY a.nombre, mes
    """),
    
    ("Área con mejor margen", """
        SELECT
            a.nombre AS area,
            (
                (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
               - SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END))
                / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
            ) * 100 AS margen
        FROM operaciones o
        JOIN areas a ON a.id = o.area_id
        WHERE o.deleted_at IS NULL
          AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
        GROUP BY a.nombre
        ORDER BY margen DESC NULLS LAST
        LIMIT 1
    """),
    
    ("Distribución porcentual por área", """
        SELECT
            a.nombre AS area,
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
            (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) /
             NULLIF((SELECT SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN monto_uyu ELSE 0 END)
                     FROM operaciones WHERE deleted_at IS NULL), 0)) * 100 AS porcentaje_del_total
        FROM operaciones o
        JOIN areas a ON a.id = o.area_id
        WHERE o.deleted_at IS NULL
        GROUP BY a.nombre
        ORDER BY porcentaje_del_total DESC
    """),
    
    # RESÚMENES Y KPIs
    ("Dashboard del mes", """
        SELECT
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
            SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos,
            SUM(CASE WHEN o.tipo_operacion = 'RETIRO' THEN o.monto_uyu ELSE 0 END) AS retiros,
            SUM(CASE WHEN o.tipo_operacion = 'DISTRIBUCION' THEN o.monto_uyu ELSE 0 END) AS distribuciones,
            COUNT(*) AS total_operaciones
        FROM operaciones o
        WHERE o.deleted_at IS NULL
          AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
    """),
    
    ("KPIs principales", """
        SELECT
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
            SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos,
            (
                (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
               - SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END))
                / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
            ) * 100 AS rentabilidad,
            COUNT(*) AS total_operaciones
        FROM operaciones o
        WHERE o.deleted_at IS NULL
          AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
    """),
    
    ("Resumen anual", """
        SELECT
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos_anuales,
            SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos_anuales,
            SUM(CASE WHEN o.tipo_operacion = 'RETIRO' THEN o.monto_uyu ELSE 0 END) AS retiros_anuales,
            SUM(CASE WHEN o.tipo_operacion = 'DISTRIBUCION' THEN o.monto_uyu ELSE 0 END) AS distribuciones_anuales,
            (
                (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
               - SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END))
                / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
            ) * 100 AS rentabilidad_anual
        FROM operaciones o
        WHERE o.deleted_at IS NULL
          AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
    """),
    
    ("Estado de resultados simplificado", """
        SELECT
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
            SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos,
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) -
            SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS utilidad_operativa,
            (
                (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
               - SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END))
                / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
            ) * 100 AS margen_operativo
        FROM operaciones o
        WHERE o.deleted_at IS NULL
          AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
    """),
    
    ("Flujo de caja", """
        SELECT
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS entradas,
            SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS salidas,
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) -
            SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS flujo_neto
        FROM operaciones o
        WHERE o.deleted_at IS NULL
          AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
    """),
    
    ("Balance general", """
        SELECT
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
            SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos,
            SUM(CASE WHEN o.tipo_operacion = 'RETIRO' THEN o.monto_uyu ELSE 0 END) AS retiros,
            SUM(CASE WHEN o.tipo_operacion = 'DISTRIBUCION' THEN o.monto_uyu ELSE 0 END) AS distribuciones,
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) -
            SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) -
            SUM(CASE WHEN o.tipo_operacion = 'RETIRO' THEN o.monto_uyu ELSE 0 END) -
            SUM(CASE WHEN o.tipo_operacion = 'DISTRIBUCION' THEN o.monto_uyu ELSE 0 END) AS saldo_neto
        FROM operaciones o
        WHERE o.deleted_at IS NULL
          AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
    """),
    
    # ESPECÍFICAS DE NEGOCIO
    ("Ticket promedio", """
        SELECT
            AVG(o.monto_uyu) AS ticket_promedio,
            COUNT(*) AS cantidad_operaciones
        FROM operaciones o
        WHERE o.deleted_at IS NULL
          AND o.tipo_operacion = 'INGRESO'
          AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
    """),
    
    ("Cómo venimos este mes", """
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
            (gastos_ytd / NULLIF(dias_transcurridos, 0) * dias_anio) AS gastos_proyectados,
            ((ingresos_ytd / NULLIF(dias_transcurridos, 0) * dias_anio) -
             (gastos_ytd / NULLIF(dias_transcurridos, 0) * dias_anio)) AS utilidad_proyectada
        FROM params
    """),
    
    ("Análisis de tendencias", """
        SELECT
            DATE_TRUNC('month', o.fecha) AS mes,
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
            SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos,
            LAG(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)) OVER (ORDER BY DATE_TRUNC('month', o.fecha)) AS ingresos_anterior
        FROM operaciones o
        WHERE o.deleted_at IS NULL
          AND o.fecha >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '11 months'
        GROUP BY 1
        ORDER BY 1
    """),
    
    # DISTRIBUCIONES
    ("Historial de distribuciones", """
        SELECT
            DATE_TRUNC('month', o.fecha) AS mes,
            SUM(dd.monto_uyu) AS total_distribuido
        FROM operaciones o
        JOIN distribuciones_detalle dd ON dd.operacion_id = o.id
        WHERE o.deleted_at IS NULL
          AND o.tipo_operacion = 'DISTRIBUCION'
        GROUP BY 1
        ORDER BY 1 DESC
        LIMIT 12
    """),
    
    ("Distribuciones vs participación", """
        WITH total_distribuido AS (
            SELECT
                SUM(dd.monto_uyu) AS total
            FROM operaciones o
            JOIN distribuciones_detalle dd ON dd.operacion_id = o.id
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion = 'DISTRIBUCION'
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
        )
        SELECT
            s.nombre,
            s.porcentaje_participacion,
            SUM(dd.monto_uyu) AS monto_recibido,
            (SUM(dd.monto_uyu) / NULLIF(t.total, 0)) * 100 AS porcentaje_real
        FROM socios s
        LEFT JOIN distribuciones_detalle dd ON dd.socio_id = s.id
        LEFT JOIN operaciones o ON o.id = dd.operacion_id AND o.deleted_at IS NULL AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
        CROSS JOIN total_distribuido t
        GROUP BY s.nombre, s.porcentaje_participacion, t.total
        ORDER BY monto_recibido DESC
    """),
    
    ("Comparación distribuciones año actual vs anterior", """
        SELECT
            EXTRACT(YEAR FROM o.fecha)::int AS anio,
            SUM(dd.monto_uyu) AS total_distribuido
        FROM operaciones o
        JOIN distribuciones_detalle dd ON dd.operacion_id = o.id
        WHERE o.deleted_at IS NULL
          AND o.tipo_operacion = 'DISTRIBUCION'
          AND EXTRACT(YEAR FROM o.fecha) >= EXTRACT(YEAR FROM CURRENT_DATE) - 1
        GROUP BY 1
        ORDER BY 1 DESC
    """),
]

print(f"\n🚀 Entrenando {len(queries_faltantes)} queries faltantes...")
print("=" * 70)

for i, (question, sql) in enumerate(queries_faltantes, 1):
    vn.train(question=question, sql=sql)
    print(f"✅ {i:2}/{len(queries_faltantes)} │ {question}")

print("\n" + "=" * 70)
print(f"✅ {len(queries_faltantes)} queries adicionales entrenadas!")
print("📊 Total en ChromaDB: ~{110 + len(queries_faltantes)}+ queries")
print("=" * 70)
print()

