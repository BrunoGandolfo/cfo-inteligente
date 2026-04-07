"""Explora el comportamiento de "Búsqueda Selectiva" en el BJN público."""

from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


BASE_URL = "http://bjn.poderjudicial.gub.uy/BJNPUBLICA/busquedaSimple.seam"
SCREENSHOT_DIR = Path(__file__).resolve().parent / "bjn_screenshots"
REPORT_PATH = SCREENSHOT_DIR / "investigacion_selectiva_report.json"
FORM_PATH = SCREENSHOT_DIR / "busqueda_selectiva_form.html"
TIMEOUT_MS = 30_000
AJAX_SLEEP_SECONDS = 5
MAX_SITE_REQUESTS = 15
ALLOWED_SCRIPT_FRAGMENTS = (
    "AjaxScript",
    "ajax4jsf/javascript/scripts/form.js",
    "PrototypeScript",
)


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def save_page_artifacts(page, name: str) -> Dict[str, str]:
    screenshot = SCREENSHOT_DIR / f"{name}.png"
    html = SCREENSHOT_DIR / f"{name}.html"
    page.screenshot(path=str(screenshot), full_page=True)
    write_text(html, page.content())
    return {
        "screenshot_path": str(screenshot.resolve()),
        "html_path": str(html.resolve()),
    }


def collect_links(page) -> List[Dict[str, str]]:
    return page.evaluate(
        """
        () => Array.from(document.querySelectorAll('a')).map(a => ({
            text: (a.textContent || '').replace(/\\s+/g, ' ').trim(),
            href: a.href || '',
            id: a.id || '',
            onclick: a.getAttribute('onclick') || ''
        })).filter(item => item.text || item.href || item.id)
        """
    )


def collect_form_summary(page) -> Dict[str, Any]:
    return page.evaluate(
        """
        () => {
            const normalize = text => (text || '').replace(/\\s+/g, ' ').trim();
            const form = document.querySelector('#formBusqueda');
            if (!form) {
                return { exists: false };
            }
            const controls = Array.from(form.querySelectorAll('input, select, textarea')).map(el => {
                const row = el.closest('tr');
                const rowText = row ? normalize(row.textContent) : '';
                const optionTexts = el.tagName.toLowerCase() === 'select'
                    ? Array.from(el.options).map(opt => normalize(opt.textContent))
                    : [];
                return {
                    tag: el.tagName.toLowerCase(),
                    type: el.getAttribute('type') || '',
                    name: el.getAttribute('name') || '',
                    id: el.id || '',
                    value: el.value || '',
                    checked: !!el.checked,
                    row_text: rowText,
                    options: optionTexts,
                };
            });
            return {
                exists: true,
                action: form.getAttribute('action') || '',
                method: form.getAttribute('method') || '',
                outer_html: form.outerHTML,
                controls,
            };
        }
        """
    )


def summarize_state(page) -> Dict[str, Any]:
    content = page.content()
    form = collect_form_summary(page)
    return {
        "url": page.url,
        "title": page.title(),
        "dom_hash": sha256_text(content),
        "links": collect_links(page),
        "form_exists": form.get("exists", False),
        "controls_count": len(form.get("controls", [])),
        "form": form,
    }


def extract_structured_filters(form: Dict[str, Any]) -> Dict[str, List[str]]:
    buckets = {
        "sedes": [],
        "materias": [],
        "tipos_resolucion": [],
        "anios": [],
        "fechas": [],
        "importancias": [],
    }
    for control in form.get("controls", []):
        haystack = " ".join(
            [
                control.get("id", ""),
                control.get("name", ""),
                control.get("row_text", ""),
            ]
        ).lower()
        options = control.get("options", [])
        if "sede" in haystack:
            buckets["sedes"].extend(options)
        if "materia" in haystack:
            buckets["materias"].extend(options)
        if "resol" in haystack or "tipo" in haystack:
            buckets["tipos_resolucion"].extend(options)
        if "año" in haystack or "anio" in haystack or "year" in haystack:
            buckets["anios"].extend(options)
        if "fecha" in haystack or control.get("type") == "date":
            buckets["fechas"].append(haystack)
        if "importancia" in haystack:
            buckets["importancias"].extend(options)
    for key, values in buckets.items():
        deduped: List[str] = []
        for value in values:
            value = value.strip()
            if value and value not in deduped:
                deduped.append(value)
        buckets[key] = deduped
    return buckets


