"""
AIOrchestrator - Solo Claude (Anthropic)

Sistema simplificado que usa ÚNICAMENTE Claude como proveedor de IA.
Si Claude falla, reintenta hasta 3 veces con delay.
Si todos los reintentos fallan, retorna None con error claro.

Autor: Sistema CFO Inteligente
Fecha: Diciembre 2025
"""

import time
from typing import Optional

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class AIOrchestrator:
    """
    Orquestador de IA - Solo usa Claude (Anthropic).
    
    Configuración:
    - Modelo: claude-sonnet-4-20250514
    - Reintentos: 3 intentos con 2 segundos de delay
    - Timeout: 30 segundos por intento
    
    Ejemplo:
        >>> orchestrator = AIOrchestrator()
        >>> response = orchestrator.complete(
        ...     prompt="Genera SQL para...",
        ...     system_prompt="Eres un experto en SQL",
        ...     max_tokens=500
        ... )
        >>> if response:
        ...     print(response)
        ... else:
        ...     print("Claude no disponible")
    """
    
    # Configuración de Claude
    CLAUDE_MODEL = "claude-sonnet-4-20250514"
    DEFAULT_TIMEOUT = 45
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # segundos entre reintentos
    
    def __init__(self):
        """
        Inicializa cliente de Claude.
        Requiere ANTHROPIC_API_KEY en configuración.
        """
        self._client = None
        self._is_available = False
        
        if not settings.anthropic_api_key:
            logger.error("AIOrchestrator: ANTHROPIC_API_KEY no configurada")
            return
        
        try:
            import anthropic
            self._client = anthropic.Anthropic(
                api_key=settings.anthropic_api_key.strip()
            )
            self._is_available = True
            logger.info(f"AIOrchestrator: Claude inicializado ({self.CLAUDE_MODEL})")
        except ImportError:
            logger.error("AIOrchestrator: Módulo 'anthropic' no instalado")
        except Exception as e:
            logger.error(f"AIOrchestrator: Error inicializando Claude: {e}")
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.3,
        timeout: int = DEFAULT_TIMEOUT
    ) -> Optional[str]:
        """
        Genera respuesta usando Claude con reintentos automáticos.
        
        Args:
            prompt: Prompt del usuario
            system_prompt: Prompt de sistema (opcional)
            max_tokens: Máximo tokens a generar
            temperature: Creatividad (0.0-1.0)
            timeout: Timeout en segundos por intento
            
        Returns:
            String con respuesta o None si Claude falla
        """
        if not self._is_available:
            logger.error("AIOrchestrator: Claude no disponible")
            return None
        
        last_error = None
        
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                logger.info(f"AIOrchestrator: Claude intento {attempt}/{self.MAX_RETRIES}")
                
                # Construir kwargs
                kwargs = {
                    "model": self.CLAUDE_MODEL,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": [{"role": "user", "content": prompt}],
                    "timeout": timeout
                }
                
                if system_prompt:
                    kwargs["system"] = system_prompt
                
                # Llamar a Claude
                response = self._client.messages.create(**kwargs)
                result = response.content[0].text
                
                logger.info(f"AIOrchestrator: Claude respondió ({len(result)} chars) en intento {attempt}")
                return result
                
            except Exception as e:
                error_type = type(e).__name__
                last_error = str(e)[:200]
                logger.warning(f"AIOrchestrator: Claude intento {attempt} falló ({error_type}): {last_error}")
                
                # Si no es el último intento, esperar antes de reintentar
                if attempt < self.MAX_RETRIES:
                    logger.info(f"AIOrchestrator: Esperando {self.RETRY_DELAY}s antes de reintentar...")
                    time.sleep(self.RETRY_DELAY)
        
        # Todos los reintentos fallaron
        logger.error(f"AIOrchestrator: Claude falló después de {self.MAX_RETRIES} intentos. Último error: {last_error}")
        return None
    
    def get_available_providers(self) -> list:
        """Retorna lista de proveedores disponibles."""
        return ["claude"] if self._is_available else []
    
    def is_available(self) -> bool:
        """Retorna True si Claude está disponible."""
        return self._is_available
    
    def get_last_error(self) -> Optional[str]:
        """Retorna información sobre el estado del proveedor."""
        if not settings.anthropic_api_key:
            return "ANTHROPIC_API_KEY no configurada"
        if not self._is_available:
            return "Claude no pudo inicializarse"
        return None
