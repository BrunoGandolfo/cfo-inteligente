from scripts.configurar_vanna_local import my_vanna as vn

vn.connect_to_postgres(
    host='localhost',
    dbname='cfo_inteligente',
    user='cfo_user',
    password='cfo_pass',
    port=5432
)

# DDL principal
vn.train(ddl="""
CREATE TABLE operaciones (
    id UUID PRIMARY KEY,
    tipo_operacion VARCHAR(20),
    fecha DATE,
    monto_original NUMERIC(15,2),
    moneda_original VARCHAR(3),
    tipo_cambio NUMERIC(10,4),
    monto_usd NUMERIC(15,2),
    monto_uyu NUMERIC(15,2),
    deleted_at TIMESTAMP
);
""")

# Entrenar pregunta específica
vn.train(
    question="¿Cuánto hemos facturado hasta la fecha?",
    sql="SELECT SUM(monto_usd) as total_facturado_usd FROM operaciones WHERE tipo_operacion = 'INGRESO' AND deleted_at IS NULL"
)

# Más ejemplos para que aprenda mejor
vn.train(
    question="¿Cuáles son los ingresos totales?",
    sql="SELECT SUM(monto_usd) FROM operaciones WHERE tipo_operacion = 'INGRESO' AND deleted_at IS NULL"
)

vn.train(
    question="¿Cuánto facturamos?",
    sql="SELECT SUM(monto_usd) FROM operaciones WHERE tipo_operacion = 'INGRESO' AND deleted_at IS NULL"
)

vn.train(
    question="Total de ventas",
    sql="SELECT SUM(monto_usd) FROM operaciones WHERE tipo_operacion = 'INGRESO' AND deleted_at IS NULL"
)

