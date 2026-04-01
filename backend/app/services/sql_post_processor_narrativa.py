"""
Post-procesador narrativo para resultados SQL dinámicos.

Convierte el resultado crudo de ejecutar_consulta_cfo() (list[dict]) a texto
pre-formateado con números escritos.  Claude recibe texto → los copia sin
recalcular ni inventar.
"""

import logging

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════
# RED DE SEGURIDAD BIMONETARIA
# ══════════════════════════════════════════════════════════════

# Columnas que representan montos o conteos y se deben sumar al agregar.
_COLS_SUMABLES = {
    "total_pesificado", "total_uyu", "monto_uyu",
    "total_dolarizado", "total_usd", "monto_usd",
    "ingresos_uyu", "gastos_uyu", "retiros_uyu", "distribuciones_uyu",
    "ingresos_usd", "gastos_usd", "retiros_usd", "distribuciones_usd",
    "neto_uyu", "resultado_neto_uyu",
    "cantidad", "count", "cantidad_operaciones", "operaciones",
}

_COLS_TICKET_EXISTENTE = {"ticket_promedio", "ticket_promedio_uyu", "promedio"}
_COLS_MONTO_TICKET = [
    "total_pesificado", "ingresos_uyu", "total_uyu", "monto_total",
    "monto_uyu", "monto", "total", "total_ingresos", "importe",
]
_COLS_CANTIDAD_TICKET = [
    "operaciones", "cantidad", "cantidad_operaciones", "cant",
    "total_operaciones", "ops", "count",
]

_COLS_PARTICIPACION = ["participacion_pct", "pct_total", "porcentaje", "pct_monto"]
_COLS_MONTO_PARTICIPACION = [
    "ingresos_uyu", "total_uyu", "monto_uyu", "total_pesificado",
    "ingresos", "total", "monto",
]
_COLS_DIMENSION_RANKING = {"cliente", "proveedor"}

# Columnas candidatas a dimensión principal (primera que exista).
_COLS_DIMENSION = [
    "localidad", "area", "nombre", "socio", "cliente", "proveedor",
]

# Columnas temporales (no deben fusionarse entre sí ni formatearse como miles).
_COLS_TEMPORALES = {
    "anio", "año", "year", "periodo", "semestre", "trimestre", "quarter",
    "mes", "month", "fecha",
}

_MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}


def _es_col_temporal(col: str) -> bool:
    """Detecta columnas temporales por nombre canónico."""
    return str(col).lower() in _COLS_TEMPORALES


def _to_float(val: object) -> float:
    """Convierte Decimal/int/str a float. Retorna 0.0 si falla."""
    try:
        return float(val or 0)
    except (TypeError, ValueError):
        return 0.0


def _pre_agregar_por_dimension(datos: list) -> list:
    """
    Red de seguridad: si los datos tienen filas duplicadas por dimensión
    (misma localidad/área/socio con moneda_original distinta), las agrega
    en Python antes de formatear.

    Ejemplo: si llegan 2 filas para Montevideo (una UYU, una USD),
    las combina en 1 fila con total_uyu sumado y usd_real calculado.
    """
    if not datos or len(datos) < 2:
        return datos

    # Preservar orden de columnas según primera aparición.
    columnas_ordenadas = []
    for row in datos:
        for col in row.keys():
            if col not in columnas_ordenadas:
                columnas_ordenadas.append(col)
    columnas = set(columnas_ordenadas)

    # Solo actuar si existe moneda_original
    if "moneda_original" not in columnas:
        return datos

    # Identificar columna de dimensión principal
    dim_col = None
    for c in _COLS_DIMENSION:
        if c in columnas:
            dim_col = c
            break
    if dim_col is None:
        return datos

    # Incluir columnas temporales en la clave para no mezclar años/períodos.
    cols_temporales = [c for c in columnas_ordenadas if _es_col_temporal(c)]
    key_cols = cols_temporales + [dim_col]

    # Verificar si realmente hay duplicados por la clave completa.
    claves = [tuple(row.get(c) for c in key_cols) for row in datos]
    if len(claves) == len(set(claves)):
        return datos  # sin duplicados por clave temporal+dimensión — no tocar

    # Agrupar por clave completa, preservando orden de aparición.
    grupos: dict[tuple, list] = {}
    orden: list[tuple] = []
    for row in datos:
        clave = tuple(row.get(c) for c in key_cols)
        if clave not in grupos:
            grupos[clave] = []
            orden.append(clave)
        grupos[clave].append(row)

    resultado = []
    for clave in orden:
        filas = grupos[clave]
        fila_nueva = {col: val for col, val in zip(key_cols, clave)}

        for col in columnas_ordenadas:
            if col in key_cols or col in ("moneda_original", "monto_original"):
                continue
            if col in _COLS_SUMABLES:
                total = sum(_to_float(f.get(col, 0)) for f in filas)
                fila_nueva[col] = round(total, 2)
            else:
                # Tomar primer valor no-None
                for f in filas:
                    v = f.get(col)
                    if v is not None:
                        fila_nueva[col] = v
                        break
                else:
                    fila_nueva[col] = None

        # USD real: sumar monto_original de filas donde moneda_original='USD'
        if "monto_original" in columnas:
            usd_real = sum(
                _to_float(f.get("monto_original", 0))
                for f in filas
                if str(f.get("moneda_original", "")).upper() == "USD"
            )
            if usd_real > 0:
                fila_nueva["usd_real"] = round(usd_real, 2)

        resultado.append(fila_nueva)

    return resultado


