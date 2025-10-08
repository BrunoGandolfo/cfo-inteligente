"""
Insights Orchestrator - FACADE que coordina generadores de insights

Selecciona y ejecuta el generator apropiado según contexto.
Implementa Strategy Pattern.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import Dict, Any, Optional

from app.services.ai.claude_client import ClaudeClient
from app.services.ai.operativo_generator import OperativoInsightGenerator
from app.services.ai.estrategico_generator import EstrategicoInsightGenerator
from app.services.ai.comparativo_generator import ComparativoInsightGenerator
from app.core.logger import get_logger

logger = get_logger(__name__)


class InsightsOrchestrator:
    """
    FACADE: Coordina generación de insights.
    
    RESPONSABILIDAD: Seleccionar generator apropiado según contexto.
    PATRÓN: Strategy Pattern + Facade Pattern
    
    Lógica de selección:
    - Si tiene_comparacion → ComparativoInsightGenerator
    - Si duracion_dias ≤ 45 → OperativoInsightGenerator
    - Si duracion_dias > 45 → EstrategicoInsightGenerator
    
    Principios aplicados:
    - Single Responsibility: Solo coordina, NO genera
    - Dependency Injection: Claude client inyectado
    - Open/Closed: Extensible (agregar nuevo generator)
    - Strategy Pattern: Selecciona strategy en runtime
    
    Ejemplo:
        >>> from app.services.ai.claude_client import ClaudeClient
        >>> client = ClaudeClient()
        >>> orchestrator = InsightsOrchestrator(client)
        >>> insights = orchestrator.generate_all(
        ...     metricas=metricas,
        ...     duracion_dias=30,
        ...     tiene_comparacion=False
        ... )
        >>> print(insights['insight_1'])
        "Rentabilidad operativa excelente: ..."
    """
    
    def __init__(self, claude_client: ClaudeClient):
        """
        Constructor con Dependency Injection.
        
        Args:
            claude_client: Cliente Claude inyectado
        """
        self.claude = claude_client
        self.logger = logger
        
        # Pre-instanciar generators (pueden reutilizarse)
        self.operativo_gen = OperativoInsightGenerator(self.claude)
        self.estrategico_gen = EstrategicoInsightGenerator(self.claude)
        # comparativo_gen se instancia on-demand (necesita métricas anteriores)
    
    def generate_all(
        self,
        metricas: Dict[str, Any],
        duracion_dias: int,
        tiene_comparacion: bool = False,
        metricas_comparacion: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        usar_ia: bool = True
    ) -> Dict[str, str]:
        """
        Genera insights seleccionando generator apropiado.
        
        Strategy Pattern: Selecciona strategy en runtime según contexto.
        
        Args:
            metricas: Métricas del período actual
            duracion_dias: Duración del período en días
            tiene_comparacion: Si hay período de comparación
            metricas_comparacion: Métricas del período de comparación (requerido si tiene_comparacion)
            timeout: Timeout para Claude API
            usar_ia: Si False, usa solo fallback (sin llamar Claude)
            
        Returns:
            Dict con insights generados
            
        Raises:
            ValueError: Si tiene_comparacion pero faltan metricas_comparacion
        """
        self.logger.info(
            f"Iniciando generación insights: duracion={duracion_dias}d, "
            f"comparacion={tiene_comparacion}, usar_ia={usar_ia}"
        )
        
        # ═══════════════════════════════════════════════════════════════
        # PASO 1: SELECCIONAR GENERATOR (Strategy Pattern)
        # ═══════════════════════════════════════════════════════════════
        
        if tiene_comparacion:
            # STRATEGY: Comparativo
            self.logger.info("Strategy seleccionado: Comparativo")
            
            if not metricas_comparacion:
                raise ValueError(
                    "tiene_comparacion=True requiere metricas_comparacion"
                )
            
            generator = ComparativoInsightGenerator(
                self.claude,
                metricas_anterior=metricas_comparacion
            )
            
            if not usar_ia:
                # Usar solo fallback
                return generator.get_fallback(metricas)
            
            return generator.generate_comparison(
                metricas_actual=metricas,
                metricas_anterior=metricas_comparacion,
                timeout=timeout
            )
        
        elif duracion_dias <= 45:
            # STRATEGY: Operativo (períodos cortos, táctico)
            self.logger.info("Strategy seleccionado: Operativo")
            generator = self.operativo_gen
            
        else:
            # STRATEGY: Estratégico (períodos largos, tendencias)
            self.logger.info("Strategy seleccionado: Estratégico")
            generator = self.estrategico_gen
        
        # ═══════════════════════════════════════════════════════════════
        # PASO 2: GENERAR INSIGHTS
        # ═══════════════════════════════════════════════════════════════
        
        if not usar_ia:
            # Usar solo fallback (útil para testing o si usuario desactiva IA)
            self.logger.info("Modo fallback: generando sin IA")
            return generator.get_fallback(metricas)
        
        # Generar con IA (con fallback automático si falla)
        return generator.generate(metricas, timeout=timeout)
    
    def get_generator_info(
        self,
        duracion_dias: int,
        tiene_comparacion: bool = False
    ) -> Dict[str, Any]:
        """
        Retorna información del generator que se usaría.
        
        Útil para debugging y testing.
        
        Args:
            duracion_dias: Duración del período
            tiene_comparacion: Si hay comparación
            
        Returns:
            Dict con info del generator
        """
        if tiene_comparacion:
            tipo = "comparativo"
            temperatura = 0.3
            max_tokens = 650
        elif duracion_dias <= 45:
            tipo = "operativo"
            temperatura = 0.3
            max_tokens = 600
        else:
            tipo = "estrategico"
            temperatura = 0.4
            max_tokens = 700
        
        return {
            "tipo": tipo,
            "temperatura": temperatura,
            "max_tokens": max_tokens,
            "modelo": self.claude.model
        }

