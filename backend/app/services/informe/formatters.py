"""Formateo de datos para narrativa de informes financieros."""


_NOMBRE_MES = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic",
}


def _fmt_uyu(valor) -> str:
    """Formatea número como peso uruguayo. Ej: 893075002.92 -> '$893.075.003'"""
    try:
        return f"${int(round(float(valor))):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "$0"


def _fmt_usd(valor) -> str:
    """Formatea número como dólar. Ej: 22838.45 -> 'US$ 22.838'"""
    try:
        return f"US$ {int(round(float(valor))):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "US$ 0"


def _fmt_pct(valor) -> str:
    """Formatea porcentaje. Ej: 67.7 -> '67,7%'"""
    try:
        return f"{float(valor):.1f}%".replace(".", ",")
    except (TypeError, ValueError):
        return "0,0%"


def _fmt_delta(valor, es_porcentaje=False) -> str:
    """Formatea delta con signo. Ej: -58.7 -> 'down 58,7%' / 1.9 -> 'up 1,9pp'"""
    try:
        v = float(valor)
        signo = "\u25b2" if v >= 0 else "\u25bc"
        abs_v = abs(v)
        if es_porcentaje:
            return f"{signo} {abs_v:.1f}%".replace(".", ",")
        else:
            return f"{signo} {abs_v:.1f}pp".replace(".", ",")
    except (TypeError, ValueError):
        return "\u2014"


