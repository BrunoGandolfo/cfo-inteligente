"""Crawler resiliente para la Base de Jurisprudencia Nacional (BJN).

Fases disponibles:
- inventario: recorre años, pagina resultados y guarda metadata básica
- enriquecimiento: abre cada sentencia y guarda el contenido completo
- status: muestra progreso agregado y por año

Notas para Bruno:
- El proyecto solo tiene una tabla de tracking, así que este script reutiliza
  `scraping_progress` para ambas fases reencolando lotes completados cuando
  todavía faltan textos completos por enriquecer.
- `crear_sentencia()` hoy no actualiza una sentencia existente: si encuentra
  `bjn_id`, retorna el registro. Por eso este script hace el update real aquí,
  sin tocar el service existente.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import logging
import math
import os
import random
import re
import signal
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Optional

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent


def seed_env_from_file(path: Path) -> None:
    """Loads KEY=VALUE pairs without overriding already exported vars."""
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


seed_env_from_file(BACKEND_DIR / ".env")
seed_env_from_file(PROJECT_ROOT / ".env")

sys.path.insert(0, str(BACKEND_DIR))

from playwright.async_api import (  # type: ignore
    Browser,
    BrowserContext,
    Error as AsyncPlaywrightError,
    Page as AsyncPage,
    TimeoutError as AsyncTimeoutError,
    async_playwright,
)
from playwright.sync_api import (  # type: ignore
    Page as SyncPage,
    TimeoutError as SyncTimeoutError,
    sync_playwright,
)
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionLocal
from app.models.scraping_progress import ScrapingFailure, ScrapingProgress
from app.models.sentencia import Sentencia
from app.schemas.scraping_progress import ScrapingFailureCreate, ScrapingLogCreate, ScrapingProgressUpdate
from app.services.jurisprudencia_service import crear_sentencia
from app.services.scraping_progress_service import ScrapingProgressService


BASE_URL = "http://bjn.poderjudicial.gub.uy/BJNPUBLICA/busquedaSimple.seam"
DEFAULT_TIMEOUT_MS = 30_000
RESULTS_PER_PAGE = 200
ORDER_VALUE = "FECHA_DESCENDENTE"
INVENTORY_YEAR_START = 1990
INVENTORY_YEAR_END = 2025
ACTION_DELAY_MIN = 2.0
ACTION_DELAY_MAX = 4.0
SLOW_RESPONSE_SECONDS = 15.0
VERY_SLOW_RESPONSE_SECONDS = 25.0
VERY_SLOW_COOLDOWN_SECONDS = 60.0
SENTENCE_RETRY_BACKOFFS = (5.0, 10.0, 20.0, 40.0)
SENTENCE_MAX_ATTEMPTS = 4
PROGRESS_LOG_EVERY = 50

SELECTORS = {
    "link_busqueda_selectiva": '[id="j_id10:j_id11"]',
    "fecha_desde": '[id="formBusqueda:j_id20:j_id23:fechaDesdeCalInputDate"]',
    "fecha_desde_hidden": '[id="formBusqueda:j_id20:j_id23:fechaDesdeCalInputCurrentDate"]',
    "fecha_hasta": '[id="formBusqueda:j_id20:j_id147:fechaHastaCalInputDate"]',
    "fecha_hasta_hidden": '[id="formBusqueda:j_id20:j_id147:fechaHastaCalInputCurrentDate"]',
    "resultados_por_pagina_field": '[id="formBusqueda:j_id20:j_id223:cantPagcomboboxField"]',
    "resultados_por_pagina_hidden": '[id="formBusqueda:j_id20:j_id223:cantPagcomboboxValue"]',
    "ordenar_por": '[name="formBusqueda:j_id20:j_id240:j_id248"]',
    "buscar": '[id="formBusqueda:j_id20:Search"]',
    "grid_resultados": '[id="formResultados:dataTable"]',
    "filas_resultados": 'table[id="formResultados:dataTable"] tr.rich-table-row',
    "pagina_siguiente": '[id="formResultados:sigLink"]',
    "popup_click_pattern": 'td[id="formResultados:dataTable:{index}:colFec"]',
}

BLOCKED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".css", ".woff", ".woff2")

SHUTDOWN_REQUESTED = False
ASYNC_SHUTDOWN_EVENT: Optional[asyncio.Event] = None
ACTIVE_WORKER_IDS: set[str] = set()


class SessionExpiredError(RuntimeError):
    """Raised when BJN invalidates the current JSF session."""


class GracefulShutdownRequested(RuntimeError):
    """Raised when shutdown was requested and the worker should stop cleanly."""


class DefaultWorkerFilter(logging.Filter):
    """Ensures every record has a worker tag."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "worker"):
            record.worker = "MAIN"
        return True


def setup_logging() -> logging.Logger:
    """Configures the shared scraper logger."""
    logger = logging.getLogger("scraper_bjn")
    if logger.handlers:
        return logger

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] [%(worker)s] [%(levelname)s] %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )
    )
    handler.addFilter(DefaultWorkerFilter())

    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


def get_worker_logger(worker_id: str) -> logging.LoggerAdapter:
    """Returns a logger adapter that injects the worker id."""
    return logging.LoggerAdapter(setup_logging(), {"worker": worker_id})


def normalize_space(value: Any) -> str:
    """Normalizes whitespace in scraped text."""
    return " ".join(str(value or "").split())


def unique_texts(values: Iterable[Any]) -> list[str]:
    """Returns normalized, non-empty texts preserving order."""
    seen: set[str] = set()
    items: list[str] = []
    for value in values:
        normalized = normalize_space(value)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        items.append(normalized)
    return items


def parse_bjn_date(raw: str | None) -> Optional[date]:
    """Parses dd/MM/yyyy or dd/MM/yy dates from the site."""
    text = normalize_space(raw)
    if not text:
        return None

    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def month_year_from_date(value: str) -> str:
    """Converts dd/MM/yyyy to MM/yyyy for RichFaces hidden fields."""
    _, month, year = value.split("/")
    return f"{month}/{year}"


def build_bjn_id(numero: str | None, sede: str | None, sentencia_fecha: Optional[date]) -> str:
    """Builds a compact, deterministic identifier that fits the DB column."""
    numero_token = re.sub(r"[^A-Za-z0-9]+", "-", normalize_space(numero)).strip("-") or "SINNUM"
    fecha_token = sentencia_fecha.strftime("%Y%m%d") if sentencia_fecha else "NODATE"
    digest_source = f"{normalize_space(numero)}|{normalize_space(sede)}|{fecha_token}"
    digest = hashlib.sha1(digest_source.encode("utf-8")).hexdigest()[:10]
    return f"{numero_token[:20]}_{fecha_token}_{digest}"[:50]


def classify_error(exc: BaseException) -> str:
    """Maps Python/Playwright exceptions to stable scraper failure types."""
    message = normalize_space(str(exc)).lower()
    if isinstance(exc, (SyncTimeoutError, AsyncTimeoutError)):
        return "timeout"
    if "viewstate" in message or "viewexpired" in message or "session" in message:
        return "session_expired"
    if "network" in message or "socket" in message or "connection" in message:
        return "network_error"
    if isinstance(exc, ValueError):
        return "parse_error"
    return "runtime_error"


