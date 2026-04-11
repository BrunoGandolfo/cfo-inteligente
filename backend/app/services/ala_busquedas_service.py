"""
Servicio de búsquedas complementarias Art. 44 C.4 para ALA.

Ejecuta búsquedas automáticas en:
- Wikipedia (API pública gratuita)
- Google/análisis IA (Claude Anthropic)
- Noticias/análisis IA (Claude Anthropic)

Decreto 379/018 - Art. 44 C.4
"""

import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import anthropic
import requests

from app.core.config import settings
from app.core.constants import CLAUDE_MODEL
from app.core.logger import get_logger

logger = get_logger(__name__)

# =============================================================================
# Constantes
# =============================================================================

WIKIPEDIA_TIMEOUT = 15  # segundos
CLAUDE_TIMEOUT = 30  # segundos
# CLAUDE_MODEL importado de app.core.constants

# Headers requeridos por Wikipedia API
WIKIPEDIA_HEADERS = {
    "User-Agent": "CFOInteligente/1.0 (https://cfo-inteligente.com; contacto@cfo-inteligente.com) requests/2.x",
    "Accept": "application/json",
}


# =============================================================================
# 1. Búsqueda Wikipedia
# =============================================================================

def buscar_wikipedia(nombre_completo: str, nacionalidad: str = "UY") -> Dict[str, Any]:
    """
    Busca en Wikipedia API pública si la persona tiene artículo.
    
    Busca en Wikipedia ES y EN.
    
    Args:
        nombre_completo: Nombre de la persona
        nacionalidad: Código ISO del país (para contexto)
    
    Returns:
        Dict con: realizada, encontrado, resultados, observaciones, error
    """
    resultado = {
        "realizada": False,
        "encontrado": False,
        "resultados": [],
        "observaciones": "",
        "error": None,
    }
    
    try:
        logger.info(f"Buscando en Wikipedia: {nombre_completo}")
        
        resultados_encontrados: List[Dict[str, str]] = []
        
        # Buscar en Wikipedia ES
        try:
            url_es = "https://es.wikipedia.org/w/api.php"
            params_es = {
                "action": "query",
                "list": "search",
                "srsearch": nombre_completo,
                "format": "json",
                "srlimit": 5,
            }
            resp_es = requests.get(url_es, params=params_es, headers=WIKIPEDIA_HEADERS, timeout=WIKIPEDIA_TIMEOUT)
            resp_es.raise_for_status()
            data_es = resp_es.json()
            
            search_results_es = data_es.get("query", {}).get("search", [])
            
            for item in search_results_es[:3]:
                titulo = item.get("title", "")
                # Obtener resumen
                try:
                    url_summary = f"https://es.wikipedia.org/api/rest_v1/page/summary/{titulo.replace(' ', '_')}"
                    resp_summary = requests.get(url_summary, headers=WIKIPEDIA_HEADERS, timeout=WIKIPEDIA_TIMEOUT)
                    if resp_summary.status_code == 200:
                        summary_data = resp_summary.json()
                        resultados_encontrados.append({
                            "titulo": titulo,
                            "resumen": summary_data.get("extract", "")[:500],
                            "url": summary_data.get("content_urls", {}).get("desktop", {}).get("page", f"https://es.wikipedia.org/wiki/{titulo}"),
                            "idioma": "ES",
                        })
                except Exception as e:
                    logger.warning(f"No se pudo obtener resumen de Wikipedia ES para '{titulo}': {e}")
                    # Si falla obtener resumen, agregar sin él
                    resultados_encontrados.append({
                        "titulo": titulo,
                        "resumen": item.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", "")[:300],
                        "url": f"https://es.wikipedia.org/wiki/{titulo.replace(' ', '_')}",
                        "idioma": "ES",
                    })
        except requests.RequestException as e:
            logger.warning(f"Error buscando Wikipedia ES: {e}")
        
        # Buscar en Wikipedia EN (para personas internacionales)
        try:
            url_en = "https://en.wikipedia.org/w/api.php"
            params_en = {
                "action": "query",
                "list": "search",
                "srsearch": nombre_completo,
                "format": "json",
                "srlimit": 3,
            }
            resp_en = requests.get(url_en, params=params_en, headers=WIKIPEDIA_HEADERS, timeout=WIKIPEDIA_TIMEOUT)
            resp_en.raise_for_status()
            data_en = resp_en.json()
            
            search_results_en = data_en.get("query", {}).get("search", [])
            
            for item in search_results_en[:2]:
                titulo = item.get("title", "")
                # Verificar que no sea duplicado de ES
                if not any(r["titulo"].lower() == titulo.lower() for r in resultados_encontrados):
                    resultados_encontrados.append({
                        "titulo": titulo,
                        "resumen": item.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", "")[:300],
                        "url": f"https://en.wikipedia.org/wiki/{titulo.replace(' ', '_')}",
                        "idioma": "EN",
                    })
        except requests.RequestException as e:
            logger.warning(f"Error buscando Wikipedia EN: {e}")
        
        # Marcar como realizada
        resultado["realizada"] = True
        resultado["resultados"] = resultados_encontrados
        resultado["encontrado"] = len(resultados_encontrados) > 0
        
        # Generar observaciones legibles
        if resultados_encontrados:
            titulos = [r["titulo"] for r in resultados_encontrados[:3]]
            resultado["observaciones"] = f"Se encontraron {len(resultados_encontrados)} artículo(s) relacionados en Wikipedia: {', '.join(titulos)}. Revisar manualmente para confirmar si corresponden a la persona verificada."
        else:
            resultado["observaciones"] = "No se encontraron artículos en Wikipedia ES ni EN para esta persona."
        
        logger.info(f"Wikipedia: encontrado={resultado['encontrado']}, resultados={len(resultados_encontrados)}")
        
    except Exception as e:
        logger.error(f"Error en búsqueda Wikipedia: {e}")
        resultado["error"] = str(e)
        resultado["observaciones"] = f"Error al buscar en Wikipedia: {str(e)}"
    
    return resultado


