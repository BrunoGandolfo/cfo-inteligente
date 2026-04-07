"""
Script de investigación: explorar búsqueda simple del BJN.
http://bjn.poderjudicial.gub.uy/BJNPUBLICA/busquedaSimple.seam

Objetivo: entender estructura, paginación, límites y selectores.
"""

import time
import os
from playwright.sync_api import sync_playwright

URL = "http://bjn.poderjudicial.gub.uy/BJNPUBLICA/busquedaSimple.seam"
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "bjn_screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

WAIT_AFTER_CLICK = 6  # segundos para AJAX


def screenshot(page, name):
    path = os.path.join(SCREENSHOTS_DIR, f"{name}.png")
    page.screenshot(path=path, full_page=True)
    print(f"  Screenshot guardado: {path}")
    return path


def extraer_info_resultados(page):
    """Extrae información visible de la página de resultados."""
    info = {}

    # Buscar mensajes de error o validación
    errores = page.query_selector_all(".rich-messages-label, .errores, .mensaje-error, .rf-msgs-sum")
    if errores:
        info["errores"] = [e.inner_text() for e in errores]

    # Buscar texto que indique total de resultados
    body_text = page.inner_text("body")
    for linea in body_text.split("\n"):
        linea_lower = linea.strip().lower()
        if any(kw in linea_lower for kw in ["resultado", "sentencia", "encontr", "total", "registro"]):
            if len(linea.strip()) < 200:
                info.setdefault("lineas_relevantes", []).append(linea.strip())

    # Buscar tabla de resultados
    tablas = page.query_selector_all("table")
    info["tablas_count"] = len(tablas)

    # Buscar filas de datos en tablas con class rich
    rich_tables = page.query_selector_all(".rich-table, .rich-datatable, .rf-dt")
    info["rich_tables_count"] = len(rich_tables)

    # Buscar data scroller / paginación
    scrollers = page.query_selector_all(
        ".rich-datascr, .rf-ds, .rich-datascroller, [class*='datascr'], [class*='paginat']"
    )
    info["scrollers_count"] = len(scrollers)
    if scrollers:
        for i, scr in enumerate(scrollers):
            info[f"scroller_{i}_html"] = scr.inner_html()[:500]

    # Buscar cualquier lista de resultados
    listas = page.query_selector_all(".rich-list, .resultados, .listaSentencias, [class*='result']")
    info["listas_count"] = len(listas)

    return info


def extraer_primer_resultado(page):
    """Extrae el HTML del primer resultado individual."""
    # Probar varios selectores comunes en RichFaces
    selectores = [
        ".rich-table-row:first-child",
        ".rich-table tbody tr:first-child",
        ".rf-dt-r:first-child",
        "table.rich-table tbody tr:nth-child(1)",
        ".resultItem:first-child",
        ".rich-datatable tbody tr:first-child",
    ]
    for sel in selectores:
        elem = page.query_selector(sel)
        if elem:
            html = elem.inner_html()
            if len(html) > 20:
                return {"selector": sel, "html": html[:2000]}
    return None


def extraer_paginacion(page):
    """Extrae info detallada de paginación."""
    info = {}
    # RichFaces datascroller
    selectores_pag = [
        ".rich-datascr",
        ".rf-ds",
        "[class*='datascr']",
        "[class*='Scroller']",
    ]
    for sel in selectores_pag:
        elems = page.query_selector_all(sel)
        if elems:
            info[f"selector_{sel}"] = len(elems)
            for i, elem in enumerate(elems):
                botones = elem.query_selector_all("td, a, span, button")
                info[f"{sel}_{i}_botones"] = len(botones)
                info[f"{sel}_{i}_text"] = elem.inner_text()[:300]
                info[f"{sel}_{i}_html"] = elem.outer_html()[:1000]

    # Buscar links de paginación genéricos
    links_pag = page.query_selector_all("a[onclick*='page'], a[onclick*='scrol'], a[onclick*='Page']")
    info["links_paginacion"] = len(links_pag)

    return info


def contar_filas_resultado(page):
    """Cuenta filas de resultados en la tabla."""
    selectores = [
        ".rich-table tbody tr",
        ".rf-dt-r",
        "table.rich-table tbody tr",
        ".rich-datatable tbody tr",
    ]
    for sel in selectores:
        filas = page.query_selector_all(sel)
        if filas:
            return {"selector": sel, "count": len(filas)}
    return {"selector": None, "count": 0}


