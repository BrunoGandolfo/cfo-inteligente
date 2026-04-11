"""
Otras consultas DGI para el contador.

Funciones:
- consultar_borradores_iass(rut): borradores IASS (impuesto a la asistencia
  a la seguridad social) del portal DGI.
- consultar_exoneracion_arrendamientos(tipo_doc, numero_doc, pais): constancia
  de exoneración de IRPF por arrendamientos.

Ambas páginas son formularios GeneXus cargados dentro de un iframe y están
protegidas por un CAPTCHA de imagen, que se resuelve con CapSolver
(ImageToTextTask) reutilizando ``resolver_captcha_imagen_dgi`` de
``dgi_service``. Si CapSolver falla, se retorna ``error="No se pudo resolver
CAPTCHA"``.

Implementación con Playwright async.
"""

import base64
import re
from datetime import datetime
from typing import Any, Dict, Optional

import httpx

from app.core.logger import get_logger
from app.services.dgi_service import _async_sleep, resolver_captcha_imagen_dgi

logger = get_logger(__name__)

# =============================================================================
# Constantes
# =============================================================================

DGI_IASS_URL = (
    "https://servicios.dgi.gub.uy/serviciosenlinea/consulta_borradoresiass"
)
DGI_EXONERACION_URL = (
    "https://servicios.dgi.gub.uy/serviciosenlinea/"
    "constancia-exoneracion-arrendamientos-irpf-consulta"
)
DGI_TRAMITES_URL = (
    "https://servicios.dgi.gub.uy/serviciosenlinea/"
    "dgi-servicios-en-linea-consulta-de-tramites"
)
DGI_EXPEDIENTES_URL = (
    "https://servicios.dgi.gub.uy/serviciosenlinea/"
    "dgi--servicios-en-linea--consulta-de-expedientes"
)
DGI_PRIMARIA_URL = (
    "https://servicios.dgi.gub.uy/serviciosenlinea/"
    "dgi--servicios-en-linea--impuesto-de-primaria-consulta-de-constancia"
)

DGI_TIMEOUT_MS = 30_000

# Fragmentos que identifican el iframe real (dentro del portal, GeneXus).
IASS_IFRAME_HINT = "BORRADORES_FE"
EXONERACION_IFRAME_HINT = "ConsultaArrendamiento"
TRAMITES_IFRAME_HINT = "GXTramitesFE"
EXPEDIENTES_IFRAME_HINT = "ConsultaExpedientes"
PRIMARIA_IFRAME_HINT = "ConstanciasIEP_FE"

# Selectores IASS
IASS_SEL_RUT = "#W0021vRUT"
IASS_SEL_SUBMIT = 'input[name="W0021BUTTON1"], button[name="W0021BUTTON1"]'

# Selectores Exoneración Arrendamientos
EXO_SEL_TIPO_DOC = "#W0012vTIPODOC_ID"
EXO_SEL_NUMERO = "#W0012vDOCUMENTO"
EXO_SEL_PAIS = "#W0012vPAIS_ID"
EXO_SEL_SUBMIT = 'input[name="W0012BUTTONCONFIRMAR"], button[name="W0012BUTTONCONFIRMAR"]'

# Selectores Seguimiento de trámites
TRAMITE_SEL_NUMERO = "#W0015vTRAMITEINSTID"
TRAMITE_SEL_SUBMIT = 'input[name="W0015BUTTONNEXT"], button[name="W0015BUTTONNEXT"]'

# Selectores Expedientes administrativos
EXPEDIENTE_SEL_NUMERO = "#W0012vNROEXPEDIENTE"
EXPEDIENTE_SEL_SUBMIT = 'input[name="W0012CONSULTAR"], button[name="W0012CONSULTAR"]'

# Selectores Constancia Impuesto de Primaria
PRIMARIA_SEL_NRO = "#W0018vNROCONSTANCIA"
PRIMARIA_SEL_SUBMIT = 'input[name="W0018CONSULTAR"], button[name="W0018CONSULTAR"]'

