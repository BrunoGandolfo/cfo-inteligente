"""
Mail diario de actividad de registro: arma el mensaje a partir del resumen y
lo envía. Lo ejecuta el scheduler todos los días a las 20:00 (Uruguay).

Responsabilidades separadas:
  - resumen_actividad_service → obtiene los datos
  - este módulo                → los presenta (asunto, HTML, texto)
  - email_service              → los envía
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from html import escape

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.email_service import enviar_email
from app.services.resumen_actividad_service import (
    DIAS_SIN_CARGA_ALERTA,
    TZ_URUGUAY,
    AlertaLocalidad,
    ResumenActividad,
    obtener_resumen,
)

logger = logging.getLogger(__name__)

_DIAS_SEMANA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


@dataclass(frozen=True)
class MailResumen:
    asunto: str
    html: str
    texto: str


def _fecha_corta(momento: datetime) -> str:
    local = momento.astimezone(TZ_URUGUAY)
    return f"{_DIAS_SEMANA[local.weekday()]} {local.day}/{local.month}"


def _fecha_hora(momento: datetime) -> str:
    return f"{_fecha_corta(momento)} {momento.astimezone(TZ_URUGUAY):%H:%M}"


def _texto_alerta(alerta: AlertaLocalidad) -> str:
    if alerta.ultima_carga is None:
        return f"{alerta.localidad}: nunca tuvo operaciones cargadas"
    ultima = f"{alerta.ultima_carga.day}/{alerta.ultima_carga.month}"
    return f"{alerta.localidad}: sin cargas hace {alerta.dias_sin_carga} días (última: {ultima})"


def construir_mail(resumen: ResumenActividad) -> MailResumen:
    """Presenta el resumen como mail (HTML + texto plano). Sin cálculos."""
    asunto = f"Actividad de registro — {_fecha_corta(resumen.hasta)}"
    if resumen.sin_actividad:
        asunto += " (sin actividad)"
    if resumen.alertas:
        asunto += " ⚠️"

    periodo = f"Del {_fecha_hora(resumen.desde)} al {_fecha_hora(resumen.hasta)}"

    # Texto plano
    lineas = [asunto, periodo, ""]
    if resumen.sin_actividad:
        lineas.append("Sin actividad en el período.")
    for u in resumen.usuarios:
        lineas.append(
            f"{u.nombre} — cargadas: {u.creadas} · editadas: {u.editadas} · anuladas: {u.anuladas}"
        )
    if resumen.alertas:
        lineas += ["", f"Alertas (más de {DIAS_SIN_CARGA_ALERTA} días sin cargas):"]
        lineas += [f"- {_texto_alerta(a)}" for a in resumen.alertas]
    texto = "\n".join(lineas)

    # HTML
    celda = 'style="padding:6px 12px;border-bottom:1px solid #e5e7eb;"'
    celda_num = 'style="padding:6px 12px;border-bottom:1px solid #e5e7eb;text-align:right;"'
    if resumen.sin_actividad:
        cuerpo = "<p>Sin actividad en el período.</p>"
    else:
        filas = "".join(
            f"<tr><td {celda}>{escape(u.nombre)}</td>"
            f"<td {celda_num}>{u.creadas}</td>"
            f"<td {celda_num}>{u.editadas}</td>"
            f"<td {celda_num}>{u.anuladas}</td></tr>"
            for u in resumen.usuarios
        )
        cuerpo = (
            '<table style="border-collapse:collapse;font-size:14px;">'
            f"<tr><th {celda}>Usuario</th><th {celda_num}>Cargadas</th>"
            f"<th {celda_num}>Editadas</th><th {celda_num}>Anuladas</th></tr>"
            f"{filas}</table>"
        )
    alertas_html = ""
    if resumen.alertas:
        items = "".join(f"<li>{escape(_texto_alerta(a))}</li>" for a in resumen.alertas)
        alertas_html = (
            '<div style="margin-top:16px;padding:10px 14px;background:#fef3c7;'
            'border-left:4px solid #d97706;">'
            f"<strong>⚠️ Más de {DIAS_SIN_CARGA_ALERTA} días sin cargas</strong>"
            f"<ul style=\"margin:6px 0 0 0;\">{items}</ul></div>"
        )
    html = (
        '<div style="font-family:Arial,sans-serif;color:#111827;">'
        f"<h2 style=\"margin:0 0 4px 0;\">{escape(asunto)}</h2>"
        f"<p style=\"margin:0 0 16px 0;color:#6b7280;\">{escape(periodo)}</p>"
        f"{cuerpo}{alertas_html}</div>"
    )

    return MailResumen(asunto=asunto, html=html, texto=texto)


async def enviar_resumen_actividad(db: Session, hasta: datetime) -> bool:
    """Obtiene el resumen de las 24 h previas a `hasta` y lo envía por mail."""
    mail = construir_mail(obtener_resumen(db, hasta))
    return await enviar_email(
        settings.email_resumen_actividad, mail.asunto, mail.html, mail.texto,
    )


def tarea_enviar_resumen_actividad() -> None:
    """Tarea programada (20:00 Uruguay). Wrapper sync para APScheduler."""
    logger.info("🕗 Ejecutando tarea programada: resumen diario de actividad")
    db: Session = SessionLocal()
    try:
        enviado = asyncio.run(enviar_resumen_actividad(db, datetime.now(TZ_URUGUAY)))
        if enviado:
            logger.info("📧 Resumen de actividad enviado")
        else:
            logger.error("❌ No se pudo enviar el resumen de actividad")
    except Exception as e:
        logger.error(f"❌ Error en resumen de actividad: {e}", exc_info=True)
    finally:
        db.close()