# =============================================================================
# 2. Búsqueda Google/IA con Claude
# =============================================================================

def buscar_google_claude(
    nombre_completo: str,
    nacionalidad: str,
    tipo_documento: str,
    numero_documento: str,
) -> Dict[str, Any]:
    """
    Usa Claude para analizar información pública conocida sobre la persona
    en contexto de debida diligencia ALA/AML.
    
    Args:
        nombre_completo: Nombre de la persona
        nacionalidad: Código ISO
        tipo_documento: CI, RUT, PASAPORTE
        numero_documento: Número del documento
    
    Returns:
        Dict con: realizada, observaciones, riesgo_sugerido, error
    """
    resultado = {
        "realizada": False,
        "observaciones": "Búsqueda no disponible",
        "riesgo_sugerido": None,
        "error": None,
    }
    
    try:
        logger.info(f"Analizando con Claude (Google/IA): {nombre_completo}")
        
        # Crear cliente Anthropic con API key de settings
        api_key = settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY no configurada")
        client = anthropic.Anthropic(api_key=api_key)
        
        prompt = f"""Eres un analista de debida diligencia para Anti-Lavado de Activos (ALA/AML).

Analiza a la siguiente persona:
- Nombre: {nombre_completo}
- Documento: {tipo_documento} {numero_documento or 'No proporcionado'}
- Nacionalidad: {nacionalidad}

Responde SOLO con información que conozcas con certeza. Si no conoces a la persona, dilo claramente. NO inventes información.

Indica:
1. ¿Es una persona pública o políticamente expuesta conocida?
2. ¿Hay información sobre investigaciones judiciales, procesos penales o sanciones?
3. ¿Hay información sobre vínculos con actividades ilícitas?
4. ¿Hay menciones relevantes en medios de comunicación?
5. Nivel de riesgo sugerido basado en información pública: NINGUNO / BAJO / MEDIO / ALTO

Si no hay información relevante, responde: "No se encontró información pública relevante sobre esta persona en el contexto de debida diligencia ALA."

Responde de forma concisa y profesional."""
        
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        respuesta = message.content[0].text if message.content else ""
        
        resultado["realizada"] = True
        resultado["observaciones"] = respuesta
        
        # Intentar extraer nivel de riesgo sugerido
        respuesta_upper = respuesta.upper()
        if "RIESGO: ALTO" in respuesta_upper or "RIESGO ALTO" in respuesta_upper:
            resultado["riesgo_sugerido"] = "ALTO"
        elif "RIESGO: MEDIO" in respuesta_upper or "RIESGO MEDIO" in respuesta_upper:
            resultado["riesgo_sugerido"] = "MEDIO"
        elif "RIESGO: BAJO" in respuesta_upper or "RIESGO BAJO" in respuesta_upper:
            resultado["riesgo_sugerido"] = "BAJO"
        elif "RIESGO: NINGUNO" in respuesta_upper or "NINGUNO" in respuesta_upper:
            resultado["riesgo_sugerido"] = "NINGUNO"
        
        logger.info(f"Claude Google/IA: completado, riesgo_sugerido={resultado['riesgo_sugerido']}")
        
    except anthropic.APIError as e:
        logger.error(f"Error API Anthropic (Google/IA): {e}")
        resultado["error"] = f"Error API: {str(e)}"
        resultado["observaciones"] = "Búsqueda con IA no disponible temporalmente."
    except Exception as e:
        logger.error(f"Error en búsqueda Google/Claude: {e}")
        resultado["error"] = str(e)
        resultado["observaciones"] = f"Error al realizar análisis: {str(e)}"
    
    return resultado


