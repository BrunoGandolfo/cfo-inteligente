"""
Sistema de Agregación de Datos para Reportes - CFO Inteligente

Módulo que implementa agregaciones de datos financieros para diferentes períodos.
Sigue patrón Factory + Template Method para máxima extensibilidad.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from .base_aggregator import BaseAggregator
from .monthly_aggregator import MonthlyAggregator
from .aggregator_factory import AggregatorFactory

__all__ = [
    'BaseAggregator',
    'MonthlyAggregator',
    'AggregatorFactory'
]

