"""Investigación automática del buscador avanzado del BJN con Playwright."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


BASE_URL = "http://bjn.poderjudicial.gub.uy/BJNPUBLICA/"
CANDIDATE_URLS = [
    BASE_URL,
    urljoin(BASE_URL, "busquedaAvanzada.seam"),
    urljoin(BASE_URL, "busquedaJurisprudencia.seam"),
    urljoin(BASE_URL, "busqueda.seam"),
    urljoin(BASE_URL, "jurisprudencia.seam"),
    urljoin(BASE_URL, "buscarJurisprudencia.seam"),
]
SCREENSHOT_DIR = Path(__file__).resolve().parent / "bjn_screenshots"
REPORT_PATH = SCREENSHOT_DIR / "investigacion_avanzada_report.json"
AJAX_SLEEP_SECONDS = 5
TIMEOUT_MS = 30_000


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()
    return value or "captura"


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def locator_for_control(page, control: Dict[str, Any]):
    if control.get("id"):
        return page.locator(f"[id=\"{control['id']}\"]")
    if control.get("name"):
        return page.locator(f"[name=\"{control['name']}\"]")
    return None


def collect_links(page) -> List[Dict[str, str]]:
    return page.evaluate(
        """
        () => Array.from(document.querySelectorAll('a'))
            .map(a => ({
                text: (a.textContent || '').trim(),
                href: a.href || '',
            }))
            .filter(item => item.text || item.href)
        """
    )


def collect_form_details(page) -> Dict[str, Any]:
    return page.evaluate(
        """
        () => {
            const normalize = (text) => (text || '').replace(/\\s+/g, ' ').trim();
            const forms = Array.from(document.querySelectorAll('form')).map((form, index) => {
                const controls = Array.from(form.querySelectorAll('input, select, textarea')).map((el) => {
                    const labels = [];
                    if (el.id) {
                        document.querySelectorAll(`label[for="${el.id}"]`).forEach(label => {
                            labels.push(normalize(label.textContent));
                        });
                    }
                    const parentLabel = el.closest('label');
                    if (parentLabel) {
                        labels.push(normalize(parentLabel.textContent));
                    }
                    const row = el.closest('tr');
                    let rowText = '';
                    let contextText = '';
                    if (row) {
                        rowText = normalize(row.textContent);
                        const cells = Array.from(row.children);
                        const cellIndex = cells.findIndex(cell => cell.contains(el));
                        if (cellIndex > 0) {
                            contextText = normalize(
                                cells
                                    .slice(0, cellIndex)
                                    .map(cell => cell.textContent || '')
                                    .join(' ')
                            );
                        }
                    }
                    return {
                        tag: el.tagName.toLowerCase(),
                        type: el.getAttribute('type') || '',
                        name: el.getAttribute('name') || '',
                        id: el.id || '',
                        labels: labels.filter(Boolean),
                        placeholder: el.getAttribute('placeholder') || '',
                        row_text: rowText,
                        context_text: contextText,
                        options: el.tagName.toLowerCase() === 'select'
                            ? Array.from(el.options).map(opt => ({
                                value: opt.value,
                                text: normalize(opt.textContent),
                            }))
                            : [],
                    };
                });
                return {
                    index,
                    id: form.id || '',
                    name: form.getAttribute('name') || '',
                    action: form.getAttribute('action') || '',
                    method: form.getAttribute('method') || '',
                    html: form.outerHTML,
                    controls,
                };
            });
            return { forms };
        }
        """
    )


def find_relevant_form(form_details: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    best_form = None
    best_score = -1
    keywords = ("fecha", "sede", "materia", "tipo", "resol", "importancia", "anio", "año")
    for form in form_details.get("forms", []):
        score = 0
        for control in form.get("controls", []):
            haystack = " ".join(
                [
                    control.get("name", ""),
                    control.get("id", ""),
                    control.get("placeholder", ""),
                    " ".join(control.get("labels", [])),
                ]
            ).lower()
            if control.get("tag") == "select":
                score += 2
            if control.get("type") in {"text", "hidden"}:
                score += 0
            for keyword in keywords:
                if keyword in haystack:
                    score += 4
        if score > best_score:
            best_form = form
            best_score = score
    return best_form


def save_page_artifacts(page, prefix: str) -> None:
    page.screenshot(path=str(SCREENSHOT_DIR / f"{prefix}.png"), full_page=True)
    write_text(SCREENSHOT_DIR / f"{prefix}.html", page.content())


def safe_title(page) -> str:
    try:
        return page.title()
    except Exception:
        return ""


def try_open(page, url: str, prefix: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {"url": url, "ok": False}
    try:
        response = page.goto(url, wait_until="domcontentloaded", timeout=TIMEOUT_MS)
        time.sleep(2)
        try:
            page.wait_for_load_state("load", timeout=5_000)
        except Exception:
            pass
        save_page_artifacts(page, prefix)
        links = collect_links(page)
        result.update(
            {
                "ok": True,
                "status": response.status if response else None,
                "final_url": page.url,
                "title": safe_title(page),
                "links": links,
            }
        )
    except PlaywrightTimeoutError as exc:
        result["error"] = f"timeout: {exc}"
    except Exception as exc:  # pragma: no cover - diagnóstico
        result["error"] = repr(exc)
    return result


def find_advanced_candidate(base_links: List[Dict[str, str]]) -> List[str]:
    seen: List[str] = []
    for item in base_links:
        text = (item.get("text") or "").lower()
        href = item.get("href") or ""
        if any(word in text for word in ("avanz", "búsqueda", "busqueda", "jurisprud")):
            if href and href not in seen:
                seen.append(href)
    return seen


def extract_select_options(form: Dict[str, Any], keywords: tuple[str, ...]) -> List[str]:
    collected: List[str] = []
    for control in form.get("controls", []):
        haystack = " ".join(
            [
                control.get("name", ""),
                control.get("id", ""),
                " ".join(control.get("labels", [])),
                control.get("row_text", ""),
                control.get("context_text", ""),
            ]
        ).lower()
        if control.get("tag") != "select":
            continue
        if not any(keyword in haystack for keyword in keywords):
            continue
        for option in control.get("options", []):
            text = (option.get("text") or "").strip()
            if text and text not in collected:
                collected.append(text)
    return collected


def find_control(form: Dict[str, Any], keywords: tuple[str, ...], tag: Optional[str] = None) -> Optional[Dict[str, Any]]:
    for control in form.get("controls", []):
        if tag and control.get("tag") != tag:
            continue
        haystack = " ".join(
            [
                control.get("name", ""),
                control.get("id", ""),
                control.get("placeholder", ""),
                " ".join(control.get("labels", [])),
                control.get("row_text", ""),
                control.get("context_text", ""),
            ]
        ).lower()
        if any(keyword in haystack for keyword in keywords):
            return control
    return None


def list_filters(form: Dict[str, Any]) -> List[Dict[str, Any]]:
    filters: List[Dict[str, Any]] = []
    for control in form.get("controls", []):
        if control.get("type") == "hidden":
            continue
        filters.append(
            {
                "tag": control.get("tag"),
                "type": control.get("type"),
                "name": control.get("name"),
                "id": control.get("id"),
                "labels": control.get("labels"),
                "placeholder": control.get("placeholder"),
                "row_text": control.get("row_text"),
                "context_text": control.get("context_text"),
                "options_count": len(control.get("options", [])),
            }
        )
    return filters


def choose_option_value(options: List[Dict[str, str]], year: int) -> Optional[str]:
    for option in options:
        text = (option.get("text") or "").strip()
        value = option.get("value") or ""
        if text == str(year) or value == str(year):
            return value or text
    return None


def find_submit_target(page, form: Dict[str, Any]):
    form_locator = page.locator(f"form#{form['id']}") if form.get("id") else None
    candidates = []
    if form_locator and form_locator.count() > 0:
        candidates.extend(
            [
                form_locator.locator("input[type=submit]"),
                form_locator.locator("button[type=submit]"),
                form_locator.locator("input[type=image]"),
                form_locator.locator("a:has-text('Buscar')"),
                form_locator.locator("button:has-text('Buscar')"),
                form_locator.locator("input[value*='Buscar']"),
            ]
        )
    candidates.extend(
        [
            page.locator("button:has-text('Buscar')"),
            page.locator("input[type=submit][value*='Buscar']"),
            page.locator("a:has-text('Buscar')"),
        ]
    )
    for locator in candidates:
        try:
            if locator.count() > 0:
                return locator.first
        except Exception:
            continue
    return None


def find_result_count(page) -> Optional[int]:
    texts = page.locator("body").all_inner_texts()
    haystack = "\n".join(texts)
    patterns = [
        r"(\d+)\s+resultados",
        r"resultados\s*:\s*(\d+)",
        r"se encontraron\s+(\d+)",
        r"total\s*:\s*(\d+)",
        r"(\d+)\s+coincidencias",
        r"(\d+)\s+sentencias",
    ]
    for pattern in patterns:
        match = re.search(pattern, haystack, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def expand_more_options(page) -> bool:
    checkbox = page.locator('[id="formBusqueda:chkMasOpciones"]')
    if checkbox.count() == 0:
        return False
    try:
        if not checkbox.is_checked():
            checkbox.click()
            time.sleep(AJAX_SLEEP_SECONDS)
        save_page_artifacts(page, "advanced_options_expanded")
        return True
    except Exception:
        return False


def run_year_query(page, advanced_url: str, form: Dict[str, Any], year: int, year_control: Dict[str, Any]) -> Dict[str, Any]:
    page.goto(advanced_url, wait_until="domcontentloaded", timeout=TIMEOUT_MS)
    time.sleep(2)
    expand_more_options(page)
    locator = locator_for_control(page, year_control)
    if locator is None or locator.count() == 0:
        return {"year": year, "error": "control de año no encontrado al reabrir página"}

    if year_control.get("tag") == "select":
        value = choose_option_value(year_control.get("options", []), year)
        if value is None:
            return {"year": year, "error": "año no disponible en dropdown"}
        locator.select_option(value=value)
    else:
        locator.fill(str(year))

    submit = find_submit_target(page, form)
    if submit is None:
        return {"year": year, "error": "botón de búsqueda no encontrado"}

    submit.click()
    time.sleep(AJAX_SLEEP_SECONDS)
    prefix = f"advanced_year_{year}"
    save_page_artifacts(page, prefix)

    return {
        "year": year,
        "url": page.url,
        "result_count": find_result_count(page),
        "html_path": str((SCREENSHOT_DIR / f"{prefix}.html").resolve()),
        "screenshot_path": str((SCREENSHOT_DIR / f"{prefix}.png").resolve()),
    }


def run_date_range_query(
    page,
    advanced_url: str,
    form: Dict[str, Any],
    year: int,
    desde_control: Dict[str, Any],
    hasta_control: Dict[str, Any],
) -> Dict[str, Any]:
    page.goto(advanced_url, wait_until="domcontentloaded", timeout=TIMEOUT_MS)
    time.sleep(2)
    expand_more_options(page)

    desde_locator = locator_for_control(page, desde_control)
    hasta_locator = locator_for_control(page, hasta_control)
    if (
        desde_locator is None
        or hasta_locator is None
        or desde_locator.count() == 0
        or hasta_locator.count() == 0
    ):
        return {"year": year, "error": "controles de fecha no encontrados al reabrir página"}

    desde_locator.fill(f"01/01/{year}")
    hasta_locator.fill(f"31/12/{year}")

    submit = find_submit_target(page, form)
    if submit is None:
        return {"year": year, "error": "botón de búsqueda no encontrado"}

    submit.click()
    time.sleep(AJAX_SLEEP_SECONDS)
    prefix = f"advanced_date_range_{year}"
    save_page_artifacts(page, prefix)

    return {
        "year": year,
        "url": page.url,
        "result_count": find_result_count(page),
        "html_path": str((SCREENSHOT_DIR / f"{prefix}.html").resolve()),
        "screenshot_path": str((SCREENSHOT_DIR / f"{prefix}.png").resolve()),
        "mode": "date_range",
    }


def main() -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    report: Dict[str, Any] = {
        "base_url": BASE_URL,
        "candidate_urls": CANDIDATE_URLS,
        "advanced_exists": False,
        "advanced_url": None,
        "base_links": [],
        "discovered_candidate_urls": [],
        "filters": [],
        "sedes": [],
        "materias": [],
        "tipos_resolucion": [],
        "year_results": [],
        "artifacts": [],
    }

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(TIMEOUT_MS)

        visited: List[Dict[str, Any]] = []
        for index, url in enumerate(CANDIDATE_URLS):
            prefix = f"candidate_{index}_{slugify(url.split('/')[-1] or 'home')}"
            result = try_open(page, url, prefix)
            result["screenshot_path"] = str((SCREENSHOT_DIR / f"{prefix}.png").resolve())
            result["html_path"] = str((SCREENSHOT_DIR / f"{prefix}.html").resolve())
            visited.append(result)

        base_result = visited[0]
        report["artifacts"].extend(visited)
        if base_result.get("ok"):
            report["base_links"] = base_result.get("links", [])
            report["discovered_candidate_urls"] = find_advanced_candidate(base_result.get("links", []))

        candidate_pool = CANDIDATE_URLS + report["discovered_candidate_urls"]
        seen_urls = set()
        advanced_result = None
        for url in candidate_pool:
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            prefix = f"inspect_{slugify(url)}"
            result = try_open(page, url, prefix)
            result["screenshot_path"] = str((SCREENSHOT_DIR / f"{prefix}.png").resolve())
            result["html_path"] = str((SCREENSHOT_DIR / f"{prefix}.html").resolve())
            report["artifacts"].append(result)
            if not result.get("ok"):
                continue
            expanded = expand_more_options(page)
            if expanded:
                form_details = collect_form_details(page)
                report["artifacts"].append(
                    {
                        "url": page.url,
                        "ok": True,
                        "status": result.get("status"),
                        "final_url": page.url,
                        "title": safe_title(page),
                        "links": collect_links(page),
                        "screenshot_path": str((SCREENSHOT_DIR / "advanced_options_expanded.png").resolve()),
                        "html_path": str((SCREENSHOT_DIR / "advanced_options_expanded.html").resolve()),
                    }
                )
            else:
                form_details = collect_form_details(page)
            form = find_relevant_form(form_details)
            if form and len(form.get("controls", [])) >= 4:
                report["advanced_exists"] = True
                report["advanced_url"] = page.url
                report["page_title"] = page.title()
                report["form_id"] = form.get("id")
                report["advanced_embedded_in_simple_search"] = expanded
                report["filters"] = list_filters(form)
                report["sedes"] = extract_select_options(form, ("sede",))
                report["materias"] = extract_select_options(form, ("materia",))
                report["tipos_resolucion"] = extract_select_options(form, ("tipo", "resol"))
                write_text(SCREENSHOT_DIR / "advanced_form.html", form.get("html", ""))
                report["advanced_form_html_path"] = str((SCREENSHOT_DIR / "advanced_form.html").resolve())
                advanced_result = {"url": page.url, "form": form}
                save_page_artifacts(page, "advanced_page")
                break

        if advanced_result:
            year_control = find_control(advanced_result["form"], ("anio", "año", "year"))
            if year_control:
                for year in (2024, 2023, 2020):
                    report["year_results"].append(
                        run_year_query(page, advanced_result["url"], advanced_result["form"], year, year_control)
                    )
            else:
                desde_control = find_control(advanced_result["form"], ("fecha desde", "desde", "fecha inicial"))
                hasta_control = find_control(advanced_result["form"], ("fecha hasta", "hasta", "fecha final"))
                if desde_control and hasta_control:
                    for year in (2024, 2023, 2020):
                        report["year_results"].append(
                            run_date_range_query(
                                page,
                                advanced_result["url"],
                                advanced_result["form"],
                                year,
                                desde_control,
                                hasta_control,
                            )
                        )

        browser.close()

    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
