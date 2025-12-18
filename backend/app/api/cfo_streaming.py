"""
Endpoint de Streaming SSE para CFO AI - Sistema CFO Inteligente

Proporciona respuestas en tiempo real palabra por palabra usando Server-Sent Events (SSE).
Compatible con el sistema de memoria conversacional.

Autor: Sistema CFO Inteligente
Fecha: Noviembre 2025
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from anthropic import Anthropic
import json
from typing import Generator
from uuid import UUID

from app.core.database import get_db
from app.core.logger import get_logger
from app.core.config import settings
from app.core.security import get_current_user
from app.services.conversacion_service import ConversacionService
from app.services.sql_router import generar_sql_inteligente
from app.services.cfo_ai_service import ejecutar_consulta_cfo
from app.services.validador_sql import ValidadorSQL
from app.services.chain_of_thought_sql import ChainOfThoughtSQL, generar_con_chain_of_thought
from app.services.sql_post_processor import SQLPostProcessor
from app.services.claude_sql_generator import ClaudeSQLGenerator
from app.services.validador_canonico import validar_respuesta_cfo
from pydantic import BaseModel
from typing import Optional
from app.models import Usuario

logger = get_logger(__name__)

router = APIRouter()

# Cliente de Anthropic para streaming
api_key_limpia = settings.anthropic_api_key.strip()
if '\n' in api_key_limpia or len(api_key_limpia) > 108:
    api_key_limpia = api_key_limpia.split('\n')[0].strip()[:108]

client = Anthropic(api_key=api_key_limpia)
claude_sql_gen = ClaudeSQLGenerator()


class PreguntaCFOStream(BaseModel):
    pregunta: str
    conversation_id: Optional[UUID] = None


def sse_format(event: str, data: dict | str) -> str:
    """Formatear mensaje en formato Server-Sent Events"""
    if not isinstance(data, str):
        data = json.dumps(data, ensure_ascii=False, default=str)
    
    lines = [f"event: {event}"]
    for line in data.splitlines() or [""]:
        lines.append(f"data: {line}")
    lines.append("")
    
    return "\n".join(lines) + "\n"


@router.post("/ask-stream")
def preguntar_cfo_stream(
    data: PreguntaCFOStream,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Endpoint con streaming SSE para respuestas palabra por palabra
    Compatible con memoria conversacional
    """
    
    def event_generator() -> Generator[str, None, None]:
        conversacion_id = None
        contexto = []
        sql_generado = None
        respuesta_completa = []
        
        try:
            # ═══════════════════════════════════════════════════════════
            # FASE 1: GESTIÓN DE CONVERSACIÓN
            # ═══════════════════════════════════════════════════════════
            
            if data.conversation_id:
                # Continuar conversación existente
                conversacion_id = data.conversation_id
                logger.info(f"Stream: Continuando conversación {conversacion_id}")
                
                # Límite aumentado a 20 mensajes (10 intercambios) para análisis complejos
                contexto = ConversacionService.obtener_contexto(db, conversacion_id, limite=20)
                logger.info(f"Stream: Contexto cargado - {len(contexto)} mensajes")
                
                yield sse_format("status", {"message": f"Continuando conversación ({len(contexto)} mensajes previos)"})
            else:
                # Crear nueva conversación
                yield sse_format("status", {"message": "Iniciando nueva conversación..."})
                
                titulo = ConversacionService.generar_titulo(data.pregunta)
                conversacion = ConversacionService.crear_conversacion(db, current_user.id, titulo)
                conversacion_id = conversacion.id
                logger.info(f"Stream: Nueva conversación creada - {conversacion_id}")
                yield sse_format("conversation_id", {"id": str(conversacion_id)})
            
            # Guardar pregunta del usuario
            if conversacion_id:
                ConversacionService.agregar_mensaje(db, conversacion_id, "user", data.pregunta)
            
            # ═══════════════════════════════════════════════════════════
            # FASE 2: GENERACIÓN SQL
            # ═══════════════════════════════════════════════════════════
            
            yield sse_format("status", {"message": "Analizando pregunta y generando SQL..."})
            
            # Chain-of-Thought si aplica
            if ChainOfThoughtSQL.necesita_metadatos(data.pregunta):
                logger.info("Stream: Chain-of-Thought detectada")
                resultado_cot = generar_con_chain_of_thought(data.pregunta, db, claude_sql_gen)
                
                if resultado_cot['exito']:
                    sql_generado = resultado_cot['sql']
                    resultado_sql = {'exito': True, 'sql': sql_generado, 'metodo': 'chain_of_thought'}
                else:
                    resultado_sql = generar_sql_inteligente(data.pregunta, contexto=contexto)
            else:
                resultado_sql = generar_sql_inteligente(data.pregunta, contexto=contexto)
            
            if not resultado_sql.get("exito"):
                error_msg = resultado_sql.get("error", "Error al generar SQL")
                logger.error(f"Stream: Error SQL - {error_msg}")
                yield sse_format("error", {"message": error_msg, "type": "sql_generation"})
                return
            
            sql_generado = resultado_sql["sql"]
            logger.info(f"=== SQL GENERADO [{resultado_sql.get('metodo', 'claude')}] ===\n{sql_generado}\n=== FIN SQL ===")
            yield sse_format("sql", {"query": sql_generado, "metodo": resultado_sql.get('metodo', 'claude')})
            
            # Validación pre-ejecución
            validacion_pre = ValidadorSQL.validar_sql_antes_ejecutar(data.pregunta, sql_generado)
            if not validacion_pre['valido']:
                logger.warning(f"Stream: SQL con advertencias - {validacion_pre['problemas']}")
                yield sse_format("warning", {"message": "SQL con posibles problemas", "detalles": validacion_pre['problemas']})
            
            # Post-procesamiento
            sql_procesado_info = SQLPostProcessor.procesar_sql(data.pregunta, sql_generado)
            sql_final = sql_procesado_info['sql']
            
            # ═══════════════════════════════════════════════════════════
            # FASE 3: EJECUCIÓN SQL
            # ═══════════════════════════════════════════════════════════
            
            yield sse_format("status", {"message": "Ejecutando consulta en PostgreSQL..."})
            
            resultado = ejecutar_consulta_cfo(db, sql_final)
            
            if not resultado.get("success"):
                error_msg = resultado.get("error", "Error al ejecutar consulta")
                logger.error(f"Stream: Error ejecución - {error_msg}")
                yield sse_format("error", {"message": error_msg, "type": "sql_execution"})
                return
            
            datos = resultado.get("data", [])
            yield sse_format("data", {"rows": len(datos), "preview": datos[:3] if datos else []})
            
            # Validación post-ejecución
            if datos:
                validacion_post = ValidadorSQL.validar_resultado(data.pregunta, sql_final, datos)
                if not validacion_post['valido']:
                    logger.warning(f"Stream: Resultado sospechoso - {validacion_post['razon']}")
            
            # ═══════════════════════════════════════════════════════════
            # FASE 4: GENERACIÓN NARRATIVA CON STREAMING
            # ═══════════════════════════════════════════════════════════
            
            yield sse_format("status", {"message": "Generando respuesta narrativa..."})
            
            datos_texto = json.dumps(datos, indent=2, ensure_ascii=False, default=str)
            
            prompt = f"""Eres el CFO AI de Conexión Consultora, una consultora uruguaya.

RESTRICCIONES CRÍTICAS - LEER ANTES DE PROCESAR DATOS:
1. NUNCA inventes datos que no estén en los resultados de la consulta
2. Si un campo está vacío/null (proveedor, cliente, descripción): decir "No especificado"
3. NUNCA inventar nombres de proveedores, clientes o descripciones
4. Si no hay datos suficientes: decir "No tengo datos suficientes" en lugar de inventar
5. Proyecciones: SOLO si el usuario lo pide explícitamente
6. NO existe tabla de tipo de cambio histórico - solo el TC de cada operación individual

EJEMPLOS DE CAMPOS VACÍOS (OBLIGATORIO):
- proveedor es null/vacío → responder "Proveedor: No especificado"
- cliente es null/vacío → responder "Cliente: No especificado"  
- descripción es null/vacío → responder "Sin descripción registrada"
- PROHIBIDO inventar: "Seguridad Total", "Empresa XYZ", "Comercial ABC", etc.

Pregunta del usuario: {data.pregunta}

Datos obtenidos de la base de datos:
{datos_texto}

FORMATO DE RESPUESTA:
- **Resumen Ejecutivo** (1-2 líneas): conclusión clave
- Si hay múltiples filas: tabla markdown o lista con bullets
- Cifras monetarias: $ X.XXX.XXX (con punto de miles)
- Porcentajes importantes: en **negrita**
- Tono: Profesional, español rioplatense
- Sin datos: explicar amablemente

Genera la respuesta:"""
            
            # Stream de Claude con manejo de errores
            # ESTRATEGIA: Acumular palabras completas antes de enviar (mejor UX)
            try:
                import time
                word_buffer = ""
                
                with client.messages.stream(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=1500,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}]
                ) as stream:
                    for text in stream.text_stream:
                        respuesta_completa.append(text)
                        word_buffer += text
                        
                        # Enviar cuando tengamos palabra completa (termina en espacio o puntuación)
                        if text.endswith((' ', '\n', '.', ',', '!', '?', ':', ';', ')', ']', '}')):
                            if word_buffer.strip():
                                yield sse_format("token", word_buffer)
                                word_buffer = ""
                                # Delay para velocidad natural (150ms por palabra ≈ 7 palabras/seg)
                                time.sleep(0.15)
                    
                    # Enviar cualquier texto restante
                    if word_buffer.strip():
                        yield sse_format("token", word_buffer)
            
            except Exception as e:
                logger.error(f"Stream: Error en streaming Claude - {e}")
                # Fallback: respuesta sin streaming
                respuesta_fallback = f"Resultado: {datos_texto[:500]}"
                yield sse_format("token", respuesta_fallback)
                respuesta_completa = [respuesta_fallback]
            
            # ═══════════════════════════════════════════════════════════
            # FASE 5: PERSISTENCIA Y FINALIZACIÓN
            # ═══════════════════════════════════════════════════════════
            
            # Guardar respuesta completa
            respuesta_final = "".join(respuesta_completa)
            
            # ═══════════════════════════════════════════════════════════
            # FASE 5.5: VALIDACIÓN CANÓNICA
            # ═══════════════════════════════════════════════════════════
            
            validacion_canonica = validar_respuesta_cfo(db, data.pregunta, respuesta_final, datos)
            
            if validacion_canonica.get('advertencia'):
                # Enviar advertencia como tokens adicionales
                advertencia = validacion_canonica['advertencia']
                yield sse_format("token", advertencia)
                respuesta_final += advertencia
                logger.warning(f"Stream: Validación canónica agregó advertencia para '{validacion_canonica['query_canonica']}'")
            elif validacion_canonica.get('validado'):
                logger.info(f"Stream: Validación canónica OK - {validacion_canonica['query_canonica']}")
            
            if conversacion_id:
                ConversacionService.agregar_mensaje(
                    db, conversacion_id, "assistant", respuesta_final, sql_generado=sql_final
                )
                logger.info(f"Stream: Respuesta guardada en conversación {conversacion_id}")
            
            # Finalizar stream
            yield sse_format("done", {
                "conversation_id": str(conversacion_id) if conversacion_id else None,
                "sql": sql_final,
                "metodo": resultado_sql.get('metodo', 'claude'),
                "filas": len(datos)
            })
            
        except Exception as e:
            logger.error(f"Stream: Error general - {e}", exc_info=True)
            yield sse_format("error", {
                "message": f"Error inesperado: {str(e)}",
                "type": "general_error"
            })
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*"
        }
    )
