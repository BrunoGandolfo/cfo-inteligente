"""
Dependencies - Dependency Injection Container

Provee dependencias para endpoints FastAPI.
Implementa patrón Singleton donde necesario.
"""

import os
from functools import lru_cache

from app.core.database import get_db  # noqa: F401 — re-export para uso en routers
from app.services.ai.claude_client import ClaudeClient
from app.core.logger import get_logger

logger = get_logger(__name__)


@lru_cache()
def get_claude_client() -> ClaudeClient:
    """
    Provee Claude client (singleton vía lru_cache).

    Returns:
        ClaudeClient configurado

    Raises:
        ValueError: Si ANTHROPIC_API_KEY no está definida
    """
    api_key = os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        logger.warning("ANTHROPIC_API_KEY no configurada - insights usarán fallback")
        raise ValueError(
            "ANTHROPIC_API_KEY no configurada. "
            "Definir en .env o variable de entorno."
        )

    client = ClaudeClient(api_key=api_key)
    logger.info("Claude client inicializado (singleton)")

    return client