def has_structured_filters(filters: Dict[str, List[str]]) -> bool:
    return any(filters[key] for key in filters)


def parse_results_state(page) -> Dict[str, Any]:
    body_text = page.locator("body").inner_text()
    total = None
    page_number = None
    pages_total = None

    total_match = re.search(r"(\d+)\s+resultado/s", body_text, flags=re.IGNORECASE)
    if total_match:
        total = int(total_match.group(1))

    page_match = re.search(r"Página\s+(\d+)\s+de\s+(\d+)", body_text, flags=re.IGNORECASE)
    if page_match:
        page_number = int(page_match.group(1))
        pages_total = int(page_match.group(2))

    current_rows = page.locator("[id='formResultados:grid'] tr.rich-table-row").count()
    return {
        "total_resultados": total,
        "pagina_actual": page_number,
        "paginas_totales": pages_total,
        "resultados_en_pagina": current_rows,
    }


def run_year_tests(page, report: Dict[str, Any]) -> List[Dict[str, Any]]:
    desde = page.locator('[id="formBusqueda:j_id20:j_id23:fechaDesdeCalInputDate"]')
    hasta = page.locator('[id="formBusqueda:j_id20:j_id147:fechaHastaCalInputDate"]')
    buscar = page.locator('[id="formBusqueda:j_id20:Search"]')

    if desde.count() == 0 or hasta.count() == 0 or buscar.count() == 0:
        return [
            {
                "status": "no_ejecutado",
                "detail": "No se encontraron los controles de fecha o el botón Buscar en la búsqueda selectiva.",
            }
        ]

    resultados: List[Dict[str, Any]] = []
    for year in (2024, 2023, 2020):
        desde.fill(f"01/01/{year}")
        hasta.fill(f"31/12/{year}")
        buscar.click()
        time.sleep(AJAX_SLEEP_SECONDS)
        artifact = save_page_artifacts(page, f"selectiva_test_{year}")
        parsed = parse_results_state(page)
        resultados.append(
            {
                "year": year,
                "fecha_desde": f"01/01/{year}",
                "fecha_hasta": f"31/12/{year}",
                **parsed,
                **artifact,
            }
        )
    return resultados


