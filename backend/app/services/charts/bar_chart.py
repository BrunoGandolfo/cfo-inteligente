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
        """Crea figura de Plotly con barras profesionales (vertical u horizontal)"""
        fig = go.Figure()
        
        categories = self.data['categories']
        series_list = self.data['series']
        
        # Orientación (vertical u horizontal)
        orientation = self.config.get('orientation', 'v')  # 'v' o 'h'
        
        # Ordenar categorías por valor (mayor a menor) si configurado
        if self.config.get('sort_by_value', False) and len(series_list) > 0:
            # Ordenar basado en primera serie
            first_values = series_list[0]['values']
            sorted_pairs = sorted(zip(categories, *[s['values'] for s in series_list]), 
                                key=lambda x: x[1], reverse=True)
            categories = [p[0] for p in sorted_pairs]
            for idx, serie in enumerate(series_list):
                serie['values'] = [p[idx+1] for p in sorted_pairs]
        
        # Agregar cada serie como grupo de barras
        for i, serie in enumerate(series_list):
            color = serie.get('color', self.EXTENDED_PALETTE[i % len(self.EXTENDED_PALETTE)])
            
            # Configurar según orientación
            if orientation == 'h':
                x_data = serie['values']
                y_data = categories
                text_position = 'inside'
                text_anchor = 'start'
            else:
                x_data = categories
                y_data = serie['values']
                text_position = 'outside'
                text_anchor = 'middle'
            
            fig.add_trace(go.Bar(
                name=serie['name'],
                x=x_data,
                y=y_data,
                orientation=orientation,
                marker=dict(
                    color=color,
                    line=dict(color='white', width=1)
                ),
                text=[self.format_currency(v, short=True) for v in serie['values']],
                textposition=text_position,
                textfont=dict(size=11, family=self.FONT_FAMILY),
                insidetextanchor=text_anchor if orientation == 'h' else None,
                hovertemplate='<b>%{' + ('y' if orientation == 'h' else 'x') + '}</b><br>' +
                              f"{serie['name']}: " +
                              '%{' + ('x' if orientation == 'h' else 'y') + ':,.0f}<extra></extra>'
            ))
        
        # Modo de barras (agrupadas vs apiladas)
        barmode = self.config.get('barmode', 'group')
        fig.update_layout(barmode=barmode)
        
        # Invertir eje Y en horizontal para que mayor esté arriba
        if orientation == 'h':
            fig.update_yaxes(autorange='reversed')
        
        # Guardar figura para poder agregar anotaciones
        self.figure = fig
        
        # Agregar anotaciones automáticas si está configurado (solo en vertical)
        if orientation == 'v' and self.config.get('annotate', True) and len(series_list) > 0:
            self.add_value_annotations(
                trace_index=0,
                highlight_max=True,
                highlight_avg=True
            )
        
        return fig

