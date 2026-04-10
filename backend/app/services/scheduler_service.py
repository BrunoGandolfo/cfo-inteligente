"""
Scheduler para tareas programadas.
Usa APScheduler con zona horaria Uruguay.
"""

import asyncio
from collections import defaultdict
from html import escape
from uuid import UUID

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
import pytz

from app.core.database import SessionLocal
from app.core.logger import get_logger
from app.models.expediente import Expediente
from app.models.telegram_usuario import TelegramUsuario
from app.services.dgr_scheduler_service import tarea_monitorear_tramites_dgr
from app.services.expediente_service import sincronizar_todos_los_expedientes
from app.services.telegram_service import enviar_mensaje_telegram

logger = get_logger(__name__)

# Zona horaria Uruguay
TZ_URUGUAY = pytz.timezone("America/Montevideo")

# Scheduler global
scheduler = AsyncIOScheduler(timezone=TZ_URUGUAY)


def _formatear_fecha(valor) -> str:
    """Formatea fechas de movimientos para notificaciones Telegram."""
    return valor.strftime("%d/%m/%Y") if valor else "Sin fecha"


def _construir_mensaje_expediente(expediente: Expediente, movimientos: list[dict]) -> str:
    """Construye el mensaje Telegram HTML para movimientos de un expediente."""
    lineas = [
        "<b>Nuevos movimientos en expediente</b>",
        f"<b>IUE:</b> {escape(expediente.iue)}",
        f"<b>Carátula:</b> {escape(expediente.caratula or 'Sin carátula')}",
        "",
        "<b>Movimientos detectados:</b>",
    ]

    movimientos_ordenados = sorted(
        movimientos,
        key=lambda movimiento: (
            movimiento.get("fecha") is not None,
            movimiento.get("fecha"),
        ),
        reverse=True,
    )
    for movimiento in movimientos_ordenados:
        lineas.extend(
            [
                f"• <b>Fecha:</b> {_formatear_fecha(movimiento.get('fecha'))}",
                f"  <b>Tipo:</b> {escape(movimiento.get('tipo') or 'Sin tipo')}",
                f"  <b>Decreto:</b> {escape(movimiento.get('decreto') or 'Sin decreto')}",
                f"  <b>Vencimiento:</b> {_formatear_fecha(movimiento.get('vencimiento'))}",
            ]
        )

    return "\n".join(lineas)


def tarea_sincronizar_expedientes() -> None:
    """Tarea programada: sincroniza expedientes y envía notificaciones."""
    logger.info("🕗 Ejecutando tarea programada: sincronización de expedientes")
    
    db: Session = SessionLocal()
    try:
        # 1. Sincronizar expedientes
        resultado = sincronizar_todos_los_expedientes(db)
        logger.info(
            f"✅ Sincronización: {resultado['sincronizados_ok']}/{resultado['total_expedientes']} "
            f"expedientes, {resultado['total_nuevos_movimientos']} nuevos movimientos"
        )
        
        # 2. Enviar notificaciones si hay nuevos movimientos
        if resultado['total_nuevos_movimientos'] > 0:
            enviar_notificaciones_pendientes(db)
            
    except Exception as e:
        logger.error(f"❌ Error en tarea programada: {e}", exc_info=True)
    finally:
        db.close()


def enviar_notificaciones_pendientes(db: Session) -> None:
    """Envía notificaciones Telegram de movimientos al responsable de cada expediente."""
    from app.services.expediente_service import obtener_movimientos_sin_notificar, marcar_movimientos_notificados

    movimientos = obtener_movimientos_sin_notificar(db)

    if not movimientos:
        logger.info("📭 Sin movimientos pendientes de notificar")
        return

    movimientos_por_expediente: dict[str, list[dict]] = defaultdict(list)
    for movimiento in movimientos:
        movimientos_por_expediente[movimiento["expediente_id"]].append(movimiento)

    expediente_ids = [UUID(expediente_id) for expediente_id in movimientos_por_expediente]
    expedientes = (
        db.query(Expediente)
        .filter(Expediente.id.in_(expediente_ids))
        .all()
    )
    expedientes_por_id = {str(expediente.id): expediente for expediente in expedientes}

    responsable_ids = [
        expediente.responsable_id
        for expediente in expedientes
        if expediente.responsable_id is not None
    ]
    telegrams = (
        db.query(TelegramUsuario)
        .filter(
            TelegramUsuario.usuario_id.in_(responsable_ids),
            TelegramUsuario.activo == True,
        )
        .all()
        if responsable_ids
        else []
    )
    telegram_por_usuario = {str(telegram.usuario_id): telegram for telegram in telegrams}

    movimientos_notificados: list[str] = []
    expedientes_notificados = 0

    for expediente_id, movimientos_expediente in movimientos_por_expediente.items():
        expediente = expedientes_por_id.get(expediente_id)
        if not expediente:
            logger.warning("Expediente %s no encontrado al enviar notificación Telegram", expediente_id)
            continue

        if not expediente.responsable_id:
            logger.warning("Expediente %s no tiene responsable asignado", expediente.iue)
            continue

        telegram_usuario = telegram_por_usuario.get(str(expediente.responsable_id))
        if not telegram_usuario:
            logger.warning(
                "Usuario %s no tiene Telegram vinculado",
                expediente.responsable_id,
            )
            continue

        mensaje = _construir_mensaje_expediente(expediente, movimientos_expediente)
        enviado = asyncio.run(enviar_mensaje_telegram(telegram_usuario.chat_id, mensaje))

        if not enviado:
            logger.error("❌ Falló notificación Telegram para expediente %s", expediente.iue)
            continue

        movimientos_notificados.extend(
            movimiento["movimiento_id"] for movimiento in movimientos_expediente
        )
        expedientes_notificados += 1

    if movimientos_notificados:
        actualizados = marcar_movimientos_notificados(db, movimientos_notificados)
        logger.info(
            "📱 Notificaciones Telegram: %s expedientes, %s movimientos marcados como notificados",
            expedientes_notificados,
            actualizados,
        )
    else:
        logger.error("❌ No se pudo enviar ninguna notificación de expedientes por Telegram")


def iniciar_scheduler() -> None:
    """Inicia el scheduler con las tareas programadas."""
    # Tarea: sincronizar expedientes a las 7:30 AM Uruguay
    scheduler.add_job(
        tarea_sincronizar_expedientes,
        CronTrigger(hour=7, minute=30, timezone=TZ_URUGUAY),
        id="sync_expedientes_diario",
        name="Sincronización diaria de expedientes",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=300,
    )

    # Tarea: monitorear trámites DGR cada 4 horas
    scheduler.add_job(
        tarea_monitorear_tramites_dgr,
        "interval",
        hours=4,
        id="monitorear_tramites_dgr",
        name="Monitorear trámites DGR",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=300,
    )
    
    scheduler.start()
    logger.info("📅 Scheduler iniciado - Expedientes 7:30 AM, DGR cada 4 horas (Uruguay)")


def detener_scheduler() -> None:
    """Detiene el scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("📅 Scheduler detenido")