# =============================================================================
# 3. Búsqueda Noticias/IA con Claude
# =============================================================================

def buscar_noticias_claude(nombre_completo: str, nacionalidad: str) -> Dict[str, Any]:
    """
    Usa Claude para analizar menciones en noticias sobre la persona.
    
    Args:
        nombre_completo: Nombre de la persona
        nacionalidad: Código ISO
    
    Returns:
        Dict con: realizada, observaciones, menciones_encontradas, error
    """
    resultado = {
        "realizada": False,
        "observaciones": "Búsqueda no disponible",
        "menciones_encontradas": False,
        "error": None,
    }
    
    try:
        logger.info(f"Analizando noticias con Claude: {nombre_completo}")
        
        # Crear cliente Anthropic con API key de settings
        api_key = settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY no configurada")
        client = anthropic.Anthropic(api_key=api_key)
        
        prompt = f"""Eres un analista de debida diligencia ALA/AML.

Busca menciones en noticias y medios de comunicación sobre:
- Nombre: {nombre_completo}
- Nacionalidad: {nacionalidad}

Responde SOLO con información que conozcas con certeza. NO inventes.

Indica:
1. ¿Ha aparecido en noticias relacionadas con lavado de activos, fraude, corrupción u otros delitos financieros?
2. ¿Ha aparecido en noticias por investigaciones judiciales o procesos penales?
3. ¿Ha aparecido en noticias por sanciones internacionales?
4. Resumen de menciones relevantes (si existen)

Si no hay menciones relevantes, responde: "No se encontraron menciones relevantes en noticias sobre esta persona."

Responde de forma concisa y profesional."""
        
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=400,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        respuesta = message.content[0].text if message.content else ""
        
        resultado["realizada"] = True
        resultado["observaciones"] = respuesta
        
        # Determinar si hay menciones relevantes
        respuesta_lower = respuesta.lower()
        sin_menciones = (
            "no se encontraron menciones" in respuesta_lower or
            "no hay menciones" in respuesta_lower or
            "no se encontró información" in respuesta_lower or
            "no conozco" in respuesta_lower
        )
        resultado["menciones_encontradas"] = not sin_menciones
        
        logger.info(f"Claude Noticias: completado, menciones={resultado['menciones_encontradas']}")
        
    except anthropic.APIError as e:
        logger.error(f"Error API Anthropic (Noticias): {e}")
        resultado["error"] = f"Error API: {str(e)}"
        resultado["observaciones"] = "Búsqueda de noticias con IA no disponible temporalmente."
    except Exception as e:
        logger.error(f"Error en búsqueda Noticias/Claude: {e}")
        resultado["error"] = str(e)
        resultado["observaciones"] = f"Error al analizar noticias: {str(e)}"
    
    return resultado


