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

vn.train(ddl="""
CREATE TABLE socios (
    id UUID PRIMARY KEY,
    nombre VARCHAR(100),
    porcentaje_participacion NUMERIC(5,2)
);
""")

vn.train(ddl="""
CREATE TABLE distribuciones_detalle (
    id UUID PRIMARY KEY,
    operacion_id UUID REFERENCES operaciones(id),
    socio_id UUID REFERENCES socios(id),
    monto_uyu NUMERIC(15,2),
    monto_usd NUMERIC(15,2)
);
""")

vn.train(ddl="""
CREATE TABLE areas (
    id UUID PRIMARY KEY,
    nombre VARCHAR(100)
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

def train_distribuciones_queries():
    queries = [
        (
            "¿Cuánto recibió Bruno este año?",
            """
            SELECT
                COALESCE(SUM(dd.monto_uyu), 0) AS monto_uyu,
                COALESCE(SUM(dd.monto_usd), 0) AS monto_usd
            FROM operaciones o
            JOIN distribuciones_detalle dd ON dd.operacion_id = o.id
            JOIN socios s ON s.id = dd.socio_id
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion = 'DISTRIBUCION'
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
              AND s.nombre = 'Bruno'
            """
        ),
        (
            "Total de distribuciones por socio este mes",
            """
            SELECT
                s.nombre AS socio,
                SUM(dd.monto_uyu) AS monto_uyu,
                SUM(dd.monto_usd) AS monto_usd
            FROM operaciones o
            JOIN distribuciones_detalle dd ON dd.operacion_id = o.id
            JOIN socios s ON s.id = dd.socio_id
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion = 'DISTRIBUCION'
              AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
            GROUP BY s.nombre
            ORDER BY monto_uyu DESC
            """
        ),
        (
            "Distribuciones en USD vs UYU por socio",
            """
            SELECT
                s.nombre AS socio,
                SUM(dd.monto_uyu) AS total_uyu,
                SUM(dd.monto_usd) AS total_usd
            FROM operaciones o
            JOIN distribuciones_detalle dd ON dd.operacion_id = o.id
            JOIN socios s ON s.id = dd.socio_id
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion = 'DISTRIBUCION'
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
            GROUP BY s.nombre
            ORDER BY total_uyu DESC
            """
        ),
        (
            "¿Cuánto recibió cada socio este año?",
            """
            SELECT
                s.nombre AS socio,
                SUM(dd.monto_uyu) AS monto_uyu,
                SUM(dd.monto_usd) AS monto_usd
            FROM operaciones o
            JOIN distribuciones_detalle dd ON dd.operacion_id = o.id
            JOIN socios s ON s.id = dd.socio_id
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion = 'DISTRIBUCION'
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
            GROUP BY s.nombre
            ORDER BY monto_uyu DESC
            """
        ),
        (
            "Última distribución realizada",
            """
            WITH ultima AS (
                SELECT id, fecha
                FROM operaciones
                WHERE deleted_at IS NULL
                  AND tipo_operacion = 'DISTRIBUCION'
                ORDER BY fecha DESC
                LIMIT 1
            )
            SELECT
                u.id AS operacion_id,
                u.fecha,
                COALESCE(SUM(dd.monto_uyu), 0) AS total_uyu,
                COALESCE(SUM(dd.monto_usd), 0) AS total_usd
            FROM ultima u
            LEFT JOIN distribuciones_detalle dd ON dd.operacion_id = u.id
            GROUP BY u.id, u.fecha
            """
        ),
        (
            "Total distribuido este trimestre",
            """
            SELECT
                SUM(dd.monto_uyu) AS total_uyu,
                SUM(dd.monto_usd) AS total_usd
            FROM operaciones o
            JOIN distribuciones_detalle dd ON dd.operacion_id = o.id
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion = 'DISTRIBUCION'
              AND DATE_TRUNC('quarter', o.fecha) = DATE_TRUNC('quarter', CURRENT_DATE)
            """
        ),
        (
            "Ranking de socios por monto recibido",
            """
            SELECT
                s.nombre AS socio,
                SUM(dd.monto_uyu) AS monto_uyu,
                SUM(dd.monto_usd) AS monto_usd
            FROM operaciones o
            JOIN distribuciones_detalle dd ON dd.operacion_id = o.id
            JOIN socios s ON s.id = dd.socio_id
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion = 'DISTRIBUCION'
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
            GROUP BY s.nombre
            ORDER BY monto_uyu DESC
            """
        ),
        (
            "Distribuciones de Agustina en 2025",
            """
            SELECT
                DATE_TRUNC('month', o.fecha) AS mes,
                SUM(dd.monto_uyu) AS monto_uyu,
                SUM(dd.monto_usd) AS monto_usd
            FROM operaciones o
            JOIN distribuciones_detalle dd ON dd.operacion_id = o.id
            JOIN socios s ON s.id = dd.socio_id
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion = 'DISTRIBUCION'
              AND s.nombre = 'Agustina'
              AND EXTRACT(YEAR FROM o.fecha) = 2025
            GROUP BY 1
            ORDER BY 1
            """
        ),
        (
            "Porcentaje recibido por cada socio",
            """
            WITH total_anual AS (
                SELECT
                    SUM(dd.monto_uyu) AS total_uyu
                FROM operaciones o
                JOIN distribuciones_detalle dd ON dd.operacion_id = o.id
                WHERE o.deleted_at IS NULL
                  AND o.tipo_operacion = 'DISTRIBUCION'
                  AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
            )
            SELECT
                s.nombre AS socio,
                SUM(dd.monto_uyu) AS monto_uyu,
                CASE WHEN ta.total_uyu = 0 THEN 0
                     ELSE (SUM(dd.monto_uyu) / ta.total_uyu) * 100
                END AS porcentaje_uyu
            FROM operaciones o
            JOIN distribuciones_detalle dd ON dd.operacion_id = o.id
            JOIN socios s ON s.id = dd.socio_id
            CROSS JOIN total_anual ta
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion = 'DISTRIBUCION'
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
            GROUP BY s.nombre, ta.total_uyu
            ORDER BY porcentaje_uyu DESC
            """
        ),
        (
            "Distribuciones pendientes vs pagadas",
            """
            WITH base AS (
                SELECT
                    o.id,
                    o.fecha,
                    COUNT(dd.id) AS cantidad_detalles,
                    COALESCE(SUM(dd.monto_uyu), 0) AS total_uyu,
                    COALESCE(SUM(dd.monto_usd), 0) AS total_usd
                FROM operaciones o
                LEFT JOIN distribuciones_detalle dd ON dd.operacion_id = o.id
                WHERE o.deleted_at IS NULL
                  AND o.tipo_operacion = 'DISTRIBUCION'
                  AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
                GROUP BY o.id, o.fecha
            )
            SELECT
                CASE WHEN cantidad_detalles > 0 THEN 'PAGADA' ELSE 'PENDIENTE' END AS estado,
                COUNT(*) AS operaciones,
                SUM(total_uyu) AS total_uyu,
                SUM(total_usd) AS total_usd
            FROM base
            GROUP BY estado
            ORDER BY estado
            """
        ),
    ]

    for question, sql in queries:
        vn.train(question=question, sql=sql)

# Entrenar queries de distribuciones
train_distribuciones_queries()

def train_comparaciones_queries():
    queries = [
        (
            "Comparar ingresos de este mes vs mes anterior",
            """
            WITH mensual AS (
                SELECT
                    DATE_TRUNC('month', o.fecha) AS mes,
                    SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos
                FROM operaciones o
                WHERE o.deleted_at IS NULL
                GROUP BY 1
            )
            SELECT
                SUM(ingresos) FILTER (WHERE mes = DATE_TRUNC('month', CURRENT_DATE)) AS ingresos_mes,
                SUM(ingresos) FILTER (WHERE mes = DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month') AS ingresos_mes_anterior,
                COALESCE(SUM(ingresos) FILTER (WHERE mes = DATE_TRUNC('month', CURRENT_DATE)), 0)
              - COALESCE(SUM(ingresos) FILTER (WHERE mes = DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'), 0) AS variacion
            FROM mensual
            WHERE mes IN (DATE_TRUNC('month', CURRENT_DATE), DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month')
            """
        ),
        (
            "Comparar Mercedes vs Montevideo este año",
            """
            SELECT
                o.localidad,
                SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
              AND o.localidad IN ('MONTEVIDEO', 'MERCEDES')
            GROUP BY o.localidad
            ORDER BY o.localidad
            """
        ),
        (
            "Comparación Q1 2025 vs Q1 2024",
            """
            SELECT
                EXTRACT(YEAR FROM o.fecha)::int AS anio,
                SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND EXTRACT(QUARTER FROM o.fecha) = 1
              AND EXTRACT(YEAR FROM o.fecha) IN (2024, 2025)
            GROUP BY 1
            ORDER BY 1
            """
        ),
        (
            "Evolución mensual de gastos últimos 6 meses",
            """
            SELECT
                DATE_TRUNC('month', o.fecha) AS mes,
                SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND o.fecha >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '5 months'
            GROUP BY 1
            ORDER BY 1
            """
        ),
        (
            "Comparar rentabilidad de este año vs año pasado",
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
              AND EXTRACT(YEAR FROM o.fecha) IN (EXTRACT(YEAR FROM CURRENT_DATE), EXTRACT(YEAR FROM CURRENT_DATE) - 1)
            GROUP BY 1
            ORDER BY 1
            """
        ),
        (
            "Ingresos por área este mes vs mes anterior",
            """
            WITH por_area AS (
                SELECT
                    a.nombre AS area,
                    DATE_TRUNC('month', o.fecha) AS mes,
                    SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos
                FROM operaciones o
                JOIN areas a ON a.id = o.area_id
                WHERE o.deleted_at IS NULL
                GROUP BY a.nombre, DATE_TRUNC('month', o.fecha)
            )
            SELECT
                area,
                SUM(ingresos) FILTER (WHERE mes = DATE_TRUNC('month', CURRENT_DATE)) AS ingresos_mes,
                SUM(ingresos) FILTER (WHERE mes = DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month') AS ingresos_mes_anterior,
                COALESCE(SUM(ingresos) FILTER (WHERE mes = DATE_TRUNC('month', CURRENT_DATE)), 0)
              - COALESCE(SUM(ingresos) FILTER (WHERE mes = DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'), 0) AS variacion
            FROM por_area
            WHERE mes IN (DATE_TRUNC('month', CURRENT_DATE), DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month')
            GROUP BY area
            ORDER BY variacion DESC NULLS LAST
            """
        ),
        (
            "Gastos Mercedes vs Montevideo último trimestre",
            """
            SELECT
                o.localidad,
                SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('quarter', o.fecha) = DATE_TRUNC('quarter', CURRENT_DATE)
              AND o.localidad IN ('MONTEVIDEO', 'MERCEDES')
            GROUP BY o.localidad
            ORDER BY o.localidad
            """
        ),
        (
            "Tendencia de ingresos últimos 12 meses",
            """
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
                ingresos - COALESCE(LAG(ingresos) OVER (ORDER BY mes), 0) AS variacion
            FROM mensual
            ORDER BY mes
            """
        ),
        (
            "Comparar distribuciones Q2 vs Q1 2025",
            """
            SELECT
                EXTRACT(QUARTER FROM o.fecha)::int AS trimestre,
                SUM(dd.monto_uyu) AS total_uyu,
                SUM(dd.monto_usd) AS total_usd
            FROM operaciones o
            JOIN distribuciones_detalle dd ON dd.operacion_id = o.id
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion = 'DISTRIBUCION'
              AND EXTRACT(YEAR FROM o.fecha) = 2025
              AND EXTRACT(QUARTER FROM o.fecha) IN (1, 2)
            GROUP BY 1
            ORDER BY 1
            """
        ),
        (
            "Área con mayor crecimiento año a año",
            """
            WITH anual AS (
                SELECT
                    a.nombre AS area,
                    EXTRACT(YEAR FROM o.fecha)::int AS anio,
                    SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos
                FROM operaciones o
                JOIN areas a ON a.id = o.area_id
                WHERE o.deleted_at IS NULL
                GROUP BY a.nombre, EXTRACT(YEAR FROM o.fecha)
            ), yoy AS (
                SELECT
                    area,
                    anio,
                    ingresos,
                    LAG(ingresos) OVER (PARTITION BY area ORDER BY anio) AS ingresos_prev,
                    ingresos - COALESCE(LAG(ingresos) OVER (PARTITION BY area ORDER BY anio), 0) AS crecimiento
                FROM anual
            )
            SELECT area, anio, ingresos, ingresos_prev, crecimiento
            FROM yoy
            WHERE anio = EXTRACT(YEAR FROM CURRENT_DATE)
            ORDER BY crecimiento DESC NULLS LAST
            LIMIT 1
            """
        ),
        (
            "Comparación de retiros mes actual vs promedio",
            """
            WITH mensual AS (
                SELECT
                    DATE_TRUNC('month', o.fecha) AS mes,
                    SUM(CASE WHEN o.tipo_operacion = 'RETIRO' THEN o.monto_uyu ELSE 0 END) AS retiros
                FROM operaciones o
                WHERE o.deleted_at IS NULL
                  AND o.fecha >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '11 months'
                GROUP BY 1
            )
            SELECT
                SUM(retiros) FILTER (WHERE mes = DATE_TRUNC('month', CURRENT_DATE)) AS retiros_mes,
                AVG(retiros) AS promedio_12m,
                COALESCE(SUM(retiros) FILTER (WHERE mes = DATE_TRUNC('month', CURRENT_DATE)), 0) - AVG(retiros) AS diferencia
            FROM mensual
            """
        ),
        (
            "Evolución trimestral de rentabilidad",
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
              AND o.fecha >= DATE_TRUNC('year', CURRENT_DATE) - INTERVAL '2 years'
            GROUP BY 1
            ORDER BY 1
            """
        ),
        (
            "Mercedes vs Montevideo por área",
            """
            SELECT
                a.nombre AS area,
                o.localidad,
                SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos
            FROM operaciones o
            JOIN areas a ON a.id = o.area_id
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
              AND o.localidad IN ('MONTEVIDEO', 'MERCEDES')
            GROUP BY a.nombre, o.localidad
            ORDER BY a.nombre, o.localidad
            """
        ),
        (
            "Comparar gastos generales 2025 vs 2024",
            """
            SELECT
                EXTRACT(YEAR FROM o.fecha)::int AS anio,
                SUM(o.monto_uyu) AS gastos
            FROM operaciones o
            JOIN areas a ON a.id = o.area_id
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion = 'GASTO'
              AND a.nombre = 'Gastos Generales'
              AND EXTRACT(YEAR FROM o.fecha) IN (2024, 2025)
            GROUP BY 1
            ORDER BY 1
            """
        ),
        (
            "Mejor vs peor mes del año en ingresos",
            """
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
                (SELECT mes FROM mensual ORDER BY ingresos DESC NULLS LAST LIMIT 1)  AS mejor_mes,
                (SELECT ingresos FROM mensual ORDER BY ingresos DESC NULLS LAST LIMIT 1) AS ingresos_mejor_mes,
                (SELECT mes FROM mensual ORDER BY ingresos ASC  NULLS LAST LIMIT 1)  AS peor_mes,
                (SELECT ingresos FROM mensual ORDER BY ingresos ASC  NULLS LAST LIMIT 1) AS ingresos_peor_mes
            """
        ),
    ]

    for question, sql in queries:
        vn.train(question=question, sql=sql)

# Entrenar queries de comparaciones
train_comparaciones_queries()

def train_gastos_ingresos_queries():
    queries = [
        (
            "Total de ingresos este mes",
            """
            SELECT
                SUM(o.monto_uyu) AS total_ingresos_mes
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion = 'INGRESO'
              AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
            """
        ),
        (
            "Total de gastos este año",
            """
            SELECT
                SUM(o.monto_uyu) AS total_gastos_anio
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion = 'GASTO'
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
            """
        ),
        (
            "Ingresos por área este trimestre",
            """
            SELECT
                a.nombre AS area,
                SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos
            FROM operaciones o
            JOIN areas a ON a.id = o.area_id
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('quarter', o.fecha) = DATE_TRUNC('quarter', CURRENT_DATE)
            GROUP BY a.nombre
            ORDER BY ingresos DESC
            """
        ),
        (
            "Gastos por área este mes",
            """
            SELECT
                a.nombre AS area,
                SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos
            FROM operaciones o
            JOIN areas a ON a.id = o.area_id
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
            GROUP BY a.nombre
            ORDER BY gastos DESC
            """
        ),
        (
            "Mayor ingreso del mes",
            """
            SELECT
                o.id,
                o.fecha,
                o.monto_uyu AS monto
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion = 'INGRESO'
              AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
            ORDER BY o.monto_uyu DESC NULLS LAST
            LIMIT 1
            """
        ),
        (
            "Mayor gasto del año",
            """
            SELECT
                o.id,
                o.fecha,
                o.monto_uyu AS monto
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion = 'GASTO'
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
            ORDER BY o.monto_uyu DESC NULLS LAST
            LIMIT 1
            """
        ),
        (
            "Promedio de ingresos diarios este mes",
            """
            WITH diarios AS (
                SELECT
                    o.fecha::date AS dia,
                    SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos_dia
                FROM operaciones o
                WHERE o.deleted_at IS NULL
                  AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
                GROUP BY o.fecha::date
            )
            SELECT AVG(ingresos_dia) AS promedio_diario
            FROM diarios
            """
        ),
        (
            "Top 5 áreas por ingresos",
            """
            SELECT
                a.nombre AS area,
                SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos
            FROM operaciones o
            JOIN areas a ON a.id = o.area_id
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
            GROUP BY a.nombre
            ORDER BY ingresos DESC NULLS LAST
            LIMIT 5
            """
        ),
        (
            "Top 5 áreas por gastos",
            """
            SELECT
                a.nombre AS area,
                SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos
            FROM operaciones o
            JOIN areas a ON a.id = o.area_id
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
            GROUP BY a.nombre
            ORDER BY gastos DESC NULLS LAST
            LIMIT 5
            """
        ),
        (
            "Ingresos en USD vs UYU este mes",
            """
            SELECT
                o.moneda_original,
                SUM(o.monto_uyu) AS total_uyu,
                SUM(o.monto_usd) AS total_usd
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion = 'INGRESO'
              AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
            GROUP BY o.moneda_original
            ORDER BY o.moneda_original
            """
        ),
        (
            "Gastos en USD vs UYU este año",
            """
            SELECT
                o.moneda_original,
                SUM(o.monto_uyu) AS total_uyu,
                SUM(o.monto_usd) AS total_usd
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion = 'GASTO'
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
            GROUP BY o.moneda_original
            ORDER BY o.moneda_original
            """
        ),
        (
            "Ingresos por localidad este trimestre",
            """
            SELECT
                o.localidad,
                SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('quarter', o.fecha) = DATE_TRUNC('quarter', CURRENT_DATE)
            GROUP BY o.localidad
            ORDER BY ingresos DESC NULLS LAST
            """
        ),
        (
            "Gastos operativos vs gastos generales",
            """
            SELECT
                CASE WHEN COALESCE(a.nombre,'') = 'Gastos Generales' THEN 'GASTOS GENERALES' ELSE 'OPERATIVOS' END AS tipo_gasto,
                SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END) AS total
            FROM operaciones o
            LEFT JOIN areas a ON a.id = o.area_id
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
            GROUP BY 1
            ORDER BY 1
            """
        ),
        (
            "Ticket promedio de ingresos",
            """
            SELECT
                AVG(o.monto_uyu) AS ticket_promedio,
                COUNT(*) AS cantidad_ingresos
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion = 'INGRESO'
              AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
            """
        ),
        (
            "Relación gastos/ingresos por área",
            """
            SELECT
                a.nombre AS area,
                SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.monto_uyu ELSE 0 END)
                / NULLIF(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.monto_uyu ELSE 0 END), 0) AS relacion_gastos_ingresos
            FROM operaciones o
            JOIN areas a ON a.id = o.area_id
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
            GROUP BY a.nombre
            ORDER BY relacion_gastos_ingresos DESC NULLS LAST
            """
        ),
    ]

    for question, sql in queries:
        vn.train(question=question, sql=sql)

# Entrenar queries de gastos e ingresos
train_gastos_ingresos_queries()

def train_rankings_analisis_queries():
    queries = [
        (
            "Ranking de meses por rentabilidad",
            """
            WITH mensual AS (
                SELECT
                    DATE_TRUNC('month', o.fecha) AS mes,
                    (
                        (SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END)
                       - SUM(CASE WHEN o.tipo_operacion='GASTO'   THEN o.monto_uyu ELSE 0 END))
                        / NULLIF(SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
                    ) * 100 AS rentabilidad
                FROM operaciones o
                WHERE o.deleted_at IS NULL
                GROUP BY 1
            )
            SELECT mes, rentabilidad
            FROM mensual
            ORDER BY rentabilidad DESC NULLS LAST
            """
        ),
        (
            "Top 10 operaciones más grandes del año",
            """
            SELECT id, fecha, tipo_operacion, monto_uyu
            FROM operaciones
            WHERE deleted_at IS NULL
              AND DATE_TRUNC('year', fecha) = DATE_TRUNC('year', CURRENT_DATE)
            ORDER BY monto_uyu DESC NULLS LAST
            LIMIT 10
            """
        ),
        (
            "Ranking de socios por distribuciones acumuladas",
            """
            SELECT
                s.nombre AS socio,
                SUM(dd.monto_uyu) AS total_uyu,
                SUM(dd.monto_usd) AS total_usd
            FROM operaciones o
            JOIN distribuciones_detalle dd ON dd.operacion_id = o.id
            JOIN socios s ON s.id = dd.socio_id
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion = 'DISTRIBUCION'
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
            GROUP BY s.nombre
            ORDER BY total_uyu DESC NULLS LAST
            """
        ),
        (
            "Top 5 días con más ingresos",
            """
            SELECT
                o.fecha::date AS dia,
                SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
            GROUP BY o.fecha::date
            ORDER BY ingresos DESC NULLS LAST
            LIMIT 5
            """
        ),
        (
            "Peores 5 días por gastos",
            """
            SELECT
                o.fecha::date AS dia,
                SUM(CASE WHEN o.tipo_operacion='GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
            GROUP BY o.fecha::date
            ORDER BY gastos DESC NULLS LAST
            LIMIT 5
            """
        ),
        (
            "Ranking de áreas por eficiencia",
            """
            SELECT
                a.nombre AS area,
                (
                    (SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END)
                   - SUM(CASE WHEN o.tipo_operacion='GASTO'   THEN o.monto_uyu ELSE 0 END))
                    / NULLIF(SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
                ) * 100 AS eficiencia
            FROM operaciones o
            JOIN areas a ON a.id = o.area_id
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
            GROUP BY a.nombre
            ORDER BY eficiencia DESC NULLS LAST
            """
        ),
        (
            "Top 3 meses con mejor flujo de caja",
            """
            WITH mensual AS (
                SELECT
                    DATE_TRUNC('month', o.fecha) AS mes,
                    (SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END)
                   - SUM(CASE WHEN o.tipo_operacion='GASTO'   THEN o.monto_uyu ELSE 0 END)) AS flujo
                FROM operaciones o
                WHERE o.deleted_at IS NULL
                GROUP BY 1
            )
            SELECT mes, flujo
            FROM mensual
            ORDER BY flujo DESC NULLS LAST
            LIMIT 3
            """
        ),
        (
            "Ranking de trimestres por crecimiento",
            """
            WITH trimestral AS (
                SELECT
                    DATE_TRUNC('quarter', o.fecha) AS trimestre,
                    SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos
                FROM operaciones o
                WHERE o.deleted_at IS NULL
                GROUP BY 1
            )
            SELECT
                trimestre,
                ingresos,
                LAG(ingresos) OVER (ORDER BY trimestre) AS ingresos_prev,
                (ingresos - COALESCE(LAG(ingresos) OVER (ORDER BY trimestre), 0)) AS crecimiento
            FROM trimestral
            ORDER BY crecimiento DESC NULLS LAST
            """
        ),
        (
            "Top localidades por rentabilidad",
            """
            SELECT
                o.localidad,
                (
                    (SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END)
                   - SUM(CASE WHEN o.tipo_operacion='GASTO'   THEN o.monto_uyu ELSE 0 END))
                    / NULLIF(SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
                ) * 100 AS rentabilidad
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
            GROUP BY o.localidad
            ORDER BY rentabilidad DESC NULLS LAST
            """
        ),
        (
            "Ranking de áreas por cantidad de operaciones",
            """
            SELECT
                a.nombre AS area,
                COUNT(*) AS operaciones
            FROM operaciones o
            JOIN areas a ON a.id = o.area_id
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
            GROUP BY a.nombre
            ORDER BY operaciones DESC NULLS LAST
            """
        ),
        (
            "Top 5 retiros más grandes",
            """
            SELECT id, fecha, monto_uyu
            FROM operaciones
            WHERE deleted_at IS NULL
              AND tipo_operacion = 'RETIRO'
              AND DATE_TRUNC('year', fecha) = DATE_TRUNC('year', CURRENT_DATE)
            ORDER BY monto_uyu DESC NULLS LAST
            LIMIT 5
            """
        ),
        (
            "Ranking de meses por distribuciones",
            """
            SELECT
                DATE_TRUNC('month', o.fecha) AS mes,
                SUM(dd.monto_uyu) AS total_uyu,
                SUM(dd.monto_usd) AS total_usd
            FROM operaciones o
            JOIN distribuciones_detalle dd ON dd.operacion_id = o.id
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion = 'DISTRIBUCION'
            GROUP BY 1
            ORDER BY total_uyu DESC NULLS LAST
            """
        ),
        (
            "Bottom 5 áreas por rentabilidad",
            """
            SELECT
                a.nombre AS area,
                (
                    (SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END)
                   - SUM(CASE WHEN o.tipo_operacion='GASTO'   THEN o.monto_uyu ELSE 0 END))
                    / NULLIF(SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
                ) * 100 AS rentabilidad
            FROM operaciones o
            JOIN areas a ON a.id = o.area_id
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
            GROUP BY a.nombre
            ORDER BY rentabilidad ASC NULLS LAST
            LIMIT 5
            """
        ),
        (
            "Ranking de años por ingresos totales",
            """
            SELECT
                EXTRACT(YEAR FROM o.fecha)::int AS anio,
                SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos
            FROM operaciones o
            WHERE o.deleted_at IS NULL
            GROUP BY 1
            ORDER BY ingresos DESC NULLS LAST
            """
        ),
        (
            "Top 10 gastos recurrentes",
            """
            SELECT
                COALESCE(o.proveedor, 'SIN_PROVEEDOR') AS proveedor,
                SUM(CASE WHEN o.tipo_operacion='GASTO' THEN o.monto_uyu ELSE 0 END) AS total_gastado,
                COUNT(*) FILTER (WHERE o.tipo_operacion='GASTO') AS cantidad
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
            GROUP BY COALESCE(o.proveedor, 'SIN_PROVEEDOR')
            ORDER BY total_gastado DESC NULLS LAST
            LIMIT 10
            """
        ),
    ]

    for question, sql in queries:
        vn.train(question=question, sql=sql)

def train_especificas_negocio_queries():
    queries = [
        (
            "¿Cuánto facturamos en el área Jurídica?",
            """
            SELECT
                SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END) AS total_juridica
            FROM operaciones o
            JOIN areas a ON a.id = o.area_id
            WHERE o.deleted_at IS NULL
              AND a.nombre = 'Jurídica'
            """
        ),
        (
            "Gastos de Notarial en Mercedes",
            """
            SELECT
                SUM(CASE WHEN o.tipo_operacion='GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos_notarial_mercedes
            FROM operaciones o
            JOIN areas a ON a.id = o.area_id
            WHERE o.deleted_at IS NULL
              AND a.nombre = 'Notarial'
              AND o.localidad = 'MERCEDES'
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
            """
        ),
        (
            "Ingresos de Contable este trimestre",
            """
            SELECT
                SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos_contable_trim
            FROM operaciones o
            JOIN areas a ON a.id = o.area_id
            WHERE o.deleted_at IS NULL
              AND a.nombre = 'Contable'
              AND DATE_TRUNC('quarter', o.fecha) = DATE_TRUNC('quarter', CURRENT_DATE)
            """
        ),
        (
            "¿Cuánto gastamos en Gastos Generales?",
            """
            SELECT
                SUM(CASE WHEN o.tipo_operacion='GASTO' THEN o.monto_uyu ELSE 0 END) AS gastos_generales_total
            FROM operaciones o
            JOIN areas a ON a.id = o.area_id
            WHERE o.deleted_at IS NULL
              AND a.nombre = 'Gastos Generales'
            """
        ),
        (
            "Retiros totales del año",
            """
            SELECT
                SUM(CASE WHEN o.tipo_operacion='RETIRO' THEN o.monto_uyu ELSE 0 END) AS retiros_ytd
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
            """
        ),
        (
            "Balance general del mes",
            """
            SELECT
                SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
                SUM(CASE WHEN o.tipo_operacion='GASTO'   THEN o.monto_uyu ELSE 0 END) AS gastos,
                SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END)
              - SUM(CASE WHEN o.tipo_operacion='GASTO'   THEN o.monto_uyu ELSE 0 END) AS resultado
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
            """
        ),
        (
            "Flujo de caja operativo",
            """
            SELECT
                SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END)
              - SUM(CASE WHEN o.tipo_operacion='GASTO'   THEN o.monto_uyu ELSE 0 END) AS flujo_operativo_mes
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
            """
        ),
        (
            "Capital de trabajo actual",
            """
            SELECT
                SUM(CASE WHEN o.tipo_operacion='INGRESO'      THEN o.monto_uyu ELSE 0 END)
              - SUM(CASE WHEN o.tipo_operacion='GASTO'        THEN o.monto_uyu ELSE 0 END)
              - SUM(CASE WHEN o.tipo_operacion='RETIRO'       THEN o.monto_uyu ELSE 0 END)
              - SUM(CASE WHEN o.tipo_operacion='DISTRIBUCION' THEN o.monto_uyu ELSE 0 END) AS capital_trabajo_aprox
            FROM operaciones o
            WHERE o.deleted_at IS NULL
            """
        ),
        (
            "¿Cuántos días faltan para fin de mes?",
            """
            SELECT
                (DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month - 1 day' - CURRENT_DATE)::int AS dias_restantes
            """
        ),
        (
            "Promedio de distribuciones por socio",
            """
            SELECT
                s.nombre AS socio,
                AVG(dd.monto_uyu) AS promedio_uyu,
                AVG(dd.monto_usd) AS promedio_usd
            FROM operaciones o
            JOIN distribuciones_detalle dd ON dd.operacion_id = o.id
            JOIN socios s ON s.id = dd.socio_id
            WHERE o.deleted_at IS NULL
              AND o.tipo_operacion = 'DISTRIBUCION'
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
            GROUP BY s.nombre
            ORDER BY promedio_uyu DESC NULLS LAST
            """
        ),
        (
            "¿Cuál es el tipo de cambio promedio usado?",
            """
            SELECT AVG(o.tipo_cambio) AS tipo_cambio_promedio_mes
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
            """
        ),
        (
            "Total de operaciones en USD",
            """
            SELECT
                COUNT(*) AS cantidad,
                SUM(o.monto_usd) AS total_usd
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND o.moneda_original = 'USD'
            """
        ),
        (
            "Total de operaciones en UYU",
            """
            SELECT
                COUNT(*) AS cantidad,
                SUM(o.monto_uyu) AS total_uyu
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND o.moneda_original = 'UYU'
            """
        ),
        (
            "¿Cuántas operaciones hicimos este mes?",
            """
            SELECT COUNT(*) AS operaciones_mes
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
            """
        ),
        (
            "Resumen ejecutivo del trimestre",
            """
            SELECT
                SUM(CASE WHEN o.tipo_operacion='INGRESO'      THEN o.monto_uyu ELSE 0 END) AS ingresos,
                SUM(CASE WHEN o.tipo_operacion='GASTO'        THEN o.monto_uyu ELSE 0 END) AS gastos,
                SUM(CASE WHEN o.tipo_operacion='RETIRO'       THEN o.monto_uyu ELSE 0 END) AS retiros,
                SUM(CASE WHEN o.tipo_operacion='DISTRIBUCION' THEN o.monto_uyu ELSE 0 END) AS distribuciones
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('quarter', o.fecha) = DATE_TRUNC('quarter', CURRENT_DATE)
            """
        ),
        (
            "Estado de resultados simplificado",
            """
            SELECT
                SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos,
                SUM(CASE WHEN o.tipo_operacion='GASTO'   THEN o.monto_uyu ELSE 0 END) AS gastos,
                SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END)
              - SUM(CASE WHEN o.tipo_operacion='GASTO'   THEN o.monto_uyu ELSE 0 END) AS resultado,
                CASE WHEN SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END) = 0
                     THEN 0
                     ELSE (
                        (SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END)
                       - SUM(CASE WHEN o.tipo_operacion='GASTO'   THEN o.monto_uyu ELSE 0 END))
                        / NULLIF(SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
                     ) * 100
                END AS margen_pct
            FROM operaciones o
            WHERE o.deleted_at IS NULL
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
            """
        ),
        (
            "Margen operativo del área Jurídica",
            """
            SELECT
                (
                    (SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END)
                   - SUM(CASE WHEN o.tipo_operacion='GASTO'   THEN o.monto_uyu ELSE 0 END))
                    / NULLIF(SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END), 0)
                ) * 100 AS margen_operativo
            FROM operaciones o
            JOIN areas a ON a.id = o.area_id
            WHERE o.deleted_at IS NULL
              AND a.nombre = 'Jurídica'
              AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
            """
        ),
        (
            "Tasa de crecimiento mensual",
            """
            WITH mensual AS (
                SELECT
                    DATE_TRUNC('month', o.fecha) AS mes,
                    SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos
                FROM operaciones o
                WHERE o.deleted_at IS NULL
                  AND o.fecha >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '11 months'
                GROUP BY 1
            )
            SELECT
                mes,
                ingresos,
                LAG(ingresos) OVER (ORDER BY mes) AS ingresos_prev,
                CASE WHEN COALESCE(LAG(ingresos) OVER (ORDER BY mes), 0) = 0 THEN NULL
                     ELSE ((ingresos - LAG(ingresos) OVER (ORDER BY mes)) / NULLIF(LAG(ingresos) OVER (ORDER BY mes), 0)) * 100
                END AS crecimiento_pct
            FROM mensual
            ORDER BY mes
            """
        ),
        (
            "Proyección de cierre de año",
            """
            WITH params AS (
                SELECT
                    SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos_mtd,
                    SUM(CASE WHEN o.tipo_operacion='GASTO'   THEN o.monto_uyu ELSE 0 END) AS gastos_mtd,
                    EXTRACT(DAY FROM CURRENT_DATE)::numeric AS dia,
                    EXTRACT(DAY FROM (DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month - 1 day'))::numeric AS dias_mes
                FROM operaciones o
                WHERE o.deleted_at IS NULL
                  AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
            )
            SELECT
                (ingresos_mtd / NULLIF(dia,0) * 365) AS ingresos_proyectados_anual,
                (gastos_mtd   / NULLIF(dia,0) * 365) AS gastos_proyectados_anual,
                CASE WHEN (ingresos_mtd / NULLIF(dia,0) * 365) = 0 THEN 0
                     ELSE (((ingresos_mtd / NULLIF(dia,0) * 365) - (gastos_mtd / NULLIF(dia,0) * 365))
                          / NULLIF((ingresos_mtd / NULLIF(dia,0) * 365), 0)) * 100
                END AS rentabilidad_proyectada_pct
            FROM params
            """
        ),
        (
            "Análisis de estacionalidad",
            """
            WITH mensual AS (
                SELECT
                    DATE_TRUNC('month', o.fecha) AS mes,
                    EXTRACT(MONTH FROM o.fecha)::int AS nro_mes,
                    SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END) AS ingresos
                FROM operaciones o
                WHERE o.deleted_at IS NULL
                GROUP BY 1, 2
            )
            SELECT
                nro_mes,
                AVG(ingresos) AS promedio_ingresos
            FROM mensual
            GROUP BY nro_mes
            ORDER BY nro_mes
            """
        ),
    ]

    for question, sql in queries:
        vn.train(question=question, sql=sql)

# Entrenar queries de rankings y análisis
train_rankings_analisis_queries()
# Entrenar queries específicas de negocio
train_especificas_negocio_queries()
print("Entrenamiento completado")
