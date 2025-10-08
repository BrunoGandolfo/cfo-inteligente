"""
Operativo Insight Generator - Análisis operativo (períodos ≤45 días)

Genera insights tácticos y accionables para períodos cortos.
Hereda de BaseInsightGenerator (Template Method Pattern).

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import Dict, Any

from app.services.ai.base_insight_generator import BaseInsightGenerator
from app.services.ai.prompt_builder import build_operativo_prompt, build_system_prompt
from app.services.ai.response_parser import parse_insights_response, validate_insights
from app.services.ai.fallback_generator import generate_operativo_fallback
from app.core.logger import get_logger

logger = get_logger(__name__)


class OperativoInsightGenerator(BaseInsightGenerator):
    """
    Generator de insights operativos (períodos ≤45 días).
    
    RESPONSABILIDAD: Generar insights tácticos y accionables.
    HERENCIA: Implementa métodos abstractos de BaseInsightGenerator.
    PATRÓN: Template Method (generate() definido en base).
    
    Características:
    - Temperatura: 0.3 (análisis conservador)
    - Max tokens: 600
    - Timeout: 25 segundos
    - Fallback automático si Claude falla
    
    Ejemplo:
        >>> from app.services.ai.claude_client import ClaudeClient
        >>> client = ClaudeClient()
        >>> generator = OperativoInsightGenerator(client)
        >>> insights = generator.generate(metricas, timeout=25)
        >>> print(insights['insight_1'])
        "Rentabilidad operativa excelente: ..."
    """
    
    # Configuración específica de operativo
    temperature = 0.3  # Conservador, basado en datos
    max_tokens = 600   # Suficiente para 3 insights de ~120 palabras
    
    def __init__(self, claude_client):
        super().__init__(claude_client)
        self.logger = logger
    
    def build_prompt(self, metricas: Dict[str, Any]) -> str:
        """
        Construye prompt para análisis operativo.
        
        Delega a función pura de prompt_builder.
        
        Args:
            metricas: Dict con métricas calculadas
            
        Returns:
            String con prompt optimizado para Claude
        """
        return build_operativo_prompt(metricas)
    
    def parse_response(self, response: str) -> Dict[str, str]:
        """
        Parsea respuesta de Claude.
        
        Delega a función pura de response_parser.
        
        Args:
            response: Texto de respuesta de Claude
            
        Returns:
            Dict con insights parseados
            
        Raises:
            ValueError: Si parsing falla completamente
        """
        insights = parse_insights_response(response)
        
        # Validar que tenga al menos insight_1
        if not validate_insights(insights, required_keys=['insight_1']):
            raise ValueError("Response no contiene insights válidos")
        
        return insights
    
    def get_fallback(self, metricas: Dict[str, Any]) -> Dict[str, str]:
        """
        Genera insights fallback sin IA.
        
        Delega a función pura de fallback_generator.
        Se usa cuando:
        - Claude API falla
        - Timeout
        - Rate limit
        - Usuario desactiva insights IA
        
        Args:
            metricas: Dict con métricas calculadas
            
        Returns:
            Dict con 3 insights operativos generados algorítmicamente
        """
        return generate_operativo_fallback(metricas)
    
    def generate(
        self,
        metricas: Dict[str, Any],
        timeout: int = 25
    ) -> Dict[str, str]:
        """
        Genera insights operativos (método heredado de base).
        
        Override para agregar system_prompt específico.
        
        Args:
            metricas: Métricas calculadas
            timeout: Timeout en segundos
            
        Returns:
            Dict con insights (reales o fallback)
        """
        try:
            self.logger.info("Generando insights operativos con Claude")
            
            # Construir prompts
            prompt = self.build_prompt(metricas)
            system_prompt = build_system_prompt()
            
            # Llamar Claude con system prompt
            response = self.claude.complete(
                prompt=prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=timeout,
                system_prompt=system_prompt
            )
            
            # Parsear respuesta
            insights = self.parse_response(response)
            
            self.logger.info(f"Insights operativos generados: {len(insights)} campos")
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generando insights operativos: {str(e)}")
            self.logger.info("Usando fallback insights operativos")
            
            # Fallback
            fallback = self.get_fallback(metricas)
            fallback['_error'] = str(e)
            
            return fallback

