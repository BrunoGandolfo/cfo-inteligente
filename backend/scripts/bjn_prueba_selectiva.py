"""Prueba operativa de Busqueda Selectiva del BJN con rango de fechas.

El script:
- lee el HTML guardado del formulario para extraer selectores exactos
- navega desde busquedaSimple.seam hasta busquedaSelectiva.seam
- configura resultados por pagina y orden
- prueba busquedas por rango de fechas para 2024, 2023 y 2020
- valida paginacion y apertura de sentencia individual
- guarda screenshots, HTML y un reporte JSON reutilizable por el crawler
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import Page, sync_playwright


BASE_URL = "http://bjn.poderjudicial.gub.uy/BJNPUBLICA/busquedaSimple.seam"
TARGET_HOST = "bjn.poderjudicial.gub.uy"
TIMEOUT_MS = 30_000
AJAX_SLEEP_SECONDS = 6.0
MAX_SITE_REQUESTS = 25
YEARS = (2024, 2023, 2020)
TRACKED_RESOURCE_TYPES = {"document", "xhr", "fetch"}

SCRIPT_DIR = Path(__file__).resolve().parent
SCREENSHOT_DIR = SCRIPT_DIR / "bjn_screenshots"
FORM_HTML_PATH = SCREENSHOT_DIR / "busqueda_selectiva_form.html"
REPORT_PATH = SCREENSHOT_DIR / "bjn_selectiva_report.json"


class SiteRequestBudgetExceeded(RuntimeError):
    """Raised when the budget of allowed requests is exhausted."""


class StepTimer:
    """Tracks step durations for the final report."""

    def __init__(self) -> None:
        self.steps: list[dict[str, Any]] = []

    def mark(self, name: str, started_at: float, notes: str = "") -> None:
        self.steps.append(
            {
                "name": name,
                "duration_seconds": round(time.perf_counter() - started_at, 3),
                "notes": notes,
            }
        )


def read_form_selectors() -> dict[str, str]:
    html = FORM_HTML_PATH.read_text(encoding="utf-8")

    def must(pattern: str, key: str) -> str:
        match = re.search(pattern, html)
        if not match:
            raise RuntimeError(f"No pude extraer {key} desde {FORM_HTML_PATH}")
        return match.group(1)

    fecha_desde_id = must(r'id="([^"]*fechaDesdeCalInputDate)"', "fecha_desde_id")
    fecha_desde_hidden_id = must(
        r'id="([^"]*fechaDesdeCalInputCurrentDate)"', "fecha_desde_hidden_id"
    )
    fecha_hasta_id = must(r'id="([^"]*fechaHastaCalInputDate)"', "fecha_hasta_id")
    fecha_hasta_hidden_id = must(
        r'id="([^"]*fechaHastaCalInputCurrentDate)"', "fecha_hasta_hidden_id"
    )
    cant_pag_field_id = must(r'id="([^"]*cantPagcomboboxField)"', "cant_pag_field_id")
    cant_pag_hidden_id = must(r'id="([^"]*cantPagcomboboxValue)"', "cant_pag_hidden_id")
    cant_pag_button_id = must(r'id="([^"]*cantPagcomboboxButton)"', "cant_pag_button_id")
    orden_name = must(r'<select name="([^"]*j_id240:j_id248)"', "orden_name")
    buscar_id = must(r'id="([^"]*:Search)"[^>]*value="Buscar"', "buscar_id")

    return {
        "link_busqueda_selectiva": '[id="j_id10:j_id11"]',
        "fecha_desde": f'[id="{fecha_desde_id}"]',
        "fecha_desde_hidden": f'[id="{fecha_desde_hidden_id}"]',
        "fecha_hasta": f'[id="{fecha_hasta_id}"]',
        "fecha_hasta_hidden": f'[id="{fecha_hasta_hidden_id}"]',
        "resultados_por_pagina_field": f'[id="{cant_pag_field_id}"]',
        "resultados_por_pagina_hidden": f'[id="{cant_pag_hidden_id}"]',
        "resultados_por_pagina_button": f'[id="{cant_pag_button_id}"]',
        "ordenar_por": f'[name="{orden_name}"]',
        "buscar": f'[id="{buscar_id}"]',
        "grid_resultados": '[id="formResultados:dataTable"]',
        "filas_resultados": 'table[id="formResultados:dataTable"] tr.rich-table-row',
        "primer_click_sentencia": 'td[id="formResultados:dataTable:0:colFec"]',
        "paginador": '[id="formResultados:zonaPaginador"]',
        "pagina_siguiente": '[id="formResultados:sigLink"]',
    }


def save_artifacts(page: Page, stem: str) -> dict[str, str]:
    screenshot_path = SCREENSHOT_DIR / f"{stem}.png"
    html_path = SCREENSHOT_DIR / f"{stem}.html"
    page.screenshot(path=str(screenshot_path), full_page=True)
    html_path.write_text(page.content(), encoding="utf-8")
    return {
        "screenshot_path": str(screenshot_path.resolve()),
        "html_path": str(html_path.resolve()),
    }


def normalize_space(text: str) -> str:
    return " ".join((text or "").split())


def extract_results_summary(page: Page) -> dict[str, Any]:
    body_text = normalize_space(page.locator("body").inner_text())
    total_match = re.search(r"(\d+)\s+resultado/s", body_text, flags=re.IGNORECASE)
    page_match = re.search(r"P[aá]gina\s+(\d+)\s+de\s+(\d+)", body_text, flags=re.IGNORECASE)

    rows = page.locator('table[id="formResultados:dataTable"] tr.rich-table-row')
    visible_rows = rows.count()
    first_items = []
    for index in range(min(5, visible_rows)):
        row = rows.nth(index)
        cells = row.locator("td")
        fecha = normalize_space(cells.nth(0).inner_text(timeout=5_000))
        tipo = normalize_space(cells.nth(1).inner_text(timeout=5_000))
        numero = normalize_space(cells.nth(2).inner_text(timeout=5_000))
        sede = normalize_space(cells.nth(3).inner_text(timeout=5_000))
        procedimiento = normalize_space(cells.nth(4).inner_text(timeout=5_000))
        first_items.append(
            {
                "index": index,
                "fecha": fecha,
                "tipo": tipo,
                "numero": numero,
                "sede": sede,
                "procedimiento": procedimiento,
            }
        )

    return {
        "body_excerpt": body_text[:500],
        "total_resultados": int(total_match.group(1)) if total_match else None,
        "pagina_actual": int(page_match.group(1)) if page_match else None,
        "paginas_totales": int(page_match.group(2)) if page_match else None,
        "resultados_en_pagina": visible_rows,
        "primeros_resultados": first_items,
    }


def wait_for_results_or_error(page: Page) -> dict[str, Any]:
    started_at = time.perf_counter()
    try:
        page.wait_for_function(
            """
            () => {
                const text = document.body ? document.body.innerText : "";
                return text.includes("resultado/s")
                    || text.includes("Ha ocurrido un error")
                    || document.querySelectorAll('table[id="formResultados:dataTable"] tr.rich-table-row').length > 0;
            }
            """,
            timeout=TIMEOUT_MS,
        )
        status = "ready"
        error = ""
    except PlaywrightTimeoutError:
        status = "timeout"
        error = "No aparecieron resultados ni mensaje de error dentro del timeout."

    body_text = normalize_space(page.locator("body").inner_text())
    return {
        "status": status,
        "error": error,
        "wait_seconds_until_state": round(time.perf_counter() - started_at, 3),
        "body_excerpt": body_text[:500],
        "has_error_banner": "Ha ocurrido un error" in body_text,
        "has_results_token": "resultado/s" in body_text,
    }


def wait_for_selectiva_form(page: Page, selectors: dict[str, str]) -> None:
    page.wait_for_function(
        """
        sels => {
            return Boolean(
                document.querySelector(sels.fecha_desde)
                && document.querySelector(sels.fecha_hasta)
                && document.querySelector(sels.buscar)
                && document.querySelector(sels.ordenar_por)
            );
        }
        """,
        arg=selectors,
        timeout=TIMEOUT_MS,
    )


def set_results_per_page(page: Page, selectors: dict[str, str], value: str) -> dict[str, Any]:
    page.evaluate(
        """
        ({hiddenSelector, fieldSelector, value}) => {
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
            "hiddenSelector": selectors["resultados_por_pagina_hidden"],
            "fieldSelector": selectors["resultados_por_pagina_field"],
            "value": value,
        },
    )
    return {
        "method": "evaluate_hidden_and_visible_field",
        "visible_value": page.locator(selectors["resultados_por_pagina_field"]).input_value(),
        "hidden_value": page.locator(selectors["resultados_por_pagina_hidden"]).input_value(),
    }


