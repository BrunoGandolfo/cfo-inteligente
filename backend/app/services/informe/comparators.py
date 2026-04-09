"""Cálculo de variaciones entre períodos para informes comparativos."""


def _calcular_variaciones(informe_ant: dict, informe_act: dict) -> dict:
    """
    Calcula variaciones entre dos períodos para todas las secciones disponibles.

    Returns:
        Dict con variaciones globales, por área, por localidad y por socio.
    """
    variaciones = {}

    def _normalizar_totales(informe: dict) -> dict:
        if not isinstance(informe, dict):
            return {}
        totales = informe.get("totales")
        if isinstance(totales, dict):
            return totales
        return informe

    def _monto_uyu(totales: dict, concepto: str) -> float:
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

    # Ticket promedio por área
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
