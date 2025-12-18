"""
TrendsCalculator - Calcula M21-M26: Tendencias y proyecciones

Calcula variaciones temporales, promedios móviles y proyecciones.
Depende de TotalsCalculator y RatiosCalculator.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from app.models import Operacion
from app.services.metrics.base_calculator import BaseCalculator
from app.utils.stats_calculator import (
    linear_regression_with_confidence,
    calculate_moving_average
)


class TrendsCalculator(BaseCalculator):
    """
    Calcula M21-M26: Tendencias temporales y proyecciones.
    
    RESPONSABILIDAD: Calcular variaciones, promedios móviles y proyecciones.
    DEPENDENCIAS: Necesita totals, ratios (inyectados).
                  Opcionalmente comparacion_totals y comparacion_ratios.
    
    Métricas calculadas:
    - M21: Variación MoM Ingresos (% cambio vs período anterior)
    - M22: Variación MoM Gastos (% cambio vs período anterior)
    - M23: Variación MoM Rentabilidad (puntos de cambio)
    - M24: Promedio Móvil 3 meses (ingresos)
    - M25: Promedio Móvil 6 meses (ingresos)
    - M26: Proyección próximos 3 meses (regresión lineal)
    
    Notas:
    - M21-M23 requieren datos de comparación
    - M24-M25 requieren histórico (NO implementado aquí, se calcula en nivel superior)
    - M26 usa regresión lineal con scipy
    
    Ejemplo:
        >>> calc = TrendsCalculator(ops, totals, ratios, comp_totals, comp_ratios)
        >>> trends = calc.calculate()
        >>> print(trends['variacion_mom_ingresos'])
        15.5  # +15.5% vs mes anterior
    """
    
    def __init__(
        self,
        operaciones: List[Operacion],
        totals: Dict[str, Decimal],
        ratios: Dict[str, Any],
        comparacion_totals: Optional[Dict[str, Decimal]] = None,
        comparacion_ratios: Optional[Dict[str, Any]] = None,
        historico_mensual: Optional[List[Decimal]] = None,
        totals_yoy: Optional[Dict[str, Decimal]] = None,
        totals_qoq: Optional[Dict[str, Decimal]] = None
    ):
        """
        Constructor con Dependency Injection.
        
        Args:
            operaciones: Lista de operaciones del período actual
            totals: Totales del período actual
            ratios: Ratios del período actual
            comparacion_totals: Totales del período de comparación (opcional)
            comparacion_ratios: Ratios del período de comparación (opcional)
            historico_mensual: Lista de ingresos mensuales históricos (opcional)
                              Para calcular proyecciones. Ej: [100000, 120000, 115000, ...]
        """
        super().__init__(operaciones)
        self.totals = totals
        self.ratios = ratios
        self.comparacion_totals = comparacion_totals
        self.comparacion_ratios = comparacion_ratios
        self.historico_mensual = historico_mensual or []
        self.totals_yoy = totals_yoy
        self.totals_qoq = totals_qoq
    
    def calculate(self) -> Dict[str, Any]:
        """
        Calcula métricas de tendencias.
        
        Returns:
            Dict con hasta 6 métricas (algunas pueden ser None si no hay datos)
        """
        # Calcular proyección completa
        proyeccion = self._calc_proyeccion_3m()
        
        return {
            'variacion_mom_ingresos': self._calc_variacion_mom_ingresos(),
            'variacion_mom_gastos': self._calc_variacion_mom_gastos(),
            'variacion_mom_rentabilidad': self._calc_variacion_mom_rentabilidad(),
            'variacion_yoy_ingresos': self._calc_variacion_yoy_ingresos(),
            'variacion_yoy_gastos': self._calc_variacion_yoy_gastos(),
            'variacion_qoq_ingresos': self._calc_variacion_qoq_ingresos(),
            'promedio_movil_3m': self._calc_promedio_movil(window=3),
            'promedio_movil_6m': self._calc_promedio_movil(window=6),
            'proyeccion_proximos_3m': proyeccion['promedio'] if proyeccion else None,
            'proyeccion_proximos_3m_upper': proyeccion['upper'] if proyeccion else None,
            'proyeccion_proximos_3m_lower': proyeccion['lower'] if proyeccion else None,
            'proyeccion_r2_score': proyeccion['r2_score'] if proyeccion else None,
            'proyeccion_tendencia_mensual': proyeccion['slope'] if proyeccion else None,
            'proyeccion_meses_historico': proyeccion['meses_historico'] if proyeccion else None
        }
    
    def get_metric_names(self) -> List[str]:
        """Retorna nombres de métricas."""
        return [
            'variacion_mom_ingresos',
            'variacion_mom_gastos',
            'variacion_mom_rentabilidad',
            'promedio_movil_3m',
            'promedio_movil_6m',
            'proyeccion_proximos_3m',
            'proyeccion_proximos_3m_upper',
            'proyeccion_proximos_3m_lower',
            'proyeccion_r2_score',
            'proyeccion_tendencia_mensual',
            'proyeccion_meses_historico'
        ]
    
    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS PRIVADOS
    # ═══════════════════════════════════════════════════════════════
    
    def _calc_variacion_mom_ingresos(self) -> Optional[float]:
        """
        Calcula variación MoM (Month over Month) de ingresos.
        
        Fórmula:
            Variación % = ((Actual - Anterior) / Anterior) × 100
        
        Returns:
            Float con variación en % (ej: 15.5 = +15.5%)
            None si no hay datos de comparación
        """
        if not self.comparacion_totals:
            return None
        
        actual = float(self.totals['ingresos_uyu'])
        anterior = float(self.comparacion_totals['ingresos_uyu'])
        
        if anterior == 0:
            return None
        
        return ((actual - anterior) / anterior) * 100
    
    def _calc_variacion_mom_gastos(self) -> Optional[float]:
        """
        Calcula variación MoM de gastos.
        
        Returns:
            Float con variación en %
            None si no hay datos de comparación
        """
        if not self.comparacion_totals:
            return None
        
        actual = float(self.totals['gastos_uyu'])
        anterior = float(self.comparacion_totals['gastos_uyu'])
        
        if anterior == 0:
            return None
        
        return ((actual - anterior) / anterior) * 100
    
    def _calc_variacion_mom_rentabilidad(self) -> Optional[float]:
        """
        Calcula variación MoM de rentabilidad en PUNTOS PORCENTUALES.
        
        NO es variación %, es diferencia absoluta de porcentajes.
        
        Ejemplo:
            Mes anterior: 30% rentabilidad
            Mes actual: 35% rentabilidad
            Variación: +5 puntos porcentuales (pp)
        
        Returns:
            Float con variación en puntos (ej: 5.0 = +5pp)
            None si no hay datos de comparación
        """
        if not self.comparacion_ratios:
            return None
        
        margen_actual = self.ratios.get('rentabilidad_neta', self.ratios.get('margen_operativo', 0))
        margen_anterior = self.comparacion_ratios.get('rentabilidad_neta', self.comparacion_ratios.get('margen_operativo', 0))
        
        # Diferencia absoluta (no porcentual)
        return margen_actual - margen_anterior
    
    def _calc_variacion_yoy_ingresos(self) -> Optional[float]:
        """
        Calcula variación Year-over-Year de ingresos.
        
        Returns:
            Float con variación en % (ej: 15.5 = +15.5%)
            None si no hay datos YoY
        """
        if not self.totals_yoy:
            return None
        
        actual = float(self.totals['ingresos_uyu'])
        anterior = float(self.totals_yoy['ingresos_uyu'])
        
        if anterior == 0:
            return None
        
        return ((actual - anterior) / anterior) * 100
    
    def _calc_variacion_yoy_gastos(self) -> Optional[float]:
        """
        Calcula variación Year-over-Year de gastos.
        
        Returns:
            Float con variación en %
            None si no hay datos YoY
        """
        if not self.totals_yoy:
            return None
        
        actual = float(self.totals['gastos_uyu'])
        anterior = float(self.totals_yoy['gastos_uyu'])
        
        if anterior == 0:
            return None
        
        return ((actual - anterior) / anterior) * 100
    
    def _calc_variacion_qoq_ingresos(self) -> Optional[float]:
        """
        Calcula variación Quarter-over-Quarter de ingresos.
        
        Returns:
            Float con variación en %
            None si no hay datos QoQ
        """
        if not self.totals_qoq:
            return None
        
        actual = float(self.totals['ingresos_uyu'])
        anterior = float(self.totals_qoq['ingresos_uyu'])
        
        if anterior == 0:
            return None
        
        return ((actual - anterior) / anterior) * 100
    
    def _calc_promedio_movil(self, window: int) -> Optional[float]:
        """
        Calcula promedio móvil de ingresos.
        
        Requiere histórico mensual de al menos `window` meses.
        
        Args:
            window: Tamaño de ventana (3 o 6 meses)
            
        Returns:
            Float con promedio móvil
            None si no hay suficiente histórico
        """
        if not self.historico_mensual or len(self.historico_mensual) < window:
            return None
        
        # Usar función de stats_calculator
        valores = [float(v) for v in self.historico_mensual]
        promedios = calculate_moving_average(valores, window=window)
        
        # Retornar el último promedio (más reciente)
        if promedios and promedios[-1] is not None:
            return promedios[-1]
        
        return None
    
    def _calc_proyeccion_3m(self) -> Optional[Dict[str, Any]]:
        """
        Calcula proyección de ingresos para próximos 3 meses usando regresión lineal.
        
        Requiere al menos 3 meses de histórico para calcular tendencia.
        
        Returns:
            Dict con proyección completa (promedio, upper, lower, r2, slope, meses)
            None si no hay suficiente histórico
            
        Método:
            1. Usa histórico mensual como serie temporal
            2. Aplica regresión lineal (scipy)
            3. Proyecta próximos 3 valores con intervalos de confianza
            4. Retorna dict completo para visualización de escenarios
        """
        if not self.historico_mensual or len(self.historico_mensual) < 3:
            return None
        
        try:
            # Preparar datos
            n = len(self.historico_mensual)
            x_values = list(range(1, n + 1))  # [1, 2, 3, ..., n]
            y_values = [float(v) for v in self.historico_mensual]
            x_future = [n + 1, n + 2, n + 3]  # Próximos 3 meses
            
            # Regresión lineal con intervalos de confianza
            y_pred, y_upper, y_lower, r2, slope = linear_regression_with_confidence(
                x_values,
                y_values,
                x_future,
                confidence_level=0.95
            )
            
            # Retornar dict completo (no solo promedio)
            return {
                'promedio': sum(y_pred) / len(y_pred),
                'upper': sum(y_upper) / len(y_upper),
                'lower': sum(y_lower) / len(y_lower),
                'r2_score': r2,
                'slope': slope,  # Tendencia mensual
                'meses_historico': n
            }
            
        except Exception:
            # Si regresión falla (datos insuficientes, etc), retornar None
            return None

