"""
AI Services Package

Generadores de insights con Claude Sonnet 4.5.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from app.services.ai.base_insight_generator import BaseInsightGenerator
from app.services.ai.claude_client import ClaudeClient
from app.services.ai.operativo_generator import OperativoInsightGenerator
from app.services.ai.estrategico_generator import EstrategicoInsightGenerator
from app.services.ai.comparativo_generator import ComparativoInsightGenerator
from app.services.ai.insights_orchestrator import InsightsOrchestrator

__all__ = [
    'BaseInsightGenerator',
    'ClaudeClient',
    'OperativoInsightGenerator',
    'EstrategicoInsightGenerator',
    'ComparativoInsightGenerator',
    'InsightsOrchestrator'
]
