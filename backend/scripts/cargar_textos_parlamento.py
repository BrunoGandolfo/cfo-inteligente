#!/usr/bin/env python3
"""
Script para carga masiva de textos completos de leyes históricas desde el Parlamento.

Para leyes (1935-1984) donde IMPO no tiene el texto disponible,
pero el Parlamento sí lo tiene públicamente.

Uso:
    cd /home/brunogandolfo/cfo-inteligente/backend
    source venv/bin/activate
    python scripts/cargar_textos_parlamento.py
"""

import sys
import os
import time
import requests
import logging
import re
from datetime import datetime, timezone
from typing import Optional
from bs4 import BeautifulSoup

# Agregar path del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.ley import Ley

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

PAUSA_ENTRE_REQUESTS = 2  # segundos
CHECKPOINT_CADA = 50  # leyes
TIMEOUT_REQUEST = 30  # segundos
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# ============================================================================
# FUNCIONES DE SCRAPING
# ============================================================================

def encontrar_enlace_temporal(url_ficha: str) -> Optional[str]:
    """
    Busca el enlace al archivo temporal .htm en la página de la ley del Parlamento.
    
    Args:
        url_ficha: URL de la ficha de la ley (ej: https://parlamento.gub.uy/documentosyleyes/leyes/ley/14940)
        
    Returns:
        URL del archivo temporal .htm, o None si no se encuentra
    """
    try:
        headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9',
        }
        
        logger.debug(f"Buscando enlace temporal en: {url_ficha}")
        response = requests.get(url_ficha, headers=headers, timeout=TIMEOUT_REQUEST)
        response.raise_for_status()
        
        # Parsear HTML
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Buscar todos los enlaces <a>
        enlaces = soup.find_all('a', href=True)
        
        for enlace in enlaces:
            href = enlace.get('href', '')
            # Buscar enlace que contenga infolegislativa.parlamento.gub.uy/temporales/
            if 'infolegislativa.parlamento.gub.uy/temporales/' in href:
                # Puede ser relativo o absoluto
                if href.startswith('http'):
                    url_temporal = href
                else:
                    # Construir URL absoluta
                    url_temporal = f"https://{href.lstrip('/')}"
                
                logger.debug(f"Enlace temporal encontrado: {url_temporal}")
                return url_temporal
        
        logger.warning(f"No se encontró enlace temporal en {url_ficha}")
        return None
        
    except requests.RequestException as e:
        logger.error(f"Error descargando ficha de ley ({url_ficha}): {e}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado buscando enlace temporal ({url_ficha}): {e}", exc_info=True)
        return None


def extraer_texto_htm(url_htm: str) -> Optional[str]:
    """
    Descarga y extrae el texto completo de un archivo .htm temporal del Parlamento.
    
    Args:
        url_htm: URL del archivo .htm temporal
        
    Returns:
        Texto completo de la ley, o None si falla
    """
    try:
        headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9',
        }
        
        logger.debug(f"Descargando texto desde: {url_htm}")
        response = requests.get(url_htm, headers=headers, timeout=TIMEOUT_REQUEST)
        response.raise_for_status()
        
        # Parsear HTML
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Buscar el body
        body = soup.find('body')
        if not body:
            logger.warning(f"No se encontró <body> en {url_htm}")
            return None
        
        # Remover scripts, styles, y elementos de navegación
        for tag in body.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            tag.decompose()
        
        # Extraer texto
        texto = body.get_text(separator='\n', strip=True)
        
        # Limpiar líneas vacías múltiples
        lineas = [linea.strip() for linea in texto.split('\n') if linea.strip()]
        texto_limpio = '\n'.join(lineas)
        
        # Validar que el texto tenga un mínimo de caracteres
        if len(texto_limpio) < 100:
            logger.warning(f"Texto muy corto ({len(texto_limpio)} chars) para {url_htm}, posiblemente página de error")
            return None
        
        logger.debug(f"Texto extraído: {len(texto_limpio)} caracteres")
        return texto_limpio
        
    except requests.RequestException as e:
        logger.error(f"Error descargando archivo .htm ({url_htm}): {e}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado extrayendo texto ({url_htm}): {e}", exc_info=True)
        return None


def obtener_texto_parlamento(numero: int) -> Optional[str]:
    """
    Obtiene el texto completo de una ley desde el Parlamento.
    
    Flujo:
    1. Consulta la ficha de la ley
    2. Busca el enlace al archivo temporal .htm
    3. Descarga y extrae el texto del .htm
    
    Args:
        numero: Número de la ley
        
    Returns:
        Texto completo de la ley, o None si falla
    """
    url_ficha = f"https://parlamento.gub.uy/documentosyleyes/leyes/ley/{numero}"
    
    # Paso 1: Buscar enlace temporal
    url_temporal = encontrar_enlace_temporal(url_ficha)
    
    if not url_temporal:
        logger.warning(f"No se encontró enlace temporal para ley {numero}")
        return None
    
    # Paso 2: Descargar y extraer texto del .htm
    texto = extraer_texto_htm(url_temporal)
    
    if texto:
        logger.info(f"Texto obtenido exitosamente para ley {numero}: {len(texto)} caracteres")
    else:
        logger.error(f"No se pudo extraer texto para ley {numero}")
    
    return texto


