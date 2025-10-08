"""
EfficiencyCalculator - Calcula M18-M20: Métricas de eficiencia

Calcula tickets promedio y cantidades de operaciones.
Depende de TotalsCalculator.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import List, Dict, Any
from decimal import Decimal
from app.models import Operacion, TipoOperacion
from app.services.metrics.base_calculator import BaseCalculator


class EfficiencyCalculator(BaseCalculator):
    """
    Calcula M18-M20: Métricas de eficiencia.
    
    RESPONSABILIDAD: Calcular promedios y conteos.
    DEPENDENCIA: Necesita totals (inyectado).
    
    Métricas calculadas:
    - M18: Ticket Promedio Ingreso = Total_ingresos / Cantidad_ingresos
    - M19: Ticket Promedio Gasto = Total_gastos / Cantidad_gastos
    - M20: Cantidad de Operaciones (total, ingresos, gastos)
    
    Utilidad:
    - Ticket promedio indica tamaño típico de transacción
    - Cantidad de operaciones indica volumen de actividad
    - Útil para detectar cambios en patrones operativos
    
    Ejemplo:
        >>> calc = EfficiencyCalculator(ops, totals)
        >>> eff = calc.calculate()
        >>> print(eff['ticket_promedio_ingreso'])
        12500.50
    """
    
    def __init__(self, operaciones: List[Operacion], totals: Dict[str, Decimal]):
        """
        Constructor con Dependency Injection.
        
        Args:
            operaciones: Lista de operaciones (para contar)
            totals: Dict con totales ya calculados
        """
        super().__init__(operaciones)
        self.totals = totals
    
    def calculate(self) -> Dict[str, Any]:
        """
        Calcula métricas de eficiencia.
        
        Returns:
            Dict con 5 métricas (3 floats + 3 ints)
        """
        # Contar operaciones por tipo
        cantidades = self._contar_operaciones()
        
        return {
            'ticket_promedio_ingreso': self._calc_ticket_promedio(
                self.totals['ingresos_uyu'],
                cantidades['cantidad_ingresos']
            ),
            'ticket_promedio_gasto': self._calc_ticket_promedio(
                self.totals['gastos_uyu'],
                cantidades['cantidad_gastos']
            ),
            'cantidad_operaciones': cantidades['cantidad_operaciones'],
            'cantidad_ingresos': cantidades['cantidad_ingresos'],
            'cantidad_gastos': cantidades['cantidad_gastos']
        }
    
    def get_metric_names(self) -> List[str]:
        """Retorna nombres de métricas."""
        return [
            'ticket_promedio_ingreso',
            'ticket_promedio_gasto',
            'cantidad_operaciones',
            'cantidad_ingresos',
            'cantidad_gastos'
        ]
    
    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS PRIVADOS (funciones puras)
    # ═══════════════════════════════════════════════════════════════
    
    def _contar_operaciones(self) -> Dict[str, int]:
        """
        Cuenta operaciones por tipo.
        
        Returns:
            Dict con conteos:
            - cantidad_operaciones: Total de todas las operaciones
            - cantidad_ingresos: Solo ingresos
            - cantidad_gastos: Solo gastos
        """
        cantidad_ingresos = 0
        cantidad_gastos = 0
        cantidad_total = len(self.operaciones)
        
        for op in self.operaciones:
            if op.tipo_operacion == TipoOperacion.INGRESO:
                cantidad_ingresos += 1
            elif op.tipo_operacion == TipoOperacion.GASTO:
                cantidad_gastos += 1
        
        return {
            'cantidad_operaciones': cantidad_total,
            'cantidad_ingresos': cantidad_ingresos,
            'cantidad_gastos': cantidad_gastos
        }
    
    def _calc_ticket_promedio(self, total: Decimal, cantidad: int) -> float:
        """
        Calcula ticket promedio: Total / Cantidad
        
        Función pura: fácil de testear.
        
        Args:
            total: Monto total (Decimal)
            cantidad: Cantidad de operaciones (int)
            
        Returns:
            Float con promedio
            0.0 si cantidad = 0 (evita división por cero)
            
        Ejemplo:
            >>> self._calc_ticket_promedio(Decimal('100000'), 8)
            12500.0
        """
        if cantidad == 0:
            return 0.0
        
        return float(total) / cantidad