# =============================================================================
# 4. Orquestador de búsquedas Art. 44
# =============================================================================

def ejecutar_busquedas_art44(
    nombre_completo: str,
    nacionalidad: str,
    tipo_documento: str,
    numero_documento: str,
) -> Dict[str, Any]:
    """
    Orquesta las 3 búsquedas Art. 44 C.4 y retorna resultado consolidado.
    
    Ejecuta Wikipedia, Google/Claude y Noticias/Claude.
    Si alguna falla, las otras continúan.
    
    Args:
        nombre_completo: Nombre de la persona
        nacionalidad: Código ISO
        tipo_documento: CI, RUT, PASAPORTE
        numero_documento: Número del documento
    
    Returns:
        Dict con: google, noticias, wikipedia, todas_completadas
    """
    logger.info(f"Ejecutando búsquedas Art. 44 C.4 para: {nombre_completo}")
    
    resultado = {
        "google": None,
        "noticias": None,
        "wikipedia": None,
        "todas_completadas": False,
    }
    
    # 1. Wikipedia (más rápida, sin API key)
    try:
        resultado["wikipedia"] = buscar_wikipedia(nombre_completo, nacionalidad)
    except Exception as e:
        logger.error(f"Error Wikipedia: {e}")
        resultado["wikipedia"] = {
            "realizada": False,
            "encontrado": False,
            "resultados": [],
            "observaciones": f"Error: {str(e)}",
            "error": str(e),
        }
    
    # 2. Google/Claude
    try:
        resultado["google"] = buscar_google_claude(
            nombre_completo, nacionalidad, tipo_documento, numero_documento
        )
    except Exception as e:
        logger.error(f"Error Google/Claude: {e}")
        resultado["google"] = {
            "realizada": False,
            "observaciones": f"Error: {str(e)}",
            "riesgo_sugerido": None,
            "error": str(e),
        }
    
    # 3. Noticias/Claude
    try:
        resultado["noticias"] = buscar_noticias_claude(nombre_completo, nacionalidad)
    except Exception as e:
        logger.error(f"Error Noticias/Claude: {e}")
        resultado["noticias"] = {
            "realizada": False,
            "observaciones": f"Error: {str(e)}",
            "menciones_encontradas": False,
            "error": str(e),
        }
    
    # Verificar si todas se completaron
    resultado["todas_completadas"] = (
        resultado["wikipedia"].get("realizada", False) and
        resultado["google"].get("realizada", False) and
        resultado["noticias"].get("realizada", False)
    )
    
    logger.info(f"Búsquedas Art. 44 completadas: {resultado['todas_completadas']}")

    return resultado


# =============================================================================
# 5. Consulta DGI — Certificado Único (Playwright sync)
# =============================================================================

DGI_CERTIFICADO_URL = (
    "https://servicios.dgi.gub.uy/CVA_Solicitud_Web/servlet/inicio_consulta_comunes"
)
DGI_TIMEOUT_MS = 30_000


