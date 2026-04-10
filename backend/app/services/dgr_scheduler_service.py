"""
Scheduler de monitoreo para trámites DGR.

Consulta periódicamente la DGR, detecta cambios y envía notificaciones
por Telegram cuando hay novedades en trámites activos.
"""

import asyncio
import json
from datetime import date, datetime, timezone
from html import escape
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.access_control import USUARIOS_NOTIFICACION_DGR
from app.core.config import Settings
from app.core.database import SessionLocal
from app.core.logger import get_logger
from app.models.telegram_usuario import TelegramUsuario
from app.models.tramite_dgr_historial import TramiteDgrHistorial
from app.models.tramite_dgr import TramiteDgr
from app.models.usuario import Usuario
from app.services.dgr_service import consultar_tramite_dgr
from app.services.telegram_service import enviar_mensaje_telegram

logger = get_logger(__name__)


def _parse_fecha_ingreso(valor):
    """Parsea fecha_ingreso que puede ser date o string."""
    if valor is None:
        return None

    if isinstance(valor, date):
        return valor

    if isinstance(valor, str):
        from app.services.dgr_service import parsear_fecha_dgr

        return parsear_fecha_dgr(valor)

    return None


def _normalizar_texto(value: Optional[str]) -> str:
    """Normaliza strings para comparar cambios de estado y observaciones."""
    return " ".join(str(value or "").split())


def _registrar_historial_cambio(
    db: Session,
    tramite: TramiteDgr,
    campo_modificado: str,
    valor_anterior: Optional[str],
    valor_nuevo: Optional[str],
) -> None:
    """Registra un cambio puntual en el historial del trámite."""
    if _normalizar_texto(valor_anterior) == _normalizar_texto(valor_nuevo):
        return

    db.add(
        TramiteDgrHistorial(
            tramite_dgr_id=tramite.id,
            campo_modificado=campo_modificado,
            valor_anterior=valor_anterior,
            valor_nuevo=valor_nuevo,
            detectado_en=datetime.now(timezone.utc),
        )
    )


def _aplicar_datos_dgr(tramite: TramiteDgr, datos: dict) -> None:
    """Aplica al modelo los datos nuevos devueltos por la consulta DGR."""
    from app.services.dgr_service import calcular_fecha_vencimiento

    tramite.fecha_ingreso = _parse_fecha_ingreso(datos.get("fecha_ingreso"))
    tramite.escribano_emisor = datos.get("escribano_emisor")
    tramite.estado_actual = datos.get("estado_actual")
    tramite.observaciones = datos.get("observaciones")

    inscripciones = datos.get("inscripciones")
    if inscripciones:
        tramite.actos = json.dumps(inscripciones, ensure_ascii=False)
    else:
        tramite.actos = None

    tramite.ultimo_chequeo = datetime.now(timezone.utc)
    tramite.updated_at = datetime.now(timezone.utc)
    tramite.fecha_vencimiento = calcular_fecha_vencimiento(
        tramite.fecha_ingreso, tramite.estado_actual
    )


def _obtener_destinatarios_notificacion(db: Session) -> list[tuple[str, int]]:
    """Resuelve emails configurados del módulo DGR a chat IDs activos de Telegram."""
    usuarios = (
        db.query(Usuario)
        .filter(func.lower(Usuario.email).in_([email.lower() for email in USUARIOS_NOTIFICACION_DGR]))
        .all()
    )
    usuarios_por_email = {usuario.email.lower(): usuario for usuario in usuarios}

    usuario_ids = [usuario.id for usuario in usuarios]
    telegrams = (
        db.query(TelegramUsuario)
        .filter(
            TelegramUsuario.usuario_id.in_(usuario_ids),
            TelegramUsuario.activo == True,
        )
        .all()
        if usuario_ids
        else []
    )
    telegram_por_usuario = {str(telegram.usuario_id): telegram for telegram in telegrams}

    destinatarios = []
    for email in USUARIOS_NOTIFICACION_DGR:
        usuario = usuarios_por_email.get(email.lower())
        if not usuario:
            logger.warning("Usuario DGR %s no existe en la base", email)
            continue

        telegram_usuario = telegram_por_usuario.get(str(usuario.id))
        if not telegram_usuario:
            logger.warning("Usuario %s no tiene Telegram vinculado", email)
            continue

        destinatarios.append((email, telegram_usuario.chat_id))

    return destinatarios


def _construir_mensaje(tramite: TramiteDgr) -> str:
    """Arma el mensaje HTML de Telegram para un trámite con cambios."""
    lineas = [
        "<b>Cambio en trámite DGR</b>",
        f"<b>Registro:</b> {escape(tramite.registro_nombre or tramite.registro)}",
        f"<b>Oficina:</b> {escape(tramite.oficina_nombre or tramite.oficina)}",
        f"<b>Documento:</b> {tramite.anio}/{tramite.numero_entrada}",
        f"<b>Escribano:</b> {escape(tramite.escribano_emisor or 'Sin dato')}",
        (
            f"<b>Estado:</b> {escape(tramite.estado_anterior or 'Sin dato')} → "
            f"{escape(tramite.estado_actual or 'Sin dato')}"
        ),
    ]
    if tramite.observaciones:
        lineas.append(f"<b>Observaciones:</b> {escape(tramite.observaciones)}")
    return "\n".join(lineas)


