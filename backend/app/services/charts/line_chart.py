"""
LineChart - Gráfico de líneas para evolución temporal

Ideal para mostrar tendencias de ingresos, gastos, rentabilidad a lo largo del tiempo.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

import plotly.graph_objects as go

from .base_chart import BaseChart


class LineChart(BaseChart):
    """
    Gráfico de líneas profesional para series temporales.
    
    Estructura de datos esperada:
    {
        'labels': ['Ene', 'Feb', 'Mar', ...],  # Etiquetas eje X
        'series': [
            {
                'name': 'Ingresos',
                'values': [100000, 120000, 115000, ...],
                'color': '#10B981'  # Opcional
            },
            {
                'name': 'Gastos',
                'values': [60000, 75000, 70000, ...],
                'color': '#EF4444'  # Opcional
            }
        ]
    }
    """
    
    def validate_data(self) -> None:
        """Valida estructura de datos para line chart"""
        if 'labels' not in self.data:
            raise ValueError("Datos deben contener 'labels' (eje X)")
        
        if 'series' not in self.data:
            raise ValueError("Datos deben contener 'series' (líneas a graficar)")
        
        if not isinstance(self.data['series'], list):
            raise ValueError("'series' debe ser una lista")
        
        if len(self.data['series']) == 0:
            raise ValueError("'series' no puede estar vacía")
        
        # Validar cada serie
        for i, serie in enumerate(self.data['series']):
            if 'name' not in serie:
                raise ValueError(f"Serie {i} debe tener 'name'")
            if 'values' not in serie:
                raise ValueError(f"Serie {i} debe tener 'values'")
            if len(serie['values']) != len(self.data['labels']):
                raise ValueError(
                    f"Serie '{serie['name']}' tiene {len(serie['values'])} valores "
                    f"pero hay {len(self.data['labels'])} labels"
                )
    
    def create_figure(self) -> go.Figure:
        """Crea figura de Plotly con líneas de serie temporal profesionales"""
        fig = go.Figure()
        
        labels = self.data['labels']
        series_list = self.data['series']
        
        # Área sombreada DESACTIVADA por defecto (estilo reporte impreso)
        # Solo activar explícitamente con config['show_area'] = True
        if self.config.get('show_area', False) and len(series_list) > 0:
            serie_principal = series_list[0]
            color_principal = serie_principal.get('color', self.EXTENDED_PALETTE[0])
            
            # Convertir hex a rgba
            hex_color = color_principal.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            fig.add_trace(go.Scatter(
                x=labels,
                y=serie_principal['values'],
                fill='tozeroy',
                fillcolor=f'rgba({r}, {g}, {b}, 0.1)',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        # Agregar cada serie como línea limpia (estilo editorial)
        for i, serie in enumerate(series_list):
            color = serie.get('color', self.EXTENDED_PALETTE[i % len(self.EXTENDED_PALETTE)])
            
            fig.add_trace(go.Scatter(
                x=labels,
                y=serie['values'],
                mode='lines+markers',
                name=serie['name'],
                line=dict(
                    color=color,
                    width=2.5  # Línea más fina, estilo editorial
                ),
                marker=dict(
                    size=6,  # Markers más pequeños
                    color=color,
                    line=dict(
                        width=1,
                        color='white'
                    )
                ),
                hovertemplate='<b>%{x}</b><br>' +
                              f"{serie['name']}: " + 
                              '%{y:,.0f}<extra></extra>'
            ))
        
        # Guardar figura para poder agregar anotaciones
        self.figure = fig
        
        # Agregar anotaciones automáticas si está configurado
        if self.config.get('annotate', True) and len(series_list) > 0:
            self.add_value_annotations(
                trace_index=1 if self.config.get('show_area', True) else 0,
                highlight_max=True,
                highlight_avg=True
            )
        
        return fig

