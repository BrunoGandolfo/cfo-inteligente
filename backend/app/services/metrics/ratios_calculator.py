"""
RatiosCalculator - Calcula M11-M13: Rentabilidad

Calcula rentabilidad neta y rentabilidad por segmentos.
Depende de TotalsCalculator.

IMPORTANTE: Solo existe "Rentabilidad Neta" = (Ing - Gas) / Ing
NO existe "margen operativo" ni "margen neto" diferenciado.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import List, Dict, Any
from decimal import Decimal
from collections import defaultdict
from app.models import Operacion, TipoOperacion
from app.services.metrics.base_calculator import BaseCalculator


class RatiosCalculator(BaseCalculator):
    """
    Calcula M11-M13: Rentabilidad %.
    
    RESPONSABILIDAD: Calcular porcentajes de rentabilidad.
    DEPENDENCIA: Necesita totals (inyectado).
    
    Métricas calculadas:
    - M11: Rentabilidad Neta % = ((Ing - Gas) / Ing) × 100
    - M12: Rentabilidad por Área (Dict {area: %})
    - M13: Rentabilidad por Localidad (Dict {localidad: %})
    
    Fórmula rentabilidad:
        Rentabilidad % = ((Ingresos - Gastos) / Ingresos) × 100
        
        NOTA: Retiros y Distribuciones NO se restan.
        Son USOS de la utilidad, no costos.
    
    Ejemplo:
        >>> totals = {'ingresos_uyu': Decimal('100'), 'gastos_uyu': Decimal('30')}
        >>> calc = RatiosCalculator(ops, totals)
        >>> ratios = calc.calculate()
        >>> print(ratios['rentabilidad_neta'])
        70.0
    """
    
    def __init__(self, operaciones: List[Operacion], totals: Dict[str, Decimal]):
        """
        Constructor con Dependency Injection.
        
        Args:
            operaciones: Lista de operaciones (para calcular por segmento)
            totals: Dict con totales ya calculados
        """
        super().__init__(operaciones)
        self.totals = totals
    
    def calculate(self) -> Dict[str, Any]:
        """
        Calcula todos los ratios de rentabilidad.
        
        Returns:
            Dict con 3 métricas (1 float y 2 dicts)
        """
        return {
            'rentabilidad_neta': self._calc_rentabilidad_neta(),
            'rentabilidad_por_area': self._calc_rentabilidad_por_area(),
            'rentabilidad_por_localidad': self._calc_rentabilidad_por_localidad()
        }
    
    def get_metric_names(self) -> List[str]:
        """Retorna nombres de métricas."""
        return [
            'rentabilidad_neta',
            'rentabilidad_por_area',
            'rentabilidad_por_localidad'
        ]
    
    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS PRIVADOS (funciones puras, fáciles de testear)
    # ═══════════════════════════════════════════════════════════════
    
    def _calc_rentabilidad_neta(self) -> float:
        """
        Calcula rentabilidad neta: ((Ingresos - Gastos) / Ingresos) × 100
        
        NOTA: Retiros y Distribuciones NO se restan.
        Son USOS de la utilidad generada, no costos operativos.
        
        Returns:
            Float en porcentaje (ej: 54.35)
            0.0 si ingresos = 0 (evita división por cero)
        """
        ingresos = float(self.totals['ingresos_uyu'])
        gastos = float(self.totals['gastos_uyu'])
        
        if ingresos == 0:
            return 0.0
        
        return ((ingresos - gastos) / ingresos) * 100
    
    def _calc_rentabilidad_por_area(self) -> Dict[str, float]:
        """
        Calcula rentabilidad por área.
        
        Para cada área:
            Rentabilidad % = ((Ingresos_area - Gastos_area) / Ingresos_area) × 100
        
        Returns:
            Dict {nombre_area: rentabilidad%}
            Ejemplo: {'Notarial': 78.61, 'Jurídica': 75.94}
        """
        # Acumuladores por área
        ingresos_por_area = defaultdict(lambda: Decimal('0'))
        gastos_por_area = defaultdict(lambda: Decimal('0'))
        
        # Sumar operaciones por área
        for op in self.operaciones:
            area_nombre = op.area.nombre if op.area else 'Sin Área'
            
            if op.tipo_operacion == TipoOperacion.INGRESO:
                ingresos_por_area[area_nombre] += op.monto_uyu
            elif op.tipo_operacion == TipoOperacion.GASTO:
                gastos_por_area[area_nombre] += op.monto_uyu
        
        # Calcular rentabilidad por área
        rentabilidad = {}
        for area in ingresos_por_area.keys():
            ing = float(ingresos_por_area[area])
            gas = float(gastos_por_area.get(area, Decimal('0')))
            
            if ing > 0:
                rentabilidad[area] = ((ing - gas) / ing) * 100
            else:
                rentabilidad[area] = 0.0
        
        return rentabilidad
    
    def _calc_rentabilidad_por_localidad(self) -> Dict[str, float]:
        """
        Calcula rentabilidad por localidad.
        
        Similar a área pero agrupado por localidad.
        
        Returns:
            Dict {localidad: rentabilidad%}
            Ejemplo: {'MONTEVIDEO': 77.42, 'MERCEDES': 72.11}
        """
        # Acumuladores por localidad
        ingresos_por_localidad = defaultdict(lambda: Decimal('0'))
        gastos_por_localidad = defaultdict(lambda: Decimal('0'))
        
        # Sumar operaciones por localidad
        for op in self.operaciones:
            localidad_nombre = op.localidad.value if op.localidad else 'Sin Localidad'
            
            if op.tipo_operacion == TipoOperacion.INGRESO:
                ingresos_por_localidad[localidad_nombre] += op.monto_uyu
            elif op.tipo_operacion == TipoOperacion.GASTO:
                gastos_por_localidad[localidad_nombre] += op.monto_uyu
        
        # Calcular rentabilidad por localidad
        rentabilidad = {}
        for localidad in ingresos_por_localidad.keys():
            ing = float(ingresos_por_localidad[localidad])
            gas = float(gastos_por_localidad.get(localidad, Decimal('0')))
            
            if ing > 0:
                rentabilidad[localidad] = ((ing - gas) / ing) * 100
            else:
                rentabilidad[localidad] = 0.0
        
        return rentabilidad