"""
Orquestador Multi-Query para Informes Financieros Completos.

Cuando un usuario pide "informe financiero completo", el pipeline normal
genera 1 SQL que inevitablemente pierde datos (RETIRO y DISTRIBUCION
no tienen area_id, asi que JOIN areas los elimina).

Este modulo resuelve el problema ejecutando 3-4 queries simples e
independientes, cada una optimizada para su tipo de dato, y combina
los resultados en un JSON estructurado que la capa narrativa interpreta.

Flujo:
  cfo_streaming.py → es_pregunta_informe()? → SI → ejecutar_informe()
                                             → NO → flujo normal (sin cambios)
"""

import re
from datetime import date
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.logger import get_logger

logger = get_logger(__name__)


# ══════════════════════════════════════════════════════════════
# DETECTOR DE INTENCIÓN INFORME
# ══════════════════════════════════════════════════════════════

# Frases que indican pedido de informe/resumen completo.
# Orden: frases largas primero para evitar falsos positivos.
_KEYWORDS_INFORME = [
    "informe comparativo del desempeño",
    "informe comparativo",
    "comparativo financiero",
    "comparar el desempeño financiero",
    "desempeño financiero",
    "comparar años",
    "comparar el año",
    "informe financiero completo",
    "informe financiero",
    "informe completo",
    "informe ejecutivo",
    "reporte financiero",
    "reporte completo",
    "resumen financiero completo",
    "resumen financiero",
    "resumen completo",
    "resumen ejecutivo",
    "situación financiera",
    "situacion financiera",
    "cómo cerró el año",
    "como cerro el año",
    "como cerro el ano",
    "cómo cerró el ano",
    "cómo viene el año",
    "como viene el año",
    "como viene el ano",
    "reporte ejecutivo",
    "informe general",
    "resumen general del año",
    "resumen general del ano",
]

# Keywords que EXCLUYEN la intención informe (preguntas puntuales)
_KEYWORDS_EXCLUSION = [
    "por área",
    "por area",
    "por mes",
    "por localidad",
    "por socio",
    "cuánto",
    "cuanto",
    "cuál",
    "cual ",
    "top ",
    "ranking",
]


def es_pregunta_informe(pregunta: str) -> bool:
    """
    Detecta si la pregunta solicita un informe/resumen financiero completo.

    Busca keywords de informe y excluye preguntas puntuales que contienen
    dimensiones especificas (por area, por mes, etc.).

    Args:
        pregunta: Pregunta del usuario en lenguaje natural.

    Returns:
        True si la pregunta es un pedido de informe completo.
    """
    p = pregunta.lower().strip()

    # Debe contener al menos un keyword de informe
    tiene_keyword = any(kw in p for kw in _KEYWORDS_INFORME)
    if not tiene_keyword:
        return False

    # Excluir si tiene dimensiones puntuales (es una pregunta especifica, no un informe)
    tiene_exclusion = any(kw in p for kw in _KEYWORDS_EXCLUSION)
    if tiene_exclusion:
        return False

    return True


# ══════════════════════════════════════════════════════════════
# EXTRACTOR DE PERÍODO
# ══════════════════════════════════════════════════════════════

_MESES_MAP = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}

_TRIMESTRES = {
    "primer": (1, 3), "1er": (1, 3), "primero": (1, 3), "q1": (1, 3),
    "segundo": (4, 6), "2do": (4, 6), "q2": (4, 6),
    "tercer": (7, 9), "3er": (7, 9), "tercero": (7, 9), "q3": (7, 9),
    "cuarto": (10, 12), "4to": (10, 12), "q4": (10, 12),
}

_SEMESTRES = {
    "primer": (1, 6), "1er": (1, 6), "primero": (1, 6),
    "segundo": (7, 12), "2do": (7, 12),
}


def extraer_periodo_informe(pregunta: str) -> Optional[dict]:
    """
    Extrae el periodo temporal de una pregunta de informe.

    Soporta:
    - Año completo: "informe del 2025"
    - Semestre: "informe del primer semestre 2024"
    - Trimestre: "informe del Q1 2025"
    - Comparativo: "informe comparativo 2024 vs 2025"
    - Sin año: retorna None (el flujo normal se encargara)

    Args:
        pregunta: Pregunta del usuario.

    Returns:
        Dict con periodo(s) o None si no puede extraer.
    """
    p = pregunta.lower()

    # Extraer todos los años mencionados (formato 20XX)
    anios = [int(a) for a in re.findall(r'\b(20[2-3]\d)\b', p)]

    # Comparativo: 2+ años
    if len(anios) >= 2:
        anios_unicos = sorted(set(anios))[:2]
        return {
            "tipo": "comparativo",
            "periodos": [
                _periodo_anio_completo(a) for a in anios_unicos
            ],
        }

    # Un año o año actual por defecto
    anio = anios[0] if anios else None
    if anio is None:
        # "este año", "el año" sin numero → año actual
        if any(kw in p for kw in ["este año", "este ano", "el año", "el ano", "del año", "del ano"]):
            anio = date.today().year
        else:
            return None

    # Detectar trimestre
    for kw, (mes_desde, mes_hasta) in _TRIMESTRES.items():
        if kw in p and "trimestre" in p:
            return {
                "tipo": "periodo",
                "anio": anio,
                "fecha_desde": f"{anio}-{mes_desde:02d}-01",
                "fecha_hasta": f"{anio}-{mes_hasta:02d}-{_ultimo_dia(anio, mes_hasta):02d}",
                "descripcion": f"trimestre {kw} {anio}",
            }

    # Detectar semestre
    for kw, (mes_desde, mes_hasta) in _SEMESTRES.items():
        if kw in p and "semestre" in p:
            return {
                "tipo": "periodo",
                "anio": anio,
                "fecha_desde": f"{anio}-{mes_desde:02d}-01",
                "fecha_hasta": f"{anio}-{mes_hasta:02d}-{_ultimo_dia(anio, mes_hasta):02d}",
                "descripcion": f"semestre {kw} {anio}",
            }

    # Detectar rango de meses (ej: "de marzo a junio 2026")
    meses_regex = "|".join(sorted(_MESES_MAP.keys(), key=len, reverse=True))
    match_rango = re.search(
        rf"(?:de\s+)?({meses_regex})\s+(?:a|hasta)\s+({meses_regex})\b",
        p
    )
    if match_rango:
        mes_desde_nombre = match_rango.group(1)
        mes_hasta_nombre = match_rango.group(2)
        mes_desde = _MESES_MAP[mes_desde_nombre]
        mes_hasta = _MESES_MAP[mes_hasta_nombre]
        if mes_desde > mes_hasta:
            mes_desde, mes_hasta = mes_hasta, mes_desde
            mes_desde_nombre, mes_hasta_nombre = mes_hasta_nombre, mes_desde_nombre
        return {
            "tipo": "periodo",
            "anio": anio,
            "fecha_desde": f"{anio}-{mes_desde:02d}-01",
            "fecha_hasta": f"{anio}-{mes_hasta:02d}-{_ultimo_dia_mes(anio, mes_hasta):02d}",
            "descripcion": f"{mes_desde_nombre} a {mes_hasta_nombre} {anio}",
        }

    # Detectar mes individual (ej: "febrero 2026")
    for nombre_mes, numero_mes in _MESES_MAP.items():
        if re.search(rf"\b{re.escape(nombre_mes)}\b", p):
            return {
                "tipo": "periodo",
                "anio": anio,
                "fecha_desde": f"{anio}-{numero_mes:02d}-01",
                "fecha_hasta": f"{anio}-{numero_mes:02d}-{_ultimo_dia_mes(anio, numero_mes):02d}",
                "descripcion": f"{nombre_mes} {anio}",
            }

    # Año completo (caso mas comun)
    return _periodo_anio_completo(anio)


def _periodo_anio_completo(anio: int) -> dict:
    """Retorna dict de periodo para un año completo."""
    return {
        "tipo": "periodo",
        "anio": anio,
        "fecha_desde": f"{anio}-01-01",
        "fecha_hasta": f"{anio}-12-31",
        "descripcion": str(anio),
    }


def _ultimo_dia(anio: int, mes: int) -> int:
    """Retorna el ultimo dia del mes."""
    import calendar
    return calendar.monthrange(anio, mes)[1]


def _ultimo_dia_mes(anio: int, mes: int) -> int:
    """Retorna el último día del mes considerando bisiestos."""
    import calendar
    return calendar.monthrange(anio, mes)[1]


# ══════════════════════════════════════════════════════════════
# QUERIES PREDEFINIDAS
# ══════════════════════════════════════════════════════════════

