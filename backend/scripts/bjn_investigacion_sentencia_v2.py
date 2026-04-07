"""
Investigación forense v2: estructura de sentencia individual en BJN.
Corrige el problema de v1 donde todas las sentencias abrían la misma URL.
Usa links específicos lnkTituloSentencia y recarga entre cada apertura.
"""

import json
import time
import os
import re
from playwright.sync_api import sync_playwright

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "bjn_screenshots")
os.makedirs(OUTPUT_DIR, exist_ok=True)

BJN_URL = "https://bjn.poderjudicial.gub.uy/BJNPUBLICA/busquedaSimple.seam"


def buscar(page, query):
    """Ejecuta búsqueda y espera resultados."""
    page.goto(BJN_URL, wait_until="networkidle")
    time.sleep(2)

    # Llenar campo de búsqueda
    input_sel = "input[id$='cajaQuery']"
    page.fill(input_sel, query)
    time.sleep(0.5)

    # Click buscar
    page.click("input[id$='Search']")
    time.sleep(6)


def extraer_metadata_lista(page):
    """Extrae metadata de todos los resultados visibles en la lista."""
    resultados = []

    # Los headers tienen formato: formResultados:grid:N:lnkTituloSentencia
    headers = page.query_selector_all("a[id*='lnkTituloSentencia']")
    print(f"  Links de sentencias encontrados: {len(headers)}")

    for i, header in enumerate(headers):
        title_text = header.inner_text().strip()

        # El body del resultado está en un panel adyacente
        body_id = f"formResultados:grid:{i}:att2Sentencia_texto_sens"
        body_el = page.query_selector(f"[id='{body_id}']")
        body_text = body_el.inner_text().strip() if body_el else ""

        # Parsear título: "16/2017 DEFINITIVA - Tribunal Apelaciones Civil 5ºTº - PROCESO CIVIL EXTRAORDINARIO"
        parsed = parse_titulo(title_text)

        resultados.append({
            "index": i,
            "titulo_raw": title_text,
            "parsed": parsed,
            "body_preview": body_text[:300],
            "link_id": header.get_attribute("id"),
        })

    return resultados


def parse_titulo(title):
    """Parsea el título de la lista de resultados."""
    # Formato: "16/2017 DEFINITIVA - Tribunal Apelaciones Civil 5ºTº - PROCESO CIVIL EXTRAORDINARIO"
    parts = title.split(" - ", 2)
    result = {"raw": title}

    if len(parts) >= 1:
        # "16/2017 DEFINITIVA" -> numero + tipo
        first = parts[0].strip()
        match = re.match(r"(\d+/\d+)\s+(.*)", first)
        if match:
            result["numero"] = match.group(1)
            result["tipo"] = match.group(2).strip()
        else:
            result["numero_tipo"] = first

    if len(parts) >= 2:
        result["sede"] = parts[1].strip()

    if len(parts) >= 3:
        result["procedimiento"] = parts[2].strip()

    return result


def abrir_sentencia(page, context, index):
    """
    Abre una sentencia específica haciendo click en su link.
    Retorna la página del popup con los datos de la sentencia.
    """
    link_id = f"formResultados:grid:{index}:lnkTituloSentencia"
    link = page.query_selector(f"a[id='{link_id}']")

    if not link:
        print(f"  Link {link_id} no encontrado")
        return None

    print(f"  Clickeando link: {link.inner_text().strip()[:60]}...")

    popup_page = None
    try:
        with page.expect_popup(timeout=15000) as popup_info:
            link.click()
        popup_page = popup_info.value
    except Exception as e:
        print(f"  Error esperando popup: {e}")
        # Intentar detectar si se abrió una nueva pestaña
        pages = context.pages
        if len(pages) > 1:
            popup_page = pages[-1]
            print(f"  Usando última página del contexto: {popup_page.url}")

    if not popup_page:
        print(f"  No se pudo abrir popup para sentencia {index}")
        return None

    try:
        popup_page.wait_for_load_state("networkidle", timeout=15000)
    except:
        time.sleep(3)

    time.sleep(2)
    return popup_page