def _etiquetar_meses(datos: list[dict]) -> list[dict]:
    """
    Convierte columnas numéricas de mes (1-12) a nombre en español.
    Si encuentra 'mes' con valor entero 1-12, lo reemplaza por el nombre.
    Si encuentra 'mes' y 'anio', genera una columna 'periodo' con formato 'marzo 2025'.
    No modifica otras columnas.
    """
    if not datos:
        return datos

    cols_mes = [c for c in datos[0].keys() if c.lower() in ("mes", "mes_num", "numero_mes")]
    if not cols_mes:
        return datos

    col_mes = cols_mes[0]
    col_anio = None
    for c in datos[0].keys():
        if c.lower() in ("anio", "año", "anio_num"):
            col_anio = c
            break

    for fila in datos:
        val = fila.get(col_mes)
        if isinstance(val, int):
            mes_num = val
        elif isinstance(val, float) and val.is_integer():
            mes_num = int(val)
        else:
            mes_num = None

        if mes_num is not None and 1 <= mes_num <= 12:
            nombre_mes = _MESES_ES[mes_num]
            if col_anio and fila.get(col_anio):
                fila["periodo"] = f"{nombre_mes} {int(fila[col_anio])}"
            fila[col_mes] = nombre_mes

    return datos


def _es_numero(val: object) -> bool:
    """True si el valor puede convertirse a número."""
    try:
        float(val)
        return True
    except (TypeError, ValueError):
        return False


def _calcular_ticket_promedio(datos: list[dict]) -> list[dict]:
    """
    Calcula ticket promedio por fila cuando existen monto y cantidad.

    Idempotente: si la fila ya trae ticket promedio, no lo recalcula.
    """
    if not datos:
        return datos

    for row in datos:
        if any(row.get(col) is not None for col in _COLS_TICKET_EXISTENTE):
            continue

        monto_col = next(
            (c for c in _COLS_MONTO_TICKET if c in row and row.get(c) is not None and _es_numero(row.get(c))),
            None,
        )
        cantidad_col = next(
            (c for c in _COLS_CANTIDAD_TICKET if c in row and row.get(c) is not None and _es_numero(row.get(c))),
            None,
        )
        if not monto_col or not cantidad_col:
            continue

        cantidad = _to_float(row.get(cantidad_col, 0))
        if cantidad <= 0:
            continue

        monto = _to_float(row.get(monto_col, 0))
        row["ticket_promedio"] = round(monto / cantidad, 2)

    return datos