def _query_totales_por_tipo() -> str:
    """
    Totales de los 4 tipos de operacion (INGRESO, GASTO, RETIRO, DISTRIBUCION).

    Sin JOIN areas — captura TODO incluyendo operaciones sin area_id.
    """
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
    """
    Ingresos y gastos desglosados por area.

    Solo INGRESO y GASTO (que SIEMPRE tienen area_id NOT NULL).
    Usa INNER JOIN areas — seguro porque filtra por tipos con area.
    """
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
    """
    Distribuciones con detalle por socio.

    Usa distribuciones_detalle (granularidad por socio) con JOIN a
    operaciones (para filtro temporal y soft delete) y socios (para nombre).
    Suma dd.total_pesificado — NUNCA o.total_pesificado (evita multiplicar x5).
    """
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
    """
    Retiros agrupados por localidad (una fila por localidad).

    No necesita JOIN (retiros no tienen area_id ni detalle por socio).
    USD real se calcula con CASE sobre moneda_original, sin GROUP BY moneda.
    """
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
    """
    TODO: retiros por socio no es derivable con el modelo actual.

    La tabla operaciones (tipo RETIRO) no posee socio_id ni existe tabla detalle
    equivalente a distribuciones_detalle para vincular cada retiro a un socio.
    Sin esa FK, cualquier query por socio sería una inferencia incorrecta.
    """
    return None