def train_rentabilidad_queries():
    queries = [
        (
            "Rentabilidad mensual básica",
            """
            SELECT
                (
                    (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
                   - SUM(CASE WHEN o.tipo_operacion = 'GASTO'   THEN o.monto_uyu ELSE 0 END))
                    / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
                ) * 100 AS rentabilidad
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion IN ('INGRESO','GASTO')
              AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
            """
        ),
        (
            "Rentabilidad por área",
            """
            SELECT
                a.nombre AS area,
                (
                    (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
                   - SUM(CASE WHEN o.tipo_operacion = 'GASTO'   THEN o.monto_uyu ELSE 0 END))
                    / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
                ) * 100 AS rentabilidad
            FROM operaciones o
            JOIN areas a ON a.id = o.area_id
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion IN ('INGRESO','GASTO')
              AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
            GROUP BY a.nombre
            ORDER BY rentabilidad DESC
            """
        ),
        (
            "Rentabilidad por localidad",
            """
            SELECT
                o.localidad,
                (
                    (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
                   - SUM(CASE WHEN o.tipo_operacion = 'GASTO'   THEN o.monto_uyu ELSE 0 END))
                    / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
                ) * 100 AS rentabilidad
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion IN ('INGRESO','GASTO')
              AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
            GROUP BY o.localidad
            ORDER BY rentabilidad DESC
            """
        ),
        (
            "Rentabilidad trimestral",
            """
            SELECT
                DATE_TRUNC('quarter', o.fecha) AS trimestre,
                (
                    (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
                   - SUM(CASE WHEN o.tipo_operacion = 'GASTO'   THEN o.monto_uyu ELSE 0 END))
                    / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
                ) * 100 AS rentabilidad
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion IN ('INGRESO','GASTO')
            GROUP BY 1
            ORDER BY 1
            """
        ),
        (
            "Comparación año anterior",
            """
            SELECT
                EXTRACT(YEAR FROM o.fecha)::int AS anio,
                (
                    (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
                   - SUM(CASE WHEN o.tipo_operacion = 'GASTO'   THEN o.monto_uyu ELSE 0 END))
                    / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
                ) * 100 AS rentabilidad
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion IN ('INGRESO','GASTO')
              AND o.fecha >= DATE_TRUNC('year', CURRENT_DATE) - INTERVAL '1 year'
            GROUP BY 1
            ORDER BY 1
            """
        ),
        (
            "Ranking de áreas por rentabilidad",
            """
            SELECT
                a.nombre AS area,
                (
                    (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
                   - SUM(CASE WHEN o.tipo_operacion = 'GASTO'   THEN o.monto_uyu ELSE 0 END))
                    / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
                ) * 100 AS rentabilidad
            FROM operaciones o
            JOIN areas a ON a.id = o.area_id
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion IN ('INGRESO','GASTO')
              AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
            GROUP BY a.nombre
            ORDER BY rentabilidad DESC NULLS LAST
            LIMIT 10
            """
        ),
        (
            "Evolución mensual de rentabilidad",
            """
            SELECT
                DATE_TRUNC('month', o.fecha) AS mes,
                (
                    (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
                   - SUM(CASE WHEN o.tipo_operacion = 'GASTO'   THEN o.monto_uyu ELSE 0 END))
                    / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
                ) * 100 AS rentabilidad
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion IN ('INGRESO','GASTO')
              AND o.fecha >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '11 months'
            GROUP BY 1
            ORDER BY 1
            """
        ),
        (
            "Rentabilidad Mercedes vs Montevideo",
            """
            SELECT
                o.localidad,
                (
                    (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
                   - SUM(CASE WHEN o.tipo_operacion = 'GASTO'   THEN o.monto_uyu ELSE 0 END))
                    / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
                ) * 100 AS rentabilidad
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion IN ('INGRESO','GASTO')
              AND o.localidad IN ('MONTEVIDEO','MERCEDES')
              AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
            GROUP BY o.localidad
            ORDER BY o.localidad
            """
        ),
        (
            "Área más rentable del mes",
            """
            SELECT
                a.nombre AS area,
                (
                    (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
                   - SUM(CASE WHEN o.tipo_operacion = 'GASTO'   THEN o.monto_uyu ELSE 0 END))
                    / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
                ) * 100 AS rentabilidad
            FROM operaciones o
            JOIN areas a ON a.id = o.area_id
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion IN ('INGRESO','GASTO')
              AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
            GROUP BY a.nombre
            ORDER BY rentabilidad DESC NULLS LAST
            LIMIT 1
            """
        ),
        (
            "Área menos rentable del mes",
            """
            SELECT
                a.nombre AS area,
                (
                    (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
                   - SUM(CASE WHEN o.tipo_operacion = 'GASTO'   THEN o.monto_uyu ELSE 0 END))
                    / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
                ) * 100 AS rentabilidad
            FROM operaciones o
            JOIN areas a ON a.id = o.area_id
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion IN ('INGRESO','GASTO')
              AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
            GROUP BY a.nombre
            ORDER BY rentabilidad ASC NULLS LAST
            LIMIT 1
            """
        ),
        (
            "Rentabilidad del año",
            """
            SELECT
                (
                    (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
                   - SUM(CASE WHEN o.tipo_operacion = 'GASTO'   THEN o.monto_uyu ELSE 0 END))
                    / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
                ) * 100 AS rentabilidad
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion IN ('INGRESO','GASTO')
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
            """
        ),
        (
            "Rentabilidad promedio últimos 3 meses",
            """
            WITH mensual AS (
                SELECT
                    DATE_TRUNC('month', o.fecha) AS mes,
                    (
                        (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
                       - SUM(CASE WHEN o.tipo_operacion = 'GASTO'   THEN o.monto_uyu ELSE 0 END))
                        / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
                    ) * 100 AS rentabilidad
                FROM operaciones o
                WHERE o.deleted_at IS NULL
                  AND o.tipo_operacion IN ('INGRESO','GASTO')
                  AND o.fecha >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '2 months'
                GROUP BY 1
            )
            SELECT AVG(rentabilidad) AS rentabilidad_promedio_3m
            FROM mensual
            """
        ),
        (
            "Tendencia de rentabilidad",
            """
            WITH mensual AS (
                SELECT
                    DATE_TRUNC('month', o.fecha) AS mes,
                    (
                        (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
                       - SUM(CASE WHEN o.tipo_operacion = 'GASTO'   THEN o.monto_uyu ELSE 0 END))
                        / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
                    ) * 100 AS rentabilidad
                FROM operaciones o
                WHERE o.deleted_at IS NULL
                  AND o.tipo_operacion IN ('INGRESO','GASTO')
                  AND o.fecha >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '2 months'
                GROUP BY 1
            )
            SELECT
                (SELECT rentabilidad FROM mensual ORDER BY mes DESC LIMIT 1) AS rentabilidad_ultima,
                (SELECT rentabilidad FROM mensual ORDER BY mes DESC OFFSET 1 LIMIT 1) AS rentabilidad_anterior,
                ((SELECT rentabilidad FROM mensual ORDER BY mes DESC LIMIT 1)
               - (SELECT rentabilidad FROM mensual ORDER BY mes DESC OFFSET 1 LIMIT 1)) AS variacion_pp
            """
        ),
        (
            "Rentabilidad por socio (distribuciones)",
            """
            WITH utilidad_mes AS (
                SELECT
                    (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
                   - SUM(CASE WHEN o.tipo_operacion = 'GASTO'   THEN o.monto_uyu ELSE 0 END)) AS utilidad
                FROM operaciones o
                WHERE o.deleted_at IS NULL
                  AND o.tipo_operacion IN ('INGRESO','GASTO')
                  AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
            )
            SELECT
                s.nombre AS socio,
                (u.utilidad * (s.porcentaje_participacion / 100.0)) AS utilidad_asignada
            FROM socios s
            CROSS JOIN utilidad_mes u
            ORDER BY utilidad_asignada DESC
            """
        ),
        (
            "Rentabilidad sin gastos generales",
            """
            SELECT
                (
                    (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
                   - SUM(CASE WHEN o.tipo_operacion = 'GASTO' AND COALESCE(a.nombre,'') <> 'Gastos Generales' THEN o.monto_uyu ELSE 0 END))
                    / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
                ) * 100 AS rentabilidad_sin_gg
            FROM operaciones o
            LEFT JOIN areas a ON a.id = o.area_id
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion IN ('INGRESO','GASTO')
              AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
            """
        ),
        (
            "Proyección de rentabilidad",
            """
            WITH params AS (
                SELECT
                    SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos_mtd,
                    SUM(CASE WHEN o.tipo_operacion = 'GASTO'   THEN o.monto_uyu ELSE 0 END) AS gastos_mtd,
                    EXTRACT(DAY FROM CURRENT_DATE)::numeric AS dia,
                    EXTRACT(DAY FROM (DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month - 1 day'))::numeric AS dias_mes
                FROM operaciones o
                WHERE o.deleted_at IS NULL
                  AND o.tipo_operacion IN ('INGRESO','GASTO')
                  AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
            )
            SELECT
                (
                    ((ingresos_mtd / NULLIF(dia,0) * dias_mes) - (gastos_mtd / NULLIF(dia,0) * dias_mes))
                    / NULLIF((ingresos_mtd / NULLIF(dia,0) * dias_mes), 0)
                ) * 100 AS rentabilidad_proyectada
            FROM params
            """
        ),
        (
            "Mejor mes de rentabilidad",
            """
            WITH mensual AS (
                SELECT
                    DATE_TRUNC('month', o.fecha) AS mes,
                    (
                        (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
                       - SUM(CASE WHEN o.tipo_operacion = 'GASTO'   THEN o.monto_uyu ELSE 0 END))
                        / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
                    ) * 100 AS rentabilidad
                FROM operaciones o
                WHERE o.deleted_at IS NULL
                  AND o.tipo_operacion IN ('INGRESO','GASTO')
                GROUP BY 1
            )
            SELECT mes, rentabilidad
            FROM mensual
            ORDER BY rentabilidad DESC NULLS LAST
            LIMIT 1
            """
        ),
        (
            "Peor mes de rentabilidad",
            """
            WITH mensual AS (
                SELECT
                    DATE_TRUNC('month', o.fecha) AS mes,
                    (
                        (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
                       - SUM(CASE WHEN o.tipo_operacion = 'GASTO'   THEN o.monto_uyu ELSE 0 END))
                        / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
                    ) * 100 AS rentabilidad
                FROM operaciones o
                WHERE o.deleted_at IS NULL
                  AND o.tipo_operacion IN ('INGRESO','GASTO')
                GROUP BY 1
            )
            SELECT mes, rentabilidad
            FROM mensual
            ORDER BY rentabilidad ASC NULLS LAST
            LIMIT 1
            """
        ),
        (
            "Comparación trimestral Q1 vs Q2",
            """
            SELECT
                EXTRACT(QUARTER FROM o.fecha)::int AS trimestre,
                (
                    (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
                   - SUM(CASE WHEN o.tipo_operacion = 'GASTO'   THEN o.monto_uyu ELSE 0 END))
                    / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
                ) * 100 AS rentabilidad
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion IN ('INGRESO','GASTO')
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
              AND EXTRACT(QUARTER FROM o.fecha) IN (1,2)
            GROUP BY 1
            ORDER BY 1
            """
        ),
        (
            "Alertas de rentabilidad baja",
            """
            WITH mensual AS (
                SELECT
                    DATE_TRUNC('month', o.fecha) AS mes,
                    (
                        (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END)
                       - SUM(CASE WHEN o.tipo_operacion = 'GASTO'   THEN o.monto_uyu ELSE 0 END))
                        / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
                    ) * 100 AS rentabilidad
                FROM operaciones o
                WHERE o.deleted_at IS NULL
                  AND o.tipo_operacion IN ('INGRESO','GASTO')
                  AND o.fecha >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '11 months'
                GROUP BY 1
            )
            SELECT mes, rentabilidad
            FROM mensual
            WHERE rentabilidad < 10
            ORDER BY mes DESC
            """
        ),
    ]

    for question, sql in queries:
        vn.train(question=question, sql=sql)

# Entrenar queries de rentabilidad prioritarias
train_rentabilidad_queries()

print("Entrenamiento completado")