# CAPTCHA GeneXus — los formularios incluyen una imagen que se ve como
# captcha.gxi / captcha.aspx / gxcaptcha. Basta con detectar un <img>
# cuyo src contenga "captcha".
CAPTCHA_IMG_SELECTOR = 'img[src*="captcha" i]'


# =============================================================================
# Helpers
# =============================================================================


async def _find_genexus_frame(page, url_hint: str):
    """
    Encuentra el frame cuyo URL contiene el hint (ej: 'BORRADORES_FE').
    Devuelve el frame o None si no lo encuentra.
    """
    for frame in page.frames:
        try:
            if url_hint.lower() in (frame.url or "").lower():
                return frame
        except Exception:
            continue
    return None


async def _wait_for_frame(page, url_hint: str, timeout_ms: int):
    """Espera hasta que el frame con el hint esté cargado (poll simple)."""
    import asyncio

    deadline_iters = max(1, timeout_ms // 500)
    for _ in range(deadline_iters):
        frame = await _find_genexus_frame(page, url_hint)
        if frame is not None:
            try:
                await frame.wait_for_load_state("domcontentloaded", timeout=5_000)
            except Exception:
                pass
            return frame
        await asyncio.sleep(0.5)
    return None


async def _captcha_presente(frame) -> bool:
    try:
        return await frame.locator(CAPTCHA_IMG_SELECTOR).count() > 0
    except Exception:
        return False


async def _resolver_captcha_en_frame(frame) -> Optional[str]:
    """
    Localiza el CAPTCHA de imagen en el frame, lo descarga, lo resuelve con
    CapSolver y rellena el campo #recaptcha_response_field.

    Returns:
        Texto reconocido del captcha o None si falló cualquier paso.
    """
    try:
        loc = frame.locator(CAPTCHA_IMG_SELECTOR).first
        src = await loc.get_attribute("src")
    except Exception as e:
        logger.warning(f"No se pudo obtener src del CAPTCHA: {e}")
        return None

    if not src:
        return None

    if src.startswith("/"):
        captcha_url = "https://servicios.dgi.gub.uy" + src
    elif src.startswith("http"):
        captcha_url = src
    else:
        captcha_url = "https://servicios.dgi.gub.uy/" + src

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(captcha_url)
            resp.raise_for_status()
            imagen_b64 = base64.b64encode(resp.content).decode("ascii")
    except Exception as e:
        logger.warning(f"Error descargando imagen CAPTCHA: {e}")
        return None

    texto = await resolver_captcha_imagen_dgi(imagen_b64)
    if not texto:
        return None

    try:
        await frame.locator("#recaptcha_response_field").fill(texto)
    except Exception as e:
        logger.warning(f"No se pudo llenar #recaptcha_response_field: {e}")
        return None

    return texto


async def _extraer_texto(frame) -> str:
    try:
        txt = await frame.locator("body").inner_text(timeout=5_000)
        return re.sub(r"\s+", " ", txt or "").strip()
    except Exception:
        return ""


def _interpretar_borrador(texto: str) -> Optional[bool]:
    t = texto.lower()
    if "no tiene borrador" in t or "no existe borrador" in t or "sin borrador" in t:
        return False
    if "borrador" in t and ("disponible" in t or "generado" in t or "emitido" in t):
        return True
    return None


def _interpretar_exoneracion(texto: str) -> Optional[bool]:
    t = texto.lower()
    if "no posee" in t or "no se encuentra exonerado" in t or "no exonerado" in t:
        return False
    if "exonerado" in t or "exoneración vigente" in t or "posee constancia" in t:
        return True
    return None


def _interpretar_estado_tramite(texto: str) -> Optional[str]:
    """Extrae un estado probable desde el texto devuelto por DGI."""
    texto_limpio = re.sub(r"\s+", " ", texto or "").strip()
    if not texto_limpio:
        return None

    patrones = [
        r"estado\s*:?\s*([A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 ./_-]{3,80})",
        r"situaci[oó]n\s*:?\s*([A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 ./_-]{3,80})",
    ]
    for patron in patrones:
        match = re.search(patron, texto_limpio, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip(" .:-")[:120]

    t = texto_limpio.lower()
    for estado in (
        "finalizado",
        "aprobado",
        "rechazado",
        "observado",
        "en trámite",
        "en tramite",
        "pendiente",
        "ingresado",
        "recibido",
    ):
        if estado in t:
            return estado.upper()

    return None


# =============================================================================
# 1. Consulta Borradores IASS
# =============================================================================


async def consultar_borradores_iass(rut: str) -> Dict[str, Any]:
    """
    Consulta borradores IASS del portal DGI.

    Args:
        rut: RUT del contribuyente.

    Returns:
        Dict con: consultado, tiene_borrador, resultado_texto, fecha_consulta, error
    """
    fecha_consulta = datetime.utcnow().isoformat()
    resultado: Dict[str, Any] = {
        "consultado": False,
        "tiene_borrador": None,
        "resultado_texto": "",
        "fecha_consulta": fecha_consulta,
        "error": None,
    }

    rut_limpio = re.sub(r"\s+", "", str(rut or "")).strip()
    if not rut_limpio:
        resultado["error"] = "RUT vacío"
        return resultado

    try:
        from playwright.async_api import async_playwright  # type: ignore
    except ImportError as e:
        resultado["error"] = f"Playwright no instalado: {e}"
        return resultado

    logger.info(f"Consultando Borradores IASS DGI para RUT={rut_limpio}")

    browser = None
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
            context = await browser.new_context()
            page = await context.new_page()
            page.set_default_timeout(DGI_TIMEOUT_MS)
            page.set_default_navigation_timeout(DGI_TIMEOUT_MS)

            await page.goto(DGI_IASS_URL, wait_until="domcontentloaded", timeout=DGI_TIMEOUT_MS)
            try:
                await page.wait_for_load_state("networkidle", timeout=DGI_TIMEOUT_MS)
            except Exception:
                pass

            frame = await _wait_for_frame(page, IASS_IFRAME_HINT, DGI_TIMEOUT_MS)
            if frame is None:
                resultado["error"] = (
                    f"No se encontró iframe '{IASS_IFRAME_HINT}' en la página DGI"
                )
                return resultado

            try:
                await frame.locator(IASS_SEL_RUT).wait_for(timeout=DGI_TIMEOUT_MS)
                await frame.locator(IASS_SEL_RUT).fill(rut_limpio)
            except Exception as e:
                resultado["error"] = f"No se pudo llenar el campo RUT: {e}"
                return resultado

            if await _captcha_presente(frame):
                texto_captcha = await _resolver_captcha_en_frame(frame)
                if not texto_captcha:
                    resultado["error"] = "No se pudo resolver CAPTCHA"
                    resultado["resultado_texto"] = await _extraer_texto(frame)
                    return resultado

            try:
                await frame.locator(IASS_SEL_SUBMIT).first.click()
            except Exception as e:
                resultado["error"] = f"No se pudo hacer click en el botón de consulta: {e}"
                return resultado

            await _async_sleep(5)
            try:
                await page.wait_for_load_state("networkidle", timeout=DGI_TIMEOUT_MS)
            except Exception:
                pass

            texto = await _extraer_texto(frame)
            resultado["resultado_texto"] = texto[:2000]
            resultado["tiene_borrador"] = _interpretar_borrador(texto)
            resultado["consultado"] = True

            logger.info(
                f"Borradores IASS OK rut={rut_limpio} tiene_borrador={resultado['tiene_borrador']}"
            )

    except Exception as e:
        logger.error(f"Error en consulta Borradores IASS: {e}")
        resultado["error"] = str(e)
        resultado["consultado"] = False
    finally:
        try:
            if browser is not None:
                await browser.close()
        except Exception:
            pass

    return resultado


# =============================================================================
# 3. Consulta Estado de Trámite DGI
# =============================================================================


async def consultar_estado_tramite(nro_tramite: str) -> Dict[str, Any]:
    """
    Consulta el estado de un trámite DGI.

    Args:
        nro_tramite: Número de trámite.

    Returns:
        Dict con: consultado, estado, resultado_texto, fecha_consulta, error
    """
    fecha_consulta = datetime.utcnow().isoformat()
    resultado: Dict[str, Any] = {
        "consultado": False,
        "estado": None,
        "resultado_texto": "",
        "fecha_consulta": fecha_consulta,
        "error": None,
    }

    tramite_limpio = re.sub(r"\s+", "", str(nro_tramite or "")).strip()
    if not tramite_limpio:
        resultado["error"] = "Número de trámite vacío"
        return resultado

    try:
        from playwright.async_api import async_playwright  # type: ignore
    except ImportError as e:
        resultado["error"] = f"Playwright no instalado: {e}"
        return resultado

    logger.info(f"Consultando estado trámite DGI nro={tramite_limpio}")

    browser = None
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
            context = await browser.new_context()
            page = await context.new_page()
            page.set_default_timeout(DGI_TIMEOUT_MS)
            page.set_default_navigation_timeout(DGI_TIMEOUT_MS)

            await page.goto(DGI_TRAMITES_URL, wait_until="domcontentloaded", timeout=DGI_TIMEOUT_MS)
            try:
                await page.wait_for_load_state("networkidle", timeout=DGI_TIMEOUT_MS)
            except Exception:
                pass

            frame = await _wait_for_frame(page, TRAMITES_IFRAME_HINT, DGI_TIMEOUT_MS)
            if frame is None:
                resultado["error"] = (
                    f"No se encontró iframe '{TRAMITES_IFRAME_HINT}' en la página DGI"
                )
                return resultado

            try:
                await frame.locator(TRAMITE_SEL_NUMERO).wait_for(timeout=DGI_TIMEOUT_MS)
                await frame.locator(TRAMITE_SEL_NUMERO).fill(tramite_limpio)
            except Exception as e:
                resultado["error"] = f"No se pudo llenar el número de trámite: {e}"
                return resultado

            if await _captcha_presente(frame):
                texto_captcha = await _resolver_captcha_en_frame(frame)
                if not texto_captcha:
                    resultado["error"] = "No se pudo resolver CAPTCHA"
                    resultado["resultado_texto"] = await _extraer_texto(frame)
                    return resultado

            try:
                await frame.locator(TRAMITE_SEL_SUBMIT).first.click()
            except Exception as e:
                resultado["error"] = f"No se pudo hacer click en el botón siguiente: {e}"
                return resultado

            await _async_sleep(5)
            try:
                await page.wait_for_load_state("networkidle", timeout=DGI_TIMEOUT_MS)
            except Exception:
                pass

            texto = await _extraer_texto(frame)
            resultado["resultado_texto"] = texto[:2000]
            resultado["estado"] = _interpretar_estado_tramite(texto)
            resultado["consultado"] = True

            logger.info(
                f"Estado trámite DGI OK nro={tramite_limpio} estado={resultado['estado']}"
            )

    except Exception as e:
        logger.error(f"Error en consulta Estado Trámite DGI: {e}")
        resultado["error"] = str(e)
        resultado["consultado"] = False
    finally:
        try:
            if browser is not None:
                await browser.close()
        except Exception:
            pass

    return resultado


# =============================================================================
# 4. Consulta Expediente Administrativo DGI
# =============================================================================


async def consultar_expediente_administrativo(nro_expediente: str) -> Dict[str, Any]:
    """
    Consulta un expediente administrativo DGI.

    Args:
        nro_expediente: Número de expediente.

    Returns:
        Dict con: consultado, resultado_texto, fecha_consulta, error
    """
    fecha_consulta = datetime.utcnow().isoformat()
    resultado: Dict[str, Any] = {
        "consultado": False,
        "resultado_texto": "",
        "fecha_consulta": fecha_consulta,
        "error": None,
    }

    expediente_limpio = re.sub(r"\s+", "", str(nro_expediente or "")).strip()
    if not expediente_limpio:
        resultado["error"] = "Número de expediente vacío"
        return resultado

    try:
        from playwright.async_api import async_playwright  # type: ignore
    except ImportError as e:
        resultado["error"] = f"Playwright no instalado: {e}"
        return resultado

    logger.info(f"Consultando expediente administrativo DGI nro={expediente_limpio}")

    browser = None
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
            context = await browser.new_context()
            page = await context.new_page()
            page.set_default_timeout(DGI_TIMEOUT_MS)
            page.set_default_navigation_timeout(DGI_TIMEOUT_MS)

            await page.goto(
                DGI_EXPEDIENTES_URL, wait_until="domcontentloaded", timeout=DGI_TIMEOUT_MS
            )
            try:
                await page.wait_for_load_state("networkidle", timeout=DGI_TIMEOUT_MS)
            except Exception:
                pass

            frame = await _wait_for_frame(page, EXPEDIENTES_IFRAME_HINT, DGI_TIMEOUT_MS)
            if frame is None:
                resultado["error"] = (
                    f"No se encontró iframe '{EXPEDIENTES_IFRAME_HINT}' en la página DGI"
                )
                return resultado

            try:
                await frame.locator(EXPEDIENTE_SEL_NUMERO).wait_for(timeout=DGI_TIMEOUT_MS)
                await frame.locator(EXPEDIENTE_SEL_NUMERO).fill(expediente_limpio)
            except Exception as e:
                resultado["error"] = f"No se pudo llenar el número de expediente: {e}"
                return resultado

            if await _captcha_presente(frame):
                texto_captcha = await _resolver_captcha_en_frame(frame)
                if not texto_captcha:
                    resultado["error"] = "No se pudo resolver CAPTCHA"
                    resultado["resultado_texto"] = await _extraer_texto(frame)
                    return resultado

            try:
                await frame.locator(EXPEDIENTE_SEL_SUBMIT).first.click()
            except Exception as e:
                resultado["error"] = f"No se pudo hacer click en el botón consultar: {e}"
                return resultado

            await _async_sleep(5)
            try:
                await page.wait_for_load_state("networkidle", timeout=DGI_TIMEOUT_MS)
            except Exception:
                pass

            texto = await _extraer_texto(frame)
            resultado["resultado_texto"] = texto[:2000]
            resultado["consultado"] = True

            logger.info(f"Expediente administrativo DGI OK nro={expediente_limpio}")

    except Exception as e:
        logger.error(f"Error en consulta Expediente Administrativo DGI: {e}")
        resultado["error"] = str(e)
        resultado["consultado"] = False
    finally:
        try:
            if browser is not None:
                await browser.close()
        except Exception:
            pass

    return resultado


# =============================================================================
# 2. Consulta Exoneración Arrendamientos IRPF
# =============================================================================

_TIPO_DOC_VALIDOS = {"CI", "NIE", "RUC", "PASAPORTE", "OTRO", "DNI"}


async def consultar_exoneracion_arrendamientos(
    tipo_doc: str,
    numero_doc: str,
    pais: str = "URUGUAY",
) -> Dict[str, Any]:
    """
    Consulta la constancia de exoneración de IRPF por arrendamientos.

    Args:
        tipo_doc: Tipo de documento (CI, NIE, RUC, Pasaporte, Otro, DNI).
        numero_doc: Número del documento.
        pais: País emisor del documento (por defecto URUGUAY).

    Returns:
        Dict con: consultado, tiene_exoneracion, resultado_texto,
        fecha_consulta, error
    """
    fecha_consulta = datetime.utcnow().isoformat()
    resultado: Dict[str, Any] = {
        "consultado": False,
        "tiene_exoneracion": None,
        "resultado_texto": "",
        "fecha_consulta": fecha_consulta,
        "error": None,
    }

    tipo = (tipo_doc or "").strip().upper()
    if tipo == "PASAPORTE":
        tipo_label = "Pasaporte"
    elif tipo == "OTRO":
        tipo_label = "Otro"
    else:
        tipo_label = tipo

    if tipo not in _TIPO_DOC_VALIDOS:
        resultado["error"] = f"Tipo documento inválido: {tipo_doc}"
        return resultado

    numero_limpio = re.sub(r"\s+", "", str(numero_doc or "")).strip()
    if not numero_limpio:
        resultado["error"] = "Número de documento vacío"
        return resultado

    pais_limpio = (pais or "URUGUAY").strip().upper()

    try:
        from playwright.async_api import async_playwright  # type: ignore
    except ImportError as e:
        resultado["error"] = f"Playwright no instalado: {e}"
        return resultado

    logger.info(
        f"Consultando Exoneración Arrendamientos IRPF tipo={tipo} num={numero_limpio} pais={pais_limpio}"
    )

    browser = None
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
            context = await browser.new_context()
            page = await context.new_page()
            page.set_default_timeout(DGI_TIMEOUT_MS)
            page.set_default_navigation_timeout(DGI_TIMEOUT_MS)

            await page.goto(
                DGI_EXONERACION_URL, wait_until="domcontentloaded", timeout=DGI_TIMEOUT_MS
            )
            try:
                await page.wait_for_load_state("networkidle", timeout=DGI_TIMEOUT_MS)
            except Exception:
                pass

            frame = await _wait_for_frame(page, EXONERACION_IFRAME_HINT, DGI_TIMEOUT_MS)
            if frame is None:
                resultado["error"] = (
                    f"No se encontró iframe '{EXONERACION_IFRAME_HINT}' en la página DGI"
                )
                return resultado

            # Tipo de documento
            try:
                await frame.locator(EXO_SEL_TIPO_DOC).wait_for(timeout=DGI_TIMEOUT_MS)
                try:
                    await frame.locator(EXO_SEL_TIPO_DOC).select_option(label=tipo_label)
                except Exception:
                    await frame.locator(EXO_SEL_TIPO_DOC).select_option(tipo_label)
            except Exception as e:
                resultado["error"] = f"No se pudo seleccionar tipo de documento: {e}"
                return resultado

            # Número de documento
            try:
                await frame.locator(EXO_SEL_NUMERO).fill(numero_limpio)
            except Exception as e:
                resultado["error"] = f"No se pudo llenar el número de documento: {e}"
                return resultado

            # País
            try:
                await frame.locator(EXO_SEL_PAIS).select_option(label=pais_limpio)
            except Exception:
                try:
                    await frame.locator(EXO_SEL_PAIS).select_option(pais_limpio)
                except Exception as e:
                    logger.warning(f"No se pudo seleccionar país '{pais_limpio}': {e}")

            if await _captcha_presente(frame):
                texto_captcha = await _resolver_captcha_en_frame(frame)
                if not texto_captcha:
                    resultado["error"] = "No se pudo resolver CAPTCHA"
                    resultado["resultado_texto"] = await _extraer_texto(frame)
                    return resultado

            try:
                await frame.locator(EXO_SEL_SUBMIT).first.click()
            except Exception as e:
                resultado["error"] = f"No se pudo hacer click en el botón confirmar: {e}"
                return resultado

            await _async_sleep(5)
            try:
                await page.wait_for_load_state("networkidle", timeout=DGI_TIMEOUT_MS)
            except Exception:
                pass

            texto = await _extraer_texto(frame)
            resultado["resultado_texto"] = texto[:2000]
            resultado["tiene_exoneracion"] = _interpretar_exoneracion(texto)
            resultado["consultado"] = True

            logger.info(
                f"Exoneración arrendamientos OK tipo={tipo} num={numero_limpio} "
                f"tiene_exoneracion={resultado['tiene_exoneracion']}"
            )

    except Exception as e:
        logger.error(f"Error en consulta Exoneración Arrendamientos: {e}")
        resultado["error"] = str(e)
        resultado["consultado"] = False
    finally:
        try:
            if browser is not None:
                await browser.close()
        except Exception:
            pass

    return resultado


# =============================================================================
# 5. Consulta Constancia Impuesto de Primaria
# =============================================================================


async def consultar_constancia_primaria(nro_constancia: str) -> Dict[str, Any]:
    """
    Consulta la constancia del Impuesto de Educación Primaria en DGI.

    El contador la necesita para operaciones inmobiliarias.

    Args:
        nro_constancia: Número de constancia a consultar.

    Returns:
        Dict con: consultado, resultado_texto, fecha_consulta, error
    """
    fecha_consulta = datetime.utcnow().isoformat()
    resultado: Dict[str, Any] = {
        "consultado": False,
        "resultado_texto": "",
        "fecha_consulta": fecha_consulta,
        "error": None,
    }

    nro_limpio = re.sub(r"\s+", "", str(nro_constancia or "")).strip()
    if not nro_limpio:
        resultado["error"] = "Número de constancia vacío"
        return resultado

    try:
        from playwright.async_api import async_playwright  # type: ignore
    except ImportError as e:
        resultado["error"] = f"Playwright no instalado: {e}"
        return resultado

    logger.info(f"Consultando Constancia Primaria DGI nro={nro_limpio}")

    browser = None
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
            context = await browser.new_context()
            page = await context.new_page()
            page.set_default_timeout(DGI_TIMEOUT_MS)
            page.set_default_navigation_timeout(DGI_TIMEOUT_MS)

            await page.goto(
                DGI_PRIMARIA_URL, wait_until="domcontentloaded", timeout=DGI_TIMEOUT_MS
            )
            try:
                await page.wait_for_load_state("networkidle", timeout=DGI_TIMEOUT_MS)
            except Exception:
                pass

            frame = await _wait_for_frame(page, PRIMARIA_IFRAME_HINT, DGI_TIMEOUT_MS)
            if frame is None:
                resultado["error"] = (
                    f"No se encontró iframe '{PRIMARIA_IFRAME_HINT}' en la página DGI"
                )
                return resultado

            try:
                await frame.locator(PRIMARIA_SEL_NRO).wait_for(timeout=DGI_TIMEOUT_MS)
                await frame.locator(PRIMARIA_SEL_NRO).fill(nro_limpio)
            except Exception as e:
                resultado["error"] = f"No se pudo llenar el número de constancia: {e}"
                return resultado

            if await _captcha_presente(frame):
                texto_captcha = await _resolver_captcha_en_frame(frame)
                if not texto_captcha:
                    resultado["error"] = "No se pudo resolver CAPTCHA"
                    resultado["resultado_texto"] = await _extraer_texto(frame)
                    return resultado

            try:
                await frame.locator(PRIMARIA_SEL_SUBMIT).first.click()
            except Exception as e:
                resultado["error"] = f"No se pudo hacer click en el botón consultar: {e}"
                return resultado

            await _async_sleep(5)
            try:
                await page.wait_for_load_state("networkidle", timeout=DGI_TIMEOUT_MS)
            except Exception:
                pass

            texto = await _extraer_texto(frame)
            resultado["resultado_texto"] = texto[:2000]
            resultado["consultado"] = True

            logger.info(f"Constancia Primaria OK nro={nro_limpio}")

    except Exception as e:
        logger.error(f"Error en consulta Constancia Primaria: {e}")
        resultado["error"] = str(e)
        resultado["consultado"] = False
    finally:
        try:
            if browser is not None:
                await browser.close()
        except Exception:
            pass

    return resultado


# =============================================================================
# 6. Consulta Devolución IVA Gasoil — beneficiarios productores rurales
# =============================================================================

DGI_DEVGASOIL_URL = (
    "https://servicios.dgi.gub.uy/serviciosenlinea/"
    "devoluciones-iva-gasoil--consulta-beneficiarios"
)
DEVGASOIL_IFRAME_HINT = "DevGasoilPublico"
DEVGASOIL_SEL_RUC = "#vNRORUC"
DEVGASOIL_SEL_SUBMIT = 'input[name="BUTTON2"], button[name="BUTTON2"], #BUTTON2'


def _interpretar_devolucion_gasoil(texto: str) -> Optional[bool]:
    t = texto.lower()
    if (
        "no es beneficiario" in t
        or "no se encuentra" in t
        or "no figura" in t
        or "no registra" in t
    ):
        return False
    if (
        "es beneficiario" in t
        or "beneficiario de la devoluci" in t
        or "figura como beneficiario" in t
    ):
        return True
    return None


async def consultar_devolucion_iva_gasoil(ruc: str) -> Dict[str, Any]:
    """
    Consulta si un RUC figura como beneficiario de la devolución de IVA Gasoil
    para productores rurales (DGI).

    Args:
        ruc: RUC del contribuyente.

    Returns:
        Dict con: consultado, es_beneficiario, resultado_texto,
        fecha_consulta, error
    """
    fecha_consulta = datetime.utcnow().isoformat()
    resultado: Dict[str, Any] = {
        "consultado": False,
        "es_beneficiario": None,
        "resultado_texto": "",
        "fecha_consulta": fecha_consulta,
        "error": None,
    }

    ruc_limpio = re.sub(r"\s+", "", str(ruc or "")).strip()
    if not ruc_limpio:
        resultado["error"] = "RUC vacío"
        return resultado

    try:
        from playwright.async_api import async_playwright  # type: ignore
    except ImportError as e:
        resultado["error"] = f"Playwright no instalado: {e}"
        return resultado

    logger.info(f"Consultando Devolución IVA Gasoil DGI para RUC={ruc_limpio}")

    browser = None
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
            context = await browser.new_context()
            page = await context.new_page()
            page.set_default_timeout(DGI_TIMEOUT_MS)
            page.set_default_navigation_timeout(DGI_TIMEOUT_MS)

            await page.goto(
                DGI_DEVGASOIL_URL, wait_until="domcontentloaded", timeout=DGI_TIMEOUT_MS
            )
            try:
                await page.wait_for_load_state("networkidle", timeout=DGI_TIMEOUT_MS)
            except Exception:
                pass

            frame = await _wait_for_frame(page, DEVGASOIL_IFRAME_HINT, DGI_TIMEOUT_MS)
            if frame is None:
                resultado["error"] = (
                    f"No se encontró iframe '{DEVGASOIL_IFRAME_HINT}' en la página DGI"
                )
                return resultado

            try:
                await frame.locator(DEVGASOIL_SEL_RUC).wait_for(timeout=DGI_TIMEOUT_MS)
                await frame.locator(DEVGASOIL_SEL_RUC).fill(ruc_limpio)
            except Exception as e:
                resultado["error"] = f"No se pudo llenar el campo RUC: {e}"
                return resultado

            if await _captcha_presente(frame):
                texto_captcha = await _resolver_captcha_en_frame(frame)
                if not texto_captcha:
                    resultado["error"] = "No se pudo resolver CAPTCHA"
                    resultado["resultado_texto"] = await _extraer_texto(frame)
                    return resultado

            try:
                await frame.locator(DEVGASOIL_SEL_SUBMIT).first.click()
            except Exception as e:
                resultado["error"] = f"No se pudo hacer click en el botón consultar: {e}"
                return resultado

            await _async_sleep(5)
            try:
                await page.wait_for_load_state("networkidle", timeout=DGI_TIMEOUT_MS)
            except Exception:
                pass

            texto = await _extraer_texto(frame)
            resultado["resultado_texto"] = texto[:2000]
            resultado["es_beneficiario"] = _interpretar_devolucion_gasoil(texto)
            resultado["consultado"] = True

            logger.info(
                f"Devolución IVA Gasoil OK ruc={ruc_limpio} "
                f"es_beneficiario={resultado['es_beneficiario']}"
            )

    except Exception as e:
        logger.error(f"Error en consulta Devolución IVA Gasoil: {e}")
        resultado["error"] = str(e)
        resultado["consultado"] = False
    finally:
        try:
            if browser is not None:
                await browser.close()
        except Exception:
            pass

    return resultado
