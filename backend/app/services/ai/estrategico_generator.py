"""
Estratégico Insight Generator - Análisis estratégico (períodos 45-180 días)

Genera insights estratégicos y de tendencias para períodos medios.
Hereda de BaseInsightGenerator (Template Method Pattern).

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import Dict, Any

from app.services.ai.base_insight_generator import BaseInsightGenerator
from app.services.ai.prompt_builder import build_estrategico_prompt, build_system_prompt
from app.services.ai.response_parser import parse_insights_response, validate_insights
from app.services.ai.fallback_generator import generate_estrategico_fallback
from app.core.logger import get_logger

logger = get_logger(__name__)


class EstrategicoInsightGenerator(BaseInsightGenerator):
    """
    Generator de insights estratégicos (períodos 45-180 días).
    
    RESPONSABILIDAD: Generar insights estratégicos y de tendencias.
    HERENCIA: Implementa métodos abstractos de BaseInsightGenerator.
    PATRÓN: Template Method.
    
    Características:
    - Temperatura: 0.4 (ligeramente más creativo que operativo)
    - Max tokens: 700 (4 insights estratégicos)
    - Timeout: 30 segundos
    - Fallback automático si Claude falla
    
    Diferencias vs Operativo:
    - Enfoque en tendencias multi-período
    - Análisis de patrones
    - Recomendaciones estratégicas (no tácticas)
    
    Ejemplo:
        >>> generator = EstrategicoInsightGenerator(claude_client)
        >>> insights = generator.generate(metricas, timeout=30)
        >>> print(insights['tendencia'])
        "Tendencia positiva sostenible: ..."
    """
    
    # Configuración específica de estratégico
    temperature = 0.4  # Ligeramente más creativo
    max_tokens = 700   # 4 insights ~100 palabras cada uno
    
    def __init__(self, claude_client):
        super().__init__(claude_client)
        self.logger = logger
    
    def build_prompt(self, metricas: Dict[str, Any]) -> str:
        """
        Construye prompt para análisis estratégico.
        
        Args:
            metricas: Dict con métricas calculadas
            
        Returns:
            String con prompt optimizado
        """
        return build_estrategico_prompt(metricas)
    
    def parse_response(self, response: str) -> Dict[str, str]:
        """
        Parsea respuesta de Claude.
        
        Args:
            response: Texto de respuesta
            
        Returns:
            Dict con insights parseados
            
        Raises:
            ValueError: Si parsing falla
        """
        insights = parse_insights_response(response)
        
        # Validar que tenga al menos "tendencia"
        if not validate_insights(insights, required_keys=['tendencia']):
            # Fallback: si no tiene estructura estratégica, aceptar insights genéricos
            if not validate_insights(insights):
                raise ValueError("Response no contiene insights válidos")
        
        return insights
    
    def get_fallback(self, metricas: Dict[str, Any]) -> Dict[str, str]:
        """
        Genera insights estratégicos fallback sin IA.
        
        Args:
            metricas: Dict con métricas calculadas
            
        Returns:
            Dict con 4 insights estratégicos generados algorítmicamente
        """
        return generate_estrategico_fallback(metricas)
    
    def generate(
        self,
        metricas: Dict[str, Any],
        timeout: int = 30
    ) -> Dict[str, str]:
        """
        Genera insights estratégicos.
        
        Override para agregar system_prompt.
        
        Args:
            metricas: Métricas calculadas
            timeout: Timeout en segundos
            
        Returns:
            Dict con insights estratégicos
        """
        try:
            self.logger.info("Generando insights estratégicos con Claude")
            
            # Construir prompts
            prompt = self.build_prompt(metricas)
            system_prompt = build_system_prompt()
            
            # Llamar Claude
            response = self.claude.complete(
                prompt=prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=timeout,
                system_prompt=system_prompt
            )
            
            # Parsear
            insights = self.parse_response(response)
            
            self.logger.info(f"Insights estratégicos generados: {len(insights)} campos")
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generando insights estratégicos: {str(e)}")
            self.logger.info("Usando fallback insights estratégicos")
            
            # Fallback
            fallback = self.get_fallback(metricas)
            fallback['_error'] = str(e)
            
            return fallback

