"""
Investigación forense de paginación y volumen del BJN.

Objetivo:
- medir volumen aproximado con queries genéricas
- entender resultados por página y controles de paginación
- verificar robots/sitemap y alternativas de crawling

Restricciones operativas:
- Playwright síncrono
- headless=True
- timeout=30s
- sleep de 5s después de cada acción AJAX
- presupuesto máximo de 20 requests "principales" al host objetivo
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import Locator, Page, Request, sync_playwright

SEARCH_URL = "http://bjn.poderjudicial.gub.uy/BJNPUBLICA/busquedaSimple.seam"
ROBOTS_URL = "http://bjn.poderjudicial.gub.uy/robots.txt"
SITEMAP_URL = "http://bjn.poderjudicial.gub.uy/sitemap.xml"
TARGET_HOST = "bjn.poderjudicial.gub.uy"

AJAX_SLEEP_SECONDS = 5
DEFAULT_TIMEOUT_MS = 30_000
MAX_TRACKED_REQUESTS = 20

GENERIC_QUERIES = ["derecho", "civil", "penal", "laboral", "familia", "2024", "2023", "2022"]
PAGINATION_TEST_PAGES = ["2", "3", "4"]

TABLE_SELECTORS = [
    ".rich-table",
    ".rich-datatable",
    ".rf-dt",
    "table[id*='tabla']",
    "table[id*='result']",
    "table[id*='lista']",
]

ROW_SELECTORS = [
    "tbody tr.rich-table-row",
    "tbody tr.rf-dt-r",
    "tbody tr",
]

PAGINATION_SELECTORS = [
    "#formResultados\\:zonaPaginador",
    ".rich-datascr",
    ".rich-datascroller",
    ".rf-ds",
    "[class*='datascr']",
    "[id*='datascr']",
    "[id*='scroller']",
]


@dataclass
class RequestBudget:
    count: int = 0
    entries: list[dict[str, str]] | None = None

    def __post_init__(self) -> None:
        if self.entries is None:
            self.entries = []

    def track(self, request: Request) -> None:
        parsed = urlparse(request.url)
        if parsed.hostname != TARGET_HOST:
            return
        if request.resource_type not in {"document", "xhr", "fetch"}:
            return
        self.count += 1
        self.entries.append(
            {
                "resource_type": request.resource_type,
                "method": request.method,
                "url": request.url,
            }
        )
        if self.count > MAX_TRACKED_REQUESTS:
            raise RuntimeError(
                f"Presupuesto de requests excedido: {self.count} > {MAX_TRACKED_REQUESTS}"
            )


def sleep_after_ajax() -> None:
    time.sleep(AJAX_SLEEP_SECONDS)


def block_heavy_assets(route) -> None:
    resource_type = route.request.resource_type
    if resource_type in {"image", "media", "font"}:
        route.abort()
        return
    route.continue_()


def safe_text(locator: Locator) -> str:
    try:
        text = locator.inner_text(timeout=2_000)
    except PlaywrightTimeoutError:
        return ""
    return " ".join(text.split())


def css_path(locator: Locator) -> str:
    try:
        return locator.evaluate(
            """el => {
                function build(node) {
                    if (!node || !node.tagName) return "";
                    if (node.id) return `#${node.id}`;
                    const tag = node.tagName.toLowerCase();
                    const classes = Array.from(node.classList || []).filter(Boolean);
                    let base = tag;
                    if (classes.length) {
                        base += "." + classes.slice(0, 3).join(".");
                    }
                    const parent = node.parentElement;
                    if (!parent || parent.tagName.toLowerCase() === "body") {
                        return base;
                    }
                    const siblings = Array.from(parent.children).filter(
                        sibling => sibling.tagName === node.tagName
                    );
                    if (siblings.length > 1) {
                        const position = siblings.indexOf(node) + 1;
                        base += `:nth-of-type(${position})`;
                    }
                    return build(parent) + " > " + base;
                }
                return build(el);
            }"""
        )
    except Exception:
        return "<selector-no-disponible>"


def find_search_input(page: Page) -> Locator:
    candidates = page.locator("input[type='text'], textarea")
    for idx in range(candidates.count()):
        candidate = candidates.nth(idx)
        if candidate.is_visible():
            return candidate
    raise RuntimeError("No encontré campo de búsqueda")


def find_search_button(page: Page) -> Locator:
    selectors = [
        "input[value*='uscar']",
        "button:has-text('Buscar')",
        "input[type='submit']",
        "a:has-text('Buscar')",
    ]
    for selector in selectors:
        locator = page.locator(selector).first
        if locator.count() and locator.is_visible():
            return locator
    raise RuntimeError("No encontré botón de búsqueda")


def find_results_table(page: Page) -> Locator | None:
    for selector in TABLE_SELECTORS:
        tables = page.locator(selector)
        for idx in range(tables.count()):
            table = tables.nth(idx)
            if not table.is_visible():
                continue
            rows = count_rows_in_table(table)
            if rows > 0:
                return table
    return None


def count_rows_in_table(table: Locator) -> int:
    for row_selector in ROW_SELECTORS:
        rows = table.locator(row_selector)
        count = 0
        for idx in range(rows.count()):
            row = rows.nth(idx)
            if not row.is_visible():
                continue
            cell_count = row.locator("td").count()
            text = safe_text(row)
            if cell_count == 0 or not text:
                continue
            count += 1
        if count:
            return count
    return 0


def extract_total_results(page: Page) -> dict[str, Any]:
    body_text = page.locator("body").inner_text(timeout=5_000)
    relevant_lines = []
    for line in body_text.splitlines():
        normalized = " ".join(line.split())
        if not normalized:
            continue
        low = normalized.lower()
        if any(keyword in low for keyword in ("resultado", "resultados", "sentencia", "sentencias", "registro", "registros", "encontr")):
            relevant_lines.append(normalized[:250])

    patterns = [
        r"(\d+)\s+resultado/s",
        r"mostrando\s+\d+\s*(?:-|a)\s*\d+\s+de\s+(\d+)",
        r"se encontraron\s+(\d+)\s+(?:resultados|sentencias|registros)",
        r"(\d+)\s+(?:resultados|sentencias|registros)\s+encontr",
        r"total(?:\s+de)?\s+(?:resultados|sentencias|registros)\s*:?\s*(\d+)",
        r"resultados?\s*:?\s*(\d+)",
        r"sentencias?\s*:?\s*(\d+)",
        r"registros?\s*:?\s*(\d+)",
    ]

    for line in relevant_lines:
        low = line.lower()
        for pattern in patterns:
            match = re.search(pattern, low, flags=re.IGNORECASE)
            if match:
                return {
                    "total": int(match.group(1)),
                    "matched_line": line,
                    "relevant_lines": relevant_lines[:12],
                }

    return {
        "total": None,
        "matched_line": None,
        "relevant_lines": relevant_lines[:12],
    }


def collect_select_controls(page: Page) -> list[dict[str, Any]]:
    controls = []
    selects = page.locator("select")
    for idx in range(selects.count()):
        select = selects.nth(idx)
        if not select.is_visible():
            continue
        options = []
        option_nodes = select.locator("option")
        for opt_idx in range(option_nodes.count()):
            option = option_nodes.nth(opt_idx)
            options.append(
                {
                    "text": safe_text(option),
                    "value": option.get_attribute("value"),
                    "selected": option.get_attribute("selected") is not None,
                }
            )
        controls.append(
            {
                "selector": css_path(select),
                "id": select.get_attribute("id"),
                "name": select.get_attribute("name"),
                "options": options,
            }
        )
    return controls


def find_pagination_container(page: Page) -> Locator | None:
    for selector in PAGINATION_SELECTORS:
        containers = page.locator(selector)
        for idx in range(containers.count()):
            container = containers.nth(idx)
            if not container.is_visible():
                continue
            text = safe_text(container)
            if any(char.isdigit() for char in text):
                return container
    return None


def collect_pagination_info(page: Page) -> dict[str, Any]:
    container = find_pagination_container(page)
    if container is None:
        return {
            "present": False,
            "container_selector": None,
            "controls": [],
            "jump_input_present": False,
        }

    controls = []
    items = container.locator("a, button, span, td, input")
    for idx in range(items.count()):
        item = items.nth(idx)
        if not item.is_visible():
            continue
        text = safe_text(item)
        tag = item.evaluate("el => el.tagName.toLowerCase()")
        href = item.get_attribute("href")
        onclick = item.get_attribute("onclick")
        control = {
            "text": text,
            "tag": tag,
            "selector": css_path(item),
            "href": href,
            "onclick": onclick,
            "class": item.get_attribute("class"),
        }
        if text or tag == "input":
            controls.append(control)

    jump_input_present = any(control["tag"] == "input" for control in controls)
    return {
        "present": True,
        "container_selector": css_path(container),
        "container_text": safe_text(container),
        "controls": controls,
        "jump_input_present": jump_input_present,
    }


def find_pagination_control(page: Page, label: str) -> Locator | None:
    container = find_pagination_container(page)
    if container is None:
        return None

    for query in (
        f"a:text-is('{label}')",
        f"button:text-is('{label}')",
        f"td:text-is('{label}')",
        f"span:text-is('{label}')",
    ):
        candidate = container.locator(query).first
        if candidate.count() and candidate.is_visible():
            return candidate

    nodes = container.locator("a, button, td, span")
    for idx in range(nodes.count()):
        node = nodes.nth(idx)
        if safe_text(node) == label:
            return node
    return None


def search_query(page: Page, query: str) -> dict[str, Any]:
    input_box = find_search_input(page)
    input_box.fill("")
    input_box.fill(query)

    start = time.perf_counter()
    find_search_button(page).click()
    sleep_after_ajax()
    elapsed = round(time.perf_counter() - start, 2)

    table = find_results_table(page)
    rows = count_rows_in_table(table) if table is not None else 0
    totals = extract_total_results(page)
    pagination = collect_pagination_info(page)
    select_controls = collect_select_controls(page)

    return {
        "query": query,
        "search_seconds": elapsed,
        "rows_on_page": rows,
        "total_results": totals["total"],
        "matched_line": totals["matched_line"],
        "relevant_lines": totals["relevant_lines"],
        "pagination": pagination,
        "select_controls": select_controls,
    }


def navigate_to_page(page: Page, label: str) -> dict[str, Any]:
    control = find_pagination_control(page, label)
    if control is None:
        return {
            "target_page": label,
            "clicked": False,
            "selector": None,
            "rows_on_page": None,
            "seconds": None,
        }

    selector = css_path(control)
    start = time.perf_counter()
    control.click()
    sleep_after_ajax()
    elapsed = round(time.perf_counter() - start, 2)

    table = find_results_table(page)
    rows = count_rows_in_table(table) if table is not None else 0
    return {
        "target_page": label,
        "clicked": True,
        "selector": selector,
        "rows_on_page": rows,
        "seconds": elapsed,
    }


def navigate_next(page: Page, current_page: int, target_page: int) -> dict[str, Any]:
    if target_page <= current_page:
        return {
            "target_page": str(target_page),
            "clicked": False,
            "selector": None,
            "rows_on_page": None,
            "seconds": None,
            "reason": "target_page debe ser mayor al current_page",
        }

    next_link = page.locator("#formResultados\\:sigLink").first
    if not next_link.count() or not next_link.is_visible():
        return {
            "target_page": str(target_page),
            "clicked": False,
            "selector": None,
            "rows_on_page": None,
            "seconds": None,
            "reason": "No encontré link siguiente",
        }

    selector = css_path(next_link)
    start = time.perf_counter()
    for _ in range(target_page - current_page):
        next_link.click()
        sleep_after_ajax()
        next_link = page.locator("#formResultados\\:sigLink").first
    elapsed = round(time.perf_counter() - start, 2)
    table = find_results_table(page)
    rows = count_rows_in_table(table) if table is not None else 0
    return {
        "target_page": str(target_page),
        "clicked": True,
        "selector": selector,
        "rows_on_page": rows,
        "seconds": elapsed,
        "navigation_mode": "next-link",
    }


def open_first_result(page: Page) -> dict[str, Any]:
    table = find_results_table(page)
    if table is None:
        return {"opened": False, "reason": "No encontré tabla de resultados"}

    first_row = None
    for row_selector in ROW_SELECTORS:
        rows = table.locator(row_selector)
        for idx in range(rows.count()):
            row = rows.nth(idx)
            if row.is_visible() and row.locator("a").count():
                first_row = row
                break
        if first_row is not None:
            break

    if first_row is None:
        return {"opened": False, "reason": "No encontré fila con link"}

    link = first_row.locator("a").first
    link_text = safe_text(link)
    link_selector = css_path(link)

    start = time.perf_counter()
    try:
        with page.expect_popup(timeout=5_000) as popup_info:
            link.click()
        popup = popup_info.value
        popup.set_default_timeout(DEFAULT_TIMEOUT_MS)
        popup.wait_for_load_state("domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)
        sleep_after_ajax()
        elapsed = round(time.perf_counter() - start, 2)
        title = popup.title()
        url = popup.url
        popup.close()
        return {
            "opened": True,
            "mode": "popup",
            "selector": link_selector,
            "text": link_text,
            "seconds": elapsed,
            "url": url,
            "title": title,
        }
    except PlaywrightTimeoutError:
        before_url = page.url
        link.click()
        sleep_after_ajax()
        elapsed = round(time.perf_counter() - start, 2)
        after_url = page.url
        title = page.title()
        return {
            "opened": True,
            "mode": "same-tab",
            "selector": link_selector,
            "text": link_text,
            "seconds": elapsed,
            "url_before": before_url,
            "url_after": after_url,
            "title": title,
        }


def collect_footer_and_menu_links(page: Page) -> list[dict[str, str]]:
    anchors = page.locator("footer a, nav a, .menu a, .footer a, a")
    links = []
    seen = set()
    for idx in range(anchors.count()):
        anchor = anchors.nth(idx)
        if not anchor.is_visible():
            continue
        text = safe_text(anchor)
        href = anchor.get_attribute("href") or ""
        key = (text, href)
        if key in seen:
            continue
        if not text and not href:
            continue
        low = f"{text} {href}".lower()
        if any(token in low for token in ("rss", "xml", "sitemap", "mapa", "site", "feed")):
            links.append({"text": text, "href": href})
            seen.add(key)
    return links


def fetch_plain_page(page: Page, url: str) -> dict[str, Any]:
    start = time.perf_counter()
    page.goto(url, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)
    elapsed = round(time.perf_counter() - start, 2)
    body_text = page.locator("body").inner_text(timeout=5_000)
    return {
        "url": url,
        "status_url": page.url,
        "seconds": elapsed,
        "content_snippet": body_text[:1200],
        "has_sitemap_reference": "sitemap" in body_text.lower(),
    }


def investigate() -> dict[str, Any]:
    report: dict[str, Any] = {
        "requests_budget": MAX_TRACKED_REQUESTS,
        "generic_queries": {},
        "pagination_navigation": [],
        "pagination_last_page_test": None,
        "open_sentence_speed": None,
        "robots": None,
        "sitemap": None,
        "footer_menu_links": [],
        "tracked_requests": [],
    }

    budget = RequestBudget()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 960},
            locale="es-UY",
        )
        context.route("**/*", block_heavy_assets)

        page = context.new_page()
        page.set_default_timeout(DEFAULT_TIMEOUT_MS)
        page.on("request", budget.track)

        page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)
        report["footer_menu_links"] = collect_footer_and_menu_links(page)

        derecho_result = search_query(page, "derecho")
        report["generic_queries"]["derecho"] = derecho_result
        report["results_per_page"] = derecho_result["rows_on_page"]
        report["page_size_controls"] = derecho_result["select_controls"]
        report["pagination_baseline"] = derecho_result["pagination"]

        current_page = 1
        for label in PAGINATION_TEST_PAGES:
            navigation = navigate_to_page(page, label)
            if not navigation["clicked"] and label.isdigit():
                navigation = navigate_next(page, current_page=current_page, target_page=int(label))
            report["pagination_navigation"].append(navigation)
            if navigation.get("clicked") and label.isdigit():
                current_page = int(label)

        # Intentar llegar a una página "alta" usando el último número visible.
        pag_info = collect_pagination_info(page)
        visible_numeric_controls = [
            control for control in pag_info["controls"]
            if control["text"].isdigit()
        ]
        if visible_numeric_controls:
            last_visible = max(visible_numeric_controls, key=lambda control: int(control["text"]))
            if last_visible["text"] not in {"2", "3", "4"}:
                report["pagination_last_page_test"] = navigate_to_page(page, last_visible["text"])
            else:
                report["pagination_last_page_test"] = {
                    "target_page": last_visible["text"],
                    "clicked": False,
                    "reason": "El último número visible ya estaba dentro del recorrido 2-4",
                    "visible_controls": [control["text"] for control in visible_numeric_controls],
                }
        else:
            report["pagination_last_page_test"] = {
                "clicked": False,
                "reason": "No encontré controles numéricos visibles",
            }

        report["open_sentence_speed"] = open_first_result(page)

        # Volver a resultados para seguir con queries de volumen.
        page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)
        for query in GENERIC_QUERIES[1:]:
            report["generic_queries"][query] = search_query(page, query)

        report["robots"] = fetch_plain_page(page, ROBOTS_URL)
        report["sitemap"] = fetch_plain_page(page, SITEMAP_URL)

        report["tracked_requests_count"] = budget.count
        report["tracked_requests"] = budget.entries

        browser.close()

    return report


if __name__ == "__main__":
    result = investigate()
    print(json.dumps(result, indent=2, ensure_ascii=False))
