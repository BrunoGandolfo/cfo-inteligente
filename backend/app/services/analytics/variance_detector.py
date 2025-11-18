"""
Variance Detector - Detector de variaciones significativas

Detecta y explica variaciones >10% entre períodos.
Genera variance analysis automático para reportes.

Autor: Sistema CFO Inteligente
Fecha: Noviembre 2025
"""

from typing import List, Dict, Any
from app.utils.formatters import format_currency, format_percentage
from app.core.logger import get_logger

logger = get_logger(__name__)


class VarianceDetector:
    """
    Detector de variaciones significativas entre períodos.
    
    Identifica cambios >threshold y genera explicaciones automáticas.
    
    Ejemplo:
        >>> detector = VarianceDetector(threshold_percent=10.0)
        >>> variances = detector.detect_variances(metricas_actual, metricas_anterior)
        >>> for v in variances:
        ...     print(f"{v['severidad']}: {v['metrica']} {v['variacion_pct']:.1f}%")
    """
    
    def __init__(
        self, 
        threshold_percent: float = 10.0, 
        threshold_margin_pp: float = 5.0
    ):
        """
        Constructor.
        
        Args:
            threshold_percent: Umbral de variación % para revenue/expenses
            threshold_margin_pp: Umbral de variación en puntos para márgenes
        """
        self.threshold_percent = threshold_percent
        self.threshold_margin_pp = threshold_margin_pp
        self.logger = logger
    
    def detect_variances(
        self, 
        metricas_actual: Dict[str, Any],
        metricas_anterior: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Detecta variaciones significativas entre dos períodos.
        
        Args:
            metricas_actual: Métricas del período actual
            metricas_anterior: Métricas del período anterior
            
        Returns:
            Lista de variaciones detectadas con explicación
        """
        variances = []
        
        # Revenue variance
        var_ingresos = metricas_actual.get('variacion_mom_ingresos', 0)
        if var_ingresos and abs(var_ingresos) > self.threshold_percent:
            ingresos_actual = metricas_actual.get('ingresos_uyu', 0)
            ingresos_anterior = metricas_anterior.get('ingresos_uyu', 0)
            delta = ingresos_actual - ingresos_anterior
            
            variances.append({
                'metrica': 'Ingresos',
                'tipo': 'revenue',
                'variacion_pct': var_ingresos,
                'valor_actual': ingresos_actual,
                'valor_anterior': ingresos_anterior,
                'delta_absoluto': delta,
                'severidad': 'CRÍTICO' if abs(var_ingresos) > 20 else 'ALTO',
                'direccion': 'favorable' if var_ingresos > 0 else 'desfavorable',
                'explicacion': self._generate_revenue_explanation(
                    var_ingresos, 
                    metricas_actual, 
                    metricas_anterior
                ),
                'accion': self._get_action_required('revenue', var_ingresos)
            })
        
        # Expense variance
        var_gastos = metricas_actual.get('variacion_mom_gastos', 0)
        if var_gastos and abs(var_gastos) > self.threshold_percent:
            gastos_actual = metricas_actual.get('gastos_uyu', 0)
            gastos_anterior = metricas_anterior.get('gastos_uyu', 0)
            delta = gastos_actual - gastos_anterior
            
            variances.append({
                'metrica': 'Gastos',
                'tipo': 'expense',
                'variacion_pct': var_gastos,
                'valor_actual': gastos_actual,
                'valor_anterior': gastos_anterior,
                'delta_absoluto': delta,
                'severidad': 'ALTO' if abs(var_gastos) > 20 else 'MEDIO',
                'direccion': 'desfavorable' if var_gastos > 0 else 'favorable',
                'explicacion': self._generate_expense_explanation(var_gastos, delta),
                'accion': self._get_action_required('expense', var_gastos)
            })
        
        # Margin variance
        var_margen = metricas_actual.get('variacion_mom_rentabilidad', 0)
        if var_margen and abs(var_margen) > self.threshold_margin_pp:
            margen_actual = metricas_actual.get('margen_neto', 0)
            margen_anterior = metricas_anterior.get('margen_neto', 0)
            
            variances.append({
                'metrica': 'Margen Neto',
                'tipo': 'margin',
                'variacion_pct': var_margen,  # En puntos porcentuales
                'valor_actual': margen_actual,
                'valor_anterior': margen_anterior,
                'delta_absoluto': var_margen,
                'severidad': 'CRÍTICO' if abs(var_margen) > 10 else 'ALTO',
                'direccion': 'favorable' if var_margen > 0 else 'desfavorable',
                'explicacion': self._generate_margin_explanation(var_margen, metricas_actual),
                'accion': self._get_action_required('margin', var_margen)
            })
        
        # Ordenar por severidad
        severidad_orden = {'CRÍTICO': 1, 'ALTO': 2, 'MEDIO': 3, 'BAJO': 4}
        variances.sort(key=lambda x: severidad_orden.get(x['severidad'], 5))
        
        self.logger.info(f"Variaciones detectadas: {len(variances)}")
        
        return variances
    
    def _generate_revenue_explanation(
        self,
        var_pct: float,
        actual: Dict[str, Any],
        anterior: Dict[str, Any]
    ) -> str:
        """Genera explicación automática de variación de ingresos"""
        
        # Analizar por área
        areas_actual = actual.get('porcentaje_ingresos_por_area', {})
        areas_anterior = anterior.get('porcentaje_ingresos_por_area', {})
        
        cambios_areas = []
        for area, pct_actual in areas_actual.items():
            pct_anterior = areas_anterior.get(area, 0)
            cambio_pp = pct_actual - pct_anterior
            if abs(cambio_pp) > 5:  # >5pp de cambio
                cambios_areas.append({
                    'area': area,
                    'cambio_pp': cambio_pp,
                    'pct_actual': pct_actual
                })
        
        if cambios_areas:
            # Ordenar por cambio absoluto
            cambios_areas.sort(key=lambda x: abs(x['cambio_pp']), reverse=True)
            area_principal = cambios_areas[0]
            
            explicacion = (
                f"Principalmente explicado por cambios en área {area_principal['area']} "
                f"({'+' if area_principal['cambio_pp'] > 0 else ''}"
                f"{area_principal['cambio_pp']:.1f}pp de participación, "
                f"ahora {format_percentage(area_principal['pct_actual'])}% del total)."
            )
            
            if len(cambios_areas) > 1:
                explicacion += f" También impacto en {cambios_areas[1]['area']}."
            
            return explicacion
        
        return "Cambio distribuido uniformemente entre áreas de práctica."
    
    def _generate_expense_explanation(self, var_pct: float, delta: float) -> str:
        """Genera explicación de variación de gastos"""
        
        if var_pct > 0:
            return (
                f"Incremento de {format_currency(delta)} respecto al período anterior. "
                f"Requiere análisis detallado de categorías de gasto."
            )
        else:
            return (
                f"Reducción de {format_currency(abs(delta))} vs período anterior. "
                f"Evidencia control efectivo de costos operativos."
            )
    
    def _generate_margin_explanation(self, var_pp: float, metricas: Dict) -> str:
        """Genera explicación de variación de margen"""
        
        var_ingresos = metricas.get('variacion_mom_ingresos', 0)
        var_gastos = metricas.get('variacion_mom_gastos', 0)
        
        if var_pp > 0:
            # Margen mejoró
            if var_ingresos > var_gastos:
                return "Expansión de margen impulsada por crecimiento de ingresos superior a gastos."
            elif var_gastos < 0:
                return "Mejora de margen explicada por control de gastos y eficiencia operativa."
            else:
                return "Expansión de margen por combinación de crecimiento e eficiencia."
        else:
            # Margen comprimido
            if var_gastos > var_ingresos:
                return "Compresión de margen causada por crecimiento de gastos superior a ingresos."
            elif var_ingresos < 0:
                return "Deterioro de margen explicado por caída de ingresos."
            else:
                return "Compresión de margen requiere análisis detallado de estructura de costos."
    
    def _get_action_required(self, tipo: str, variacion: float) -> str:
        """Retorna acción requerida según tipo y severidad"""
        
        severidad_alta = abs(variacion) > 20
        
        if tipo == 'revenue':
            if variacion < -20:
                return "Investigar causas inmediatamente"
            elif variacion > 20:
                return "Validar sostenibilidad"
            else:
                return "Monitorear tendencia"
        
        elif tipo == 'expense':
            if variacion > 20:
                return "Auditar categorías de gasto"
            else:
                return "Monitorear estructura de costos"
        
        elif tipo == 'margin':
            if variacion < -10:
                return "Plan de acción correctiva"
            elif variacion < -5:
                return "Revisar pricing y costos"
            else:
                return "Monitorear"
        
        return "Monitorear"

