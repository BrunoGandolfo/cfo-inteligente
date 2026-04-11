"""Service de consulta de Certificado Único de Vigencia DGI.

Usa Playwright + CapSolver (ImageToTextTask) para resolver el CAPTCHA de imagen
custom de DGI y consultar la vigencia tributaria de un contribuyente en
https://servicios.dgi.gub.uy/serviciosenlinea/dgi--servicios-en-linea--solicitud-de-certificado-de-vigencia-actual
"""

import base64
import time
from datetime import datetime, timezone
from typing import Optional

import httpx
# playwright se importa lazy dentro de consultar_certificado_unico()
from app.core.config import Settings
from app.core.logger import get_logger

logger = get_logger(__name__)

DGI_URL = (
    "https://servicios.dgi.gub.uy/serviciosenlinea/"
    "dgi--servicios-en-linea--solicitud-de-certificado-de-vigencia-actual"
)
CAPSOLVER_API = "https://api.capsolver.com"
EMAIL_GENERICO = "ala@cfointeligente.com"


async def _async_sleep(seconds: float) -> None:
    """Wrapper para asyncio.sleep (facilita testing)."""
    import asyncio
    await asyncio.sleep(seconds)


async def resolver_captcha_imagen_dgi(imagen_base64: str) -> Optional[str]:
    """Resuelve un CAPTCHA de imagen (JPG) usando CapSolver ImageToTextTask.

    Args:
        imagen_base64: Imagen del captcha codificada en base64 (sin prefijo data:).

    Returns:
        Texto reconocido del captcha o None si falla.
    """
    settings = Settings()
    api_key = settings.capsolver_api_key
    if not api_key:
        logger.error("CAPSOLVER_API_KEY no configurada")
        return None

    inicio = time.time()

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                f"{CAPSOLVER_API}/createTask",
                json={
                    "clientKey": api_key,
                    "task": {
                        "type": "ImageToTextTask",
                        "body": imagen_base64,
                    },
                },
            )
            data = resp.json()
        except Exception:
            logger.exception("Error creando tarea CapSolver (ImageToText)")
            return None

        if data.get("errorId", 1) != 0:
            logger.error("CapSolver createTask error: %s", data.get("errorDescription"))
            return None

        task_id = data.get("taskId")
        if not task_id:
            logger.error("CapSolver no retornó taskId")
            return None

        # Polling: ImageToTextTask suele resolver en 1-3s. Máx 30s (15 * 2s).
        for _ in range(15):
            await _async_sleep(2)
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
                texto = result.get("solution", {}).get("text")
                elapsed = time.time() - inicio
                logger.info("Captcha imagen DGI resuelto en %.1fs", elapsed)
                return texto
            elif status == "failed":
                logger.error("CapSolver tarea fallida: %s", result.get("errorDescription"))
                return None

    logger.error("CapSolver timeout tras 15 intentos de polling")
    return None


def _interpretar_resultado(texto: str) -> tuple[Optional[bool], str]:
    """Determina vigencia a partir del texto del iframe DGI."""
    t = (texto or "").lower()
    if "no vigente" in t:
        return False, "NO VIGENTE"
    if "no existe" in t:
        return None, "RUT NO EXISTE"
    if "error" in t:
        return None, "ERROR"
    if "vigente" in t:
        return True, "VIGENTE"
    return None, "INDETERMINADO"


async def consultar_certificado_unico(rut: str, ci: str) -> dict:
    """Consulta el Certificado Único de Vigencia de DGI.

    Args:
        rut: RUT del contribuyente (12 dígitos).
        ci: Cédula de identidad del solicitante.

    Returns:
        Dict con: consultado, vigente, resultado_texto, fecha_consulta, error.
    """
    logger.info("Consultando DGI Certificado Único: rut=%s ci=%s", rut, ci)

    fecha_consulta = datetime.now(timezone.utc).isoformat()
    out = {
        "consultado": False,
        "vigente": None,
        "resultado_texto": "",
        "fecha_consulta": fecha_consulta,
        "error": None,
    }

    browser = None
    try:
        from playwright.async_api import async_playwright
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(DGI_URL, timeout=30000)
        await _async_sleep(5)

        # Localizar iframe del formulario CVA_Solicitud_Web
        frame = None
        for f in page.frames:
            if "CVA_Solicitud_Web" in f.url:
                frame = f
                break
        if frame is None:
            out["error"] = "No se encontró iframe CVA_Solicitud_Web"
            logger.error(out["error"])
            return out

        # Llenar formulario
        await frame.fill("#W0019vRUT", rut)
        await frame.fill("#W0019vCEDULA", ci)
        await frame.fill("#W0019vCORREO", EMAIL_GENERICO)

        # Descargar imagen del CAPTCHA
        captcha_img = await frame.query_selector("img[src*='Captcha/GetImage']")
        if captcha_img is None:
            out["error"] = "No se encontró imagen de captcha"
            logger.error(out["error"])
            return out

        captcha_src = await captcha_img.get_attribute("src")
        if not captcha_src:
            out["error"] = "Imagen de captcha sin src"
            logger.error(out["error"])
            return out

        if captcha_src.startswith("/"):
            captcha_url = "https://servicios.dgi.gub.uy" + captcha_src
        elif captcha_src.startswith("http"):
            captcha_url = captcha_src
        else:
            captcha_url = "https://servicios.dgi.gub.uy/" + captcha_src

        async with httpx.AsyncClient(timeout=30) as client:
            resp_img = await client.get(captcha_url)
            resp_img.raise_for_status()
            imagen_bytes = resp_img.content

        imagen_b64 = base64.b64encode(imagen_bytes).decode("ascii")

        texto_captcha = await resolver_captcha_imagen_dgi(imagen_b64)
        if not texto_captcha:
            out["error"] = "No se pudo resolver el captcha"
            logger.error(out["error"])
            return out

        await frame.fill("#recaptcha_response_field", texto_captcha)
        await frame.click("[name='W0019BUTTONCONFIRMAR']")

        await _async_sleep(5)

        body_text = await frame.evaluate("() => document.body.innerText")
        vigente, etiqueta = _interpretar_resultado(body_text)

        out["consultado"] = True
        out["vigente"] = vigente
        out["resultado_texto"] = etiqueta
        logger.info("DGI consulta finalizada: %s (rut=%s)", etiqueta, rut)
        return out

    except Exception as e:
        logger.exception("Error consultando DGI")
        out["error"] = str(e)
        return out
    finally:
        if browser:
            await browser.close()