def _formatear_informe_para_narrativa(informe: dict) -> str:
    """Convierte el dict del orquestador a texto pre-formateado para Claude."""
    if not informe:
        return "Sin datos disponibles."

    lineas = []
    lineas.append("TIPO: informe_completo")
    lineas.append("INSTRUCCION: Este es un informe financiero multi-seccion. Narrar TODAS las secciones que aparecen abajo.")
    lineas.append("")
    periodo = informe.get("periodo", {})
    desc_periodo = periodo.get("descripcion", periodo) if isinstance(periodo, dict) else str(periodo)
    lineas.append(f"PERIODO: {desc_periodo}")
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
        lineas.append(f"  Ratio distribuciones/ingresos:  {_fmt_pct(cap.get('ratio_distribuciones_sobre_ingresos', 0))}")
        lineas.append(f"  Ratio distribuciones/resultado: {_fmt_pct(cap.get('ratio_distribuciones_sobre_resultado', 0))}")
        lineas.append("")

    # --- POR AREA ---
    por_area = informe.get("por_area", [])
    if por_area:
        lineas.append("RESULTADOS POR AREA:")
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
        lineas.append("TICKET PROMEDIO POR AREA (INGRESOS):")
        for t in tickets:
            if t.get("tipo_operacion") == "INGRESO":
                lineas.append(
                    f"  {str(t.get('area', '?')):20s}  "
                    f"Ticket: {_fmt_uyu(t.get('ticket_promedio_uyu', 0))}  "
                    f"({t.get('cantidad', 0)} operaciones)"
                )
        lineas.append("")

    # --- MATRIZ AREA x LOCALIDAD ---
    matriz = informe.get("matriz_area_localidad", [])
    if matriz:
        lineas.append("RENTABILIDAD POR AREA Y OFICINA:")
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

    # --- EVOLUCION TRIMESTRAL ---
    trimestral = informe.get("evolucion_trimestral", [])
    if trimestral:
        lineas.append("EVOLUCION TRIMESTRAL:")
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

    # --- EVOLUCION MENSUAL ---
    mensual = informe.get("evolucion_mensual", [])
    if mensual:
        lineas.append("EVOLUCION MENSUAL:")
        for m in mensual:
            mes_num = int(m.get("mes", 0))
            nombre_mes = _NOMBRE_MES.get(mes_num, f"M{mes_num}")
            lineas.append(
                f"  {nombre_mes:5s}  "
                f"Ing: {_fmt_uyu(m.get('ingresos_uyu', 0))}  "
                f"Gas: {_fmt_uyu(m.get('gastos_uyu', 0))}"
            )
        lineas.append("")

    # --- COMPOSICION POR MONEDA ---
    moneda = informe.get("composicion_por_moneda", [])
    if moneda:
        lineas.append("COMPOSICION POR MONEDA:")
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

    # --- CONCENTRACION CLIENTES ---
    concentracion = informe.get("concentracion_clientes", [])
    if concentracion:
        lineas.append("CONCENTRACION DE CARTERA:")
        top3 = sum(float(c.get("participacion_pct", 0) or 0) for c in concentracion[:3])
        lineas.append(f"  Top 3 clientes: {_fmt_pct(top3)} de la facturacion")
        if len(concentracion) >= 10:
            top10 = float(concentracion[-1].get("participacion_acumulada_pct", 0) or 0)
            lineas.append(f"  Top 10 clientes: {_fmt_pct(top10)} de la facturacion")
        lineas.append("")

    # --- TOP CLIENTES ---
    top_clientes = informe.get("top_clientes", [])
    if top_clientes:
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
    """Convierte el dict del comparativo a texto pre-formateado para Claude."""
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
    per_ant = per_ant_info.get("descripcion", "Periodo anterior") if isinstance(per_ant_info, dict) else str(per_ant_info)
    per_act = per_act_info.get("descripcion", "Periodo actual") if isinstance(per_act_info, dict) else str(per_act_info)

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
        lineas.append(f"  {label:15s}  {per_ant}: {v_ant}  ->  {per_act}: {v_act}  ({delta}, {abs_delta})")

    neto_ant = tot_ant.get("resultado_neto", {})
    neto_act = tot_act.get("resultado_neto", {})
    rent_ant = _fmt_pct(neto_ant.get("rentabilidad", 0))
    rent_act = _fmt_pct(neto_act.get("rentabilidad", 0))
    rent_delta = _fmt_delta(variaciones.get("rentabilidad_pp", 0))
    lineas.append(f"  {'Rentabilidad':15s}  {per_ant}: {rent_ant}  ->  {per_act}: {rent_act}  ({rent_delta})")
    lineas.append("")

    # --- POR AREA CON VARIACIONES ---
    areas_ant = {x.get("area"): x for x in p_ant.get("por_area", [])}
    areas_act = {x.get("area"): x for x in p_act.get("por_area", [])}
    var_areas = variaciones.get("por_area", {})
    todas_areas = sorted(set(areas_ant) | set(areas_act))
    if todas_areas:
        lineas.append("POR AREA:")
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
                f"Drent: {r_delta}"
            )
        lineas.append("")

    # --- TICKET PROMEDIO POR AREA COMPARADO ---
    var_tickets = variaciones.get("ticket_promedio_por_area", {})
    tickets_ant = {(x.get("area"), x.get("tipo_operacion")): x for x in p_ant.get("ticket_promedio_por_area", [])}
    tickets_act = {(x.get("area"), x.get("tipo_operacion")): x for x in p_act.get("ticket_promedio_por_area", [])}
    if tickets_ant or tickets_act:
        lineas.append("TICKET PROMEDIO POR AREA (COMPARADO):")
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

    # --- MATRIZ AREA x LOCALIDAD COMPARADA ---
    matriz_ant = {(x.get("area"), x.get("localidad")): x for x in p_ant.get("matriz_area_localidad", [])}
    matriz_act = {(x.get("area"), x.get("localidad")): x for x in p_act.get("matriz_area_localidad", [])}
    if matriz_ant or matriz_act:
        lineas.append("RENTABILIDAD POR AREA Y OFICINA (COMPARADO):")
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
                f"D: {delta_str}"
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
                f"Drent: {r_delta}"
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
        lineas.append("EVOLUCION TRIMESTRAL COMPARADA:")
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
                aviso = f"  *** SOLO EN {per_ant} - {per_act} sin datos"
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
    conc_act = {x.get("cliente"): x for x in p_act.get("concentracion_clientes", [])}
    if top_act:
        lineas.append(f"TOP 10 CLIENTES {per_act} (con movimiento de ranking):")
        for i, c in enumerate(p_act.get("top_clientes", []), 1):
            cliente = c.get("cliente", "?")
            en_ant = f"tambien en top {per_ant}" if cliente in top_ant else f"NUEVO en top {per_act}"
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

    # --- COMPOSICION MONEDA COMPARADA ---
    mon_ant = {}
    for m in p_ant.get("composicion_por_moneda", []):
        mon_ant[(m.get("tipo_operacion"), m.get("moneda_original"))] = m
    mon_act = {}
    for m in p_act.get("composicion_por_moneda", []):
        mon_act[(m.get("tipo_operacion"), m.get("moneda_original"))] = m
    if mon_ant or mon_act:
        lineas.append("COMPOSICION POR MONEDA COMPARADA:")
        tipo_actual = None
        for (tipo, moneda_val) in sorted(set(mon_ant) | set(mon_act)):
            if tipo != tipo_actual:
                lineas.append(f"  {tipo}:")
                tipo_actual = tipo
            a = mon_ant.get((tipo, moneda_val), {})
            b = mon_act.get((tipo, moneda_val), {})
            lineas.append(
                f"    {str(moneda_val):5s}  "
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
            f"  Ratio distribuciones {per_ant}: {_fmt_pct(cap_ant.get('ratio_distribuciones_sobre_resultado', 0))}  "
            f"{per_act}: {_fmt_pct(cap_act.get('ratio_distribuciones_sobre_resultado', 0))}"
        )
        lineas.append("")

    return "\n".join(lineas)
