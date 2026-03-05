"""
Endpoint de Streaming SSE para CFO AI - Sistema CFO Inteligente

Proporciona respuestas en tiempo real palabra por palabra usando Server-Sent Events (SSE).
Compatible con el sistema de memoria conversacional.

Autor: Sistema CFO Inteligente
Fecha: Noviembre 2025
"""

from decimal import Decimal
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from anthropic import Anthropic
import json
from typing import Generator, Any
from uuid import UUID

from app.core.database import get_db
from app.core.logger import get_logger
from app.core.config import settings
from app.core.security import get_current_user
from app.core.constants import CLAUDE_MAX_TOKENS, CLAUDE_MODEL
from app.services.conversacion_service import ConversacionService
from app.services.sql_router import generar_sql_inteligente
from app.services.cfo_ai_service import ejecutar_consulta_cfo
from app.services.validador_sql import ValidadorSQL
from app.services.sql_post_processor import SQLPostProcessor
from app.services.validador_canonico import validar_respuesta_cfo
from app.services.informe_orquestador import (
    es_pregunta_informe,
    ejecutar_informe,
    _formatear_informe_para_narrativa,
    _formatear_comparativo_para_narrativa,
)
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
                
                # Límite de 12 mensajes (6 intercambios) para evitar timeouts
                contexto = ConversacionService.obtener_contexto(db, conversacion_id, limite=12)
                logger.info(f"Stream: Contexto cargado - {len(contexto)} mensajes")
                
                # Advertencia si conversación muy larga
                if len(contexto) >= 10:
                    yield sse_format("warning", {"message": "⚠️ Conversación larga detectada. Para mejor rendimiento, considera iniciar una nueva conversación."})
                
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
            # FASE 2A: ORQUESTADOR DE INFORMES (multi-query)
            # Si es un informe completo, ejecutar queries predefinidas
            # en vez de generar 1 SQL (que pierde retiros/distribuciones)
            # ═══════════════════════════════════════════════════════════

            if es_pregunta_informe(data.pregunta):
                yield sse_format("status", {"message": "Preparando informe financiero completo..."})
                logger.info(f"Stream: Pregunta detectada como informe — activando orquestador multi-query")

                resultado_informe = ejecutar_informe(db, data.pregunta)

                if resultado_informe is not None:
                    # Informe ensamblado exitosamente — saltar a narrativa
                    if resultado_informe.get("tipo") == "informe_comparativo":
                        # resultado_informe YA contiene el comparativo completo
                        # (ejecutar_informe delega a ejecutar_informe_comparativo internamente)
                        # no ejecutar ejecutar_informe_comparativo() de nuevo — evita 64 queries duplicadas
                        texto_narrativa = _formatear_comparativo_para_narrativa(resultado_informe)
                    else:
                        texto_narrativa = _formatear_informe_para_narrativa(resultado_informe)

                    datos_texto = texto_narrativa
                    sql_generado = "(informe multi-query: 4 consultas predefinidas)"

                    yield sse_format("sql", {"query": sql_generado, "metodo": "informe_orquestador"})
                    yield sse_format("data", {
                        "rows": sum(
                            len(v) for v in [
                                resultado_informe.get("por_area", []),
                                resultado_informe.get("distribuciones_por_socio", []),
                                resultado_informe.get("retiros_por_localidad", []),
                            ]
                        ) + len(resultado_informe.get("totales", {})),
                        "preview": {"tipo": resultado_informe.get("tipo"), "periodo": resultado_informe.get("periodo")},
                    })

                    # Pre-computar resumen sobre los totales del informe
                    totales = resultado_informe.get("totales", {})
                    resumen_informe = {
                        "sumas": {
                            "ingresos_uyu": totales.get("ingresos", {}).get("uyu", 0),
                            "gastos_uyu": totales.get("gastos", {}).get("uyu", 0),
                            "resultado_neto_uyu": totales.get("resultado_neto", {}).get("uyu", 0),
                            "retiros_uyu": totales.get("retiros", {}).get("uyu", 0),
                            "distribuciones_uyu": totales.get("distribuciones", {}).get("uyu", 0),
                        }
                    }

                    # Narrativa con datos del informe
                    yield sse_format("status", {"message": "Generando respuesta narrativa..."})

                    from app.core.cfo_narrative_prompt import CFO_NARRATIVE_SYSTEM_PROMPT, build_cfo_user_message
                    user_msg = build_cfo_user_message(
                        pregunta=data.pregunta,
                        financial_data=texto_narrativa,
                        conversation_history=contexto,
                        resumen_precalculado=resumen_informe,
                    )

                    try:
                        import time
                        word_buffer = ""

                        with client.messages.stream(
                            model=CLAUDE_MODEL,
                            max_tokens=CLAUDE_MAX_TOKENS,
                            temperature=0.1,
                            system=CFO_NARRATIVE_SYSTEM_PROMPT,
                            messages=[{"role": "user", "content": user_msg}]
                        ) as stream:
                            for text_chunk in stream.text_stream:
                                respuesta_completa.append(text_chunk)
                                word_buffer += text_chunk

                                if text_chunk.endswith((' ', '\n', '.', ',', '!', '?', ':', ';', ')', ']', '}')):
                                    if word_buffer.strip():
                                        yield sse_format("token", word_buffer)
                                        word_buffer = ""
                                        time.sleep(0.15)

                            if word_buffer.strip():
                                yield sse_format("token", word_buffer)

                    except Exception as e:
                        logger.error(f"Stream: Error en streaming narrativo de informe — {e}")
                        respuesta_fallback = f"Informe: {datos_texto[:500]}"
                        yield sse_format("token", respuesta_fallback)
                        respuesta_completa = [respuesta_fallback]

                    # Persistencia y finalización (misma lógica que FASE 5)
                    respuesta_final = "".join(respuesta_completa)

                    validacion_canonica = validar_respuesta_cfo(db, data.pregunta, respuesta_final, [resultado_informe])

                    if validacion_canonica.get('advertencia'):
                        advertencia = validacion_canonica['advertencia']
                        yield sse_format("token", advertencia)
                        respuesta_final += advertencia

                    mensaje_guardado = None
                    if conversacion_id:
                        mensaje_guardado = ConversacionService.agregar_mensaje(
                            db, conversacion_id, "assistant", respuesta_final, sql_generado=sql_generado
                        )

                    yield sse_format("done", {
                        "conversation_id": str(conversacion_id) if conversacion_id else None,
                        "mensaje_id": str(mensaje_guardado.id) if mensaje_guardado else None,
                        "sql": sql_generado,
                        "metodo": "informe_orquestador",
                        "filas": 0,
                    })
                    return

                # Si ejecutar_informe retornó None, continuar con flujo normal
                logger.info("Stream: Orquestador no pudo resolver — continuando flujo normal")

            # ═══════════════════════════════════════════════════════════
            # FASE 2: GENERACIÓN SQL (flujo normal)
            # ═══════════════════════════════════════════════════════════

            yield sse_format("status", {"message": "Analizando pregunta y generando SQL..."})

            resultado_sql = generar_sql_inteligente(data.pregunta, contexto=contexto, db=db)
            
            if not resultado_sql.get("exito"):
                error_msg = resultado_sql.get("error", "No pude procesar tu consulta")
                logger.error(f"Stream: Error SQL - {error_msg}")
                
                # Mensaje amigable para el usuario
                mensaje_usuario = error_msg
                if "temporalmente" in error_msg.lower() or "disponible" in error_msg.lower():
                    mensaje_usuario = "⏳ El servicio está ocupado. Por favor, espera unos segundos e intenta de nuevo."
                elif "reformular" in error_msg.lower() or "entender" in error_msg.lower():
                    mensaje_usuario = "🤔 No entendí bien tu consulta. ¿Podrías escribirla de otra forma? Por ejemplo: '¿Cuál fue la facturación de octubre?'"
                
                yield sse_format("error", {"message": mensaje_usuario, "type": "sql_generation"})
                return
            
            sql_generado = resultado_sql["sql"]
            logger.info(f"=== SQL GENERADO [{resultado_sql.get('metodo', 'claude')}] ===\n{sql_generado}\n=== FIN SQL ===")
            yield sse_format("sql", {"query": sql_generado, "metodo": resultado_sql.get('metodo', 'claude')})
            
            # Validación pre-ejecución
            validacion_pre = ValidadorSQL.validar_sql_antes_ejecutar(data.pregunta, sql_generado)
            if not validacion_pre['valido']:
                if validacion_pre.get('bloqueante'):
                    logger.warning(f"Stream: SQL bloqueado por validación - {validacion_pre['problemas']}")
                    yield sse_format("error", {
                        "message": "No se puede ejecutar la consulta: problema de validación (enum en UNION ALL). Corregí la consulta o reformulá la pregunta.",
                        "detalles": validacion_pre['problemas'],
                        "type": "validation_blocking",
                    })
                    return
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

            # Pre-formatear datos SQL a texto para Claude (evita aritmética mental)
            from app.services.sql_post_processor_narrativa import post_procesar_resultado_sql
            datos_texto_sql = post_procesar_resultado_sql(datos, pregunta=data.pregunta)
            
            # Validación post-ejecución
            if datos:
                validacion_post = ValidadorSQL.validar_resultado(data.pregunta, sql_final, datos)
                if not validacion_post['valido']:
                    logger.warning(f"Stream: Resultado sospechoso - {validacion_post['razon']}")
            
            # ═══════════════════════════════════════════════════════════
            # FASE 4: GENERACIÓN NARRATIVA CON STREAMING
            # ═══════════════════════════════════════════════════════════
            
            yield sse_format("status", {"message": "Generando respuesta narrativa..."})
            
            # Pre-computar resumen para evitar aritmética mental de Claude
            resumen = _computar_resumen(datos)

            # Formatear datos y construir prompt narrativo (system/user split para caching)
            from app.core.cfo_narrative_prompt import CFO_NARRATIVE_SYSTEM_PROMPT, build_cfo_user_message
            datos_texto = json.dumps(datos, indent=2, ensure_ascii=False, default=str)
            user_msg = build_cfo_user_message(
                pregunta=data.pregunta,
                financial_data=datos_texto_sql,
                conversation_history=contexto,
                resumen_precalculado=resumen,
            )

            # Stream de Claude con manejo de errores
            # ESTRATEGIA: Acumular palabras completas antes de enviar (mejor UX)
            try:
                import time
                word_buffer = ""

                with client.messages.stream(
                    model=CLAUDE_MODEL,
                    max_tokens=CLAUDE_MAX_TOKENS,
                    temperature=0.1,
                    system=CFO_NARRATIVE_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_msg}]
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
            
            mensaje_guardado = None
            if conversacion_id:
                mensaje_guardado = ConversacionService.agregar_mensaje(
                    db, conversacion_id, "assistant", respuesta_final, sql_generado=sql_final
                )
                logger.info(f"Stream: Respuesta guardada en conversación {conversacion_id}, mensaje_id={mensaje_guardado.id}")
            
            # Finalizar stream
            yield sse_format("done", {
                "conversation_id": str(conversacion_id) if conversacion_id else None,
                "mensaje_id": str(mensaje_guardado.id) if mensaje_guardado else None,
                "sql": sql_final,
                "metodo": resultado_sql.get('metodo', 'claude'),
                "filas": len(datos)
            })
            
        except Exception as e:
            logger.error(f"Stream: Error general - {e}", exc_info=True)
            yield sse_format("error", {
                "message": "😅 Algo salió mal. Por favor, intenta de nuevo en unos segundos.",
                "type": "general_error",
                "detail": str(e)[:100]  # Para debugging
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
