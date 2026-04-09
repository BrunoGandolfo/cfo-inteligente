"""Ensamblado de secciones del informe financiero."""

from decimal import Decimal
from typing import Any

from app.core.logger import get_logger

logger = get_logger(__name__)


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


def _ensamblar_totales(filas_tipo: list[dict]) -> dict:
    """Transforma filas de GROUP BY tipo_operacion en dict de totales."""
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

    ing = totales.get("ingresos", {}).get("uyu", 0) or 0
    gas = totales.get("gastos", {}).get("uyu", 0) or 0
    totales["resultado_neto"] = {
        "uyu": round(ing - gas, 2),
        "rentabilidad": round((ing - gas) / ing * 100, 1) if ing > 0 else 0,
    }
    dist = totales.get("distribuciones", {}).get("uyu", 0) or 0
    totales["capital_de_trabajo"] = {
        "uyu": round(ing - gas - dist, 2),
    }

    return totales


def _ensamblar_por_area(filas_area: list[dict]) -> list[dict]:
    """Serializa filas de operativo por area."""
    return _serializar_filas(filas_area)


def _ensamblar_distribuciones(filas_dist: list[dict]) -> list[dict]:
    """Serializa filas de distribuciones por socio."""
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
    """Serializa filas de retiros por socio."""
    return _serializar_filas(filas_ret_socio)


def _ensamblar_por_localidad(filas_loc: list[dict]) -> list[dict]:
    """Serializa desglose por localidad y calcula neto/rentabilidad por oficina."""
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
    """Serializa composición por moneda y agrega % por tipo de operación."""
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
    """Serializa matriz area x localidad."""
    return _serializar_filas(filas)


def _ensamblar_ticket_promedio(filas: list[dict]) -> list[dict]:
    """Serializa ticket promedio por área."""
    return _serializar_filas(filas)


def _ensamblar_concentracion_clientes(filas: list[dict]) -> list[dict]:
    """Serializa concentración de cartera de clientes."""
    return _serializar_filas(filas)


def _ensamblar_capital_trabajo(filas: list[dict]) -> dict:
    """Serializa capital de trabajo (fila unica -> dict)."""
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


