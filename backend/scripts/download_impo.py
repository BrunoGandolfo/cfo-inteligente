"""
Script de descarga masiva de normativa uruguaya desde IMPO.

Descarga leyes, decretos-ley y decretos reglamentarios del sitio de IMPO
(Instituto Nacional de Publicaciones Oficiales), los persiste en PostgreSQL
y extrae relaciones entre normas.

Fases:
  1 - Leyes (1..20468) + Decretos-Ley (14068..15738)
  2 - Decretos referenciados (descubiertos en notas de Fase 1)
  3 - Verificación e indexación

Uso:
  python scripts/download_impo.py --fase 1 --desde-ley 16060 --hasta-ley 16065
  python scripts/download_impo.py --fase 2
  python scripts/download_impo.py --fase 3
  python scripts/download_impo.py --fase 1 --dry-run
"""
import sys
import os
import re
import json
import time
import argparse
import logging
from datetime import datetime, date

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import text
from app.core.database import SessionLocal
from app.models.norma import Norma, NormaArticulo, NormaRelacion
from app.services.impo_relation_parser import parse_nota_relaciones

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
IMPO_BASE = "https://www.impo.com.uy/bases"
DELAY_ENTRE_REQUESTS = 1.0
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 5
USER_AGENT = "CFO-Inteligente/1.0 (Legal Research; contact: bgandolfo@cgmasociados.com)"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("impo")

# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------

def build_url(tipo_norma: str, numero: int, anio: int) -> str:
    """Construye la URL JSON de IMPO para una norma."""
    segmento = {
        "LEY": "leyes",
        "DECRETO_LEY": "decretos-ley",
        "DECRETO": "decretos",
    }[tipo_norma]
    return f"{IMPO_BASE}/{segmento}/{numero}-{anio}?json=true"


def url_html(tipo_norma: str, numero: int, anio: int) -> str:
    """URL pública (sin ?json=true) para guardar como referencia."""
    return build_url(tipo_norma, numero, anio).replace("?json=true", "")


# ---------------------------------------------------------------------------
# Estimación de año por número de ley
# ---------------------------------------------------------------------------

def estimar_anio_ley(numero: int) -> list[int]:
    """
    Retorna lista de años probables para un número de ley, ordenados por probabilidad.

    Los rangos se solapan para cubrir casos frontera (ej: Ley 16060 es de 1989
    pero está en la frontera del bucket 16000).
    """
    if numero <= 1000:
        return list(range(1826, 1875))
    elif numero <= 3000:
        return list(range(1865, 1915))
    elif numero <= 5000:
        return list(range(1895, 1935))
    elif numero <= 8000:
        return list(range(1915, 1950))
    elif numero <= 10000:
        return list(range(1930, 1960))
    elif numero <= 12000:
        return list(range(1945, 1970))
    elif numero <= 13500:
        return list(range(1955, 1980))
    elif numero <= 14500:
        return list(range(1968, 1990))
    elif numero <= 16100:
        return list(range(1980, 2000))
    elif numero <= 17500:
        return list(range(1993, 2008))
    elif numero <= 18500:
        return list(range(2000, 2014))
    elif numero <= 19500:
        return list(range(2008, 2020))
    elif numero <= 20100:
        return list(range(2014, 2024))
    else:
        return list(range(2020, 2027))


def estimar_anio_decreto_ley(numero: int) -> list[int]:
    """Decretos-ley uruguayos: período 1973-1985."""
    return list(range(1973, 1986))


def lookup_anio_desde_leyes(db, numero: int) -> int | None:
    """
    Busca el año de una ley en la tabla 'leyes' (cargada desde el Parlamento).
    Returns:
        El año si existe, None si no se encontró.
    """
    result = db.execute(
        text("SELECT anio FROM leyes WHERE numero = :numero AND anio IS NOT NULL LIMIT 1"),
        {"numero": numero}
    ).fetchone()
    return result[0] if result else None


# ---------------------------------------------------------------------------
# Descarga
# ---------------------------------------------------------------------------

def _es_json_valido(response: requests.Response) -> bool:
    """Verifica que la respuesta sea JSON y no una página HTML de error."""
    ct = response.headers.get("Content-Type", "")
    if "application/json" in ct:
        return True
    text = response.text.strip()
    return text.startswith("{") or text.startswith("[")