def set_order(page: Page, selectors: dict[str, str], value: str) -> dict[str, Any]:
    page.locator(selectors["ordenar_por"]).select_option(value)
    selected_value = page.locator(selectors["ordenar_por"]).input_value()
    selected_label = page.locator(
        f'{selectors["ordenar_por"]} option:checked'
    ).inner_text(timeout=5_000)
    return {
        "method": "select_option",
        "selected_value": selected_value,
        "selected_label": normalize_space(selected_label),
    }


def set_date_fill(page: Page, input_selector: str, hidden_selector: str, value: str) -> dict[str, Any]:
    locator = page.locator(input_selector)
    locator.click()
    locator.fill(value)
    locator.press("Tab")
    page.wait_for_timeout(200)
    hidden_value = month_year_from_date(value)
    page.evaluate(
        """
        ({hiddenSelector, hiddenValue}) => {
            const hidden = document.querySelector(hiddenSelector);
            if (hidden) {
                hidden.value = hiddenValue;
            }
        }
        """,
        {"hiddenSelector": hidden_selector, "hiddenValue": hidden_value},
    )
    return {
        "method": "fill",
        "input_value": locator.input_value(),
        "hidden_value": page.locator(hidden_selector).input_value(),
    }


def set_date_evaluate(
    page: Page, input_selector: str, hidden_selector: str, value: str
) -> dict[str, Any]:
    hidden_value = month_year_from_date(value)
    page.evaluate(
        """
        ({inputSelector, hiddenSelector, value, hiddenValue}) => {
            const input = document.querySelector(inputSelector);
            const hidden = document.querySelector(hiddenSelector);
            if (!input) {
                throw new Error("No encontre el input de fecha");
            }
            input.value = value;
            input.dispatchEvent(new Event("input", { bubbles: true }));
            input.dispatchEvent(new Event("change", { bubbles: true }));
            input.dispatchEvent(new Event("blur", { bubbles: true }));
            if (hidden) {
                hidden.value = hiddenValue;
            }
        }
        """,
        {
            "inputSelector": input_selector,
            "hiddenSelector": hidden_selector,
            "value": value,
            "hiddenValue": hidden_value,
        },
    )
    return {
        "method": "evaluate",
        "input_value": page.locator(input_selector).input_value(),
        "hidden_value": page.locator(hidden_selector).input_value(),
    }


