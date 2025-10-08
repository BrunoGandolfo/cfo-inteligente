"""
DistributionCalculator - Calcula M15-M17: Distribución porcentual

Calcula cómo se distribuyen ingresos y distribuciones por segmentos.
Depende de TotalsCalculator.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import List, Dict, Any
from decimal import Decimal
from collections import defaultdict
from app.models import Operacion, TipoOperacion
from app.services.metrics.base_calculator import BaseCalculator


class DistributionCalculator(BaseCalculator):
    """
    Calcula M15-M17: Distribución porcentual.
    
    RESPONSABILIDAD: Calcular porcentajes de distribución.
    DEPENDENCIA: Necesita totals (inyectado).
    
    Métricas calculadas:
    - M15: % Ingresos por Área (Dict {area: %})
    - M16: % Ingresos por Localidad (Dict {localidad: %})
    - M17: % Distribución por Socio (Dict {socio: %})
    
    Fórmula:
        % Area = (Ingresos_area / Total_ingresos) × 100
    
    Ejemplo:
        >>> calc = DistributionCalculator(ops, totals)
        >>> dist = calc.calculate()
        >>> print(dist['porcentaje_ingresos_por_area'])
        {'Notarial': 45.5, 'Jurídica': 34.2, 'Contable': 20.3}
    """
    
    def __init__(self, operaciones: List[Operacion], totals: Dict[str, Decimal]):
        """
        Constructor con Dependency Injection.
        
        Args:
            operaciones: Lista de operaciones (para agrupar)
            totals: Dict con totales ya calculados
        """
        super().__init__(operaciones)
        self.totals = totals
    
    def calculate(self) -> Dict[str, Any]:
        """
        Calcula todas las distribuciones porcentuales.
        
        Returns:
            Dict con 3 métricas (todas Dict {segmento: porcentaje})
        """
        return {
            'porcentaje_ingresos_por_area': self._calc_porcentaje_ingresos_por_area(),
            'porcentaje_ingresos_por_localidad': self._calc_porcentaje_ingresos_por_localidad(),
            'porcentaje_distribucion_por_socio': self._calc_porcentaje_distribucion_por_socio()
        }
    
    def get_metric_names(self) -> List[str]:
        """Retorna nombres de métricas."""
        return [
            'porcentaje_ingresos_por_area',
            'porcentaje_ingresos_por_localidad',
            'porcentaje_distribucion_por_socio'
        ]
    
    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS PRIVADOS
    # ═══════════════════════════════════════════════════════════════
    
    def _calc_porcentaje_ingresos_por_area(self) -> Dict[str, float]:
        """
        Calcula % de ingresos por área.
        
        Para cada área:
            % = (Ingresos_area / Total_ingresos) × 100
        
        Returns:
            Dict {area: porcentaje}
            Ejemplo: {'Notarial': 45.5, 'Jurídica': 34.2}
        """
        total_ingresos = float(self.totals['ingresos_uyu'])
        
        if total_ingresos == 0:
            return {}
        
        # Acumular ingresos por área
        ingresos_por_area = defaultdict(lambda: Decimal('0'))
        
        for op in self.operaciones:
            if op.tipo_operacion == TipoOperacion.INGRESO:
                area_nombre = op.area.nombre if op.area else 'Sin Área'
                ingresos_por_area[area_nombre] += op.monto_uyu
        
        # Calcular porcentajes
        porcentajes = {}
        for area, monto in ingresos_por_area.items():
            porcentajes[area] = (float(monto) / total_ingresos) * 100
        
        return porcentajes
    
    def _calc_porcentaje_ingresos_por_localidad(self) -> Dict[str, float]:
        """
        Calcula % de ingresos por localidad.
        
        Returns:
            Dict {localidad: porcentaje}
            Ejemplo: {'MONTEVIDEO': 65.0, 'MERCEDES': 35.0}
        """
        total_ingresos = float(self.totals['ingresos_uyu'])
        
        if total_ingresos == 0:
            return {}
        
        # Acumular ingresos por localidad
        ingresos_por_localidad = defaultdict(lambda: Decimal('0'))
        
        for op in self.operaciones:
            if op.tipo_operacion == TipoOperacion.INGRESO:
                localidad_nombre = op.localidad.value if op.localidad else 'Sin Localidad'
                ingresos_por_localidad[localidad_nombre] += op.monto_uyu
        
        # Calcular porcentajes
        porcentajes = {}
        for localidad, monto in ingresos_por_localidad.items():
            porcentajes[localidad] = (float(monto) / total_ingresos) * 100
        
        return porcentajes
    
    def _calc_porcentaje_distribucion_por_socio(self) -> Dict[str, float]:
        """
        Calcula % de distribución por socio.
        
        Lógica:
        1. Buscar operaciones de tipo DISTRIBUCION
        2. Para cada una, sumar los montos de distribuciones_detalle por socio
        3. Calcular porcentaje sobre total de distribuciones
        
        Returns:
            Dict {socio: porcentaje}
            Ejemplo: {'Juan Pérez': 33.33, 'María López': 33.33, 'Carlos García': 33.34}
            
        Nota:
            Si no hay distribuciones, retorna dict vacío.
            Si una distribución no tiene detalles, se ignora.
        """
        total_distribuciones = float(self.totals['distribuciones_uyu'])
        
        if total_distribuciones == 0:
            return {}
        
        # Acumular distribuciones por socio
        # Operacion.distribuciones es la relación a DistribucionDetalle
        distribuciones_por_socio = defaultdict(lambda: Decimal('0'))
        
        for op in self.operaciones:
            if op.tipo_operacion == TipoOperacion.DISTRIBUCION:
                # Iterar sobre los detalles de distribución (relación backref)
                if hasattr(op, 'distribuciones') and op.distribuciones:
                    for detalle in op.distribuciones:
                        socio_nombre = detalle.socio.nombre if detalle.socio else 'Sin Socio'
                        distribuciones_por_socio[socio_nombre] += detalle.monto_uyu
        
        # Calcular porcentajes
        porcentajes = {}
        for socio, monto in distribuciones_por_socio.items():
            porcentajes[socio] = (float(monto) / total_distribuciones) * 100
        
        return porcentajes

