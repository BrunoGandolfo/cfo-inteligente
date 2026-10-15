"""
Interruptores de funcionalidades que dependen de servicios externos.

Una funcionalidad está habilitada solo si (1) su flag está en true Y (2) su
credencial está configurada. Ambas condiciones a propósito: el flag es la
decisión explícita de prenderla; la credencial evita prender algo que no
puede funcionar (como pasó con la DGR, que corrió meses sin clave de
CapSolver y cada intento dejaba procesos colgados: incidente 15/10/2026).

Qué está apagado, por qué y cómo prenderlo: docs/FUNCIONALIDADES_DESACTIVADAS.md
"""

from fastapi import HTTPException, status

from app.core.config import settings


def dgr_habilitado() -> bool:
    """Consultas a la DGR (monitoreo automático y sincronización manual)."""
    return settings.dgr_habilitado and bool(settings.capsolver_api_key)


def dgi_consultas_habilitadas() -> bool:
    """Consultas DGI del módulo Contable (todas resuelven captcha con CapSolver)."""
    return settings.dgi_consultas_habilitadas and bool(settings.capsolver_api_key)


def telegram_habilitado() -> bool:
    """Notificaciones y vinculación de usuarios por Telegram."""
    return settings.telegram_habilitado and bool(settings.telegram_bot_token)


_MOTIVOS = {
    "dgr": "Consultas a la DGR desactivadas: requieren configurar CapSolver.",
    "dgi": "Consultas DGI desactivadas: requieren configurar CapSolver.",
    "telegram": "Notificaciones por Telegram desactivadas: requieren configurar el bot.",
}

_ESTADO = {
    "dgr": dgr_habilitado,
    "dgi": dgi_consultas_habilitadas,
    "telegram": telegram_habilitado,
}


def exigir_habilitada(funcionalidad: str) -> None:
    """Corta el request con 503 y un motivo claro si la funcionalidad está apagada."""
    if not _ESTADO[funcionalidad]():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_MOTIVOS[funcionalidad],
        )


def resumen_estado() -> dict[str, bool]:
    """Estado de cada interruptor, para loguear al arrancar."""
    return {nombre: estado() for nombre, estado in _ESTADO.items()}
