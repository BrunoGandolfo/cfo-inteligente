#!/usr/bin/env python3
"""Harvests doctrina metadata from juridical journals via OAI-PMH."""

import logging
import sys
import time
import xml.etree.ElementTree as ET
from datetime import date, datetime
from typing import Any, Optional

import requests
from sqlalchemy import func

sys.path.insert(0, ".")

from app.core.database import SessionLocal
from app.models.doctrina import Doctrina


REVISTAS = [
    {
        "nombre": "UdelaR",
        "oai_url": "https://revista.fder.edu.uy/index.php/rfd/oai",
        "revista_completa": "Revista de la Facultad de Derecho - Universidad de la Republica",
    },
    {
        "nombre": "UCU",
        "oai_url": "https://revistas.ucu.edu.uy/index.php/revistadederecho/oai",
        "revista_completa": "Revista de Derecho - Universidad Catolica del Uruguay",
    },
]

OAI_NAMESPACES = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
    "dc": "http://purl.org/dc/elements/1.1/",
}

REQUEST_TIMEOUT = 30
PAGE_DELAY_SECONDS = 1


def setup_logging() -> logging.Logger:
    """Configures a simple console logger for the harvester."""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger("harvest_doctrina")


def normalize_space(value: Any) -> str:
    """Returns a compact single-line representation for text fields."""
    return " ".join(str(value or "").split())


def unique_texts(values: list[str]) -> list[str]:
    """Keeps normalized non-empty texts preserving order."""
    seen: set[str] = set()
    items: list[str] = []
    for value in values:
        normalized = normalize_space(value)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        items.append(normalized)
    return items


def parse_fecha_publicacion(raw_value: str | None) -> Optional[date]:
    """Parses common Dublin Core date formats into a date object."""
    value = normalize_space(raw_value)
    if not value:
        return None

    normalized = value.replace("Z", "")
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y"):
        try:
            parsed = datetime.strptime(normalized, fmt)
            return parsed.date()
        except ValueError:
            continue

    if "T" in normalized:
        try:
            return datetime.fromisoformat(normalized).date()
        except ValueError:
            return None
    return None


def first_text(element: ET.Element, xpath: str) -> str:
    """Returns the first matching text for an XML xpath."""
    found = element.find(xpath, OAI_NAMESPACES)
    if found is None:
        return ""
    return normalize_space(found.text)


def all_texts(element: ET.Element, xpath: str) -> list[str]:
    """Returns all matching non-empty texts for an XML xpath."""
    values = [normalize_space(node.text) for node in element.findall(xpath, OAI_NAMESPACES)]
    return unique_texts(values)


def longest_text(values: list[str]) -> str:
    """Returns the longest normalized text from a list."""
    cleaned = unique_texts(values)
    if not cleaned:
        return ""
    return max(cleaned, key=len)


def extract_url_articulo(metadata: ET.Element) -> str:
    """Returns the first HTTP identifier from Dublin Core metadata."""
    for value in all_texts(metadata, ".//dc:identifier"):
        if "http" in value.lower():
            return value
    return ""


def build_pdf_url(url_articulo: str) -> str:
    """Builds a likely OJS download URL from an article URL."""
    if not url_articulo or "/article/view/" not in url_articulo:
        return ""
    return url_articulo.replace("/article/view/", "/article/download/", 1)


def extract_url_pdf(metadata: ET.Element, url_articulo: str) -> str:
    """Returns the PDF URL from dc:relation or an OJS-derived fallback."""
    for value in all_texts(metadata, ".//dc:relation"):
        lowered = value.lower()
        if "http" in lowered and "pdf" in lowered:
            return value

    derived = build_pdf_url(url_articulo)
    return derived


def apply_non_empty_updates(instance: Doctrina, payload: dict[str, Any]) -> bool:
    """Updates only meaningful fields, preserving existing richer data."""
    changed = False
    for field, value in payload.items():
        if field == "oai_identifier":
            continue
        if value is None:
            continue
        if isinstance(value, str):
            value = normalize_space(value)
            if not value:
                continue
        if isinstance(value, list):
            value = unique_texts(value)
            if not value:
                continue

        current = getattr(instance, field)
        if current != value:
            setattr(instance, field, value)
            changed = True
    return changed


def upsert_doctrina(db, payload: dict[str, Any]) -> str:
    """Creates or updates a doctrina record keyed by OAI identifier."""
    existing = (
        db.query(Doctrina)
        .filter(
            Doctrina.oai_identifier == payload["oai_identifier"],
            Doctrina.deleted_at.is_(None),
        )
        .first()
    )

    if existing is None:
        db.add(Doctrina(**payload))
        db.commit()
        return "inserted"

    if apply_non_empty_updates(existing, payload):
        db.commit()
        return "updated"

    return "unchanged"


