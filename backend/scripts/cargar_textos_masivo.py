#!/usr/bin/env python3
"""
Script para carga masiva de textos completos desde IMPO.

Procesa todas las leyes que no tienen texto completo (tiene_texto=False).
Incluye pausas para no saturar IMPO y checkpoint cada 100 leyes.

Uso:
    cd /home/brunogandolfo/cfo-inteligente/backend
    source venv/bin/activate
    python scripts/cargar_textos_masivo.py
"""

import sys
import os
import time
import json
import requests
from datetime import datetime

# Agregar path del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.ley import Ley
from app.services.ley_service import obtener_texto_impo

# Configuración
PAUSA_ENTRE_REQUESTS = 1  # segundos
PAUSA_CADA_LOTE = 10  # segundos
TAMANO_LOTE = 50  # leyes
CHECKPOINT_CADA = 100  # leyes
TIMEOUT_REQUEST = 30  # segundos


def procesar_ley(db, ley, contador, total):
    """
    Procesa una ley individual: descarga texto de IMPO y guarda.
    
    Returns:
        True si exitoso, False si falló
    """
    try:
        print(f"Procesando {contador}/{total} - Ley {ley.numero} ({ley.anio})...", end=" ", flush=True)
        
        # Verificar que tenga URL de IMPO
        if not ley.url_impo:
            print("❌ Sin URL de IMPO")
            return False
        
        # Obtener texto de IMPO
        texto_completo = obtener_texto_impo(ley.url_impo)
        
        if texto_completo is None:
            print("❌ No se pudo obtener texto")
            return False
        
        # Actualizar ley
        ley.texto_completo = texto_completo
        ley.tiene_texto = True
        
        db.commit()
        db.refresh(ley)
        
        print(f"✅ Cargado ({len(texto_completo)} caracteres)")
        return True
        
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {str(e)[:50]}")
        db.rollback()
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error parseando JSON: {str(e)[:50]}")
        db.rollback()
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)[:50]}")
        db.rollback()
        return False


def main():
    """Función principal del script."""
    print("=" * 70)
    print("CARGA MASIVA DE TEXTOS DESDE IMPO")
    print("=" * 70)
    print()
    
    db = SessionLocal()
    
    try:
        # Contar leyes sin texto
        total_sin_texto = db.query(Ley).filter(
            Ley.tiene_texto == False,
            Ley.deleted_at.is_(None),
            Ley.url_impo.isnot(None)
        ).count()
        
        if total_sin_texto == 0:
            print("✅ No hay leyes pendientes de cargar texto.")
            return
        
        print(f"📊 Total de leyes sin texto: {total_sin_texto}")
        print(f"⏱️  Pausa entre requests: {PAUSA_ENTRE_REQUESTS}s")
        print(f"⏸️  Pausa cada {TAMANO_LOTE} leyes: {PAUSA_CADA_LOTE}s")
        print(f"💾 Checkpoint cada {CHECKPOINT_CADA} leyes")
        print()
        
        respuesta = input("¿Continuar? (s/n): ").strip().lower()
        if respuesta != 's':
            print("❌ Cancelado por el usuario")
            return
        
        print()
        print("🚀 Iniciando carga...")
        print()
        
        # Obtener todas las leyes sin texto
        leyes = db.query(Ley).filter(
            Ley.tiene_texto == False,
            Ley.deleted_at.is_(None),
            Ley.url_impo.isnot(None)
        ).order_by(Ley.anio.desc(), Ley.numero.desc()).all()
        
        estadisticas = {
            "exitosas": 0,
            "fallidas": 0,
            "inicio": datetime.now()
        }
        
        contador = 0
        
        for ley in leyes:
            contador += 1
            
            # Procesar ley
            exito = procesar_ley(db, ley, contador, total_sin_texto)
            
            if exito:
                estadisticas["exitosas"] += 1
            else:
                estadisticas["fallidas"] += 1
            
            # Pausa entre requests (excepto en la última)
            if contador < total_sin_texto:
                time.sleep(PAUSA_ENTRE_REQUESTS)
            
            # Pausa cada lote
            if contador % TAMANO_LOTE == 0 and contador < total_sin_texto:
                print()
                print(f"⏸️  Pausa de {PAUSA_CADA_LOTE}s después de {contador} leyes...")
                time.sleep(PAUSA_CADA_LOTE)
                print()
            
            # Checkpoint cada N leyes
            if contador % CHECKPOINT_CADA == 0:
                db.commit()  # Asegurar que todo esté guardado
                print()
                print(f"💾 Checkpoint: {contador}/{total_sin_texto} procesadas "
                      f"({estadisticas['exitosas']} exitosas, {estadisticas['fallidas']} fallidas)")
                print()
        
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
        print(f"Total procesadas: {contador}")
        print(f"✅ Exitosas: {estadisticas['exitosas']}")
        print(f"❌ Fallidas: {estadisticas['fallidas']}")
        print(f"⏱️  Tiempo: {horas}h {minutos}m {segundos}s")
        print()
        
        if estadisticas["fallidas"] > 0:
            print("💡 Las leyes fallidas se pueden reintentar ejecutando el script nuevamente.")
            print()
        
    except KeyboardInterrupt:
        print()
        print()
        print("⚠️  Interrumpido por el usuario")
        print(f"Progreso guardado: {contador} leyes procesadas")
        print(f"✅ Exitosas: {estadisticas.get('exitosas', 0)}")
        print(f"❌ Fallidas: {estadisticas.get('fallidas', 0)}")
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

