"""
GaugeChart - Gráfico gauge/velocímetro para KPIs

Visualiza métrica actual vs target con gauge visual.
Ideal para mostrar performance de KPIs principales.

Autor: Sistema CFO Inteligente
Fecha: Noviembre 2025
"""

from typing import Dict, Any
import plotly.graph_objects as go

from .base_chart import BaseChart


class GaugeChart(BaseChart):
    """
    Gráfico gauge profesional para KPIs.
    
    Estructura de datos esperada:
    {
        'value': 72.5,           # Valor actual
        'target': 70.0,          # Target/objetivo (opcional)
        'title': 'Margen Neto',  # Título del KPI
        'suffix': '%',           # Sufijo (opcional)
        'range_max': 100         # Rango máximo (opcional)
    }
    
    Uso típico:
        data = {
            'value': 72.5,
            'target': 70.0,
            'title': 'Margen Neto',
            'suffix': '%'
        }
        config = {'title': 'Performance Margen'}
        chart = GaugeChart(data, config)
        chart.generate('output/gauge.png')
    """
    
    def validate_data(self) -> None:
        """Valida estructura de datos para gauge chart"""
        if 'value' not in self.data:
            raise ValueError("Datos deben contener 'value'")
        
        value = self.data['value']
        if not isinstance(value, (int, float)):
            raise ValueError(f"'value' debe ser numérico, es {type(value)}")
    
    def create_figure(self) -> go.Figure:
        """
        Crea figura de Plotly con gauge.
        
        Returns:
            go.Figure configurada con gauge
        """
        value = self.data['value']
        target = self.data.get('target', value * 1.2)
        suffix = self.data.get('suffix', '')
        range_max = self.data.get('range_max', target * 1.5)
        kpi_title = self.data.get('title', '')
        
        # Determinar color del gauge según performance vs target
        if value >= target:
            bar_color = self.COLORS['success']
        elif value >= target * 0.9:
            bar_color = self.COLORS['warning']
        else:
            bar_color = self.COLORS['danger']
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            
            # Delta vs target
            delta={
                'reference': target,
                'increasing': {'color': self.COLORS['success']},
                'decreasing': {'color': self.COLORS['danger']},
                'suffix': suffix
            },
            
            # Número principal
            number={
                'suffix': suffix,
                'font': {
                    'size': 48,
                    'family': self.FONT_FAMILY,
                    'color': '#1F2937'
                }
            },
            
            # Título del KPI
            title={
                'text': kpi_title,
                'font': {
                    'size': 16,
                    'family': self.FONT_FAMILY,
                    'color': '#6B7280'
                }
            },
            
            # Configuración del gauge
            gauge={
                'axis': {
                    'range': [0, range_max],
                    'tickwidth': 1,
                    'tickcolor': '#9CA3AF'
                },
                'bar': {'color': bar_color, 'thickness': 0.75},
                'bgcolor': 'white',
                'borderwidth': 2,
                'bordercolor': '#E5E7EB',
                'steps': [
                    {'range': [0, target * 0.7], 'color': '#FEE2E2'},        # Rojo claro
                    {'range': [target * 0.7, target], 'color': '#FEF3C7'},   # Ámbar claro
                    {'range': [target, range_max], 'color': '#D1FAE5'}       # Verde claro
                ],
                'threshold': {
                    'line': {'color': self.COLORS['primary'], 'width': 4},
                    'thickness': 0.75,
                    'value': target
                }
            }
        ))
        
        return fig

