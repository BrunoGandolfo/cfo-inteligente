"""
LocalidadAnalyzer - Analiza métricas por localidad

Calcula utilidad neta, distribuciones y ratios por localidad.
CRÍTICO para detectar descapitalización por oficina.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import List, Dict, Any
from decimal import Decimal
from collections import defaultdict
from app.models import Operacion, TipoOperacion
from app.services.metrics.base_calculator import BaseCalculator


class LocalidadAnalyzer(BaseCalculator):
    """
    Analiza métricas financieras por localidad.
    
    RESPONSABILIDAD: Análisis específico por oficina (Montevideo/Mercedes).
    DEPENDENCIA: Necesita operaciones.
    
    Métricas calculadas:
    - Utilidad neta por localidad
    - Distribuciones por localidad
    - Ratio distribución/utilidad por localidad (CRÍTICO)
    
    Ratio Distribución/Utilidad:
        < 50%: ✅ Prudente (acumulando)
        50-80%: ⚠️ Moderado
        > 80%: ⚠️ Alto riesgo
        > 100%: 🚨 DESCAPITALIZANDO (distribuyendo más de lo ganado)
    """
    
    def __init__(self, operaciones: List[Operacion]):
        super().__init__(operaciones)
    
    def calculate(self) -> Dict[str, Any]:
        """
        Calcula análisis completo por localidad.
        
        Returns:
            Dict con análisis por localidad
        """
        return {
            'utilidad_neta_por_localidad': self._calc_utilidad_neta_por_localidad(),
            'distribuciones_por_localidad': self._calc_distribuciones_por_localidad(),
            'ratio_distribucion_utilidad': self._calc_ratio_distribucion_utilidad()
        }
    
    def get_metric_names(self) -> List[str]:
        return [
            'utilidad_neta_por_localidad',
            'distribuciones_por_localidad',
            'ratio_distribucion_utilidad'
        ]
    
    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS PRIVADOS
    # ═══════════════════════════════════════════════════════════════
    
    def _calc_utilidad_neta_por_localidad(self) -> Dict[str, float]:
        """
        Calcula utilidad neta por localidad.
        
        Para cada localidad:
            Utilidad = Ingresos - Gastos
        
        Returns:
            Dict {localidad: utilidad}
            Ejemplo: {'MONTEVIDEO': 123032427.0, 'MERCEDES': 137442777.0}
        """
        # Acumuladores
        ingresos_loc = defaultdict(lambda: Decimal('0'))
        gastos_loc = defaultdict(lambda: Decimal('0'))
        
        for op in self.operaciones:
            loc = op.localidad.value if op.localidad else 'Sin Localidad'
            
            if op.tipo_operacion == TipoOperacion.INGRESO:
                ingresos_loc[loc] += op.monto_uyu
            elif op.tipo_operacion == TipoOperacion.GASTO:
                gastos_loc[loc] += op.monto_uyu
        
        # Calcular utilidad
        utilidad = {}
        for loc in ingresos_loc.keys():
            ing = float(ingresos_loc[loc])
            gas = float(gastos_loc.get(loc, Decimal('0')))
            utilidad[loc] = ing - gas
        
        return utilidad
    
    def _calc_distribuciones_por_localidad(self) -> Dict[str, float]:
        """
        Calcula distribuciones totales por localidad.
        
        Returns:
            Dict {localidad: distribuciones}
            Ejemplo: {'MONTEVIDEO': 4237598.0, 'MERCEDES': 9058919.0}
        """
        distribuciones_loc = defaultdict(lambda: Decimal('0'))
        
        for op in self.operaciones:
            if op.tipo_operacion == TipoOperacion.DISTRIBUCION:
                loc = op.localidad.value if op.localidad else 'Sin Localidad'
                distribuciones_loc[loc] += op.monto_uyu
        
        return {loc: float(monto) for loc, monto in distribuciones_loc.items()}
    
    def _calc_ratio_distribucion_utilidad(self) -> Dict[str, Dict[str, Any]]:
        """
        Calcula ratio distribución/utilidad por localidad.
        
        CRÍTICO para detectar descapitalización.
        
        Returns:
            Dict {localidad: {
                'utilidad': float,
                'distribuciones': float,
                'ratio_porcentaje': float,
                'estado': str
            }}
        """
        utilidad_loc = self._calc_utilidad_neta_por_localidad()
        dist_loc = self._calc_distribuciones_por_localidad()
        
        ratios = {}
        for loc, utilidad in utilidad_loc.items():
            distribuciones = dist_loc.get(loc, 0.0)
            
            if utilidad > 0:
                ratio_pct = (distribuciones / utilidad) * 100
                
                # Determinar estado
                if ratio_pct > 100:
                    estado = 'DESCAPITALIZANDO'
                elif ratio_pct > 80:
                    estado = 'ALTO_RIESGO'
                elif ratio_pct > 50:
                    estado = 'MODERADO'
                else:
                    estado = 'PRUDENTE'
                
                ratios[loc] = {
                    'utilidad': utilidad,
                    'distribuciones': distribuciones,
                    'ratio_porcentaje': ratio_pct,
                    'estado': estado
                }
            else:
                ratios[loc] = {
                    'utilidad': utilidad,
                    'distribuciones': distribuciones,
                    'ratio_porcentaje': 0.0,
                    'estado': 'SIN_DATOS'
                }
        
        return ratios
