"""
Router API para CFO Inteligente - Conecta Vanna con ejecución
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.services.cfo_ai_service import ejecutar_consulta_cfo
from app.services.sql_post_processor import SQLPostProcessor
from app.services.claude_sql_generator import ClaudeSQLGenerator
from app.services.sql_router import generar_sql_inteligente
from app.services.validador_sql import validar_resultado_sql
from pydantic import BaseModel
import sys
import os
import json
import anthropic
from dotenv import load_dotenv

# Cargar variables de entorno (fallback por si acaso)
load_dotenv()

# Agregar path para importar scripts
sys.path.append(os.path.join(os.path.dirname(__file__), '../../scripts'))
from configurar_vanna_local import my_vanna as vn

router = APIRouter()

# FIX: Limpiar la API key por si viene con saltos de línea o duplicada
api_key_limpia = settings.anthropic_api_key.strip()
if '\n' in api_key_limpia or len(api_key_limpia) > 108:
    # Si está duplicada, tomar solo la primera parte
    api_key_limpia = api_key_limpia.split('\n')[0].strip()[:108]

# Cliente de Anthropic para Claude Sonnet 4.5 (respuestas narrativas)
client = anthropic.Anthropic(api_key=api_key_limpia)

# Generador de SQL con Claude Sonnet 4.5 (modelo principal)
claude_sql_gen = ClaudeSQLGenerator()

class PreguntaCFO(BaseModel):
    pregunta: str

def generar_respuesta_narrativa(pregunta: str, datos: list, sql_generado: str) -> str:
    """
    Usa Claude Sonnet 4.5 para generar respuesta narrativa profesional
    """
    try:
        # === LOGS DE DIAGNÓSTICO ===
        print("\n" + "="*80)
        print("🔍 DEBUG: Iniciando generar_respuesta_narrativa()")
        print("="*80)
        
        # Verificar API Key
        print(f"✅ API Key presente: {bool(api_key_limpia)}")
        if api_key_limpia:
            print(f"✅ API Key primeros 10 chars: {api_key_limpia[:10]}...")
            print(f"✅ API Key longitud: {len(api_key_limpia)} (debe ser 108)")
        
        # Verificar cliente
        print(f"✅ Cliente Anthropic inicializado: {bool(client)}")
        
        # Verificar datos
        print(f"✅ Datos recibidos: {len(datos)} filas")
        print(f"✅ Pregunta: {pregunta}")
        
        # Formatear datos de manera legible
        datos_texto = json.dumps(datos, indent=2, ensure_ascii=False, default=str)
        print(f"✅ Datos formateados (primeros 200 chars): {datos_texto[:200]}...")
        
        prompt = f"""Eres el CFO AI de Conexión Consultora, una consultora en Uruguay.

Pregunta del usuario: {pregunta}

Datos obtenidos de la base de datos:
{datos_texto}

SQL ejecutado:
{sql_generado}

INSTRUCCIONES:
- Genera una respuesta clara, profesional y útil en español rioplatense
- Destaca el dato principal de manera conversacional
- Si hay múltiples filas, resume los puntos clave
- Sé conciso (2-4 líneas máximo)
- Usa formato narrativo, NO JSON ni formato técnico
- Si es una cifra monetaria, usa el formato apropiado (ej: "$ 1.234.567")
- Si es un porcentaje, redondea a 2 decimales
- Si no hay datos, explica amablemente que no hay información para ese período

