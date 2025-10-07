"""
InsightContextBuilder - Construye contexto para generación de insights

Prepara el contexto completo que se enviará a Claude para análisis.
Incluye métricas, históricos, comparaciones y lentes analíticas.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import Dict, Any
from datetime import date
import json

from .analysis_lenses import AnalysisLenses
from app.core.logger import get_logger

logger = get_logger(__name__)


class InsightContextBuilder:
    """
    Construye contexto rico y estructurado para análisis de IA.
    
    Builder Pattern: permite construir contexto paso a paso.
    """
    
    def __init__(self, period_type: str):
        """
        Args:
            period_type: Tipo de período ('monthly', 'quarterly', 'yearly')
        """
        self.period_type = period_type
        self.context = {
            'period_info': {},
            'metrics': {},
            'historical': {},
            'analysis_lenses': [],
            'data_volume': {}
        }
    
    def with_metrics(self, metrics: Dict[str, Any]) -> 'InsightContextBuilder':
        """Agrega métricas principales al contexto"""
        self.context['metrics'] = metrics
        return self
    
    def with_historical(self, historical: Dict[str, Any]) -> 'InsightContextBuilder':
        """Agrega datos históricos para comparación"""
        self.context['historical'] = historical
        return self
    
    def with_period_info(self, start_date: date, end_date: date, label: str) -> 'InsightContextBuilder':
        """Agrega información del período"""
        self.context['period_info'] = {
            'type': self.period_type,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'label': label
        }
        return self
    
    def with_data_volume(self, total_ops: int, by_type: Dict[str, int]) -> 'InsightContextBuilder':
        """Agrega información sobre volumen de datos"""
        self.context['data_volume'] = {
            'total_operations': total_ops,
            'by_type': by_type
        }
        return self
    
    def select_analysis_lenses(self, month_number: int = None) -> 'InsightContextBuilder':
        """
        Selecciona lentes analíticos apropiados para el período.
        
        Args:
            month_number: Número de mes (1-12) para rotación mensual
        """
        lenses = AnalysisLenses.select_lenses(self.period_type, month_number)
        self.context['analysis_lenses'] = lenses
        
        logger.info(f"Lentes seleccionados para {self.period_type}: {', '.join(lenses)}")
        
        return self
    
    def build(self) -> Dict[str, Any]:
        """
        Construye y retorna el contexto completo.
        
        Returns:
            Dict con todo el contexto listo para prompt de Claude
        """
        # Validar que hay datos mínimos
        if not self.context['metrics']:
            raise ValueError("Contexto requiere métricas (usar with_metrics)")
        
        if not self.context['period_info']:
            raise ValueError("Contexto requiere información de período (usar with_period_info)")
        
        logger.debug(f"Contexto construido para {self.period_type}: {len(json.dumps(self.context))} caracteres")
        
        return self.context
    
    def to_prompt_string(self) -> str:
        """
        Convierte contexto a string formateado para prompt de Claude.
        
        Returns:
            String con datos estructurados legibles para IA
        """
        ctx = self.context
        
        # Construir prompt estructurado
        lines = [
            f"=== PERÍODO: {ctx['period_info']['label']} ===",
            f"Tipo: {ctx['period_info']['type']}",
            f"Fechas: {ctx['period_info']['start_date']} a {ctx['period_info']['end_date']}",
            "",
            "=== MÉTRICAS PRINCIPALES ===",
            f"Ingresos: ${ctx['metrics']['ingresos']['uyu']:,.2f} UYU ({ctx['metrics']['ingresos']['cantidad_operaciones']} ops)",
            f"Gastos: ${ctx['metrics']['gastos']['uyu']:,.2f} UYU ({ctx['metrics']['gastos']['cantidad_operaciones']} ops)",
            f"Rentabilidad: {ctx['metrics']['rentabilidad_porcentaje']:.2f}%",
            f"Resultado Operativo: ${ctx['metrics']['resultado_operativo']:,.2f}",
            f"Resultado Neto: ${ctx['metrics']['resultado_neto']:,.2f}",
            ""
        ]
        
        # Datos históricos si existen
        if ctx['historical'].get('promedios'):
            hist = ctx['historical']
            lines.extend([
                "=== CONTEXTO HISTÓRICO (6 meses) ===",
                f"Promedio ingresos: ${hist['promedios']['ingresos']:,.2f}",
                f"Promedio gastos: ${hist['promedios']['gastos']:,.2f}",
                f"Promedio rentabilidad: {hist['promedios']['rentabilidad']:.2f}%",
                ""
            ])
        
        # Lentes analíticos
        if ctx['analysis_lenses']:
            lines.append("=== LENTES ANALÍTICOS A APLICAR ===")
            prompt_fragments = AnalysisLenses.get_prompt_fragments(ctx['analysis_lenses'])
            lines.append(prompt_fragments)
        
        return "\n".join(lines)