def _query_desglose_por_localidad() -> str:
    """
    Desglose de los 4 tipos de operación por localidad.

    Compara SIEMPRE Montevideo vs Mercedes como unidades de negocio.
    """
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
    """
    Evolución mes a mes con los 4 tipos de operación.
    """
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
    """
    Composición de UYU vs USD por tipo de operación.
    """
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
    """
    Top 10 clientes por facturación (solo INGRESO).
    """
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
    """
    Top 10 proveedores por gasto (solo GASTO).
    """
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
    """
    Matriz área × localidad con ingresos, gastos, neto y rentabilidad.

    Permite comparar rendimiento de cada área en cada oficina.
    Solo INGRESO y GASTO (que tienen area_id real).
    """
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
    """
    Ticket promedio de ingreso y gasto por área.

    Detecta si un área factura muchos tickets chicos o pocos grandes.
    """
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
    """
    Concentración de cartera: top 10 clientes con participación acumulada.

    Permite detectar riesgo de dependencia (ej: si top 3 = 60% de facturación).
    """
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
    """
    Capital de trabajo y ratios de sostenibilidad.

    Calcula cuánto queda en la empresa después de gastos, retiros y distribuciones,
    y los ratios de extracción sobre ingresos y sobre resultado neto.
    """
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
            SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END) -
            SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END) AS capital_trabajo_uyu,
            CASE
                WHEN SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END) = 0 THEN 0
                ELSE ROUND(
                    (SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END) +
                     SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END)) * 100.0 /
                    SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 1
                )
            END AS ratio_extracciones_sobre_ingresos,
            CASE
                WHEN (SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END) -
                      SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END)) = 0 THEN 0
                ELSE ROUND(
                    (SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END) +
                     SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END)) * 100.0 /
                    (SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END) -
                     SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END)), 1
                )
            END AS ratio_extracciones_sobre_resultado
        FROM operaciones
        WHERE deleted_at IS NULL
          AND fecha >= :fecha_desde
          AND fecha <= :fecha_hasta
    """


def _query_evolucion_trimestral() -> str:
    """
    Evolución trimestral con ingresos, gastos, resultado, rentabilidad,
    retiros, distribuciones y capital retenido por Q.
    """
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
            SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END) -
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
    """
    Dos queries para detectar clientes nuevos y perdidos entre períodos.

    Usa params con sufijo _ant y _act para referenciar ambos períodos.
    Retorna dict con keys "perdidos" y "nuevos".
    """
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
    """
    Ejecuta una query parametrizada y retorna lista de dicts.

    Args:
        db: Session de SQLAlchemy.
        sql: Query SQL con placeholders :nombre.
        params: Dict de parametros.

    Returns:
        Lista de dicts con los resultados.
    """
    result = db.execute(text(sql), params)
    return [dict(row._mapping) for row in result]


def _ejecutar_query_opcional(
    db: Session,
    sql: Optional[str],
    params: dict,
    nombre: str,
    valor_default: Optional[list[dict]] = None,
) -> list[dict]:
    """
    Ejecuta una query opcional sin romper el informe completo.

    Se usa para secciones complementarias del reporte de directorio. Si fallan,
    se retorna valor default y se deja trazabilidad en logs.
    """
    if sql is None:
        return valor_default or []
    try:
        return _ejecutar_query(db, sql, params)
    except Exception as e:
        logger.warning(f"Orquestador: sección opcional '{nombre}' no disponible — {e}")
        return valor_default or []


def _serializar_valor(val: Any) -> Any:
    """Convierte Decimal y otros tipos no-JSON a tipos nativos."""
    if isinstance(val, Decimal):
        return float(val)
    return val


def _serializar_filas(filas: list[dict]) -> list[dict]:
    """Serializa todas las filas para JSON."""
    return [
        {k: _serializar_valor(v) for k, v in fila.items()}
        for fila in filas
    ]


# ══════════════════════════════════════════════════════════════
# ENSAMBLADOR DE INFORME
# ══════════════════════════════════════════════════════════════

def _ensamblar_totales(filas_tipo: list[dict]) -> dict:
    """
    Transforma filas de GROUP BY tipo_operacion en dict de totales.

    Entrada: [{"tipo_operacion": "INGRESO", "total_uyu": X, ...}, ...]
    Salida: {"ingresos": {"uyu": X, "usd": Y, "cantidad": N}, ...}
    """
    mapa_nombres = {
        "INGRESO": "ingresos",
        "GASTO": "gastos",
        "RETIRO": "retiros",
        "DISTRIBUCION": "distribuciones",
    }
    totales = {}
    for fila in filas_tipo:
        tipo = fila.get("tipo_operacion", "")
        nombre = mapa_nombres.get(tipo, tipo.lower())
        totales[nombre] = {
            "uyu": _serializar_valor(fila.get("total_uyu", 0)),
            "usd": _serializar_valor(fila.get("total_usd", 0)),
            "cantidad": fila.get("cantidad", 0),
        }

    # Calcular resultado neto y rentabilidad
    ing = totales.get("ingresos", {}).get("uyu", 0) or 0
    gas = totales.get("gastos", {}).get("uyu", 0) or 0
    totales["resultado_neto"] = {
        "uyu": round(ing - gas, 2),
        "rentabilidad": round((ing - gas) / ing * 100, 1) if ing > 0 else 0,
    }
    # Capital de trabajo
    ret = totales.get("retiros", {}).get("uyu", 0) or 0
    dist = totales.get("distribuciones", {}).get("uyu", 0) or 0
    totales["capital_de_trabajo"] = {
        "uyu": round(ing - gas - ret - dist, 2),
    }

    return totales


def _ensamblar_por_area(filas_area: list[dict]) -> list[dict]:
    """Serializa filas de operativo por area."""
    return _serializar_filas(filas_area)


def _ensamblar_distribuciones(filas_dist: list[dict]) -> list[dict]:
    """
    Serializa filas de distribuciones por socio.

    Mantiene compatibilidad con el contrato anterior:
    - cantidad_distribuciones (alias legacy de cantidad)
    - total_pesificado/total_dolarizado presentes aunque la query antigua no los traiga
    """
    filas = _serializar_filas(filas_dist)
    for fila in filas:
        if "cantidad_distribuciones" not in fila:
            fila["cantidad_distribuciones"] = fila.get("cantidad", 0)
        if "cantidad" not in fila:
            fila["cantidad"] = fila.get("cantidad_distribuciones", 0)
        if "total_pesificado" not in fila:
            fila["total_pesificado"] = fila.get("monto_uyu", 0)
        if "total_dolarizado" not in fila:
            fila["total_dolarizado"] = fila.get("monto_usd", 0)
    return filas


def _ensamblar_retiros(filas_ret: list[dict]) -> list[dict]:
    """Serializa filas de retiros por localidad."""
    return _serializar_filas(filas_ret)


def _ensamblar_retiros_por_socio(filas_ret_socio: list[dict]) -> list[dict]:
    """Serializa filas de retiros por socio (placeholder hasta tener FK socio_id)."""
    return _serializar_filas(filas_ret_socio)


def _ensamblar_por_localidad(filas_loc: list[dict]) -> list[dict]:
    """
    Serializa desglose por localidad y calcula neto/rentabilidad por oficina.
    """
    filas = _serializar_filas(filas_loc)
    for fila in filas:
        ingresos = fila.get("ingresos_uyu", 0) or 0
        gastos = fila.get("gastos_uyu", 0) or 0
        fila["resultado_neto_uyu"] = round(ingresos - gastos, 2)
        fila["rentabilidad"] = round((ingresos - gastos) / ingresos * 100, 1) if ingresos > 0 else 0
    return filas


def _ensamblar_evolucion_mensual(filas_mes: list[dict]) -> list[dict]:
    """Serializa evolución mensual."""
    return _serializar_filas(filas_mes)


def _ensamblar_composicion_por_moneda(filas_moneda: list[dict]) -> list[dict]:
    """
    Serializa composición por moneda y agrega % por tipo de operación.
    """
    filas = _serializar_filas(filas_moneda)
    totales_por_tipo: dict[str, float] = {}
    for fila in filas:
        tipo = fila.get("tipo_operacion")
        total = fila.get("total_uyu", 0) or 0
        totales_por_tipo[tipo] = totales_por_tipo.get(tipo, 0) + total

    for fila in filas:
        tipo = fila.get("tipo_operacion")
        total_tipo = totales_por_tipo.get(tipo, 0) or 0
        total = fila.get("total_uyu", 0) or 0
        fila["porcentaje_tipo"] = round(total / total_tipo * 100, 1) if total_tipo > 0 else 0

    return filas


def _ensamblar_top_clientes(filas_clientes: list[dict]) -> list[dict]:
    """Serializa top clientes."""
    return _serializar_filas(filas_clientes)


def _ensamblar_top_proveedores(filas_prov: list[dict]) -> list[dict]:
    """Serializa top proveedores."""
    return _serializar_filas(filas_prov)


def _ensamblar_matriz_area_localidad(filas: list[dict]) -> list[dict]:
    """Serializa matriz área × localidad."""
    return _serializar_filas(filas)


def _ensamblar_ticket_promedio(filas: list[dict]) -> list[dict]:
    """Serializa ticket promedio por área."""
    return _serializar_filas(filas)


def _ensamblar_concentracion_clientes(filas: list[dict]) -> list[dict]:
    """Serializa concentración de cartera de clientes."""
    return _serializar_filas(filas)


def _ensamblar_capital_trabajo(filas: list[dict]) -> dict:
    """Serializa capital de trabajo (fila única → dict)."""
    if not filas:
        return {}
    return {k: _serializar_valor(v) for k, v in filas[0].items()}


def _ensamblar_clientes_movimiento(filas_perdidos: list[dict], filas_nuevos: list[dict]) -> dict:
    """Ensambla clientes perdidos y nuevos entre dos períodos."""
    return {
        "perdidos": _serializar_filas(filas_perdidos),
        "nuevos": _serializar_filas(filas_nuevos),
    }


def _ensamblar_evolucion_trimestral(filas: list[dict]) -> list[dict]:
    """Serializa evolución trimestral con nombre legible del Q."""
    nombres = {1: "Q1 (Ene-Mar)", 2: "Q2 (Abr-Jun)", 3: "Q3 (Jul-Sep)", 4: "Q4 (Oct-Dic)"}
    resultado = []
    for f in filas:
        d = {k: _serializar_valor(v) for k, v in f.items()}
        d["trimestre_nombre"] = nombres.get(d.get("trimestre"), f"Q{d.get('trimestre')}")
        resultado.append(d)
    return resultado


# ══════════════════════════════════════════════════════════════
# FORMATEADORES PARA NARRATIVA
# ══════════════════════════════════════════════════════════════

_NOMBRE_MES = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic",
}


def _fmt_uyu(valor) -> str:
    """Formatea número como peso uruguayo. Ej: 893075002.92 → '$893.075.003'"""
    try:
        return f"${int(round(float(valor))):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "$0"


def _fmt_usd(valor) -> str:
    """Formatea número como dólar. Ej: 22838.45 → 'US$ 22.838'"""
    try:
        return f"US$ {int(round(float(valor))):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "US$ 0"


def _fmt_pct(valor) -> str:
    """Formatea porcentaje. Ej: 67.7 → '67,7%'"""
    try:
        return f"{float(valor):.1f}%".replace(".", ",")
    except (TypeError, ValueError):
        return "0,0%"


def _fmt_delta(valor, es_porcentaje=False) -> str:
    """Formatea delta con signo. Ej: -58.7 → '▼ 58,7%' / 1.9 → '▲ 1,9pp'"""
    try:
        v = float(valor)
        signo = "▲" if v >= 0 else "▼"
        abs_v = abs(v)
        if es_porcentaje:
            return f"{signo} {abs_v:.1f}%".replace(".", ",")
        else:
            return f"{signo} {abs_v:.1f}pp".replace(".", ",")
    except (TypeError, ValueError):
        return "—"


def _formatear_informe_para_narrativa(informe: dict) -> str:
    """
    Convierte el dict del orquestador a texto pre-formateado para Claude.
    Claude recibe texto con números escritos → los copia sin inventar.
    """
    if not informe:
        return "Sin datos disponibles."

    lineas = []
    lineas.append("TIPO: informe_completo")
    lineas.append("INSTRUCCIÓN: Este es un informe financiero multi-sección. Narrar TODAS las secciones que aparecen abajo.")
    lineas.append("")
    periodo = informe.get("periodo", {})
    desc_periodo = periodo.get("descripcion", periodo) if isinstance(periodo, dict) else str(periodo)
    lineas.append(f"PERÍODO: {desc_periodo}")
    lineas.append("")

    # --- TOTALES ---
    totales = informe.get("totales", {})
    if totales:
        ing = totales.get("ingresos", {})
        gas = totales.get("gastos", {})
        ret = totales.get("retiros", {})
        dis = totales.get("distribuciones", {})
        neto = totales.get("resultado_neto", {})
        cap_t = totales.get("capital_de_trabajo", {})
        lineas.append("TOTALES GLOBALES:")
        lineas.append(f"  Ingresos:       {_fmt_uyu(ing.get('uyu', 0))} / {_fmt_usd(ing.get('usd', 0))}  ({ing.get('cantidad', 0)} ops)")
        lineas.append(f"  Gastos:         {_fmt_uyu(gas.get('uyu', 0))} / {_fmt_usd(gas.get('usd', 0))}  ({gas.get('cantidad', 0)} ops)")
        lineas.append(f"  Resultado neto: {_fmt_uyu(neto.get('uyu', 0))}")
        lineas.append(f"  Rentabilidad:   {_fmt_pct(neto.get('rentabilidad', 0))}")
        lineas.append(f"  Retiros:        {_fmt_uyu(ret.get('uyu', 0))}  ({ret.get('cantidad', 0)} ops)")
        lineas.append(f"  Distribuciones: {_fmt_uyu(dis.get('uyu', 0))}  ({dis.get('cantidad', 0)} ops)")
        lineas.append(f"  Capital de trabajo: {_fmt_uyu(cap_t.get('uyu', 0))}")
        lineas.append("")

    # --- CAPITAL DE TRABAJO (ratios) ---
    cap = informe.get("capital_trabajo", {})
    if cap:
        lineas.append("RATIOS DE SOSTENIBILIDAD:")
        lineas.append(f"  Capital disponible:             {_fmt_uyu(cap.get('capital_trabajo_uyu', 0))}")
        lineas.append(f"  Ratio extracciones/ingresos:    {_fmt_pct(cap.get('ratio_extracciones_sobre_ingresos', 0))}")
        lineas.append(f"  Ratio extracciones/resultado:   {_fmt_pct(cap.get('ratio_extracciones_sobre_resultado', 0))}")
        lineas.append("")

    # --- POR ÁREA ---
    por_area = informe.get("por_area", [])
    if por_area:
        lineas.append("RESULTADOS POR ÁREA:")
        for a in por_area:
            lineas.append(
                f"  {str(a.get('area', '?')):20s}  "
                f"Ing: {_fmt_uyu(a.get('ingresos_uyu', 0))}  "
                f"Gas: {_fmt_uyu(a.get('gastos_uyu', 0))}  "
                f"Rent: {_fmt_pct(a.get('rentabilidad', 0))}"
            )
        lineas.append("")

    # --- TICKET PROMEDIO ---
    tickets = informe.get("ticket_promedio_por_area", [])
    if tickets:
        lineas.append("TICKET PROMEDIO POR ÁREA (INGRESOS):")
        for t in tickets:
            if t.get("tipo_operacion") == "INGRESO":
                lineas.append(
                    f"  {str(t.get('area', '?')):20s}  "
                    f"Ticket: {_fmt_uyu(t.get('ticket_promedio_uyu', 0))}  "
                    f"({t.get('cantidad', 0)} operaciones)"
                )
        lineas.append("")

    # --- MATRIZ ÁREA × LOCALIDAD ---
    matriz = informe.get("matriz_area_localidad", [])
    if matriz:
        lineas.append("RENTABILIDAD POR ÁREA Y OFICINA:")
        area_actual = None
        for m in matriz:
            area = m.get("area", "?")
            if area != area_actual:
                lineas.append(f"  {area}:")
                area_actual = area
            loc = m.get("localidad", "?")
            lineas.append(
                f"    {str(loc):15s}  "
                f"Ing: {_fmt_uyu(m.get('ingresos_uyu', 0))}  "
                f"Rent: {_fmt_pct(m.get('rentabilidad', 0) or 0)}"
            )
        lineas.append("")

    # --- POR LOCALIDAD ---
    por_loc = informe.get("por_localidad", [])
    if por_loc:
        lineas.append("RESULTADOS POR LOCALIDAD:")
        for loc in por_loc:
            lineas.append(
                f"  {str(loc.get('localidad', '?')):15s}  "
                f"Ing: {_fmt_uyu(loc.get('ingresos_uyu', 0))}  "
                f"Gas: {_fmt_uyu(loc.get('gastos_uyu', 0))}  "
                f"Rent: {_fmt_pct(loc.get('rentabilidad', 0))}"
            )
        lineas.append("")

    # --- DISTRIBUCIONES POR SOCIO ---
    socios = informe.get("distribuciones_por_socio", [])
    if socios:
        lineas.append("DISTRIBUCIONES POR SOCIO:")
        for s in socios:
            total_pesificado = s.get("total_pesificado", s.get("monto_uyu", 0))
            total_dolarizado = s.get("total_dolarizado", s.get("monto_usd", 0))
            monto_uyu = float(s.get("monto_uyu", 0) or 0)
            monto_usd = float(s.get("monto_usd", 0) or 0)
            cantidad = s.get("cantidad", s.get("cantidad_distribuciones", 0))
            partes_originales = []
            if monto_uyu > 0:
                partes_originales.append(f"{_fmt_uyu(monto_uyu)} UYU")
            if monto_usd > 0:
                partes_originales.append(f"{_fmt_usd(monto_usd)} USD")
            detalle_original = f" | Original: {' + '.join(partes_originales)}" if partes_originales else ""
            lineas.append(
                f"  {str(s.get('socio', '?')):15s}  "
                f"{_fmt_uyu(total_pesificado)} / {_fmt_usd(total_dolarizado)}"
                f"{detalle_original}  "
                f"({cantidad} ops)"
            )
        lineas.append("")

    # --- RETIROS POR LOCALIDAD ---
    retiros = informe.get("retiros_por_localidad", [])
    if retiros:
        lineas.append("RETIROS POR LOCALIDAD:")
        for r in retiros:
            usd_real = float(r.get("retiros_usd_real", 0) or 0)
            parte_usd = f" | {_fmt_usd(usd_real)} (USD real)" if usd_real > 0 else ""
            lineas.append(
                f"  {str(r.get('localidad', '?')):15s}  "
                f"{_fmt_uyu(r.get('total_uyu', 0))}{parte_usd}  "
                f"({r.get('cantidad', 0)} ops)"
            )
        lineas.append("")

    # --- EVOLUCIÓN TRIMESTRAL ---
    trimestral = informe.get("evolucion_trimestral", [])
    if trimestral:
        lineas.append("EVOLUCIÓN TRIMESTRAL:")
        for t in trimestral:
            ops = t.get("total_operaciones", 0)
            aviso = "  *** DATOS INCOMPLETOS" if ops < 30 else ""
            lineas.append(
                f"  {str(t.get('trimestre_nombre', '?')):18s}  "
                f"Ing: {_fmt_uyu(t.get('ingresos_uyu', 0))}  "
                f"Rent: {_fmt_pct(t.get('rentabilidad', 0) or 0)}  "
                f"Cap.ret: {_fmt_uyu(t.get('capital_retenido_uyu', 0))}  "
                f"({ops} ops){aviso}"
            )
        lineas.append("")

    # --- EVOLUCIÓN MENSUAL ---
    mensual = informe.get("evolucion_mensual", [])
    if mensual:
        lineas.append("EVOLUCIÓN MENSUAL:")
        for m in mensual:
            mes_num = int(m.get("mes", 0))
            nombre_mes = _NOMBRE_MES.get(mes_num, f"M{mes_num}")
            lineas.append(
                f"  {nombre_mes:5s}  "
                f"Ing: {_fmt_uyu(m.get('ingresos_uyu', 0))}  "
                f"Gas: {_fmt_uyu(m.get('gastos_uyu', 0))}"
            )
        lineas.append("")

    # --- COMPOSICIÓN POR MONEDA ---
    moneda = informe.get("composicion_por_moneda", [])
    if moneda:
        lineas.append("COMPOSICIÓN POR MONEDA:")
        tipo_actual = None
        for m in moneda:
            tipo = m.get("tipo_operacion", "?")
            if tipo != tipo_actual:
                lineas.append(f"  {tipo}:")
                tipo_actual = tipo
            lineas.append(
                f"    {str(m.get('moneda_original', '?')):5s}  "
                f"{_fmt_uyu(m.get('total_uyu', 0))}  "
                f"({_fmt_pct(m.get('porcentaje_tipo', 0))})"
            )
        lineas.append("")

    # --- CONCENTRACIÓN CLIENTES ---
    concentracion = informe.get("concentracion_clientes", [])
    if concentracion:
        lineas.append("CONCENTRACIÓN DE CARTERA:")
        top3 = sum(float(c.get("participacion_pct", 0) or 0) for c in concentracion[:3])
        lineas.append(f"  Top 3 clientes: {_fmt_pct(top3)} de la facturación")
        if len(concentracion) >= 10:
            top10 = float(concentracion[-1].get("participacion_acumulada_pct", 0) or 0)
            lineas.append(f"  Top 10 clientes: {_fmt_pct(top10)} de la facturación")
        lineas.append("")

    # --- TOP CLIENTES ---
    top_clientes = informe.get("top_clientes", [])
    if top_clientes:
        # Cruzar con concentración para obtener % de participación
        pct_por_cliente = {}
        for c in concentracion:
            pct_por_cliente[c.get("cliente")] = c.get("participacion_pct", 0)
        lineas.append("TOP 10 CLIENTES:")
        for i, c in enumerate(top_clientes, 1):
            cliente = c.get("cliente", "?")
            pct = pct_por_cliente.get(cliente, 0) or 0
            lineas.append(
                f"  {i:2}. {str(cliente)[:30]:30s}  "
                f"{_fmt_uyu(c.get('total_uyu', 0))}  "
                f"({_fmt_pct(pct)}, {c.get('cantidad_operaciones', 0)} ops)"
            )
        lineas.append("")

    # --- TOP PROVEEDORES ---
    top_proveedores = informe.get("top_proveedores", [])
    if top_proveedores:
        lineas.append("TOP 10 PROVEEDORES:")
        for i, p in enumerate(top_proveedores, 1):
            lineas.append(
                f"  {i:2}. {str(p.get('proveedor', '?'))[:30]:30s}  "
                f"{_fmt_uyu(p.get('total_uyu', 0))}  "
                f"({p.get('cantidad_operaciones', 0)} ops)"
            )
        lineas.append("")

    return "\n".join(lineas)


def _formatear_comparativo_para_narrativa(resultado_comparativo: dict) -> str:
    """
    Convierte el dict del comparativo a texto pre-formateado para Claude.
    Incluye ambos períodos + variaciones pre-calculadas escritas como texto.
    """
    if not resultado_comparativo:
        return "Sin datos disponibles."

    periodos = resultado_comparativo.get("periodos", [])
    variaciones = resultado_comparativo.get("variaciones", {})
    clientes_mov = resultado_comparativo.get("clientes_movimiento", {})

    if len(periodos) < 2:
        return "Datos de comparativo incompletos."

    p_ant = periodos[0]
    p_act = periodos[1]
    per_ant_info = p_ant.get("periodo", {})
    per_act_info = p_act.get("periodo", {})
    per_ant = per_ant_info.get("descripcion", "Período anterior") if isinstance(per_ant_info, dict) else str(per_ant_info)
    per_act = per_act_info.get("descripcion", "Período actual") if isinstance(per_act_info, dict) else str(per_act_info)

    lineas = []
    lineas.append(f"COMPARATIVO: {per_ant} vs {per_act}")
    lineas.append("")

    # --- TOTALES CON VARIACIONES ---
    tot_ant = p_ant.get("totales", {})
    tot_act = p_act.get("totales", {})
    lineas.append("TOTALES GLOBALES:")
    for concepto, label in [
        ("ingresos", "Ingresos"),
        ("gastos", "Gastos"),
        ("retiros", "Retiros"),
        ("distribuciones", "Distribuciones"),
    ]:
        v_ant = _fmt_uyu((tot_ant.get(concepto) or {}).get("uyu", 0))
        v_act = _fmt_uyu((tot_act.get(concepto) or {}).get("uyu", 0))
        var = variaciones.get(f"{concepto}_uyu", {})
        delta = _fmt_delta(var.get("porcentual", 0), es_porcentaje=True)
        abs_delta = _fmt_uyu(var.get("absoluta", 0))
        lineas.append(f"  {label:15s}  {per_ant}: {v_ant}  →  {per_act}: {v_act}  ({delta}, {abs_delta})")

    neto_ant = tot_ant.get("resultado_neto", {})
    neto_act = tot_act.get("resultado_neto", {})
    rent_ant = _fmt_pct(neto_ant.get("rentabilidad", 0))
    rent_act = _fmt_pct(neto_act.get("rentabilidad", 0))
    rent_delta = _fmt_delta(variaciones.get("rentabilidad_pp", 0))
    lineas.append(f"  {'Rentabilidad':15s}  {per_ant}: {rent_ant}  →  {per_act}: {rent_act}  ({rent_delta})")
    lineas.append("")

    # --- POR ÁREA CON VARIACIONES ---
    areas_ant = {x.get("area"): x for x in p_ant.get("por_area", [])}
    areas_act = {x.get("area"): x for x in p_act.get("por_area", [])}
    var_areas = variaciones.get("por_area", {})
    todas_areas = sorted(set(areas_ant) | set(areas_act))
    if todas_areas:
        lineas.append("POR ÁREA:")
        for area in todas_areas:
            a = areas_ant.get(area, {})
            b = areas_act.get(area, {})
            v = var_areas.get(area, {})
            ing_delta = _fmt_delta(v.get("ingresos_porcentual", 0), es_porcentaje=True)
            gas_delta = _fmt_delta(v.get("gastos_porcentual", 0), es_porcentaje=True)
            r_delta = _fmt_delta(v.get("rentabilidad_pp", 0))
            lineas.append(
                f"  {str(area):20s}  "
                f"Ing {per_ant}: {_fmt_uyu(a.get('ingresos_uyu', 0))}  "
                f"Ing {per_act}: {_fmt_uyu(b.get('ingresos_uyu', 0))}  "
                f"Var ing: {ing_delta}  "
                f"Gas {per_ant}: {_fmt_uyu(a.get('gastos_uyu', 0))}  "
                f"Gas {per_act}: {_fmt_uyu(b.get('gastos_uyu', 0))}  "
                f"Var gas: {gas_delta}  "
                f"Rent {per_ant}: {_fmt_pct(a.get('rentabilidad', 0))}  "
                f"Rent {per_act}: {_fmt_pct(b.get('rentabilidad', 0))}  "
                f"Δrent: {r_delta}"
            )
        lineas.append("")

    # --- TICKET PROMEDIO POR ÁREA COMPARADO ---
    var_tickets = variaciones.get("ticket_promedio_por_area", {})
    tickets_ant = {(x.get("area"), x.get("tipo_operacion")): x for x in p_ant.get("ticket_promedio_por_area", [])}
    tickets_act = {(x.get("area"), x.get("tipo_operacion")): x for x in p_act.get("ticket_promedio_por_area", [])}
    if tickets_ant or tickets_act:
        lineas.append("TICKET PROMEDIO POR ÁREA (COMPARADO):")
        claves_ticket = sorted(set(tickets_ant) | set(tickets_act), key=lambda x: (str(x[0]), str(x[1])))
        for area, tipo in claves_ticket:
            t_ant = tickets_ant.get((area, tipo), {})
            t_act = tickets_act.get((area, tipo), {})
            v = (var_tickets.get(area, {}) or {}).get(tipo, {})
            delta = _fmt_delta(v.get("ticket_porcentual", 0), es_porcentaje=True)
            lineas.append(
                f"  {str(area):20s} {str(tipo):10s}  "
                f"{per_ant}: {_fmt_uyu(t_ant.get('ticket_promedio_uyu', 0))}  "
                f"{per_act}: {_fmt_uyu(t_act.get('ticket_promedio_uyu', 0))}  "
                f"Var: {delta}"
            )
        lineas.append("")

    # --- MATRIZ ÁREA × LOCALIDAD COMPARADA ---
    matriz_ant = {(x.get("area"), x.get("localidad")): x for x in p_ant.get("matriz_area_localidad", [])}
    matriz_act = {(x.get("area"), x.get("localidad")): x for x in p_act.get("matriz_area_localidad", [])}
    if matriz_ant or matriz_act:
        lineas.append("RENTABILIDAD POR ÁREA Y OFICINA (COMPARADO):")
        claves = sorted(set(matriz_ant) | set(matriz_act))
        area_actual = None
        for (area, loc) in claves:
            if area != area_actual:
                lineas.append(f"  {area}:")
                area_actual = area
            a = matriz_ant.get((area, loc), {})
            b = matriz_act.get((area, loc), {})
            r_ant = float(a.get("rentabilidad") or 0)
            r_act = float(b.get("rentabilidad") or 0)
            delta_pp = r_act - r_ant
            delta_str = _fmt_delta(delta_pp)
            lineas.append(
                f"    {str(loc):15s}  "
                f"{per_ant}: {_fmt_pct(r_ant)}  "
                f"{per_act}: {_fmt_pct(r_act)}  "
                f"Δ: {delta_str}"
            )
        lineas.append("")

    # --- POR LOCALIDAD CON VARIACIONES ---
    var_loc = variaciones.get("por_localidad", {})
    loc_ant = {x.get("localidad"): x for x in p_ant.get("por_localidad", [])}
    loc_act = {x.get("localidad"): x for x in p_act.get("por_localidad", [])}
    if loc_ant or loc_act:
        lineas.append("POR LOCALIDAD:")
        for loc in sorted(set(loc_ant) | set(loc_act)):
            a = loc_ant.get(loc, {})
            b = loc_act.get(loc, {})
            v = var_loc.get(loc, {})
            delta = _fmt_delta(v.get("ingresos_porcentual", 0), es_porcentaje=True)
            r_delta = _fmt_delta(v.get("rentabilidad_pp", 0))
            lineas.append(
                f"  {str(loc):15s}  "
                f"Ing {per_ant}: {_fmt_uyu(a.get('ingresos_uyu', 0))}  "
                f"Ing {per_act}: {_fmt_uyu(b.get('ingresos_uyu', 0))}  "
                f"Var: {delta}  "
                f"Rent {per_ant}: {_fmt_pct(a.get('rentabilidad', 0))}  "
                f"Rent {per_act}: {_fmt_pct(b.get('rentabilidad', 0))}  "
                f"Δrent: {r_delta}"
            )
        lineas.append("")

    # --- DISTRIBUCIONES POR SOCIO CON VARIACIONES ---
    var_socios = variaciones.get("por_socio", {})
    socios_ant = {x.get("socio"): x for x in p_ant.get("distribuciones_por_socio", [])}
    socios_act = {x.get("socio"): x for x in p_act.get("distribuciones_por_socio", [])}
    if socios_ant or socios_act:
        lineas.append("DISTRIBUCIONES POR SOCIO:")
        for socio in sorted(set(socios_ant) | set(socios_act)):
            a = socios_ant.get(socio, {})
            b = socios_act.get(socio, {})
            v = var_socios.get(socio, {})
            delta = _fmt_delta(v.get("porcentual", 0), es_porcentaje=True)
            total_ant = a.get("total_pesificado", a.get("monto_uyu", 0))
            total_act = b.get("total_pesificado", b.get("monto_uyu", 0))
            lineas.append(
                f"  {str(socio):15s}  "
                f"{per_ant}: {_fmt_uyu(total_ant)}  "
                f"{per_act}: {_fmt_uyu(total_act)}  "
                f"Var: {delta}"
            )
        lineas.append("")

    # --- TRIMESTRAL CON VARIACIONES ---
    var_trim = variaciones.get("por_trimestre", {})
    trim_ant = {x.get("trimestre"): x for x in p_ant.get("evolucion_trimestral", [])}
    trim_act = {x.get("trimestre"): x for x in p_act.get("evolucion_trimestral", [])}
    nombres_trim = {1: "Q1 (Ene-Mar)", 2: "Q2 (Abr-Jun)", 3: "Q3 (Jul-Sep)", 4: "Q4 (Oct-Dic)"}
    if trim_ant or trim_act:
        lineas.append("EVOLUCIÓN TRIMESTRAL COMPARADA:")
        for q in sorted(set(trim_ant) | set(trim_act)):
            a = trim_ant.get(q, {})
            b = trim_act.get(q, {})
            nombre = nombres_trim.get(q, f"Q{q}")
            v = var_trim.get(f"Q{q}", {})
            solo_ant = v.get("solo_en_ant", False)
            solo_act = v.get("solo_en_act", False)
            ops_act = b.get("total_operaciones", 0)
            aviso = ""
            if solo_ant:
                aviso = f"  *** SOLO EN {per_ant} — {per_act} sin datos"
            elif solo_act:
                aviso = f"  *** SOLO EN {per_act}"
            elif ops_act and ops_act < 30:
                aviso = f"  *** DATOS INCOMPLETOS EN {per_act} ({ops_act} ops)"
            delta_ing = _fmt_delta(v.get("ingresos_porcentual", 0), es_porcentaje=True)
            delta_rent = _fmt_delta(v.get("rentabilidad_pp", 0))
            lineas.append(
                f"  {nombre:18s}  "
                f"{per_ant}: {_fmt_uyu(a.get('ingresos_uyu', 0))} / {_fmt_pct(a.get('rentabilidad', 0) or 0)}  "
                f"{per_act}: {_fmt_uyu(b.get('ingresos_uyu', 0))} / {_fmt_pct(b.get('rentabilidad', 0) or 0)}  "
                f"Var: {delta_ing} / {delta_rent}{aviso}"
            )
        lineas.append("")

    # --- TOP CLIENTES COMPARADO ---
    top_ant = {x.get("cliente"): x for x in p_ant.get("top_clientes", [])}
    top_act = {x.get("cliente"): x for x in p_act.get("top_clientes", [])}
    # Concentración para % participación
    conc_act = {x.get("cliente"): x for x in p_act.get("concentracion_clientes", [])}
    if top_act:
        lineas.append(f"TOP 10 CLIENTES {per_act} (con movimiento de ranking):")
        for i, c in enumerate(p_act.get("top_clientes", []), 1):
            cliente = c.get("cliente", "?")
            en_ant = f"también en top {per_ant}" if cliente in top_ant else f"NUEVO en top {per_act}"
            pct = conc_act.get(cliente, {}).get("participacion_pct", 0) or 0
            lineas.append(
                f"  {i:2}. {str(cliente)[:30]:30s}  "
                f"{_fmt_uyu(c.get('total_uyu', 0))}  "
                f"({_fmt_pct(pct)})  [{en_ant}]"
            )
        lineas.append("")

    # --- CLIENTES NUEVOS Y PERDIDOS ---
    perdidos = clientes_mov.get("perdidos", [])
    nuevos = clientes_mov.get("nuevos", [])
    lineas.append("MOVIMIENTO DE CARTERA:")
    lineas.append(f"  Clientes perdidos (en {per_ant} pero no en {per_act}): {len(perdidos)}")
    if perdidos:
        for c in perdidos[:5]:
            lineas.append(f"    - {c.get('cliente', '?')}: {_fmt_uyu(c.get('total_uyu', 0))}")
    lineas.append(f"  Clientes nuevos (en {per_act} pero no en {per_ant}): {len(nuevos)}")
    if nuevos:
        for c in nuevos[:5]:
            lineas.append(f"    - {c.get('cliente', '?')}: {_fmt_uyu(c.get('total_uyu', 0))}")
    lineas.append("")

    # --- COMPOSICIÓN MONEDA COMPARADA ---
    mon_ant = {}
    for m in p_ant.get("composicion_por_moneda", []):
        mon_ant[(m.get("tipo_operacion"), m.get("moneda_original"))] = m
    mon_act = {}
    for m in p_act.get("composicion_por_moneda", []):
        mon_act[(m.get("tipo_operacion"), m.get("moneda_original"))] = m
    if mon_ant or mon_act:
        lineas.append("COMPOSICIÓN POR MONEDA COMPARADA:")
        tipo_actual = None
        for (tipo, moneda) in sorted(set(mon_ant) | set(mon_act)):
            if tipo != tipo_actual:
                lineas.append(f"  {tipo}:")
                tipo_actual = tipo
            a = mon_ant.get((tipo, moneda), {})
            b = mon_act.get((tipo, moneda), {})
            lineas.append(
                f"    {str(moneda):5s}  "
                f"{per_ant}: {_fmt_uyu(a.get('total_uyu', 0))} ({_fmt_pct(a.get('porcentaje_tipo', 0))})  "
                f"{per_act}: {_fmt_uyu(b.get('total_uyu', 0))} ({_fmt_pct(b.get('porcentaje_tipo', 0))})"
            )
        lineas.append("")

    # --- CAPITAL DE TRABAJO COMPARADO ---
    cap_ant = p_ant.get("capital_trabajo", {})
    cap_act = p_act.get("capital_trabajo", {})
    if cap_ant or cap_act:
        lineas.append("CAPITAL DE TRABAJO COMPARADO:")
        lineas.append(
            f"  Capital disponible  {per_ant}: {_fmt_uyu(cap_ant.get('capital_trabajo_uyu', 0))}  "
            f"{per_act}: {_fmt_uyu(cap_act.get('capital_trabajo_uyu', 0))}"
        )
        lineas.append(
            f"  Ratio extracciones  {per_ant}: {_fmt_pct(cap_ant.get('ratio_extracciones_sobre_resultado', 0))}  "
            f"{per_act}: {_fmt_pct(cap_act.get('ratio_extracciones_sobre_resultado', 0))}"
        )
        lineas.append("")

    return "\n".join(lineas)


# ══════════════════════════════════════════════════════════════
# EJECUTOR PRINCIPAL
# ══════════════════════════════════════════════════════════════

def ejecutar_informe(db: Session, pregunta: str) -> Optional[dict]:
    """
    Ejecuta un informe financiero completo usando multi-query.

    Detecta el periodo de la pregunta, ejecuta 9 queries independientes,
    y combina los resultados en un JSON estructurado.

    Args:
        db: Session de SQLAlchemy.
        pregunta: Pregunta del usuario.

    Returns:
        Dict estructurado con todas las secciones del informe,
        o None si no pudo extraer periodo (el flujo normal se encargara).
    """
    periodo = extraer_periodo_informe(pregunta)
    if periodo is None:
        logger.warning("Orquestador: no pudo extraer periodo de la pregunta")
        return None

    # Comparativo: delegar
    if periodo.get("tipo") == "comparativo":
        return ejecutar_informe_comparativo(db, pregunta, periodo)

    params = {
        "fecha_desde": periodo["fecha_desde"],
        "fecha_hasta": periodo["fecha_hasta"],
    }

    logger.info(
        f"Orquestador: ejecutando informe para {periodo.get('descripcion', '?')} "
        f"({params['fecha_desde']} a {params['fecha_hasta']})"
    )

    # Ejecutar las 9 queries
    try:
        # Core (si falla una de estas, no hay informe consistente)
        filas_tipo = _ejecutar_query(db, _query_totales_por_tipo(), params)
        filas_area = _ejecutar_query(db, _query_operativo_por_area(), params)
        filas_dist = _ejecutar_query(db, _query_distribuciones_por_socio(), params)
        filas_ret = _ejecutar_query(db, _query_retiros_por_localidad(), params)
        filas_loc = _ejecutar_query(db, _query_desglose_por_localidad(), params)
        filas_mes = _ejecutar_query(db, _query_evolucion_mensual(), params)
        filas_moneda = _ejecutar_query(db, _query_composicion_por_moneda(), params)
        filas_clientes = _ejecutar_query(db, _query_top_clientes(), params)
        filas_proveedores = _ejecutar_query(db, _query_top_proveedores(), params)
    except Exception as e:
        logger.error(f"Orquestador: error ejecutando queries — {e}", exc_info=True)
        return None

    # Secciones opcionales (si fallan, no se aborta el informe)
    query_retiros_socio = _query_retiros_por_socio()
    if query_retiros_socio is None:
        logger.info("Orquestador: retiros_por_socio no disponible (operaciones.RETIRO no tiene socio_id)")
    filas_ret_socio = _ejecutar_query_opcional(db, query_retiros_socio, params, "retiros_por_socio")
    filas_matriz = _ejecutar_query_opcional(db, _query_matriz_area_localidad(), params, "matriz_area_localidad")
    filas_ticket = _ejecutar_query_opcional(db, _query_ticket_promedio_por_area(), params, "ticket_promedio_por_area")
    filas_concentracion = _ejecutar_query_opcional(db, _query_concentracion_clientes(), params, "concentracion_clientes")
    filas_capital = _ejecutar_query_opcional(db, _query_capital_trabajo(), params, "capital_trabajo")
    filas_trimestral = _ejecutar_query_opcional(db, _query_evolucion_trimestral(), params, "evolucion_trimestral")

    # Ensamblar resultado
    totales = _ensamblar_totales(filas_tipo)
    por_area = _ensamblar_por_area(filas_area)
    distribuciones = _ensamblar_distribuciones(filas_dist)
    retiros = _ensamblar_retiros(filas_ret)
    retiros_por_socio = _ensamblar_retiros_por_socio(filas_ret_socio)
    por_localidad = _ensamblar_por_localidad(filas_loc)
    evolucion_mensual = _ensamblar_evolucion_mensual(filas_mes)
    composicion_moneda = _ensamblar_composicion_por_moneda(filas_moneda)
    top_clientes = _ensamblar_top_clientes(filas_clientes)
    top_proveedores = _ensamblar_top_proveedores(filas_proveedores)
    matriz_area_loc = _ensamblar_matriz_area_localidad(filas_matriz)
    ticket_promedio = _ensamblar_ticket_promedio(filas_ticket)
    concentracion_cli = _ensamblar_concentracion_clientes(filas_concentracion)
    capital_trabajo = _ensamblar_capital_trabajo(filas_capital)
    evolucion_trim = _ensamblar_evolucion_trimestral(filas_trimestral)

    # Validar completitud
    if not totales:
        logger.warning("Orquestador: totales vacios — periodo sin operaciones?")

    resultado = {
        "tipo": "informe_completo",
        "periodo": periodo,
        "totales": totales,
        "por_area": por_area,
        "distribuciones_por_socio": distribuciones,
        "retiros_por_localidad": retiros,
        "retiros_por_socio": retiros_por_socio,
        "por_localidad": por_localidad,
        "evolucion_mensual": evolucion_mensual,
        "composicion_por_moneda": composicion_moneda,
        "top_clientes": top_clientes,
        "top_proveedores": top_proveedores,
        "matriz_area_localidad": matriz_area_loc,
        "ticket_promedio_por_area": ticket_promedio,
        "concentracion_clientes": concentracion_cli,
        "capital_trabajo": capital_trabajo,
        "evolucion_trimestral": evolucion_trim,
    }

    total_filas = (
        len(filas_tipo) + len(filas_area) + len(filas_dist) + len(filas_ret) +
        len(filas_loc) + len(filas_mes) + len(filas_moneda) +
        len(filas_clientes) + len(filas_proveedores) +
        len(filas_matriz) + len(filas_ticket) + len(filas_concentracion) +
        len(filas_capital) + len(filas_trimestral) + len(filas_ret_socio)
    )
    logger.info(
        f"Orquestador: informe ensamblado — {total_filas} filas totales "
        f"({len(filas_tipo)} tipos, {len(filas_area)} areas, "
        f"{len(filas_dist)} distribuciones, {len(filas_ret)} retiros, "
        f"{len(filas_loc)} localidades, {len(filas_mes)} meses, "
        f"{len(filas_moneda)} monedas, {len(filas_clientes)} clientes, "
        f"{len(filas_proveedores)} proveedores)"
    )

    return resultado


def ejecutar_informe_comparativo(
    db: Session, pregunta: str, periodo_info: Optional[dict] = None
) -> Optional[dict]:
    """
    Ejecuta informes para 2 periodos y calcula variaciones.

    Args:
        db: Session de SQLAlchemy.
        pregunta: Pregunta del usuario.
        periodo_info: Dict con tipo=comparativo y lista de periodos (opcional,
                      se extrae de la pregunta si no se provee).

    Returns:
        Dict con ambos informes y variaciones, o None si falla.
    """
    if periodo_info is None:
        periodo_info = extraer_periodo_informe(pregunta)
    if periodo_info is None or periodo_info.get("tipo") != "comparativo":
        return None

    periodos = periodo_info["periodos"]
    if len(periodos) < 2:
        return None

    informes = []
    for p in periodos:
        params = {"fecha_desde": p["fecha_desde"], "fecha_hasta": p["fecha_hasta"]}
        try:
            # Core obligatorio por período
            filas_tipo = _ejecutar_query(db, _query_totales_por_tipo(), params)
            filas_area = _ejecutar_query(db, _query_operativo_por_area(), params)
            filas_dist = _ejecutar_query(db, _query_distribuciones_por_socio(), params)
            filas_ret = _ejecutar_query(db, _query_retiros_por_localidad(), params)
            filas_loc = _ejecutar_query(db, _query_desglose_por_localidad(), params)
            filas_mes = _ejecutar_query(db, _query_evolucion_mensual(), params)
            filas_moneda = _ejecutar_query(db, _query_composicion_por_moneda(), params)
            filas_clientes = _ejecutar_query(db, _query_top_clientes(), params)
            filas_proveedores = _ejecutar_query(db, _query_top_proveedores(), params)
        except Exception as e:
            logger.error(f"Orquestador comparativo: error para periodo {p} — {e}")
            return None

        informes.append({
            "periodo": p,
            "totales": _ensamblar_totales(filas_tipo),
            "por_area": _ensamblar_por_area(filas_area),
            "distribuciones_por_socio": _ensamblar_distribuciones(filas_dist),
            "retiros_por_localidad": _ensamblar_retiros(filas_ret),
            "retiros_por_socio": [],
            "por_localidad": _ensamblar_por_localidad(filas_loc),
            "evolucion_mensual": _ensamblar_evolucion_mensual(filas_mes),
            "composicion_por_moneda": _ensamblar_composicion_por_moneda(filas_moneda),
            "top_clientes": _ensamblar_top_clientes(filas_clientes),
            "top_proveedores": _ensamblar_top_proveedores(filas_proveedores),
            "matriz_area_localidad": [],
            "ticket_promedio_por_area": [],
            "concentracion_clientes": [],
            "capital_trabajo": {},
            "evolucion_trimestral": [],
        })

    # Enriquecer cada período con secciones opcionales SIN romper comparativo
    for i, p in enumerate(periodos):
        params = {"fecha_desde": p["fecha_desde"], "fecha_hasta": p["fecha_hasta"]}
        filas_ret_socio = _ejecutar_query_opcional(db, _query_retiros_por_socio(), params, "retiros_por_socio")
        filas_matriz = _ejecutar_query_opcional(db, _query_matriz_area_localidad(), params, "matriz_area_localidad")
        filas_ticket = _ejecutar_query_opcional(db, _query_ticket_promedio_por_area(), params, "ticket_promedio_por_area")
        filas_concentracion = _ejecutar_query_opcional(db, _query_concentracion_clientes(), params, "concentracion_clientes")
        filas_capital = _ejecutar_query_opcional(db, _query_capital_trabajo(), params, "capital_trabajo")
        filas_trimestral = _ejecutar_query_opcional(db, _query_evolucion_trimestral(), params, "evolucion_trimestral")

        informes[i]["retiros_por_socio"] = _ensamblar_retiros_por_socio(filas_ret_socio)
        informes[i]["matriz_area_localidad"] = _ensamblar_matriz_area_localidad(filas_matriz)
        informes[i]["ticket_promedio_por_area"] = _ensamblar_ticket_promedio(filas_ticket)
        informes[i]["concentracion_clientes"] = _ensamblar_concentracion_clientes(filas_concentracion)
        informes[i]["capital_trabajo"] = _ensamblar_capital_trabajo(filas_capital)
        informes[i]["evolucion_trimestral"] = _ensamblar_evolucion_trimestral(filas_trimestral)

    # Clientes nuevos y perdidos entre períodos
    p_ant = periodos[0]
    p_act = periodos[1]
    params_clientes = {
        "fecha_desde_ant": p_ant["fecha_desde"],
        "fecha_hasta_ant": p_ant["fecha_hasta"],
        "fecha_desde_act": p_act["fecha_desde"],
        "fecha_hasta_act": p_act["fecha_hasta"],
    }
    try:
        queries_mov = _query_clientes_nuevos_perdidos()
        filas_perdidos = _ejecutar_query(db, queries_mov["perdidos"], params_clientes)
        filas_nuevos = _ejecutar_query(db, queries_mov["nuevos"], params_clientes)
    except Exception as e:
        logger.error(f"Orquestador comparativo: error en clientes movimiento — {e}")
        filas_perdidos = []
        filas_nuevos = []
    clientes_movimiento = _ensamblar_clientes_movimiento(filas_perdidos, filas_nuevos)

    # Calcular variaciones entre periodo[0] y periodo[1]
    variaciones = _calcular_variaciones(informes[0], informes[1])

    logger.info(
        f"Orquestador: informe comparativo ensamblado — "
        f"{periodos[0].get('descripcion', '?')} vs {periodos[1].get('descripcion', '?')}"
    )

    return {
        "tipo": "informe_comparativo",
        "periodos": informes,
        "variaciones": variaciones,
        "clientes_movimiento": clientes_movimiento,
    }


def _calcular_variaciones(informe_ant: dict, informe_act: dict) -> dict:
    """
    Calcula variaciones entre dos períodos para todas las secciones disponibles.

    Args:
        informe_ant: Informe completo del periodo anterior.
        informe_act: Informe completo del periodo actual.

    Returns:
        Dict con variaciones globales, por área, por localidad y por socio.
    """
    variaciones = {}

    def _normalizar_totales(informe: dict) -> dict:
        """
        Normaliza la estructura de entrada para soportar dos formatos:
        1) Informe completo: {"totales": {...}, ...}
        2) Totales directos: {"ingresos": {...}, "gastos": {...}, ...}
        """
        if not isinstance(informe, dict):
            return {}
        totales = informe.get("totales")
        if isinstance(totales, dict):
            return totales
        return informe

    def _monto_uyu(totales: dict, concepto: str) -> float:
        """Obtiene monto UYU de un concepto con tolerancia a formatos mixtos."""
        valor = totales.get(concepto, 0)
        if isinstance(valor, dict):
            return (valor.get("uyu", 0)) or 0
        return valor or 0

    # Totales globales
    totales_ant = _normalizar_totales(informe_ant)
    totales_act = _normalizar_totales(informe_act)
    for concepto in ("ingresos", "gastos", "retiros", "distribuciones"):
        ant = _monto_uyu(totales_ant, concepto)
        act = _monto_uyu(totales_act, concepto)
        absoluta = round(act - ant, 2)
        porcentual = round(absoluta / ant * 100, 1) if ant != 0 else 0
        variaciones[f"{concepto}_uyu"] = {
            "absoluta": absoluta,
            "porcentual": porcentual,
        }

    # Rentabilidad global (puntos porcentuales)
    rent_ant = totales_ant.get("resultado_neto", {}).get("rentabilidad", 0) or 0
    rent_act = totales_act.get("resultado_neto", {}).get("rentabilidad", 0) or 0
    variaciones["rentabilidad_pp"] = round(rent_act - rent_ant, 1)

    # Por área
    areas_ant = {x["area"]: x for x in informe_ant.get("por_area", [])}
    areas_act = {x["area"]: x for x in informe_act.get("por_area", [])}
    todas_areas = set(areas_ant) | set(areas_act)
    variaciones["por_area"] = {}
    for area in sorted(todas_areas):
        a = areas_ant.get(area, {})
        b = areas_act.get(area, {})
        ing_ant = a.get("ingresos_uyu", 0) or 0
        ing_act = b.get("ingresos_uyu", 0) or 0
        gas_ant = a.get("gastos_uyu", 0) or 0
        gas_act = b.get("gastos_uyu", 0) or 0
        rent_a = a.get("rentabilidad", 0) or 0
        rent_b = b.get("rentabilidad", 0) or 0
        variaciones["por_area"][area] = {
            "ingresos_absoluta": round(ing_act - ing_ant, 2),
            "ingresos_porcentual": round((ing_act - ing_ant) / ing_ant * 100, 1) if ing_ant != 0 else 0,
            "gastos_absoluta": round(gas_act - gas_ant, 2),
            "gastos_porcentual": round((gas_act - gas_ant) / gas_ant * 100, 1) if gas_ant != 0 else 0,
            "rentabilidad_pp": round(rent_b - rent_a, 1),
        }

    # Por localidad
    loc_ant = {x["localidad"]: x for x in informe_ant.get("por_localidad", [])}
    loc_act = {x["localidad"]: x for x in informe_act.get("por_localidad", [])}
    variaciones["por_localidad"] = {}
    for loc in sorted(set(loc_ant) | set(loc_act)):
        a = loc_ant.get(loc, {})
        b = loc_act.get(loc, {})
        ing_ant = a.get("ingresos_uyu", 0) or 0
        ing_act = b.get("ingresos_uyu", 0) or 0
        rent_a = a.get("rentabilidad", 0) or 0
        rent_b = b.get("rentabilidad", 0) or 0
        variaciones["por_localidad"][loc] = {
            "ingresos_absoluta": round(ing_act - ing_ant, 2),
            "ingresos_porcentual": round((ing_act - ing_ant) / ing_ant * 100, 1) if ing_ant != 0 else 0,
            "rentabilidad_pp": round(rent_b - rent_a, 1),
        }

    # Por socio (distribuciones)
    socios_ant = {x["socio"]: x for x in informe_ant.get("distribuciones_por_socio", [])}
    socios_act = {x["socio"]: x for x in informe_act.get("distribuciones_por_socio", [])}
    variaciones["por_socio"] = {}
    for socio in sorted(set(socios_ant) | set(socios_act)):
        a = socios_ant.get(socio, {})
        b = socios_act.get(socio, {})
        m_ant = a.get("total_pesificado", a.get("monto_uyu", 0)) or 0
        m_act = b.get("total_pesificado", b.get("monto_uyu", 0)) or 0
        variaciones["por_socio"][socio] = {
            "absoluta": round(m_act - m_ant, 2),
            "porcentual": round((m_act - m_ant) / m_ant * 100, 1) if m_ant != 0 else 0,
        }

    # Ticket promedio por área (comparativo por área y tipo_operacion)
    tickets_ant = {(x.get("area"), x.get("tipo_operacion")): x for x in informe_ant.get("ticket_promedio_por_area", [])}
    tickets_act = {(x.get("area"), x.get("tipo_operacion")): x for x in informe_act.get("ticket_promedio_por_area", [])}
    variaciones["ticket_promedio_por_area"] = {}
    claves_ticket = sorted(set(tickets_ant) | set(tickets_act), key=lambda x: (str(x[0]), str(x[1])))
    for area, tipo in claves_ticket:
        a = tickets_ant.get((area, tipo), {})
        b = tickets_act.get((area, tipo), {})
        ticket_ant = a.get("ticket_promedio_uyu", 0) or 0
        ticket_act = b.get("ticket_promedio_uyu", 0) or 0
        variaciones["ticket_promedio_por_area"].setdefault(area, {})
        variaciones["ticket_promedio_por_area"][area][tipo] = {
            "ticket_absoluta": round(ticket_act - ticket_ant, 2),
            "ticket_porcentual": round((ticket_act - ticket_ant) / ticket_ant * 100, 1) if ticket_ant != 0 else 0,
            "cantidad_ant": a.get("cantidad", 0) or 0,
            "cantidad_act": b.get("cantidad", 0) or 0,
        }

    # Por trimestre
    trim_ant = {x["trimestre"]: x for x in informe_ant.get("evolucion_trimestral", [])}
    trim_act = {x["trimestre"]: x for x in informe_act.get("evolucion_trimestral", [])}
    nombres_q = {1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4"}
    variaciones["por_trimestre"] = {}
    for q in sorted(set(trim_ant) | set(trim_act)):
        a = trim_ant.get(q, {})
        b = trim_act.get(q, {})
        ing_ant = a.get("ingresos_uyu", 0) or 0
        ing_act = b.get("ingresos_uyu", 0) or 0
        rent_a = a.get("rentabilidad", 0) or 0
        rent_b = b.get("rentabilidad", 0) or 0
        variaciones["por_trimestre"][nombres_q.get(q, f"Q{q}")] = {
            "ingresos_absoluta": round(ing_act - ing_ant, 2),
            "ingresos_porcentual": round((ing_act - ing_ant) / ing_ant * 100, 1) if ing_ant != 0 else 0,
            "rentabilidad_pp": round(rent_b - rent_a, 1),
            "solo_en_ant": ing_ant > 0 and ing_act == 0,
            "solo_en_act": ing_ant == 0 and ing_act > 0,
        }

    return variaciones
