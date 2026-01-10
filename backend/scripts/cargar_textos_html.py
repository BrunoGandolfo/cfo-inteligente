#!/usr/bin/env python3
"""
Script para carga masiva de textos completos desde IMPO usando scraping HTML.

Para leyes históricas (1935-1984) donde el JSON no está disponible,
pero el HTML sí lo está.

Uso:
    cd /home/brunogandolfo/cfo-inteligente/backend
    source venv/bin/activate
    python scripts/cargar_textos_html.py
"""

import sys
import os
import time
import requests
import logging
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
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# ============================================================================
# FUNCIONES DE SCRAPING
# ============================================================================

def obtener_texto_html_impo(numero: int, anio: int) -> Optional[str]:
    """
    Descarga y parsea el texto completo de una ley desde IMPO HTML.
    
    Args:
        numero: Número de la ley
        anio: Año de la ley
        
    Returns:
        Texto completo concatenado de todos los artículos, o None si falla
    """
    url = f"https://www.impo.com.uy/bases/leyes/{numero}-{anio}"
    
    try:
        logger.info(f"Descargando HTML de IMPO: {url}")
        
        headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9',
        }
        
        response = requests.get(url, headers=headers, timeout=TIMEOUT_REQUEST)
        response.raise_for_status()
        
        # Verificar que sea HTML
        if not response.text.strip().startswith('<'):
            logger.warning(f"Respuesta no es HTML para {url}")
            return None
        
        # Parsear HTML con BeautifulSoup
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Buscar artículos en diferentes estructuras posibles
        textos_articulos = []
        
        # ESTRATEGIA 1: Buscar divs con clase "articulo"
        articulos_divs = soup.find_all('div', class_='articulo')
        if articulos_divs:
            logger.debug(f"Encontrados {len(articulos_divs)} artículos en div.articulo")
            for div in articulos_divs:
                texto = div.get_text(separator='\n', strip=True)
                if texto:
                    textos_articulos.append(texto)
        
        # ESTRATEGIA 2: Buscar elementos con id que contenga "articulo"
        if not textos_articulos:
            articulos_ids = soup.find_all(id=lambda x: x and 'articulo' in x.lower())
            if articulos_ids:
                logger.debug(f"Encontrados {len(articulos_ids)} artículos por ID")
                for elem in articulos_ids:
                    texto = elem.get_text(separator='\n', strip=True)
                    if texto:
                        textos_articulos.append(texto)
        
        # ESTRATEGIA 3: Buscar en la estructura principal del contenido
        if not textos_articulos:
            # Buscar el contenido principal (puede estar en main, article, o div principal)
            contenido_principal = (
                soup.find('main') or 
                soup.find('article') or 
                soup.find('div', class_=lambda x: x and ('content' in x.lower() or 'ley' in x.lower()))
            )
            
            if contenido_principal:
                # Buscar párrafos o divs que parezcan artículos
                parrafos = contenido_principal.find_all(['p', 'div'])
                texto_concatenado = []
                
                for p in parrafos:
                    texto = p.get_text(separator=' ', strip=True)
                    # Filtrar párrafos muy cortos (probablemente navegación)
                    if len(texto) > 50:
                        texto_concatenado.append(texto)
                
                if texto_concatenado:
                    textos_articulos = texto_concatenado
                    logger.debug(f"Extraído texto de {len(texto_concatenado)} párrafos/divs")
        
        # ESTRATEGIA 4: Extraer todo el texto del body si no encontramos estructura específica
        if not textos_articulos:
            body = soup.find('body')
            if body:
                # Remover scripts, styles, nav, header, footer
                for tag in body.find_all(['script', 'style', 'nav', 'header', 'footer']):
                    tag.decompose()
                
                texto_completo = body.get_text(separator='\n', strip=True)
                # Limpiar líneas vacías múltiples
                lineas = [linea.strip() for linea in texto_completo.split('\n') if linea.strip()]
                if lineas:
                    textos_articulos = ['\n'.join(lineas)]
                    logger.debug(f"Extraído texto completo del body ({len(lineas)} líneas)")
        
        if not textos_articulos:
            logger.warning(f"No se encontraron artículos en el HTML de {url}")
            return None
        
        # Concatenar todos los artículos
        texto_completo = "\n\n".join(textos_articulos)
        
        # Validar que el texto tenga un mínimo de caracteres (evitar páginas de error)
        if len(texto_completo) < 100:
            logger.warning(f"Texto muy corto ({len(texto_completo)} chars) para {url}, posiblemente página de error")
            return None
        
        logger.info(f"Texto descargado exitosamente: {len(texto_completo)} caracteres")
        return texto_completo
        
    except requests.RequestException as e:
        logger.error(f"Error descargando HTML de IMPO ({url}): {e}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado parseando HTML de IMPO ({url}): {e}", exc_info=True)
        return None


