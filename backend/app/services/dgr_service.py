"""Service de consulta de trámites DGR (Dirección General de Registros).

Usa Playwright + CapSolver para resolver reCAPTCHA y consultar estado de trámites
en https://www.dgr.gub.uy/Consulta_Tramites/servlet/dgr.gub.uy.consultatramite.cn
"""

import json
import logging
import time
from typing import Optional

import httpx
from playwright.async_api import async_playwright
from app.core.config import Settings

logger = logging.getLogger(__name__)

DGR_URL = "https://www.dgr.gub.uy/Consulta_Tramites/servlet/dgr.gub.uy.consultatramite.cn"
RECAPTCHA_SITEKEY = "6LepiTkUAAAAAKnwCbJbgI-XoaXHl_-WcJCzjXWD"
CAPSOLVER_API = "https://api.capsolver.com"


async def resolver_recaptcha(site_url: str, site_key: str) -> Optional[str]:
    """Resuelve reCAPTCHA v2 invisible usando CapSolver API.

    Returns:
        Token gRecaptchaResponse o None si falla.
    """
    settings = Settings()
    api_key = settings.capsolver_api_key
    if not api_key:
        logger.error("CAPSOLVER_API_KEY no configurada")
        return None

    inicio = time.time()

    async with httpx.AsyncClient(timeout=120) as client:
        # Crear tarea
        try:
            resp = await client.post(
                f"{CAPSOLVER_API}/createTask",
                json={
                    "clientKey": api_key,
                    "task": {
                        "type": "ReCaptchaV2TaskProxyLess",
                        "websiteURL": site_url,
                        "websiteKey": site_key,
                    },
                },
            )
            data = resp.json()
        except Exception:
            logger.exception("Error creando tarea CapSolver")
            return None

        if data.get("errorId", 1) != 0:
            logger.error("CapSolver createTask error: %s", data.get("errorDescription"))
            return None

        task_id = data.get("taskId")
        if not task_id:
            logger.error("CapSolver no retornó taskId")
            return None

        # Polling de resultado
        for _ in range(60):
            await _async_sleep(3)
            try:
                resp = await client.post(
                    f"{CAPSOLVER_API}/getTaskResult",
                    json={"clientKey": api_key, "taskId": task_id},
                )
                result = resp.json()
            except Exception:
                logger.exception("Error consultando resultado CapSolver")
                continue

            status = result.get("status")
            if status == "ready":
                token = result.get("solution", {}).get("gRecaptchaResponse")
                elapsed = time.time() - inicio
                logger.info("reCAPTCHA resuelto en %.1fs", elapsed)
                return token
            elif status == "failed":
                logger.error("CapSolver tarea fallida: %s", result.get("errorDescription"))
                return None

    logger.error("CapSolver timeout tras 60 intentos de polling")
    return None


async def _async_sleep(seconds: float) -> None:
    """Wrapper para asyncio.sleep (facilita testing)."""
    import asyncio
    await asyncio.sleep(seconds)


async def consultar_tramite_dgr(
    registro: str,
    oficina: str,
    anio: int,
    numero: int,
    bis: str = "",
) -> Optional[dict]:
    """Consulta el estado de un trámite en la DGR.

    Args:
        registro: Código del registro (RA, RPI, RGI, etc.)
        oficina: Código de oficina (X=Montevideo, A=Canelones, etc.)
        anio: Año del trámite
        numero: Número de entrada
        bis: Campo bis (opcional)

    Returns:
        Dict con datos del trámite o None si falló.
    """
    logger.info(
        "Consultando DGR: registro=%s oficina=%s anio=%d numero=%d bis=%s",
        registro, oficina, anio, numero, bis,
    )

    browser = None
    try:
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Navegar al formulario
        await page.goto(DGR_URL, timeout=30000)

        # Llenar campos del formulario
        await page.select_option("#vREG", value=registro)
        await page.select_option("#vDEP", value=oficina)
        await page.fill("#vANO", str(anio))
        await page.fill("#vNRO", str(numero))
        if bis:
            await page.fill("#vBIS", bis)

        # Resolver reCAPTCHA
        token = await resolver_recaptcha(DGR_URL, RECAPTCHA_SITEKEY)
        if not token:
            logger.error("No se pudo resolver reCAPTCHA")
            return None

        # Inyectar token en el DOM
        await page.evaluate(
            """(token) => {
                document.getElementById('g-recaptcha-response').value = token;
                if (window.recaptchaObjects && recaptchaObjects.length > 0) {
                    recaptchaObjects[0].Response = token;
                }
            }""",
            token,
        )

        # Click en Consultar
        await page.click("#BUTTON4")

        # Esperar respuesta
        await _async_sleep(5)

        # Obtener contenido de la página
        content = await page.content()

        # Verificar captcha fallido
        if "No se pudo validar el captcha" in content:
            logger.error("DGR rechazó el captcha")
            return None

        # Parsear resultado
        resultado = _parsear_resultado(content)

        if resultado:
            logger.info("Trámite consultado exitosamente: %s", resultado.get("estado_actual", "?"))
        else:
            logger.warning("No se pudieron parsear datos del trámite")

        return resultado

    except Exception:
        logger.exception("Error consultando DGR")
        return None
    finally:
        if browser:
            await browser.close()