def ensure_not_shutdown() -> None:
    """Raises if a graceful shutdown was requested."""
    if SHUTDOWN_REQUESTED:
        raise GracefulShutdownRequested("Shutdown requested")


@dataclass
class AdaptiveDelayController:
    """Keeps action delays adaptive based on recent server response times."""

    multiplier: float = 1.0

    def next_delay(self) -> float:
        return random.uniform(ACTION_DELAY_MIN, ACTION_DELAY_MAX) * self.multiplier

    def register_response(self, duration_seconds: float) -> tuple[bool, bool]:
        is_slow = duration_seconds > SLOW_RESPONSE_SECONDS
        is_very_slow = duration_seconds > VERY_SLOW_RESPONSE_SECONDS
        self.multiplier = 2.0 if is_slow else 1.0
        return is_slow, is_very_slow

    def sync_sleep(self) -> None:
        time.sleep(self.next_delay())

    async def async_sleep(self) -> None:
        await asyncio.sleep(self.next_delay())


def emit_log(
    logger: logging.LoggerAdapter,
    db,
    worker_id: str,
    nivel: str,
    evento: str,
    mensaje: str,
    *,
    progress_id: Optional[int] = None,
    sentencias_por_minuto: Optional[float] = None,
    tiempo_respuesta_ms: Optional[int] = None,
) -> None:
    """Logs to stdout and persists the structured event to scraping_logs."""
    python_level = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warn": logging.WARNING,
        "error": logging.ERROR,
    }[nivel]
    logger.log(python_level, mensaje)

    if db is None:
        return

    try:
        ScrapingProgressService.log(
            db,
            ScrapingLogCreate(
                worker_id=worker_id,
                progress_id=progress_id,
                nivel=nivel,  # type: ignore[arg-type]
                evento=evento,
                mensaje=mensaje,
                sentencias_por_minuto=(
                    Decimal(f"{sentencias_por_minuto:.2f}") if sentencias_por_minuto is not None else None
                ),
                tiempo_respuesta_ms=tiempo_respuesta_ms,
            ),
        )
    except Exception:
        db.rollback()
        logger.debug("No pude persistir el log en scraping_logs", extra={"worker": worker_id})


def observe_latency_sync(
    controller: AdaptiveDelayController,
    duration_seconds: float,
    logger: logging.LoggerAdapter,
    db,
    worker_id: str,
    *,
    progress_id: Optional[int] = None,
    evento: str = "server_response",
) -> None:
    """Adapts delays based on the response time of a sync step."""
    is_slow, is_very_slow = controller.register_response(duration_seconds)
    if is_slow:
        emit_log(
            logger,
            db,
            worker_id,
            "warn",
            evento,
            f"Servidor lento ({duration_seconds:.2f}s). Multiplico delays por 2.",
            progress_id=progress_id,
            tiempo_respuesta_ms=int(duration_seconds * 1000),
        )
    if is_very_slow:
        emit_log(
            logger,
            db,
            worker_id,
            "warn",
            "server_cooldown",
            f"Servidor muy lento ({duration_seconds:.2f}s). Pauso {VERY_SLOW_COOLDOWN_SECONDS:.0f}s antes de continuar.",
            progress_id=progress_id,
            tiempo_respuesta_ms=int(duration_seconds * 1000),
        )
        time.sleep(VERY_SLOW_COOLDOWN_SECONDS)


async def observe_latency_async(
    controller: AdaptiveDelayController,
    duration_seconds: float,
    logger: logging.LoggerAdapter,
    db,
    worker_id: str,
    *,
    progress_id: Optional[int] = None,
    evento: str = "server_response",
) -> None:
    """Adapts delays based on the response time of an async step."""
    is_slow, is_very_slow = controller.register_response(duration_seconds)
    if is_slow:
        emit_log(
            logger,
            db,
            worker_id,
            "warn",
            evento,
            f"Servidor lento ({duration_seconds:.2f}s). Multiplico delays por 2.",
            progress_id=progress_id,
            tiempo_respuesta_ms=int(duration_seconds * 1000),
        )
    if is_very_slow:
        emit_log(
            logger,
            db,
            worker_id,
            "warn",
            "server_cooldown",
            f"Servidor muy lento ({duration_seconds:.2f}s). Pauso {VERY_SLOW_COOLDOWN_SECONDS:.0f}s antes de continuar.",
            progress_id=progress_id,
            tiempo_respuesta_ms=int(duration_seconds * 1000),
        )
        await asyncio.sleep(VERY_SLOW_COOLDOWN_SECONDS)


def handle_signal(signum: int, _frame: Any) -> None:
    """Requests a graceful shutdown from SIGINT/SIGTERM."""
    global SHUTDOWN_REQUESTED
    SHUTDOWN_REQUESTED = True
    setup_logging().warning(
        "Señal %s recibida. Se solicita apagado ordenado.",
        signum,
        extra={"worker": "MAIN"},
    )
    if ASYNC_SHUTDOWN_EVENT is not None:
        ASYNC_SHUTDOWN_EVENT.set()


def install_signal_handlers() -> None:
    """Installs SIGINT/SIGTERM handlers for resumable shutdown."""
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)


def pause_active_batches(reason: str) -> None:
    """Marks currently claimed batches as paused so the next run can resume."""
    if not ACTIVE_WORKER_IDS:
        return

    db = SessionLocal()
    try:
        batches = (
            db.query(ScrapingProgress)
            .filter(
                ScrapingProgress.estado == "in_progress",
                ScrapingProgress.worker_id.in_(tuple(ACTIVE_WORKER_IDS)),
            )
            .all()
        )
        for batch in batches:
            batch.estado = "paused"
            batch.worker_id = None
            batch.error_ultimo = reason
        if batches:
            db.commit()
    finally:
        db.close()


def requeue_paused_batches(db) -> int:
    """Treats paused batches as pending on the next run."""
    batches = db.query(ScrapingProgress).filter(ScrapingProgress.estado == "paused").all()
    for batch in batches:
        batch.estado = "pending"
        batch.worker_id = None
    if batches:
        db.commit()
    return len(batches)


def count_sentencias_for_batch(db, batch: ScrapingProgress, *, enriched_only: bool = False) -> int:
    """Counts sentences for a given batch date range."""
    query = db.query(func.count(Sentencia.id)).filter(
        Sentencia.deleted_at.is_(None),
        Sentencia.fecha >= batch.fecha_inicio,
        Sentencia.fecha <= batch.fecha_fin,
    )
    if enriched_only:
        query = query.filter(Sentencia.texto_completo.is_not(None))
    return int(query.scalar() or 0)


def batch_needs_enrichment(db, batch: ScrapingProgress) -> bool:
    """Determines if a completed batch still has sentences without full text."""
    total_in_db = count_sentencias_for_batch(db, batch, enriched_only=False)
    enriched_in_db = count_sentencias_for_batch(db, batch, enriched_only=True)
    expected = max(batch.sentencias_encontradas or 0, total_in_db)
    return expected > 0 and enriched_in_db < expected


