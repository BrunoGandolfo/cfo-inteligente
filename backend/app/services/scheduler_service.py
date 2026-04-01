"""
Scheduler para tareas programadas.
Usa APScheduler con zona horaria Uruguay.
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
import pytz

from app.core.database import SessionLocal
from app.services.expediente_service import sincronizar_todos_los_expedientes

logger = logging.getLogger(__name__)

# Zona horaria Uruguay
TZ_URUGUAY = pytz.timezone("America/Montevideo")

# Scheduler global
scheduler = AsyncIOScheduler(timezone=TZ_URUGUAY)


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
    """Envía notificaciones de movimientos pendientes a todos los socios."""
    from app.services.expediente_service import obtener_movimientos_sin_notificar, marcar_movimientos_notificados
    from app.services import twilio_service
    
    movimientos = obtener_movimientos_sin_notificar(db)
    
    if not movimientos:
        logger.info("📭 Sin movimientos pendientes de notificar")
        return
    
    # Enviar a todos los socios
    resultado = twilio_service.notificar_a_todos_los_socios(movimientos)
    
    if resultado["enviados_ok"] > 0:
        # Marcar como notificados si al menos un envío fue exitoso
        ids = [m["movimiento_id"] for m in movimientos]
        marcar_movimientos_notificados(db, ids)
        logger.info(f"📱 Notificaciones: {resultado['enviados_ok']}/{resultado['total_numeros']} socios notificados")
    else:
        logger.error(f"❌ Falló el envío a todos los socios")


def iniciar_scheduler() -> None:
    """Inicia el scheduler con las tareas programadas."""
    # Tarea: sincronizar expedientes a las 7:30 AM Uruguay
    scheduler.add_job(
        tarea_sincronizar_expedientes,
        CronTrigger(hour=7, minute=30, timezone=TZ_URUGUAY),
        id="sync_expedientes_diario",
        name="Sincronización diaria de expedientes",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("📅 Scheduler iniciado - Próxima ejecución: 7:30 AM (Uruguay)")


def detener_scheduler() -> None:
    """Detiene el scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("📅 Scheduler detenido")

