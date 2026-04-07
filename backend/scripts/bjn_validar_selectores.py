"""Validates popup selectors against raw Hoja de Insumo HTML."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import BrowserContext, Page, Response, sync_playwright


BUSQUEDA_SIMPLE_URL = "http://bjn.poderjudicial.gub.uy/BJNPUBLICA/busquedaSimple.seam"
BUSQUEDA_SELECTIVA_URL = "http://bjn.poderjudicial.gub.uy/BJNPUBLICA/busquedaSelectiva.seam"
KNOWN_POPUP_URL = "http://bjn.poderjudicial.gub.uy/BJNPUBLICA/hojaInsumo2.seam?cid=108878"
DEFAULT_TIMEOUT_MS = 30_000
AJAX_SLEEP_SECONDS = 6.0
OUTPUT_DIR = Path(__file__).resolve().parent / "bjn_screenshots"
TRAFFIC_PATH = OUTPUT_DIR / "trafico_popup.json"
HTML_OUTPUT_PATH = OUTPUT_DIR / "popup_html_ejemplo.html"

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

POPUP_FIELD_SELECTORS = [
    ("numero", "table#j_id3 tbody td:nth-child(1)"),
    ("sede", "table#j_id3 tbody td:nth-child(2)"),
    ("importancia", "table#j_id3 tbody td:nth-child(3)"),
    ("tipo", "table#j_id3 tbody td:nth-child(4)"),
    ("fecha", "table#j_id21 tbody td:nth-child(1)"),
    ("materias", "table#j_id35 tbody td"),
    ("firmantes", "table#gridFirmantes tbody td"),
    ("redactores", "table#gridRedactores tbody td"),
    ("abstract", "table#j_id77 tbody td:nth-child(1)"),
    ("descriptores", "table#j_id77 tbody td:nth-child(2)"),
    ("descriptores_extra", "table#j_id89 tbody td"),
    ("resumen", "table#j_id107 tbody td"),
    ("texto_completo", "span#textoSentenciaBox"),
    ("texto_fallback", "#panelTextoSent_body"),
]


def normalize_space(text: str) -> str:
    return " ".join((text or "").split())


def month_year_from_date(value: str) -> str:
    _, month, year = value.split("/")
    return f"{month}/{year}"


def install_route_blocking(context: BrowserContext) -> None:
    def route_handler(route) -> None:
        request = route.request
        url_lower = request.url.lower()
        if request.resource_type in BLOCKED_RESOURCE_TYPES or url_lower.endswith(BLOCKED_EXTENSIONS):
            route.abort()
            return
        route.continue_()

    context.route("**/*", route_handler)


def load_popup_urls() -> list[str]:
    if not TRAFFIC_PATH.exists():
        return [KNOWN_POPUP_URL]

    payload = json.loads(TRAFFIC_PATH.read_text(encoding="utf-8"))
    urls: list[str] = []
    click_popup_url = payload.get("click", {}).get("popup_url")
    if click_popup_url:
        urls.append(click_popup_url)
    urls.extend(payload.get("popup_urls", []))
    for response in payload.get("responses", []):
        if "hojaInsumo2.seam" in response.get("url", ""):
            urls.append(response["url"])
    urls.append(KNOWN_POPUP_URL)

    unique_urls: list[str] = []
    seen: set[str] = set()
    for url in urls:
        if not url or url in seen:
            continue
        seen.add(url)
        unique_urls.append(url)
    return unique_urls


def try_requests_fetch(url: str) -> str | None:
    try:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print(f"[requests] {url} -> status {response.status_code}")
            return None
        text = response.text
        if "Hoja de Insumo" not in text and "textoSentenciaBox" not in text:
            print(f"[requests] {url} -> 200 pero no parece HTML de sentencia")
            return None
        print(f"[requests] HTML obtenido desde {url} ({len(text)} chars)")
        return text
    except Exception as exc:
        print(f"[requests] {url} fallo: {exc}")
        return None


def fresh_popup_html_with_playwright() -> str:
    popup_html: dict[str, str] = {}

    def maybe_capture_popup_response(response: Response) -> None:
        if "hojaInsumo2.seam" not in response.url:
            return
        try:
            if response.status != 200:
                return
            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type:
                return
            popup_html["url"] = response.url
            popup_html["html"] = response.text()
        except Exception:
            return

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context()
        install_route_blocking(context)
        context.on("response", maybe_capture_popup_response)

        page = context.new_page()
        page.set_default_timeout(DEFAULT_TIMEOUT_MS)
        page.goto(BUSQUEDA_SELECTIVA_URL, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)
        try:
            page.locator(SELECTORS["fecha_desde"]).wait_for(timeout=10_000)
        except Exception:
            page.goto(BUSQUEDA_SIMPLE_URL, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)
            page.locator(SELECTORS["link_busqueda_selectiva"]).click()
            page.wait_for_url("**/busquedaSelectiva.seam*", timeout=DEFAULT_TIMEOUT_MS)
            page.locator(SELECTORS["fecha_desde"]).wait_for(timeout=DEFAULT_TIMEOUT_MS)

        fecha_desde = "01/01/2024"
        fecha_hasta = "31/12/2024"
        page.locator(SELECTORS["fecha_desde"]).fill(fecha_desde)
        page.locator(SELECTORS["fecha_hasta"]).fill(fecha_hasta)
        page.evaluate(
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
        time.sleep(AJAX_SLEEP_SECONDS)
        page.locator(SELECTORS["buscar"]).click()
        page.locator(SELECTORS["grid_resultados"]).wait_for(timeout=DEFAULT_TIMEOUT_MS)
        time.sleep(AJAX_SLEEP_SECONDS)

        with page.expect_popup(timeout=15_000) as popup_info:
            page.locator(SELECTORS["primer_click_sentencia"]).click()
        popup = popup_info.value
        popup.wait_for_load_state("domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)

        started_at = time.time()
        while "html" not in popup_html and (time.time() - started_at) < 10:
            time.sleep(0.2)

        if "html" not in popup_html:
            popup_html["url"] = popup.url
            popup_html["html"] = popup.content()

        popup.close()
        context.close()
        browser.close()

    print(f"[playwright] HTML fresco obtenido desde {popup_html['url']} ({len(popup_html['html'])} chars)")
    return popup_html["html"]


def resolve_popup_html() -> tuple[str, str]:
    popup_urls = load_popup_urls()
    print("Popup URLs candidatas:")
    for url in popup_urls:
        print(f"  - {url}")

    for url in popup_urls:
        html = try_requests_fetch(url)
        if html:
            return html, f"requests:{url}"

    html = fresh_popup_html_with_playwright()
    return html, "playwright:fresh_capture"


def print_available_structures(soup: BeautifulSoup) -> None:
    table_ids = [tag.get("id") for tag in soup.select("table[id]") if tag.get("id")]
    table_ids = sorted(dict.fromkeys(table_ids))
    any_ids = [tag.get("id") for tag in soup.select("[id]") if tag.get("id")]
    any_ids = sorted(dict.fromkeys(any_ids))
    print(f"    Tables con id: {table_ids[:30]}")
    print(f"    IDs disponibles: {any_ids[:50]}")


def validate_selectors(html: str) -> None:
    soup = BeautifulSoup(html, "html.parser")
    print(f"HTML length: {len(html)} chars")
    print(f"Title: {normalize_space(soup.title.get_text(' ', strip=True)) if soup.title else '(sin title)'}")

    for field_name, selector in POPUP_FIELD_SELECTORS:
        matches = soup.select(selector)
        found = bool(matches)
        print(f"\n[{field_name}] {selector}")
        print(f"  ¿Se encontró?: {'sí' if found else 'no'}")
        if found:
            texts = [normalize_space(match.get_text(' ', strip=True)) for match in matches]
            texts = [text for text in texts if text]
            joined = " | ".join(texts)
            print(f"  Coincidencias: {len(matches)}")
            print(f"  Texto: {joined[:200]}")
        else:
            print_available_structures(soup)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    html, source = resolve_popup_html()
    HTML_OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"\nHTML guardado en {HTML_OUTPUT_PATH}")
    print(f"Fuente utilizada: {source}")
    validate_selectors(html)


if __name__ == "__main__":
    main()
