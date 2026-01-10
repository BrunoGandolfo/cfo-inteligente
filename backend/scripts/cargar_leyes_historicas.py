#!/usr/bin/env python3
"""
Script para cargar leyes históricas (1935-1985) desde el endpoint JSON del Parlamento.

Procesa todas las leyes del período histórico que faltan en la base de datos.
Incluye paginación automática y rate limiting para no saturar el servidor.

Uso:
    cd /home/brunogandolfo/cfo-inteligente/backend
    source venv/bin/activate
    python scripts/cargar_leyes_historicas.py
"""

import sys
import os
import time
import json
import requests
from datetime import datetime, date

# Agregar path del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.ley import Ley
from app.schemas.ley import LeyCreate
from app.services.ley_service import crear_ley, obtener_ley_por_numero_anio

# Configuración
API_BASE_URL = "https://parlamento.gub.uy/documentosyleyes/leyes/json"
FECHA_DESDE = "1935-09-13"
FECHA_HASTA = "1985-03-01"
RATE_LIMIT = 0.3  # segundos entre páginas
TIMEOUT = 30  # segundos


def parsear_fecha_promulgacion(fecha_str: str) -> tuple:
    """
    Parsea fecha en formato dd-mm-yyyy o dd/mm/yyyy.
    
    Retorna (date, año) o (None, None)
    
    Args:
        fecha_str: String con fecha (ej: "13/09/1935" o "13-09-1935")
        
    Returns:
        Tuple (date object, año) o (None, None) si falla
    """
    if not fecha_str:
        return None, None
    
    try:
        # Normalizar separador
        fecha_str = fecha_str.replace('-', '/')
        partes = fecha_str.split('/')
        if len(partes) == 3:
            dia, mes, anio = int(partes[0]), int(partes[1]), int(partes[2])
            fecha = date(anio, mes, dia)
            return fecha, anio
    except (ValueError, IndexError) as e:
        print(f"  ⚠️  Error parseando fecha '{fecha_str}': {e}")
    
    return None, None


def parsear_entero(valor: str | int | None, default: int = 0) -> int:
    """Parsea string a entero con valor por defecto."""
    if valor is None:
        return default
    if isinstance(valor, int):
        return valor
    if isinstance(valor, str):
        valor = valor.strip()
        if not valor or valor == "":
            return default
        try:
            return int(valor)
        except ValueError:
            return default
    return default


def parsear_url(url_str: str | None) -> str | None:
    """Limpia y valida URL."""
    if not url_str or not isinstance(url_str, str):
        return None
    
    url_limpia = url_str.strip()
    if url_limpia == "":
        return None
    
    # Validar que sea una URL válida
    if url_limpia.startswith("http://") or url_limpia.startswith("https://"):
        return url_limpia
    
    return None


