"""
Investigación forense de estructura de sentencia individual en BJN (Base de Jurisprudencia Nacional).
Extrae metadata de lista, abre popups de sentencias, analiza estructura completa.
"""

import json
import time
import os
from playwright.sync_api import sync_playwright

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "bjn_screenshots")
os.makedirs(OUTPUT_DIR, exist_ok=True)

BJN_URL = "https://bjn.poderjudicial.gub.uy/BJNPUBLICA/busquedaSimple.seam"


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page = context.new_page()
        page.set_default_timeout(30000)

        # ── 1. Navegar y buscar ──────────────────────────────────────
        print("[1] Navegando a BJN...")
        page.goto(BJN_URL, wait_until="networkidle")
        time.sleep(2)

        # Buscar el input de búsqueda simple
        search_input = page.query_selector("input[id$='busquedaSimpleDecorate:busquedaSimple']")
        if not search_input:
            # Fallback: buscar cualquier input de texto visible
            search_input = page.query_selector("input[type='text']")

        if not search_input:
            print("ERROR: No se encontró campo de búsqueda")
            page.screenshot(path=os.path.join(OUTPUT_DIR, "error_no_input.png"))
            browser.close()
            return

        search_input.fill("prescripcion adquisitiva")
        time.sleep(1)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "01_busqueda_escrita.png"))

        # Click en botón buscar
        buscar_btn = page.query_selector("input[type='submit'][value='Buscar']")
        if not buscar_btn:
            buscar_btn = page.query_selector("button:has-text('Buscar')")
        if not buscar_btn:
            buscar_btn = page.query_selector("input[type='submit']")

        if buscar_btn:
            buscar_btn.click()
        else:
            search_input.press("Enter")

        print("[2] Esperando resultados...")
        time.sleep(6)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "02_resultados_lista.png"))

        # ── 2. Extraer metadata de los primeros 5 resultados ─────────
        print("[3] Extrayendo metadata de lista...")

        # Buscar paneles de resultados
        panels = page.query_selector_all(".rich-panel")
        if not panels:
            panels = page.query_selector_all("[class*='rich-panel']")

        print(f"    Paneles encontrados: {len(panels)}")

        resultados_metadata = []
        for i, panel in enumerate(panels[:5]):
            info = {}
            info["index"] = i

            # Extraer texto del header
            header = panel.query_selector(".rich-panel-header")
            if header:
                info["header_text"] = header.inner_text().strip()
                info["header_html"] = header.inner_html().strip()

            # Extraer texto del body
            body = panel.query_selector(".rich-panel-body")
            if body:
                info["body_text"] = body.inner_text().strip()
                info["body_html"] = body.inner_html().strip()[:2000]  # Limitar

            # Buscar spans, links, etc. dentro del panel
            spans = panel.query_selector_all("span")
            info["spans"] = [s.inner_text().strip() for s in spans if s.inner_text().strip()]

            links = panel.query_selector_all("a")
            info["links"] = [{"text": a.inner_text().strip(), "href": a.get_attribute("href") or ""} for a in links]

            # Buscar elementos con clases específicas
            for cls in ["sede", "fecha", "materia", "numero", "importancia", "ficha"]:
                els = panel.query_selector_all(f"[class*='{cls}']")
                if els:
                    info[f"class_{cls}"] = [e.inner_text().strip() for e in els]

            resultados_metadata.append(info)
            print(f"    Resultado {i}: {info.get('header_text', 'SIN HEADER')[:80]}")

        # Guardar metadata
        with open(os.path.join(OUTPUT_DIR, "metadata_lista.json"), "w", encoding="utf-8") as f:
            json.dump(resultados_metadata, f, ensure_ascii=False, indent=2)

        # ── 3. Investigar estructura del HTML de resultados ──────────
        print("[4] Analizando estructura HTML de resultados...")

        # Capturar HTML completo de la zona de resultados
        results_container = page.query_selector("[id*='resultado']") or page.query_selector("[id*='list']") or page.query_selector("form")
        if results_container:
            results_html = results_container.inner_html()
            with open(os.path.join(OUTPUT_DIR, "resultados_html_raw.html"), "w", encoding="utf-8") as f:
                f.write(results_html[:50000])

        # Capturar todos los IDs y clases relevantes
        all_elements = page.evaluate("""() => {
            const els = document.querySelectorAll('[class*="rich-panel"], [class*="result"], [class*="ficha"]');
            return Array.from(els).slice(0, 30).map(el => ({
                tag: el.tagName,
                id: el.id,
                className: el.className,
                childCount: el.children.length
            }));
        }""")
        print(f"    Elementos relevantes: {len(all_elements)}")
        with open(os.path.join(OUTPUT_DIR, "elementos_estructura.json"), "w", encoding="utf-8") as f:
            json.dump(all_elements, f, ensure_ascii=False, indent=2)

        # ── 4. Abrir primera sentencia (click en .rich-panel-body) ───
        print("[5] Abriendo primera sentencia...")

        panel_bodies = page.query_selector_all(".rich-panel-body")
        if not panel_bodies:
            print("ERROR: No se encontraron .rich-panel-body")
            browser.close()
            return

        sentencias_analizadas = []

        for sent_idx in range(min(4, len(panel_bodies))):
            print(f"\n[6.{sent_idx}] Abriendo sentencia {sent_idx + 1}...")

            # Re-obtener panel bodies (el DOM puede cambiar)
            panel_bodies = page.query_selector_all(".rich-panel-body")
            if sent_idx >= len(panel_bodies):
                print(f"    Solo hay {len(panel_bodies)} paneles, no puedo abrir sentencia {sent_idx + 1}")
                break

            target = panel_bodies[sent_idx]

            # Escuchar popup
            popup_page = None
            try:
                with page.expect_popup(timeout=15000) as popup_info:
                    target.click()
                popup_page = popup_info.value
                print(f"    Popup abierto: {popup_page.url}")
            except Exception as e:
                print(f"    No se abrió popup con click en body. Error: {e}")
                # Intentar click en header
                headers = page.query_selector_all(".rich-panel-header")
                if sent_idx < len(headers):
                    try:
                        with page.expect_popup(timeout=15000) as popup_info:
                            headers[sent_idx].click()
                        popup_page = popup_info.value
                        print(f"    Popup abierto via header: {popup_page.url}")
                    except Exception as e2:
                        print(f"    Tampoco con header: {e2}")
                        # Intentar con links dentro del panel
                        panels_retry = page.query_selector_all(".rich-panel")
                        if sent_idx < len(panels_retry):
                            link = panels_retry[sent_idx].query_selector("a")
                            if link:
                                try:
                                    with page.expect_popup(timeout=15000) as popup_info:
                                        link.click()
                                    popup_page = popup_info.value
                                    print(f"    Popup abierto via link: {popup_page.url}")
                                except Exception as e3:
                                    print(f"    Ningún método funcionó: {e3}")

            if not popup_page:
                print(f"    SKIP sentencia {sent_idx + 1} - no se pudo abrir")
                continue

            # Esperar carga del popup
            try:
                popup_page.wait_for_load_state("networkidle", timeout=15000)
            except:
                time.sleep(3)

            time.sleep(3)
            popup_page.screenshot(path=os.path.join(OUTPUT_DIR, f"sentencia_{sent_idx + 1}_popup.png"))

            # ── Extraer TODO del popup ───────────────────────────────
            sentencia_data = {"index": sent_idx + 1, "url": popup_page.url}

            # HTML completo
            full_html = popup_page.content()
            sentencia_data["html_length"] = len(full_html)

            if sent_idx == 0:
                # Guardar HTML completo de la primera sentencia
                with open(os.path.join(OUTPUT_DIR, "sentencia_ejemplo.html"), "w", encoding="utf-8") as f:
                    f.write(full_html)
                print(f"    HTML guardado: {len(full_html)} caracteres")

            # Texto completo
            body_el = popup_page.query_selector("body")
            full_text = body_el.inner_text() if body_el else ""
            sentencia_data["text_length"] = len(full_text)

            # Buscar secciones típicas
            for seccion in ["VISTOS", "RESULTANDO", "CONSIDERANDO", "FALLO", "SE RESUELVE",
                           "SENTENCIA", "DECRETO", "AUTO", "RESOLUCIÓN"]:
                if seccion in full_text.upper():
                    # Encontrar posición
                    pos = full_text.upper().find(seccion)
                    sentencia_data[f"seccion_{seccion}"] = {
                        "encontrada": True,
                        "posicion": pos,
                        "contexto": full_text[max(0, pos-20):pos+100].strip()
                    }
                else:
                    sentencia_data[f"seccion_{seccion}"] = {"encontrada": False}

            # Buscar metadata estructurada en el popup
            # Tablas
            tables = popup_page.query_selector_all("table")
            sentencia_data["tablas_count"] = len(tables)

            table_data = []
            for t_idx, table in enumerate(tables[:5]):
                rows = table.query_selector_all("tr")
                row_data = []
                for row in rows[:20]:
                    cells = row.query_selector_all("td, th")
                    row_data.append([c.inner_text().strip() for c in cells])
                table_data.append({"table_index": t_idx, "rows": row_data})
            sentencia_data["tablas"] = table_data

            # Divs con clases relevantes
            metadata_divs = popup_page.evaluate("""() => {
                const results = [];
                const allDivs = document.querySelectorAll('div, span, td, th, label, dt, dd');
                for (const el of allDivs) {
                    const text = el.innerText?.trim() || '';
                    const lower = text.toLowerCase();
                    if (text.length < 200 && (
                        lower.includes('sede') || lower.includes('fecha') ||
                        lower.includes('materia') || lower.includes('número') ||
                        lower.includes('nro') || lower.includes('tipo') ||
                        lower.includes('firmante') || lower.includes('descriptor') ||
                        lower.includes('importancia') || lower.includes('ficha') ||
                        lower.includes('proceso') || lower.includes('turno') ||
                        lower.includes('ministro') || lower.includes('redactor')
                    )) {
                        results.push({
                            tag: el.tagName,
                            class: el.className,
                            id: el.id,
                            text: text.substring(0, 200)
                        });
                    }
                }
                return results.slice(0, 50);
            }""")
            sentencia_data["metadata_elements"] = metadata_divs

            # Links y botones en el popup
            popup_links = popup_page.query_selector_all("a, button, input[type='button'], input[type='submit']")
            sentencia_data["links_buttons"] = []
            for el in popup_links[:20]:
                sentencia_data["links_buttons"].append({
                    "tag": el.evaluate("el => el.tagName"),
                    "text": el.inner_text().strip()[:100] if el.inner_text() else "",
                    "href": el.get_attribute("href") or "",
                    "type": el.get_attribute("type") or "",
                    "id": el.get_attribute("id") or "",
                    "class": el.get_attribute("class") or ""
                })

            # Estructura de divs principales
            main_structure = popup_page.evaluate("""() => {
                const body = document.body;
                function mapChildren(el, depth) {
                    if (depth > 3) return [];
                    return Array.from(el.children).slice(0, 10).map(child => ({
                        tag: child.tagName,
                        id: child.id,
                        class: child.className?.substring(0, 100) || '',
                        textPreview: child.innerText?.substring(0, 100) || '',
                        childCount: child.children.length,
                        children: mapChildren(child, depth + 1)
                    }));
                }
                return mapChildren(body, 0);
            }""")
            sentencia_data["dom_structure"] = main_structure

            # Primer fragmento de texto (para ver formato)
            sentencia_data["text_preview_first_500"] = full_text[:500]
            sentencia_data["text_preview_last_500"] = full_text[-500:]

            sentencias_analizadas.append(sentencia_data)
            print(f"    Sentencia {sent_idx + 1}: {sentencia_data['text_length']} chars, {sentencia_data['tablas_count']} tablas")

            # Cerrar popup
            popup_page.close()
            time.sleep(2)

        # ── 7. Guardar análisis completo ─────────────────────────────
        with open(os.path.join(OUTPUT_DIR, "analisis_sentencias.json"), "w", encoding="utf-8") as f:
            json.dump(sentencias_analizadas, f, ensure_ascii=False, indent=2)

        # ── 8. Resumen comparativo ───────────────────────────────────
        print("\n" + "=" * 70)
        print("RESUMEN DE INVESTIGACIÓN")
        print("=" * 70)

        print(f"\nResultados en lista: {len(resultados_metadata)}")
        for r in resultados_metadata:
            print(f"  [{r['index']}] {r.get('header_text', 'SIN HEADER')[:80]}")

        print(f"\nSentencias abiertas: {len(sentencias_analizadas)}")
        for s in sentencias_analizadas:
            print(f"  [{s['index']}] URL: {s['url']}")
            print(f"         HTML: {s['html_length']} chars, Texto: {s['text_length']} chars")
            print(f"         Tablas: {s['tablas_count']}")
            secciones = [k.replace("seccion_", "") for k, v in s.items()
                        if k.startswith("seccion_") and isinstance(v, dict) and v.get("encontrada")]
            print(f"         Secciones: {', '.join(secciones) if secciones else 'NINGUNA'}")

        print(f"\nArchivos generados en {OUTPUT_DIR}/:")
        for f in sorted(os.listdir(OUTPUT_DIR)):
            fpath = os.path.join(OUTPUT_DIR, f)
            size = os.path.getsize(fpath)
            print(f"  {f} ({size:,} bytes)")

        browser.close()
        print("\n[DONE]")


if __name__ == "__main__":
    run()
