"""
Scheduler de monitoreo para trámites DGR.

Consulta periódicamente la DGR, detecta cambios y envía notificaciones
por WhatsApp cuando hay novedades en trámites activos.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.tramite_dgr import TramiteDgr
from app.services import twilio_service
from app.services.dgr_service import consultar_tramite_dgr

logger = logging.getLogger(__name__)


def _parse_fecha_ingreso(fecha_str: Optional[str]):
    """Parsea fecha_ingreso devuelta por la DGR."""
    if not fecha_str:
        return None

    for fmt in ("%d/%m/%y", "%d/%m/%Y"):
        try:
            return datetime.strptime(fecha_str, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def _normalizar_texto(value: Optional[str]) -> str:
    """Normaliza strings para comparar cambios de estado y observaciones."""
    return " ".join(str(value or "").split())


def _aplicar_datos_dgr(tramite: TramiteDgr, datos: dict) -> None:
    """Aplica al modelo los datos nuevos devueltos por la consulta DGR."""
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


def _obtener_numeros_notificacion() -> list[str]:
    """Lee la lista de números de WhatsApp desde el entorno."""
    numeros_str = os.getenv("TWILIO_NOTIFY_NUMBERS", "")
    return [numero.strip() for numero in numeros_str.split(",") if numero.strip()]


def _construir_mensaje(tramite: TramiteDgr) -> str:
    """Arma el mensaje de WhatsApp para un trámite con cambios."""
    lineas = [
        "🔔 *Cambio en trámite DGR*",
        f"📋 {tramite.registro_nombre or tramite.registro} - {tramite.oficina_nombre or tramite.oficina}",
        f"📄 Documento: {tramite.anio}/{tramite.numero_entrada}",
        f"📝 Escribano: {tramite.escribano_emisor or 'Sin dato'}",
        f"⚠️ Estado: {tramite.estado_anterior or 'Sin dato'} → {tramite.estado_actual or 'Sin dato'}",
    ]
    if tramite.observaciones:
        lineas.append(f"❗ Observaciones: {tramite.observaciones}")
    return "\n".join(lineas)


async def _tarea_monitorear_tramites_dgr_async() -> None:
    """Ejecuta el monitoreo completo de trámites activos DGR."""
    db: Session = SessionLocal()
    total_consultados = 0
    cambios_detectados = 0
    notificaciones_enviadas = 0

    try:
        capsolver_api_key = os.getenv("CAPSOLVER_API_KEY")
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

                hay_cambio_estado = bool(estado_nuevo) and estado_nuevo != estado_anterior
                hay_observaciones_nuevas = (
                    bool(observaciones_nuevas) and observaciones_nuevas != observaciones_anteriores
                )

                if hay_cambio_estado or hay_observaciones_nuevas:
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
                    time.sleep(15)

        pendientes = (
            db.query(TramiteDgr)
            .filter(
                TramiteDgr.cambio_detectado == True,
                TramiteDgr.deleted_at.is_(None),
            )
            .order_by(TramiteDgr.ultimo_chequeo.desc())
            .all()
        )

        numeros = _obtener_numeros_notificacion()
        if not numeros:
            logger.warning("⚠️ TWILIO_NOTIFY_NUMBERS no configurado; no se enviarán notificaciones DGR")
        else:
            for tramite in pendientes:
                mensaje = _construir_mensaje(tramite)
                enviados_ok = 0

                for numero in numeros:
                    resultado = twilio_service.enviar_whatsapp(numero, mensaje)
                    if resultado.get("exito"):
                        enviados_ok += 1
                        notificaciones_enviadas += 1
                    else:
                        logger.error(
                            "❌ Error notificando trámite DGR %s a %s: %s",
                            tramite.id,
                            numero,
                            resultado.get("error"),
                        )

                if enviados_ok == len(numeros):
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
