"""
LineChart - Gráfico de líneas para evolución temporal

Ideal para mostrar tendencias de ingresos, gastos, rentabilidad a lo largo del tiempo.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import Dict, Any, List
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
        """Crea figura de Plotly con líneas de serie temporal"""
        fig = go.Figure()
        
        labels = self.data['labels']
        series_list = self.data['series']
        
        # Agregar cada serie como línea
        for i, serie in enumerate(series_list):
            color = serie.get('color', self.EXTENDED_PALETTE[i % len(self.EXTENDED_PALETTE)])
            
            fig.add_trace(go.Scatter(
                x=labels,
                y=serie['values'],
                mode='lines+markers',
                name=serie['name'],
                line=dict(
                    color=color,
                    width=3
                ),
                marker=dict(
                    size=8,
                    color=color,
                    line=dict(
                        width=2,
                        color='white'
                    )
                ),
                hovertemplate='<b>%{x}</b><br>' +
                              f"{serie['name']}: " + 
                              '%{y:,.0f}<extra></extra>'
            ))
        
        return fig

