"""
Router API para CFO Inteligente - Conecta Vanna con ejecución
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.logger import get_logger
from app.core.security import get_current_user
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
        
        # Formatear datos de manera legible
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

Pregunta del usuario: {pregunta}

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
            
            # Obtener contexto de mensajes previos (últimos 20)
            # Límite aumentado a 20 mensajes (10 intercambios) para análisis complejos
            contexto = ConversacionService.obtener_contexto(db, conversacion_id, limite=20)
            logger.info(f"Contexto cargado: {len(contexto)} mensajes previos")
        else:
            # Crear nueva conversación INMEDIATAMENTE (antes de generar SQL)
            titulo = ConversacionService.generar_titulo(data.pregunta)
            conversacion = ConversacionService.crear_conversacion(db, current_user.id, titulo)
            conversacion_id = conversacion.id
            logger.info(f"Nueva conversación creada: {conversacion_id}")
        
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
