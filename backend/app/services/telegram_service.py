"""Servicio de notificaciones vía Telegram Bot API.

Usa httpx directo contra la API de Telegram (sin librerías de terceros).
Bot: @Cfo_inteligente_bot
"""

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org"


async def enviar_mensaje_telegram(chat_id: int, texto: str) -> bool:
    """Envía un mensaje de texto a un chat de Telegram.

    Args:
        chat_id: ID numérico del chat/usuario destino.
        texto: Contenido del mensaje (soporta HTML básico).

    Returns:
        True si el mensaje se envió correctamente, False si falló.
    """
    token = settings.telegram_bot_token
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN no configurado")
        return False

    url = f"{TELEGRAM_API}/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "HTML",
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            data = resp.json()

        if resp.status_code == 200 and data.get("ok"):
            logger.info("Mensaje Telegram enviado a chat_id=%d", chat_id)
            return True

        logger.error(
            "Telegram API error: status=%d description=%s",
            resp.status_code,
            data.get("description", "sin detalle"),
        )
        return False

    except httpx.HTTPError as e:
        logger.error("Error HTTP enviando mensaje Telegram a %d: %s", chat_id, e)
        return False
    except Exception as e:
        logger.error("Error inesperado enviando mensaje Telegram a %d: %s", chat_id, e)
        return False


async def enviar_mensaje_a_varios(chat_ids: list[int], texto: str) -> dict:
    """Envía el mismo mensaje a múltiples chats de Telegram.

    Args:
        chat_ids: Lista de IDs de chat destino.
        texto: Contenido del mensaje.

    Returns:
        {"enviados": N, "fallidos": N, "total": N}
    """
    enviados = 0
    fallidos = 0

    for chat_id in chat_ids:
        ok = await enviar_mensaje_telegram(chat_id, texto)
        if ok:
            enviados += 1
        else:
            fallidos += 1

    total = len(chat_ids)
    logger.info(
        "Telegram batch: %d/%d enviados, %d fallidos",
        enviados, total, fallidos,
    )

    return {"enviados": enviados, "fallidos": fallidos, "total": total}