def _parse_json_response(response: requests.Response) -> dict | None:
    """Intenta parsear el JSON de la respuesta, con fallback de limpieza."""
    response.encoding = "ISO-8859-1"
    try:
        return response.json()
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: limpiar trailing commas y reintentar
    text = response.text.strip()
    text = re.sub(r',\s*([}\]])', r'\1', text)
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None


def download_norma(tipo_norma: str, numero: int, anio: int) -> dict | None:
    """
    Descarga una norma de IMPO.

    Returns:
        dict con JSON de IMPO, o None si no existe / error irrecuperable.
    """
    url = build_url(tipo_norma, numero, anio)
    headers = {"User-Agent": USER_AGENT}

    for intento in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT, headers=headers)

            if resp.status_code == 404:
                return None

            resp.raise_for_status()

            if not _es_json_valido(resp):
                return None

            data = _parse_json_response(resp)
            if data is None:
                log.warning("JSON inválido: %s (intento %d)", url, intento)
                if intento < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * intento)
                    continue
                return None

            return data

        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code in (404, 410):
                return None
            log.warning("HTTP error %s (intento %d): %s", url, intento, e)
        except requests.exceptions.RequestException as e:
            log.warning("Request error %s (intento %d): %s", url, intento, e)

        if intento < MAX_RETRIES:
            time.sleep(RETRY_DELAY * intento)

    return None


# ---------------------------------------------------------------------------
# Parseo de fechas
# ---------------------------------------------------------------------------

def parse_fecha(fecha_str: str | None) -> date | None:
    """Parsea 'dd/mm/yyyy' → datetime.date. Retorna None si falla."""
    if not fecha_str or not fecha_str.strip():
        return None
    try:
        return datetime.strptime(fecha_str.strip(), "%d/%m/%Y").date()
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Persistencia
# ---------------------------------------------------------------------------

def buscar_norma_destino(db, rel: dict):
    """Busca norma destino en BD. Retorna UUID o None."""
    if not rel.get("anio_destino"):
        return None
    norma = (
        db.query(Norma)
        .filter_by(
            tipo_norma=rel["tipo_norma_destino"],
            numero=rel["numero_destino"],
            anio=rel["anio_destino"],
            deleted_at=None,
        )
        .first()
    )
    return norma.id if norma else None


def persist_norma(db, data: dict, tipo_norma: str, numero: int, anio: int) -> Norma | None:
    """
    Persiste norma, artículos y relaciones en BD.

    Si ya existe con descarga_estado='ok', la skipea.
    Retorna la instancia Norma o None si se skipeó.
    """
    existente = (
        db.query(Norma)
        .filter_by(tipo_norma=tipo_norma, numero=numero, anio=anio, deleted_at=None)
        .first()
    )
    if existente and existente.descarga_estado == "ok":
        return None  # ya descargada

    if existente:
        norma = existente
    else:
        norma = Norma(
            tipo_norma=tipo_norma,
            numero=numero,
            anio=anio,
        )
        db.add(norma)

    # Campos mapeados
    norma.nombre = data.get("nombreNorma", "")
    norma.fecha_promulgacion = parse_fecha(data.get("fechaPromulgacion"))
    norma.fecha_publicacion = parse_fecha(data.get("fechaPublicacion"))
    norma.indexacion = data.get("indexacionNorma", "")
    norma.vistos = data.get("vistos", "")
    norma.referencias_norma = data.get("referenciasNorma", "")
    norma.url_impo = url_html(tipo_norma, numero, anio)
    norma.json_original = data
    norma.descarga_estado = "ok"
    norma.descarga_error = None

    # Flush para obtener norma.id
    db.flush()

    # Artículos
    for art in data.get("articulos", []):
        numero_art = art.get("nroArticulo", "")
        titulo = art.get("titulosArticulo", "") or art.get("tituloArticulo", "")
        texto = art.get("textoArticulo", "")
        notas = art.get("notasArticulo", "") or art.get("notasDelArticulo", "")
        referencias = art.get("referenciasAlArticulo", "")
        indexacion_art = art.get("indexacionArticulo", "")

        articulo = NormaArticulo(
            norma_id=norma.id,
            numero_articulo=str(numero_art),
            titulo=titulo,
            texto=texto,
            notas=notas,
            referencias=referencias,
            indexacion=indexacion_art,
        )
        db.add(articulo)

        # Relaciones desde notas
        rels = parse_nota_relaciones(notas, str(numero_art))
        for rel in rels:
            destino_id = buscar_norma_destino(db, rel)
            anio_dest = rel.get("anio_destino")
            dest_ref = (
                f"{rel['tipo_norma_destino']} {rel['numero_destino']}/{anio_dest}"
                if anio_dest
                else f"{rel['tipo_norma_destino']} {rel['numero_destino']}"
            )

            relacion = NormaRelacion(
                norma_origen_id=norma.id,
                tipo_relacion=rel["tipo_relacion"],
                articulo_origen=(rel.get("articulo_origen") or "")[:100] or None,
                articulo_destino=(rel.get("articulo_destino") or "")[:100] or None,
                texto_original=rel["texto_original"],
                norma_destino_ref=dest_ref,
                norma_destino_id=destino_id,
            )
            db.add(relacion)

    db.commit()
    return norma