def main() -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    request_log: List[Dict[str, str]] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(TIMEOUT_MS)

        def handle_route(route) -> None:
            request = route.request
            if request.url.startswith("http://bjn.poderjudicial.gub.uy/BJNPUBLICA"):
                if request.resource_type in {"document", "script", "xhr", "fetch"}:
                    if request.resource_type == "document":
                        if any(
                            request.url.endswith(ext)
                            for ext in (".gif", ".png", ".jpg", ".jpeg", ".ico", ".css", ".js", ".pdf")
                        ):
                            route.abort()
                            return
                    if request.resource_type == "script":
                        if not any(fragment in request.url for fragment in ALLOWED_SCRIPT_FRAGMENTS):
                            route.abort()
                            return
                    if len(request_log) >= MAX_SITE_REQUESTS:
                        route.abort()
                        return
                    request_log.append(
                        {
                            "resource_type": request.resource_type,
                            "method": request.method,
                            "url": request.url,
                        }
                    )
                    route.continue_()
                    return
                route.abort()
                return
            route.abort()

        page.route("**/*", handle_route)

        report: Dict[str, Any] = {
            "base_url": BASE_URL,
            "site_request_limit": MAX_SITE_REQUESTS,
            "selector_css_exacto": '[id="j_id10:j_id11"]',
            "request_log": [],
            "otros_links_descubiertos": [],
            "filtros": [],
            "dropdowns": [],
            "structured_filters": {},
            "filtro_tests": [],
            "artifacts": [],
        }

        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=TIMEOUT_MS)
        page.wait_for_function("typeof A4J !== 'undefined'", timeout=TIMEOUT_MS)
        report["artifacts"].append(save_page_artifacts(page, "selectiva_01_inicial"))

        estado_inicial = summarize_state(page)
        report["estado_inicial"] = {
            "url": estado_inicial["url"],
            "title": estado_inicial["title"],
            "dom_hash": estado_inicial["dom_hash"],
            "controls_count": estado_inicial["controls_count"],
        }
        report["otros_links_descubiertos"] = estado_inicial["links"]

        selectiva_locator = page.locator(report["selector_css_exacto"])
        if selectiva_locator.count() == 0:
            raise RuntimeError("No se encontró el link 'Búsqueda Selectiva'")

        link_info = page.evaluate(
            """
            () => {
                const el = document.querySelector('[id="j_id10:j_id11"]');
                if (!el) return null;
                return {
                    text: (el.textContent || '').replace(/\\s+/g, ' ').trim(),
                    href: el.getAttribute('href') || '',
                    id: el.id || '',
                    onclick: el.getAttribute('onclick') || ''
                };
            }
            """
        )
        report["busqueda_selectiva_link"] = link_info

        selectiva_locator.click()
        time.sleep(AJAX_SLEEP_SECONDS)
        report["artifacts"].append(save_page_artifacts(page, "selectiva_02_despues_click"))

        estado_despues_click = summarize_state(page)
        report["despues_click"] = {
            "url": estado_despues_click["url"],
            "title": estado_despues_click["title"],
            "dom_hash": estado_despues_click["dom_hash"],
            "controls_count": estado_despues_click["controls_count"],
            "cambio_dom": estado_despues_click["dom_hash"] != estado_inicial["dom_hash"],
            "redirect": estado_despues_click["url"] != estado_inicial["url"],
        }

        mas_opciones_locator = page.locator('[id="formBusqueda:chkMasOpciones"]')
        report["mas_opciones_presente"] = mas_opciones_locator.count() > 0

        if mas_opciones_locator.count() > 0 and not mas_opciones_locator.is_checked():
            mas_opciones_locator.click()
            time.sleep(AJAX_SLEEP_SECONDS)
            report["artifacts"].append(save_page_artifacts(page, "selectiva_03_mas_opciones"))

        estado_expandido = summarize_state(page)
        report["estado_expandido"] = {
            "url": estado_expandido["url"],
            "title": estado_expandido["title"],
            "dom_hash": estado_expandido["dom_hash"],
            "controls_count": estado_expandido["controls_count"],
        }

        form = estado_expandido["form"]
        write_text(FORM_PATH, form.get("outer_html", ""))
        report["busqueda_selectiva_form_html_path"] = str(FORM_PATH.resolve())

        dropdowns = []
        filters = []
        for control in form.get("controls", []):
            filters.append(
                {
                    "tag": control.get("tag"),
                    "type": control.get("type"),
                    "name": control.get("name"),
                    "id": control.get("id"),
                    "row_text": control.get("row_text"),
                }
            )
            if control.get("tag") == "select":
                dropdowns.append(
                    {
                        "name": control.get("name"),
                        "id": control.get("id"),
                        "row_text": control.get("row_text"),
                        "options": control.get("options"),
                    }
                )

        report["filtros"] = filters
        report["dropdowns"] = dropdowns
        report["structured_filters"] = extract_structured_filters(form)

        if has_structured_filters(report["structured_filters"]):
            report["filtro_tests"] = run_year_tests(page, report)
        else:
            report["filtro_tests"].append(
                {
                    "status": "sin_filtros_estructurados",
                    "detail": "No se encontraron filtros por año, sede, materia, tipo de resolución, importancia ni rango de fechas.",
                }
            )

        report["request_log"] = request_log
        report["total_site_requests"] = len(request_log)

        browser.close()

    write_text(REPORT_PATH, json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except PlaywrightTimeoutError as exc:
        raise SystemExit(f"Timeout de Playwright: {exc}") from exc