def computar_resumen_informe(resultado_informe: dict) -> dict:
    """
    Construye un resumen rico para narrativa de informes.

    Soporta:
    - informe_completo (totales en raiz)
    - informe_comparativo (usa periodos[-1] como base y adjunta variaciones)
    """
    if not isinstance(resultado_informe, dict) or not resultado_informe:
        return {}

    def _as_float(val, default: float = 0.0) -> float:
        try:
            return float(val if val is not None else default)
        except (TypeError, ValueError):
            return float(default)

    def _round_monto(val) -> float:
        return round(_as_float(val), 0)

    def _round_pct(val) -> float:
        return round(_as_float(val), 1)

    informe_base = resultado_informe
    totales = informe_base.get("totales", {})

    if (not totales) and isinstance(resultado_informe.get("periodos"), list) and resultado_informe["periodos"]:
        ultimo_periodo = resultado_informe["periodos"][-1] or {}
        if isinstance(ultimo_periodo, dict):
            informe_base = ultimo_periodo
            totales = ultimo_periodo.get("totales", {}) or {}

    resumen: dict[str, Any] = {}

    if isinstance(totales, dict) and totales:
        ingresos = totales.get("ingresos", {}) or {}
        gastos = totales.get("gastos", {}) or {}
        resultado_neto = totales.get("resultado_neto", {}) or {}
        retiros = totales.get("retiros", {}) or {}
        distribuciones = totales.get("distribuciones", {}) or {}
        capital_trabajo = totales.get("capital_de_trabajo", {}) or {}

        resumen["sumas"] = {
            "ingresos_uyu": _round_monto(ingresos.get("uyu", 0)),
            "gastos_uyu": _round_monto(gastos.get("uyu", 0)),
            "resultado_neto_uyu": _round_monto(resultado_neto.get("uyu", 0)),
            "retiros_uyu": _round_monto(retiros.get("uyu", 0)),
            "distribuciones_uyu": _round_monto(distribuciones.get("uyu", 0)),
            "rentabilidad_pct": _round_pct(resultado_neto.get("rentabilidad", 0)),
            "capital_de_trabajo_uyu": _round_monto(capital_trabajo.get("uyu", 0)),
        }

    concentracion = informe_base.get("concentracion_clientes", [])
    if isinstance(concentracion, list) and concentracion:
        filas_concentracion = sorted(
            [c for c in concentracion if isinstance(c, dict)],
            key=lambda x: _as_float(x.get("ranking", 0))
        )

        if filas_concentracion:
            top_3 = next(
                (c.get("participacion_acumulada_pct") for c in filas_concentracion if int(_as_float(c.get("ranking"))) == 3),
                None,
            )
            top_5 = next(
                (c.get("participacion_acumulada_pct") for c in filas_concentracion if int(_as_float(c.get("ranking"))) == 5),
                None,
            )
            top_10 = next(
                (c.get("participacion_acumulada_pct") for c in filas_concentracion if int(_as_float(c.get("ranking"))) == 10),
                None,
            )

            if top_3 is None:
                top_3 = sum(_as_float(c.get("participacion_pct", 0)) for c in filas_concentracion[:3])
            if top_5 is None and len(filas_concentracion) >= 5:
                top_5 = sum(_as_float(c.get("participacion_pct", 0)) for c in filas_concentracion[:5])
            if top_10 is None and len(filas_concentracion) >= 10:
                top_10 = _as_float(filas_concentracion[9].get("participacion_acumulada_pct", 0))

            resumen_concentracion = {"top_3_pct": _round_pct(top_3)}
            if top_5 is not None:
                resumen_concentracion["top_5_pct"] = _round_pct(top_5)
            if top_10 is not None:
                resumen_concentracion["top_10_pct"] = _round_pct(top_10)
            resumen["concentracion"] = resumen_concentracion

    top_clientes = informe_base.get("top_clientes", [])
    if isinstance(top_clientes, list) and top_clientes:
        participacion_por_cliente = {}
        if isinstance(concentracion, list):
            for fila in concentracion:
                if isinstance(fila, dict):
                    participacion_por_cliente[fila.get("cliente")] = _round_pct(fila.get("participacion_pct", 0))

        resumen["top_clientes"] = []
        for i, c in enumerate(top_clientes, 1):
            if not isinstance(c, dict):
                continue
            resumen["top_clientes"].append({
                "ranking": int(_as_float(c.get("ranking", i), i)),
                "cliente": c.get("cliente", "No especificado"),
                "total_uyu": _round_monto(c.get("total_uyu", 0)),
                "participacion_pct": participacion_por_cliente.get(c.get("cliente"), _round_pct(c.get("participacion_pct", 0))),
                "operaciones": int(_as_float(c.get("cantidad_operaciones", 0))),
            })

    top_proveedores = informe_base.get("top_proveedores", [])
    if isinstance(top_proveedores, list) and top_proveedores:
        resumen["top_proveedores"] = []
        for i, p in enumerate(top_proveedores, 1):
            if not isinstance(p, dict):
                continue
            resumen["top_proveedores"].append({
                "ranking": int(_as_float(p.get("ranking", i), i)),
                "proveedor": p.get("proveedor", "No especificado"),
                "total_uyu": _round_monto(p.get("total_uyu", 0)),
                "operaciones": int(_as_float(p.get("cantidad_operaciones", 0))),
            })

    por_area = informe_base.get("por_area", [])
    if isinstance(por_area, list) and por_area:
        resumen["por_area"] = []
        for fila in por_area:
            if not isinstance(fila, dict):
                continue
            resumen["por_area"].append({
                "area": fila.get("area", "No especificado"),
                "ingresos_uyu": _round_monto(fila.get("ingresos_uyu", 0)),
                "gastos_uyu": _round_monto(fila.get("gastos_uyu", 0)),
                "rentabilidad_pct": _round_pct(fila.get("rentabilidad", 0)),
            })

    por_localidad = informe_base.get("por_localidad", [])
    if isinstance(por_localidad, list) and por_localidad:
        resumen["por_localidad"] = []
        for fila in por_localidad:
            if not isinstance(fila, dict):
                continue
            resumen["por_localidad"].append({
                "localidad": fila.get("localidad", "No especificado"),
                "ingresos_uyu": _round_monto(fila.get("ingresos_uyu", 0)),
                "gastos_uyu": _round_monto(fila.get("gastos_uyu", 0)),
                "rentabilidad_pct": _round_pct(fila.get("rentabilidad", 0)),
            })

    distribuciones_socio = informe_base.get("distribuciones_por_socio", [])
    if isinstance(distribuciones_socio, list) and distribuciones_socio:
        resumen["distribuciones_por_socio"] = []
        for fila in distribuciones_socio:
            if not isinstance(fila, dict):
                continue
            total_pesificado = fila.get("total_pesificado", fila.get("monto_uyu", 0))
            resumen["distribuciones_por_socio"].append({
                "socio": fila.get("socio", "No especificado"),
                "total_pesificado": _round_monto(total_pesificado),
            })

    capital = informe_base.get("capital_trabajo", {})
    if isinstance(capital, dict) and capital:
        resumen["ratios_sostenibilidad"] = {
            "capital_trabajo_uyu": _round_monto(capital.get("capital_trabajo_uyu", 0)),
            "ratio_dist_sobre_ingresos_pct": _round_pct(capital.get("ratio_distribuciones_sobre_ingresos", 0)),
            "ratio_dist_sobre_resultado_pct": _round_pct(capital.get("ratio_distribuciones_sobre_resultado", 0)),
        }

    variaciones = resultado_informe.get("variaciones")
    if isinstance(variaciones, dict) and variaciones:
        resumen["variaciones"] = variaciones

    return resumen