def marcar_not_found(db, tipo_norma: str, numero: int, anio: int):
    """Marca una norma como not_found si no existía previamente."""
    existente = (
        db.query(Norma)
        .filter_by(tipo_norma=tipo_norma, numero=numero, anio=anio, deleted_at=None)
        .first()
    )
    if existente:
        return
    norma = Norma(
        tipo_norma=tipo_norma,
        numero=numero,
        anio=anio,
        descarga_estado="not_found",
    )
    db.add(norma)
    db.commit()


# ---------------------------------------------------------------------------
# Descarga con búsqueda de año
# ---------------------------------------------------------------------------

def descargar_con_busqueda_anio(
    db, tipo_norma: str, numero: int, anios_posibles: list[int], dry_run: bool = False
) -> bool:
    """
    Intenta descargar una norma probando cada año posible.

    Returns:
        True si se descargó y persistió, False si no se encontró.
    """
    for anio in anios_posibles:
        if dry_run:
            log.info("  [DRY-RUN] %s", build_url(tipo_norma, numero, anio))
            continue

        data = download_norma(tipo_norma, numero, anio)
        time.sleep(DELAY_ENTRE_REQUESTS)

        if data:
            result = persist_norma(db, data, tipo_norma, numero, anio)
            if result:
                log.info("  OK: %s %d/%d (%d artículos)", tipo_norma, numero, anio,
                         len(data.get("articulos", [])))
            else:
                log.info("  SKIP (ya existe): %s %d/%d", tipo_norma, numero, anio)
            return True

    if not dry_run:
        # Ningún año funcionó — marcar not_found con el primer año del rango
        marcar_not_found(db, tipo_norma, numero, anios_posibles[0] if anios_posibles else 0)

    return False


# ---------------------------------------------------------------------------
# Fases
# ---------------------------------------------------------------------------

