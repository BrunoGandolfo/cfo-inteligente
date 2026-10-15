"""Cierre seguro de playwright para las consultas que abren un navegador.

Sin pw.stop() quedan vivos el driver de node y sus procesos; si además
browser.close() falla y corta el finally, tampoco se cierra el resto. Con días
de uptime eso agotó los threads del contenedor y tumbó el login (incidente
15/10/2026). Este helper cierra ambos siempre y nunca lanza.
"""

from typing import Any, Optional

from app.core.logger import get_logger

logger = get_logger(__name__)


async def cerrar_playwright(browser: Optional[Any], pw: Optional[Any], contexto: str) -> None:
    """Cierra el navegador y detiene playwright; un fallo en uno no impide el otro."""
    if browser:
        try:
            await browser.close()
        except Exception:
            logger.exception("Error cerrando navegador (%s)", contexto)
    if pw:
        try:
            await pw.stop()
        except Exception:
            logger.exception("Error deteniendo playwright (%s)", contexto)