def extraer_sentencia(popup_page):
    """Extrae todos los datos estructurados de una sentencia abierta."""
    data = {"url": popup_page.url}

    # ── Metadata de tablas ──────────────────────────────────────
    # Tabla 1: Número, Sede, Importancia, Tipo (id=j_id3)
    tabla1 = extraer_tabla(popup_page, "j_id3")
    if tabla1 and len(tabla1) > 0:
        row = tabla1[0]
        data["numero"] = row.get("Número", "")
        data["sede"] = row.get("Sede", "")
        data["importancia"] = row.get("Importancia", "")
        data["tipo"] = row.get("Tipo", "")

    # Tabla 2: Fecha, Ficha, Procedimiento (id=j_id21)
    tabla2 = extraer_tabla(popup_page, "j_id21")
    if tabla2 and len(tabla2) > 0:
        row = tabla2[0]
        data["fecha"] = row.get("Fecha", "")
        data["ficha"] = row.get("Ficha", "")
        data["procedimiento"] = row.get("Procedimiento", "")

    # Tabla 3: Materias (id=j_id35)
    tabla3 = extraer_tabla(popup_page, "j_id35")
    data["materias"] = [row.get("Materias", "") for row in (tabla3 or [])]

    # Tabla: Firmantes (id=gridFirmantes)
    firmantes_raw = extraer_tabla(popup_page, "gridFirmantes")
    data["firmantes"] = firmantes_raw or []

    # Tabla: Redactores (id=gridRedactores)
    redactores_raw = extraer_tabla(popup_page, "gridRedactores")
    data["redactores"] = redactores_raw or []

    # Tabla: Abstract (id=j_id77)
    abstract_raw = extraer_tabla(popup_page, "j_id77")
    data["abstract"] = abstract_raw or []

    # Tabla: Descriptores (id=j_id89)
    descriptores_raw = extraer_tabla(popup_page, "j_id89")
    data["descriptores"] = [row.get("Descriptores", "") for row in (descriptores_raw or [])]

    # Tabla: Resumen (id=j_id107)
    resumen_raw = extraer_tabla(popup_page, "j_id107")
    data["resumen"] = [row.get("Resumen", "") for row in (resumen_raw or [])]

    # ── Texto de la sentencia ──────────────────────────────────
    texto_box = popup_page.query_selector("#textoSentenciaBox")
    if texto_box:
        data["texto_html"] = texto_box.inner_html()
        data["texto_plano"] = texto_box.inner_text()
        data["texto_chars"] = len(data["texto_plano"])

        # Analizar secciones
        texto = data["texto_plano"].upper()
        for seccion in ["VISTOS", "RESULTANDO", "CONSIDERANDO", "FALLO",
                       "SE RESUELVE", "SENTENCIA", "DECRETO", "AUTO"]:
            if seccion in texto:
                pos = texto.find(seccion)
                data[f"tiene_{seccion.lower().replace(' ', '_')}"] = True
                data[f"pos_{seccion.lower().replace(' ', '_')}"] = pos
            else:
                data[f"tiene_{seccion.lower().replace(' ', '_')}"] = False
    else:
        data["texto_plano"] = ""
        data["texto_chars"] = 0
        # Fallback: buscar cualquier panel de texto
        panel_texto = popup_page.query_selector("#panelTextoSent_body")
        if panel_texto:
            data["texto_plano"] = panel_texto.inner_text()
            data["texto_html"] = panel_texto.inner_html()
            data["texto_chars"] = len(data["texto_plano"])

    # ── Botones disponibles ──────────────────────────────────────
    botones = popup_page.query_selector_all("input[type='button'], input[type='submit']")
    data["botones"] = [{"value": b.get_attribute("value"), "id": b.get_attribute("id") or ""} for b in botones]

    # ── HTML completo ────────────────────────────────────────────
    data["html_completo_chars"] = len(popup_page.content())

    return data


