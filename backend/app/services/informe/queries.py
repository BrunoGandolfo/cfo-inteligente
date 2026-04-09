"""Queries SQL predefinidas para informes financieros multi-query."""

from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.logger import get_logger

logger = get_logger(__name__)


# ══════════════════════════════════════════════════════════════
# QUERIES PREDEFINIDAS
# ══════════════════════════════════════════════════════════════

def _query_totales_por_tipo() -> str:
    """Totales de los 4 tipos de operacion (INGRESO, GASTO, RETIRO, DISTRIBUCION)."""
    return """
        SELECT
            tipo_operacion,
            SUM(total_pesificado) AS total_uyu,
            SUM(total_dolarizado) AS total_usd,
            COUNT(*) AS cantidad
        FROM operaciones
        WHERE deleted_at IS NULL
          AND fecha >= :fecha_desde
          AND fecha <= :fecha_hasta
        GROUP BY tipo_operacion
        ORDER BY tipo_operacion
    """


def _query_operativo_por_area() -> str:
    """Ingresos y gastos desglosados por area."""
    return """
        SELECT
            a.nombre AS area,
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) AS ingresos_uyu,
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_dolarizado ELSE 0 END) AS ingresos_usd,
            SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END) AS gastos_uyu,
            SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_dolarizado ELSE 0 END) AS gastos_usd,
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) -
            SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END) AS neto_uyu,
            CASE
                WHEN SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) = 0 THEN 0
                ELSE ROUND(
                    (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) -
                     SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END)) * 100.0 /
                    SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 1
                )
            END AS rentabilidad
        FROM operaciones o
        INNER JOIN areas a ON o.area_id = a.id
        WHERE o.deleted_at IS NULL
          AND o.tipo_operacion IN ('INGRESO', 'GASTO')
          AND o.fecha >= :fecha_desde
          AND o.fecha <= :fecha_hasta
        GROUP BY a.nombre
        ORDER BY ingresos_uyu DESC
    """


def _query_distribuciones_por_socio() -> str:
    """Distribuciones con detalle por socio."""
    return """
        SELECT
            s.nombre AS socio,
            SUM(dd.total_pesificado) AS total_pesificado,
            SUM(dd.total_dolarizado) AS total_dolarizado,
            SUM(dd.monto_uyu) AS monto_uyu,
            SUM(dd.monto_usd) AS monto_usd,
            MAX(dd.porcentaje) AS porcentaje,
            COUNT(*) AS cantidad
        FROM distribuciones_detalle dd
        INNER JOIN operaciones o ON dd.operacion_id = o.id
        INNER JOIN socios s ON dd.socio_id = s.id
        WHERE o.tipo_operacion = 'DISTRIBUCION'
          AND o.deleted_at IS NULL
          AND o.fecha >= :fecha_desde
          AND o.fecha <= :fecha_hasta
        GROUP BY s.nombre
        ORDER BY total_pesificado DESC
    """


def _query_retiros_por_localidad() -> str:
    """Retiros agrupados por localidad."""
    return """
        SELECT
            localidad,
            SUM(total_pesificado) AS total_uyu,
            SUM(CASE WHEN moneda_original = 'USD' THEN monto_original ELSE 0 END) AS retiros_usd_real,
            COUNT(*) AS cantidad
        FROM operaciones
        WHERE tipo_operacion = 'RETIRO'
          AND deleted_at IS NULL
          AND fecha >= :fecha_desde
          AND fecha <= :fecha_hasta
        GROUP BY localidad
        ORDER BY total_uyu DESC
    """


def _query_retiros_por_socio() -> Optional[str]:
    """TODO: retiros por socio no derivable con el modelo actual."""
    return None


def _query_desglose_por_localidad() -> str:
    """Desglose de los 4 tipos de operación por localidad."""
    return """
        SELECT
            localidad,
            SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END) AS ingresos_uyu,
            SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END) AS ingresos_usd,
            SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END) AS gastos_uyu,
            SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END) AS gastos_usd,
            SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END) AS retiros_uyu,
            SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END) AS retiros_usd,
            SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END) AS distribuciones_uyu,
            SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_dolarizado ELSE 0 END) AS distribuciones_usd
        FROM operaciones
        WHERE deleted_at IS NULL
          AND fecha >= :fecha_desde
          AND fecha <= :fecha_hasta
        GROUP BY localidad
        ORDER BY localidad
    """


def _query_evolucion_mensual() -> str:
    """Evolución mes a mes con los 4 tipos de operación."""
    return """
        SELECT
            EXTRACT(MONTH FROM fecha)::INTEGER AS mes,
            SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END) AS ingresos_uyu,
            SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END) AS gastos_uyu,
            SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END) AS retiros_uyu,
            SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END) AS distribuciones_uyu,
            COUNT(*) AS total_operaciones
        FROM operaciones
        WHERE deleted_at IS NULL
          AND fecha >= :fecha_desde
          AND fecha <= :fecha_hasta
        GROUP BY EXTRACT(MONTH FROM fecha)
        ORDER BY mes
    """


