"""
Router API para CFO Inteligente - Conecta Vanna con ejecución
"""
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.logger import get_logger
from app.core.security import get_current_user
from app.core.constants import CLAUDE_MAX_TOKENS, CLAUDE_MAX_TOKENS_INFORME
from app.services.cfo_ai_service import ejecutar_consulta_cfo

logger = get_logger(__name__)
from app.services.sql_post_processor import SQLPostProcessor
from app.services.sql_post_processor_narrativa import post_procesar_resultado_sql
from app.services.sql_router import generar_sql_inteligente
from app.services.validador_sql import validar_resultado_sql
from app.services.validador_canonico import validar_respuesta_cfo
from pydantic import BaseModel
from typing import Optional, List, Any
from uuid import UUID
import json
from app.services.conversacion_service import ConversacionService
from app.schemas.conversacion import ConversacionListResponse, ConversacionResponse
from app.services.ai.ai_orchestrator import AIOrchestrator
from app.services.informe_orquestador import (
    es_pregunta_informe,
    ejecutar_informe,
    _formatear_informe_para_narrativa,
    _formatear_comparativo_para_narrativa,
)
from app.models import Usuario

router = APIRouter()

# AIOrchestrator para respuestas narrativas (fallback multi-proveedor)
_orchestrator = AIOrchestrator()

class PreguntaCFO(BaseModel):
    pregunta: str
    conversation_id: Optional[UUID] = None  # NUEVO: para continuar conversación


# Columnas que indican agrupación (valores tipo string para subtotales)
_COLUMNAS_AGRUPACION = {
    'localidad', 'area', 'nombre_area', 'tipo_operacion', 'tipo',
    'nombre_mes', 'socio', 'nombre', 'cliente', 'proveedor',
    'moneda_original', 'trimestre', 'semestre', 'anio',
}

# Columnas de porcentaje que NO deben re-sumarse
_COLUMNAS_PORCENTAJE = {'porcentaje', 'rentabilidad', 'rentabilidad_porcentaje', 'participacion'}

# Columnas numéricas que NO tiene sentido sumar (temporales/identificadores)
_COLS_NO_SUMAR = {
    'mes', 'mes_num', 'numero_mes',
    'anio', 'año', 'anio_num', 'year',
    'trimestre', 'semestre',
    'numero', 'id',
}


