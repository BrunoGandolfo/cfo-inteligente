"""
ResultsCalculator - Calcula M9-M10: Resultados operativo y neto

Calcula resultados finales basándose en totales.
Depende de TotalsCalculator (Dependency Injection).

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import List, Dict, Any
from decimal import Decimal
from app.models import Operacion
from app.services.metrics.base_calculator import BaseCalculator


class ResultsCalculator(BaseCalculator):
    """
    Calcula M9-M10: Resultados operativo y neto.
    
    RESPONSABILIDAD: Calcular resultados finales.
    DEPENDENCIA: Necesita totals (inyectado por constructor).
    
    Métricas calculadas:
    - M9: Resultado Operativo = Ingresos - Gastos
    - M10: Resultado Neto = Operativo - Retiros - Distribuciones
    
    Principio Dependency Injection:
        NO crea TotalsCalculator internamente.
        Recibe totals ya calculados por parámetro.
        Esto permite:
        - Testear aisladamente (mock totals)
        - Reutilizar cálculos (no recalcular)
        - Evitar coupling fuerte
    
    Ejemplo:
        >>> totals = {'ingresos_uyu': Decimal('100'), 'gastos_uyu': Decimal('40')}
        >>> calc = ResultsCalculator(ops, totals)
        >>> results = calc.calculate()
        >>> print(results['resultado_operativo_uyu'])
        Decimal('60')
    """
    
    def __init__(self, operaciones: List[Operacion], totals: Dict[str, Decimal]):
        """
        Constructor con Dependency Injection.
        
        Args:
            operaciones: Lista de operaciones (para cumplir contrato BaseCalculator)
            totals: Dict con totales ya calculados por TotalsCalculator
                   Debe contener keys: ingresos_uyu, gastos_uyu, retiros_uyu, 
                   distribuciones_uyu (y versiones _usd)
        """
        super().__init__(operaciones)
        self.totals = totals  # ← Dependency Injection
    
    def calculate(self) -> Dict[str, Any]:
        """
        Calcula resultados basándose en totals.
        
        NO vuelve a sumar operaciones, reutiliza totals ya calculados.
        Esto es eficiente y evita duplicación.
        
        Returns:
            Dict con 4 métricas (resultado_operativo y resultado_neto en UYU/USD)
        """
        # Resultado Operativo = Ingresos - Gastos
        resultado_operativo_uyu = (
            self.totals['ingresos_uyu'] - self.totals['gastos_uyu']
        )
        resultado_operativo_usd = (
            self.totals['ingresos_usd'] - self.totals['gastos_usd']
        )
        
        # Resultado Neto = Operativo - Retiros - Distribuciones
        resultado_neto_uyu = (
            resultado_operativo_uyu 
            - self.totals['retiros_uyu'] 
            - self.totals['distribuciones_uyu']
        )
        resultado_neto_usd = (
            resultado_operativo_usd 
            - self.totals['retiros_usd'] 
            - self.totals['distribuciones_usd']
        )
        
        return {
            'resultado_operativo_uyu': resultado_operativo_uyu,
            'resultado_operativo_usd': resultado_operativo_usd,
            'resultado_neto_uyu': resultado_neto_uyu,
            'resultado_neto_usd': resultado_neto_usd
        }
    
    def get_metric_names(self) -> List[str]:
        """
        Retorna nombres de métricas que este calculador produce.
        
        Returns:
            Lista de 4 keys del dict de calculate()
        """
        return [
            'resultado_operativo_uyu',
            'resultado_operativo_usd',
            'resultado_neto_uyu',
            'resultado_neto_usd'
        ]