def _parsear_resultado(html: str) -> Optional[dict]:
    """Parsea el HTML de respuesta de la DGR.

    Extrae datos de identificación, inscripciones, movimientos y constancia
    desde el HTML GeneXus que devuelve el formulario de consulta.

    Returns:
        Dict con campos limpios del trámite o None si no se encontraron datos.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    # --- Datos de identificación (pares label/valor en <td> hermanos) ---
    labels_map = {
        "Registro": "registro",
        "Oficina Registral": "oficina",
        "Documento: Año | Nro.": "documento",
        "Fecha Ingreso": "fecha_ingreso",
        "Escribano | Emisor": "escribano_emisor",
    }
    resultado = {
        "registro": None,
        "oficina": None,
        "documento": None,
        "fecha_ingreso": None,
        "escribano_emisor": None,
        "estado_actual": None,
        "inscripciones": [],
        "observaciones": None,
        "movimientos": [],
        "constancia_disponible": False,
        "fecha_descarga": None,
    }

    for td in soup.find_all("td"):
        text = td.get_text(strip=True)
        if text in labels_map:
            next_td = td.find_next_sibling("td")
            if next_td:
                resultado[labels_map[text]] = next_td.get_text(strip=True) or None

    # --- Inscripciones (GridinscripcionesContainerTbl) ---
    # Columnas: [0]EstadoCod [1]reg [2]Escribano [3]Acto [4]Estado [5]Observaciones ...
    grid_insc = soup.find(id="GridinscripcionesContainerTbl")
    if grid_insc:
        rows = grid_insc.find_all("tr")[1:]  # saltar header
        observaciones_list = []
        for row in rows:
            cols = [c.get_text(strip=True) for c in row.find_all("td")]
            if len(cols) >= 5:
                acto = cols[3]
                estado = cols[4]
                obs = cols[5] if len(cols) > 5 else ""
                if acto:
                    resultado["inscripciones"].append({"acto": acto, "estado": estado})
                if obs:
                    observaciones_list.append(obs)
        if observaciones_list:
            resultado["observaciones"] = "; ".join(observaciones_list)

    # Determinar estado general desde las inscripciones
    if resultado["inscripciones"]:
        estados = [i["estado"] for i in resultado["inscripciones"]]
        if "Observado" in estados:
            resultado["estado_actual"] = "Observado"
        elif "Provisorio" in estados:
            resultado["estado_actual"] = "Provisorio"
        elif all(e == "Definitivo" for e in estados):
            resultado["estado_actual"] = "Definitivo"
        elif estados:
            resultado["estado_actual"] = estados[0]

    # --- Movimientos (GridmovimientosContainerTbl) ---
    # Columnas: [0]ord ... [10]tipo desc [11]fecha desde [12]fecha hasta
    grid_mov = soup.find(id="GridmovimientosContainerTbl")
    if grid_mov:
        rows = grid_mov.find_all("tr")[1:]  # saltar header
        for row in rows:
            cols = [c.get_text(strip=True) for c in row.find_all("td")]
            if len(cols) >= 12:
                tipo = cols[10]
                fecha = cols[11]
                if tipo:
                    resultado["movimientos"].append({"tipo": tipo, "fecha": fecha})

    # --- Constancia de inscripción ---
    constancia_span = soup.find(id="TIENEPLANCHADIGITAL")
    if constancia_span:
        text = constancia_span.get_text(strip=True)
        if "habilitada" in text.lower():
            resultado["constancia_disponible"] = True

    # --- Fecha aprox. de descarga ---
    fecha_span = soup.find(id="span_vFECHAPRUEBA2")
    if fecha_span:
        fecha_text = fecha_span.get_text(strip=True)
        if fecha_text and fecha_text != "/  /":
            resultado["fecha_descarga"] = fecha_text

    # Verificar que se obtuvieron datos mínimos
    if not resultado["fecha_ingreso"] and not resultado["inscripciones"]:
        return None

    return resultado