def _calcular_composicion_moneda(datos: list[dict]) -> dict:
    """
    Calcula composición porcentual por moneda.

    Prioriza total_pesificado (base homogénea en UYU). Si no existe, usa
    monto_original y marca advertencia por mezcla de unidades.
    """
    if not datos:
        return {}

    columnas = set()
    for row in datos:
        columnas.update(row.keys())

    if "moneda_original" not in columnas:
        return {}

    monedas_presentes = {
        str(r.get("moneda_original", "")).upper().strip()
        for r in datos
        if r.get("moneda_original") is not None
    }
    monedas_presentes = {m for m in monedas_presentes if m}
    if len(monedas_presentes) < 2:
        return {}

    base_col = None
    advertencia = None
    if "total_pesificado" in columnas:
        base_col = "total_pesificado"
    elif "monto_original" in columnas:
        base_col = "monto_original"
        advertencia = (
            "Base en monto_original: las monedas tienen unidades distintas. "
            "Interpretar con cautela."
        )
    else:
        return {}

    totales = {}
    for row in datos:
        moneda = str(row.get("moneda_original", "")).upper().strip()
        if not moneda:
            continue
        valor = _to_float(row.get(base_col, 0))
        totales[moneda] = totales.get(moneda, 0.0) + valor

    total_general = sum(totales.values())
    if total_general <= 0:
        return {}

    porcentajes = {
        moneda: round((valor * 100.0 / total_general), 1)
        for moneda, valor in totales.items()
    }

    return {
        "base_col": base_col,
        "advertencia": advertencia,
        "por_moneda": porcentajes,
    }


def _calcular_concentracion_acumulada(datos: list[dict]) -> dict:
    """
    Calcula concentración acumulada Top 3/5/10 usando participaciones existentes.

    Usa porcentajes preexistentes y respeta el orden de filas (ranking recibido).
    """
    if not datos or len(datos) <= 3:
        return {}

    valores_pct = []
    for row in datos:
        col_pct = next(
            (c for c in _COLS_PARTICIPACION if c in row and row.get(c) is not None and _es_numero(row.get(c))),
            None,
        )
        if not col_pct:
            continue
        valores_pct.append(_to_float(row.get(col_pct, 0)))

    base_pct = "precalculada"

    # Si no hay % explícitos, calcular concentración sobre total mostrado.
    if len(valores_pct) <= 3:
        columnas = set()
        for row in datos:
            columnas.update(row.keys())

        col_monto = next((c for c in _COLS_MONTO_PARTICIPACION if c in columnas), None)
        if col_monto:
            total = sum(_to_float(r.get(col_monto, 0)) for r in datos)
            if total > 0:
                valores_pct = [
                    round(_to_float(r.get(col_monto, 0)) * 100.0 / total, 1)
                    for r in datos
                ]
                base_pct = "total_mostrado"

    if len(valores_pct) <= 3:
        return {}

    # Asegurar que Top N realmente tome los mayores porcentajes.
    valores_pct = sorted(valores_pct, reverse=True)

    concentracion = {
        "top_3_pct": round(sum(valores_pct[:3]), 1),
    }
    if len(valores_pct) >= 5:
        concentracion["top_5_pct"] = round(sum(valores_pct[:5]), 1)
    if len(valores_pct) >= 10:
        concentracion["top_10_pct"] = round(sum(valores_pct[:10]), 1)
    if base_pct == "total_mostrado":
        concentracion["sobre_total_mostrado"] = True

    return concentracion


def _es_subset_ranking(datos: list[dict], columnas: set, pregunta: str = "") -> bool:
    """
    Heurística para detectar ranking/subset (ej. TOP con LIMIT).

    Si es un ranking chico por cliente/proveedor, evitar participación automática
    para no confundir % sobre total mostrado con % sobre total global.
    """
    if not datos:
        return False

    tiene_dimension_ranking = any(col in columnas for col in _COLS_DIMENSION_RANKING)
    pocas_filas = len(datos) <= 10
    pregunta_l = (pregunta or "").lower()
    menciona_ranking = any(t in pregunta_l for t in ("top", "ranking", "principales", "mayores"))

    return (tiene_dimension_ranking and pocas_filas) or (menciona_ranking and pocas_filas)


