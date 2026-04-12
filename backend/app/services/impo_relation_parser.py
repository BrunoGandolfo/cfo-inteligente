"""Parser de relaciones normativas extraídas desde notas HTML de IMPO.

Funciones puras: no usan BD, HTTP ni archivos.
"""

import html
import re


_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")

_RELACION_RE = re.compile(
    r"(?P<prefix>(?:(?:Literal|Numeral)\s+[A-Za-z0-9]+\)\s+)?)"
    r"(?P<label>"
    r"Reglamentad[oa]\s+por|"
    r"Redacci[oó]n dada por|"
    r"Agregad[oa]/?s?\s+por|"
    r"Derogad[oa](?:/a)?\s+por|"
    r"Este artículo dio nueva redacción a|"
    r"Ver vigencia|"
    r"Ver"
    r")\s*:\s*"
    r"(?P<body>.*?)(?="
    r"(?:(?:(?:Literal|Numeral)\s+[A-Za-z0-9]+\)\s+)?"
    r"(?:Reglamentad[oa]\s+por|"
    r"Redacci[oó]n dada por|"
    r"Agregado/?s?\s+por|"
    r"Derogado/?a?\s+por|"
    r"Este artículo dio nueva redacción a|"
    r"Ver vigencia|"
    r"Ver)"
    r"\s*:)|$)"
    ,
    re.IGNORECASE | re.DOTALL,
)

_NORMA_REF_RE = re.compile(
    r"(?P<tipo>Ley|Decreto[- ]?Ley|Decreto)\s+N[º°o]?\s*"
    r"(?P<num>[\d.]+)"
    r"(?:/(?P<anio>\d{3,4}))?"
    r"(?:\s+de\s+(?P<fecha>\d{2}/\d{2}/\d{4}))?"
    r"(?:\s+art[ií]culo\s+(?P<articulo>[^,.;]+?))?"
    r"(?=$|[,;])",
    re.IGNORECASE,
)


def _limpiar_texto(texto: str | None) -> str:
    if not texto:
        return ""
    limpio = html.unescape(str(texto))
    limpio = _TAG_RE.sub(" ", limpio)
    limpio = _WS_RE.sub(" ", limpio).strip()
    return limpio


def _normalizar_tipo_norma(tipo: str) -> str:
    tipo_limpio = tipo.lower().replace("-", " ").strip()
    if tipo_limpio == "ley":
        return "LEY"
    if tipo_limpio == "decreto ley":
        return "DECRETO_LEY"
    if tipo_limpio == "decreto":
        return "DECRETO"
    return tipo.upper()


def _convertir_anio_decreto(anio: str) -> int:
    if len(anio) == 4:
        return int(anio)
    if len(anio) == 3:
        return 1000 + int(anio) if anio.startswith("9") else 2000 + int(anio)
    return int(anio)


def parse_norma_ref(texto: str) -> dict | None:
    """Extrae tipo, número, año, fecha y artículo desde una referencia normativa."""
    limpio = _limpiar_texto(texto)
    if not limpio:
        return None
    limpio = limpio.rstrip(" ,.;")

    match = _NORMA_REF_RE.search(limpio)
    if not match:
        return None

    tipo_norma = _normalizar_tipo_norma(match.group("tipo"))
    numero = int(match.group("num").replace(".", ""))
    fecha = match.group("fecha")
    articulo = match.group("articulo")
    if articulo:
        articulo = _WS_RE.sub(" ", articulo).strip()
        articulo = re.split(r"\s*\(", articulo, maxsplit=1)[0].strip()

    anio: int | None
    anio_match = match.group("anio")
    if anio_match:
        anio = _convertir_anio_decreto(anio_match) if tipo_norma == "DECRETO" else int(anio_match)
    elif fecha:
        anio = int(fecha.split("/")[-1])
    else:
        anio = None

    return {
        "tipo_norma": tipo_norma,
        "numero": numero,
        "anio": anio,
        "fecha": fecha,
        "articulo": articulo,
    }