def _computar_resumen(datos: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Pre-computa totales, subtotales, máximos y mínimos de los datos SQL.

    Evita que Claude tenga que hacer aritmética mental con números grandes.
    Los resultados se inyectan como <resumen_precalculado> en el prompt narrativo.

    Args:
        datos: Lista de dicts (filas) devueltas por PostgreSQL.

    Returns:
        Dict con sumas, subtotales por columna de agrupación, y extremos.
    """
    if not datos:
        return {}

    resumen: dict[str, Any] = {"total_filas": len(datos)}

    # Identificar columnas numéricas (sumables) y de agrupación
    primera_fila = datos[0]
    cols_numericas = []
    cols_agrupacion = []

    for col, val in primera_fila.items():
        col_lower = col.lower()
        if (
            col_lower in _COLUMNAS_PORCENTAJE
            or col_lower in _COLS_NO_SUMAR
            or col_lower.endswith("_id")
        ):
            continue  # No sumar porcentajes
        if isinstance(val, (int, float, Decimal)) and val is not None and not isinstance(val, bool):
            cols_numericas.append(col)
        elif isinstance(val, str) and col_lower in _COLUMNAS_AGRUPACION:
            cols_agrupacion.append(col)

    if not cols_numericas:
        return resumen

    # Sumas globales
    sumas = {}
    promedios = {}
    for col in cols_numericas:
        valores = [row.get(col) for row in datos if row.get(col) is not None]
        if valores:
            total = sum(float(v) for v in valores)
            sumas[col] = round(total, 2)
            promedios[col] = round(total / len(valores), 2)
    resumen["sumas"] = sumas
    resumen["promedios"] = promedios

    # Máximo y mínimo (con referencia a la fila)
    if len(datos) > 1:
        for col in cols_numericas:
            valores_con_ref = []
            for row in datos:
                v = row.get(col)
                if v is not None:
                    # Buscar una columna de texto para identificar la fila
                    ref = None
                    for gc in cols_agrupacion:
                        if row.get(gc):
                            ref = str(row[gc])
                            break
                    if not ref:
                        # Usar la primera columna string que no sea la numérica
                        for k, val in row.items():
                            if k != col and isinstance(val, str) and val:
                                ref = val
                                break
                    valores_con_ref.append((float(v), ref))

            if len(valores_con_ref) > 1:
                max_val = max(valores_con_ref, key=lambda x: x[0])
                min_val = min(valores_con_ref, key=lambda x: x[0])
                if f"maximo" not in resumen:
                    resumen["maximo"] = {}
                    resumen["minimo"] = {}
                resumen["maximo"][col] = {"valor": round(max_val[0], 2), "fila": max_val[1]}
                resumen["minimo"][col] = {"valor": round(min_val[0], 2), "fila": min_val[1]}

    # Subtotales por columna de agrupación
    for gc in cols_agrupacion:
        valores_grupo = set(str(row.get(gc, '')) for row in datos if row.get(gc) is not None)
        if 1 < len(valores_grupo) <= 20:  # Solo si hay agrupación razonable
            subtotales = {}
            for grupo_val in sorted(valores_grupo):
                filas_grupo = [row for row in datos if str(row.get(gc, '')) == grupo_val]
                sub = {}
                for col in cols_numericas:
                    vals = [float(row.get(col, 0) or 0) for row in filas_grupo]
                    sub[col] = round(sum(vals), 2)
                subtotales[grupo_val] = sub
            resumen[f"subtotales_por_{gc.lower()}"] = subtotales

    # Ticket promedio global (si hay monto y cantidad compatibles)
    monto_cols = ["total_pesificado", "ingresos_uyu", "total_uyu", "monto_uyu"]
    cantidad_cols = ["operaciones", "cantidad", "cantidad_operaciones"]
    monto_col = next((c for c in monto_cols if c in sumas), None)
    cantidad_col = next((c for c in cantidad_cols if c in sumas), None)
    if monto_col and cantidad_col:
        cantidad_total = float(sumas.get(cantidad_col, 0) or 0)
        if cantidad_total > 0:
            resumen["ticket_promedio"] = {
                "valor": round(float(sumas[monto_col]) / cantidad_total, 2),
                "monto_col": monto_col,
                "cantidad_col": cantidad_col,
            }

    # Concentración por ranking (top 3/5/10 sobre columna principal)
    if len(datos) >= 5 and sumas:
        col_principal = max(sumas.items(), key=lambda kv: kv[1])[0]
        total_principal = float(sumas.get(col_principal, 0) or 0)
        if total_principal > 0:
            valores_ordenados = sorted(
                [float(row.get(col_principal, 0) or 0) for row in datos],
                reverse=True
            )
            concentracion = {
                "top_3_pct": round(sum(valores_ordenados[:3]) * 100.0 / total_principal, 2),
                "top_5_pct": round(sum(valores_ordenados[:5]) * 100.0 / total_principal, 2),
            }
            if len(valores_ordenados) >= 10:
                concentracion["top_10_pct"] = round(sum(valores_ordenados[:10]) * 100.0 / total_principal, 2)
            resumen["concentracion"] = concentracion

    return resumen

def generar_respuesta_narrativa(pregunta: str, datos: list, sql_generado: str, contexto: list = None) -> str:
    """
    Usa Claude Sonnet 4.5 para generar respuesta narrativa profesional
    """
    try:
        # === LOGS DE DIAGNÓSTICO ===
        logger.debug("Iniciando generar_respuesta_narrativa()")

        logger.debug(f"Datos recibidos: {len(datos)} filas para pregunta: {pregunta[:60]}")

        # Pre-formatear SQL y pre-computar resumen para evitar aritmética de Claude.
        datos_texto_sql = post_procesar_resultado_sql(datos, pregunta=pregunta)
        resumen = _computar_resumen(datos)

        # Formatear datos y construir prompt narrativo (system/user split para caching)
        from app.core.cfo_narrative_prompt import CFO_NARRATIVE_SYSTEM_PROMPT, build_cfo_user_message
        user_msg = build_cfo_user_message(
            pregunta=pregunta,
            financial_data=datos_texto_sql,
            conversation_history=contexto,
            resumen_precalculado=resumen,
        )

        logger.info("Generando narrativa con AIOrchestrator (fallback multi-proveedor)")

        respuesta = _orchestrator.complete(
            prompt=user_msg,
            system_prompt=CFO_NARRATIVE_SYSTEM_PROMPT,
            max_tokens=CLAUDE_MAX_TOKENS,
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

        # FASE 1.5: Orquestador de informes (multi-query)
        if es_pregunta_informe(data.pregunta):
            resultado_informe = ejecutar_informe(db, data.pregunta)
            if resultado_informe is not None:
                if resultado_informe.get("tipo") == "informe_comparativo":
                    texto_narrativa = _formatear_comparativo_para_narrativa(resultado_informe)
                else:
                    texto_narrativa = _formatear_informe_para_narrativa(resultado_informe)
                return _generar_respuesta_informe(
                    db, data, texto_narrativa, resultado_informe,
                    conversacion_id, contexto,
                )
            logger.info("Orquestador no pudo resolver — continuando flujo SQL normal")

        # FASE 2: Generar SQL
        resultado_sql = _generar_sql(data.pregunta, db, contexto)
        if not resultado_sql['exito']:
            return _error_sql_generation(data.pregunta, resultado_sql)

        # FASE 3: Validar y procesar SQL
        sql_final, resultado_sql, sql_procesado_info = _validar_y_procesar_sql(data.pregunta, resultado_sql)

        # FASE 4: Ejecutar y validar resultado
        resultado = _ejecutar_y_validar(db, data.pregunta, sql_final)

        # FASE 5: Generar respuesta
        if resultado.get('success') and resultado.get('data') is not None:
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
    """Genera SQL delegando al router inteligente."""
    return generar_sql_inteligente(pregunta, contexto=contexto, db=db)


def _validar_y_procesar_sql(pregunta: str, resultado_sql: dict) -> tuple:
    """Valida SQL pre-ejecución y aplica post-procesamiento."""
    from app.services.validador_sql import ValidadorSQL
    
    sql_generado = resultado_sql['sql']
    validacion_pre = ValidadorSQL.validar_sql_antes_ejecutar(pregunta, sql_generado)
    
    if not validacion_pre['valido']:
        logger.warning(f"Validación Pre-SQL rechazó: {', '.join(validacion_pre['problemas'])}")
        raise HTTPException(status_code=400, detail="No se pudo generar una consulta válida")
    
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
    respuesta_narrativa = generar_respuesta_narrativa(data.pregunta, resultado['data'], sql_final, contexto=contexto)
    
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


def _generar_respuesta_informe(db, data, texto_narrativa: str, resultado_informe: dict,
                               conversacion_id, contexto) -> dict:
    """Genera respuesta narrativa para informes del orquestador multi-query."""
    from app.core.cfo_narrative_prompt import CFO_NARRATIVE_SYSTEM_PROMPT, build_cfo_user_message

    totales = resultado_informe.get("totales", {})
    if not totales and resultado_informe.get("periodos"):
        totales = resultado_informe["periodos"][-1].get("totales", {})

    resumen_informe = {
        "sumas": {
            "ingresos_uyu": totales.get("ingresos", {}).get("uyu", 0),
            "gastos_uyu": totales.get("gastos", {}).get("uyu", 0),
            "resultado_neto_uyu": totales.get("resultado_neto", {}).get("uyu", 0),
            "retiros_uyu": totales.get("retiros", {}).get("uyu", 0),
            "distribuciones_uyu": totales.get("distribuciones", {}).get("uyu", 0),
        }
    }

    user_msg = build_cfo_user_message(
        pregunta=data.pregunta,
        financial_data=texto_narrativa,
        conversation_history=contexto,
        resumen_precalculado=resumen_informe,
    )

    respuesta_narrativa = _orchestrator.complete(
        prompt=user_msg,
        system_prompt=CFO_NARRATIVE_SYSTEM_PROMPT,
        max_tokens=CLAUDE_MAX_TOKENS_INFORME,
        temperature=0.1,
    )

    if not respuesta_narrativa:
        respuesta_narrativa = f"Informe: {texto_narrativa[:500]}"

    sql_generado = "(informe multi-query: orquestador)"

    validacion_canonica = validar_respuesta_cfo(db, data.pregunta, respuesta_narrativa, [resultado_informe])
    if validacion_canonica.get('advertencia'):
        respuesta_narrativa += validacion_canonica['advertencia']

    if conversacion_id:
        ConversacionService.agregar_mensaje(db, conversacion_id, "assistant", respuesta_narrativa, sql_generado=sql_generado)

    return {
        "pregunta": data.pregunta, "respuesta": respuesta_narrativa,
        "datos_raw": resultado_informe,
        "sql_generado": sql_generado, "status": "success",
        "conversation_id": str(conversacion_id) if conversacion_id else None,
        "metadata": {
            "metodo_generacion_sql": "informe_orquestador",
            "contexto_mensajes": len(contexto),
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