def parse_record(record: ET.Element, revista_config: dict[str, str]) -> Optional[dict[str, Any]]:
    """Extracts a doctrina payload from an OAI-PMH record."""
    header = record.find("oai:header", OAI_NAMESPACES)
    if header is None:
        return None
    if header.attrib.get("status") == "deleted":
        return None

    oai_identifier = first_text(header, "oai:identifier")
    metadata = record.find("oai:metadata", OAI_NAMESPACES)
    if not oai_identifier or metadata is None:
        return None

    titulo = first_text(metadata, ".//dc:title")
    if not titulo:
        return None

    autores = all_texts(metadata, ".//dc:creator")
    descripciones = all_texts(metadata, ".//dc:description")
    materias = all_texts(metadata, ".//dc:subject")
    url_articulo = extract_url_articulo(metadata)
    url_pdf = extract_url_pdf(metadata, url_articulo)

    return {
        "oai_identifier": oai_identifier,
        "titulo": titulo,
        "autor": "; ".join(autores) if autores else None,
        "fecha_publicacion": parse_fecha_publicacion(first_text(metadata, ".//dc:date")),
        "fuente": revista_config["nombre"],
        "revista": revista_config["revista_completa"],
        "url_articulo": url_articulo or None,
        "url_pdf": url_pdf or None,
        "abstract": longest_text(descripciones) or None,
        "texto_completo": None,
        "materias": materias or None,
        "idioma": first_text(metadata, ".//dc:language") or None,
    }


def fetch_xml(session: requests.Session, url: str, params: dict[str, str]) -> ET.Element:
    """Downloads and parses an OAI-PMH XML page."""
    response = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return ET.fromstring(response.content)


def harvest_revista(
    db,
    session: requests.Session,
    revista_config: dict[str, str],
    logger: logging.Logger,
) -> dict[str, int]:
    """Harvests all records for one revista, following resumption tokens."""
    stats = {"inserted": 0, "updated": 0, "unchanged": 0, "errors": 0, "pages": 0}
    params = {"verb": "ListRecords", "metadataPrefix": "oai_dc"}
    page_number = 0

    logger.info("[%s] Inicio cosecha OAI-PMH", revista_config["nombre"])

    while True:
        page_number += 1
        try:
            root = fetch_xml(session, revista_config["oai_url"], params)
        except Exception as exc:
            logger.error("[%s] Error descargando pagina OAI %s: %s", revista_config["nombre"], page_number, exc)
            break

        stats["pages"] += 1
        records = root.findall(".//oai:record", OAI_NAMESPACES)
        logger.info("[%s] Pagina %s con %s records", revista_config["nombre"], page_number, len(records))

        for record in records:
            try:
                payload = parse_record(record, revista_config)
                if payload is None:
                    continue

                result = upsert_doctrina(db, payload)
                stats[result] += 1
                logger.info(
                    "[%s] %s — %s",
                    revista_config["nombre"],
                    payload["titulo"][:80],
                    (payload.get("autor") or "")[:50],
                )
            except Exception as exc:
                db.rollback()
                stats["errors"] += 1
                identifier = first_text(record, "oai:header/oai:identifier")
                logger.error(
                    "[%s] Error procesando record %s: %s",
                    revista_config["nombre"],
                    identifier or "sin_identifier",
                    exc,
                )

        token_text = first_text(root, ".//oai:resumptionToken")
        if not token_text:
            break

        params = {"verb": "ListRecords", "resumptionToken": token_text}
        time.sleep(PAGE_DELAY_SECONDS)

    logger.info(
        "[%s] Fin cosecha: %s nuevos, %s actualizados, %s sin cambios, %s errores, %s paginas",
        revista_config["nombre"],
        stats["inserted"],
        stats["updated"],
        stats["unchanged"],
        stats["errors"],
        stats["pages"],
    )
    return stats


def print_summary(db, inserted: int, updated: int, logger: logging.Logger) -> None:
    """Prints the final database summary after harvesting."""
    total = db.query(func.count(Doctrina.id)).filter(Doctrina.deleted_at.is_(None)).scalar() or 0
    with_pdf = (
        db.query(func.count(Doctrina.id))
        .filter(Doctrina.deleted_at.is_(None), Doctrina.url_pdf.is_not(None))
        .scalar()
        or 0
    )
    logger.info("Total articulos en doctrina: %s", total)
    logger.info("Nuevos insertados: %s", inserted)
    logger.info("Actualizados: %s", updated)
    logger.info("Con URL de PDF: %s", with_pdf)


def main() -> None:
    """Harvests both configured revistas into PostgreSQL."""
    logger = setup_logging()
    db = SessionLocal()
    session = requests.Session()

    total_inserted = 0
    total_updated = 0

    try:
        for revista in REVISTAS:
            stats = harvest_revista(db, session, revista, logger)
            total_inserted += stats["inserted"]
            total_updated += stats["updated"]
        print_summary(db, total_inserted, total_updated, logger)
    finally:
        session.close()
        db.close()


if __name__ == "__main__":
    main()