def fase1_leyes_y_decretos_ley(
    db,
    desde_ley=1,
    hasta_ley=20468,
    desde_dl=14068,
    hasta_dl=15738,
    delay=DELAY_ENTRE_REQUESTS,
    dry_run=False,
):
    """Fase 1: Descarga leyes y decretos-ley."""
    global DELAY_ENTRE_REQUESTS
    DELAY_ENTRE_REQUESTS = delay

    total_leyes = hasta_ley - desde_ley + 1
    total_dl = hasta_dl - desde_dl + 1 if hasta_dl >= desde_dl else 0
    total = total_leyes + total_dl
    descargadas = 0
    encontradas = 0

    log.info("=== FASE 1: Leyes %d-%d (%d) + Decretos-Ley %d-%d (%d) ===",
             desde_ley, hasta_ley, total_leyes, desde_dl, hasta_dl, total_dl)

    if not dry_run:
        con_lookup = db.execute(
            text("SELECT count(*) FROM leyes WHERE numero >= :desde AND numero <= :hasta AND anio IS NOT NULL"),
            {"desde": desde_ley, "hasta": hasta_ley}
        ).scalar()
        log.info("Lookup disponible: %d/%d leyes con año conocido (1 request c/u)", con_lookup, total_leyes)

    # -- Leyes --
    for numero in range(desde_ley, hasta_ley + 1):
        descargadas += 1

        # Verificar si ya existe con estado ok o not_found
        if not dry_run:
            existente = (
                db.query(Norma)
                .filter_by(tipo_norma="LEY", numero=numero, deleted_at=None)
                .filter(Norma.descarga_estado.in_(["ok", "not_found"]))
                .first()
            )
            if existente:
                if descargadas % 100 == 0:
                    log.info("Fase 1: %d/%d (%.1f%%) — Ley %d (skip)",
                             descargadas, total, descargadas / total * 100, numero)
                continue

        anio_conocido = lookup_anio_desde_leyes(db, numero) if not dry_run else None
        if anio_conocido:
            anios = [anio_conocido]
        else:
            anios = estimar_anio_ley(numero)
        ok = descargar_con_busqueda_anio(db, "LEY", numero, anios, dry_run)
        if ok:
            encontradas += 1

        if descargadas % 100 == 0:
            log.info("Fase 1: %d/%d (%.1f%%) — última: Ley %d — encontradas: %d",
                     descargadas, total, descargadas / total * 100, numero, encontradas)

    # -- Decretos-Ley --
    if hasta_dl >= desde_dl:
        for numero in range(desde_dl, hasta_dl + 1):
            descargadas += 1

            if not dry_run:
                existente = (
                    db.query(Norma)
                    .filter_by(tipo_norma="DECRETO_LEY", numero=numero, deleted_at=None)
                    .filter(Norma.descarga_estado.in_(["ok", "not_found"]))
                    .first()
                )
                if existente:
                    continue

            anios = estimar_anio_decreto_ley(numero)
            ok = descargar_con_busqueda_anio(db, "DECRETO_LEY", numero, anios, dry_run)
            if ok:
                encontradas += 1

            if descargadas % 100 == 0:
                log.info("Fase 1: %d/%d (%.1f%%) — último: DL %d — encontradas: %d",
                         descargadas, total, descargadas / total * 100, numero, encontradas)

    log.info("=== FASE 1 COMPLETA: %d procesadas, %d encontradas ===", descargadas, encontradas)


def fase2_decretos_referenciados(db, delay=DELAY_ENTRE_REQUESTS, dry_run=False):
    """Fase 2: Descarga decretos referenciados en notas de Fase 1."""
    global DELAY_ENTRE_REQUESTS
    DELAY_ENTRE_REQUESTS = delay

    log.info("=== FASE 2: Decretos referenciados ===")

    # Buscar relaciones con destino pendiente que referencian decretos
    pendientes = (
        db.query(NormaRelacion)
        .filter(
            NormaRelacion.norma_destino_id.is_(None),
            NormaRelacion.norma_destino_ref.ilike("%DECRETO%"),
        )
        .all()
    )

    # Extraer pares únicos (tipo, numero, anio) de norma_destino_ref
    por_descargar = {}
    patron = re.compile(r"(DECRETO(?:_LEY)?)\s+(\d+)/(\d+)")
    for rel in pendientes:
        match = patron.search(rel.norma_destino_ref or "")
        if match:
            tipo = match.group(1)
            numero = int(match.group(2))
            anio = int(match.group(3))
            # Normalizar año corto
            if anio < 100:
                anio = 1900 + anio if anio > 25 else 2000 + anio
            elif anio < 1000:
                anio = 1000 + anio
            clave = (tipo, numero, anio)
            if clave not in por_descargar:
                por_descargar[clave] = []
            por_descargar[clave].append(rel.id)

    total = len(por_descargar)
    log.info("Encontrados %d decretos pendientes de descarga", total)

    descargados = 0
    for (tipo, numero, anio), rel_ids in por_descargar.items():
        descargados += 1

        # Verificar si ya existe
        existente = (
            db.query(Norma)
            .filter_by(tipo_norma=tipo, numero=numero, anio=anio, deleted_at=None)
            .first()
        )

        if existente and existente.descarga_estado == "ok":
            # Actualizar relaciones pendientes
            for rel_id in rel_ids:
                db.query(NormaRelacion).filter_by(id=rel_id).update(
                    {"norma_destino_id": existente.id}
                )
            db.commit()
            log.info("  VINCULADO (existente): %s %d/%d → %d relaciones", tipo, numero, anio, len(rel_ids))
            continue

        if dry_run:
            log.info("  [DRY-RUN] %s", build_url(tipo, numero, anio))
            continue

        data = download_norma(tipo, numero, anio)
        time.sleep(DELAY_ENTRE_REQUESTS)

        if data:
            norma = persist_norma(db, data, tipo, numero, anio)
            if norma:
                # Vincular relaciones
                for rel_id in rel_ids:
                    db.query(NormaRelacion).filter_by(id=rel_id).update(
                        {"norma_destino_id": norma.id}
                    )
                db.commit()
                log.info("  OK: %s %d/%d → %d relaciones vinculadas", tipo, numero, anio, len(rel_ids))
            else:
                log.info("  SKIP: %s %d/%d", tipo, numero, anio)
        else:
            log.info("  NOT FOUND: %s %d/%d", tipo, numero, anio)

        if descargados % 100 == 0:
            log.info("Fase 2: %d/%d (%.1f%%)", descargados, total, descargados / total * 100)

    log.info("=== FASE 2 COMPLETA: %d procesados ===", descargados)


