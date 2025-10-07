"""
Sistema de Generación de Insights con IA - CFO Inteligente

Módulo para generar análisis inteligentes y variables usando Claude Sonnet 4.5.
Los insights NO son plantillas estáticas sino análisis contextuales únicos.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from .analysis_lenses import AnalysisLenses
from .insight_context_builder import InsightContextBuilder
from .insight_generator import InsightGenerator
from .insight_formatter import InsightFormatter

__all__ = [
    'AnalysisLenses',
    'InsightContextBuilder',
    'InsightGenerator',
    'InsightFormatter'
]

