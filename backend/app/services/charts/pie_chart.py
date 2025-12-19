"""
PieChart - Gráfico de torta para distribuciones

Ideal para mostrar composición por área, localidad, o categoría.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

import plotly.graph_objects as go

from .base_chart import BaseChart


class PieChart(BaseChart):
    """
    Gráfico de torta profesional para distribuciones.
    
    Estructura de datos esperada:
    {
        'labels': ['Jurídica', 'Notarial', 'Contable', ...],
        'values': [450000, 320000, 180000, ...],
        'colors': ['#10B981', '#3B82F6', ...]  # Opcional
    }
    """
    
    def validate_data(self) -> None:
        """Valida estructura de datos para pie chart"""
        if 'labels' not in self.data:
            raise ValueError("Datos deben contener 'labels'")
        
        if 'values' not in self.data:
            raise ValueError("Datos deben contener 'values'")
        
        if len(self.data['labels']) != len(self.data['values']):
            raise ValueError(
                f"labels ({len(self.data['labels'])}) y values ({len(self.data['values'])}) "
                "deben tener la misma longitud"
            )
        
        if len(self.data['labels']) == 0:
            raise ValueError("Debe haber al menos 1 categoría")
        
        # Validar que valores sean positivos
        if any(v < 0 for v in self.data['values']):
            raise ValueError("Todos los valores deben ser positivos")
    
    def create_figure(self) -> go.Figure:
        """Crea figura de Plotly con gráfico de torta"""
        labels = self.data['labels']
        values = self.data['values']
        colors = self.data.get('colors', self.EXTENDED_PALETTE[:len(labels)])
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker=dict(
                colors=colors,
                line=dict(color='white', width=2)
            ),
            textposition='inside',
            textinfo='label+percent',
            textfont=dict(
                size=12,
                color='white',
                family=self.FONT_FAMILY
            ),
            hovertemplate='<b>%{label}</b><br>' +
                          'Monto: $%{value:,.0f}<br>' +
                          'Porcentaje: %{percent}<extra></extra>',
            hole=0.3  # Donut chart (más moderno)
        )])
        
        return fig

