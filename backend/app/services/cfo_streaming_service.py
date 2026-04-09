"""Lógica de negocio para el endpoint SSE de CFO AI."""

from __future__ import annotations

import json
import time
from decimal import Decimal
from typing import Any, Generator, Optional
from uuid import UUID

from anthropic import Anthropic
from sqlalchemy.orm import Session

from app.core.cfo_narrative_prompt import (
    CFO_NARRATIVE_SYSTEM_PROMPT,
    build_cfo_user_message,
)
from app.core.config import settings
from app.core.constants import CLAUDE_MAX_TOKENS, CLAUDE_MAX_TOKENS_INFORME, CLAUDE_MODEL
from app.core.logger import get_logger
from app.services.cfo_ai_service import ejecutar_consulta_cfo
from app.services.conversacion_service import ConversacionService
from app.services.informe_orquestador import (
    _formatear_comparativo_para_narrativa,
    _formatear_informe_para_narrativa,
    computar_resumen_informe,
    ejecutar_informe,
    es_pregunta_informe,
)
from app.services.sql_post_processor import SQLPostProcessor
from app.services.sql_post_processor_narrativa import post_procesar_resultado_sql
from app.services.sql_router import generar_sql_inteligente
from app.services.validador_canonico import validar_respuesta_cfo
from app.services.validador_sql import ValidadorSQL

logger = get_logger(__name__)

# Cliente de Anthropic para streaming
api_key_limpia = settings.anthropic_api_key.strip()
if "\n" in api_key_limpia or len(api_key_limpia) > 108:
    api_key_limpia = api_key_limpia.split("\n")[0].strip()[:108]

client = Anthropic(api_key=api_key_limpia)

# Columnas que indican agrupación (valores tipo string para subtotales)
_COLUMNAS_AGRUPACION = {
    "localidad",
    "area",
    "nombre_area",
    "tipo_operacion",
    "tipo",
    "nombre_mes",
    "socio",
    "nombre",
    "cliente",
    "proveedor",
    "moneda_original",
    "trimestre",
    "semestre",
    "anio",
}

# Columnas de porcentaje que NO deben re-sumarse
_COLUMNAS_PORCENTAJE = {"porcentaje", "rentabilidad", "rentabilidad_porcentaje", "participacion"}

# Columnas numéricas que NO tiene sentido sumar (temporales/identificadores)
_COLS_NO_SUMAR = {
    "mes",
    "mes_num",
    "numero_mes",
    "anio",
    "año",
    "anio_num",
    "year",
    "trimestre",
    "semestre",
    "numero",
    "id",
}


def sse_format(event: str, data: dict | str) -> str:
    """Formatea un evento Server-Sent Events manteniendo el contrato actual."""
    if not isinstance(data, str):
        data = json.dumps(data, ensure_ascii=False, default=str)

    lines = [f"event: {event}"]
    for line in data.splitlines() or [""]:
        lines.append(f"data: {line}")
    lines.append("")

    return "\n".join(lines) + "\n"


