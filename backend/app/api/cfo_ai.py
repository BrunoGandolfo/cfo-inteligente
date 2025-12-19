"""
Router API para CFO Inteligente - Conecta Vanna con ejecución
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.logger import get_logger
from app.core.security import get_current_user
from app.services.cfo_ai_service import ejecutar_consulta_cfo

logger = get_logger(__name__)
from app.services.sql_post_processor import SQLPostProcessor
from app.services.claude_sql_generator import ClaudeSQLGenerator
from app.services.sql_router import generar_sql_inteligente
from app.services.validador_sql import validar_resultado_sql
from app.services.validador_canonico import validar_respuesta_cfo
from app.services.chain_of_thought_sql import ChainOfThoughtSQL, generar_con_chain_of_thought
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
import json
from app.services.conversacion_service import ConversacionService
from app.schemas.conversacion import ConversacionListResponse, ConversacionResponse
from app.services.ai.ai_orchestrator import AIOrchestrator
from app.models import Usuario

router = APIRouter()

# AIOrchestrator para respuestas narrativas (fallback multi-proveedor)
_orchestrator = AIOrchestrator()

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
        
        logger.debug(f"Datos recibidos: {len(datos)} filas para pregunta: {pregunta[:60]}")
        
        # Formatear datos y construir prompt (usando helper centralizado)
        from app.core.prompts import build_cfo_narrative_prompt
        datos_texto = json.dumps(datos, indent=2, ensure_ascii=False, default=str)
        prompt = build_cfo_narrative_prompt(pregunta, datos_texto)
        
        logger.info("Generando narrativa con AIOrchestrator (fallback multi-proveedor)")
        
        respuesta = _orchestrator.complete(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.1
        )
        
        if not respuesta:
            logger.error("AIOrchestrator retornó None - usando fallback de datos crudos")
            return f"Resultado: {json.dumps(datos, indent=2, ensure_ascii=False, default=str)}"
        
        logger.info(f"Narrativa generada exitosamente ({len(respuesta)} chars)")
        return respuesta
        
    except Exception as e:
        # Si falla Claude, retornar datos crudos formateados
        logger.error(f"Error crítico en generar_respuesta_narrativa: {type(e).__name__}: {e}", exc_info=True)
        
        return f"Resultado: {json.dumps(datos, indent=2, ensure_ascii=False, default=str)}"

@router.post("/ask")
def preguntar_cfo(data: PreguntaCFO, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    """Endpoint que recibe pregunta en español y retorna datos con memoria de conversación."""
    conversacion_id = None
    contexto = []
    
    try:
        # FASE 1: Gestionar conversación
        conversacion_id, contexto = _gestionar_conversacion(db, data, current_user)
        
        # FASE 2: Generar SQL
        resultado_sql = _generar_sql(data.pregunta, db, contexto)
        if not resultado_sql['exito']:
            return _error_sql_generation(data.pregunta, resultado_sql)
        
        # FASE 3: Validar y procesar SQL
        sql_final, resultado_sql, sql_procesado_info = _validar_y_procesar_sql(data.pregunta, resultado_sql)
        
        # FASE 4: Ejecutar y validar resultado
        resultado = _ejecutar_y_validar(db, data.pregunta, sql_final)
        
        # FASE 5: Generar respuesta
        if resultado.get('success') and resultado.get('data'):
            return _generar_respuesta_exitosa(
                db, data, resultado_sql, sql_final, resultado, 
                conversacion_id, contexto, sql_procesado_info
            )
        
        return _error_ejecucion(data.pregunta, sql_final, resultado, conversacion_id)
            
    except Exception as e:
        logger.error(f"Error en preguntar_cfo: {str(e)}", exc_info=True)
        return {"pregunta": data.pregunta, "sql_generado": None, "resultado": None, 
                "error": str(e), "status": "error", 
                "conversation_id": str(conversacion_id) if conversacion_id else None}


def _gestionar_conversacion(db: Session, data: PreguntaCFO, current_user) -> tuple:
    """Obtiene o crea conversación y guarda pregunta."""
    if data.conversation_id:
        conversacion_id = data.conversation_id
        contexto = ConversacionService.obtener_contexto(db, conversacion_id, limite=20)
        logger.info(f"Contexto cargado: {len(contexto)} mensajes previos")
    else:
        titulo = ConversacionService.generar_titulo(data.pregunta)
        conversacion = ConversacionService.crear_conversacion(db, current_user.id, titulo)
        conversacion_id = conversacion.id
        contexto = []
        logger.info(f"Nueva conversación creada: {conversacion_id}")
    
    ConversacionService.agregar_mensaje(db, conversacion_id, "user", data.pregunta)
    return conversacion_id, contexto


def _generar_sql(pregunta: str, db: Session, contexto: list) -> dict:
    """Genera SQL usando chain-of-thought si es necesario."""
    if ChainOfThoughtSQL.necesita_metadatos(pregunta):
        resultado_cot = generar_con_chain_of_thought(pregunta, db, claude_sql_gen)
        if resultado_cot['exito']:
            return {
                'sql': resultado_cot['sql'], 'metodo': 'claude_chain_of_thought',
                'exito': True, 'tiempo_total': 0, 'tiempos': {'claude': 0, 'vanna': None},
                'intentos': {'claude': 2, 'vanna': 0, 'total': 2}, 'error': None
            }
        logger.warning("Chain-of-Thought falló, usando flujo normal")
    return generar_sql_inteligente(pregunta, contexto=contexto)


def _validar_y_procesar_sql(pregunta: str, resultado_sql: dict) -> tuple:
    """Valida SQL pre-ejecución y aplica post-procesamiento."""
    from app.services.validador_sql import ValidadorSQL
    from app.services.query_fallback import QueryFallback
    
    sql_generado = resultado_sql['sql']
    validacion_pre = ValidadorSQL.validar_sql_antes_ejecutar(pregunta, sql_generado)
    
    if not validacion_pre['valido']:
        logger.warning(f"Validación Pre-SQL rechazó: {', '.join(validacion_pre['problemas'])}")
        if validacion_pre['sugerencia_fallback'] == 'query_predefinida':
            sql_predefinido = QueryFallback.get_query_for(pregunta)
            if sql_predefinido:
                sql_generado = sql_predefinido
                resultado_sql['metodo'] += '_fallback_predefinido'
            else:
                resultado_sql['metodo'] += '_con_advertencias'
        else:
            resultado_sql['metodo'] += '_con_advertencias'
    
    sql_procesado_info = SQLPostProcessor.procesar_sql(pregunta, sql_generado)
    return sql_procesado_info['sql'], resultado_sql, sql_procesado_info


def _ejecutar_y_validar(db: Session, pregunta: str, sql_final: str) -> dict:
    """Ejecuta SQL y valida resultado."""
    resultado = ejecutar_consulta_cfo(db, sql_final)
    
    if resultado.get('success') and resultado.get('data'):
        validacion = validar_resultado_sql(pregunta, sql_final, resultado['data'])
        if not validacion['valido']:
            logger.warning(f"Resultado sospechoso: {validacion['razon']}")
    
    return resultado


def _generar_respuesta_exitosa(db, data, resultado_sql, sql_final, resultado, 
                               conversacion_id, contexto, sql_procesado_info) -> dict:
    """Genera respuesta narrativa y metadata para caso exitoso."""
    respuesta_narrativa = generar_respuesta_narrativa(data.pregunta, resultado['data'], sql_final)
    
    validacion_canonica = validar_respuesta_cfo(db, data.pregunta, respuesta_narrativa, resultado['data'])
    if validacion_canonica.get('advertencia'):
        respuesta_narrativa += validacion_canonica['advertencia']
    
    if conversacion_id:
        ConversacionService.agregar_mensaje(db, conversacion_id, "assistant", respuesta_narrativa, sql_generado=sql_final)
    
    return {
        "pregunta": data.pregunta, "respuesta": respuesta_narrativa, "datos_raw": resultado['data'],
        "sql_generado": sql_final, "status": "success",
        "conversation_id": str(conversacion_id) if conversacion_id else None,
        "metadata": {
            "metodo_generacion_sql": resultado_sql['metodo'],
            "tiempo_generacion_sql": resultado_sql['tiempo_total'],
            "intentos_sql": resultado_sql['intentos']['total'],
            "tiempos_detalle": resultado_sql['tiempos'],
            "post_procesamiento": sql_procesado_info.get('modificado', False),
            "contexto_mensajes": len(contexto),
            "validacion_canonica": {
                "aplicada": validacion_canonica.get('validado', False),
                "query": validacion_canonica.get('query_canonica'),
                "diferencia_pct": validacion_canonica.get('diferencia_porcentual'),
                "dentro_tolerancia": validacion_canonica.get('dentro_tolerancia')
            }
        }
    }


def _error_sql_generation(pregunta: str, resultado_sql: dict) -> dict:
    """Respuesta para error en generación SQL."""
    return {
        "pregunta": pregunta, "respuesta": f"No pude generar SQL válido. {resultado_sql['error']}",
        "sql_generado": None, "status": "error", "error_tipo": "sql_generation_failed",
        "metadata": {"metodo": resultado_sql['metodo'], "tiempo_generacion": resultado_sql['tiempo_total'],
                     "intentos": resultado_sql['intentos']['total'], "tiempos_detalle": resultado_sql['tiempos']}
    }


def _error_ejecucion(pregunta: str, sql_generado: str, resultado: dict, conversacion_id) -> dict:
    """Respuesta para error en ejecución SQL."""
    return {
        "pregunta": pregunta, "respuesta": f"No pude obtener datos. Error: {resultado.get('error', 'Desconocido')}",
        "sql_generado": sql_generado, "resultado": resultado, "status": "error",
        "conversation_id": str(conversacion_id) if conversacion_id else None
    }


# ══════════════════════════════════════════════════════════════
# ENDPOINTS DE GESTIÓN DE CONVERSACIONES
# ══════════════════════════════════════════════════════════════

@router.get("/conversaciones", response_model=List[ConversacionListResponse])
def listar_conversaciones(
    db: Session = Depends(get_db),
    limit: int = 50,
    current_user: Usuario = Depends(get_current_user)
):
    """Lista las conversaciones del usuario autenticado"""
    conversaciones = ConversacionService.listar_conversaciones(db, current_user.id, limit)
    
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
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene una conversación completa con todos sus mensajes (solo del usuario)"""
    from app.models.conversacion import Conversacion
    conversacion = db.query(Conversacion).filter(Conversacion.id == conversacion_id).first()
    
    if not conversacion:
        raise HTTPException(404, "Conversación no encontrada")
    
    # Validar que la conversación pertenezca al usuario
    if conversacion.usuario_id != current_user.id:
        raise HTTPException(403, "No tienes acceso a esta conversación")
    
    return conversacion


@router.delete("/conversaciones/{conversacion_id}")
def eliminar_conversacion(
    conversacion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina una conversación del usuario (y sus mensajes por CASCADE)"""
    from app.models.conversacion import Conversacion
    conversacion = db.query(Conversacion).filter(Conversacion.id == conversacion_id).first()
    
    if not conversacion:
        raise HTTPException(404, "Conversación no encontrada")
    
    # Validar que la conversación pertenezca al usuario
    if conversacion.usuario_id != current_user.id:
        raise HTTPException(403, "No tienes acceso a esta conversación")
    
    db.delete(conversacion)
    db.commit()
    
    return {"success": True, "message": "Conversación eliminada"}