async def _tarea_monitorear_tramites_dgr_async() -> None:
    """Ejecuta el monitoreo completo de trámites activos DGR."""
    db: Session = SessionLocal()
    total_consultados = 0
    cambios_detectados = 0
    notificaciones_enviadas = 0

    try:
        capsolver_api_key = Settings().capsolver_api_key
        if not capsolver_api_key:
            logger.warning("CAPSOLVER_API_KEY no configurada; las consultas DGR pueden fallar")

        tramites = (
            db.query(TramiteDgr)
            .filter(
                TramiteDgr.activo == True,
                TramiteDgr.deleted_at.is_(None),
            )
            .order_by(TramiteDgr.created_at.asc())
            .all()
        )

        logger.info("🔎 Monitoreando %s trámites DGR activos", len(tramites))

        for index, tramite in enumerate(tramites):
            try:
                total_consultados += 1
                resultado = await consultar_tramite_dgr(
                    tramite.registro,
                    tramite.oficina,
                    tramite.anio,
                    tramite.numero_entrada,
                    tramite.bis or "",
                )

                if resultado is None:
                    logger.warning(
                        "⚠️ DGR no devolvió datos para trámite %s (%s/%s)",
                        tramite.id,
                        tramite.anio,
                        tramite.numero_entrada,
                    )
                    continue

                estado_anterior = _normalizar_texto(tramite.estado_actual)
                estado_nuevo = _normalizar_texto(resultado.get("estado_actual"))
                observaciones_anteriores = _normalizar_texto(tramite.observaciones)
                observaciones_nuevas = _normalizar_texto(resultado.get("observaciones"))
                actos_nuevos = (
                    json.dumps(resultado.get("inscripciones"), ensure_ascii=False)
                    if resultado.get("inscripciones")
                    else None
                )
                actos_anteriores = tramite.actos

                hay_cambio_estado = estado_nuevo != estado_anterior
                hay_observaciones_nuevas = observaciones_nuevas != observaciones_anteriores
                hay_cambio_actos = _normalizar_texto(actos_nuevos) != _normalizar_texto(actos_anteriores)

                if hay_cambio_estado or hay_observaciones_nuevas or hay_cambio_actos:
                    _registrar_historial_cambio(
                        db,
                        tramite,
                        "estado_actual",
                        tramite.estado_actual,
                        resultado.get("estado_actual"),
                    )
                    _registrar_historial_cambio(
                        db,
                        tramite,
                        "observaciones",
                        tramite.observaciones,
                        resultado.get("observaciones"),
                    )
                    _registrar_historial_cambio(
                        db,
                        tramite,
                        "actos",
                        tramite.actos,
                        actos_nuevos,
                    )
                    tramite.estado_anterior = tramite.estado_actual
                    tramite.cambio_detectado = True
                    cambios_detectados += 1

                _aplicar_datos_dgr(tramite, resultado)
                db.commit()

            except Exception as exc:
                db.rollback()
                logger.error(
                    "❌ Error monitoreando trámite DGR %s (%s/%s): %s",
                    tramite.id,
                    tramite.anio,
                    tramite.numero_entrada,
                    exc,
                    exc_info=True,
                )
            finally:
                if index < len(tramites) - 1:
                    await asyncio.sleep(15)

        pendientes = (
            db.query(TramiteDgr)
            .filter(
                TramiteDgr.cambio_detectado == True,
                TramiteDgr.deleted_at.is_(None),
            )
            .order_by(TramiteDgr.ultimo_chequeo.desc())
            .all()
        )

        destinatarios = _obtener_destinatarios_notificacion(db)
        if not destinatarios:
            logger.warning("⚠️ No hay destinatarios Telegram configurados para notificaciones DGR")
        else:
            for tramite in pendientes:
                mensaje = _construir_mensaje(tramite)
                enviados_ok = 0

                for email, chat_id in destinatarios:
                    if await enviar_mensaje_telegram(chat_id, mensaje):
                        enviados_ok += 1
                        notificaciones_enviadas += 1
                    else:
                        logger.error(
                            "❌ Error notificando trámite DGR %s a %s por Telegram",
                            tramite.id,
                            email,
                        )

                if enviados_ok == len(destinatarios):
                    tramite.cambio_detectado = False
                    tramite.updated_at = datetime.now(timezone.utc)
                    db.commit()
                else:
                    db.rollback()

        logger.info(
            "✅ Monitoreo DGR completado: %s consultados, %s cambios detectados, %s notificaciones enviadas",
            total_consultados,
            cambios_detectados,
            notificaciones_enviadas,
        )

    finally:
        db.close()


def tarea_monitorear_tramites_dgr() -> None:
    """Wrapper sync para que APScheduler ejecute la tarea async de DGR."""
    logger.info("🕗 Ejecutando tarea programada: monitoreo de trámites DGR")
    asyncio.run(_tarea_monitorear_tramites_dgr_async())