def _dgi_find_rut_input(container):
    """Busca heurísticamente el input de RUT/CI en un frame o página GeneXus."""
    candidate_selectors = [
        'input[id*="RUT" i]',
        'input[name*="RUT" i]',
        'input[id*="DOC" i]',
        'input[name*="DOC" i]',
        'input[id*="Numero" i]',
        'input[placeholder*="RUT" i]',
        'input[placeholder*="documento" i]',
        'input[type="text"]',
    ]
    for sel in candidate_selectors:
        try:
            loc = container.locator(sel).first
            if loc.count() > 0:
                return loc
        except Exception:
            continue
    return None


def _dgi_find_submit(container):
    """Busca el botón/enlace de envío del formulario."""
    candidate_selectors = [
        'input[type="submit"]',
        'button[type="submit"]',
        'button:has-text("Consultar")',
        'input[value*="Consultar" i]',
        'a:has-text("Consultar")',
        'button:has-text("Aceptar")',
        'input[value*="Aceptar" i]',
    ]
    for sel in candidate_selectors:
        try:
            loc = container.locator(sel).first
            if loc.count() > 0:
                return loc
        except Exception:
            continue
    return None


def _dgi_interpretar_resultado(texto: str) -> Optional[bool]:
    """Devuelve True si vigente, False si no vigente, None si indeterminado."""
    t = texto.lower()
    if "no vigente" in t or "no está vigente" in t or "no se encuentra vigente" in t:
        return False
    if "vigente" in t or "al día" in t:
        return True
    if "no existe" in t or "no encontrado" in t or "inexistente" in t:
        return False
    return None


def consultar_dgi_certificado(rut_ci: str) -> Dict[str, Any]:
    """
    Consulta el Certificado Único de DGI Uruguay para un RUT o CI.

    Abre el formulario público GeneXus con Playwright (headless), completa
    el campo de documento y extrae el resultado. No integra al flujo ALA
    principal — solo expone la función para pruebas manuales.

    Args:
        rut_ci: RUT o CI a consultar (string)

    Returns:
        Dict con claves: consultado, vigente, resultado_texto, fecha_consulta, error
    """
    fecha_consulta = datetime.utcnow().isoformat()
    resultado: Dict[str, Any] = {
        "consultado": False,
        "vigente": None,
        "resultado_texto": "",
        "fecha_consulta": fecha_consulta,
        "error": None,
    }

    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError as e:
        resultado["error"] = f"Playwright no instalado: {e}"
        return resultado

    rut_limpio = re.sub(r"\s+", "", str(rut_ci or "")).strip()
    if not rut_limpio:
        resultado["error"] = "RUT/CI vacío"
        return resultado

    logger.info(f"Consultando DGI Certificado Único para: {rut_limpio}")

    browser = None
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context()
            page = context.new_page()
            page.set_default_timeout(DGI_TIMEOUT_MS)
            page.set_default_navigation_timeout(DGI_TIMEOUT_MS)

            page.goto(DGI_CERTIFICADO_URL, wait_until="domcontentloaded", timeout=DGI_TIMEOUT_MS)

            try:
                page.wait_for_load_state("networkidle", timeout=DGI_TIMEOUT_MS)
            except Exception:
                pass

            # GeneXus suele cargar el form en el main frame; si no, recorrer iframes.
            containers = [page.main_frame] + [f for f in page.frames if f != page.main_frame]

            rut_input = None
            submit_btn = None
            chosen_container = None
            for c in containers:
                rut_input = _dgi_find_rut_input(c)
                if rut_input is not None:
                    submit_btn = _dgi_find_submit(c)
                    chosen_container = c
                    break

            if rut_input is None:
                resultado["error"] = "No se encontró campo RUT/CI en el formulario DGI"
                return resultado

            rut_input.fill(rut_limpio)

            if submit_btn is not None:
                try:
                    submit_btn.click()
                except Exception as e:
                    logger.warning(f"Click submit falló, intentando Enter: {e}")
                    rut_input.press("Enter")
            else:
                rut_input.press("Enter")

            try:
                page.wait_for_load_state("networkidle", timeout=DGI_TIMEOUT_MS)
            except Exception:
                pass

            body_text = ""
            try:
                if chosen_container is not None:
                    body_text = chosen_container.locator("body").inner_text(timeout=5_000)
            except Exception:
                try:
                    body_text = page.locator("body").inner_text(timeout=5_000)
                except Exception as e:
                    logger.warning(f"No se pudo extraer texto del resultado: {e}")

            body_text_norm = re.sub(r"\s+", " ", body_text or "").strip()
            resultado["resultado_texto"] = body_text_norm[:2000]
            resultado["vigente"] = _dgi_interpretar_resultado(body_text_norm)
            resultado["consultado"] = True

            logger.info(
                f"DGI consulta OK rut={rut_limpio} vigente={resultado['vigente']}"
            )

    except Exception as e:
        logger.error(f"Error consultando DGI Certificado Único: {e}")
        resultado["error"] = str(e)
        resultado["consultado"] = False
    finally:
        try:
            if browser is not None:
                browser.close()
        except Exception:
            pass

    return resultado


