"""
MonthlyAggregator - Agregación de datos financieros mensuales

Implementación concreta de BaseAggregator para reportes mensuales.
Agrega métricas específicas del mes: días laborables, semanas, comparación MoM.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from datetime import date, timedelta
from typing import Dict, List, Any
from calendar import monthrange

from .base_aggregator import BaseAggregator
from app.models import Operacion, TipoOperacion


class MonthlyAggregator(BaseAggregator):
    """
    Agregador específico para períodos mensuales.
    
    Métricas adicionales:
    - Días laborables del mes
    - Semanas completas
    - Promedio diario
    - Comparación con mes anterior (MoM)
    - Comparación con mismo mes año anterior (YoY)
    """
    
    def get_period_type(self) -> str:
        """Tipo de período: monthly"""
        return 'monthly'
    
    def validate_period(self, start_date: date, end_date: date) -> None:
        """
        Valida que el período sea exactamente 1 mes calendario.
        
        Verifica:
        - start_date es primer día del mes
        - end_date es último día del mes
        - Mismo mes y año
        
        Raises:
            ValueError: Si el período no es válido
        """
        # Verificar que start_date es día 1
        if start_date.day != 1:
            raise ValueError(f"start_date debe ser día 1 del mes, recibido: {start_date}")
        
        # Calcular último día del mes
        ultimo_dia = monthrange(start_date.year, start_date.month)[1]
        
        # Verificar que end_date es último día
        if end_date != date(start_date.year, start_date.month, ultimo_dia):
            raise ValueError(
                f"end_date debe ser último día del mes ({ultimo_dia}), recibido: {end_date}"
            )
        
        # Verificar mismo mes y año
        if start_date.month != end_date.month or start_date.year != end_date.year:
            raise ValueError("start_date y end_date deben estar en el mismo mes")
        
        self.logger.debug(f"Período mensual válido: {self._get_month_label(start_date)}")
    
    def calculate_period_specific_metrics(
        self, 
        operaciones: List[Operacion],
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Calcula métricas específicas del mes:
        - Días del mes
        - Días laborables (lun-vie)
        - Semanas completas
        - Promedio diario de facturación
        - Comparación MoM (Month over Month)
        - Comparación YoY (Year over Year)
        """
        # Días del mes
        dias_mes = (end_date - start_date).days + 1
        
        # Contar días laborables (lunes=0, domingo=6)
        dias_laborables = sum(
            1 for i in range(dias_mes)
            if (start_date + timedelta(days=i)).weekday() < 5  # 0-4 = lun-vie
        )
        
        # Semanas completas (aproximado)
        semanas_completas = dias_mes // 7
        
        # Promedio diario
        total_ingresos = sum(
            float(op.monto_uyu) for op in operaciones 
            if op.tipo_operacion == TipoOperacion.INGRESO
        ) or 0.0
        
        promedio_diario = total_ingresos / dias_mes if dias_mes > 0 else 0.0
        promedio_laborable = total_ingresos / dias_laborables if dias_laborables > 0 else 0.0
        
        # Comparación mes anterior (MoM)
        mom_data = self._calculate_mom_comparison(start_date, total_ingresos)
        
        # Comparación año anterior (YoY)
        yoy_data = self._calculate_yoy_comparison(start_date, total_ingresos)
        
        return {
            'dias_mes': dias_mes,
            'dias_laborables': dias_laborables,
            'semanas_completas': semanas_completas,
            'promedio_diario': round(promedio_diario, 2),
            'promedio_dia_laborable': round(promedio_laborable, 2),
            'comparacion_mom': mom_data,
            'comparacion_yoy': yoy_data,
            'mes_nombre': self._get_month_label(start_date)
        }
    
    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS PRIVADOS
    # ═══════════════════════════════════════════════════════════════
    
    def _calculate_mom_comparison(self, current_month: date, current_ingresos: float) -> Dict[str, Any]:
        """Calcula comparación con mes anterior (Month over Month)"""
        # Mes anterior
        if current_month.month == 1:
            prev_month = date(current_month.year - 1, 12, 1)
        else:
            prev_month = date(current_month.year, current_month.month - 1, 1)
        
        ultimo_dia_prev = monthrange(prev_month.year, prev_month.month)[1]
        prev_month_end = date(prev_month.year, prev_month.month, ultimo_dia_prev)
        
        # Query mes anterior
        ops_anterior = self.fetch_operations(prev_month, prev_month_end)
        
        ingresos_anterior = sum(
            float(op.monto_uyu) for op in ops_anterior 
            if op.tipo_operacion == TipoOperacion.INGRESO
        ) or 0.0
        
        # Calcular variación
        if ingresos_anterior > 0:
            variacion_porcentaje = ((current_ingresos - ingresos_anterior) / ingresos_anterior) * 100.0
            variacion_absoluta = current_ingresos - ingresos_anterior
        else:
            variacion_porcentaje = 0.0
            variacion_absoluta = current_ingresos
        
        return {
            'mes_anterior': prev_month.strftime('%Y-%m'),
            'ingresos_anterior': round(ingresos_anterior, 2),
            'variacion_absoluta': round(variacion_absoluta, 2),
            'variacion_porcentaje': round(variacion_porcentaje, 2),
            'tendencia': 'alcista' if variacion_porcentaje > 0 else 'bajista' if variacion_porcentaje < 0 else 'estable'
        }
    
    def _calculate_yoy_comparison(self, current_month: date, current_ingresos: float) -> Dict[str, Any]:
        """Calcula comparación con mismo mes año anterior (Year over Year)"""
        # Mismo mes año anterior
        prev_year_month = date(current_month.year - 1, current_month.month, 1)
        ultimo_dia = monthrange(prev_year_month.year, prev_year_month.month)[1]
        prev_year_month_end = date(prev_year_month.year, prev_year_month.month, ultimo_dia)
        
        # Query mismo mes año anterior
        ops_year_ago = self.fetch_operations(prev_year_month, prev_year_month_end)
        
        ingresos_year_ago = sum(
            float(op.monto_uyu) for op in ops_year_ago 
            if op.tipo_operacion == TipoOperacion.INGRESO
        ) or 0.0
        
        # Calcular variación
        if ingresos_year_ago > 0:
            variacion_porcentaje = ((current_ingresos - ingresos_year_ago) / ingresos_year_ago) * 100.0
            variacion_absoluta = current_ingresos - ingresos_year_ago
        else:
            variacion_porcentaje = 0.0
            variacion_absoluta = current_ingresos
        
        return {
            'mes_year_ago': prev_year_month.strftime('%Y-%m'),
            'ingresos_year_ago': round(ingresos_year_ago, 2),
            'variacion_absoluta': round(variacion_absoluta, 2),
            'variacion_porcentaje': round(variacion_porcentaje, 2),
            'crecimiento_anual': round(variacion_porcentaje, 2)
        }
    
    def _get_month_label(self, fecha: date) -> str:
        """Retorna label legible: 'Octubre 2025'"""
        meses_es = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        return f"{meses_es[fecha.month]} {fecha.year}"

