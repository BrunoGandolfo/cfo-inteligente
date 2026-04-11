"""Service de consulta de Afiliación Bancaria DGI.

Usa Playwright + CapSolver (ImageToTextTask) para resolver el CAPTCHA de imagen
custom de DGI y consultar si un contribuyente tiene cuenta bancaria declarada
ante DGI (relevante para ALA — debida diligencia).

URL: https://servicios.dgi.gub.uy/serviciosenlinea/dgi--servicios-en-linea--consultas--consulta-de-afiliacion-bancaria

ADVERTENCIA LEGAL:
    Este servicio DGI indica expresamente: "Información reservada — para uso
    del titular. Acceso de terceros sujeto a responsabilidad legal."
    Su uso debe ceñirse a los casos habilitados por la normativa ALA
    (Decreto 379/018) y contar con autorización documentada del titular.
"""

import base64
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.core.logger import get_logger
from app.services.dgi_service import _async_sleep, resolver_captcha_imagen_dgi

logger = get_logger(__name__)

DGI_AFILIACION_URL = (
    "https://servicios.dgi.gub.uy/serviciosenlinea/"
    "dgi--servicios-en-linea--consultas--consulta-de-afiliacion-bancaria"
)


def _interpretar_afiliacion(texto: str) -> tuple[Optional[bool], str]:
    """Determina afiliación bancaria a partir del texto del iframe DGI."""
    t = (texto or "").lower()
    if "no existe" in t or "no se encontr" in t:
        return None, "RUT NO EXISTE"
    if "error" in t:
        return None, "ERROR"
    if "no registra" in t or "sin afiliaci" in t or "no posee" in t:
        return False, "SIN AFILIACION BANCARIA"
    if "afiliaci" in t or "cuenta" in t or "banco" in t:
        return True, "CON AFILIACION BANCARIA"
    return None, "INDETERMINADO"


async def consultar_afiliacion_bancaria(rut: str) -> dict:
    """Consulta si un contribuyente tiene afiliación bancaria declarada ante DGI.

    ADVERTENCIA LEGAL: Información reservada — para uso del titular. Acceso de
    terceros sujeto a responsabilidad legal. Usar sólo en el marco de procesos
    ALA debidamente autorizados (Decreto 379/018).

    Args:
        rut: RUT del contribuyente (12 dígitos).

    Returns:
        Dict con:
            - consultado: bool
            - tiene_afiliacion: bool | None
            - resultado_texto: str
            - fecha_consulta: str (ISO 8601 UTC)
            - error: str | None
    """
    logger.info("Consultando DGI Afiliación Bancaria: rut=%s", rut)

    fecha_consulta = datetime.now(timezone.utc).isoformat()
    out: dict = {
        "consultado": False,
        "tiene_afiliacion": None,
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

        await page.goto(DGI_AFILIACION_URL, timeout=30000)
        await _async_sleep(5)

        # Localizar iframe del formulario (contiene 'consafilbanc' en la URL)
        frame = None
        for f in page.frames:
            if "consafilbanc" in f.url.lower():
                frame = f
                break
        if frame is None:
            out["error"] = "No se encontró iframe consafilbanc"
            logger.error(out["error"])
            return out

        # Llenar RUT (campo dice vCI pero corresponde al RUT)
        await frame.fill("#W0025vCI", rut)

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
        await frame.click("[name='W0025BTNCONFIRMAR']")

        await _async_sleep(5)

        body_text = await frame.evaluate("() => document.body.innerText")
        tiene_afiliacion, etiqueta = _interpretar_afiliacion(body_text)

        out["consultado"] = True
        out["tiene_afiliacion"] = tiene_afiliacion
        out["resultado_texto"] = etiqueta
        logger.info("DGI afiliación finalizada: %s (rut=%s)", etiqueta, rut)
        return out

    except Exception as e:
        logger.exception("Error consultando DGI Afiliación Bancaria")
        out["error"] = str(e)
        return out
    finally:
        if browser:
            await browser.close()
