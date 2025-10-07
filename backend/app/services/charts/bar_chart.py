"""
BarChart - Gráfico de barras para comparaciones

Ideal para comparar localidades, áreas, períodos.
Soporta barras agrupadas (múltiples series).

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import Dict, Any
import plotly.graph_objects as go

from .base_chart import BaseChart


class BarChart(BaseChart):
    """
    Gráfico de barras profesional para comparaciones.
    
    Estructura de datos esperada:
    {
        'categories': ['Montevideo', 'Mercedes'],  # Eje X
        'series': [
            {
                'name': 'Ingresos',
                'values': [650000, 450000],
                'color': '#10B981'  # Opcional
            },
            {
                'name': 'Gastos',
                'values': [400000, 250000],
                'color': '#EF4444'  # Opcional
            }
        ]
    }
    """
    
    def validate_data(self) -> None:
        """Valida estructura de datos para bar chart"""
        if 'categories' not in self.data:
            raise ValueError("Datos deben contener 'categories' (eje X)")
        
        if 'series' not in self.data:
            raise ValueError("Datos deben contener 'series' (barras)")
        
        if not isinstance(self.data['series'], list):
            raise ValueError("'series' debe ser una lista")
        
        if len(self.data['series']) == 0:
            raise ValueError("'series' no puede estar vacía")
        
        # Validar cada serie
        num_categories = len(self.data['categories'])
        
        for i, serie in enumerate(self.data['series']):
            if 'name' not in serie:
                raise ValueError(f"Serie {i} debe tener 'name'")
            if 'values' not in serie:
                raise ValueError(f"Serie {i} debe tener 'values'")
            if len(serie['values']) != num_categories:
                raise ValueError(
                    f"Serie '{serie['name']}' tiene {len(serie['values'])} valores "
                    f"pero hay {num_categories} categorías"
                )
    
    def create_figure(self) -> go.Figure:
        """Crea figura de Plotly con barras agrupadas"""
        fig = go.Figure()
        
        categories = self.data['categories']
        series_list = self.data['series']
        
        # Agregar cada serie como grupo de barras
        for i, serie in enumerate(series_list):
            color = serie.get('color', self.EXTENDED_PALETTE[i % len(self.EXTENDED_PALETTE)])
            
            fig.add_trace(go.Bar(
                name=serie['name'],
                x=categories,
                y=serie['values'],
                marker=dict(
                    color=color,
                    line=dict(color='white', width=1)
                ),
                text=[self.format_currency(v, short=True) for v in serie['values']],
                textposition='outside',
                textfont=dict(size=11),
                hovertemplate='<b>%{x}</b><br>' +
                              f"{serie['name']}: " +
                              '%{y:,.0f}<extra></extra>'
            ))
        
        # Modo de barras (agrupadas vs apiladas)
        barmode = self.config.get('barmode', 'group')  # 'group', 'stack', 'relative'
        fig.update_layout(barmode=barmode)
        
        return fig

