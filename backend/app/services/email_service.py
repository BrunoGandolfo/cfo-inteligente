"""Servicio de envío de mails vía Resend (API HTTPS).

Usa httpx directo contra la API de Resend (sin librerías de terceros), igual
que telegram_service. Nunca loguea la API key ni el contenido del mail.
"""

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


async def enviar_email(destinatario: str, asunto: str, html: str, texto: str) -> bool:
    """Envía un mail con versión HTML y texto plano.

    Args:
        destinatario: Dirección de destino.
        asunto: Asunto del mail.
        html: Cuerpo en HTML.
        texto: Cuerpo en texto plano (para clientes que no muestran HTML).

    Returns:
        True si Resend aceptó el mail, False si falló (nunca lanza excepción:
        un mail que no sale no debe tumbar la tarea que lo llama).
    """
    api_key = settings.resend_api_key
    if not api_key:
        logger.error("RESEND_API_KEY no configurada")
        return False

    payload = {
        "from": settings.email_remitente,
        "to": [destinatario],
        "subject": asunto,
        "html": html,
        "text": texto,
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                RESEND_API_URL,
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
            )

        if resp.status_code == 200:
            logger.info("Mail enviado a %s (id=%s)", destinatario, resp.json().get("id"))
            return True

        logger.error(
            "Resend API error: status=%d detalle=%s",
            resp.status_code,
            resp.text[:300],
        )
        return False

    except httpx.HTTPError as e:
        logger.error("Error HTTP enviando mail a %s: %s", destinatario, e)
        return False
    except Exception as e:
        logger.error("Error inesperado enviando mail a %s: %s", destinatario, e)
        return False
