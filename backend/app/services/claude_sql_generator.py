"""
Generador de SQL con fallback multi-proveedor (Claude → OpenAI → Gemini)
Usa AIOrchestrator para mayor resiliencia
"""

from app.core.logger import get_logger
from app.core.constants import CLAUDE_MAX_TOKENS, CLAUDE_TEMPERATURE
from app.services.ai.ai_orchestrator import AIOrchestrator
from app.services.sql_generator_prompts import build_sql_system_prompt

logger = get_logger(__name__)


class ClaudeSQLGenerator:
    """Generador de SQL con fallback multi-proveedor: Claude → OpenAI → Gemini."""
    
    def __init__(self):
        self._orchestrator = AIOrchestrator()
        self._system_prompt = build_sql_system_prompt()
        logger.info("ClaudeSQLGenerator inicializado con AIOrchestrator")
    
    def generar_sql(self, pregunta: str, contexto: list = None) -> str:
        """
        Genera SQL usando IA con fallback multi-proveedor y memoria de conversación.
        
        Args:
            pregunta: Pregunta del usuario en lenguaje natural
            contexto: Lista de mensajes previos [{"role": "user|assistant", "content": "..."}]
            
        Returns:
            SQL válido de PostgreSQL o texto explicativo si no puede
        """
        contexto = contexto or []
        
        # Construir prompt completo
        prompt_completo = self._build_prompt(pregunta, contexto)

        try:
            # Usar AIOrchestrator con fallback automático
            sql_generado = self._orchestrator.complete(
                prompt=prompt_completo,
                max_tokens=CLAUDE_MAX_TOKENS,
                temperature=CLAUDE_TEMPERATURE
            )
            
            if not sql_generado:
                logger.error("AIOrchestrator retornó None - todos los proveedores fallaron")
                return "ERROR: Todos los proveedores de IA fallaron"
            
            sql_generado = self._limpiar_sql(sql_generado)
            logger.info(f"SQL generado con {len(contexto)} mensajes de contexto")
            
            return sql_generado
            
        except Exception as e:
            logger.error(f"Error en SQL Generator: {e}", exc_info=True)
            return f"ERROR: {str(e)}"
    
    def _build_prompt(self, pregunta: str, contexto: list) -> str:
        """Construye el prompt completo incluyendo sistema y contexto."""
        base_prompt = f"""{self._system_prompt}

INSTRUCCIONES:
• Genera SOLO el SQL query en PostgreSQL, sin explicaciones ni markdown
• El SQL debe ser ejecutable directamente
• SIEMPRE incluye WHERE deleted_at IS NULL"""
        
        if contexto:
            contexto_str = "\n\nCONTEXTO DE CONVERSACIÓN PREVIA:\n"
            for msg in contexto:
                role = "Usuario" if msg["role"] == "user" else "Asistente"
                content = msg['content'][:500] if len(msg['content']) > 500 else msg['content']
                contexto_str += f"{role}: {content}\n"
            return base_prompt + contexto_str + f"\n\nPREGUNTA ACTUAL: {pregunta}"
        
        return base_prompt + f"\n\nPREGUNTA: {pregunta}"
    
    def _limpiar_sql(self, sql: str) -> str:
        """Limpia SQL de markdown y espacios."""
        sql = sql.strip()
        if sql.startswith("```"):
            sql = sql.replace("```sql", "").replace("```", "").strip()
        return sql