def _computar_resumen(datos: list[dict[str, Any]]) -> dict[str, Any]:
    """Pre-computa totales, subtotales y extremos de resultados SQL."""
    if not datos:
        return {}

    resumen: dict[str, Any] = {"total_filas": len(datos)}

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
            continue
        if isinstance(val, (int, float, Decimal)) and val is not None and not isinstance(val, bool):
            cols_numericas.append(col)
        elif isinstance(val, str) and col_lower in _COLUMNAS_AGRUPACION:
            cols_agrupacion.append(col)

    if not cols_numericas:
        return resumen

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

    if len(datos) > 1:
        for col in cols_numericas:
            valores_con_ref = []
            for row in datos:
                valor = row.get(col)
                if valor is None:
                    continue

                referencia = None
                for col_agrupacion in cols_agrupacion:
                    if row.get(col_agrupacion):
                        referencia = str(row[col_agrupacion])
                        break
                if not referencia:
                    for key, raw_val in row.items():
                        if key != col and isinstance(raw_val, str) and raw_val:
                            referencia = raw_val
                            break
                valores_con_ref.append((float(valor), referencia))

            if len(valores_con_ref) > 1:
                max_val = max(valores_con_ref, key=lambda item: item[0])
                min_val = min(valores_con_ref, key=lambda item: item[0])
                if "maximo" not in resumen:
                    resumen["maximo"] = {}
                    resumen["minimo"] = {}
                resumen["maximo"][col] = {"valor": round(max_val[0], 2), "fila": max_val[1]}
                resumen["minimo"][col] = {"valor": round(min_val[0], 2), "fila": min_val[1]}

    for col_agrupacion in cols_agrupacion:
        valores_grupo = set(
            str(row.get(col_agrupacion, "")) for row in datos if row.get(col_agrupacion) is not None
        )
        if 1 < len(valores_grupo) <= 20:
            subtotales = {}
            for grupo_val in sorted(valores_grupo):
                filas_grupo = [row for row in datos if str(row.get(col_agrupacion, "")) == grupo_val]
                subtotal = {}
                for col in cols_numericas:
                    vals = [float(row.get(col, 0) or 0) for row in filas_grupo]
                    subtotal[col] = round(sum(vals), 2)
                subtotales[grupo_val] = subtotal
            resumen[f"subtotales_por_{col_agrupacion.lower()}"] = subtotales

    monto_cols = ["total_pesificado", "ingresos_uyu", "total_uyu", "monto_uyu"]
    cantidad_cols = ["operaciones", "cantidad", "cantidad_operaciones"]
    monto_col = next((col for col in monto_cols if col in sumas), None)
    cantidad_col = next((col for col in cantidad_cols if col in sumas), None)
    if monto_col and cantidad_col:
        cantidad_total = float(sumas.get(cantidad_col, 0) or 0)
        if cantidad_total > 0:
            resumen["ticket_promedio"] = {
                "valor": round(float(sumas[monto_col]) / cantidad_total, 2),
                "monto_col": monto_col,
                "cantidad_col": cantidad_col,
            }

    if len(datos) >= 5 and sumas:
        col_principal = max(sumas.items(), key=lambda item: item[1])[0]
        total_principal = float(sumas.get(col_principal, 0) or 0)
        if total_principal > 0:
            valores_ordenados = sorted(
                [float(row.get(col_principal, 0) or 0) for row in datos],
                reverse=True,
            )
            concentracion = {
                "top_3_pct": round(sum(valores_ordenados[:3]) * 100.0 / total_principal, 2),
                "top_5_pct": round(sum(valores_ordenados[:5]) * 100.0 / total_principal, 2),
            }
            if len(valores_ordenados) >= 10:
                concentracion["top_10_pct"] = round(
                    sum(valores_ordenados[:10]) * 100.0 / total_principal,
                    2,
                )
            resumen["concentracion"] = concentracion

    return resumen