# =============================================================================
# 6. Consulta DGR — Interdicciones (Registro Nacional de Actos Personales)
# =============================================================================
#
# INVESTIGACIÓN PORTAL DGR (https://portal.dgr.gub.uy):
# El portal DGR no expone una consulta pública gratuita al Registro Nacional
# de Actos Personales (interdicciones). Los servicios disponibles en el portal
# son todos autenticados o de pago:
#
#   - /servicios1/usuarios/consultas    → página estática informativa, sin form público
#   - SWI/public/consulta_solicitud.jsf → sólo consulta ESTADO de una solicitud
#                                         previamente ingresada (requiere
#                                         nro de cliente + nro de solicitud)
#   - SisUsuariosPub/...loginexterno    → requiere login de usuario DGR
#   - ADE/...actuacionescribanos.login  → requiere login de escribano
#   - "Solicitudes Remotas" (sol-con)   → trámite arancelado con usuario
#
# La consulta al Registro de Actos Personales (interdicciones, inhibiciones,
# emancipaciones, etc.) en Uruguay se realiza presentando una "solicitud de
# información registral" con costo de timbre/tasa, y la respuesta es un
# certificado registral emitido por DGR — no una consulta web instantánea.
#
# Por ende, esta función NO automatiza la consulta: retorna error limpio
# indicando que el servicio requiere autenticación/pago. Se mantiene la
# firma pedida por el tooling ALA para integración futura si DGR habilita
# un endpoint público o si se implementa el flujo autenticado.
# =============================================================================


def consultar_dgr_interdicciones(ci: str) -> Dict[str, Any]:
    """
    Consulta interdicciones en el Registro Nacional de Actos Personales (DGR).

    ⚠️  NO automatizado: el portal DGR no expone consulta pública gratuita.
    La consulta real requiere presentar una solicitud registral arancelada
    con usuario autenticado ("Solicitudes Remotas"). Ver comentario arriba
    para detalle de la investigación del portal.

    Args:
        ci: Cédula de identidad de la persona a consultar.

    Returns:
        Dict con: consultado, tiene_interdicciones, resultado_texto,
        fecha_consulta, error
    """
    fecha_consulta = datetime.utcnow().isoformat()
    ci_limpia = re.sub(r"\s+", "", str(ci or "")).strip()

    logger.info(f"Consulta DGR Interdicciones solicitada para CI={ci_limpia}")

    return {
        "consultado": False,
        "tiene_interdicciones": None,
        "resultado_texto": (
            "El Registro Nacional de Actos Personales (DGR) no ofrece consulta "
            "pública web de interdicciones. La verificación se realiza mediante "
            "solicitud registral arancelada presentada a través del portal "
            "autenticado de DGR (Solicitudes Remotas / Sol-Con)."
        ),
        "fecha_consulta": fecha_consulta,
        "error": "Consulta requiere autenticación/pago",
    }