def prepare_batches_for_enrichment(db, logger: logging.LoggerAdapter) -> int:
    """Requeues completed batches that still need full-text enrichment."""
    requeued = 0
    requeued += requeue_paused_batches(db)

    completed_batches = (
        db.query(ScrapingProgress)
        .filter(ScrapingProgress.estado == "completed")
        .order_by(ScrapingProgress.fecha_inicio.asc())
        .all()
    )

    for batch in completed_batches:
        if not batch_needs_enrichment(db, batch):
            continue
        batch.estado = "pending"
        batch.pagina_actual = 0
        batch.worker_id = None
        batch.error_ultimo = None
        requeued += 1

    if requeued:
        db.commit()
        logger.info("Reencolé %s lote/s para enriquecimiento", requeued)
    return requeued


def persist_sentencia(db, payload: dict[str, Any], *, overwrite_existing: bool) -> Sentencia:
    """Creates or updates a sentence while keeping the existing service contract."""
    bjn_id = payload["bjn_id"]
    existing = (
        db.query(Sentencia)
        .filter(Sentencia.bjn_id == bjn_id, Sentencia.deleted_at.is_(None))
        .first()
    )
    if existing is None:
        return crear_sentencia(db, payload)

    changed = False
    for field, value in payload.items():
        if field == "bjn_id":
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

        current = getattr(existing, field)
        should_update = overwrite_existing or current in (None, "", [])
        if should_update and current != value:
            setattr(existing, field, value)
            changed = True

    if changed:
        db.commit()
        db.refresh(existing)
    return existing


def resolve_matching_failure(db, progress_id: int, pagina: int, posicion: int) -> None:
    """Resolves an unresolved failure once the sentence succeeds."""
    failure = (
        db.query(ScrapingFailure)
        .filter(
            ScrapingFailure.progress_id == progress_id,
            ScrapingFailure.pagina == pagina,
            ScrapingFailure.posicion_en_pagina == posicion,
            ScrapingFailure.resuelta.is_(False),
        )
        .first()
    )
    if failure is not None:
        ScrapingProgressService.resolve_failure(db, failure.id)


def calculate_sentencias_per_minute(processed_count: int, started_at: float) -> float:
    """Computes sentences per minute from a monotonic clock."""
    elapsed_minutes = max((time.perf_counter() - started_at) / 60.0, 1e-9)
    return processed_count / elapsed_minutes


def install_route_blocking_sync(page: SyncPage) -> None:
    """Blocks non-essential assets in sync Playwright pages."""

    def route_handler(route) -> None:
        request = route.request
        url = request.url.lower()
        if request.resource_type in {"image", "media", "font", "stylesheet"} or url.endswith(
            BLOCKED_EXTENSIONS
        ):
            route.abort()
            return
        route.continue_()

    page.route("**/*", route_handler)


async def install_route_blocking_async(context: BrowserContext) -> None:
    """Blocks non-essential assets in async Playwright contexts."""

    async def route_handler(route) -> None:
        request = route.request
        url = request.url.lower()
        if request.resource_type in {"image", "media", "font", "stylesheet"} or url.endswith(
            BLOCKED_EXTENSIONS
        ):
            await route.abort()
            return
        await route.continue_()

    await context.route("**/*", route_handler)


def assert_not_session_expired_sync(page: SyncPage) -> None:
    """Detects common JSF/RichFaces session-expiration symptoms."""
    url = page.url.lower()
    body = normalize_space(page.locator("body").inner_text())
    if (
        "busquedasimple.seam" in url
        and "busquedaselectiva" not in url
        and "resultado/s" not in body.lower()
    ):
        raise SessionExpiredError("Redirect a busquedaSimple.seam durante la navegación")
    if "viewstate" in body.lower() or "viewexpired" in body.lower():
        raise SessionExpiredError("Error de ViewState detectado")


async def assert_not_session_expired_async(page: AsyncPage) -> None:
    """Detects common JSF/RichFaces session-expiration symptoms."""
    url = page.url.lower()
    body = normalize_space(await page.locator("body").inner_text())
    if (
        "busquedasimple.seam" in url
        and "busquedaselectiva" not in url
        and "resultado/s" not in body.lower()
    ):
        raise SessionExpiredError("Redirect a busquedaSimple.seam durante la navegación")
    if "viewstate" in body.lower() or "viewexpired" in body.lower():
        raise SessionExpiredError("Error de ViewState detectado")


def parse_results_overview_from_text(body_text: str) -> dict[str, Optional[int]]:
    """Parses total results and current/total pages from body text."""
    total_match = re.search(r"(\d+)\s+resultado/s", body_text, flags=re.IGNORECASE)
    page_match = re.search(r"P[aá]gina\s+(\d+)\s+de\s+(\d+)", body_text, flags=re.IGNORECASE)
    total_results = int(total_match.group(1)) if total_match else None
    current_page = int(page_match.group(1)) if page_match else None
    total_pages = int(page_match.group(2)) if page_match else None
    if total_results is not None and total_pages is None:
        total_pages = max(math.ceil(total_results / RESULTS_PER_PAGE), 1)
    return {
        "total_results": total_results,
        "current_page": current_page,
        "total_pages": total_pages,
    }


def extract_result_rows_sync(page: SyncPage) -> list[dict[str, Any]]:
    """Extracts the visible metadata rows from the results table."""
    rows = page.locator(SELECTORS["filas_resultados"])
    results: list[dict[str, Any]] = []
    for index in range(rows.count()):
        row = rows.nth(index)
        cells = row.locator("td")
        if cells.count() < 4:
            continue
        fecha_text = normalize_space(cells.nth(0).inner_text(timeout=5_000))
        tipo_text = normalize_space(cells.nth(1).inner_text(timeout=5_000))
        numero_text = normalize_space(cells.nth(2).inner_text(timeout=5_000))
        sede_text = normalize_space(cells.nth(3).inner_text(timeout=5_000))
        procedimiento_text = (
            normalize_space(cells.nth(4).inner_text(timeout=5_000)) if cells.count() > 4 else ""
        )
        results.append(
            {
                "index": index,
                "fecha_text": fecha_text,
                "fecha": parse_bjn_date(fecha_text),
                "tipo": tipo_text,
                "numero": numero_text,
                "sede": sede_text,
                "procedimiento": procedimiento_text,
            }
        )
    return results


async def extract_result_rows_async(page: AsyncPage) -> list[dict[str, Any]]:
    """Extracts the visible metadata rows from the results table."""
    rows = page.locator(SELECTORS["filas_resultados"])
    row_count = await rows.count()
    results: list[dict[str, Any]] = []
    for index in range(row_count):
        row = rows.nth(index)
        cells = row.locator("td")
        cell_count = await cells.count()
        if cell_count < 4:
            continue
        fecha_text = normalize_space(await cells.nth(0).inner_text(timeout=5_000))
        tipo_text = normalize_space(await cells.nth(1).inner_text(timeout=5_000))
        numero_text = normalize_space(await cells.nth(2).inner_text(timeout=5_000))
        sede_text = normalize_space(await cells.nth(3).inner_text(timeout=5_000))
        procedimiento_text = (
            normalize_space(await cells.nth(4).inner_text(timeout=5_000)) if cell_count > 4 else ""
        )
        results.append(
            {
                "index": index,
                "fecha_text": fecha_text,
                "fecha": parse_bjn_date(fecha_text),
                "tipo": tipo_text,
                "numero": numero_text,
                "sede": sede_text,
                "procedimiento": procedimiento_text,
            }
        )
    return results


