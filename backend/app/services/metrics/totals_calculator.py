"""
TotalsCalculator - Calcula M1-M8: Totales absolutos

Calcula totales por tipo de operación y moneda.
Es el calculador base sin dependencias.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import List, Dict, Any
from decimal import Decimal
from app.models import TipoOperacion
from app.services.metrics.base_calculator import BaseCalculator


class TotalsCalculator(BaseCalculator):
    """
    Calcula M1-M8: Totales absolutos por tipo y moneda.
    
    RESPONSABILIDAD: Solo sumar operaciones.
    DEPENDENCIAS: Ninguna (independiente).
    
    Métricas calculadas:
    - M1: Total Ingresos UYU
    - M2: Total Ingresos USD
    - M3: Total Gastos UYU
    - M4: Total Gastos USD
    - M5: Total Retiros UYU
    - M6: Total Retiros USD
    - M7: Total Distribuciones UYU
    - M8: Total Distribuciones USD
    
    Ejemplo:
        >>> ops = [operacion1, operacion2, ...]
        >>> calc = TotalsCalculator(ops)
        >>> totals = calc.calculate()
        >>> print(totals['ingresos_uyu'])
        Decimal('114941988.84')
    """
    
    def calculate(self) -> Dict[str, Any]:
        """
        Suma operaciones por tipo y moneda.
        
        Returns:
            Dict con 8 métricas totales (todas en Decimal)
            
        Nota:
            Retorna Decimal para precisión financiera.
            NO redondea, mantiene 2 decimales de la BD.
        """
        return {
            'ingresos_uyu': self._sum_by_type(TipoOperacion.INGRESO, 'monto_uyu'),
            'ingresos_usd': self._sum_by_type(TipoOperacion.INGRESO, 'monto_usd'),
            'gastos_uyu': self._sum_by_type(TipoOperacion.GASTO, 'monto_uyu'),
            'gastos_usd': self._sum_by_type(TipoOperacion.GASTO, 'monto_usd'),
            'retiros_uyu': self._sum_by_type(TipoOperacion.RETIRO, 'monto_uyu'),
            'retiros_usd': self._sum_by_type(TipoOperacion.RETIRO, 'monto_usd'),
            'distribuciones_uyu': self._sum_by_type(TipoOperacion.DISTRIBUCION, 'monto_uyu'),
            'distribuciones_usd': self._sum_by_type(TipoOperacion.DISTRIBUCION, 'monto_usd')
        }
    
    def get_metric_names(self) -> List[str]:
        """
        Retorna nombres de métricas que este calculador produce.
        
        Returns:
            Lista de 8 keys del dict de calculate()
        """
        return [
            'ingresos_uyu',
            'ingresos_usd',
            'gastos_uyu',
            'gastos_usd',
            'retiros_uyu',
            'retiros_usd',
            'distribuciones_uyu',
            'distribuciones_usd'
        ]
    
    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS PRIVADOS (helpers internos)
    # ═══════════════════════════════════════════════════════════════
    
    def _sum_by_type(self, tipo: TipoOperacion, campo: str) -> Decimal:
        """
        Helper: suma campo específico para tipo de operación.
        
        Función pura: fácil de testear aisladamente.
        
        Args:
            tipo: Enum TipoOperacion (INGRESO, GASTO, RETIRO, DISTRIBUCION)
            campo: 'monto_uyu' o 'monto_usd'
            
        Returns:
            Suma total como Decimal (default Decimal('0') si vacío)
            
        Ejemplo:
            >>> self._sum_by_type(TipoOperacion.INGRESO, 'monto_uyu')
            Decimal('114941988.84')
        """
        total = Decimal('0')
        
        for op in self.operaciones:
            if op.tipo_operacion == tipo:
                valor = getattr(op, campo, Decimal('0'))
                if valor is not None:
                    total += valor
        
        return total

