"""
Router API para CFO Inteligente - Conecta Vanna con ejecución
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.logger import get_logger
from app.services.cfo_ai_service import ejecutar_consulta_cfo

logger = get_logger(__name__)
from app.services.sql_post_processor import SQLPostProcessor
from app.services.claude_sql_generator import ClaudeSQLGenerator
from app.services.sql_router import generar_sql_inteligente
from app.services.validador_sql import validar_resultado_sql
from app.services.chain_of_thought_sql import ChainOfThoughtSQL, generar_con_chain_of_thought
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
import json
import anthropic
from dotenv import load_dotenv
from app.services.conversacion_service import ConversacionService
from app.schemas.conversacion import ConversacionListResponse, ConversacionResponse

# Cargar variables de entorno (fallback por si acaso)
load_dotenv()

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
    conversation_id: Optional[UUID] = None  # NUEVO: para continuar conversación

def generar_respuesta_narrativa(pregunta: str, datos: list, sql_generado: str) -> str:
    """
    Usa Claude Sonnet 4.5 para generar respuesta narrativa profesional
    """
    try:
        # === LOGS DE DIAGNÓSTICO ===
        logger.debug("Iniciando generar_respuesta_narrativa()")
        
        # Verificar configuración
        logger.debug(f"API Key presente: {bool(api_key_limpia)}, longitud: {len(api_key_limpia)}")
        logger.debug(f"Datos recibidos: {len(datos)} filas para pregunta: {pregunta[:60]}")
        
        # Formatear datos de manera legible
        datos_texto = json.dumps(datos, indent=2, ensure_ascii=False, default=str)
        
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
        
        logger.info("Generando narrativa con Claude Sonnet 4.5")
        
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=250,
            messages=[{"role": "user", "content": prompt}]
        )
        
        respuesta = message.content[0].text
        logger.info(f"Narrativa generada exitosamente ({len(respuesta)} chars)")
        
        return respuesta
        
    except Exception as e:
        # Si falla Claude, retornar datos crudos formateados
        logger.error(f"Error crítico en generar_respuesta_narrativa: {type(e).__name__}: {e}", exc_info=True)
        
        return f"Resultado: {json.dumps(datos, indent=2, ensure_ascii=False, default=str)}"

@router.post("/ask")
def preguntar_cfo(data: PreguntaCFO, db: Session = Depends(get_db)):
    """
    Endpoint que recibe pregunta en español y retorna datos con memoria de conversación
    """
    conversacion_id = None
    contexto = []
    
    try:
        # === SISTEMA DE MEMORIA: Obtener o crear conversación (ANTES de generar SQL) ===
        if data.conversation_id:
            # Continuar conversación existente
            conversacion_id = data.conversation_id
            logger.info(f"Continuando conversación {conversacion_id}")
            
            # Obtener contexto de mensajes previos (últimos 10)
            contexto = ConversacionService.obtener_contexto(db, conversacion_id, limite=10)
            logger.info(f"Contexto cargado: {len(contexto)} mensajes previos")
        else:
            # Crear nueva conversación INMEDIATAMENTE (antes de generar SQL)
            titulo = ConversacionService.generar_titulo(data.pregunta)
            from app.models.usuario import Usuario
            usuario = db.query(Usuario).filter(Usuario.email == "bgandolfo@cgmasociados.com").first()
            
            if usuario:
                conversacion = ConversacionService.crear_conversacion(db, usuario.id, titulo)
                conversacion_id = conversacion.id
                logger.info(f"Nueva conversación creada: {conversacion_id}")
            else:
                logger.warning("Usuario bgandolfo@cgmasociados.com no encontrado - continuando sin memoria")
        
        # Guardar pregunta del usuario AHORA (antes de generar SQL para tener historial completo)
        if conversacion_id:
            ConversacionService.agregar_mensaje(db, conversacion_id, "user", data.pregunta)
            logger.info(f"Pregunta guardada en conversación {conversacion_id}")
        
        # === CHAIN-OF-THOUGHT: Detectar si necesita metadatos temporales ===
        if ChainOfThoughtSQL.necesita_metadatos(data.pregunta):
            logger.info("Chain-of-Thought detectada: pregunta temporal compleja")
            
            # Generar SQL en 2 pasos con contexto temporal real
            resultado_cot = generar_con_chain_of_thought(data.pregunta, db, claude_sql_gen)
            
            if resultado_cot['exito']:
                # Usar SQL generado con Chain-of-Thought
                sql_generado = resultado_cot['sql']
                resultado_sql = {
                    'sql': sql_generado,
                    'metodo': 'claude_chain_of_thought',
                    'exito': True,
                    'tiempo_total': 0,  # Se calculará después
                    'tiempos': {'claude': 0, 'vanna': None},
                    'intentos': {'claude': 2, 'vanna': 0, 'total': 2},  # 2 pasos
                    'error': None,
                    'debug': {'metadatos': resultado_cot['metadatos_usados']}
                }
            else:
                # Chain-of-Thought falló, usar flujo normal
                logger.warning("Chain-of-Thought falló, usando flujo normal de generación SQL")
                resultado_sql = generar_sql_inteligente(data.pregunta, contexto=contexto)
        else:
            # Pregunta simple, flujo normal CON CONTEXTO
            resultado_sql = generar_sql_inteligente(data.pregunta, contexto=contexto)
        
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
        
        # VALIDACIÓN PRE-EJECUCIÓN: Detectar problemas lógicos en SQL ANTES de ejecutar
        from app.services.validador_sql import ValidadorSQL
        validacion_pre = ValidadorSQL.validar_sql_antes_ejecutar(data.pregunta, sql_generado)
        
        if not validacion_pre['valido']:
            logger.warning(f"Validación Pre-SQL rechazó SQL - Problemas: {', '.join(validacion_pre['problemas'])}")
            
            # RECHAZAR SQL y usar fallback
            if validacion_pre['sugerencia_fallback'] == 'query_predefinida':
                from app.services.query_fallback import QueryFallback
                sql_predefinido = QueryFallback.get_query_for(data.pregunta)
                
                if sql_predefinido:
                    logger.info("Usando query predefinida como fallback")
                    sql_generado = sql_predefinido
                    resultado_sql['metodo'] = f"{resultado_sql['metodo']}_fallback_predefinido"
                else:
                    logger.warning("No hay query predefinida, SQL puede tener errores")
                    # Continuar con SQL original pero marcar advertencia
                    resultado_sql['metodo'] = f"{resultado_sql['metodo']}_con_advertencias"
            else:
                logger.warning("SQL continúa pero puede tener errores lógicos")
                resultado_sql['metodo'] = f"{resultado_sql['metodo']}_con_advertencias"
        
        # POST-PROCESAMIENTO: Mejorar SQL según patrones en la pregunta
        sql_procesado_info = SQLPostProcessor.procesar_sql(data.pregunta, sql_generado)
        sql_final = sql_procesado_info['sql']
        
        # Ejecutar el SQL (procesado o original)
        resultado = ejecutar_consulta_cfo(db, sql_final)
        
        # VALIDACIÓN POST-EJECUCIÓN: Verificar que los datos sean razonables
        if resultado.get('success') and resultado.get('data'):
            validacion = validar_resultado_sql(data.pregunta, sql_final, resultado['data'])
            
            if not validacion['valido']:
                logger.warning(f"Validación post-SQL - Resultado sospechoso: {validacion['razon']} (Tipo: {validacion['tipo_query']})")
                # Por ahora solo loggeamos, no rechazamos
        
        # Generar respuesta narrativa con Claude Sonnet 4.5
        if resultado.get('success') and resultado.get('data'):
            respuesta_narrativa = generar_respuesta_narrativa(
                data.pregunta,
                resultado['data'],
                sql_generado
            )
            
            # === GUARDAR RESPUESTA DEL ASSISTANT ===
            if conversacion_id:
                ConversacionService.agregar_mensaje(
                    db, conversacion_id, "assistant", respuesta_narrativa, sql_generado=sql_generado
                )
                logger.info(f"Respuesta guardada en conversación {conversacion_id}")
            
            return {
                "pregunta": data.pregunta,
                "respuesta": respuesta_narrativa,
                "datos_raw": resultado['data'],
                "sql_generado": sql_generado,
                "status": "success",
                "conversation_id": str(conversacion_id) if conversacion_id else None,  # NUEVO
                "metadata": {
                    "metodo_generacion_sql": resultado_sql['metodo'],
                    "tiempo_generacion_sql": resultado_sql['tiempo_total'],
                    "intentos_sql": resultado_sql['intentos']['total'],
                    "tiempos_detalle": resultado_sql['tiempos'],
                    "post_procesamiento": sql_procesado_info.get('modificado', False),
                    "contexto_mensajes": len(contexto)  # NUEVO
                }
            }
        else:
            # Si el SQL falló, retornar el error
            return {
                "pregunta": data.pregunta,
                "respuesta": f"No pude obtener datos para esa pregunta. Error: {resultado.get('error', 'Desconocido')}",
                "sql_generado": sql_generado,
                "resultado": resultado,
                "status": "error",
                "conversation_id": str(conversacion_id) if conversacion_id else None
            }
            
    except Exception as e:
        logger.error(f"Error en preguntar_cfo: {str(e)}", exc_info=True)
        return {
            "pregunta": data.pregunta,
            "sql_generado": None,
            "resultado": None,
            "error": str(e),
            "status": "error",
            "conversation_id": str(conversacion_id) if conversacion_id else None
        }


# ══════════════════════════════════════════════════════════════
# ENDPOINTS DE GESTIÓN DE CONVERSACIONES
# ══════════════════════════════════════════════════════════════

@router.get("/conversaciones", response_model=List[ConversacionListResponse])
def listar_conversaciones(
    db: Session = Depends(get_db),
    limit: int = 50
):
    """Lista las conversaciones del usuario (por ahora hardcoded a Bruno)"""
    # TODO: Usar current_user cuando auth esté completo
    from app.models.usuario import Usuario
    usuario = db.query(Usuario).filter(Usuario.email == "bgandolfo@cgmasociados.com").first()
    
    if not usuario:
        return []
    
    conversaciones = ConversacionService.listar_conversaciones(db, usuario.id, limit)
    
    return [
        {
            "id": conv.id,
            "titulo": conv.titulo,
            "updated_at": conv.updated_at,
            "cantidad_mensajes": len(conv.mensajes)
        }
        for conv in conversaciones
    ]


@router.get("/conversaciones/{conversacion_id}", response_model=ConversacionResponse)
def obtener_conversacion(
    conversacion_id: UUID,
    db: Session = Depends(get_db)
):
    """Obtiene una conversación completa con todos sus mensajes"""
    # TODO: Validar propiedad cuando auth esté completo
    from app.models.conversacion import Conversacion
    conversacion = db.query(Conversacion).filter(Conversacion.id == conversacion_id).first()
    
    if not conversacion:
        from fastapi import HTTPException
        raise HTTPException(404, "Conversación no encontrada")
    
    return conversacion


@router.delete("/conversaciones/{conversacion_id}")
def eliminar_conversacion(
    conversacion_id: UUID,
    db: Session = Depends(get_db)
):
    """Elimina una conversación (y sus mensajes por CASCADE)"""
    from app.models.conversacion import Conversacion
    conversacion = db.query(Conversacion).filter(Conversacion.id == conversacion_id).first()
    
    if not conversacion:
        from fastapi import HTTPException
        raise HTTPException(404, "Conversación no encontrada")
    
    db.delete(conversacion)
    db.commit()
    
    return {"success": True, "message": "Conversación eliminada"}