def extraer_tabla(page, table_id):
    """Extrae datos de una tabla RichFaces por su ID."""
    table = page.query_selector(f"table[id='{table_id}']")
    if not table:
        return None

    # Obtener headers
    th_elements = table.query_selector_all("thead th")
    headers = [th.inner_text().strip() for th in th_elements]

    # Filtrar headers de colspan (que son títulos de sección)
    # Tomar solo los últimos N headers que correspondan a las columnas
    # Si hay header-continue, esos son los headers reales
    continue_headers = table.query_selector_all("tr.rich-table-header-continue th")
    if continue_headers:
        headers = [th.inner_text().strip() for th in continue_headers]

    # Obtener filas de datos
    rows = table.query_selector_all("tbody tr")
    data = []
    for row in rows:
        cells = row.query_selector_all("td")
        cell_texts = [c.inner_text().strip() for c in cells]

        if len(cell_texts) == len(headers):
            data.append(dict(zip(headers, cell_texts)))
        elif len(cell_texts) > 0:
            # Si no coincide, guardarlo como lista
            data.append({"cells": cell_texts})

    return data


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page = context.new_page()
        page.set_default_timeout(30000)

        # ── FASE 1: Búsqueda ──────────────────────────────────────
        print("=" * 70)
        print("FASE 1: BÚSQUEDA")
        print("=" * 70)
        buscar(page, "prescripcion adquisitiva")
        page.screenshot(path=os.path.join(OUTPUT_DIR, "v2_01_resultados.png"))

        # ── FASE 2: Metadata de lista ─────────────────────────────
        print("\n" + "=" * 70)
        print("FASE 2: METADATA DE LISTA")
        print("=" * 70)
        resultados = extraer_metadata_lista(page)

        for r in resultados[:10]:
            print(f"\n  [{r['index']}] {r['titulo_raw']}")
            print(f"      Parsed: {r['parsed']}")
            print(f"      Body: {r['body_preview'][:100]}...")

        with open(os.path.join(OUTPUT_DIR, "v2_metadata_lista.json"), "w", encoding="utf-8") as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2)

        # ── FASE 3: Abrir sentencias individuales ─────────────────
        print("\n" + "=" * 70)
        print("FASE 3: SENTENCIAS INDIVIDUALES")
        print("=" * 70)

        sentencias = []
        for idx in range(min(4, len(resultados))):
            print(f"\n--- Sentencia {idx + 1} ---")

            # IMPORTANTE: Re-buscar antes de cada sentencia para resetear estado JSF
            if idx > 0:
                print("  Re-ejecutando búsqueda para resetear estado JSF...")
                buscar(page, "prescripcion adquisitiva")
                time.sleep(2)

            popup = abrir_sentencia(page, context, idx)
            if not popup:
                continue

            popup.screenshot(path=os.path.join(OUTPUT_DIR, f"v2_sentencia_{idx + 1}.png"))

            data = extraer_sentencia(popup)
            data["lista_index"] = idx
            data["lista_titulo"] = resultados[idx]["titulo_raw"]

            # Guardar HTML de la primera sentencia
            if idx == 0:
                with open(os.path.join(OUTPUT_DIR, "v2_sentencia_1_completa.html"), "w", encoding="utf-8") as f:
                    f.write(popup.content())

            # No guardar texto_html completo en el JSON (es muy largo)
            data_for_json = {k: v for k, v in data.items() if k != "texto_html"}
            if "texto_plano" in data_for_json:
                data_for_json["texto_plano_preview"] = data_for_json.pop("texto_plano")[:500]

            sentencias.append(data_for_json)

            print(f"  Número: {data.get('numero', 'N/A')}")
            print(f"  Sede: {data.get('sede', 'N/A')}")
            print(f"  Fecha: {data.get('fecha', 'N/A')}")
            print(f"  Importancia: {data.get('importancia', 'N/A')}")
            print(f"  Tipo: {data.get('tipo', 'N/A')}")
            print(f"  Procedimiento: {data.get('procedimiento', 'N/A')}")
            print(f"  Ficha: {data.get('ficha', 'N/A')}")
            print(f"  Materias: {data.get('materias', [])}")
            print(f"  Firmantes: {data.get('firmantes', [])}")
            print(f"  Redactores: {data.get('redactores', [])}")
            print(f"  Abstract: {data.get('abstract', [])}")
            print(f"  Descriptores: {data.get('descriptores', [])}")
            print(f"  Resumen: {data.get('resumen', [])}")
            print(f"  Texto: {data.get('texto_chars', 0)} chars")
            print(f"  Secciones: ", end="")
            for sec in ["vistos", "resultando", "considerando", "fallo", "se_resuelve"]:
                if data.get(f"tiene_{sec}"):
                    print(f"{sec.upper()} ", end="")
            print()
            print(f"  Botones: {[b['value'] for b in data.get('botones', [])]}")
            print(f"  HTML total: {data.get('html_completo_chars', 0)} chars")

            popup.close()
            time.sleep(2)

        # ── FASE 4: Guardar análisis completo ─────────────────────
        with open(os.path.join(OUTPUT_DIR, "v2_analisis_sentencias.json"), "w", encoding="utf-8") as f:
            json.dump(sentencias, f, ensure_ascii=False, indent=2)

        # ── FASE 5: Análisis de consistencia ──────────────────────
        print("\n" + "=" * 70)
        print("FASE 5: ANÁLISIS DE CONSISTENCIA")
        print("=" * 70)

        if sentencias:
            campos_presentes = set()
            for s in sentencias:
                for k in s:
                    if s[k] and s[k] not in [False, [], "", 0, None, "N/A"]:
                        campos_presentes.add(k)

            print(f"\n  Campos consistentemente presentes:")
            for c in sorted(campos_presentes):
                count = sum(1 for s in sentencias if s.get(c) and s[c] not in [False, [], "", 0, None])
                print(f"    {c}: {count}/{len(sentencias)}")

            # Comparar estructura
            print(f"\n  Tamaño de texto por sentencia:")
            for s in sentencias:
                print(f"    [{s['lista_index']}] {s.get('texto_chars', 0):,} chars - {s.get('lista_titulo', '')[:50]}")

        # ── RESUMEN FINAL ─────────────────────────────────────────
        print("\n" + "=" * 70)
        print("RESUMEN DE ARCHIVOS GENERADOS")
        print("=" * 70)
        for f in sorted(os.listdir(OUTPUT_DIR)):
            if f.startswith("v2_"):
                fpath = os.path.join(OUTPUT_DIR, f)
                size = os.path.getsize(fpath)
                print(f"  {f} ({size:,} bytes)")

        browser.close()
        print("\n[DONE]")


if __name__ == "__main__":
    run()
