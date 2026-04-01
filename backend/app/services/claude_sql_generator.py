"""
Generador de SQL con Claude — System/User split para prompt caching
Usa AIOrchestrator con system_prompt separado para mayor adherencia a reglas.
"""

from datetime import date

from app.core.logger import get_logger
from app.core.constants import CLAUDE_MAX_TOKENS, CLAUDE_TEMPERATURE
from app.services.ai.ai_orchestrator import AIOrchestrator
from app.services.sql_generator_prompts import build_sql_system_prompt

logger = get_logger(__name__)


class ClaudeSQLGenerator:
    """Generador de SQL con system/user split: reglas como system, pregunta como user."""

    def __init__(self) -> None:
        """Inicializa el orquestador y el prompt de sistema persistente."""
        self._orchestrator = AIOrchestrator()
        self._system_prompt = build_sql_system_prompt()
        logger.info("ClaudeSQLGenerator inicializado con AIOrchestrator (system/user split)")

    def generar_sql(
        self,
        pregunta: str,
        contexto: list[dict[str, str]] | None = None
    ) -> str:
        """
        Genera SQL usando Claude con system/user split.

        El modelo mental (esquema, reglas, mapa de navegacion) va como system message
        (mayor adherencia, cacheable). La pregunta y contexto van como user message.

        Args:
            pregunta: Pregunta del usuario en lenguaje natural
            contexto: Lista de mensajes previos [{"role": "user|assistant", "content": "..."}]

        Returns:
            SQL valido de PostgreSQL o texto explicativo si no puede
        """
        contexto = contexto or []

        # Construir user prompt (solo la parte dinamica)
        user_prompt = self._build_user_prompt(pregunta, contexto)

        try:
            # System/user split: reglas como system, pregunta como user
            sql_generado = self._orchestrator.complete(
                prompt=user_prompt,
                system_prompt=self._system_prompt,
                max_tokens=CLAUDE_MAX_TOKENS,
                temperature=CLAUDE_TEMPERATURE
            )

            if not sql_generado:
                logger.error("AIOrchestrator retorno None - todos los proveedores fallaron")
                return "ERROR: Todos los proveedores de IA fallaron"

            sql_generado = self._limpiar_sql(sql_generado)
            logger.info(f"SQL generado con {len(contexto)} mensajes de contexto")

            return sql_generado

        except Exception as e:
            logger.error(f"Error en SQL Generator: {e}", exc_info=True)
            return f"ERROR: {str(e)}"

    def _build_user_prompt(self, pregunta: str, contexto: list[dict[str, str]]) -> str:
        """Construye el user message: solo fecha, contexto conversacional y pregunta."""
        partes = [f"Fecha actual: {date.today().isoformat()}"]

        if contexto:
            partes.append("\nCONTEXTO DE CONVERSACION PREVIA:")
            for msg in contexto:
                role = "Usuario" if msg["role"] == "user" else "Asistente"
                content = msg['content'][:500] if len(msg['content']) > 500 else msg['content']
                partes.append(f"{role}: {content}")

        partes.append(f"\nPREGUNTA: {pregunta}")
        partes.append("\nGenera SOLO el SQL query en PostgreSQL, sin explicaciones ni markdown.")
        return "\n".join(partes)

    def _limpiar_sql(self, sql: str) -> str:
        """Limpia SQL de markdown y espacios."""
        sql = sql.strip()
        if sql.startswith("```"):
            sql = sql.replace("```sql", "").replace("```", "").strip()
        return sql
