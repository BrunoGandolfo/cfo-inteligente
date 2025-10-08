"""
ClaudeClient - Wrapper para Anthropic API

Cliente robusto con manejo de errores, timeouts y rate limits.
Reutilizable fuera de este proyecto.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

import os
from typing import Optional
import anthropic
from anthropic import APITimeoutError, APIConnectionError, RateLimitError

from app.core.logger import get_logger

logger = get_logger(__name__)


class ClaudeClient:
    """
    Wrapper profesional para Anthropic API.
    
    RESPONSABILIDAD: Solo comunicación con Claude.
    REUTILIZABLE: Puede usarse en otros proyectos.
    
    Features:
    - Manejo robusto de errores
    - Timeout configurable
    - Logging de requests
    - Retry logic (opcional)
    
    Configuración:
    - API Key desde env var ANTHROPIC_API_KEY
    - Modelo default: claude-sonnet-4-20250514
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
    
    # Modelos disponibles (actualizado Octubre 2025)
    MODEL_SONNET_4 = "claude-sonnet-4-20250514"
    MODEL_OPUS_4 = "claude-opus-4-20250514"
    MODEL_HAIKU_4 = "claude-4-haiku-20250514"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = MODEL_SONNET_4
    ):
        """
        Constructor.
        
        Args:
            api_key: API key de Anthropic (si None, usa env var)
            model: Modelo a usar (default: Sonnet 4)
            
        Raises:
            ValueError: Si api_key no está disponible
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY no encontrada. "
                "Define variable de entorno o pasa api_key al constructor."
            )
        
        self.model = model
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        logger.info(f"ClaudeClient inicializado con modelo: {self.model}")
    
    def complete(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 600,
        timeout: int = 30,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Llama a Claude API con prompt.
        
        Args:
            prompt: Prompt de usuario
            temperature: Creatividad (0.0-1.0, default 0.3 para análisis)
            max_tokens: Máximo tokens a generar
            timeout: Timeout en segundos
            system_prompt: Prompt de sistema (opcional)
            
        Returns:
            String con respuesta de Claude
            
        Raises:
            APITimeoutError: Si excede timeout
            RateLimitError: Si excede rate limit
            APIConnectionError: Si hay problema de conexión
            Exception: Otros errores
            
        Nota:
            El caller debe manejar estas excepciones (generators lo hacen).
        """
        logger.info(
            f"Llamando Claude API: model={self.model}, "
            f"temp={temperature}, max_tokens={max_tokens}, timeout={timeout}s"
        )
        logger.debug(f"Prompt length: {len(prompt)} chars")
        
        try:
            # Construir mensaje
            messages = [{"role": "user", "content": prompt}]
            
            # Kwargs para API
            api_kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
                "timeout": timeout
            }
            
            # Agregar system prompt si existe
            if system_prompt:
                api_kwargs["system"] = system_prompt
            
            # Llamar API
            message = self.client.messages.create(**api_kwargs)
            
            # Extraer texto
            response_text = message.content[0].text
            
            logger.info(f"Claude API respondió: {len(response_text)} chars")
            logger.debug(f"Response preview: {response_text[:200]}...")
            
            return response_text
            
        except APITimeoutError as e:
            logger.error(f"Claude API timeout después de {timeout}s: {e}")
            raise
            
        except RateLimitError as e:
            logger.error(f"Claude API rate limit excedido: {e}")
            raise
            
        except APIConnectionError as e:
            logger.error(f"Claude API error de conexión: {e}")
            raise
            
        except Exception as e:
            logger.error(f"Claude API error inesperado: {type(e).__name__}: {e}")
            raise
    
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
        Llama a Claude API con reintentos automáticos.
        
        Útil para manejar errores transitorios (red, rate limits temporales).
        
        Args:
            prompt: Prompt de usuario
            temperature: Creatividad
            max_tokens: Máximo tokens
            timeout: Timeout por intento
            max_retries: Máximo de reintentos
            system_prompt: Prompt de sistema (opcional)
            
        Returns:
            String con respuesta de Claude
            
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
                
            except (APIConnectionError, RateLimitError) as e:
                # Errores recuperables
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
                    
            except APITimeoutError as e:
                # Timeout no es recuperable con retry (mismo timeout)
                logger.error(f"Timeout no recuperable: {e}")
                raise
                
            except Exception as e:
                # Otros errores no son recuperables
                logger.error(f"Error no recuperable: {e}")
                raise
        
        # Si llegamos aquí, todos los intentos fallaron
        raise last_error
    
    def get_model_info(self) -> dict:
        """
        Retorna información del modelo actual.
        
        Returns:
            Dict con info del modelo
        """
        return {
            "model": self.model,
            "is_sonnet": "sonnet" in self.model.lower(),
            "is_opus": "opus" in self.model.lower(),
            "is_haiku": "haiku" in self.model.lower()
        }

