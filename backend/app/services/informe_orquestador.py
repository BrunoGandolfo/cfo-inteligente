"""
Orquestador Multi-Query para Informes Financieros Completos.

Cuando un usuario pide "informe financiero completo", el pipeline normal
genera 1 SQL que inevitablemente pierde datos. Este modulo resuelve el
problema ejecutando queries independientes y combinando los resultados.

Los submódulos viven en app/services/informe/:
- detector.py    — detección de intención y extracción de período
- queries.py     — queries SQL predefinidas y ejecutor
- assemblers.py  — ensamblado de secciones y resumen
- formatters.py  — formateo para narrativa de Claude
- comparators.py — cálculo de variaciones entre períodos
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.core.logger import get_logger

# Re-exports para compatibilidad con imports existentes
from app.services.informe.detector import (  # noqa: F401
    es_pregunta_informe,
    extraer_periodo_informe,
)
from app.services.informe.queries import (  # noqa: F401
    _ejecutar_query,
    _ejecutar_query_opcional,
    _query_capital_trabajo,
    _query_clientes_nuevos_perdidos,
    _query_composicion_por_moneda,
    _query_concentracion_clientes,
    _query_desglose_por_localidad,
    _query_distribuciones_por_socio,
    _query_evolucion_mensual,
    _query_evolucion_trimestral,
    _query_matriz_area_localidad,
    _query_operativo_por_area,
    _query_retiros_por_localidad,
    _query_retiros_por_socio,
    _query_ticket_promedio_por_area,
    _query_top_clientes,
    _query_top_proveedores,
    _query_totales_por_tipo,
)
from app.services.informe.assemblers import (  # noqa: F401
    _ensamblar_capital_trabajo,
    _ensamblar_clientes_movimiento,
    _ensamblar_composicion_por_moneda,
    _ensamblar_concentracion_clientes,
    _ensamblar_distribuciones,
    _ensamblar_evolucion_mensual,
    _ensamblar_evolucion_trimestral,
    _ensamblar_matriz_area_localidad,
    _ensamblar_por_area,
    _ensamblar_por_localidad,
    _ensamblar_retiros,
    _ensamblar_retiros_por_socio,
    _ensamblar_ticket_promedio,
    _ensamblar_top_clientes,
    _ensamblar_top_proveedores,
    _ensamblar_totales,
    _serializar_filas,
    _serializar_valor,
    computar_resumen_informe,
)
from app.services.informe.formatters import (  # noqa: F401
    _fmt_delta,
    _fmt_pct,
    _fmt_usd,
    _fmt_uyu,
    _formatear_comparativo_para_narrativa,
    _formatear_informe_para_narrativa,
)
from app.services.informe.comparators import (  # noqa: F401
    _calcular_variaciones,
)

logger = get_logger(__name__)


# ══════════════════════════════════════════════════════════════
# EJECUTOR PRINCIPAL
# ══════════════════════════════════════════════════════════════

def ejecutar_informe(db: Session, pregunta: str) -> Optional[dict]:
    """
    Ejecuta un informe financiero completo usando multi-query.

    Detecta el periodo de la pregunta, ejecuta queries independientes,
    y combina los resultados en un JSON estructurado.
    """
    periodo = extraer_periodo_informe(pregunta)
    if periodo is None:
        logger.warning("Orquestador: no pudo extraer periodo de la pregunta")
        return None

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

    try:
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

    filas_ret_socio = _ejecutar_query_opcional(db, _query_retiros_por_socio(), params, "retiros_por_socio")
    filas_matriz = _ejecutar_query_opcional(db, _query_matriz_area_localidad(), params, "matriz_area_localidad")
    filas_ticket = _ejecutar_query_opcional(db, _query_ticket_promedio_por_area(), params, "ticket_promedio_por_area")
    filas_concentracion = _ejecutar_query_opcional(db, _query_concentracion_clientes(), params, "concentracion_clientes")
    filas_capital = _ejecutar_query_opcional(db, _query_capital_trabajo(), params, "capital_trabajo")
    filas_trimestral = _ejecutar_query_opcional(db, _query_evolucion_trimestral(), params, "evolucion_trimestral")

    resultado = {
        "tipo": "informe_completo",
        "periodo": periodo,
        "totales": _ensamblar_totales(filas_tipo),
        "por_area": _ensamblar_por_area(filas_area),
        "distribuciones_por_socio": _ensamblar_distribuciones(filas_dist),
        "retiros_por_localidad": _ensamblar_retiros(filas_ret),
        "retiros_por_socio": _ensamblar_retiros_por_socio(filas_ret_socio),
        "por_localidad": _ensamblar_por_localidad(filas_loc),
        "evolucion_mensual": _ensamblar_evolucion_mensual(filas_mes),
        "composicion_por_moneda": _ensamblar_composicion_por_moneda(filas_moneda),
        "top_clientes": _ensamblar_top_clientes(filas_clientes),
        "top_proveedores": _ensamblar_top_proveedores(filas_proveedores),
        "matriz_area_localidad": _ensamblar_matriz_area_localidad(filas_matriz),
        "ticket_promedio_por_area": _ensamblar_ticket_promedio(filas_ticket),
        "concentracion_clientes": _ensamblar_concentracion_clientes(filas_concentracion),
        "capital_trabajo": _ensamblar_capital_trabajo(filas_capital),
        "evolucion_trimestral": _ensamblar_evolucion_trimestral(filas_trimestral),
    }

    if not resultado["totales"]:
        logger.warning("Orquestador: totales vacios — periodo sin operaciones?")

    logger.info(f"Orquestador: informe ensamblado para {periodo.get('descripcion', '?')}")
    return resultado


def ejecutar_informe_comparativo(
    db: Session, pregunta: str, periodo_info: Optional[dict] = None
) -> Optional[dict]:
    """Ejecuta informes para 2 periodos y calcula variaciones."""
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

    for i, p in enumerate(periodos):
        params = {"fecha_desde": p["fecha_desde"], "fecha_hasta": p["fecha_hasta"]}
        informes[i]["retiros_por_socio"] = _ensamblar_retiros_por_socio(
            _ejecutar_query_opcional(db, _query_retiros_por_socio(), params, "retiros_por_socio"))
        informes[i]["matriz_area_localidad"] = _ensamblar_matriz_area_localidad(
            _ejecutar_query_opcional(db, _query_matriz_area_localidad(), params, "matriz_area_localidad"))
        informes[i]["ticket_promedio_por_area"] = _ensamblar_ticket_promedio(
            _ejecutar_query_opcional(db, _query_ticket_promedio_por_area(), params, "ticket_promedio_por_area"))
        informes[i]["concentracion_clientes"] = _ensamblar_concentracion_clientes(
            _ejecutar_query_opcional(db, _query_concentracion_clientes(), params, "concentracion_clientes"))
        informes[i]["capital_trabajo"] = _ensamblar_capital_trabajo(
            _ejecutar_query_opcional(db, _query_capital_trabajo(), params, "capital_trabajo"))
        informes[i]["evolucion_trimestral"] = _ensamblar_evolucion_trimestral(
            _ejecutar_query_opcional(db, _query_evolucion_trimestral(), params, "evolucion_trimestral"))

    p_ant, p_act = periodos[0], periodos[1]
    params_clientes = {
        "fecha_desde_ant": p_ant["fecha_desde"], "fecha_hasta_ant": p_ant["fecha_hasta"],
        "fecha_desde_act": p_act["fecha_desde"], "fecha_hasta_act": p_act["fecha_hasta"],
    }
    try:
        queries_mov = _query_clientes_nuevos_perdidos()
        filas_perdidos = _ejecutar_query(db, queries_mov["perdidos"], params_clientes)
        filas_nuevos = _ejecutar_query(db, queries_mov["nuevos"], params_clientes)
    except Exception as e:
        logger.error(f"Orquestador comparativo: error en clientes movimiento — {e}")
        filas_perdidos, filas_nuevos = [], []

    variaciones = _calcular_variaciones(informes[0], informes[1])

    logger.info(
        f"Orquestador: comparativo ensamblado — "
        f"{periodos[0].get('descripcion', '?')} vs {periodos[1].get('descripcion', '?')}"
    )

    return {
        "tipo": "informe_comparativo",
        "periodos": informes,
        "variaciones": variaciones,
        "clientes_movimiento": _ensamblar_clientes_movimiento(filas_perdidos, filas_nuevos),
    }
