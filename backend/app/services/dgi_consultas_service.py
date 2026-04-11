"""Consultas publicas DGI complementarias.

Consulta declaracion IRPF por CI usando el formulario GeneXus de DGI.
"""

import base64
import re
import time
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urljoin

import httpx

from app.core.config import Settings
from app.core.logger import get_logger

logger = get_logger(__name__)

DGI_DECLARACION_IRPF_URL = (
    "https://servicios.dgi.gub.uy/serviciosenlinea/"
    "dgi--servicios-en-linea--declaracion-irpf-consulta"
)
DGI_RESIDENCIA_FISCAL_URL = (
    "https://servicios.dgi.gub.uy/serviciosenlinea/"
    "certificadoresidenciafiscalconsulta"
)
CAPSOLVER_API = "https://api.capsolver.com"
DGI_TIMEOUT_MS = 30_000

try:
    from app.services.dgi_service import resolver_captcha_imagen_dgi
except ImportError:

    async def resolver_captcha_imagen_dgi(imagen_base64: str) -> Optional[str]:
        """Resuelve un CAPTCHA de imagen DGI usando CapSolver ImageToTextTask."""
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
                logger.error("CapSolver no retorno taskId")
                return None

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
                if status == "failed":
                    logger.error("CapSolver tarea fallida: %s", result.get("errorDescription"))
                    return None

        logger.error("CapSolver timeout tras 15 intentos de polling")
        return None


async def _async_sleep(seconds: float) -> None:
    """Wrapper para asyncio.sleep."""
    import asyncio

    await asyncio.sleep(seconds)


def _limpiar_ci(ci: str) -> str:
    return re.sub(r"\D", "", str(ci or ""))


def _normalizar_texto_resultado(texto: str) -> str:
    return re.sub(r"\s+", " ", texto or "").strip()


def _interpretar_declaracion_irpf(texto: str) -> Optional[bool]:
    """Devuelve True/False si el texto permite inferir declaracion, None si no."""
    t = (texto or "").lower()

    negativos = (
        "no tiene declaracion",
        "no tiene declaraciones",
        "no existe declaracion",
        "no existen declaraciones",
        "no se encontro declaracion",
        "no se encontraron declaraciones",
        "no registra declaracion",
        "no registra declaraciones",
        "sin declaracion",
        "sin declaraciones",
    )
    if any(patron in t for patron in negativos):
        return False

    positivos = (
        "tiene declaracion",
        "tiene declaraciones",
        "existe declaracion",
        "existen declaraciones",
        "declaracion presentada",
        "declaraciones presentadas",
        "presento declaracion",
        "presenta declaracion",
    )
    if any(patron in t for patron in positivos):
        return True

    return None


def _extraer_anio(texto: str) -> Optional[str]:
    match = re.search(r"\b(19\d{2}|20\d{2})\b", texto or "")
    return match.group(1) if match else None


def _captcha_url(frame_url: str, captcha_src: str) -> str:
    return urljoin(frame_url or DGI_DECLARACION_IRPF_URL, captcha_src)


async def _descargar_imagen_captcha(context, captcha_url: str) -> bytes:
    cookies = await context.cookies(captcha_url)
    cookie_jar = {cookie["name"]: cookie["value"] for cookie in cookies}
    async with httpx.AsyncClient(timeout=30, cookies=cookie_jar) as client:
        resp = await client.get(captcha_url)
        resp.raise_for_status()
        return resp.content


def _buscar_frame_irpf(page):
    for frame in page.frames:
        if "F1102_ConsExiste" in frame.url:
            return frame
    return None