def set_date_keyboard(
    page: Page, input_selector: str, hidden_selector: str, value: str
) -> dict[str, Any]:
    locator = page.locator(input_selector)
    locator.click()
    locator.press("Control+A")
    locator.press("Backspace")
    page.keyboard.type(value)
    locator.press("Tab")
    hidden_value = month_year_from_date(value)
    page.evaluate(
        """
        ({hiddenSelector, hiddenValue}) => {
            const hidden = document.querySelector(hiddenSelector);
            if (hidden) {
                hidden.value = hiddenValue;
            }
        }
        """,
        {"hiddenSelector": hidden_selector, "hiddenValue": hidden_value},
    )
    return {
        "method": "keyboard_type",
        "input_value": locator.input_value(),
        "hidden_value": page.locator(hidden_selector).input_value(),
    }


def month_year_from_date(value: str) -> str:
    day, month, year = value.split("/")
    return f"{month}/{year}"


def apply_date_method(
    page: Page, selectors: dict[str, str], method_name: str, date_from: str, date_to: str
) -> dict[str, Any]:
    methods = {
        "fill": set_date_fill,
        "evaluate": set_date_evaluate,
        "keyboard_type": set_date_keyboard,
    }
    func = methods[method_name]
    from_result = func(
        page,
        selectors["fecha_desde"],
        selectors["fecha_desde_hidden"],
        date_from,
    )
    to_result = func(
        page,
        selectors["fecha_hasta"],
        selectors["fecha_hasta_hidden"],
        date_to,
    )
    return {
        "fecha_desde": from_result,
        "fecha_hasta": to_result,
    }


def submit_search(page: Page, selectors: dict[str, str]) -> None:
    page.locator(selectors["buscar"]).click()


