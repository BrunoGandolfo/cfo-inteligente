"""
Base Calculator - Interface para calculadores de métricas

Define contrato que deben cumplir todos los calculadores.

Principio: Interface Segregation (SOLID)
Patrón: Strategy Pattern

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.models import Operacion


class BaseCalculator(ABC):
    """
    Contrato base para todos los calculadores de métricas.
    
    Cada calculador implementa un grupo de métricas relacionadas:
    - TotalsCalculator: M1-M8 (totales absolutos)
    - ResultsCalculator: M9-M10 (resultados)
    - RatiosCalculator: M11-M14 (rentabilidad %)
    - DistributionCalculator: M15-M17 (distribución %)
    - EfficiencyCalculator: M18-M20 (eficiencia)
    - TrendsCalculator: M21-M26 (tendencias y comparaciones)
    
    Principio Single Responsibility:
    - Cada calculador calcula SOLO su grupo de métricas
    - Sin side effects
    - Funciones puras donde sea posible
    """
    
    def __init__(self, operaciones: List[Operacion]):
        """
        Args:
            operaciones: Lista de operaciones del período a analizar
        """
        self.operaciones = operaciones
    
    @abstractmethod
    def calculate(self) -> Dict[str, Any]:
        """
        Calcula todas las métricas de responsabilidad de este calculador.
        
        Returns:
            Dict con métricas calculadas.
            Keys específicas de cada implementación.
            
        Ejemplo (TotalsCalculator):
            {
                'ingresos_uyu': 114941988.84,
                'gastos_uyu': 76486651.33,
                ...
            }
        """
        pass
    
    @abstractmethod
    def get_metric_names(self) -> List[str]:
        """
        Retorna nombres de métricas que este calculador produce.
        
        Útil para:
        - Documentación automática
        - Validación de output
        - Debugging
        
        Returns:
            Lista de nombres de métricas (keys del dict de calculate())
            
        Ejemplo:
            ['ingresos_uyu', 'gastos_uyu', 'retiros_uyu', ...]
        """
        pass

