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


def tarea_sincronizar_expedientes():
    """Tarea programada: sincroniza todos los expedientes."""
    logger.info("🕗 Ejecutando tarea programada: sincronización de expedientes")
    
    db: Session = SessionLocal()
    try:
        resultado = sincronizar_todos_los_expedientes(db)
        logger.info(
            f"✅ Tarea completada: {resultado['sincronizados_ok']}/{resultado['total_expedientes']} "
            f"expedientes, {resultado['total_nuevos_movimientos']} nuevos movimientos"
        )
    except Exception as e:
        logger.error(f"❌ Error en tarea programada: {e}")
    finally:
        db.close()


def iniciar_scheduler():
    """Inicia el scheduler con las tareas programadas."""
    # Tarea: sincronizar expedientes a las 8:00 AM Uruguay
    scheduler.add_job(
        tarea_sincronizar_expedientes,
        CronTrigger(hour=8, minute=0, timezone=TZ_URUGUAY),
        id="sync_expedientes_diario",
        name="Sincronización diaria de expedientes",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("📅 Scheduler iniciado - Próxima ejecución: 8:00 AM (Uruguay)")


def detener_scheduler():
    """Detiene el scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("📅 Scheduler detenido")