def execute_inventory_search_sync(
    page: SyncPage,
    batch: ScrapingProgress,
    controller: AdaptiveDelayController,
    logger: logging.LoggerAdapter,
    db,
    worker_id: str,
) -> dict[str, Optional[int]]:
    """Opens BJN search, configures selective search and runs the yearly query."""
    ensure_not_shutdown()

    started_at = time.perf_counter()
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)
    observe_latency_sync(controller, time.perf_counter() - started_at, logger, db, worker_id, progress_id=batch.id)
    controller.sync_sleep()

    page.wait_for_function("typeof A4J !== 'undefined'", timeout=DEFAULT_TIMEOUT_MS)
    page.locator(SELECTORS["link_busqueda_selectiva"]).click()
    controller.sync_sleep()

    started_at = time.perf_counter()
    page.wait_for_url("**/busquedaSelectiva.seam?cid=*", timeout=DEFAULT_TIMEOUT_MS)
    observe_latency_sync(controller, time.perf_counter() - started_at, logger, db, worker_id, progress_id=batch.id)
    controller.sync_sleep()

    page.locator(SELECTORS["fecha_desde"]).wait_for(timeout=DEFAULT_TIMEOUT_MS)
    page.evaluate(
        """
        ({ hiddenSelector, fieldSelector, value }) => {
            const hidden = document.querySelector(hiddenSelector);
            const field = document.querySelector(fieldSelector);
            if (!hidden || !field) {
                throw new Error("No encontre el combo de resultados por pagina");
            }
            hidden.value = value;
            field.value = value;
            field.dispatchEvent(new Event("change", { bubbles: true }));
            field.dispatchEvent(new Event("blur", { bubbles: true }));
        }
        """,
        {
            "hiddenSelector": SELECTORS["resultados_por_pagina_hidden"],
            "fieldSelector": SELECTORS["resultados_por_pagina_field"],
            "value": str(RESULTS_PER_PAGE),
        },
    )
    controller.sync_sleep()

    page.locator(SELECTORS["ordenar_por"]).select_option(ORDER_VALUE)
    controller.sync_sleep()

    fecha_desde = batch.fecha_inicio.strftime("%d/%m/%Y")
    fecha_hasta = batch.fecha_fin.strftime("%d/%m/%Y")
    page.locator(SELECTORS["fecha_desde"]).fill(fecha_desde)
    page.evaluate(
        """({ selector, value }) => {
            const hidden = document.querySelector(selector);
            if (hidden) hidden.value = value;
        }""",
        {"selector": SELECTORS["fecha_desde_hidden"], "value": month_year_from_date(fecha_desde)},
    )
    controller.sync_sleep()

    page.locator(SELECTORS["fecha_hasta"]).fill(fecha_hasta)
    page.evaluate(
        """({ selector, value }) => {
            const hidden = document.querySelector(selector);
            if (hidden) hidden.value = value;
        }""",
        {"selector": SELECTORS["fecha_hasta_hidden"], "value": month_year_from_date(fecha_hasta)},
    )
    controller.sync_sleep()

    started_at = time.perf_counter()
    page.locator(SELECTORS["buscar"]).click()
    page.wait_for_function(
        """
        () => {
            const body = document.body ? document.body.innerText : "";
            return body.includes("resultado/s")
                || body.includes("No se encontraron resultados")
                || document.querySelectorAll("table[id='formResultados:dataTable'] tr.rich-table-row").length > 0;
        }
        """,
        timeout=DEFAULT_TIMEOUT_MS,
    )
    duration = time.perf_counter() - started_at
    observe_latency_sync(
        controller,
        duration,
        logger,
        db,
        worker_id,
        progress_id=batch.id,
        evento="search_response",
    )
    controller.sync_sleep()
    assert_not_session_expired_sync(page)

    body_text = normalize_space(page.locator("body").inner_text(timeout=5_000))
    overview = parse_results_overview_from_text(body_text)
    return overview


def navigate_to_page_sync(
    page: SyncPage,
    target_page: int,
    controller: AdaptiveDelayController,
    logger: logging.LoggerAdapter,
    db,
    worker_id: str,
    progress_id: int,
) -> dict[str, Optional[int]]:
    """Moves from page 1 to the requested page by repeatedly clicking 'Siguiente'."""
    current_overview = parse_results_overview_from_text(normalize_space(page.locator("body").inner_text(timeout=5_000)))
    current_page = current_overview["current_page"] or 1
    if target_page <= current_page:
        return current_overview

    while current_page < target_page:
        ensure_not_shutdown()
        if page.locator(SELECTORS["pagina_siguiente"]).count() == 0:
            raise ValueError(f"No encontré link siguiente para llegar a la página {target_page}")

        started_at = time.perf_counter()
        page.locator(SELECTORS["pagina_siguiente"]).click()
        page.wait_for_function(
            """pageNumber => {
                const body = document.body ? document.body.innerText : "";
                const regex = new RegExp(`P[aá]gina\\\\s+${pageNumber}\\\\s+de\\\\s+\\\\d+`, "i");
                return regex.test(body);
            }""",
            arg=current_page + 1,
            timeout=DEFAULT_TIMEOUT_MS,
        )
        observe_latency_sync(
            controller,
            time.perf_counter() - started_at,
            logger,
            db,
            worker_id,
            progress_id=progress_id,
            evento="page_turn",
        )
        controller.sync_sleep()
        assert_not_session_expired_sync(page)
        current_overview = parse_results_overview_from_text(
            normalize_space(page.locator("body").inner_text(timeout=5_000))
        )
        current_page = current_overview["current_page"] or (current_page + 1)

    return current_overview


