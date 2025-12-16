"""
AIOrchestrator - Fallback inteligente entre proveedores de IA

Intenta proveedores en orden: Claude → OpenAI → Gemini
Si uno falla (timeout, rate limit, error), pasa al siguiente.

Autor: Sistema CFO Inteligente
Fecha: Diciembre 2025
"""

from typing import Optional
import time

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class AIOrchestrator:
    """
    Orquestador de proveedores de IA con fallback automático.
    
    Orden de prioridad:
    1. Claude (Anthropic) - claude-sonnet-4-5-20250929
    2. OpenAI - gpt-4o-mini
    3. Gemini (Google) - gemini-1.5-flash
    
    Cada proveedor tiene timeout de 30 segundos.
    Si todos fallan, retorna None.
    
    Ejemplo:
        >>> orchestrator = AIOrchestrator()
        >>> response = orchestrator.complete(
        ...     prompt="Analiza estos datos...",
        ...     system_prompt="Eres un analista financiero",
        ...     max_tokens=500
        ... )
        >>> print(response)
        "El análisis muestra..."
    """
    
    # Modelos por proveedor
    CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
    OPENAI_MODEL = "gpt-3.5-turbo"
    GEMINI_MODEL = "gemini-1.5-flash"
    
    # Timeout por proveedor (segundos)
    DEFAULT_TIMEOUT = 30
    
    def __init__(self):
        """
        Inicializa clientes de cada proveedor disponible.
        Solo inicializa proveedores con API key configurada.
        """
        self._claude_client = None
        self._openai_client = None
        self._gemini_model = None
        
        # Inicializar Claude si hay API key
        if settings.anthropic_api_key:
            try:
                import anthropic
                self._claude_client = anthropic.Anthropic(
                    api_key=settings.anthropic_api_key.strip()
                )
                logger.info("AIOrchestrator: Claude inicializado")
            except Exception as e:
                logger.warning(f"AIOrchestrator: No se pudo inicializar Claude: {e}")
        
        # Inicializar OpenAI si hay API key
        if settings.openai_api_key:
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(
                    api_key=settings.openai_api_key.strip()
                )
                logger.info("AIOrchestrator: OpenAI inicializado")
            except Exception as e:
                logger.warning(f"AIOrchestrator: No se pudo inicializar OpenAI: {e}")
        
        # Inicializar Gemini si hay API key
        if settings.google_ai_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.google_ai_key.strip())
                self._gemini_model = genai.GenerativeModel(self.GEMINI_MODEL)
                logger.info("AIOrchestrator: Gemini inicializado")
            except Exception as e:
                logger.warning(f"AIOrchestrator: No se pudo inicializar Gemini: {e}")
        
        # Log resumen
        providers = []
        if self._claude_client:
            providers.append("Claude")
        if self._openai_client:
            providers.append("OpenAI")
        if self._gemini_model:
            providers.append("Gemini")
        
        if providers:
            logger.info(f"AIOrchestrator: Proveedores disponibles: {', '.join(providers)}")
        else:
            logger.error("AIOrchestrator: NINGÚN proveedor de IA disponible")
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.3,
        timeout: int = DEFAULT_TIMEOUT
    ) -> Optional[str]:
        """
        Genera respuesta usando fallback entre proveedores.
        
        Args:
            prompt: Prompt del usuario
            system_prompt: Prompt de sistema (opcional)
            max_tokens: Máximo tokens a generar
            temperature: Creatividad (0.0-1.0)
            timeout: Timeout en segundos por proveedor
            
        Returns:
            String con respuesta o None si todos los proveedores fallan
        """
        start_time = time.time()
        
        # Intento 1: Claude
        if self._claude_client:
            result = self._try_claude(prompt, system_prompt, max_tokens, temperature, timeout)
            if result:
                return result
        
        # Intento 2: OpenAI
        if self._openai_client:
            result = self._try_openai(prompt, system_prompt, max_tokens, temperature, timeout)
            if result:
                return result
        
        # Intento 3: Gemini
        if self._gemini_model:
            result = self._try_gemini(prompt, system_prompt, max_tokens, temperature, timeout)
            if result:
                return result
        
        # Todos fallaron
        elapsed = time.time() - start_time
        logger.error(f"AIOrchestrator: TODOS los proveedores fallaron después de {elapsed:.1f}s")
        return None
    
    def _try_claude(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        timeout: int
    ) -> Optional[str]:
        """Intenta llamar a Claude."""
        try:
            logger.info(f"AIOrchestrator: Intentando Claude ({self.CLAUDE_MODEL})")
            
            kwargs = {
                "model": self.CLAUDE_MODEL,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
                "timeout": timeout
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = self._claude_client.messages.create(**kwargs)
            result = response.content[0].text
            
            logger.info(f"AIOrchestrator: Claude respondió ({len(result)} chars)")
            return result
            
        except Exception as e:
            error_type = type(e).__name__
            logger.warning(f"AIOrchestrator: Claude falló ({error_type}): {e}")
            return None
    
    def _try_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        timeout: int
    ) -> Optional[str]:
        """Intenta llamar a OpenAI."""
        try:
            logger.info(f"AIOrchestrator: Intentando OpenAI ({self.OPENAI_MODEL})")
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self._openai_client.chat.completions.create(
                model=self.OPENAI_MODEL,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout
            )
            
            result = response.choices[0].message.content
            
            logger.info(f"AIOrchestrator: OpenAI respondió ({len(result)} chars)")
            return result
            
        except Exception as e:
            error_type = type(e).__name__
            logger.warning(f"AIOrchestrator: OpenAI falló ({error_type}): {e}")
            return None
    
    def _try_gemini(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        timeout: int
    ) -> Optional[str]:
        """Intenta llamar a Gemini."""
        try:
            logger.info(f"AIOrchestrator: Intentando Gemini ({self.GEMINI_MODEL})")
            
            # Gemini combina system prompt con user prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Configuración de generación
            generation_config = {
                "max_output_tokens": max_tokens,
                "temperature": temperature
            }
            
            response = self._gemini_model.generate_content(
                full_prompt,
                generation_config=generation_config,
                request_options={"timeout": timeout}
            )
            
            result = response.text
            
            logger.info(f"AIOrchestrator: Gemini respondió ({len(result)} chars)")
            return result
            
        except Exception as e:
            error_type = type(e).__name__
            logger.warning(f"AIOrchestrator: Gemini falló ({error_type}): {e}")
            return None
    
    def get_available_providers(self) -> list:
        """Retorna lista de proveedores disponibles."""
        providers = []
        if self._claude_client:
            providers.append("claude")
        if self._openai_client:
            providers.append("openai")
        if self._gemini_model:
            providers.append("gemini")
        return providers
    
    def is_available(self) -> bool:
        """Retorna True si al menos un proveedor está disponible."""
        return bool(self._claude_client or self._openai_client or self._gemini_model)