def _extraer_relaciones_desde_fragmento(
    tipo_relacion: str,
    fragmento: str,
    articulo_origen: str | None,
    texto_original: str,
) -> list[dict]:
    relaciones: list[dict] = []
    fragmento = fragmento.rstrip(" ,.;")
    refs = list(_NORMA_REF_RE.finditer(fragmento))
    if not refs and tipo_relacion == "REFERENCIA":
        ref = parse_norma_ref(fragmento)
        if ref:
            refs = [_NORMA_REF_RE.search(fragmento)] if _NORMA_REF_RE.search(fragmento) else []

    for ref_match in refs:
        ref = parse_norma_ref(ref_match.group(0))
        if not ref:
            continue
        relaciones.append(
            {
                "tipo_relacion": tipo_relacion,
                "tipo_norma_destino": ref["tipo_norma"],
                "numero_destino": ref["numero"],
                "anio_destino": ref["anio"],
                "fecha_destino": ref["fecha"],
                "articulo_destino": ref["articulo"],
                "texto_original": texto_original,
                "articulo_origen": articulo_origen,
            }
        )
    return relaciones


def parse_nota_relaciones(nota_html: str, articulo_origen: str = None) -> list[dict]:
    """Parsea relaciones normativas desde una nota HTML de IMPO."""
    texto = _limpiar_texto(nota_html)
    if not texto:
        return []

    relaciones: list[dict] = []

    for match in _RELACION_RE.finditer(texto):
        label = match.group("label").lower()
        body = match.group("body").strip()
        texto_original = match.group(0).strip()
        prefix = match.group("prefix").strip() or None
        articulo_origen_relacion = articulo_origen or prefix

        if label.startswith("reglamentad"):
            partes = [p.strip() for p in body.split(",") if p.strip()]
            for parte in partes:
                parte = parte.rstrip(" ,.;")
                ref = parse_norma_ref(parte)
                if not ref:
                    continue
                relaciones.append(
                    {
                        "tipo_relacion": "REGLAMENTA",
                        "tipo_norma_destino": ref["tipo_norma"],
                        "numero_destino": ref["numero"],
                        "anio_destino": ref["anio"],
                        "fecha_destino": ref["fecha"],
                        "articulo_destino": ref["articulo"],
                        "texto_original": texto_original if len(partes) == 1 else f"{match.group('label')}: {parte}",
                        "articulo_origen": articulo_origen_relacion,
                    }
                )
            continue

        if label.startswith("redacci") and "nueva redacción" not in label:
            tipo_relacion = "MODIFICA"
        elif label.startswith("agregad"):
            tipo_relacion = "AGREGA"
        elif label.startswith("derogad"):
            tipo_relacion = "DEROGA"
        elif "nueva redacción" in label:
            tipo_relacion = "NUEVA_REDACCION"
        elif "vigencia" in label:
            tipo_relacion = "VIGENCIA"
        elif label == "ver":
            tipo_relacion = "REFERENCIA"
        else:
            continue

        relaciones.extend(
            _extraer_relaciones_desde_fragmento(
                tipo_relacion=tipo_relacion,
                fragmento=body,
                articulo_origen=articulo_origen_relacion,
                texto_original=texto_original,
            )
        )

    return relaciones


def extraer_decretos_pendientes(relaciones: list[dict]) -> list[dict]:
    """Filtra relaciones que apuntan a decretos pendientes de descarga."""
    pendientes: list[dict] = []
    vistos: set[tuple[object, object, object]] = set()
    for relacion in relaciones or []:
        if relacion.get("tipo_norma_destino") != "DECRETO":
            continue
        clave = (
            relacion.get("tipo_norma_destino"),
            relacion.get("numero_destino"),
            relacion.get("anio_destino"),
        )
        if clave in vistos:
            continue
        vistos.add(clave)
        pendientes.append(
            {
                "tipo_norma": relacion.get("tipo_norma_destino"),
                "numero": relacion.get("numero_destino"),
                "anio": relacion.get("anio_destino"),
            }
        )
    return pendientes