def process_inventory_batch(db, batch: ScrapingProgress, worker_id: str) -> None:
    """Runs the inventory phase for a single yearly batch."""
    logger = get_worker_logger(worker_id)
    controller = AdaptiveDelayController()
    batch_started_at = time.perf_counter()
    emit_log(
        logger,
        db,
        worker_id,
        "info",
        "batch_started",
        f"Inicio inventario {batch.fecha_inicio.year} ({batch.fecha_inicio}..{batch.fecha_fin})",
        progress_id=batch.id,
    )

    for session_attempt in range(1, 4):
        ensure_not_shutdown()
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
                page = browser.new_page()
                page.set_default_timeout(DEFAULT_TIMEOUT_MS)
                page.set_default_navigation_timeout(DEFAULT_TIMEOUT_MS)
                install_route_blocking_sync(page)

                overview = execute_inventory_search_sync(page, batch, controller, logger, db, worker_id)
                total_results = overview["total_results"] or 0
                total_pages = overview["total_pages"] or 0
                resume_page = max((batch.pagina_actual or 0) + 1, 1)

                if total_results == 0:
                    ScrapingProgressService.update_progress(
                        db,
                        batch.id,
                        ScrapingProgressUpdate(
                            pagina_actual=0,
                            total_paginas=0,
                            sentencias_encontradas=0,
                            sentencias_descargadas=0,
                        ),
                    )
                    ScrapingProgressService.complete_batch(db, batch.id)
                    emit_log(
                        logger,
                        db,
                        worker_id,
                        "info",
                        "batch_completed",
                        f"Lote {batch.fecha_inicio.year} sin resultados",
                        progress_id=batch.id,
                    )
                    browser.close()
                    return

                if resume_page > 1:
                    navigate_to_page_sync(page, resume_page, controller, logger, db, worker_id, batch.id)

                while True:
                    ensure_not_shutdown()
                    assert_not_session_expired_sync(page)

                    body_text = normalize_space(page.locator("body").inner_text(timeout=5_000))
                    page_overview = parse_results_overview_from_text(body_text)
                    current_page = page_overview["current_page"] or resume_page
                    rows = extract_result_rows_sync(page)

                    for row in rows:
                        payload = {
                            "bjn_id": build_bjn_id(row["numero"], row["sede"], row["fecha"]),
                            "numero": row["numero"],
                            "sede": row["sede"],
                            "fecha": row["fecha"],
                            "tipo": row["tipo"],
                            "query_origen": f"inventario:{batch.fecha_inicio.year}",
                        }
                        persist_sentencia(db, payload, overwrite_existing=False)

                    saved_count = count_sentencias_for_batch(db, batch, enriched_only=False)
                    ScrapingProgressService.update_progress(
                        db,
                        batch.id,
                        ScrapingProgressUpdate(
                            pagina_actual=current_page,
                            total_paginas=total_pages,
                            sentencias_encontradas=total_results,
                            sentencias_descargadas=saved_count,
                        ),
                    )

                    if saved_count and saved_count % PROGRESS_LOG_EVERY == 0:
                        spm = calculate_sentencias_per_minute(saved_count, batch_started_at)
                        emit_log(
                            logger,
                            db,
                            worker_id,
                            "info",
                            "inventory_progress",
                            f"Inventario {batch.fecha_inicio.year}: página {current_page}/{total_pages}, guardadas {saved_count}/{total_results}",
                            progress_id=batch.id,
                            sentencias_por_minuto=spm,
                        )

                    has_next = page.locator(SELECTORS["pagina_siguiente"]).count() > 0 and current_page < total_pages
                    if not has_next:
                        break

                    started_at = time.perf_counter()
                    page.locator(SELECTORS["pagina_siguiente"]).click()
                    page.wait_for_function(
                        """pageNumber => {
                            const body = document.body ? document.body.innerText : "";
                            const regex = new RegExp(`P[aá]gina\\\\s+${pageNumber}\\\\s+de\\\\s+\\\\d+`, "i");
                            return regex.test(body);
                        }""",
                        arg=current_page + 1,
                        timeout=DEFAULT_TIMEOUT_MS,
                    )
                    observe_latency_sync(
                        controller,
                        time.perf_counter() - started_at,
                        logger,
                        db,
                        worker_id,
                        progress_id=batch.id,
                        evento="page_turn",
                    )
                    controller.sync_sleep()

                ScrapingProgressService.complete_batch(db, batch.id)
                emit_log(
                    logger,
                    db,
                    worker_id,
                    "info",
                    "batch_completed",
                    f"Inventario completo {batch.fecha_inicio.year}: {total_results} resultados en {total_pages} páginas",
                    progress_id=batch.id,
                    sentencias_por_minuto=calculate_sentencias_per_minute(
                        count_sentencias_for_batch(db, batch, enriched_only=False),
                        batch_started_at,
                    ),
                )
                browser.close()
                return
        except SessionExpiredError as exc:
            db.refresh(batch)
            emit_log(
                logger,
                db,
                worker_id,
                "warn",
                "session_expired",
                f"Sesión expirada en inventario {batch.fecha_inicio.year}. Reabro browser y retomo desde página {(batch.pagina_actual or 0) + 1}. Intento {session_attempt}/3. {exc}",
                progress_id=batch.id,
            )
            continue
        except GracefulShutdownRequested:
            raise
        except Exception as exc:
            db.rollback()
            ScrapingProgressService.fail_batch(db, batch.id, str(exc))
            emit_log(
                logger,
                db,
                worker_id,
                "error",
                "batch_failed",
                f"Falló inventario {batch.fecha_inicio.year}: {exc}",
                progress_id=batch.id,
            )
            return

    ScrapingProgressService.fail_batch(db, batch.id, "Session expired repeatedly during inventory")
    emit_log(
        logger,
        db,
        worker_id,
        "error",
        "batch_failed",
        f"Inventario {batch.fecha_inicio.year} agotó reintentos de sesión",
        progress_id=batch.id,
    )


async def execute_search_async(
    page: AsyncPage,
    batch: ScrapingProgress,
    controller: AdaptiveDelayController,
    logger: logging.LoggerAdapter,
    db,
    worker_id: str,
) -> dict[str, Optional[int]]:
    """Async version of the selective search workflow."""
    ensure_not_shutdown()

    started_at = time.perf_counter()
    await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)
    await observe_latency_async(controller, time.perf_counter() - started_at, logger, db, worker_id, progress_id=batch.id)
    await controller.async_sleep()

    await page.wait_for_function("typeof A4J !== 'undefined'", timeout=DEFAULT_TIMEOUT_MS)
    await page.locator(SELECTORS["link_busqueda_selectiva"]).click()
    await controller.async_sleep()

    started_at = time.perf_counter()
    await page.wait_for_url("**/busquedaSelectiva.seam?cid=*", timeout=DEFAULT_TIMEOUT_MS)
    await observe_latency_async(controller, time.perf_counter() - started_at, logger, db, worker_id, progress_id=batch.id)
    await controller.async_sleep()

    await page.locator(SELECTORS["fecha_desde"]).wait_for(timeout=DEFAULT_TIMEOUT_MS)
    await page.evaluate(
        """
        ({ hiddenSelector, fieldSelector, value }) => {
            const hidden = document.querySelector(hiddenSelector);
            const field = document.querySelector(fieldSelector);
            if (!hidden || !field) {
                throw new Error("No encontre el combo de resultados por pagina");
            }
            hidden.value = value;
            field.value = value;
            field.dispatchEvent(new Event("change", { bubbles: true }));
            field.dispatchEvent(new Event("blur", { bubbles: true }));
        }
        """,
        {
            "hiddenSelector": SELECTORS["resultados_por_pagina_hidden"],
            "fieldSelector": SELECTORS["resultados_por_pagina_field"],
            "value": str(RESULTS_PER_PAGE),
        },
    )
    await controller.async_sleep()

    await page.locator(SELECTORS["ordenar_por"]).select_option(ORDER_VALUE)
    await controller.async_sleep()

    fecha_desde = batch.fecha_inicio.strftime("%d/%m/%Y")
    fecha_hasta = batch.fecha_fin.strftime("%d/%m/%Y")
    await page.locator(SELECTORS["fecha_desde"]).fill(fecha_desde)
    await page.evaluate(
        """({ selector, value }) => {
            const hidden = document.querySelector(selector);
            if (hidden) hidden.value = value;
        }""",
        {"selector": SELECTORS["fecha_desde_hidden"], "value": month_year_from_date(fecha_desde)},
    )
    await controller.async_sleep()

    await page.locator(SELECTORS["fecha_hasta"]).fill(fecha_hasta)
    await page.evaluate(
        """({ selector, value }) => {
            const hidden = document.querySelector(selector);
            if (hidden) hidden.value = value;
        }""",
        {"selector": SELECTORS["fecha_hasta_hidden"], "value": month_year_from_date(fecha_hasta)},
    )
    await controller.async_sleep()

    started_at = time.perf_counter()
    await page.locator(SELECTORS["buscar"]).click()
    await page.wait_for_function(
        """
        () => {
            const body = document.body ? document.body.innerText : "";
            return body.includes("resultado/s")
                || body.includes("No se encontraron resultados")
                || document.querySelectorAll("table[id='formResultados:dataTable'] tr.rich-table-row").length > 0;
        }
        """,
        timeout=DEFAULT_TIMEOUT_MS,
    )
    await observe_latency_async(
        controller,
        time.perf_counter() - started_at,
        logger,
        db,
        worker_id,
        progress_id=batch.id,
        evento="search_response",
    )
    await controller.async_sleep()
    await assert_not_session_expired_async(page)

    body_text = normalize_space(await page.locator("body").inner_text(timeout=5_000))
    return parse_results_overview_from_text(body_text)