def _query_composicion_por_moneda() -> str:
    """Composición de UYU vs USD por tipo de operación."""
    return """
        SELECT
            tipo_operacion,
            moneda_original,
            SUM(total_pesificado) AS total_uyu,
            COUNT(*) AS cantidad
        FROM operaciones
        WHERE deleted_at IS NULL
          AND fecha >= :fecha_desde
          AND fecha <= :fecha_hasta
        GROUP BY tipo_operacion, moneda_original
        ORDER BY tipo_operacion, moneda_original
    """


def _query_top_clientes() -> str:
    """Top 10 clientes por facturación (solo INGRESO)."""
    return """
        SELECT
            cliente,
            SUM(total_pesificado) AS total_uyu,
            SUM(total_dolarizado) AS total_usd,
            COUNT(*) AS cantidad_operaciones
        FROM operaciones
        WHERE tipo_operacion = 'INGRESO'
          AND deleted_at IS NULL
          AND fecha >= :fecha_desde
          AND fecha <= :fecha_hasta
          AND cliente IS NOT NULL
          AND cliente != ''
        GROUP BY cliente
        ORDER BY total_uyu DESC
        LIMIT 10
    """


def _query_top_proveedores() -> str:
    """Top 10 proveedores por gasto (solo GASTO)."""
    return """
        SELECT
            proveedor,
            SUM(total_pesificado) AS total_uyu,
            SUM(total_dolarizado) AS total_usd,
            COUNT(*) AS cantidad_operaciones
        FROM operaciones
        WHERE tipo_operacion = 'GASTO'
          AND deleted_at IS NULL
          AND fecha >= :fecha_desde
          AND fecha <= :fecha_hasta
          AND proveedor IS NOT NULL
          AND proveedor != ''
        GROUP BY proveedor
        ORDER BY total_uyu DESC
        LIMIT 10
    """


def _query_matriz_area_localidad() -> str:
    """Matriz área x localidad con ingresos, gastos, neto y rentabilidad."""
    return """
        SELECT
            a.nombre AS area,
            o.localidad,
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) AS ingresos_uyu,
            SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END) AS gastos_uyu,
            SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) -
            SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END) AS neto_uyu,
            CASE
                WHEN SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) = 0 THEN 0
                ELSE ROUND(
                    (SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) -
                     SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END)) * 100.0 /
                    SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 1
                )
            END AS rentabilidad,
            COUNT(*) AS cantidad_operaciones
        FROM operaciones o
        INNER JOIN areas a ON o.area_id = a.id
        WHERE o.deleted_at IS NULL
          AND o.tipo_operacion IN ('INGRESO', 'GASTO')
          AND o.fecha >= :fecha_desde
          AND o.fecha <= :fecha_hasta
        GROUP BY a.nombre, o.localidad
        ORDER BY a.nombre, o.localidad
    """


def _query_ticket_promedio_por_area() -> str:
    """Ticket promedio de ingreso y gasto por área."""
    return """
        SELECT
            a.nombre AS area,
            o.tipo_operacion,
            COUNT(*) AS cantidad,
            SUM(o.total_pesificado) AS total_uyu,
            ROUND(SUM(o.total_pesificado) / COUNT(*), 2) AS ticket_promedio_uyu
        FROM operaciones o
        INNER JOIN areas a ON o.area_id = a.id
        WHERE o.deleted_at IS NULL
          AND o.tipo_operacion IN ('INGRESO', 'GASTO')
          AND o.fecha >= :fecha_desde
          AND o.fecha <= :fecha_hasta
        GROUP BY a.nombre, o.tipo_operacion
        ORDER BY a.nombre, o.tipo_operacion
    """


def _query_concentracion_clientes() -> str:
    """Concentración de cartera: top 10 clientes con participación acumulada."""
    return """
        WITH total_ingresos AS (
            SELECT SUM(total_pesificado) AS total
            FROM operaciones
            WHERE tipo_operacion = 'INGRESO'
              AND deleted_at IS NULL
              AND fecha >= :fecha_desde
              AND fecha <= :fecha_hasta
        ),
        ranking AS (
            SELECT
                cliente,
                SUM(total_pesificado) AS total_uyu,
                COUNT(*) AS cantidad_operaciones,
                ROW_NUMBER() OVER (ORDER BY SUM(total_pesificado) DESC) AS ranking
            FROM operaciones
            WHERE tipo_operacion = 'INGRESO'
              AND deleted_at IS NULL
              AND fecha >= :fecha_desde
              AND fecha <= :fecha_hasta
              AND cliente IS NOT NULL AND cliente != ''
            GROUP BY cliente
        )
        SELECT
            r.cliente,
            r.total_uyu,
            r.cantidad_operaciones,
            r.ranking,
            ROUND(r.total_uyu * 100.0 / t.total, 1) AS participacion_pct,
            ROUND(SUM(r2.total_uyu) * 100.0 / t.total, 1) AS participacion_acumulada_pct
        FROM ranking r
        CROSS JOIN total_ingresos t
        JOIN ranking r2 ON r2.ranking <= r.ranking
        WHERE r.ranking <= 10
        GROUP BY r.cliente, r.total_uyu, r.cantidad_operaciones, r.ranking, t.total
        ORDER BY r.ranking
    """


