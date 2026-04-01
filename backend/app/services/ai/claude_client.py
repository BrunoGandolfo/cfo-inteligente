"""
ClaudeClient - Wrapper de compatibilidad sobre AIOrchestrator

Usa AIOrchestrator internamente para centralizar el acceso a Claude.
Mantiene compatibilidad con código existente.

Autor: Sistema CFO Inteligente
Fecha: Diciembre 2025
"""

from typing import Optional

from app.core.constants import CLAUDE_MODEL
from app.core.logger import get_logger

logger = get_logger(__name__)


class ClaudeClient:
    """
    Wrapper de IA sobre Claude.
    
    Usa AIOrchestrator internamente para centralizar:
    1. Cliente Anthropic
    2. Reintentos
    3. Logging y compatibilidad hacia atrás
    
    Features:
    - Reintentos automáticos vía AIOrchestrator
    - Timeout configurable
    - Logging detallado
    - Compatibilidad hacia atrás (misma firma de métodos)
    
    Configuración:
    - API Key desde env var ANTHROPIC_API_KEY
    - Modelo default: CLAUDE_MODEL (desde constants.py)
    - Timeout default: 30 segundos
    
    Ejemplo:
        >>> client = ClaudeClient()
        >>> response = client.complete(
        ...     prompt="Analiza estos datos: ...",
        ...     temperature=0.3,
        ...     max_tokens=600
        ... )
        >>> print(response)
        "Análisis: Los ingresos aumentaron..."
    """
    
    # Modelo centralizado desde constants.py
    MODEL_SONNET_4 = CLAUDE_MODEL
    
    # Singleton del orchestrator (compartido entre instancias)
    _orchestrator = None
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = MODEL_SONNET_4
    ):
        """
        Constructor.
        Inicializa AIOrchestrator para acceso a Claude.
        
        Args:
            api_key: API key de Anthropic (ignorado, usa config)
            model: Modelo preferido (para logging)
            
        Raises:
            ValueError: Si Claude no está disponible
        """
        self.model = model
        
        # Inicializar AIOrchestrator (singleton para reutilizar conexiones)
        if ClaudeClient._orchestrator is None:
            try:
                from app.services.ai.ai_orchestrator import AIOrchestrator
                ClaudeClient._orchestrator = AIOrchestrator()
                logger.info("ClaudeClient: AIOrchestrator inicializado para Claude")
            except Exception as e:
                logger.warning(f"ClaudeClient: No se pudo inicializar AIOrchestrator: {e}")
                ClaudeClient._orchestrator = None
        
        # Verificar disponibilidad de Claude
        if ClaudeClient._orchestrator and not ClaudeClient._orchestrator.is_available():
            raise ValueError(
                "Claude no disponible. "
                "Configura ANTHROPIC_API_KEY."
            )
        
        logger.info(f"ClaudeClient inicializado (modelo preferido: {self.model})")
    
    def complete(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 600,
        timeout: int = 30,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Genera respuesta usando Claude vía AIOrchestrator.
        
        Args:
            prompt: Prompt de usuario
            temperature: Creatividad (0.0-1.0, default 0.3 para análisis)
            max_tokens: Máximo tokens a generar
            timeout: Timeout en segundos
            system_prompt: Prompt de sistema (opcional)
            
        Returns:
            String con respuesta
            
        Raises:
            Exception: Si Claude falla
        """
        logger.info(
            f"ClaudeClient.complete(): "
            f"temp={temperature}, max_tokens={max_tokens}, timeout={timeout}s"
        )
        
        # Usar AIOrchestrator para centralizar acceso a Claude
        if ClaudeClient._orchestrator:
            response_text = ClaudeClient._orchestrator.complete(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout
            )
            
            if response_text:
                return response_text
            else:
                raise Exception("Claude no pudo responder después de los reintentos configurados")
        else:
            raise ValueError("AIOrchestrator no inicializado - Claude no disponible")
    
    def complete_with_retry(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 600,
        timeout: int = 30,
        max_retries: int = 3,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Genera respuesta con reintentos.
        
        Útil para manejar errores transitorios (red, rate limits temporales).
        
        Args:
            prompt: Prompt de usuario
            temperature: Creatividad
            max_tokens: Máximo tokens
            timeout: Timeout por intento
            max_retries: Máximo de reintentos
            system_prompt: Prompt de sistema (opcional)
            
        Returns:
            String con respuesta
            
        Raises:
            Exception: Si todos los reintentos fallan
        """
        import time
        
        last_error = None
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Intento {attempt}/{max_retries}")
                
                return self.complete(
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout,
                    system_prompt=system_prompt
                )
                
            except Exception as e:
                last_error = e
                logger.warning(f"Intento {attempt} falló: {e}")
                
                if attempt < max_retries:
                    # Backoff exponencial: 2s, 4s, 8s
                    wait_time = 2 ** attempt
                    logger.info(f"Esperando {wait_time}s antes de reintentar...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Todos los intentos fallaron")
                    raise last_error
        
        # Si llegamos aquí, todos los intentos fallaron
        raise last_error
    
    def get_model_info(self) -> dict:
        """
        Retorna información del modelo actual.
        
        Returns:
            Dict con info del modelo y estado del orchestrator
        """
        info = {
            "model": self.model,
            "is_sonnet": "sonnet" in self.model.lower(),
            "is_opus": "opus" in self.model.lower(),
            "is_haiku": "haiku" in self.model.lower(),
            "fallback_enabled": ClaudeClient._orchestrator is not None
        }
        
        # Agregar proveedores disponibles si hay orchestrator
        if ClaudeClient._orchestrator:
            info["available_providers"] = ClaudeClient._orchestrator.get_available_providers()
        
        return info
