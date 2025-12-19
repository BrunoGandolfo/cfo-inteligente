"""
Base Insight Generator - Interface para generadores de insights

Define contrato para diferentes tipos de análisis IA.

Principio: Strategy Pattern
Cada tipo de análisis (operativo, estratégico, comparativo) es una strategy.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Any
from app.core.logger import get_logger

if TYPE_CHECKING:
    from app.services.ai.ai_orchestrator import AIOrchestrator as ClaudeClient

logger = get_logger(__name__)


class BaseInsightGenerator(ABC):
    """
    Contrato base para generadores de insights con IA.
    
    Implementaciones:
    - OperativoInsightGenerator: Análisis períodos ≤45 días
    - EstrategicoInsightGenerator: Análisis períodos 45-180 días
    - ComparativoInsightGenerator: Análisis comparativo entre períodos
    
    Template Method Pattern:
    - generate() define flujo común
    - build_prompt(), parse_response(), get_fallback() son abstractos
    """
    
    # Configuración por tipo (override en subclases)
    temperature: float = 0.3
    max_tokens: int = 600
    
    def __init__(self, claude_client: 'ClaudeClient'):
        """
        Args:
            claude_client: Cliente Claude inyectado (DI)
        """
        self.claude = claude_client
    
    @abstractmethod
    def build_prompt(self, metricas: Dict[str, Any]) -> str:
        """
        Construye prompt específico del tipo de análisis.
        
        Args:
            metricas: Dict con métricas calculadas (MetricsAggregate)
            
        Returns:
            Prompt optimizado para Claude Sonnet 4.5
            
        Debe incluir:
        - Contexto del análisis
        - Datos concretos con números
        - Instrucciones de formato (JSON)
        - Prohibiciones (frases genéricas)
        - Obligaciones (números específicos)
        """
    
    @abstractmethod
    def parse_response(self, response: str) -> Dict[str, str]:
        """
        Parsea respuesta de Claude.
        
        Args:
            response: Texto de respuesta de Claude
            
        Returns:
            Dict estructurado con insights
            
        Debe manejar:
        - JSON válido
        - JSON con markdown (```json ... ```)
        - Texto plano (fallback)
        """
    
    @abstractmethod
    def get_fallback(self, metricas: Dict[str, Any]) -> Dict[str, str]:
        """
        Genera insights fallback sin IA (solo reglas + números).
        
        Args:
            metricas: Dict con métricas calculadas
            
        Returns:
            Dict con insights básicos generados algorítmicamente
            
        Se usa cuando:
        - Claude API falla
        - Timeout
        - Rate limit
        - Usuario desactiva insights IA
        """
    
    def generate(
        self, 
        metricas: Dict[str, Any], 
        timeout: int = 30
    ) -> Dict[str, str]:
        """
        Template Method: Genera insights con manejo robusto de errores.
        
        Flujo:
        1. build_prompt(metricas)
        2. claude.complete(prompt)
        3. parse_response(response)
        4. Si error → get_fallback(metricas)
        
        Args:
            metricas: Métricas calculadas
            timeout: Timeout en segundos para Claude API
            
        Returns:
            Dict con insights (o fallback si error)
            
        Este método NO lanza excepciones - siempre retorna insights
        (reales o fallback).
        """
        try:
            logger.info(f"Generando insights: {self.__class__.__name__}")
            
            # Paso 1: Construir prompt
            prompt = self.build_prompt(metricas)
            
            # Paso 2: Llamar Claude
            response = self.claude.complete(
                prompt=prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=timeout
            )
            
            # Paso 3: Parsear respuesta
            insights = self.parse_response(response)
            
            logger.info(f"Insights generados exitosamente: {len(insights)} campos")
            return insights
            
        except Exception as e:
            logger.error(f"Error generando insights con IA: {str(e)}")
            logger.info("Usando fallback insights (sin IA)")
            
            # Paso 4: Fallback
            fallback = self.get_fallback(metricas)
            fallback['_generated_by'] = 'fallback'
            fallback['_error'] = str(e)
            
            return fallback

