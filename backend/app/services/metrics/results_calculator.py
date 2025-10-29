"""
ResultsCalculator - Calcula M9: Utilidad Neta

Calcula utilidad neta basándose en totales.
Depende de TotalsCalculator (Dependency Injection).

IMPORTANTE: Retiros y Distribuciones NO se restan.
Son USOS de la utilidad, no costos operativos.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import List, Dict, Any
from decimal import Decimal
from app.models import Operacion
from app.services.metrics.base_calculator import BaseCalculator


class ResultsCalculator(BaseCalculator):
    """
    Calcula M9: Utilidad Neta.
    
    RESPONSABILIDAD: Calcular utilidad neta.
    DEPENDENCIA: Necesita totals (inyectado por constructor).
    
    Métrica calculada:
    - M9: Utilidad Neta = Ingresos - Gastos
    
    NOTA CRÍTICA:
    - Retiros y Distribuciones NO se restan de la utilidad
    - Son USOS posteriores del resultado, no costos
    - Solo existe UN concepto: Utilidad Neta
    
    Principio Dependency Injection:
        NO crea TotalsCalculator internamente.
        Recibe totals ya calculados por parámetro.
    
    Ejemplo:
        >>> totals = {'ingresos_uyu': Decimal('100'), 'gastos_uyu': Decimal('40')}
        >>> calc = ResultsCalculator(ops, totals)
        >>> results = calc.calculate()
        >>> print(results['utilidad_neta_uyu'])
        Decimal('60')
    """
    
    def __init__(self, operaciones: List[Operacion], totals: Dict[str, Decimal]):
        """
        Constructor con Dependency Injection.
        
        Args:
            operaciones: Lista de operaciones (para cumplir contrato BaseCalculator)
            totals: Dict con totales ya calculados por TotalsCalculator
                   Debe contener keys: ingresos_uyu, gastos_uyu (y versiones _usd)
        """
        super().__init__(operaciones)
        self.totals = totals
    
    def calculate(self) -> Dict[str, Any]:
        """
        Calcula utilidad neta basándose en totals.
        
        NO vuelve a sumar operaciones, reutiliza totals ya calculados.
        
        Returns:
            Dict con 2 métricas (utilidad_neta en UYU/USD)
        """
        # Utilidad Neta = Ingresos - Gastos
        utilidad_neta_uyu = (
            self.totals['ingresos_uyu'] - self.totals['gastos_uyu']
        )
        utilidad_neta_usd = (
            self.totals['ingresos_usd'] - self.totals['gastos_usd']
        )
        
        return {
            'utilidad_neta_uyu': utilidad_neta_uyu,
            'utilidad_neta_usd': utilidad_neta_usd
        }
    
    def get_metric_names(self) -> List[str]:
        """
        Retorna nombres de métricas que este calculador produce.
        
        Returns:
            Lista de 2 keys del dict de calculate()
        """
        return [
            'utilidad_neta_uyu',
            'utilidad_neta_usd'
        ]