def probar_estructura_html(numero: int, anio: int) -> bool:
    """
    Prueba la estructura HTML de una ley para inspeccionar el formato.
    
    Args:
        numero: Número de la ley
        anio: Año de la ley
        
    Returns:
        True si se pudo extraer texto, False en caso contrario
    """
    logger.info(f"🔍 Probando estructura HTML para Ley {numero} ({anio})...")
    
    texto = obtener_texto_html_impo(numero, anio)
    
    if texto:
        logger.info(f"✅ Éxito: {len(texto)} caracteres extraídos")
        logger.info(f"📄 Primeros 500 caracteres:\n{texto[:500]}...")
        return True
    else:
        logger.error(f"❌ No se pudo extraer texto")
        return False


def cargar_texto_ley_html(db, ley: Ley) -> bool:
    """
    Carga el texto completo de una ley desde IMPO HTML y lo guarda en la BD.
    
    Args:
        db: Sesión de base de datos
        ley: Instancia de Ley
        
    Returns:
        True si el texto se cargó exitosamente, False en caso contrario
    """
    if not ley.url_impo:
        logger.warning(f"Ley {ley.numero}/{ley.anio} no tiene URL de IMPO")
        return False
    
    # Extraer número y año de la URL o usar los campos del modelo
    texto = obtener_texto_html_impo(ley.numero, ley.anio)
    
    if texto:
        ley.texto_completo = texto
        ley.tiene_texto = True
        ley.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(ley)
        logger.info(f"✅ Texto cargado y guardado para ley {ley.numero}/{ley.anio} ({len(texto)} caracteres)")
        return True
    else:
        logger.error(f"❌ Fallo al obtener texto HTML para ley {ley.numero}/{ley.anio}")
        return False


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def cargar_textos_html():
    """
    Función principal para cargar textos completos desde IMPO HTML.
    Procesa leyes que no tienen texto y tienen una URL de IMPO.
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
            Ley.url_impo.isnot(None),
            Ley.deleted_at.is_(None)
        ).count()
        
        logger.info(f"📊 Iniciando carga masiva de textos HTML. {total_pendientes} leyes pendientes.")
        
        # PRUEBA INICIAL: Probar con una ley para verificar estructura
        logger.info("=" * 60)
        logger.info("FASE 1: PRUEBA DE ESTRUCTURA HTML")
        logger.info("=" * 60)
        
        ley_prueba = db.query(Ley).filter(
            Ley.tiene_texto == False,
            Ley.url_impo.isnot(None),
            Ley.deleted_at.is_(None)
        ).first()
        
        if ley_prueba:
            logger.info(f"Probando con Ley {ley_prueba.numero} ({ley_prueba.anio})...")
            exito_prueba = probar_estructura_html(ley_prueba.numero, ley_prueba.anio)
            
            if not exito_prueba:
                logger.error("❌ La prueba falló. Revisar estructura HTML de IMPO.")
                respuesta = input("¿Continuar de todas formas? (s/n): ")
                if respuesta.lower() != 's':
                    logger.info("Proceso cancelado por el usuario")
                    return
        else:
            logger.warning("No hay leyes pendientes para probar")
            return
        
        logger.info("=" * 60)
        logger.info("FASE 2: CARGA MASIVA")
        logger.info("=" * 60)
        
        # Procesar leyes en lotes
        offset = 0
        limite_consulta = 100
        
        while True:
            leyes_pendientes = db.query(Ley).filter(
                Ley.tiene_texto == False,
                Ley.url_impo.isnot(None),
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
                    
                    exito = cargar_texto_ley_html(db, ley)
                    
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
        
        logger.info("=" * 60)
        logger.info("RESUMEN DE CARGA MASIVA DE TEXTOS HTML")
        logger.info("=" * 60)
        logger.info(f"Total leyes procesadas: {leyes_procesadas}")
        logger.info(f"Exitosas: {total_exitosas}")
        logger.info(f"Fallidas: {total_fallidas}")
        logger.info(f"Tiempo total: {duration:.2f} segundos")
        if leyes_procesadas > 0:
            logger.info(f"Promedio: {duration/leyes_procesadas:.2f} segundos por ley")
        logger.info("=" * 60)


if __name__ == "__main__":
    cargar_textos_html()

