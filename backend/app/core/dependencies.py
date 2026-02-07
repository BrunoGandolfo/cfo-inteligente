"""
Dependencies - Dependency Injection Container

Provee dependencias para endpoints FastAPI.
Implementa patrón Singleton donde necesario.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

import os
from typing import Dict, Any
from functools import lru_cache

from sqlalchemy.orm import Session
from fastapi import Depends

from app.core.database import SessionLocal, get_db
from app.services.ai.claude_client import ClaudeClient
from app.core.logger import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════
# CLAUDE CLIENT (SINGLETON)
# ═══════════════════════════════════════════════════════════════

@lru_cache()
def get_claude_client() -> ClaudeClient:
    """
    Provee Claude client (singleton).
    
    Patrón: Singleton vía lru_cache (solo 1 instancia).
    
    Returns:
        ClaudeClient configurado
        
    Raises:
        ValueError: Si ANTHROPIC_API_KEY no está definida
        
    Uso:
        @app.post("/...")
        def endpoint(claude: ClaudeClient = Depends(get_claude_client)):
            ...
    """
    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY no configurada - insights usarán fallback")
        # Retornar None o un mock? Por ahora lanzar error
        raise ValueError(
            "ANTHROPIC_API_KEY no configurada. "
            "Definir en .env o variable de entorno."
        )
    
    client = ClaudeClient(api_key=api_key)
    logger.info("Claude client inicializado (singleton)")
    
    return client


# ═══════════════════════════════════════════════════════════════
# CHART CONFIG
# ═══════════════════════════════════════════════════════════════

def get_chart_config(paleta: str = 'moderna_2024') -> Dict[str, Any]:
    """
    Provee configuración de charts según paleta.
    
    Args:
        paleta: 'institucional' | 'moderna_2024'
        
    Returns:
        Dict con configuración de colores y estilos
        
    Uso:
        config = get_chart_config(paleta='moderna_2024')
    """
    paletas = {
        'moderna_2024': {
            'primary': '#3B82F6',
            'success': '#10B981',
            'danger': '#EF4444',
            'warning': '#F59E0B',
            'secondary': '#8B5CF6',
            'extended': [
                '#10B981',  # Verde
                '#3B82F6',  # Azul
                '#EF4444',  # Rojo
                '#F59E0B',  # Ámbar
                '#8B5CF6',  # Violeta
                '#EC4899',  # Rosa
            ],
            'width_default': 800,
            'height_default': 500,
            'dpi': 300
        },
        'institucional': {
            'primary': '#1E40AF',
            'success': '#059669',
            'danger': '#DC2626',
            'warning': '#D97706',
            'secondary': '#7C3AED',
            'extended': [
                '#059669',
                '#1E40AF',
                '#DC2626',
                '#D97706',
                '#7C3AED',
                '#DB2777',
            ],
            'width_default': 800,
            'height_default': 500,
            'dpi': 300
        }
    }
    
    return paletas.get(paleta, paletas['moderna_2024'])


# ═══════════════════════════════════════════════════════════════
# OPERATIONS REPOSITORY
# ═══════════════════════════════════════════════════════════════

def get_operations_repository(
    db: Session = Depends(get_db)
):
    """
    Provee repositorio de operaciones.
    
    Inyecta db session automáticamente.
    
    Args:
        db: Session inyectada por Depends(get_db)
        
    Returns:
        OperationsRepository configurado
        
    Uso:
        @app.get("/...")
        def endpoint(repo = Depends(get_operations_repository)):
            ops = repo.get_by_period(...)
    """
    from app.repositories.operations_repository import OperationsRepository
    
    return OperationsRepository(db)


# ═══════════════════════════════════════════════════════════════
# INSIGHTS ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════

def get_insights_orchestrator(
    claude_client: ClaudeClient = Depends(get_claude_client)
):
    """
    Provee InsightsOrchestrator.
    
    Inyecta Claude client automáticamente.
    
    Args:
        claude_client: Claude client inyectado
        
    Returns:
        InsightsOrchestrator configurado
    """
    from app.services.ai.insights_orchestrator import InsightsOrchestrator
    
    return InsightsOrchestrator(claude_client)


# ═══════════════════════════════════════════════════════════════
# METRICS AGGREGATOR
# ═══════════════════════════════════════════════════════════════

def create_metrics_aggregator(
    operaciones,
    fecha_inicio,
    fecha_fin,
    operaciones_comparacion=None,
    historico_mensual=None
):
    """
    Factory para MetricsAggregator.
    
    No es dependency de FastAPI, es helper.
    
    Args:
        operaciones: Lista de operaciones
        fecha_inicio: Fecha inicio
        fecha_fin: Fecha fin
        operaciones_comparacion: Operaciones de comparación (opcional)
        historico_mensual: Histórico mensual (opcional)
        
    Returns:
        MetricsAggregator configurado
    """
    from app.services.metrics.metrics_aggregator import MetricsAggregator
    
    return MetricsAggregator(
        operaciones=operaciones,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        operaciones_comparacion=operaciones_comparacion,
        historico_mensual=historico_mensual
    )


# ═══════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════

def check_dependencies() -> Dict[str, bool]:
    """
    Verifica que dependencias críticas estén disponibles.
    
    Útil para health checks.
    
    Returns:
        Dict con status de dependencias
    """
    status = {}
    
    # Check Database
    try:
        db = next(get_db())
        db.execute("SELECT 1")
        status['database'] = True
        db.close()
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        status['database'] = False
    
    # Check Claude API Key
    status['anthropic_api_key'] = bool(os.getenv('ANTHROPIC_API_KEY'))
    
    # Check templates directory
    from pathlib import Path
    backend_dir = Path(__file__).parent.parent
    templates_dir = backend_dir / 'templates'
    status['templates_directory'] = templates_dir.exists()
    
    return status

