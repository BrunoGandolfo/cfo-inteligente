#!/usr/bin/env python3
"""Descarga PDFs de doctrina, extrae texto y lo persiste en texto_completo."""

from __future__ import annotations

import argparse
import html
import logging
import os
import re
import sys
import tempfile
import time
from urllib.parse import urljoin

import fitz
import requests

sys.path.insert(0, ".")

from app.core.database import SessionLocal
from app.models.doctrina import Doctrina


REQUEST_TIMEOUT = 30
DOWNLOAD_DELAY_SECONDS = 0.5
MAX_PDF_SIZE_BYTES = 50 * 1024 * 1024
MIN_TEXT_LENGTH_WARNING = 100
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
)
OJS_ARTICLE_PATTERN = re.compile(
    r"/article/(?P<kind>download|view)/(?P<article_id>[^/?#]+)(?:/(?P<galley_id>[^/?#]+))?/?$"
)
HREF_PATTERN = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)


def setup_logging() -> logging.Logger:
    """Configura logging de consola con timestamps legibles."""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger("extract_doctrina_pdfs")


def parse_args() -> argparse.Namespace:
    """Parsea flags del script."""
    parser = argparse.ArgumentParser(
        description="Descarga PDFs de doctrina y extrae texto completo."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Procesa solo los primeros N articulos pendientes.",
    )
    return parser.parse_args()


def descargar_pdf_temporal(
    url: str,
    headers: dict[str, str],
    logger: logging.Logger,
) -> str | None:
    """Descarga un PDF a un archivo temporal y devuelve su ruta."""
    temp_path: str | None = None

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
            stream=True,
        )
    except requests.Timeout:
        logger.warning("Timeout descargando PDF: %s", url)
        return None
    except requests.RequestException as exc:
        logger.warning("Error HTTP descargando PDF %s: %s", url, exc)
        return None

    try:
        if response.status_code != 200:
            logger.warning("Respuesta HTTP %s para PDF: %s", response.status_code, url)
            return None

        content_length = response.headers.get("Content-Length")
        if content_length:
            try:
                expected_size = int(content_length)
            except ValueError:
                expected_size = None
            else:
                if expected_size > MAX_PDF_SIZE_BYTES:
                    logger.warning(
                        "PDF demasiado grande (%s bytes), se omite: %s",
                        expected_size,
                        url,
                    )
                    return None

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_path = temp_file.name
            total_bytes = 0

            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue

                total_bytes += len(chunk)
                if total_bytes > MAX_PDF_SIZE_BYTES:
                    logger.warning(
                        "PDF excede 50MB durante descarga (%s bytes), se omite: %s",
                        total_bytes,
                        url,
                    )
                    return None

                temp_file.write(chunk)

        return temp_path
    except Exception:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise
    finally:
        response.close()


def extraer_texto_pdf(temp_path: str, source_url: str, logger: logging.Logger) -> str | None:
    """Extrae texto desde un PDF temporal."""
    try:
        with fitz.open(temp_path) as doc:
            texto = "".join(page.get_text() for page in doc).strip()
    except Exception as exc:
        logger.warning("No se pudo abrir o extraer PDF %s: %s", source_url, exc)
        return None

    if len(texto) < MIN_TEXT_LENGTH_WARNING:
        logger.warning(
            "Texto extraido muy corto (%s caracteres), posible PDF escaneado: %s",
            len(texto),
            source_url,
        )

    return texto or None


def derive_ojs_article_view_url(url_pdf: str) -> str | None:
    """Deriva la pagina del articulo cuando url_pdf es una URL OJS incompleta."""
    match = OJS_ARTICLE_PATTERN.search(url_pdf)
    if not match:
        return None
    if match.group("kind") != "download" or match.group("galley_id"):
        return None
    return url_pdf.replace("/article/download/", "/article/view/", 1)


