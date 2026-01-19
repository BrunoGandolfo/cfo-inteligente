#!/usr/bin/env python3
"""
Script para generar resúmenes de leyes usando Ollama local.

Reemplaza el uso de DeepSeek API por inferencia local con Ollama.
Ventajas: sin rate limiting, sin costos, más rápido con GPU local.

Uso:
    cd /home/brunogandolfo/cfo-inteligente/backend
    python scripts/generar_resumenes_ollama.py
    
    # Con parámetros opcionales:
    python scripts/generar_resumenes_ollama.py --modelo qwen2.5-128k:latest --batch-size 50
"""

import sys
import time
import json
import logging
import requests
import re
import argparse
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# Configuración
DATABASE_URL = "postgresql://postgres:NLlXASvwKuOHCUsDpdUWcojpPDUDLmzx@shortline.proxy.rlwy.net:50827/railway"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:32b"  # Modelo por defecto
OLLAMA_TIMEOUT = 300  # 5 minutos (modelo local puede tardar)

BATCH_SIZE = 50  # Commit cada N leyes
PAUSE_SECONDS = 0.5  # Pausa mínima entre leyes (menor que DeepSeek)
TIMEOUT_IMPO = 30

LOG_FILE = f"resumenes_ollama_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
ERROR_FILE = f"resumenes_ollama_errores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
CHECKPOINT_FILE = f"resumenes_ollama_checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

PROMPT_OPTIMIZADO = """Eres un abogado uruguayo senior especializado en análisis legislativo. Tu tarea es generar un resumen estructurado de la Ley {numero}/{anio} de Uruguay para uso profesional.

INSTRUCCIONES:
- Extrae SOLO información que esté explícitamente en el texto
- NO inventes ni supongas información que no aparezca
- Si una sección no tiene información relevante, indica "No especificado"
- Usa lenguaje técnico-jurídico preciso

ESTRUCTURA REQUERIDA:

## 1. IDENTIFICACION
- Ley: {numero}/{anio}
- Materia principal: (laboral, tributario, societario, procesal, civil, penal, administrativo, etc.)

## 2. OBJETO Y ALCANCE
- Que regula? (maximo 2 oraciones)
- A quienes aplica?

## 3. REGIMEN JURIDICO PRINCIPAL
- Las 3-5 disposiciones mas importantes (indicar articulos)

## 4. DERECHOS Y OBLIGACIONES
- Que derechos otorga y a quien?
- Que obligaciones impone y a quien?

## 5. SANCIONES
- Que consecuencias preve por incumplimiento?

## 6. APLICACION PRACTICA
- Cuando debe un profesional consultar esta ley? (maximo 3 casos)

EXTENSION: 300-500 palabras.

TEXTO DE LA LEY:
{texto}"""


def sanitizar_texto(texto):
    """Limpia texto para evitar caracteres problemáticos."""
    if not texto:
        return ""
    # Eliminar caracteres de control
    texto = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', texto)
    texto = texto.replace('\r', ' ').replace('\t', ' ')
    # Limitar longitud del texto para evitar prompts muy largos
    # Ollama puede manejar contexto largo, pero limitamos a ~50k caracteres
    if len(texto) > 50000:
        texto = texto[:50000] + "\n\n[... texto truncado por longitud ...]"
    return texto


def sanitizar_json(texto):
    """Limpia JSON antes de parsear."""
    if not texto:
        return ""
    texto = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', texto)
    texto = texto.replace('\r', ' ').replace('\t', ' ')
    return texto


def obtener_conexion():
    """Crea nueva conexión a BD."""
    return psycopg2.connect(DATABASE_URL)


def verificar_conexion(conn):
    """Verifica si la conexión está viva, reconecta si es necesario."""
    try:
        if conn is None or conn.closed:
            logger.info("Reconectando a BD...")
            return obtener_conexion()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        return conn
    except Exception:
        logger.info("Conexión perdida, reconectando...")
        try:
            conn.close()
        except:
            pass
        return obtener_conexion()