def cargar_texto_ley_parlamento(db, ley: Ley) -> bool:
    """
    Carga el texto completo de una ley desde el Parlamento y lo guarda en la BD.
    
    Args:
        db: Sesión de base de datos
        ley: Instancia de Ley
        
    Returns:
        True si el texto se cargó exitosamente, False en caso contrario
    """
    if not ley.numero:
        logger.warning(f"Ley sin número (ID: {ley.id})")
        return False
    
    texto = obtener_texto_parlamento(ley.numero)
    
    if texto:
        ley.texto_completo = texto
        ley.tiene_texto = True
        ley.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(ley)
        logger.info(f"✅ Texto cargado y guardado para ley {ley.numero}/{ley.anio} ({len(texto)} caracteres)")
        return True
    else:
        logger.error(f"❌ Fallo al obtener texto del Parlamento para ley {ley.numero}/{ley.anio}")
        return False


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def cargar_textos_parlamento():
    """
    Función principal para cargar textos completos desde el Parlamento.
    Procesa leyes que no tienen texto, ordenadas por año (más antiguas primero).
    """
    db = SessionLocal()
    
    total_exitosas = 0
    total_fallidas = 0
    leyes_procesadas = 0
    
    start_time = time.time()

    try:
        # Contar leyes pendientes
        total_pendientes = db.query(Ley).filter(
            Ley.tiene_texto == False,
            Ley.deleted_at.is_(None)
        ).count()
        
        logger.info(f"📊 Iniciando carga masiva de textos desde Parlamento. {total_pendientes} leyes pendientes.")
        
        # FASE 1: PRUEBA CON 3 LEYES
        logger.info("=" * 60)
        logger.info("FASE 1: PRUEBA CON 3 LEYES")
        logger.info("=" * 60)
        
        leyes_prueba = db.query(Ley).filter(
            Ley.tiene_texto == False,
            Ley.deleted_at.is_(None)
        ).order_by(Ley.anio.asc(), Ley.numero.asc()).limit(3).all()
        
        if not leyes_prueba:
            logger.warning("No hay leyes pendientes para probar")
            return
        
        logger.info(f"Probando con {len(leyes_prueba)} leyes...")
        exitos_prueba = 0
        
        for ley in leyes_prueba:
            logger.info(f"\n--- Probando Ley {ley.numero} ({ley.anio}) ---")
            exito = cargar_texto_ley_parlamento(db, ley)
            if exito:
                exitos_prueba += 1
            time.sleep(PAUSA_ENTRE_REQUESTS)
        
        logger.info(f"\n✅ Prueba completada: {exitos_prueba}/{len(leyes_prueba)} exitosas")
        
        if exitos_prueba == 0:
            logger.error("❌ La prueba falló completamente. Revisar estructura HTML del Parlamento.")
            respuesta = input("¿Continuar de todas formas? (s/n): ")
            if respuesta.lower() != 's':
                logger.info("Proceso cancelado por el usuario")
                return
        
        # FASE 2: CARGA MASIVA
        logger.info("\n" + "=" * 60)
        logger.info("FASE 2: CARGA MASIVA")
        logger.info("=" * 60)
        
        # Procesar leyes en lotes (ordenadas por año, más antiguas primero)
        offset = 0
        limite_consulta = 100
        
        while True:
            leyes_pendientes = db.query(Ley).filter(
                Ley.tiene_texto == False,
                Ley.deleted_at.is_(None)
            ).order_by(Ley.anio.asc(), Ley.numero.asc()).offset(offset).limit(limite_consulta).all()
            
            if not leyes_pendientes:
                break  # No hay más leyes pendientes
            
            for ley in leyes_pendientes:
                leyes_procesadas += 1
                
                try:
                    logger.info(
                        f"Procesando {leyes_procesadas}/{total_pendientes} - "
                        f"Ley {ley.numero} ({ley.anio})..."
                    )
                    
                    exito = cargar_texto_ley_parlamento(db, ley)
                    
                    if exito:
                        total_exitosas += 1
                    else:
                        total_fallidas += 1
                    
                    # Pausa entre requests
                    time.sleep(PAUSA_ENTRE_REQUESTS)
                    
                    # Checkpoint cada N leyes
                    if leyes_procesadas % CHECKPOINT_CADA == 0:
                        logger.info(
                            f"--- CHECKPOINT: {total_exitosas} exitosas, "
                            f"{total_fallidas} fallidas ---"
                        )
                        db.commit()  # Asegurar que los cambios se guarden
                
                except KeyboardInterrupt:
                    logger.warning("Proceso interrumpido por el usuario (Ctrl+C)")
                    raise
                except Exception as e:
                    logger.error(
                        f"Error procesando ley {ley.numero}/{ley.anio} (ID: {ley.id}): {e}",
                        exc_info=True
                    )
                    total_fallidas += 1
                    time.sleep(PAUSA_ENTRE_REQUESTS)  # Mantener pausa incluso en error
                    continue
            
            offset += limite_consulta  # Mover offset para la siguiente página
        
    except KeyboardInterrupt:
        logger.warning("Carga masiva interrumpida por el usuario (Ctrl+C). Guardando progreso...")
    except Exception as e:
        logger.critical(f"Error crítico en la carga masiva: {e}", exc_info=True)
    finally:
        db.close()
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info("\n" + "=" * 60)
        logger.info("RESUMEN DE CARGA MASIVA DE TEXTOS DESDE PARLAMENTO")
        logger.info("=" * 60)
        logger.info(f"Total leyes procesadas: {leyes_procesadas}")
        logger.info(f"Exitosas: {total_exitosas}")
        logger.info(f"Fallidas: {total_fallidas}")
        logger.info(f"Tiempo total: {duration:.2f} segundos")
        if leyes_procesadas > 0:
            logger.info(f"Promedio: {duration/leyes_procesadas:.2f} segundos por ley")
        logger.info("=" * 60)


if __name__ == "__main__":
    cargar_textos_parlamento()