async def navigate_to_page_async(
    page: AsyncPage,
    target_page: int,
    controller: AdaptiveDelayController,
    logger: logging.LoggerAdapter,
    db,
    worker_id: str,
    progress_id: int,
) -> dict[str, Optional[int]]:
    """Async version of page navigation through the datascroller."""
    body_text = normalize_space(await page.locator("body").inner_text(timeout=5_000))
    current_overview = parse_results_overview_from_text(body_text)
    current_page = current_overview["current_page"] or 1
    if target_page <= current_page:
        return current_overview

    while current_page < target_page:
        ensure_not_shutdown()
        if await page.locator(SELECTORS["pagina_siguiente"]).count() == 0:
            raise ValueError(f"No encontré link siguiente para llegar a la página {target_page}")

        started_at = time.perf_counter()
        await page.locator(SELECTORS["pagina_siguiente"]).click()
        await page.wait_for_function(
            """pageNumber => {
                const body = document.body ? document.body.innerText : "";
                const regex = new RegExp(`P[aá]gina\\\\s+${pageNumber}\\\\s+de\\\\s+\\\\d+`, "i");
                return regex.test(body);
            }""",
            arg=current_page + 1,
            timeout=DEFAULT_TIMEOUT_MS,
        )
        await observe_latency_async(
            controller,
            time.perf_counter() - started_at,
            logger,
            db,
            worker_id,
            progress_id=progress_id,
            evento="page_turn",
        )
        await controller.async_sleep()
        await assert_not_session_expired_async(page)
        body_text = normalize_space(await page.locator("body").inner_text(timeout=5_000))
        current_overview = parse_results_overview_from_text(body_text)
        current_page = current_overview["current_page"] or (current_page + 1)

    return current_overview


async def popup_texts(page: AsyncPage, selector: str) -> list[str]:
    """Returns all normalized texts for a popup selector."""
    locator = page.locator(selector)
    count = await locator.count()
    if count == 0:
        return []
    return unique_texts(await locator.all_inner_texts())


async def popup_first_text(page: AsyncPage, selector: str) -> str:
    """Returns the first text for a popup selector or empty string."""
    locator = page.locator(selector)
    count = await locator.count()
    if count == 0:
        return ""
    return normalize_space(await locator.first.inner_text(timeout=5_000))


async def extract_popup_payload(popup: AsyncPage) -> dict[str, Any]:
    """Extracts supported sentencia fields from the Hoja de Insumo popup."""
    numero = await popup_first_text(popup, "table#j_id3 tbody td:nth-child(1)")
    sede = await popup_first_text(popup, "table#j_id3 tbody td:nth-child(2)")
    importancia = await popup_first_text(popup, "table#j_id3 tbody td:nth-child(3)")
    tipo = await popup_first_text(popup, "table#j_id3 tbody td:nth-child(4)")
    fecha_text = await popup_first_text(popup, "table#j_id21 tbody td:nth-child(1)")
    materias = await popup_texts(popup, "table#j_id35 tbody td")
    firmantes = await popup_texts(popup, "table#gridFirmantes tbody td")
    redactores = await popup_texts(popup, "table#gridRedactores tbody td")
    abstract_text = await popup_first_text(popup, "table#j_id77 tbody td:nth-child(1)")
    abstract_descriptores = await popup_first_text(popup, "table#j_id77 tbody td:nth-child(2)")
    descriptores = unique_texts(
        [abstract_descriptores] + await popup_texts(popup, "table#j_id89 tbody td")
    )
    resumen_items = await popup_texts(popup, "table#j_id107 tbody td")
    texto = await popup_first_text(popup, "span#textoSentenciaBox")
    if not texto:
        texto = await popup_first_text(popup, "#panelTextoSent_body")

    return {
        "numero": numero,
        "sede": sede,
        "importancia": importancia,
        "tipo": tipo,
        "fecha": parse_bjn_date(fecha_text),
        "materias": materias,
        "firmantes": firmantes,
        "redactores": redactores,
        "abstract": abstract_text,
        "descriptores": descriptores,
        "resumen_items": resumen_items,
        "texto_completo": texto,
    }


