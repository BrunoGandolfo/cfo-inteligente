"""
AggregatorFactory - Factory Pattern para crear agregadores

Crea la instancia correcta de agregador según el tipo de período solicitado.
Simplifica la creación y mejora la extensibilidad.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import Type, Dict, List
from sqlalchemy.orm import Session

from .base_aggregator import BaseAggregator
from .monthly_aggregator import MonthlyAggregator


class AggregatorFactory:
    """
    Factory para crear agregadores según tipo de período.
    
    Uso:
        factory = AggregatorFactory(db)
        aggregator = factory.create('monthly')
        datos = aggregator.aggregate(start_date, end_date)
    """
    
    # Registro de agregadores disponibles
    _aggregators: Dict[str, Type[BaseAggregator]] = {
        'monthly': MonthlyAggregator,
        # 'weekly': WeeklyAggregator,      # TODO: Implementar
        # 'quarterly': QuarterlyAggregator, # TODO: Implementar
        # 'yearly': YearlyAggregator,       # TODO: Implementar
    }
    
    def __init__(self, db: Session):
        """
        Args:
            db: Sesión de SQLAlchemy
        """
        self.db = db
    
    def create(self, period_type: str) -> BaseAggregator:
        """
        Crea instancia del agregador apropiado.
        
        Args:
            period_type: Tipo de período ('weekly', 'monthly', 'quarterly', 'yearly')
            
        Returns:
            Instancia del agregador correspondiente
            
        Raises:
            ValueError: Si period_type no está registrado
        """
        aggregator_class = self._aggregators.get(period_type)
        
        if not aggregator_class:
            available = ', '.join(self._aggregators.keys())
            raise ValueError(
                f"Agregador '{period_type}' no existe. "
                f"Disponibles: {available}"
            )
        
        return aggregator_class(self.db)
    
    @classmethod
    def register_aggregator(cls, period_type: str, aggregator_class: Type[BaseAggregator]):
        """
        Registra un nuevo agregador (permite extensión sin modificar código).
        
        Args:
            period_type: Nombre del tipo de período
            aggregator_class: Clase del agregador (debe heredar de BaseAggregator)
        """
        if not issubclass(aggregator_class, BaseAggregator):
            raise TypeError(f"{aggregator_class} debe heredar de BaseAggregator")
        
        cls._aggregators[period_type] = aggregator_class
    
    @classmethod
    def get_available_types(cls) -> List[str]:
        """Retorna lista de tipos de período disponibles"""
        return list(cls._aggregators.keys())