def reopen_selectiva_form(
    page: Page,
    selectors: dict[str, str],
    artifact_stem: str | None = None,
) -> dict[str, Any]:
    started_at = time.perf_counter()
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=TIMEOUT_MS)
    page.wait_for_function("typeof A4J !== 'undefined'", timeout=TIMEOUT_MS)
    time.sleep(2.0)
    page.locator(selectors["link_busqueda_selectiva"]).click()
    page.wait_for_url("**/busquedaSelectiva.seam?cid=*", timeout=TIMEOUT_MS)
    time.sleep(AJAX_SLEEP_SECONDS)
    wait_for_selectiva_form(page, selectors)
    entry: dict[str, Any] = {
        "url": page.url,
        "load_elapsed_seconds": round(time.perf_counter() - started_at, 3),
        "post_click_sleep_seconds": AJAX_SLEEP_SECONDS,
    }
    if artifact_stem:
        entry.update(save_artifacts(page, artifact_stem))
    return entry


def configure_selectiva_form(
    page: Page,
    selectors: dict[str, str],
    artifact_stem: str | None = None,
) -> dict[str, Any]:
    started_at = time.perf_counter()
    entry = {
        "results_per_page_setup": set_results_per_page(page, selectors, "200"),
        "order_setup": set_order(page, selectors, "FECHA_DESCENDENTE"),
        "elapsed_seconds": round(time.perf_counter() - started_at, 3),
    }
    if artifact_stem:
        entry.update(save_artifacts(page, artifact_stem))
    return entry


def run_year_search(
    page: Page,
    selectors: dict[str, str],
    year: int,
    date_method: str,
    screenshot_stem: str,
) -> dict[str, Any]:
    date_from = f"01/01/{year}"
    date_to = f"31/12/{year}"

    started_at = time.perf_counter()
    date_details = apply_date_method(page, selectors, date_method, date_from, date_to)
    submit_search(page, selectors)
    time.sleep(AJAX_SLEEP_SECONDS)
    wait_state = wait_for_results_or_error(page)
    artifact = save_artifacts(page, screenshot_stem)

    entry: dict[str, Any] = {
        "year": year,
        "date_from": date_from,
        "date_to": date_to,
        "date_method": date_method,
        "date_details": date_details,
        "post_search_sleep_seconds": AJAX_SLEEP_SECONDS,
        "search_total_elapsed_seconds": round(time.perf_counter() - started_at, 3),
        **wait_state,
        **artifact,
    }

    if wait_state["status"] == "ready" and not wait_state["has_error_banner"]:
        entry.update(extract_results_summary(page))

    return entry


def run_year_search_from_fresh_form(
    page: Page,
    selectors: dict[str, str],
    year: int,
    date_method: str,
    screenshot_stem: str,
    form_open_stem: str | None = None,
    form_config_stem: str | None = None,
) -> dict[str, Any]:
    return {
        "form_open": reopen_selectiva_form(page, selectors, form_open_stem),
        "form_configuration": configure_selectiva_form(page, selectors, form_config_stem),
        "search": run_year_search(page, selectors, year, date_method, screenshot_stem),
    }


def run_year_search_with_retries(
    page: Page,
    selectors: dict[str, str],
    year: int,
    methods: tuple[str, ...],
    screenshot_prefix: str,
) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    successful_attempt: dict[str, Any] | None = None

    for idx, method in enumerate(methods, start=1):
        attempt = run_year_search_from_fresh_form(
            page,
            selectors,
            year,
            method,
            f"{screenshot_prefix}_{method}",
            form_open_stem=f"{screenshot_prefix}_form_{idx}",
            form_config_stem=f"{screenshot_prefix}_config_{idx}",
        )
        attempts.append(attempt)
        search = attempt["search"]
        if search["status"] == "ready" and not search["has_error_banner"]:
            successful_attempt = attempt
            break

    return {
        "year": year,
        "attempts": attempts,
        "successful_attempt": successful_attempt,
        "selected_date_method": (
            successful_attempt["search"]["date_method"] if successful_attempt else None
        ),
    }


def ensure_page_1(page: Page, selectors: dict[str, str], year_2024_entry: dict[str, Any]) -> None:
    if year_2024_entry.get("pagina_actual") in (None, 1):
        return
    raise RuntimeError("La busqueda 2024 no quedo en pagina 1; revisar flujo.")


