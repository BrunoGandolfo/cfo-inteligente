"""
Comparativo Insight Generator - Análisis comparativo entre períodos

Genera insights comparando período actual vs anterior.
Hereda de BaseInsightGenerator (Template Method Pattern).

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import Dict, Any

from app.services.ai.base_insight_generator import BaseInsightGenerator
from app.services.ai.prompt_builder import build_comparativo_prompt, build_system_prompt
from app.services.ai.response_parser import parse_insights_response, validate_insights
from app.services.ai.fallback_generator import generate_comparativo_fallback
from app.core.logger import get_logger

logger = get_logger(__name__)


class ComparativoInsightGenerator(BaseInsightGenerator):
    """
    Generator de insights comparativos (período actual vs anterior).
    
    RESPONSABILIDAD: Generar insights de cambios y variaciones.
    HERENCIA: Implementa métodos abstractos de BaseInsightGenerator.
    PATRÓN: Template Method.
    
    Características:
    - Temperatura: 0.3 (conservador, enfoque en datos)
    - Max tokens: 650 (3 insights comparativos)
    - Timeout: 30 segundos
    - Fallback automático si Claude falla
    
    Diferencias vs otros:
    - Requiere 2 conjuntos de métricas (actual + anterior)
    - Enfoque en variaciones y causas
    - Recomendaciones basadas en tendencias
    
    Ejemplo:
        >>> generator = ComparativoInsightGenerator(claude_client)
        >>> insights = generator.generate_comparison(
        ...     metricas_actual,
        ...     metricas_anterior,
        ...     timeout=30
        ... )
        >>> print(insights['cambio_principal'])
        "Variación de ingresos: +15.5% ..."
    """
    
    # Configuración específica de comparativo
    temperature = 0.3  # Conservador, basado en datos concretos
    max_tokens = 650   # 3 insights ~100-120 palabras
    
    def __init__(self, claude_client: 'ClaudeClient', metricas_anterior: Dict[str, Any] = None):
        """
        Constructor extendido para incluir métricas anteriores.
        
        Args:
            claude_client: Cliente Claude inyectado
            metricas_anterior: Métricas del período de comparación (opcional)
        """
        super().__init__(claude_client)
        self.logger = logger
        self.metricas_anterior = metricas_anterior or {}
    
    def build_prompt(self, metricas: Dict[str, Any]) -> str:
        """
        Construye prompt comparativo.
        
        Args:
            metricas: Métricas del período actual
            
        Returns:
            String con prompt optimizado
            
        Nota:
            Usa self.metricas_anterior (seteado en constructor o en generate_comparison)
        """
        return build_comparativo_prompt(metricas, self.metricas_anterior)
    
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
        
        # Validar estructura comparativa
        if not validate_insights(insights, required_keys=['cambio_principal']):
            # Fallback: aceptar estructura genérica si no tiene keys específicos
            if not validate_insights(insights):
                raise ValueError("Response no contiene insights válidos")
        
        return insights
    
    def get_fallback(self, metricas: Dict[str, Any]) -> Dict[str, str]:
        """
        Genera insights comparativos fallback sin IA.
        
        Args:
            metricas: Métricas del período actual
            
        Returns:
            Dict con 3 insights comparativos generados algorítmicamente
        """
        return generate_comparativo_fallback(metricas, self.metricas_anterior)
    
    def generate_comparison(
        self,
        metricas_actual: Dict[str, Any],
        metricas_anterior: Dict[str, Any],
        timeout: int = 30
    ) -> Dict[str, str]:
        """
        Genera insights comparativos entre dos períodos.
        
        Método específico de esta clase (no existe en base).
        
        Args:
            metricas_actual: Métricas del período actual
            metricas_anterior: Métricas del período de comparación
            timeout: Timeout en segundos
            
        Returns:
            Dict con insights comparativos
        """
        # Setear métricas anteriores para que build_prompt las use
        self.metricas_anterior = metricas_anterior
        
        # Delegar a generate() de la base
        return self.generate(metricas_actual, timeout=timeout)
    
    def generate(
        self,
        metricas: Dict[str, Any],
        timeout: int = 30
    ) -> Dict[str, str]:
        """
        Genera insights comparativos.
        
        Override de método base para agregar system_prompt.
        
        Args:
            metricas: Métricas del período actual
            timeout: Timeout en segundos
            
        Returns:
            Dict con insights comparativos
            
        Nota:
            Requiere que self.metricas_anterior esté seteado.
        """
        try:
            if not self.metricas_anterior:
                raise ValueError(
                    "Métricas anteriores no disponibles. "
                    "Usar generate_comparison() o setear metricas_anterior en constructor."
                )
            
            self.logger.info("Generando insights comparativos con Claude")
            
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
            
            self.logger.info(f"Insights comparativos generados: {len(insights)} campos")
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generando insights comparativos: {str(e)}")
            self.logger.info("Usando fallback insights comparativos")
            
            # Fallback
            fallback = self.get_fallback(metricas)
            fallback['_error'] = str(e)
            
            return fallback