def post_procesar_resultado_sql(datos: list, pregunta: str = "") -> str:
    """
    Convierte el resultado crudo de ejecutar_consulta_cfo() a texto pre-formateado.
    Claude recibe texto con números escritos → los copia sin recalcular ni inventar.

    Detecta automáticamente las columnas disponibles y calcula derivados en Python.
    Regla absoluta: si es un número, lo calcula Python. Si es texto, lo redacta Claude.
    """
    if not datos:
        return "Sin datos disponibles para esta consulta."

    # Etiquetar meses numéricos antes de cualquier otro procesamiento.
    datos = _etiquetar_meses(datos)

    # Red de seguridad bimonetaria
    datos = _pre_agregar_por_dimension(datos)

    # Derivados críticos (Python calcula, Claude narra)
    datos = _calcular_ticket_promedio(datos)
    composicion_moneda = _calcular_composicion_moneda(datos)
    concentracion_acumulada = _calcular_concentracion_acumulada(datos)

    lineas = []

    # --- Helpers de formato (mismos que informe_orquestador.py) ---
    def fmt_uyu(v: object):
        try:
            return f"${int(round(float(v))):,}".replace(",", ".")
        except (TypeError, ValueError):
            return "$0"

    def fmt_usd(v: object):
        try:
            return f"US$ {int(round(float(v))):,}".replace(",", ".")
        except (TypeError, ValueError):
            return "US$ 0"

    def fmt_pct(v: object):
        try:
            return f"{float(v):.1f}%".replace(".", ",")
        except (TypeError, ValueError):
            return "0,0%"

    def fmt_num(v: object):
        try:
            f = float(v)
            if f == int(f):
                return f"{int(f):,}".replace(",", ".")
            return f"{f:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (TypeError, ValueError):
            return str(v)

    # --- Detectar columnas disponibles ---
    columnas = set(datos[0].keys()) if datos else set()
    es_subset_ranking = _es_subset_ranking(datos, columnas, pregunta=pregunta)
    se_mostro_participacion = False

    # --- Calcular total general para porcentajes ---
    col_principal = next(
        (c for c in ["ingresos_uyu", "total_uyu", "monto_uyu", "total_pesificado", "ingresos"]
         if c in columnas),
        None,
    )
    total_general = None
    if col_principal and len(datos) > 1:
        try:
            total_general = sum(float(row.get(col_principal, 0) or 0) for row in datos)
        except (TypeError, ValueError):
            total_general = None

    # --- Formatear cada fila ---
    for i, row in enumerate(datos):
        partes = []

        # Identificador de la fila
        for id_col in [
            "nombre", "area", "localidad", "socio", "cliente", "proveedor",
            "mes", "nombre_mes", "trimestre", "trimestre_nombre", "periodo",
            "moneda_original", "tipo_operacion",
        ]:
            if id_col in row and row[id_col] is not None:
                partes.append(f"{row[id_col]}")
                break

        # Ingresos
        for col in ["ingresos_uyu", "ingresos", "total_ingresos"]:
            if col in row and row[col] is not None:
                partes.append(f"Ingresos: {fmt_uyu(row[col])}")
                break

        # Gastos
        for col in ["gastos_uyu", "gastos", "total_gastos"]:
            if col in row and row[col] is not None:
                partes.append(f"Gastos: {fmt_uyu(row[col])}")
                break

        # Resultado neto
        for col in ["resultado_neto", "resultado_neto_uyu", "neto"]:
            if col in row and row[col] is not None:
                partes.append(f"Resultado neto: {fmt_uyu(row[col])}")
                break

        # Rentabilidad — NUNCA recalcular, usar la columna si existe
        rent_found = False
        for col in ["rentabilidad", "rentabilidad_pct", "margen"]:
            if col in row and row[col] is not None:
                partes.append(f"Rentabilidad: {fmt_pct(row[col])}")
                rent_found = True
                break
        if not rent_found:
            # Si no viene la columna pero hay ingresos y gastos, calcular en Python
            ing_col = next((c for c in ["ingresos_uyu", "ingresos"] if c in row), None)
            gas_col = next((c for c in ["gastos_uyu", "gastos"] if c in row), None)
            if ing_col and gas_col:
                try:
                    ing = float(row[ing_col] or 0)
                    gas = float(row[gas_col] or 0)
                    if ing > 0:
                        rent = round((ing - gas) * 100.0 / ing, 1)
                        partes.append(f"Rentabilidad: {fmt_pct(rent)}")
                except Exception as e:
                    logger.warning(f"Error calculando rentabilidad fila: {e}")

        # Monto principal (distribuciones, retiros, etc.)
        for col in ["total_uyu", "monto_uyu", "total_pesificado", "monto"]:
            if col in row and row[col] is not None and col not in ["ingresos_uyu", "gastos_uyu"]:
                partes.append(f"Monto: {fmt_uyu(row[col])}")
                break

        # USD real desde monto_original cuando moneda es USD
        moneda = row.get("moneda_original", "")
        monto_orig = row.get("monto_original")
        if monto_orig is not None and str(moneda).upper() == "USD":
            partes.append(f"USD original: {fmt_usd(monto_orig)}")

        # USD — siempre desde la columna real, nunca calculado
        for col in ["ingresos_usd", "gastos_usd", "total_usd", "monto_usd", "total_dolarizado"]:
            if col in row and row[col] is not None:
                partes.append(f"USD: {fmt_usd(row[col])}")
                break

        # Porcentaje sobre total — calcular en Python si hay total_general
        pct_found = False
        for col in _COLS_PARTICIPACION:
            if col in row and row[col] is not None:
                partes.append(f"Participación: {fmt_pct(row[col])}")
                pct_found = True
                se_mostro_participacion = True
                break
        if not pct_found:
            if (not es_subset_ranking) and total_general and col_principal and col_principal in row:
                try:
                    v = float(row[col_principal] or 0)
                    if total_general > 0:
                        pct = round(v * 100.0 / total_general, 1)
                        partes.append(f"Participación: {fmt_pct(pct)}")
                        se_mostro_participacion = True
                except Exception as e:
                    logger.warning(f"Error calculando participación fila: {e}")

        # Ticket promedio
        for col in ["ticket_promedio", "ticket_promedio_uyu", "promedio"]:
            if col in row and row[col] is not None:
                partes.append(f"Ticket promedio: {fmt_uyu(row[col])}")
                break

        # Conteos
        for col in ["operaciones", "cantidad", "ops", "count", "cantidad_operaciones"]:
            if col in row and row[col] is not None:
                partes.append(f"Operaciones: {fmt_num(row[col])}")
                break

        # Tipo de cambio
        for col in ["tipo_cambio", "tipo_cambio_promedio", "tc_promedio", "tc_efectivo"]:
            if col in row and row[col] is not None:
                try:
                    partes.append(f"Tipo de cambio: ${float(row[col]):.4f}")
                except Exception as e:
                    logger.warning(f"Error formateando tipo de cambio: {e}")
                break

        # Cualquier otra columna numérica no cubierta
        columnas_cubiertas = {
            "nombre", "area", "localidad", "socio", "cliente", "proveedor",
            "mes", "nombre_mes", "trimestre", "trimestre_nombre", "periodo",
            "moneda_original", "tipo_operacion",
            "ingresos_uyu", "ingresos", "total_ingresos",
            "gastos_uyu", "gastos", "total_gastos",
            "resultado_neto", "resultado_neto_uyu", "neto",
            "rentabilidad", "rentabilidad_pct", "margen",
            "total_uyu", "monto_uyu", "total_pesificado", "monto",
            "ingresos_usd", "gastos_usd", "total_usd", "monto_usd", "total_dolarizado",
            "participacion_pct", "pct_total", "porcentaje", "pct_monto",
            "ticket_promedio", "ticket_promedio_uyu", "promedio",
            "operaciones", "cantidad", "ops", "count", "cantidad_operaciones",
            "tipo_cambio", "tipo_cambio_promedio", "tc_promedio", "tc_efectivo",
            "monto_original",
        }
        for col, val in row.items():
            if col not in columnas_cubiertas and val is not None:
                if _es_col_temporal(col):
                    partes.append(f"{col}: {val}")
                    continue
                try:
                    float(val)
                    partes.append(f"{col}: {fmt_num(val)}")
                except (TypeError, ValueError):
                    if val:
                        partes.append(f"{col}: {val}")

        lineas.append("  " + "  |  ".join(partes) if partes else f"  Fila {i+1}: sin datos")

    # --- Totales al final si hay múltiples filas ---
    if len(datos) > 1:
        lineas.append("")

        if col_principal and total_general:
            lineas.append(f"  TOTAL: {fmt_uyu(total_general)}")

            # Rentabilidad global si hay ingresos y gastos
            ing_col = next((c for c in ["ingresos_uyu", "ingresos"] if c in columnas), None)
            gas_col = next((c for c in ["gastos_uyu", "gastos"] if c in columnas), None)
            if ing_col and gas_col:
                try:
                    ing_total = sum(float(r.get(ing_col, 0) or 0) for r in datos)
                    gas_total = sum(float(r.get(gas_col, 0) or 0) for r in datos)
                    if ing_total > 0:
                        rent_global = round((ing_total - gas_total) * 100.0 / ing_total, 1)
                        lineas.append(f"  RENTABILIDAD GLOBAL: {fmt_pct(rent_global)}")
                except Exception as e:
                    logger.warning(f"Error calculando rentabilidad global: {e}")

            # Si hay columnas de moneda y monto_original, calcular USD real
            if "moneda_original" in columnas and "monto_original" in columnas:
                try:
                    total_usd_real = sum(
                        float(r.get("monto_original", 0) or 0)
                        for r in datos
                        if str(r.get("moneda_original", "")).upper() == "USD"
                    )
                    total_uyu_pesos = sum(
                        float(r.get("monto_original", 0) or 0)
                        for r in datos
                        if str(r.get("moneda_original", "")).upper() == "UYU"
                    )
                    if total_usd_real > 0:
                        lineas.append(f"  TOTAL USD (operaciones en dólares): {fmt_usd(total_usd_real)}")
                    if total_uyu_pesos > 0:
                        lineas.append(f"  TOTAL UYU (operaciones en pesos): {fmt_uyu(total_uyu_pesos)}")
                except Exception as e:
                    logger.warning(f"Error calculando totales USD/UYU reales: {e}")

        # Ticket promedio global
        monto_col_global = next((c for c in _COLS_MONTO_TICKET if c in columnas), None)
        cantidad_col_global = next((c for c in _COLS_CANTIDAD_TICKET if c in columnas), None)
        if monto_col_global and cantidad_col_global:
            try:
                monto_total = sum(_to_float(r.get(monto_col_global, 0)) for r in datos)
                cantidad_total = sum(_to_float(r.get(cantidad_col_global, 0)) for r in datos)
                if cantidad_total > 0:
                    ticket_global = round(monto_total / cantidad_total, 2)
                    lineas.append(f"  TICKET PROMEDIO GLOBAL: {fmt_uyu(ticket_global)}")
            except Exception as e:
                logger.warning(f"Error calculando ticket promedio global: {e}")

        # Composición por moneda (sobre base homogénea si existe)
        if composicion_moneda:
            try:
                por_moneda = composicion_moneda.get("por_moneda", {})
                orden = []
                for prioridad in ["UYU", "USD"]:
                    if prioridad in por_moneda:
                        orden.append(prioridad)
                for moneda in sorted(por_moneda.keys()):
                    if moneda not in orden:
                        orden.append(moneda)

                comp_txt = " / ".join(f"{fmt_pct(por_moneda[m])} en {m}" for m in orden)
                if composicion_moneda.get("base_col") == "total_pesificado":
                    lineas.append(f"  COMPOSICIÓN: {comp_txt} (sobre base pesificada)")
                else:
                    lineas.append(f"  COMPOSICIÓN: {comp_txt}")
                    advertencia = composicion_moneda.get("advertencia")
                    if advertencia:
                        lineas.append(f"  Nota composición: {advertencia}")
            except Exception as e:
                logger.warning(f"Error formateando composición por moneda: {e}")

        # Concentración acumulada (Top 3/5/10)
        if concentracion_acumulada:
            try:
                partes_concentracion = []
                if "top_3_pct" in concentracion_acumulada:
                    partes_concentracion.append(f"Top 3 = {fmt_pct(concentracion_acumulada['top_3_pct'])}")
                if "top_5_pct" in concentracion_acumulada:
                    partes_concentracion.append(f"Top 5 = {fmt_pct(concentracion_acumulada['top_5_pct'])}")
                if "top_10_pct" in concentracion_acumulada:
                    partes_concentracion.append(f"Top 10 = {fmt_pct(concentracion_acumulada['top_10_pct'])}")
                if partes_concentracion:
                    sufijo = ""
                    if concentracion_acumulada.get("sobre_total_mostrado"):
                        sufijo = " (sobre total mostrado)"
                    lineas.append(f"  CONCENTRACIÓN: {' | '.join(partes_concentracion)}{sufijo}")
            except Exception as e:
                logger.warning(f"Error formateando concentración acumulada: {e}")

        if es_subset_ranking and se_mostro_participacion:
            lineas.append("  Nota participación: porcentaje reportado sobre elementos mostrados (ranking/top), no sobre total global.")

    return "\n".join(lineas)