def go_to_page_2(page: Page, selectors: dict[str, str]) -> dict[str, Any]:
    if page.locator(selectors["pagina_siguiente"]).count() == 0:
        return {
            "status": "missing_next_link",
            "detail": "No aparecio el link de pagina siguiente.",
        }

    before_summary = extract_results_summary(page)
    before_marker = (
        before_summary["primeros_resultados"][0]["numero"]
        if before_summary["primeros_resultados"]
        else ""
    )
    started_at = time.perf_counter()
    page.locator(selectors["pagina_siguiente"]).click()
    try:
        page.wait_for_function(
            """
            ({ beforeMarker }) => {
                const text = document.body ? document.body.innerText : "";
                if (/P[aá]gina\\s+2\\s+de\\s+\\d+/i.test(text)) {
                    return true;
                }
                if (beforeMarker && !text.includes(beforeMarker)) {
                    return true;
                }
                return false;
            }
            """,
            arg={"beforeMarker": before_marker},
            timeout=TIMEOUT_MS,
        )
    except PlaywrightTimeoutError:
        pass
    time.sleep(AJAX_SLEEP_SECONDS)
    wait_state = wait_for_results_or_error(page)
    artifact = save_artifacts(page, "selectiva_2024_pagina_2")
    entry: dict[str, Any] = {
        "status": wait_state["status"],
        "post_click_sleep_seconds": AJAX_SLEEP_SECONDS,
        "elapsed_seconds": round(time.perf_counter() - started_at, 3),
        "before_summary": before_summary,
        **wait_state,
        **artifact,
    }
    if wait_state["status"] == "ready" and not wait_state["has_error_banner"]:
        entry.update(extract_results_summary(page))
        entry["boton_siguiente_funciona"] = entry.get("pagina_actual") == 2
        entry["muestra_200_en_pagina"] = entry.get("resultados_en_pagina") == 200
    return entry


def open_sentence_popup(page: Page, selectors: dict[str, str]) -> dict[str, Any]:
    first_cell = page.locator(selectors["primer_click_sentencia"]).first
    if first_cell.count() == 0:
        return {
            "status": "no_sentence_links",
            "detail": "No encontre una celda clickeable de sentencia en la grilla actual.",
        }

    link_text = normalize_space(first_cell.locator("xpath=ancestor::tr[1]").inner_text(timeout=5_000))
    started_at = time.perf_counter()
    with page.expect_popup(timeout=TIMEOUT_MS) as popup_info:
        first_cell.click()
    popup = popup_info.value
    try:
        popup.wait_for_load_state("domcontentloaded", timeout=TIMEOUT_MS)
    except PlaywrightTimeoutError:
        pass
    time.sleep(2.0)

    artifact = save_artifacts(popup, "selectiva_sentencia_popup")
    popup_body = normalize_space(popup.locator("body").inner_text())
    popup_data = {
        "status": "opened",
        "title_clicked": link_text,
        "popup_url": popup.url,
        "elapsed_seconds": round(time.perf_counter() - started_at, 3),
        "same_popup_shape_as_simple_search": bool(
            popup.locator("#textoSentenciaBox").count()
            and popup.locator("#panelTextoSent_body").count()
        ),
        "has_texto_sentencia_box": popup.locator("#textoSentenciaBox").count() > 0,
        "has_panel_texto_sent_body": popup.locator("#panelTextoSent_body").count() > 0,
        "has_metadata_table_j_id3": popup.locator('table[id="j_id3"]').count() > 0,
        "has_metadata_table_j_id21": popup.locator('table[id="j_id21"]').count() > 0,
        "body_excerpt": popup_body[:500],
        **artifact,
    }
    popup.close()
    return popup_data


def build_route_handler(request_log: list[dict[str, Any]]):
    def handle_route(route) -> None:
        request = route.request
        parsed = urlparse(request.url)

        if parsed.hostname != TARGET_HOST:
            route.abort()
            return

        lower_url = request.url.lower()
        if any(
            token in lower_url
            for token in (
                "spacer.gif",
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".ico",
                ".css",
                ".woff",
                ".woff2",
                ".ttf",
                ".svg",
            )
        ):
            route.abort()
            return

        if request.resource_type in {"image", "media", "font", "stylesheet"}:
            route.abort()
            return

        if request.resource_type in TRACKED_RESOURCE_TYPES:
            request_log.append(
                {
                    "resource_type": request.resource_type,
                    "method": request.method,
                    "url": request.url,
                }
            )
            if len(request_log) > MAX_SITE_REQUESTS:
                route.abort()
                raise SiteRequestBudgetExceeded(
                    f"Presupuesto de requests excedido: {len(request_log)} > {MAX_SITE_REQUESTS}"
                )

        route.continue_()

    return handle_route


