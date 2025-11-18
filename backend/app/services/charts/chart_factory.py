"""
ChartFactory - Factory Pattern para crear gráficos

Crea instancias de gráficos según tipo solicitado.
Simplifica la creación y valida configuraciones.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import Dict, Any, Type
from pathlib import Path

from .base_chart import BaseChart
from .line_chart import LineChart
from .pie_chart import PieChart
from .bar_chart import BarChart
from .waterfall_chart import WaterfallChart
from .donut_chart import DonutChart
from .combo_chart import ComboChart
from .heatmap_chart import HeatmapChart
from .gauge_chart import GaugeChart
from .treemap_chart import TreemapChart
from .funnel_chart import FunnelChart


class ChartFactory:
    """
    Factory para crear gráficos según tipo.
    
    Uso:
        data = {'labels': [...], 'series': [...]}
        config = {'title': 'Mi Gráfico', 'width': 1000}
        
        chart = ChartFactory.create('line', data, config)
        chart.generate('output/grafico.png')
    """
    
    # Registro de gráficos disponibles
    _charts: Dict[str, Type[BaseChart]] = {
        'line': LineChart,
        'pie': PieChart,
        'bar': BarChart,
        'waterfall': WaterfallChart,
        'donut': DonutChart,
        'combo': ComboChart,
        'heatmap': HeatmapChart,
        'gauge': GaugeChart,
        'treemap': TreemapChart,
        'funnel': FunnelChart
    }
    
    @classmethod
    def create(
        cls,
        chart_type: str,
        data: Dict[str, Any],
        config: Dict[str, Any] = None
    ) -> BaseChart:
        """
        Crea instancia del gráfico apropiado.
        
        Args:
            chart_type: Tipo de gráfico ('line', 'pie', 'bar', 'waterfall', 
                       'donut', 'combo', 'heatmap')
            data: Datos para el gráfico (estructura específica por tipo)
            config: Configuración opcional (title, width, height, etc)
            
        Returns:
            Instancia del gráfico correspondiente
            
        Raises:
            ValueError: Si chart_type no está registrado
        """
        chart_class = cls._charts.get(chart_type)
        
        if not chart_class:
            available = ', '.join(cls._charts.keys())
            raise ValueError(
                f"Tipo de gráfico '{chart_type}' no existe. "
                f"Disponibles: {available}"
            )
        
        return chart_class(data, config)
    
    @classmethod
    def create_and_save(
        cls,
        chart_type: str,
        data: Dict[str, Any],
        output_path: str,
        config: Dict[str, Any] = None
    ) -> str:
        """
        Método de conveniencia: crea gráfico y lo guarda en un solo paso.
        
        Returns:
            Ruta del archivo guardado
        """
        chart = cls.create(chart_type, data, config)
        return chart.generate(output_path)
    
    @classmethod
    def register_chart(cls, chart_type: str, chart_class: Type[BaseChart]):
        """Registra nuevo tipo de gráfico (extensibilidad)"""
        if not issubclass(chart_class, BaseChart):
            raise TypeError(f"{chart_class} debe heredar de BaseChart")
        
        cls._charts[chart_type] = chart_class
    
    @classmethod
    def get_available_types(cls) -> list[str]:
        """Retorna lista de tipos de gráfico disponibles"""
        return list(cls._charts.keys())