def _query_capital_trabajo() -> str:
    """Capital de trabajo y ratios de sostenibilidad."""
    return """
        SELECT
            SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END) AS ingresos_uyu,
            SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END) AS gastos_uyu,
            SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END) AS retiros_uyu,
            SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END) AS distribuciones_uyu,
            SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END) -
            SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END) AS resultado_neto_uyu,
            SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END) -
            SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END) -
            SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END) AS capital_trabajo_uyu,
            CASE
                WHEN SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END) = 0 THEN 0
                ELSE ROUND(
                    SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END) * 100.0 /
                    SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 1
                )
            END AS ratio_distribuciones_sobre_ingresos,
            CASE
                WHEN (SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END) -
                      SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END)) = 0 THEN 0
                ELSE ROUND(
                    SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END) * 100.0 /
                    (SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END) -
                     SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END)), 1
                )
            END AS ratio_distribuciones_sobre_resultado
        FROM operaciones
        WHERE deleted_at IS NULL
          AND fecha >= :fecha_desde
          AND fecha <= :fecha_hasta
    """


def _query_evolucion_trimestral() -> str:
    """Evolución trimestral con ingresos, gastos, resultado, rentabilidad."""
    return """
        SELECT
            EXTRACT(QUARTER FROM fecha)::INTEGER AS trimestre,
            EXTRACT(YEAR FROM fecha)::INTEGER AS anio,
            SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END) AS ingresos_uyu,
            SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END) AS gastos_uyu,
            SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END) -
            SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END) AS resultado_neto_uyu,
            CASE
                WHEN SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END) = 0 THEN 0
                ELSE ROUND(
                    (SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END) -
                     SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END)) * 100.0 /
                    SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 1
                )
            END AS rentabilidad,
            SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END) AS retiros_uyu,
            SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END) AS distribuciones_uyu,
            SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END) -
            SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END) -
            SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END) AS capital_retenido_uyu,
            COUNT(*) AS total_operaciones
        FROM operaciones
        WHERE deleted_at IS NULL
          AND fecha >= :fecha_desde
          AND fecha <= :fecha_hasta
        GROUP BY EXTRACT(QUARTER FROM fecha), EXTRACT(YEAR FROM fecha)
        ORDER BY anio, trimestre
    """


def _query_clientes_nuevos_perdidos() -> dict:
    """Dos queries para detectar clientes nuevos y perdidos entre períodos."""
    return {
        "perdidos": """
            SELECT cliente, SUM(total_pesificado) AS total_uyu, COUNT(*) AS cantidad
            FROM operaciones
            WHERE tipo_operacion = 'INGRESO'
              AND deleted_at IS NULL
              AND fecha >= :fecha_desde_ant AND fecha <= :fecha_hasta_ant
              AND cliente IS NOT NULL AND cliente != ''
              AND cliente NOT IN (
                  SELECT DISTINCT cliente FROM operaciones
                  WHERE tipo_operacion = 'INGRESO'
                    AND deleted_at IS NULL
                    AND fecha >= :fecha_desde_act AND fecha <= :fecha_hasta_act
                    AND cliente IS NOT NULL AND cliente != ''
              )
            GROUP BY cliente
            ORDER BY total_uyu DESC
            LIMIT 10
        """,
        "nuevos": """
            SELECT cliente, SUM(total_pesificado) AS total_uyu, COUNT(*) AS cantidad
            FROM operaciones
            WHERE tipo_operacion = 'INGRESO'
              AND deleted_at IS NULL
              AND fecha >= :fecha_desde_act AND fecha <= :fecha_hasta_act
              AND cliente IS NOT NULL AND cliente != ''
              AND cliente NOT IN (
                  SELECT DISTINCT cliente FROM operaciones
                  WHERE tipo_operacion = 'INGRESO'
                    AND deleted_at IS NULL
                    AND fecha >= :fecha_desde_ant AND fecha <= :fecha_hasta_ant
                    AND cliente IS NOT NULL AND cliente != ''
              )
            GROUP BY cliente
            ORDER BY total_uyu DESC
            LIMIT 10
        """,
    }


# ══════════════════════════════════════════════════════════════
# EJECUTOR DE QUERIES
# ══════════════════════════════════════════════════════════════

def _ejecutar_query(db: Session, sql: str, params: dict) -> list[dict]:
    """Ejecuta una query parametrizada y retorna lista de dicts."""
    result = db.execute(text(sql), params)
    return [dict(row._mapping) for row in result]


def _ejecutar_query_opcional(
    db: Session,
    sql: Optional[str],
    params: dict,
    nombre: str,
    valor_default: Optional[list[dict]] = None,
) -> list[dict]:
    """Ejecuta una query opcional sin romper el informe completo."""
    if sql is None:
        return valor_default or []
    try:
        return _ejecutar_query(db, sql, params)
    except Exception as e:
        logger.warning(f"Orquestador: sección opcional '{nombre}' no disponible — {e}")
        return valor_default or []