def _stream_claude_response(
    *,
    system_prompt: str,
    user_message: str,
    max_tokens: int,
    respuesta_completa: list[str],
) -> Generator[str, None, None]:
    """Emite tokens SSE con la misma granularidad actual de streaming."""
    word_buffer = ""

    with client.messages.stream(
        model=CLAUDE_MODEL,
        max_tokens=max_tokens,
        temperature=0.1,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        for text_chunk in stream.text_stream:
            respuesta_completa.append(text_chunk)
            word_buffer += text_chunk

            if text_chunk.endswith((" ", "\n", ".", ",", "!", "?", ":", ";", ")", "]", "}")):
                if word_buffer.strip():
                    yield sse_format("token", word_buffer)
                    word_buffer = ""
                    time.sleep(0.15)

        if word_buffer.strip():
            yield sse_format("token", word_buffer)


def _guardar_respuesta_final(
    db: Session,
    *,
    conversacion_id: Optional[UUID],
    respuesta_final: str,
    sql_generado: Optional[str],
) -> Any:
    """Persiste el mensaje del asistente si la conversación existe."""
    if not conversacion_id:
        return None
    return ConversacionService.agregar_mensaje(
        db,
        conversacion_id,
        "assistant",
        respuesta_final,
        sql_generado=sql_generado,
    )


def _inicializar_conversacion(
    db: Session,
    *,
    pregunta: str,
    conversation_id: Optional[UUID],
    usuario_id: UUID,
) -> tuple[Optional[UUID], list[dict[str, Any]], list[str]]:
    """Carga o crea una conversación y devuelve SSE iniciales."""
    eventos: list[str] = []
    contexto: list[dict[str, Any]] = []
    conversacion_id = conversation_id

    if conversation_id:
        logger.info(f"Stream: Continuando conversación {conversation_id}")
        contexto = ConversacionService.obtener_contexto(db, conversation_id, limite=12)
        logger.info(f"Stream: Contexto cargado - {len(contexto)} mensajes")

        if len(contexto) >= 10:
            eventos.append(
                sse_format(
                    "warning",
                    {
                        "message": "⚠️ Conversación larga detectada. Para mejor rendimiento, considera iniciar una nueva conversación.",
                    },
                )
            )

        eventos.append(
            sse_format("status", {"message": f"Continuando conversación ({len(contexto)} mensajes previos)"})
        )
    else:
        eventos.append(sse_format("status", {"message": "Iniciando nueva conversación..."}))
        titulo = ConversacionService.generar_titulo(pregunta)
        conversacion = ConversacionService.crear_conversacion(db, usuario_id, titulo)
        conversacion_id = conversacion.id
        logger.info(f"Stream: Nueva conversación creada - {conversacion_id}")
        eventos.append(sse_format("conversation_id", {"id": str(conversacion_id)}))

    if conversacion_id:
        ConversacionService.agregar_mensaje(db, conversacion_id, "user", pregunta)

    return conversacion_id, contexto, eventos


def _generar_eventos_informe(
    db: Session,
    *,
    pregunta: str,
    contexto: list[dict[str, Any]],
    conversacion_id: Optional[UUID],
    respuesta_completa: list[str],
) -> Optional[Generator[str, None, None]]:
    """Ejecuta el flujo multi-query de informes y emite SSE si aplica."""
    if not es_pregunta_informe(pregunta):
        return None

    def generator() -> Generator[str, None, None]:
        yield sse_format("status", {"message": "Preparando informe financiero completo..."})
        logger.info("Stream: Pregunta detectada como informe — activando orquestador multi-query")

        resultado_informe = ejecutar_informe(db, pregunta)
        if resultado_informe is None:
            logger.info("Stream: Orquestador no pudo resolver — continuando flujo normal")
            return

        if resultado_informe.get("tipo") == "informe_comparativo":
            texto_narrativa = _formatear_comparativo_para_narrativa(resultado_informe)
        else:
            texto_narrativa = _formatear_informe_para_narrativa(resultado_informe)

        sql_generado = "(informe multi-query: 4 consultas predefinidas)"

        yield sse_format("sql", {"query": sql_generado, "metodo": "informe_orquestador"})
        yield sse_format(
            "data",
            {
                "rows": sum(
                    len(value)
                    for value in [
                        resultado_informe.get("por_area", []),
                        resultado_informe.get("distribuciones_por_socio", []),
                        resultado_informe.get("retiros_por_localidad", []),
                    ]
                )
                + len(resultado_informe.get("totales", {})),
                "preview": {
                    "tipo": resultado_informe.get("tipo"),
                    "periodo": resultado_informe.get("periodo"),
                },
            },
        )

        resumen_informe = computar_resumen_informe(resultado_informe)
        yield sse_format("status", {"message": "Generando respuesta narrativa..."})

        user_msg = build_cfo_user_message(
            pregunta=pregunta,
            financial_data=texto_narrativa,
            conversation_history=contexto,
            resumen_precalculado=resumen_informe,
        )

        try:
            yield from _stream_claude_response(
                system_prompt=CFO_NARRATIVE_SYSTEM_PROMPT,
                user_message=user_msg,
                max_tokens=CLAUDE_MAX_TOKENS_INFORME,
                respuesta_completa=respuesta_completa,
            )
        except Exception as exc:
            logger.error(f"Stream: Error en streaming narrativo de informe — {exc}")
            respuesta_fallback = f"Informe: {texto_narrativa[:500]}"
            yield sse_format("token", respuesta_fallback)
            respuesta_completa[:] = [respuesta_fallback]

        respuesta_final = "".join(respuesta_completa)
        validacion_canonica = validar_respuesta_cfo(db, pregunta, respuesta_final, [resultado_informe])
        if validacion_canonica.get("advertencia"):
            advertencia = validacion_canonica["advertencia"]
            yield sse_format("token", advertencia)
            respuesta_final += advertencia

        mensaje_guardado = _guardar_respuesta_final(
            db,
            conversacion_id=conversacion_id,
            respuesta_final=respuesta_final,
            sql_generado=sql_generado,
        )

        yield sse_format(
            "done",
            {
                "conversation_id": str(conversacion_id) if conversacion_id else None,
                "mensaje_id": str(mensaje_guardado.id) if mensaje_guardado else None,
                "sql": sql_generado,
                "metodo": "informe_orquestador",
                "filas": 0,
            },
        )

    return generator()


def _generar_eventos_sql(
    db: Session,
    *,
    pregunta: str,
    contexto: list[dict[str, Any]],
    conversacion_id: Optional[UUID],
    respuesta_completa: list[str],
) -> Generator[str, None, None]:
    """Ejecuta el flujo SQL estándar y emite eventos SSE."""
    yield sse_format("status", {"message": "Analizando pregunta y generando SQL..."})

    resultado_sql = generar_sql_inteligente(pregunta, contexto=contexto, db=db)
    if not resultado_sql.get("exito"):
        error_msg = resultado_sql.get("error", "No pude procesar tu consulta")
        logger.error(f"Stream: Error SQL - {error_msg}")

        mensaje_usuario = error_msg
        if "temporalmente" in error_msg.lower() or "disponible" in error_msg.lower():
            mensaje_usuario = "⏳ El servicio está ocupado. Por favor, espera unos segundos e intenta de nuevo."
        elif "reformular" in error_msg.lower() or "entender" in error_msg.lower():
            mensaje_usuario = (
                "🤔 No entendí bien tu consulta. ¿Podrías escribirla de otra forma? "
                "Por ejemplo: '¿Cuál fue la facturación de octubre?'"
            )

        yield sse_format("error", {"message": mensaje_usuario, "type": "sql_generation"})
        return

    sql_generado = resultado_sql["sql"]
    logger.info(f"=== SQL GENERADO [{resultado_sql.get('metodo', 'claude')}] ===\n{sql_generado}\n=== FIN SQL ===")
    yield sse_format("sql", {"query": sql_generado, "metodo": resultado_sql.get("metodo", "claude")})

    validacion_pre = ValidadorSQL.validar_sql_antes_ejecutar(pregunta, sql_generado)
    if not validacion_pre["valido"]:
        if validacion_pre.get("bloqueante"):
            logger.warning(f"Stream: SQL bloqueado por validación - {validacion_pre['problemas']}")
            yield sse_format(
                "error",
                {
                    "message": "No se puede ejecutar la consulta: problema de validación (enum en UNION ALL). Corregí la consulta o reformulá la pregunta.",
                    "detalles": validacion_pre["problemas"],
                    "type": "validation_blocking",
                },
            )
            return
        logger.warning(f"Stream: SQL con advertencias - {validacion_pre['problemas']}")
        yield sse_format(
            "warning",
            {"message": "SQL con posibles problemas", "detalles": validacion_pre["problemas"]},
        )

    sql_procesado_info = SQLPostProcessor.procesar_sql(pregunta, sql_generado)
    sql_final = sql_procesado_info["sql"]

    yield sse_format("status", {"message": "Ejecutando consulta en PostgreSQL..."})
    resultado = ejecutar_consulta_cfo(db, sql_final)
    if not resultado.get("success"):
        error_msg = resultado.get("error", "Error al ejecutar consulta")
        logger.error(f"Stream: Error ejecución - {error_msg}")
        yield sse_format("error", {"message": error_msg, "type": "sql_execution"})
        return

    datos = resultado.get("data", [])
    yield sse_format("data", {"rows": len(datos), "preview": datos[:3] if datos else []})

    datos_texto_sql = post_procesar_resultado_sql(datos, pregunta=pregunta)
    if datos:
        validacion_post = ValidadorSQL.validar_resultado(pregunta, sql_final, datos)
        if not validacion_post["valido"]:
            logger.warning(f"Stream: Resultado sospechoso - {validacion_post['razon']}")

    yield sse_format("status", {"message": "Generando respuesta narrativa..."})
    resumen = _computar_resumen(datos)
    user_msg = build_cfo_user_message(
        pregunta=pregunta,
        financial_data=datos_texto_sql,
        conversation_history=contexto,
        resumen_precalculado=resumen,
    )

    try:
        yield from _stream_claude_response(
            system_prompt=CFO_NARRATIVE_SYSTEM_PROMPT,
            user_message=user_msg,
            max_tokens=CLAUDE_MAX_TOKENS,
            respuesta_completa=respuesta_completa,
        )
    except Exception as exc:
        logger.error(f"Stream: Error en streaming Claude - {exc}")
        datos_texto = json.dumps(datos, indent=2, ensure_ascii=False, default=str)
        respuesta_fallback = f"Resultado: {datos_texto[:500]}"
        yield sse_format("token", respuesta_fallback)
        respuesta_completa[:] = [respuesta_fallback]

    respuesta_final = "".join(respuesta_completa)
    validacion_canonica = validar_respuesta_cfo(db, pregunta, respuesta_final, datos)

    if validacion_canonica.get("advertencia"):
        advertencia = validacion_canonica["advertencia"]
        yield sse_format("token", advertencia)
        respuesta_final += advertencia
        logger.warning(
            f"Stream: Validación canónica agregó advertencia para '{validacion_canonica['query_canonica']}'"
        )
    elif validacion_canonica.get("validado"):
        logger.info(f"Stream: Validación canónica OK - {validacion_canonica['query_canonica']}")

    mensaje_guardado = _guardar_respuesta_final(
        db,
        conversacion_id=conversacion_id,
        respuesta_final=respuesta_final,
        sql_generado=sql_final,
    )
    if conversacion_id and mensaje_guardado:
        logger.info(
            f"Stream: Respuesta guardada en conversación {conversacion_id}, mensaje_id={mensaje_guardado.id}"
        )

    yield sse_format(
        "done",
        {
            "conversation_id": str(conversacion_id) if conversacion_id else None,
            "mensaje_id": str(mensaje_guardado.id) if mensaje_guardado else None,
            "sql": sql_final,
            "metodo": resultado_sql.get("metodo", "claude"),
            "filas": len(datos),
        },
    )


def generar_eventos_cfo_stream(
    db: Session,
    *,
    pregunta: str,
    conversation_id: Optional[UUID],
    usuario_id: UUID,
) -> Generator[str, None, None]:
    """Genera la secuencia SSE completa del chat CFO sin acoplarla al router HTTP."""
    conversacion_id: Optional[UUID] = None
    contexto: list[dict[str, Any]] = []
    respuesta_completa: list[str] = []

    try:
        conversacion_id, contexto, eventos_iniciales = _inicializar_conversacion(
            db,
            pregunta=pregunta,
            conversation_id=conversation_id,
            usuario_id=usuario_id,
        )
        for evento in eventos_iniciales:
            yield evento

        flujo_informe = _generar_eventos_informe(
            db,
            pregunta=pregunta,
            contexto=contexto,
            conversacion_id=conversacion_id,
            respuesta_completa=respuesta_completa,
        )
        if flujo_informe is not None:
            for evento in flujo_informe:
                yield evento
            if respuesta_completa:
                return

        yield from _generar_eventos_sql(
            db,
            pregunta=pregunta,
            contexto=contexto,
            conversacion_id=conversacion_id,
            respuesta_completa=respuesta_completa,
        )

    except Exception as exc:
        logger.error(f"Stream: Error general - {exc}", exc_info=True)
        yield sse_format(
            "error",
            {
                "message": "😅 Algo salió mal. Por favor, intenta de nuevo en unos segundos.",
                "type": "general_error",
                "detail": str(exc)[:100],
            },
        )