def fase3_verificacion(db):
    """Fase 3: Resumen de verificación."""
    log.info("=== FASE 3: Verificación ===")

    from sqlalchemy import func

    # Normas por tipo y estado
    stats = (
        db.query(Norma.tipo_norma, Norma.descarga_estado, func.count())
        .filter(Norma.deleted_at.is_(None))
        .group_by(Norma.tipo_norma, Norma.descarga_estado)
        .order_by(Norma.tipo_norma, Norma.descarga_estado)
        .all()
    )

    log.info("\n--- Normas por tipo y estado ---")
    for tipo, estado, count in stats:
        log.info("  %-15s %-12s %6d", tipo, estado, count)

    # Total artículos
    total_articulos = db.query(func.count(NormaArticulo.id)).scalar()
    log.info("\n--- Total artículos: %d ---", total_articulos)

    # Relaciones
    total_rel = db.query(func.count(NormaRelacion.id)).scalar()
    vinculadas = (
        db.query(func.count(NormaRelacion.id))
        .filter(NormaRelacion.norma_destino_id.isnot(None))
        .scalar()
    )
    pendientes_rel = total_rel - vinculadas

    log.info("\n--- Relaciones ---")
    log.info("  Total:      %6d", total_rel)
    log.info("  Vinculadas: %6d", vinculadas)
    log.info("  Pendientes: %6d", pendientes_rel)

    # Relaciones por tipo
    rel_por_tipo = (
        db.query(NormaRelacion.tipo_relacion, func.count())
        .group_by(NormaRelacion.tipo_relacion)
        .order_by(func.count().desc())
        .all()
    )
    log.info("\n--- Relaciones por tipo ---")
    for tipo, count in rel_por_tipo:
        log.info("  %-20s %6d", tipo, count)

    log.info("\n=== FASE 3 COMPLETA ===")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Descarga masiva de normativa uruguaya desde IMPO"
    )
    parser.add_argument(
        "--fase", choices=["1", "2", "3", "all"], default="all",
        help="Fase a ejecutar (default: all)"
    )
    parser.add_argument("--desde-ley", type=int, default=1, help="Número de ley inicial (default: 1)")
    parser.add_argument("--hasta-ley", type=int, default=20468, help="Número de ley final (default: 20468)")
    parser.add_argument("--desde-dl", type=int, default=14068, help="Número decreto-ley inicial (default: 14068)")
    parser.add_argument("--hasta-dl", type=int, default=15738, help="Número decreto-ley final (default: 15738)")
    parser.add_argument("--delay", type=float, default=1.0, help="Segundos entre requests (default: 1.0)")
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar URLs sin descargar")

    args = parser.parse_args()

    log.info("Inicio: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    log.info("Parámetros: fase=%s, delay=%.1fs, dry_run=%s", args.fase, args.delay, args.dry_run)

    db = SessionLocal()

    try:
        if args.fase in ("1", "all"):
            fase1_leyes_y_decretos_ley(
                db,
                desde_ley=args.desde_ley,
                hasta_ley=args.hasta_ley,
                desde_dl=args.desde_dl,
                hasta_dl=args.hasta_dl,
                delay=args.delay,
                dry_run=args.dry_run,
            )

        if args.fase in ("2", "all"):
            fase2_decretos_referenciados(db, delay=args.delay, dry_run=args.dry_run)

        if args.fase in ("3", "all"):
            fase3_verificacion(db)
    finally:
        db.close()

    log.info("Fin: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == "__main__":
    main()