def main() -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    selectors = read_form_selectors()
    request_log: list[dict[str, Any]] = []
    timer = StepTimer()

    report: dict[str, Any] = {
        "base_url": BASE_URL,
        "current_date": time.strftime("%Y-%m-%d"),
        "timeout_ms": TIMEOUT_MS,
        "ajax_sleep_seconds": AJAX_SLEEP_SECONDS,
        "max_site_requests": MAX_SITE_REQUESTS,
        "selectors": selectors,
        "request_log": request_log,
        "steps": timer.steps,
    }

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context()
            page = context.new_page()
            page.set_default_timeout(TIMEOUT_MS)
            page.route("**/*", build_route_handler(request_log))

            started_at = time.perf_counter()
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=TIMEOUT_MS)
            time.sleep(2.0)
            report["step_busqueda_simple"] = {
                "url": page.url,
                **save_artifacts(page, "selectiva_step_01_busqueda_simple"),
            }
            timer.mark("load_busqueda_simple", started_at)

            started_at = time.perf_counter()
            page.locator(selectors["link_busqueda_selectiva"]).click()
            page.wait_for_url("**/busquedaSelectiva.seam?cid=*", timeout=TIMEOUT_MS)
            time.sleep(AJAX_SLEEP_SECONDS)
            wait_for_selectiva_form(page, selectors)
            report["step_busqueda_selectiva_loaded"] = {
                "url": page.url,
                "post_click_sleep_seconds": AJAX_SLEEP_SECONDS,
                **save_artifacts(page, "selectiva_step_02_formulario"),
            }
            timer.mark("open_busqueda_selectiva", started_at)

            started_at = time.perf_counter()
            report["results_per_page_setup"] = set_results_per_page(page, selectors, "200")
            report["order_setup"] = set_order(page, selectors, "FECHA_DESCENDENTE")
            report["step_form_configured"] = save_artifacts(page, "selectiva_step_03_form_configurado")
            timer.mark(
                "configure_form",
                started_at,
                notes="200 resultados por pagina y fecha descendente",
            )

            started_at = time.perf_counter()
            report["year_2024"] = run_year_search_with_retries(
                page,
                selectors,
                2024,
                ("fill", "evaluate", "keyboard_type"),
                "selectiva_test_2024",
            )
            year_2024 = report["year_2024"]["successful_attempt"]
            timer.mark(
                "search_2024",
                started_at,
                notes=f"date_method={report['year_2024']['selected_date_method']}",
            )

            if not year_2024:
                raise RuntimeError("No logre una busqueda exitosa para 2024.")

            year_2024_search = year_2024["search"]
            ensure_page_1(page, selectors, year_2024_search)

            started_at = time.perf_counter()
            report["page_2_2024"] = go_to_page_2(page, selectors)
            timer.mark("go_to_page_2", started_at)

            started_at = time.perf_counter()
            report["sentence_popup"] = open_sentence_popup(page, selectors)
            timer.mark("open_sentence_popup", started_at)

            started_at = time.perf_counter()
            report["year_2023"] = run_year_search_from_fresh_form(
                page,
                selectors,
                2023,
                report["year_2024"]["selected_date_method"],
                "selectiva_test_2023_ok",
                form_open_stem="selectiva_test_2023_form",
                form_config_stem="selectiva_test_2023_config",
            )
            timer.mark(
                "search_2023",
                started_at,
                notes=f"date_method={report['year_2024']['selected_date_method']}",
            )

            started_at = time.perf_counter()
            report["year_2020"] = run_year_search_from_fresh_form(
                page,
                selectors,
                2020,
                report["year_2024"]["selected_date_method"],
                "selectiva_test_2020_ok",
                form_open_stem="selectiva_test_2020_form",
                form_config_stem="selectiva_test_2020_config",
            )
            timer.mark(
                "search_2020",
                started_at,
                notes=f"date_method={report['year_2024']['selected_date_method']}",
            )

            browser.close()

        report["status"] = "ok"
    except Exception as exc:
        report["status"] = "error"
        report["error"] = repr(exc)
    finally:
        REPORT_PATH.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