def verificar_ollama():
    """Verifica que Ollama esté disponible."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        response.raise_for_status()
        models = response.json().get('models', [])
        model_names = [m.get('name', '') for m in models]
        return True, model_names
    except Exception as e:
        logger.error(f"Error verificando Ollama: {e}")
        return False, []


def obtener_texto_impo(url_impo):
    """
    Descarga texto completo de la ley desde IMPO.
    
    Args:
        url_impo: URL de la ley en IMPO
        
    Returns:
        Texto completo de la ley o None si falla
    """
    if not url_impo:
        return None
    try:
        url_json = f"{url_impo}?json=true"
        response = requests.get(url_json, timeout=TIMEOUT_IMPO)
        response.raise_for_status()
        contenido = response.text.strip()
        
        # Si retorna HTML, no es JSON válido
        if contenido.startswith('<!DOCTYPE') or contenido.startswith('<html'):
            return None
        
        contenido_limpio = sanitizar_json(contenido)
        data = json.loads(contenido_limpio)
        articulos = data.get('articulos', [])
        
        if not articulos:
            return None
        
        textos = []
        for art in articulos:
            texto_art = art.get('textoArticulo', '')
            if texto_art:
                textos.append(texto_art)
        
        return '\n\n'.join(textos) if textos else None
        
    except Exception as e:
        logger.warning(f"Error IMPO: {e}")
        return None


def generar_resumen_ollama(numero, anio, texto, modelo=OLLAMA_MODEL):
    """
    Genera resumen usando Ollama local.
    
    Args:
        numero: Número de ley
        anio: Año de ley
        texto: Texto completo de la ley
        modelo: Modelo de Ollama a usar
        
    Returns:
        Tuple (resumen, tokens_usados) o (None, 0) si falla
    """
    prompt = PROMPT_OPTIMIZADO.format(numero=numero, anio=anio, texto=texto)
    
    payload = {
        "model": modelo,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,  # Baja temperatura para consistencia
            "num_predict": 1000,  # Máximo tokens de respuesta
            "top_p": 0.9,
            "repeat_penalty": 1.1
        }
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=OLLAMA_TIMEOUT,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        data = response.json()
        resumen = data.get('response', '').strip()
        
        # Ollama no siempre retorna usage, estimamos tokens
        elapsed = time.time() - start_time
        tokens_estimados = len(resumen.split()) * 1.3  # Estimación aproximada
        
        if not resumen:
            logger.warning("Ollama retornó respuesta vacía")
            return None, 0
        
        return resumen, int(tokens_estimados)
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout esperando respuesta de Ollama (>{OLLAMA_TIMEOUT}s)")
        return None, 0
    except requests.exceptions.ConnectionError:
        logger.error("Error de conexión con Ollama. ¿Está corriendo?")
        return None, 0
    except Exception as e:
        logger.error(f"Error Ollama: {e}")
        return None, 0


def guardar_resumen(conn, ley_id, resumen):
    """Guarda resumen en BD con reconexión automática."""
    try:
        conn = verificar_conexion(conn)
        with conn.cursor() as cur:
            # Intentar actualizar resumen (puede no existir el campo resumen_generado_at)
            try:
                cur.execute(
                    "UPDATE leyes SET resumen = %s, resumen_generado_at = NOW(), updated_at = NOW() WHERE id = %s",
                    (resumen, ley_id)
                )
            except psycopg2.errors.UndefinedColumn:
                # Si no existe resumen_generado_at, solo actualizar resumen
                cur.execute(
                    "UPDATE leyes SET resumen = %s, updated_at = NOW() WHERE id = %s",
                    (resumen, ley_id)
                )
        conn.commit()
        return True, conn
    except Exception as e:
        logger.error(f"Error BD: {e}")
        try:
            conn.rollback()
        except:
            pass
        try:
            conn = obtener_conexion()
        except:
            pass
        return False, conn


def guardar_checkpoint(ley_id, numero, anio):
    """Guarda checkpoint para poder continuar si se interrumpe."""
    try:
        with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
            f.write(f"{ley_id}|{numero}|{anio}\n")
    except Exception as e:
        logger.warning(f"Error guardando checkpoint: {e}")


def cargar_checkpoint():
    """Carga último checkpoint si existe."""
    try:
        # Buscar archivo de checkpoint más reciente
        import glob
        checkpoints = glob.glob("resumenes_ollama_checkpoint_*.txt")
        if not checkpoints:
            return None
        
        latest = max(checkpoints, key=lambda x: os.path.getmtime(x))
        with open(latest, 'r', encoding='utf-8') as f:
            line = f.readline().strip()
            if line:
                parts = line.split('|')
                if len(parts) >= 3:
                    return parts[0]  # Retornar ley_id
        return None
    except Exception as e:
        logger.warning(f"Error cargando checkpoint: {e}")
        return None


def registrar_error(ley_id, numero, anio, error):
    """Registra error en archivo."""
    try:
        with open(ERROR_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().isoformat()} | {ley_id} | Ley {numero}/{anio} | {error}\n")
    except Exception as e:
        logger.warning(f"Error registrando error: {e}")


def procesar_leyes(modelo, batch_size, desde_id=None):
    """
    Procesa leyes sin resumen usando Ollama.
    
    Args:
        modelo: Modelo de Ollama a usar
        batch_size: Tamaño de batch para commits
        desde_id: ID de ley desde donde continuar (checkpoint)
    """
    logger.info("=" * 60)
    logger.info("INICIO: Generación de resúmenes con Ollama Local")
    logger.info("=" * 60)
    logger.info(f"Modelo: {modelo}")
    logger.info(f"Ollama URL: {OLLAMA_URL}")
    logger.info(f"Batch size: {batch_size}")
    logger.info("")
    
    # Verificar Ollama
    ollama_ok, modelos_disponibles = verificar_ollama()
    if not ollama_ok:
        logger.error("❌ Ollama no está disponible. Verificar que esté corriendo.")
        logger.error("   Ejecutar: ollama serve")
        return
    
    logger.info(f"✅ Ollama disponible. Modelos instalados: {len(modelos_disponibles)}")
    
    # Verificar que el modelo solicitado esté disponible
    if modelo not in modelos_disponibles:
        logger.warning(f"⚠️  Modelo '{modelo}' no encontrado en Ollama.")
        logger.info(f"Modelos disponibles: {', '.join(modelos_disponibles[:5])}...")
        respuesta = input(f"¿Continuar con '{modelo}' de todas formas? (s/n): ")
        if respuesta.lower() != 's':
            logger.info("Cancelado.")
            return
    
    # Conectar a BD
    try:
        conn = obtener_conexion()
        logger.info("✅ Conexión a BD establecida")
    except Exception as e:
        logger.error(f"❌ Error conectando a BD: {e}")
        return
    
    # Obtener leyes pendientes
    try:
        query = """
            SELECT id, numero, anio, titulo, url_impo
            FROM leyes
            WHERE resumen IS NULL 
            AND deleted_at IS NULL 
            AND url_impo IS NOT NULL
        """
        
        # Si hay checkpoint, continuar desde ahí
        if desde_id:
            query += " AND id::text >= %s"
            params = (desde_id,)
        else:
            params = None
        
        query += " ORDER BY anio DESC, numero DESC"
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)
            leyes = cur.fetchall()
    except Exception as e:
        logger.error(f"❌ Error obteniendo leyes: {e}")
        conn.close()
        return
    
    total = len(leyes)
    logger.info(f"📊 Total de leyes a procesar: {total}")
    
    if total == 0:
        logger.info("✅ No hay leyes pendientes")
        conn.close()
        return
    
    # Estadísticas
    stats = {
        'procesadas': 0,
        'exitosas': 0,
        'sin_texto': 0,
        'errores_ollama': 0,
        'errores_bd': 0,
        'tokens_total': 0,
        'tiempo_total': 0,
        'inicio': datetime.now()
    }
    
    logger.info("")
    logger.info("🚀 Iniciando procesamiento...")
    logger.info("")
    
    try:
        for i, ley in enumerate(leyes, 1):
            ley_id = str(ley['id'])
            numero = ley['numero']
            anio = ley['anio']
            url_impo = ley.get('url_impo')
            
            try:
                # Descargar texto desde IMPO
                texto = obtener_texto_impo(url_impo)
                
                if not texto or not texto.strip():
                    stats['sin_texto'] += 1
                    registrar_error(ley_id, numero, anio, "Sin texto en IMPO")
                    logger.warning(f"[{i}/{total}] Ley {numero}/{anio} - Sin texto en IMPO")
                    stats['procesadas'] += 1
                    continue
                
                # Generar resumen con Ollama
                inicio_ley = time.time()
                resumen, tokens = generar_resumen_ollama(numero, anio, texto, modelo)
                tiempo_ley = time.time() - inicio_ley
                stats['tiempo_total'] += tiempo_ley
                
                if not resumen:
                    stats['errores_ollama'] += 1
                    registrar_error(ley_id, numero, anio, "Error en Ollama")
                    logger.error(f"[{i}/{total}] Ley {numero}/{anio} - Error Ollama")
                    stats['procesadas'] += 1
                    continue
                
                # Guardar en BD
                exito, conn = guardar_resumen(conn, ley_id, resumen)
                if exito:
                    stats['exitosas'] += 1
                    stats['tokens_total'] += tokens
                    logger.info(
                        f"[{i}/{total}] Ley {numero}/{anio} - OK "
                        f"({tokens:.0f} tokens, {tiempo_ley:.1f}s)"
                    )
                    # Guardar checkpoint
                    guardar_checkpoint(ley_id, numero, anio)
                else:
                    stats['errores_bd'] += 1
                    registrar_error(ley_id, numero, anio, "Error guardando en BD")
                    logger.error(f"[{i}/{total}] Ley {numero}/{anio} - Error BD")
                
                stats['procesadas'] += 1
                
            except KeyboardInterrupt:
                logger.info("")
                logger.warning("⚠️  Interrumpido por el usuario")
                logger.info(f"Progreso guardado: {stats['procesadas']}/{total}")
                guardar_checkpoint(ley_id, numero, anio)
                break
            except Exception as e:
                stats['errores_ollama'] += 1
                stats['procesadas'] += 1
                registrar_error(ley_id, numero, anio, str(e))
                logger.error(f"[{i}/{total}] Ley {numero}/{anio} - Error: {e}")
            
            # Checkpoint cada batch_size
            if i % batch_size == 0:
                elapsed = (datetime.now() - stats['inicio']).total_seconds()
                rate = stats['exitosas'] / elapsed * 60 if elapsed > 0 else 0  # leyes/minuto
                tiempo_promedio = stats['tiempo_total'] / stats['exitosas'] if stats['exitosas'] > 0 else 0
                tiempo_restante = (total - i) * tiempo_promedio / 60  # minutos
                
                logger.info("-" * 60)
                logger.info(f"📊 CHECKPOINT {i}/{total}")
                logger.info(f"✅ Exitosas: {stats['exitosas']} | ❌ Errores: {stats['errores_ollama'] + stats['errores_bd']}")
                logger.info(f"📝 Tokens: {stats['tokens_total']:.0f} | ⏱️  Tiempo promedio: {tiempo_promedio:.1f}s/ley")
                logger.info(f"🚀 Velocidad: {rate:.1f} leyes/minuto | ⏳ Tiempo restante: {tiempo_restante:.0f} min")
                logger.info(f"📄 Sin texto: {stats['sin_texto']}")
                logger.info("-" * 60)
                
                # Renovar conexión preventivamente
                conn = verificar_conexion(conn)
            
            # Pausa mínima entre leyes
            if i < total:  # No pausar después de la última
                time.sleep(PAUSE_SECONDS)
        
        # Resumen final
        elapsed = (datetime.now() - stats['inicio']).total_seconds()
        rate_final = stats['exitosas'] / elapsed * 60 if elapsed > 0 else 0
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ RESUMEN FINAL")
        logger.info("=" * 60)
        logger.info(f"📊 Procesadas: {stats['procesadas']}")
        logger.info(f"✅ Exitosas: {stats['exitosas']}")
        logger.info(f"📄 Sin texto: {stats['sin_texto']}")
        logger.info(f"❌ Errores Ollama: {stats['errores_ollama']}")
        logger.info(f"❌ Errores BD: {stats['errores_bd']}")
        logger.info(f"📝 Tokens totales: {stats['tokens_total']:.0f}")
        logger.info(f"⏱️  Tiempo total: {elapsed/3600:.1f} horas")
        logger.info(f"🚀 Velocidad promedio: {rate_final:.1f} leyes/minuto")
        logger.info(f"📁 Log: {LOG_FILE}")
        logger.info(f"📁 Errores: {ERROR_FILE}")
        logger.info("=" * 60)
        
    finally:
        conn.close()


def main():
    """Función principal con argumentos."""
    parser = argparse.ArgumentParser(
        description="Generar resúmenes de leyes usando Ollama local"
    )
    parser.add_argument(
        '--modelo',
        default=OLLAMA_MODEL,
        help=f'Modelo de Ollama a usar (default: {OLLAMA_MODEL})'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=BATCH_SIZE,
        help=f'Tamaño de batch para commits (default: {BATCH_SIZE})'
    )
    parser.add_argument(
        '--desde-id',
        help='ID de ley desde donde continuar (checkpoint)'
    )
    parser.add_argument(
        '--continuar',
        action='store_true',
        help='Continuar desde último checkpoint automáticamente'
    )
    
    args = parser.parse_args()
    
    # Cargar checkpoint si se solicita
    desde_id = args.desde_id
    if args.continuar and not desde_id:
        desde_id = cargar_checkpoint()
        if desde_id:
            logger.info(f"📌 Continuando desde checkpoint: {desde_id}")
    
    # Confirmación
    print("=" * 60)
    print("GENERADOR DE RESUMENES - Ollama Local")
    print("=" * 60)
    print(f"Modelo: {args.modelo}")
    print(f"Batch size: {args.batch_size}")
    if desde_id:
        print(f"Continuando desde: {desde_id}")
    print("")
    print("⚠️  Este proceso puede tardar varias horas.")
    print("⚠️  Se puede interrumpir con Ctrl+C y continuar después.")
    print("")
    
    confirmacion = input("¿Iniciar? (SI para confirmar): ")
    if confirmacion.strip().upper() == 'SI':
        procesar_leyes(args.modelo, args.batch_size, desde_id)
    else:
        print("❌ Cancelado.")


if __name__ == "__main__":
    import os
    main()