async def process_sentence_row(
    page: AsyncPage,
    db,
    batch: ScrapingProgress,
    page_number: int,
    row: dict[str, Any],
    controller: AdaptiveDelayController,
    logger: logging.LoggerAdapter,
    worker_id: str,
) -> None:
    """Opens a sentencia popup, extracts full data and persists it with retries."""
    row_index = row["index"]
    selector = SELECTORS["popup_click_pattern"].format(index=row_index)
    last_exception: Optional[BaseException] = None

    for attempt in range(1, SENTENCE_MAX_ATTEMPTS + 1):
        ensure_not_shutdown()
        popup: Optional[AsyncPage] = None
        try:
            async with page.expect_popup(timeout=DEFAULT_TIMEOUT_MS) as popup_info:
                await page.locator(selector).click()
            popup = await popup_info.value

            started_at = time.perf_counter()
            await popup.wait_for_load_state("domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)
            await popup.locator("#textoSentenciaBox, #panelTextoSent_body").first.wait_for(
                timeout=DEFAULT_TIMEOUT_MS
            )
            await assert_not_session_expired_async(popup)
            await observe_latency_async(
                controller,
                time.perf_counter() - started_at,
                logger,
                db,
                worker_id,
                progress_id=batch.id,
                evento="popup_open",
            )
            await controller.async_sleep()

            payload = await extract_popup_payload(popup)
            numero = payload["numero"] or row["numero"]
            sede = payload["sede"] or row["sede"]
            sentencia_fecha = payload["fecha"] or row["fecha"]
            bjn_id = build_bjn_id(numero, sede, sentencia_fecha)

            persistence_payload = {
                "bjn_id": bjn_id,
                "numero": numero,
                "sede": sede,
                "fecha": sentencia_fecha,
                "tipo": payload["tipo"] or row["tipo"],
                "importancia": payload["importancia"],
                "materias": payload["materias"],
                "firmantes": payload["firmantes"],
                "abstract": payload["abstract"],
                "descriptores": payload["descriptores"],
                "texto_completo": payload["texto_completo"],
                "query_origen": f"enriquecimiento:{batch.fecha_inicio.year}",
            }
            persist_sentencia(db, persistence_payload, overwrite_existing=True)
            resolve_matching_failure(db, batch.id, page_number, row_index)
            if popup is not None:
                await popup.close()
            await controller.async_sleep()
            return
        except GracefulShutdownRequested:
            if popup is not None:
                await popup.close()
            raise
        except SessionExpiredError:
            if popup is not None:
                await popup.close()
            raise
        except Exception as exc:
            last_exception = exc
            if popup is not None:
                await popup.close()
            if attempt >= SENTENCE_MAX_ATTEMPTS:
                break
            backoff = SENTENCE_RETRY_BACKOFFS[min(attempt - 1, len(SENTENCE_RETRY_BACKOFFS) - 1)]
            emit_log(
                logger,
                db,
                worker_id,
                "warn",
                "sentence_retry",
                f"Retry {attempt}/{SENTENCE_MAX_ATTEMPTS} para sentencia fila {row_index} página {page_number}: {exc}. Espero {backoff:.0f}s.",
                progress_id=batch.id,
            )
            await asyncio.sleep(backoff)

    if last_exception is None:
        last_exception = RuntimeError("Fallo desconocido procesando sentencia")

    ScrapingProgressService.register_failure(
        db,
        ScrapingFailureCreate(
            progress_id=batch.id,
            pagina=page_number,
            posicion_en_pagina=row_index,
            numero_sentencia=row["numero"],
            sede=row["sede"],
            fecha_sentencia=row["fecha"],
            error_tipo=classify_error(last_exception),
            error_mensaje=str(last_exception),
        ),
    )
    emit_log(
        logger,
        db,
        worker_id,
        "error",
        "sentence_failed",
        f"Sentencia fila {row_index} página {page_number} falló definitivamente: {last_exception}",
        progress_id=batch.id,
    )


async def process_enrichment_batch(
    browser: Browser,
    db,
    batch: ScrapingProgress,
    worker_id: str,
) -> None:
    """Runs full-text enrichment for a single yearly batch."""
    logger = get_worker_logger(worker_id)
    controller = AdaptiveDelayController()
    batch_started_at = time.perf_counter()
    emit_log(
        logger,
        db,
        worker_id,
        "info",
        "batch_started",
        f"Inicio enriquecimiento {batch.fecha_inicio.year} ({batch.fecha_inicio}..{batch.fecha_fin})",
        progress_id=batch.id,
    )

    for session_attempt in range(1, 4):
        context: Optional[BrowserContext] = None
        page: Optional[AsyncPage] = None
        try:
            ensure_not_shutdown()
            context = await browser.new_context()
            await install_route_blocking_async(context)
            page = await context.new_page()
            page.set_default_timeout(DEFAULT_TIMEOUT_MS)
            page.set_default_navigation_timeout(DEFAULT_TIMEOUT_MS)

            overview = await execute_search_async(page, batch, controller, logger, db, worker_id)
            total_results = overview["total_results"] or 0
            total_pages = overview["total_pages"] or 0
            resume_page = max((batch.pagina_actual or 0) + 1, 1)

            if total_results == 0:
                ScrapingProgressService.update_progress(
                    db,
                    batch.id,
                    ScrapingProgressUpdate(
                        pagina_actual=0,
                        total_paginas=0,
                        sentencias_encontradas=0,
                        sentencias_descargadas=0,
                    ),
                )
                ScrapingProgressService.complete_batch(db, batch.id)
                emit_log(
                    logger,
                    db,
                    worker_id,
                    "info",
                    "batch_completed",
                    f"Lote {batch.fecha_inicio.year} sin resultados para enriquecer",
                    progress_id=batch.id,
                )
                await context.close()
                return

            if resume_page > 1:
                await navigate_to_page_async(page, resume_page, controller, logger, db, worker_id, batch.id)

            while True:
                ensure_not_shutdown()
                await assert_not_session_expired_async(page)

                body_text = normalize_space(await page.locator("body").inner_text(timeout=5_000))
                page_overview = parse_results_overview_from_text(body_text)
                current_page = page_overview["current_page"] or resume_page
                rows = await extract_result_rows_async(page)

                for row in rows:
                    await process_sentence_row(page, db, batch, current_page, row, controller, logger, worker_id)

                enriched_count = count_sentencias_for_batch(db, batch, enriched_only=True)
                ScrapingProgressService.update_progress(
                    db,
                    batch.id,
                    ScrapingProgressUpdate(
                        pagina_actual=current_page,
                        total_paginas=total_pages,
                        sentencias_encontradas=total_results,
                        sentencias_descargadas=enriched_count,
                    ),
                )

                if enriched_count and enriched_count % PROGRESS_LOG_EVERY == 0:
                    spm = calculate_sentencias_per_minute(enriched_count, batch_started_at)
                    emit_log(
                        logger,
                        db,
                        worker_id,
                        "info",
                        "enrichment_progress",
                        f"Enriquecimiento {batch.fecha_inicio.year}: página {current_page}/{total_pages}, textos completos {enriched_count}/{total_results}",
                        progress_id=batch.id,
                        sentencias_por_minuto=spm,
                    )

                has_next = (await page.locator(SELECTORS["pagina_siguiente"]).count()) > 0 and current_page < total_pages
                if not has_next:
                    break

                started_at = time.perf_counter()
                await page.locator(SELECTORS["pagina_siguiente"]).click()
                await page.wait_for_function(
                    """pageNumber => {
                        const body = document.body ? document.body.innerText : "";
                        const regex = new RegExp(`P[aá]gina\\\\s+${pageNumber}\\\\s+de\\\\s+\\\\d+`, "i");
                        return regex.test(body);
                    }""",
                    arg=current_page + 1,
                    timeout=DEFAULT_TIMEOUT_MS,
                )
                await observe_latency_async(
                    controller,
                    time.perf_counter() - started_at,
                    logger,
                    db,
                    worker_id,
                    progress_id=batch.id,
                    evento="page_turn",
                )
                await controller.async_sleep()

            ScrapingProgressService.complete_batch(db, batch.id)
            emit_log(
                logger,
                db,
                worker_id,
                "info",
                "batch_completed",
                f"Enriquecimiento completo {batch.fecha_inicio.year}: {total_results} resultados en {total_pages} páginas",
                progress_id=batch.id,
                sentencias_por_minuto=calculate_sentencias_per_minute(
                    count_sentencias_for_batch(db, batch, enriched_only=True),
                    batch_started_at,
                ),
            )
            await context.close()
            return
        except SessionExpiredError as exc:
            db.refresh(batch)
            emit_log(
                logger,
                db,
                worker_id,
                "warn",
                "session_expired",
                f"Sesión expirada en enriquecimiento {batch.fecha_inicio.year}. Reabro context y retomo desde página {(batch.pagina_actual or 0) + 1}. Intento {session_attempt}/3. {exc}",
                progress_id=batch.id,
            )
            if context is not None:
                await context.close()
            continue
        except GracefulShutdownRequested:
            if context is not None:
                await context.close()
            raise
        except Exception as exc:
            db.rollback()
            ScrapingProgressService.fail_batch(db, batch.id, str(exc))
            emit_log(
                logger,
                db,
                worker_id,
                "error",
                "batch_failed",
                f"Falló enriquecimiento {batch.fecha_inicio.year}: {exc}",
                progress_id=batch.id,
            )
            if context is not None:
                await context.close()
            return

    ScrapingProgressService.fail_batch(db, batch.id, "Session expired repeatedly during enrichment")
    emit_log(
        logger,
        db,
        worker_id,
        "error",
        "batch_failed",
        f"Enriquecimiento {batch.fecha_inicio.year} agotó reintentos de sesión",
        progress_id=batch.id,
    )


def show_status() -> bool:
    """Prints current progress without touching the remote site."""
    logger = get_worker_logger("STATUS")
    db = SessionLocal()
    try:
        summary = ScrapingProgressService.get_overall_progress(db)
        total_sentencias = int(
            db.query(func.count(Sentencia.id)).filter(Sentencia.deleted_at.is_(None)).scalar() or 0
        )
        enriched_sentencias = int(
            db.query(func.count(Sentencia.id))
            .filter(Sentencia.deleted_at.is_(None), Sentencia.texto_completo.is_not(None))
            .scalar()
            or 0
        )

        print("Estado BJN")
        print(f"- Lotes totales: {summary['totalBatches']}")
        print(f"- Lotes completados: {summary['completedBatches']}")
        print(f"- Lotes en progreso: {summary['inProgressBatches']}")
        print(f"- Lotes pendientes: {summary['pendingBatches']}")
        print(f"- Lotes fallidos: {summary['failedBatches']}")
        print(f"- Sentencias registradas: {total_sentencias}")
        print(f"- Sentencias con texto completo: {enriched_sentencias}")
        print(f"- Sentencias descargadas (tracking): {summary['totalSentenciasDescargadas']}")
        print(f"- Sentencias fallidas (tracking): {summary['totalSentenciasFallidas']}")
        print("")
        print("Progreso por año")

        batches = db.query(ScrapingProgress).order_by(ScrapingProgress.fecha_inicio.asc()).all()
        if not batches:
            print("- Sin lotes creados todavía")
            return True

        for batch in batches:
            year = batch.fecha_inicio.year
            print(
                f"- {year}: estado={batch.estado}, pagina={batch.pagina_actual}/{batch.total_paginas or 0}, "
                f"encontradas={batch.sentencias_encontradas}, descargadas={batch.sentencias_descargadas}, "
                f"fallidas={batch.sentencias_fallidas}"
            )
        return True
    except SQLAlchemyError as exc:
        print(f"Status no disponible: no pude conectar a la base de datos ({exc.__class__.__name__}).")
        return False
    finally:
        db.close()
        logger.debug("Status generado", extra={"worker": "STATUS"})


def run_inventory() -> None:
    """Entry point for the synchronous inventory phase."""
    worker_id = "WORKER-1"
    logger = get_worker_logger(worker_id)
    db = SessionLocal()
    ACTIVE_WORKER_IDS.add(worker_id)
    try:
        ScrapingProgressService.initialize_partitions(db, INVENTORY_YEAR_START, INVENTORY_YEAR_END)
        requeued = requeue_paused_batches(db)
        if requeued:
            emit_log(
                logger,
                db,
                worker_id,
                "info",
                "requeue_paused",
                f"Reencolé {requeued} lote/s pausados antes de inventario.",
            )

        while not SHUTDOWN_REQUESTED:
            batch = ScrapingProgressService.claim_next_batch(db, worker_id)
            if batch is None:
                emit_log(logger, db, worker_id, "info", "inventory_done", "No quedan lotes para inventario.")
                return
            process_inventory_batch(db, batch, worker_id)
            db.expire_all()
    except GracefulShutdownRequested:
        emit_log(
            logger,
            db,
            worker_id,
            "warn",
            "shutdown",
            "Inventario interrumpido por señal. Pauso lotes activos.",
        )
        raise
    finally:
        db.close()
        ACTIVE_WORKER_IDS.discard(worker_id)


async def enrichment_worker(worker_number: int, browser: Browser) -> None:
    """Async worker loop that claims enrichment batches until exhaustion."""
    worker_id = f"WORKER-{worker_number}"
    logger = get_worker_logger(worker_id)
    db = SessionLocal()
    ACTIVE_WORKER_IDS.add(worker_id)
    try:
        while not SHUTDOWN_REQUESTED:
            ensure_not_shutdown()
            batch = ScrapingProgressService.claim_next_batch(db, worker_id)
            if batch is None:
                emit_log(logger, db, worker_id, "info", "worker_done", "No hay más lotes para este worker.")
                return
            await process_enrichment_batch(browser, db, batch, worker_id)
            db.expire_all()
    except GracefulShutdownRequested:
        emit_log(
            logger,
            db,
            worker_id,
            "warn",
            "shutdown",
            "Worker interrumpido por señal. Pauso lotes activos.",
        )
        raise
    finally:
        db.close()
        ACTIVE_WORKER_IDS.discard(worker_id)


async def run_enrichment_async(workers: int) -> None:
    """Entry point for the asynchronous enrichment phase."""
    global ASYNC_SHUTDOWN_EVENT

    main_logger = get_worker_logger("MAIN")
    db = SessionLocal()
    try:
        ScrapingProgressService.initialize_partitions(db, INVENTORY_YEAR_START, INVENTORY_YEAR_END)
        prepare_batches_for_enrichment(db, main_logger)
    finally:
        db.close()

    ASYNC_SHUTDOWN_EVENT = asyncio.Event()
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        try:
            tasks = [asyncio.create_task(enrichment_worker(index + 1, browser)) for index in range(workers)]
            await asyncio.gather(*tasks)
        finally:
            await browser.close()
            ASYNC_SHUTDOWN_EVENT = None


def parse_args() -> argparse.Namespace:
    """Parses CLI arguments."""
    parser = argparse.ArgumentParser(description="Crawler resiliente para jurisprudencia BJN")
    parser.add_argument(
        "--fase",
        choices=("inventario", "enriquecimiento"),
        help="Fase del crawler a ejecutar",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Cantidad de workers para enriquecimiento (default: 4)",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Muestra progreso actual sin ejecutar scraping",
    )
    return parser.parse_args()


def main() -> int:
    """CLI entry point."""
    install_signal_handlers()
    args = parse_args()

    if args.status:
        return 0 if show_status() else 1

    if args.fase is None:
        print("Debés indicar --fase inventario | enriquecimiento, o usar --status.")
        return 1

    try:
        if args.fase == "inventario":
            run_inventory()
        elif args.fase == "enriquecimiento":
            asyncio.run(run_enrichment_async(max(args.workers, 1)))
        return 0
    except GracefulShutdownRequested:
        pause_active_batches("Paused by signal")
        return 130
    except KeyboardInterrupt:
        pause_active_batches("Paused by keyboard interrupt")
        return 130
    except SQLAlchemyError as exc:
        print(f"Error de base de datos: {exc.__class__.__name__}")
        return 1
    finally:
        if SHUTDOWN_REQUESTED:
            pause_active_batches("Paused by signal")


if __name__ == "__main__":
    raise SystemExit(main())
