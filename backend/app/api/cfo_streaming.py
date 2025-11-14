"""
Endpoint de Streaming SSE para CFO AI - Sistema CFO Inteligente

Proporciona respuestas en tiempo real palabra por palabra usando Server-Sent Events (SSE).
Compatible con el sistema de memoria conversacional.

Autor: Sistema CFO Inteligente
Fecha: Noviembre 2025
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from anthropic import Anthropic
import os
import json
from typing import Generator
from uuid import UUID

from app.core.database import get_db
from app.core.logger import get_logger
from app.core.config import settings
from app.services.conversacion_service import ConversacionService
from app.services.sql_router import generar_sql_inteligente
from app.services.cfo_ai_service import ejecutar_consulta_cfo
from app.services.validador_sql import ValidadorSQL
from app.services.chain_of_thought_sql import ChainOfThoughtSQL, generar_con_chain_of_thought
from app.services.sql_post_processor import SQLPostProcessor
from app.services.claude_sql_generator import ClaudeSQLGenerator
from pydantic import BaseModel
from typing import Optional

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
    db: Session = Depends(get_db)
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
                from app.models.usuario import Usuario
                usuario = db.query(Usuario).filter(
                    Usuario.email == "bgandolfo@cgmasociados.com"
                ).first()
                
                if usuario:
                    conversacion = ConversacionService.crear_conversacion(db, usuario.id, titulo)
                    conversacion_id = conversacion.id
                    logger.info(f"Stream: Nueva conversación creada - {conversacion_id}")
                    yield sse_format("conversation_id", {"id": str(conversacion_id)})
                else:
                    logger.warning("Stream: Usuario no encontrado - continuando sin memoria")
                    yield sse_format("warning", {"message": "Continuando sin memoria persistente"})
            
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
            
            prompt = f"""Eres el CFO AI de Conexión Consultora, una consultora en Uruguay.

Pregunta del usuario: {data.pregunta}

Datos obtenidos de la base de datos:
{datos_texto}

SQL ejecutado:
{sql_final}

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
            
            # Stream de Claude con manejo de errores
            # ESTRATEGIA: Acumular palabras completas antes de enviar (mejor UX)
            try:
                import time
                word_buffer = ""
                
                with client.messages.stream(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=500,
                    temperature=0.2,
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