def descargar_pagina(page: int) -> list[dict] | None:
    """
    Descarga una página del endpoint JSON del Parlamento.
    
    Args:
        page: Número de página (0-indexed)
        
    Returns:
        Lista de leyes (dicts) o None si falla
    """
    try:
        params = {
            "Fechadesde": FECHA_DESDE,
            "Fechahasta": FECHA_HASTA,
            "Ltemas": "",
            "Ly_Nro": "",
            "Searchtext": "",
            "Tipobusqueda": "T",
            "_format": "json",
            "page": page
        }
        
        response = requests.get(API_BASE_URL, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        # El endpoint devuelve un array de objetos
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "results" in data:
            return data["results"]
        else:
            return []
            
    except requests.RequestException as e:
        print(f"❌ Error descargando página {page}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error parseando JSON página {page}: {e}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado página {page}: {e}")
        return None


def procesar_ley(db, ley_data: dict, contador: int) -> tuple[bool, bool]:
    """
    Procesa una ley individual: parsea datos y hace upsert.
    
    Returns:
        Tuple (exito, es_nueva)
    """
    try:
        # Extraer y validar número de ley
        numero = parsear_entero(ley_data.get("Numero_de_Ley"))
        if numero <= 0:
            return False, False
        
        # Parsear fecha y extraer año
        fecha_prom_str = ley_data.get("Promulgacion", "")
        fecha_promulgacion, anio = parsear_fecha_promulgacion(fecha_prom_str)
        
        # Validar año
        if anio is None or anio < 1935 or anio > 1985:
            return False, False
        
        # Extraer título (obligatorio)
        titulo = ley_data.get("Titulo", "").strip()
        if not titulo:
            titulo = f"Ley {numero}"  # Fallback para leyes sin título
        
        # Extraer URLs
        url_impo = parsear_url(ley_data.get("Texto_Actualizado"))
        url_parlamento = parsear_url(ley_data.get("Texto_Original"))
        
        # Extraer contadores de referencias
        leyes_referenciadas = parsear_entero(ley_data.get("Leyes_Referenciadas"))
        leyes_que_referencia = parsear_entero(ley_data.get("Leyes_que_referencia"))
        
        # Verificar si ya existe
        ley_existente = obtener_ley_por_numero_anio(db, numero, anio)
        es_nueva = ley_existente is None
        
        # Crear schema
        ley_create = LeyCreate(
            numero=numero,
            anio=anio,
            titulo=titulo,
            fecha_promulgacion=fecha_promulgacion,
            url_parlamento=url_parlamento,
            url_impo=url_impo,
            leyes_referenciadas=leyes_referenciadas,
            leyes_que_referencia=leyes_que_referencia
        )
        
        # Crear o actualizar (la función crear_ley hace upsert)
        crear_ley(db, ley_create)
        
        return True, es_nueva
        
    except Exception as e:
        print(f"  ⚠️  Error procesando ley: {e}")
        db.rollback()
        return False, False


def main():
    """Función principal del script."""
    print("=" * 70)
    print("CARGA DE LEYES HISTÓRICAS (1935-1985)")
    print("=" * 70)
    print()
    print(f"📅 Período: {FECHA_DESDE} a {FECHA_HASTA}")
    print(f"🌐 Endpoint: {API_BASE_URL}")
    print(f"⏱️  Rate limit: {RATE_LIMIT}s entre páginas")
    print()
    
    respuesta = input("¿Continuar? (s/n): ").strip().lower()
    if respuesta != 's':
        print("❌ Cancelado por el usuario")
        return
    
    print()
    print("🚀 Iniciando carga...")
    print()
    
    db = SessionLocal()
    
    try:
        estadisticas = {
            "nuevas": 0,
            "actualizadas": 0,
            "errores": 0,
            "total_procesadas": 0,
            "inicio": datetime.now()
        }
        
        page = 0
        contador_leyes = 0
        
        while True:
            # Descargar página
            print(f"📄 Descargando página {page}...", end=" ", flush=True)
            leyes_pagina = descargar_pagina(page)
            
            if leyes_pagina is None:
                print("❌ Error, saltando página")
                estadisticas["errores"] += 1
                page += 1
                time.sleep(RATE_LIMIT)
                continue
            
            if len(leyes_pagina) == 0:
                print("✅ Fin de páginas")
                break
            
            print(f"✅ {len(leyes_pagina)} leyes encontradas")
            
            # Procesar cada ley de la página
            for ley_data in leyes_pagina:
                contador_leyes += 1
                estadisticas["total_procesadas"] += 1
                
                exito, es_nueva = procesar_ley(db, ley_data, contador_leyes)
                
                if exito:
                    if es_nueva:
                        estadisticas["nuevas"] += 1
                    else:
                        estadisticas["actualizadas"] += 1
                else:
                    estadisticas["errores"] += 1
                
                # Log cada 100 leyes
                if contador_leyes % 100 == 0:
                    print()
                    print(f"📊 Progreso: {contador_leyes} leyes procesadas "
                          f"({estadisticas['nuevas']} nuevas, "
                          f"{estadisticas['actualizadas']} actualizadas, "
                          f"{estadisticas['errores']} errores)")
                    print()
            
            # Rate limiting entre páginas
            page += 1
            if leyes_pagina:  # Solo pausar si hubo resultados
                time.sleep(RATE_LIMIT)
        
        # Commit final
        db.commit()
        
        # Calcular tiempo transcurrido
        tiempo_transcurrido = datetime.now() - estadisticas["inicio"]
        horas = tiempo_transcurrido.seconds // 3600
        minutos = (tiempo_transcurrido.seconds % 3600) // 60
        segundos = tiempo_transcurrido.seconds % 60
        
        # Resumen final
        print()
        print("=" * 70)
        print("✅ CARGA COMPLETADA")
        print("=" * 70)
        print(f"Total procesadas: {estadisticas['total_procesadas']}")
        print(f"✅ Nuevas: {estadisticas['nuevas']}")
        print(f"🔄 Actualizadas: {estadisticas['actualizadas']}")
        print(f"❌ Errores: {estadisticas['errores']}")
        print(f"⏱️  Tiempo: {horas}h {minutos}m {segundos}s")
        print()
        
    except KeyboardInterrupt:
        print()
        print()
        print("⚠️  Interrumpido por el usuario")
        print(f"Progreso guardado: {estadisticas.get('total_procesadas', 0)} leyes procesadas")
        print(f"✅ Nuevas: {estadisticas.get('nuevas', 0)}")
        print(f"🔄 Actualizadas: {estadisticas.get('actualizadas', 0)}")
        print(f"❌ Errores: {estadisticas.get('errores', 0)}")
        db.commit()
    except Exception as e:
        print()
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()