async def consultar_declaracion_irpf(ci: str) -> dict:
    """Consulta en DGI si una CI tiene declaracion IRPF.

    Returns:
        Dict con: consultado, tiene_declaracion, resultado_texto, anio,
        fecha_consulta, error.
    """
    fecha_consulta = datetime.now(timezone.utc).isoformat()
    out = {
        "consultado": False,
        "tiene_declaracion": None,
        "resultado_texto": "",
        "anio": None,
        "fecha_consulta": fecha_consulta,
        "error": None,
    }

    ci_limpia = _limpiar_ci(ci)
    if not ci_limpia:
        out["error"] = "CI vacia"
        return out

    logger.info("Consultando DGI declaracion IRPF: ci=%s", ci_limpia)

    browser = None
    pw = None
    try:
        from playwright.async_api import async_playwright

        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        page.set_default_timeout(DGI_TIMEOUT_MS)
        page.set_default_navigation_timeout(DGI_TIMEOUT_MS)

        await page.goto(DGI_DECLARACION_IRPF_URL, timeout=DGI_TIMEOUT_MS)
        await _async_sleep(5)

        frame = _buscar_frame_irpf(page)
        if frame is None:
            for _ in range(10):
                await _async_sleep(1)
                frame = _buscar_frame_irpf(page)
                if frame is not None:
                    break

        if frame is None:
            out["error"] = "No se encontro iframe F1102_ConsExiste"
            logger.error(out["error"])
            return out

        await frame.fill("#W0025vCI", ci_limpia)

        captcha_img = await frame.query_selector("img[src*='Captcha/GetImage']")
        if captcha_img is None:
            out["error"] = "No se encontro imagen de captcha"
            logger.error(out["error"])
            return out

        captcha_src = await captcha_img.get_attribute("src")
        if not captcha_src:
            out["error"] = "Imagen de captcha sin src"
            logger.error(out["error"])
            return out

        imagen_bytes = await _descargar_imagen_captcha(
            context,
            _captcha_url(frame.url, captcha_src),
        )
        imagen_b64 = base64.b64encode(imagen_bytes).decode("ascii")

        texto_captcha = await resolver_captcha_imagen_dgi(imagen_b64)
        if not texto_captcha:
            out["error"] = "No se pudo resolver el captcha"
            logger.error(out["error"])
            return out

        await frame.fill("#recaptcha_response_field", texto_captcha)
        await frame.click('[name="W0025BTNCONFIRMAR"]')

        try:
            await page.wait_for_load_state("networkidle", timeout=DGI_TIMEOUT_MS)
        except Exception:
            pass
        await _async_sleep(3)

        frame = _buscar_frame_irpf(page) or frame
        body_text = await frame.evaluate("() => document.body.innerText")
        resultado_texto = _normalizar_texto_resultado(body_text)

        if "captcha" in resultado_texto.lower() and "incorrect" in resultado_texto.lower():
            out["error"] = "Captcha rechazado por DGI"
            logger.error(out["error"])
            return out

        out["consultado"] = True
        out["tiene_declaracion"] = _interpretar_declaracion_irpf(resultado_texto)
        out["resultado_texto"] = resultado_texto
        out["anio"] = _extraer_anio(resultado_texto)

        logger.info(
            "DGI IRPF consulta finalizada: ci=%s tiene_declaracion=%s anio=%s",
            ci_limpia,
            out["tiene_declaracion"],
            out["anio"],
        )
        return out

    except Exception as e:
        logger.exception("Error consultando DGI declaracion IRPF")
        out["error"] = str(e)
        return out
    finally:
        if browser:
            await browser.close()
        if pw:
            await pw.stop()


def _buscar_frame_residencia(page):
    for frame in page.frames:
        if "ECOFE" in frame.url:
            return frame
    return None


async def consultar_certificado_residencia_fiscal(
    nro_solicitud: str,
    linea: str,
    tipo: str,
    principio_crc: str,
) -> dict:
    """Verifica un Certificado de Residencia Fiscal ya emitido por DGI.

    No usa CAPTCHA: el control es el código de seguridad de 4 partes
    impreso en el propio certificado.

    Returns:
        Dict con: consultado, resultado_texto, fecha_consulta, error.
    """
    fecha_consulta = datetime.now(timezone.utc).isoformat()
    out = {
        "consultado": False,
        "resultado_texto": "",
        "fecha_consulta": fecha_consulta,
        "error": None,
    }

    nro = (nro_solicitud or "").strip()
    lin = (linea or "").strip()
    tip = (tipo or "").strip()
    prc = (principio_crc or "").strip()
    if not nro or not lin or not tip or not prc:
        out["error"] = "Faltan campos del código de seguridad"
        return out

    logger.info(
        "Consultando DGI Certificado Residencia Fiscal: nro=%s linea=%s tipo=%s",
        nro, lin, tip,
    )

    browser = None
    pw = None
    try:
        from playwright.async_api import async_playwright

        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        page.set_default_timeout(DGI_TIMEOUT_MS)
        page.set_default_navigation_timeout(DGI_TIMEOUT_MS)

        await page.goto(DGI_RESIDENCIA_FISCAL_URL, timeout=DGI_TIMEOUT_MS)
        await _async_sleep(5)

        frame = _buscar_frame_residencia(page)
        if frame is None:
            for _ in range(10):
                await _async_sleep(1)
                frame = _buscar_frame_residencia(page)
                if frame is not None:
                    break

        if frame is None:
            out["error"] = "No se encontro iframe ECOFE"
            logger.error(out["error"])
            return out

        await frame.fill("#vNROSOL", nro)
        await frame.fill("#vCRFLIN", lin)
        await frame.fill("#vTPOCRF", tip)
        await frame.fill("#vPRINCIPIOCRC", prc)

        await frame.click('[name="BUTTON1"]')

        await _async_sleep(5)
        try:
            await page.wait_for_load_state("networkidle", timeout=DGI_TIMEOUT_MS)
        except Exception:
            pass

        frame = _buscar_frame_residencia(page) or frame
        body_text = await frame.evaluate("() => document.body.innerText")
        resultado_texto = _normalizar_texto_resultado(body_text)

        out["consultado"] = True
        out["resultado_texto"] = resultado_texto[:2000]
        logger.info("DGI Residencia Fiscal consulta finalizada: nro=%s", nro)
        return out

    except Exception as e:
        logger.exception("Error consultando DGI certificado residencia fiscal")
        out["error"] = str(e)
        return out
    finally:
        if browser:
            await browser.close()
        if pw:
            await pw.stop()
