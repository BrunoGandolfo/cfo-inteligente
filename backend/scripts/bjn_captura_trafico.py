"""Captura forense del trafico de red al abrir una sentencia del BJN.

Script temporal de investigacion:
- abre la busqueda selectiva
- ejecuta una busqueda simple para 2024
- registra requests y responses justo antes del click en la primera sentencia
- captura tambien el trafico del popup si se abre una nueva ventana
- guarda todo en bjn_screenshots/trafico_popup.json
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.async_api import BrowserContext, Page, Request, Response, async_playwright


BUSQUEDA_SIMPLE_URL = "http://bjn.poderjudicial.gub.uy/BJNPUBLICA/busquedaSimple.seam"
BUSQUEDA_SELECTIVA_URL = "http://bjn.poderjudicial.gub.uy/BJNPUBLICA/busquedaSelectiva.seam"
DEFAULT_TIMEOUT_MS = 30_000
AJAX_SLEEP_SECONDS = 6.0
POST_CLICK_WAIT_SECONDS = 5.0
SCREENSHOT_DIR = Path(__file__).resolve().parent / "bjn_screenshots"
OUTPUT_PATH = SCREENSHOT_DIR / "trafico_popup.json"

SELECTORS = {
    "link_busqueda_selectiva": '[id="j_id10:j_id11"]',
    "fecha_desde": '[id="formBusqueda:j_id20:j_id23:fechaDesdeCalInputDate"]',
    "fecha_desde_hidden": '[id="formBusqueda:j_id20:j_id23:fechaDesdeCalInputCurrentDate"]',
    "fecha_hasta": '[id="formBusqueda:j_id20:j_id147:fechaHastaCalInputDate"]',
    "fecha_hasta_hidden": '[id="formBusqueda:j_id20:j_id147:fechaHastaCalInputCurrentDate"]',
    "resultados_por_pagina_field": '[id="formBusqueda:j_id20:j_id223:cantPagcomboboxField"]',
    "resultados_por_pagina_hidden": '[id="formBusqueda:j_id20:j_id223:cantPagcomboboxValue"]',
    "buscar": '[id="formBusqueda:j_id20:Search"]',
    "grid_resultados": '[id="formResultados:dataTable"]',
    "primer_click_sentencia": 'td[id="formResultados:dataTable:0:colFec"]',
}

BLOCKED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".css", ".woff", ".woff2")
BLOCKED_RESOURCE_TYPES = {"image", "media", "font", "stylesheet"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def month_year_from_date(value: str) -> str:
    _, month, year = value.split("/")
    return f"{month}/{year}"


def safe_decode_body(raw_body: bytes) -> str:
    for encoding in ("utf-8", "latin-1"):
        try:
            return raw_body.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw_body.decode("utf-8", errors="replace")


async def build_response_record(response: Response, observer: str, page_label: str) -> dict[str, Any]:
    body_preview = ""
    body_size_bytes: int | None = None
    body_error = ""
    body_text = ""
    try:
        raw_body = await response.body()
        body_size_bytes = len(raw_body)
        body_text = safe_decode_body(raw_body)
        body_preview = body_text[:2000]
    except Exception as exc:
        body_error = str(exc)
        try:
            body_text = await response.text()
            body_preview = body_text[:2000]
            body_size_bytes = len(body_text.encode("utf-8", errors="replace"))
        except Exception as nested_exc:
            body_error = f"{body_error} | fallback_text_error={nested_exc}"
            body_preview = ""
            body_text = ""

    try:
        headers = await response.all_headers()
    except Exception:
        headers = {}

    upper_body = body_text.upper()
    return {
        "captured_at": utc_now_iso(),
        "observer": observer,
        "page_label": page_label,
        "resource_type": response.request.resource_type,
        "method": response.request.method,
        "url": response.url,
        "status": response.status,
        "content_type": headers.get("content-type", ""),
        "body_size_bytes": body_size_bytes,
        "body_preview": body_preview,
        "body_error": body_error,
        "contains_textoSentenciaBox": "textosentenciabox" in body_text.lower(),
        "contains_legal_text_markers": any(
            token in upper_body for token in ("RESULTANDO", "CONSIDERANDO", "VISTOS", "SE FALLA")
        ),
    }


async def install_route_blocking(context: BrowserContext) -> None:
    async def route_handler(route) -> None:
        request = route.request
        url_lower = request.url.lower()
        if request.resource_type in BLOCKED_RESOURCE_TYPES or url_lower.endswith(BLOCKED_EXTENSIONS):
            await route.abort()
            return
        await route.continue_()

    await context.route("**/*", route_handler)


def add_request_listener(page: Page, page_label: str, sink: list[dict[str, Any]]) -> None:
    def handle_request(request: Request) -> None:
        post_data = request.post_data
        if callable(post_data):
            post_data = post_data()
        sink.append(
            {
                "captured_at": utc_now_iso(),
                "observer": "page",
                "page_label": page_label,
                "resource_type": request.resource_type,
                "method": request.method,
                "url": request.url,
                "post_data_preview": (post_data or "")[:1000],
            }
        )

    page.on("request", handle_request)


def add_response_listener(
    page: Page,
    page_label: str,
    sink: list[dict[str, Any]],
    pending_tasks: set[asyncio.Task[Any]],
) -> None:
    async def handle_response(response: Response) -> None:
        sink.append(await build_response_record(response, "page", page_label))

    def schedule_response(response: Response) -> None:
        task = asyncio.create_task(handle_response(response))
        pending_tasks.add(task)
        task.add_done_callback(pending_tasks.discard)

    page.on("response", schedule_response)


def attach_page_collectors(
    page: Page,
    page_label: str,
    requests: list[dict[str, Any]],
    responses: list[dict[str, Any]],
    pending_tasks: set[asyncio.Task[Any]],
    pages_info: list[dict[str, Any]],
) -> None:
    pages_info.append(
        {
            "captured_at": utc_now_iso(),
            "page_label": page_label,
            "url_at_attach": page.url,
        }
    )
    add_request_listener(page, page_label, requests)
    add_response_listener(page, page_label, responses, pending_tasks)


def attach_context_collectors(
    context: BrowserContext,
    requests: list[dict[str, Any]],
    responses: list[dict[str, Any]],
    pending_tasks: set[asyncio.Task[Any]],
    page_labels: dict[int, str],
) -> None:
    def infer_page_label_from_request(request: Request) -> str:
        try:
            frame = request.frame
            if frame is not None and frame.page is not None:
                return page_labels.get(id(frame.page), "UNKNOWN")
        except Exception:
            pass
        return "UNKNOWN"

    def handle_request(request: Request) -> None:
        post_data = request.post_data
        if callable(post_data):
            post_data = post_data()
        requests.append(
            {
                "captured_at": utc_now_iso(),
                "observer": "context",
                "page_label": infer_page_label_from_request(request),
                "resource_type": request.resource_type,
                "method": request.method,
                "url": request.url,
                "post_data_preview": (post_data or "")[:1000],
            }
        )

    async def handle_response(response: Response) -> None:
        responses.append(
            await build_response_record(
                response,
                "context",
                infer_page_label_from_request(response.request),
            )
        )

    def schedule_response(response: Response) -> None:
        task = asyncio.create_task(handle_response(response))
        pending_tasks.add(task)
        task.add_done_callback(pending_tasks.discard)

    context.on("request", handle_request)
    context.on("response", schedule_response)


async def ensure_selectiva(page: Page) -> None:
    await page.goto(BUSQUEDA_SELECTIVA_URL, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)
    try:
        await page.locator(SELECTORS["fecha_desde"]).wait_for(timeout=10_000)
        return
    except Exception:
        await page.goto(BUSQUEDA_SIMPLE_URL, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)
        await page.locator(SELECTORS["link_busqueda_selectiva"]).click()
        await page.wait_for_url("**/busquedaSelectiva.seam*", timeout=DEFAULT_TIMEOUT_MS)
        await page.locator(SELECTORS["fecha_desde"]).wait_for(timeout=DEFAULT_TIMEOUT_MS)


async def search_2024(page: Page) -> None:
    fecha_desde = "01/01/2024"
    fecha_hasta = "31/12/2024"

    await page.locator(SELECTORS["fecha_desde"]).fill(fecha_desde)
    await page.locator(SELECTORS["fecha_hasta"]).fill(fecha_hasta)
    await page.evaluate(
        """
        ({fechaDesdeHidden, fechaHastaHidden, fechaDesdeValue, fechaHastaValue, cantPagField, cantPagHidden}) => {
            const desdeHidden = document.querySelector(fechaDesdeHidden);
            const hastaHidden = document.querySelector(fechaHastaHidden);
            const cantField = document.querySelector(cantPagField);
            const cantHiddenEl = document.querySelector(cantPagHidden);
            if (!desdeHidden || !hastaHidden || !cantField || !cantHiddenEl) {
                throw new Error("No encontre los hidden fields necesarios");
            }
            desdeHidden.value = fechaDesdeValue;
            hastaHidden.value = fechaHastaValue;
            cantField.value = "200";
            cantHiddenEl.value = "200";
            cantField.dispatchEvent(new Event("change", { bubbles: true }));
            cantField.dispatchEvent(new Event("blur", { bubbles: true }));
        }
        """,
        {
            "fechaDesdeHidden": SELECTORS["fecha_desde_hidden"],
            "fechaHastaHidden": SELECTORS["fecha_hasta_hidden"],
            "fechaDesdeValue": month_year_from_date(fecha_desde),
            "fechaHastaValue": month_year_from_date(fecha_hasta),
            "cantPagField": SELECTORS["resultados_por_pagina_field"],
            "cantPagHidden": SELECTORS["resultados_por_pagina_hidden"],
        },
    )
    await asyncio.sleep(AJAX_SLEEP_SECONDS)
    await page.locator(SELECTORS["buscar"]).click()
    await page.locator(SELECTORS["grid_resultados"]).wait_for(timeout=DEFAULT_TIMEOUT_MS)
    await asyncio.sleep(AJAX_SLEEP_SECONDS)


def summarize_traffic(
    requests: list[dict[str, Any]],
    responses: list[dict[str, Any]],
) -> dict[str, Any]:
    deduped_requests = list(
        {
            (
                entry["method"],
                entry["resource_type"],
                entry["url"],
                entry.get("post_data_preview", ""),
            ): entry
            for entry in requests
        }.values()
    )
    deduped_responses = list(
        {
            (
                entry["method"],
                entry["resource_type"],
                entry["url"],
                entry.get("status"),
                entry.get("content_type", ""),
                entry.get("body_size_bytes"),
            ): entry
            for entry in responses
        }.values()
    )
    unique_urls = sorted({entry["url"] for entry in deduped_requests + deduped_responses})
    content_types = sorted(
        {entry["content_type"] for entry in deduped_responses if entry.get("content_type")}
    )
    popup_text_hits = [
        {
            "url": entry["url"],
            "content_type": entry.get("content_type", ""),
            "page_label": entry.get("page_label", ""),
            "observer": entry.get("observer", ""),
        }
        for entry in deduped_responses
        if entry.get("contains_textoSentenciaBox")
    ]
    legal_text_hits = [
        {
            "url": entry["url"],
            "content_type": entry.get("content_type", ""),
            "page_label": entry.get("page_label", ""),
            "observer": entry.get("observer", ""),
        }
        for entry in deduped_responses
        if entry.get("contains_legal_text_markers")
    ]
    return {
        "request_count": len(deduped_requests),
        "response_count": len(deduped_responses),
        "unique_url_count": len(unique_urls),
        "unique_urls": unique_urls,
        "content_types": content_types,
        "responses_with_textoSentenciaBox": popup_text_hits,
        "responses_with_legal_text_markers": legal_text_hits,
    }


async def main() -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    captured_requests: list[dict[str, Any]] = []
    captured_responses: list[dict[str, Any]] = []
    captured_pages: list[dict[str, Any]] = []
    pending_response_tasks: set[asyncio.Task[Any]] = set()
    popup_urls: list[str] = []
    page_labels: dict[int, str] = {}
    click_info: dict[str, Any] = {
        "clicked_selector": SELECTORS["primer_click_sentencia"],
        "click_started_at": None,
        "click_finished_at": None,
        "popup_url": None,
    }

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False, args=["--no-sandbox"])
        context = await browser.new_context()
        await install_route_blocking(context)
        attach_context_collectors(
            context,
            captured_requests,
            captured_responses,
            pending_response_tasks,
            page_labels,
        )

        page = await context.new_page()
        page.set_default_timeout(DEFAULT_TIMEOUT_MS)

        popup_counter = 0

        def handle_new_page(new_page: Page) -> None:
            nonlocal popup_counter
            popup_counter += 1
            page_label = f"POPUP-{popup_counter}"
            page_labels[id(new_page)] = page_label
            attach_page_collectors(
                new_page,
                page_label,
                captured_requests,
                captured_responses,
                pending_response_tasks,
                captured_pages,
            )

        context.on("page", handle_new_page)

        await ensure_selectiva(page)
        await search_2024(page)

        page_labels[id(page)] = "MAIN"
        attach_page_collectors(
            page,
            "MAIN",
            captured_requests,
            captured_responses,
            pending_response_tasks,
            captured_pages,
        )

        popup_page: Page | None = None
        click_info["click_started_at"] = utc_now_iso()
        try:
            async with page.expect_popup(timeout=15_000) as popup_info:
                await page.locator(SELECTORS["primer_click_sentencia"]).click()
            popup_page = await popup_info.value
            await popup_page.wait_for_load_state("domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)
            click_info["popup_url"] = popup_page.url
            popup_urls.append(popup_page.url)
        except Exception as exc:
            click_info["popup_error"] = str(exc)
        click_info["click_finished_at"] = utc_now_iso()

        await asyncio.sleep(POST_CLICK_WAIT_SECONDS)

        if pending_response_tasks:
            await asyncio.gather(*list(pending_response_tasks), return_exceptions=True)

        summary = summarize_traffic(captured_requests, captured_responses)
        result = {
            "generated_at": utc_now_iso(),
            "search_url": BUSQUEDA_SELECTIVA_URL,
            "click": click_info,
            "popup_urls": popup_urls,
            "pages": captured_pages,
            "requests": captured_requests,
            "responses": captured_responses,
            "summary": summary,
        }
        OUTPUT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

        print(f"Requests capturados: {summary['request_count']}")
        print(f"Responses capturadas: {summary['response_count']}")
        print(f"URLs únicas: {summary['unique_url_count']}")
        print("Content-Types encontrados:")
        for content_type in summary["content_types"]:
            print(f"  - {content_type}")
        print("URLs únicas:")
        for url in summary["unique_urls"]:
            print(f"  - {url}")
        if summary["responses_with_textoSentenciaBox"]:
            print("Se encontró 'textoSentenciaBox' en responses:")
            for hit in summary["responses_with_textoSentenciaBox"]:
                print(f"  - {hit['page_label']} {hit['url']}")
        else:
            print("No se encontró 'textoSentenciaBox' en los cuerpos capturados.")
        if summary["responses_with_legal_text_markers"]:
            print("Se encontraron marcadores de texto jurídico en responses:")
            for hit in summary["responses_with_legal_text_markers"]:
                print(f"  - {hit['page_label']} {hit['url']}")
        else:
            print("No se detectaron marcadores obvios de texto jurídico en los cuerpos capturados.")

        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