def resolve_ojs_pdf_url(
    url_pdf: str,
    headers: dict[str, str],
    logger: logging.Logger,
) -> str | None:
    """Intenta resolver el galley PDF real desde la pagina del articulo OJS."""
    article_view_url = derive_ojs_article_view_url(url_pdf)
    if not article_view_url:
        return None

    try:
        response = requests.get(article_view_url, headers=headers, timeout=REQUEST_TIMEOUT)
    except requests.Timeout:
        logger.warning("Timeout resolviendo galley OJS para PDF: %s", article_view_url)
        return None
    except requests.RequestException as exc:
        logger.warning("Error HTTP resolviendo galley OJS %s: %s", article_view_url, exc)
        return None

    try:
        if response.status_code != 200:
            logger.warning(
                "Respuesta HTTP %s resolviendo galley OJS: %s",
                response.status_code,
                article_view_url,
            )
            return None

        match = OJS_ARTICLE_PATTERN.search(article_view_url)
        if not match:
            return None
        article_id = match.group("article_id")

        for href in HREF_PATTERN.findall(html.unescape(response.text)):
            candidate = urljoin(article_view_url, href).split("#", 1)[0]
            candidate_match = OJS_ARTICLE_PATTERN.search(candidate)
            if not candidate_match or candidate_match.group("article_id") != article_id:
                continue
            if candidate_match.group("galley_id") is None:
                continue

            if candidate_match.group("kind") == "view":
                candidate = candidate.replace("/article/view/", "/article/download/", 1)

            logger.info("URL PDF OJS resuelta: %s", candidate)
            return candidate

        logger.warning("No se encontro galley PDF OJS para articulo: %s", article_view_url)
        return None
    finally:
        response.close()


def intentar_descarga_y_extraccion(
    url_pdf: str,
    headers: dict[str, str],
    logger: logging.Logger,
) -> str | None:
    """Descarga un PDF temporalmente, extrae texto y limpia el archivo."""
    temp_path = descargar_pdf_temporal(url_pdf, headers, logger)
    if not temp_path:
        return None

    try:
        return extraer_texto_pdf(temp_path, url_pdf, logger)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def descargar_y_extraer(url_pdf: str, logger: logging.Logger) -> str | None:
    """Descarga un PDF temporalmente y retorna el texto extraido."""
    headers = {"User-Agent": USER_AGENT}

    texto = intentar_descarga_y_extraccion(url_pdf, headers, logger)
    if texto:
        return texto

    fallback_url = resolve_ojs_pdf_url(url_pdf, headers, logger)
    if not fallback_url or fallback_url == url_pdf:
        return None

    logger.info("Reintentando descarga con galley OJS: %s", fallback_url)
    return intentar_descarga_y_extraccion(fallback_url, headers, logger)


def main(limit: int | None = None) -> None:
    """Procesa doctrina pendiente y persiste texto completo articulo por articulo."""
    logger = setup_logging()
    db = SessionLocal()

    procesados = 0
    exitosos = 0
    fallidos = 0
    total_caracteres = 0

    try:
        query = (
            db.query(Doctrina)
            .filter(
                Doctrina.texto_completo.is_(None),
                Doctrina.url_pdf.is_not(None),
                Doctrina.deleted_at.is_(None),
            )
            .order_by(Doctrina.id)
        )

        if limit is not None:
            query = query.limit(limit)

        articulos = query.all()
        total = len(articulos)

        logger.info("Articulos pendientes para procesar: %s", total)

        for index, articulo in enumerate(articulos, start=1):
            procesados += 1
            titulo = (articulo.titulo or "")[:80]
            logger.info("[%s/%s] %s - %s", index, total, titulo, articulo.fuente)

            try:
                texto = descargar_y_extraer(articulo.url_pdf, logger)
                if not texto:
                    fallidos += 1
                    logger.warning("No se obtuvo texto para articulo %s", articulo.id)
                    continue

                articulo.texto_completo = texto
                db.commit()

                exitosos += 1
                total_caracteres += len(texto)
                logger.info(
                    "Texto guardado para articulo %s (%s caracteres)",
                    articulo.id,
                    len(texto),
                )
            except Exception as exc:
                db.rollback()
                fallidos += 1
                logger.exception("Error procesando articulo %s: %s", articulo.id, exc)
            finally:
                time.sleep(DOWNLOAD_DELAY_SECONDS)
    finally:
        db.close()

    promedio = (total_caracteres / exitosos) if exitosos else 0

    print("")
    print("Resumen final")
    print(f"Total procesados: {procesados}")
    print(f"Exitosos: {exitosos}")
    print(f"Fallidos: {fallidos}")
    print(f"Promedio de caracteres por articulo: {promedio:.2f}")


if __name__ == "__main__":
    args = parse_args()
    main(limit=args.limit)