def investigar():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="es-UY",
        )
        page = context.new_page()
        page.set_default_timeout(30000)

        # ================================================================
        # 1. CARGAR PÁGINA INICIAL
        # ================================================================
        print("=" * 70)
        print("1. CARGANDO PÁGINA DE BÚSQUEDA SIMPLE")
        print("=" * 70)
        page.goto(URL, wait_until="networkidle")
        time.sleep(2)
        screenshot(page, "01_pagina_inicial")

        # Identificar el formulario y campo de búsqueda
        inputs = page.query_selector_all("input[type='text'], textarea")
        print(f"  Inputs de texto encontrados: {len(inputs)}")
        for i, inp in enumerate(inputs):
            attrs = {
                "id": inp.get_attribute("id"),
                "name": inp.get_attribute("name"),
                "class": inp.get_attribute("class"),
                "placeholder": inp.get_attribute("placeholder"),
                "value": inp.get_attribute("value"),
            }
            print(f"    Input {i}: {attrs}")

        # Buscar botón de búsqueda
        botones = page.query_selector_all("input[type='submit'], input[type='button'], button, a.btn, .boton, [class*='btn'], [value*='uscar']")
        print(f"  Botones encontrados: {len(botones)}")
        for i, btn in enumerate(botones):
            attrs = {
                "id": btn.get_attribute("id"),
                "value": btn.get_attribute("value"),
                "text": btn.inner_text()[:50] if btn.inner_text() else None,
                "type": btn.get_attribute("type"),
                "class": btn.get_attribute("class"),
                "tag": btn.evaluate("el => el.tagName"),
            }
            print(f"    Botón {i}: {attrs}")

        # Capturar HTML completo del form
        forms = page.query_selector_all("form")
        print(f"  Forms encontrados: {len(forms)}")
        for i, form in enumerate(forms):
            form_id = form.get_attribute("id")
            form_action = form.get_attribute("action")
            print(f"    Form {i}: id={form_id}, action={form_action}")

        # ================================================================
        # 2. BÚSQUEDA VACÍA
        # ================================================================
        print("\n" + "=" * 70)
        print("2. BÚSQUEDA VACÍA")
        print("=" * 70)

        # Buscar el botón de buscar
        btn_buscar = page.query_selector("input[value*='uscar'], button:has-text('Buscar'), input[type='submit']")
        if btn_buscar:
            print(f"  Clickeando botón: {btn_buscar.get_attribute('id') or btn_buscar.get_attribute('value')}")
            btn_buscar.click()
            time.sleep(WAIT_AFTER_CLICK)
            screenshot(page, "02_busqueda_vacia")

            info = extraer_info_resultados(page)
            print(f"  Info resultados: {info}")
            filas = contar_filas_resultado(page)
            print(f"  Filas de resultado: {filas}")
        else:
            print("  ERROR: No se encontró botón de búsqueda")

        # ================================================================
        # 3. BÚSQUEDA CON QUERY CORTA
        # ================================================================
        queries_test = ["a", "e", "de", "la", "derecho"]
        for idx, q in enumerate(queries_test):
            print(f"\n{'=' * 70}")
            print(f"3.{idx+1}. BÚSQUEDA: '{q}'")
            print("=" * 70)

            # Recargar página para estado limpio
            page.goto(URL, wait_until="networkidle")
            time.sleep(2)

            # Encontrar input de búsqueda (primer input text visible)
            campo = page.query_selector("input[type='text']")
            if not campo:
                # Probar textarea
                campo = page.query_selector("textarea")

            if campo:
                campo.fill(q)
                time.sleep(0.5)

                btn_buscar = page.query_selector(
                    "input[value*='uscar'], button:has-text('Buscar'), input[type='submit']"
                )
                if btn_buscar:
                    btn_buscar.click()
                    time.sleep(WAIT_AFTER_CLICK)
                    screenshot(page, f"03_{idx+1}_busqueda_{q}")

                    info = extraer_info_resultados(page)
                    filas = contar_filas_resultado(page)
                    print(f"  Info: {info}")
                    print(f"  Filas: {filas}")

                    # Extraer primer resultado
                    if filas["count"] > 0:
                        primer_res = extraer_primer_resultado(page)
                        if primer_res:
                            print(f"  Primer resultado (selector={primer_res['selector']}):")
                            print(f"    HTML: {primer_res['html'][:500]}...")

                    # Extraer paginación
                    pag = extraer_paginacion(page)
                    if pag:
                        print(f"  Paginación: {pag}")
            else:
                print("  ERROR: No se encontró campo de búsqueda")

        # ================================================================
        # 4. EXPLORAR PAGINACIÓN (usando la última búsqueda con resultados)
        # ================================================================
        print(f"\n{'=' * 70}")
        print("4. EXPLORAR PAGINACIÓN")
        print("=" * 70)

        # Buscar "derecho" que debería tener muchos resultados
        page.goto(URL, wait_until="networkidle")
        time.sleep(2)
        campo = page.query_selector("input[type='text']")
        if campo:
            campo.fill("derecho")
            btn_buscar = page.query_selector(
                "input[value*='uscar'], button:has-text('Buscar'), input[type='submit']"
            )
            if btn_buscar:
                btn_buscar.click()
                time.sleep(WAIT_AFTER_CLICK)

                filas = contar_filas_resultado(page)
                print(f"  Filas página 1: {filas}")

                # Intentar navegar a página 2
                pag_info = extraer_paginacion(page)
                print(f"  Paginación detectada: {pag_info}")

                # Probar click en "siguiente" o "2"
                next_selectors = [
                    ".rich-datascr-act + td a",
                    ".rich-datascr td:last-child a",
                    "a[onclick*='next']",
                    ".rich-datascr-button:last-child",
                    # RichFaces next button
                    "td.rich-datascr-button:last-of-type",
                ]

                # También probar link con texto "2" o "»"
                for sel in next_selectors:
                    elem = page.query_selector(sel)
                    if elem:
                        print(f"  Encontrado siguiente con selector: {sel}")
                        elem.click()
                        time.sleep(WAIT_AFTER_CLICK)
                        screenshot(page, "04_pagina_2")
                        filas2 = contar_filas_resultado(page)
                        print(f"  Filas página 2: {filas2}")
                        break
                else:
                    # Buscar todos los links/botones dentro del scroller
                    scr = page.query_selector(".rich-datascr, [class*='datascr']")
                    if scr:
                        all_links = scr.query_selector_all("td")
                        print(f"  TDs en scroller: {len(all_links)}")
                        for i, td in enumerate(all_links):
                            print(f"    TD {i}: text='{td.inner_text()[:20]}', class='{td.get_attribute('class')}'")
                            onclick = td.get_attribute("onclick") or ""
                            print(f"           onclick={onclick[:100]}")

                        # Intentar click en el segundo TD (que suele ser página 2)
                        if len(all_links) > 2:
                            print("  Intentando click en TD[2] (página 2)...")
                            all_links[2].click()
                            time.sleep(WAIT_AFTER_CLICK)
                            screenshot(page, "04_pagina_2_via_td")
                            filas2 = contar_filas_resultado(page)
                            print(f"  Filas página 2: {filas2}")

        # ================================================================
        # 5. DUMP COMPLETO DEL HTML DE RESULTADOS
        # ================================================================
        print(f"\n{'=' * 70}")
        print("5. ESTRUCTURA HTML DE RESULTADOS")
        print("=" * 70)

        # Recargar con búsqueda conocida
        page.goto(URL, wait_until="networkidle")
        time.sleep(2)
        campo = page.query_selector("input[type='text']")
        if campo:
            campo.fill("laboral")
            btn_buscar = page.query_selector(
                "input[value*='uscar'], button:has-text('Buscar'), input[type='submit']"
            )
            if btn_buscar:
                btn_buscar.click()
                time.sleep(WAIT_AFTER_CLICK)
                screenshot(page, "05_resultados_laboral")

                # Guardar HTML completo del body
                body_html = page.inner_html("body")
                html_path = os.path.join(SCREENSHOTS_DIR, "resultados_laboral.html")
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(body_html)
                print(f"  HTML guardado en: {html_path}")

                # Buscar la tabla principal de resultados
                tabla = page.query_selector(".rich-table, .rich-datatable, table[id*='result'], table[id*='lista']")
                if tabla:
                    tabla_html = tabla.outer_html()
                    tabla_path = os.path.join(SCREENSHOTS_DIR, "tabla_resultados.html")
                    with open(tabla_path, "w", encoding="utf-8") as f:
                        f.write(tabla_html)
                    print(f"  Tabla de resultados guardada en: {tabla_path}")
                    print(f"  Tabla ID: {tabla.get_attribute('id')}")
                    print(f"  Tabla class: {tabla.get_attribute('class')}")

                    # Primera fila detallada
                    primera_fila = tabla.query_selector("tbody tr:first-child, tr.rich-table-row:first-child")
                    if primera_fila:
                        print(f"\n  PRIMER RESULTADO (HTML):")
                        print(f"  {primera_fila.outer_html()[:3000]}")

                        # Extraer celdas
                        celdas = primera_fila.query_selector_all("td")
                        print(f"\n  Celdas en primera fila: {len(celdas)}")
                        for i, celda in enumerate(celdas):
                            print(f"    Celda {i}: {celda.inner_text()[:100]}")
                else:
                    print("  No se encontró tabla de resultados con selectores estándar")
                    # Dump de todas las tablas
                    all_tables = page.query_selector_all("table")
                    for i, t in enumerate(all_tables):
                        t_id = t.get_attribute("id") or "sin-id"
                        t_class = t.get_attribute("class") or "sin-class"
                        rows = len(t.query_selector_all("tr"))
                        print(f"    Tabla {i}: id={t_id}, class={t_class}, rows={rows}")

        browser.close()
        print("\n" + "=" * 70)
        print("INVESTIGACIÓN COMPLETADA")
        print("=" * 70)


if __name__ == "__main__":
    investigar()
