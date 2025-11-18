"""
Anomaly Detector - Detector de anomalías en métricas financieras

Detecta automáticamente variaciones significativas, tendencias negativas,
y comportamientos fuera de parámetros normales.

Autor: Sistema CFO Inteligente
Fecha: Noviembre 2025
"""

from typing import List, Dict, Any
from app.utils.formatters import format_currency, format_percentage
from app.core.logger import get_logger

logger = get_logger(__name__)


class AnomalyDetector:
    """
    Detector de anomalías en métricas financieras.
    
    Identifica automáticamente:
    - Caídas de revenue >20%
    - Picos de gastos >30%
    - Compresión de márgenes >5pp
    - Tendencias negativas sostenidas
    
    Ejemplo:
        >>> detector = AnomalyDetector(threshold_percent=10.0)
        >>> anomalies = detector.detect_all(metricas_actual, metricas_anterior)
        >>> for a in anomalies:
        ...     print(f"{a['severidad']}: {a['mensaje']}")
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
    
    def detect_all(
        self, 
        metricas_actual: Dict[str, Any],
        metricas_anterior: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Detecta todas las anomalías en las métricas.
        
        Args:
            metricas_actual: Métricas del período actual
            metricas_anterior: Métricas del período anterior (opcional)
            
        Returns:
            Lista de anomalías detectadas, ordenadas por severidad
        """
        anomalies = []
        
        if not metricas_anterior:
            logger.debug("Sin período de comparación, solo anomalías absolutas")
            return self._detect_absolute_anomalies(metricas_actual)
        
        # Revenue drop >20%
        var_ingresos = metricas_actual.get('variacion_mom_ingresos', 0)
        if var_ingresos < -20:
            anomalies.append({
                'tipo': 'revenue_drop',
                'severidad': 'CRÍTICO',
                'metrica': 'Ingresos',
                'variacion_pct': var_ingresos,
                'valor_actual': metricas_actual.get('ingresos_uyu', 0),
                'valor_anterior': metricas_anterior.get('ingresos_uyu', 0),
                'mensaje': f"⚠️ Caída crítica de ingresos: {format_percentage(var_ingresos)}%",
                'explicacion': self._explain_revenue_drop(metricas_actual, metricas_anterior)
            })
        
        # Revenue surge >30%
        if var_ingresos > 30:
            anomalies.append({
                'tipo': 'revenue_surge',
                'severidad': 'ALTO',
                'metrica': 'Ingresos',
                'variacion_pct': var_ingresos,
                'mensaje': f"📈 Crecimiento excepcional de ingresos: {format_percentage(var_ingresos)}%",
                'explicacion': "Validar sostenibilidad del crecimiento"
            })
        
        # Expense spike >30%
        var_gastos = metricas_actual.get('variacion_mom_gastos', 0)
        if var_gastos > 30:
            anomalies.append({
                'tipo': 'expense_spike',
                'severidad': 'ALTO',
                'metrica': 'Gastos',
                'variacion_pct': var_gastos,
                'mensaje': f"⚠️ Pico de gastos: {format_percentage(var_gastos)}%",
                'explicacion': "Investigar causas del incremento"
            })
        
        # Margin compression >5pp
        var_margen = metricas_actual.get('variacion_mom_rentabilidad', 0)
        if var_margen < -5:
            anomalies.append({
                'tipo': 'margin_compression',
                'severidad': 'CRÍTICO',
                'metrica': 'Margen',
                'variacion_pp': var_margen,
                'mensaje': f"⚠️ Compresión de margen: {format_percentage(abs(var_margen))} puntos",
                'explicacion': "Analizar estructura de costos"
            })
        
        # Low margin absolute
        margen_neto = metricas_actual.get('margen_neto', 0)
        if margen_neto < 20:
            anomalies.append({
                'tipo': 'low_margin',
                'severidad': 'ALTO',
                'metrica': 'Margen Neto',
                'valor': margen_neto,
                'mensaje': f"⚠️ Margen bajo: {format_percentage(margen_neto)}%",
                'explicacion': "Por debajo de mínimo viable (20%)"
            })
        
        # Ordenar por severidad
        severidad_orden = {'CRÍTICO': 1, 'ALTO': 2, 'MEDIO': 3, 'BAJO': 4}
        anomalies.sort(key=lambda x: severidad_orden.get(x['severidad'], 5))
        
        logger.info(f"Anomalías detectadas: {len(anomalies)}")
        
        return anomalies
    
    def _detect_absolute_anomalies(self, metricas: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detecta anomalías sin comparación temporal"""
        anomalies = []
        
        # Margen bajo absoluto
        margen = metricas.get('margen_neto', 0)
        if margen < 20:
            anomalies.append({
                'tipo': 'low_margin_absolute',
                'severidad': 'ALTO',
                'metrica': 'Margen Neto',
                'valor': margen,
                'mensaje': f"Margen neto de {format_percentage(margen)}% por debajo de estándar",
                'explicacion': "Requiere optimización de estructura de costos"
            })
        
        return anomalies
    
    def _explain_revenue_drop(
        self, 
        actual: Dict[str, Any], 
        anterior: Dict[str, Any]
    ) -> str:
        """
        Genera explicación automática de caída de ingresos.
        
        Analiza por área para identificar drivers del cambio.
        """
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
                    'cambio_pp': cambio_pp
                })
        
        if cambios_areas:
            area_principal = max(cambios_areas, key=lambda x: abs(x['cambio_pp']))
            return (
                f"Principalmente explicado por cambios en área {area_principal['area']} "
                f"({'+' if area_principal['cambio_pp'] > 0 else ''}"
                f"{area_principal['cambio_pp']:.1f}pp de participación)."
            )
        
        return "Cambio distribuido uniformemente entre áreas."