Genera SOLO la respuesta, sin preámbulos ni explicaciones adicionales."""
        
        print("🚀 Llamando a Claude Sonnet 4.5...")
        print(f"   Modelo: claude-sonnet-4-5-20250929")
        print(f"   Max tokens: 250")
        
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=250,
            messages=[{"role": "user", "content": prompt}]
        )
        
        print("✅ Respuesta recibida de Claude")
        print(f"   Tipo de contenido: {type(message.content)}")
        print(f"   Contenido: {message.content[0].text[:100]}...")
        
        respuesta = message.content[0].text
        print(f"✅ Respuesta narrativa generada exitosamente ({len(respuesta)} chars)")
        print("="*80 + "\n")
        
        return respuesta
        
    except Exception as e:
        # Si falla Claude, retornar datos crudos formateados
        print("\n" + "❌"*40)
        print(f"ERROR CRÍTICO en generar_respuesta_narrativa: {type(e).__name__}: {e}")
        print("❌"*40)
        import traceback
        traceback.print_exc()
        print("❌"*40 + "\n")
        
        return f"Resultado: {json.dumps(datos, indent=2, ensure_ascii=False, default=str)}"

@router.post("/ask")
def preguntar_cfo(data: PreguntaCFO, db: Session = Depends(get_db)):
    """
    Endpoint que recibe pregunta en español y retorna datos
    """
    try:
        # === GENERAR SQL CON ROUTER INTELIGENTE (Claude → Vanna fallback) ===
        resultado_sql = generar_sql_inteligente(data.pregunta)
        
        if not resultado_sql['exito']:
            return {
                "pregunta": data.pregunta,
                "respuesta": f"No pude generar SQL válido. {resultado_sql['error']}",
                "sql_generado": None,
                "status": "error",
                "error_tipo": "sql_generation_failed",
                "metadata": {
                    "metodo": resultado_sql['metodo'],
                    "tiempo_generacion": resultado_sql['tiempo_total'],
                    "intentos": resultado_sql['intentos']['total'],
                    "tiempos_detalle": resultado_sql['tiempos']
                }
            }
        
        sql_generado = resultado_sql['sql']
        
        # POST-PROCESAMIENTO: Mejorar SQL según patrones en la pregunta
        sql_procesado_info = SQLPostProcessor.procesar_sql(data.pregunta, sql_generado)
        sql_final = sql_procesado_info['sql']
        
        # Ejecutar el SQL (procesado o original)
        resultado = ejecutar_consulta_cfo(db, sql_final)
        
        # VALIDACIÓN POST-EJECUCIÓN: Verificar que los datos sean razonables
        if resultado.get('success') and resultado.get('data'):
            validacion = validar_resultado_sql(data.pregunta, sql_final, resultado['data'])
            
            if not validacion['valido']:
                print(f"⚠️ [Validación] Resultado sospechoso: {validacion['razon']}")
                print(f"   Tipo query: {validacion['tipo_query']}")
                # Por ahora solo loggeamos, no rechazamos
        
        # Generar respuesta narrativa con Claude Sonnet 4.5
        if resultado.get('success') and resultado.get('data'):
            respuesta_narrativa = generar_respuesta_narrativa(
                data.pregunta,
                resultado['data'],
                sql_generado
            )
            
            return {
                "pregunta": data.pregunta,
                "respuesta": respuesta_narrativa,
                "datos_raw": resultado['data'],
                "sql_generado": sql_generado,
                "status": "success",
                "metadata": {
                    "metodo_generacion_sql": resultado_sql['metodo'],
                    "tiempo_generacion_sql": resultado_sql['tiempo_total'],
                    "intentos_sql": resultado_sql['intentos']['total'],
                    "tiempos_detalle": resultado_sql['tiempos'],
                    "post_procesamiento": sql_procesado_info.get('modificado', False)
                }
            }
        else:
            # Si el SQL falló, retornar el error
            return {
                "pregunta": data.pregunta,
                "respuesta": f"No pude obtener datos para esa pregunta. Error: {resultado.get('error', 'Desconocido')}",
                "sql_generado": sql_generado,
                "resultado": resultado,
                "status": "error"
            }
            
    except Exception as e:
        return {
            "pregunta": data.pregunta,
            "sql_generado": None,
            "resultado": None,
            "error": str(e),
            "status": "error"
        }
