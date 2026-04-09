"""Detección de intención de informe y extracción de período temporal."""

import re
from datetime import date
from typing import Optional

from app.core.logger import get_logger

logger = get_logger(__name__)


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
    "informe de",
    "informe del",
    "reporte de",
    "reporte del",
    "resumen de",
    "resumen del",
    "informe",
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


def es_pregunta_informe(pregunta: str) -> bool:
    """
    Detecta si la pregunta solicita un informe/resumen financiero completo.

    Busca keywords de informe y excluye preguntas puntuales que contienen
    dimensiones especificas (por area, por mes, etc.).
    """
    p = pregunta.lower().strip()

    tiene_keyword = any(kw in p for kw in _KEYWORDS_INFORME)
    if not tiene_keyword:
        return False

    tiene_exclusion = any(kw in p for kw in _KEYWORDS_EXCLUSION)
    if tiene_exclusion:
        return False

    return True


def extraer_periodo_informe(pregunta: str) -> Optional[dict]:
    """
    Extrae el periodo temporal de una pregunta de informe.

    Soporta:
    - Año completo: "informe del 2025"
    - Semestre: "informe del primer semestre 2024"
    - Trimestre: "informe del Q1 2025"
    - Comparativo: "informe comparativo 2024 vs 2025"
    - Sin año: retorna None
    """
    p = pregunta.lower()

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

    anio = anios[0] if anios else None
    if anio is None:
        if any(kw in p for kw in ["este año", "este ano", "el año", "el ano", "del año", "del ano"]):
            anio = date.today().year
        else:
            tiene_mes = any(mes in p for mes in _MESES_MAP)
            if tiene_mes:
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

    # Detectar rango de meses
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

    # Detectar mes individual
    for nombre_mes, numero_mes in _MESES_MAP.items():
        if re.search(rf"\b{re.escape(nombre_mes)}\b", p):
            return {
                "tipo": "periodo",
                "anio": anio,
                "fecha_desde": f"{anio}-{numero_mes:02d}-01",
                "fecha_hasta": f"{anio}-{numero_mes:02d}-{_ultimo_dia_mes(anio, numero_mes):02d}",
                "descripcion": f"{nombre_mes} {anio}",
            }

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
