"""
TreemapChart - Gráfico treemap para jerarquías

Visualiza datos jerárquicos con rectángulos anidados.
Ideal para distribución de ingresos por área y sub-categorías.

Autor: Sistema CFO Inteligente
Fecha: Noviembre 2025
"""

from typing import Dict, Any, List
import plotly.graph_objects as go

from .base_chart import BaseChart


class TreemapChart(BaseChart):
    """
    Gráfico treemap profesional para datos jerárquicos.
    
    Casos de uso:
    - Ingresos por Área > Sub-área
    - Gastos por Categoría > Sub-categoría
    - Cualquier estructura jerárquica con valores
    
    Estructura de datos esperada:
    {
        'labels': ['Total', 'Jurídica', 'Notarial', 'Contable', 
                   'Jur-Inmob', 'Jur-Comercial', 'Not-Escrituras'],
        'parents': ['', 'Total', 'Total', 'Total', 
                    'Jurídica', 'Jurídica', 'Notarial'],
        'values': [1000000, 650000, 250000, 100000, 
                   400000, 250000, 180000]
    }
    
    Notas:
    - labels: nombre de cada nodo
    - parents: padre de cada nodo ('' para root)
    - values: valor numérico de cada nodo
    - Colores automáticos según jerarquía
    
    Uso típico:
        data = {
            'labels': ['Total', 'Área 1', 'Área 2', 'Sub 1.1'],
            'parents': ['', 'Total', 'Total', 'Área 1'],
            'values': [1000, 600, 400, 350]
        }
        config = {'title': 'Ingresos por Área'}
        chart = TreemapChart(data, config)
        chart.generate('output/treemap.png')
    """
    
    def validate_data(self) -> None:
        """Valida estructura de datos para treemap"""
        required_keys = ['labels', 'parents', 'values']
        
        for key in required_keys:
            if key not in self.data:
                raise ValueError(f"Datos deben contener '{key}'")
        
        n = len(self.data['labels'])
        
        if len(self.data['parents']) != n:
            raise ValueError(f"'parents' debe tener {n} elementos")
        
        if len(self.data['values']) != n:
            raise ValueError(f"'values' debe tener {n} elementos")
        
        # Validar que valores sean positivos
        if any(v < 0 for v in self.data['values']):
            raise ValueError("Todos los valores deben ser positivos")
    
    def create_figure(self) -> go.Figure:
        """
        Crea figura de Plotly con treemap.
        
        Returns:
            go.Figure configurada con treemap
        """
        labels = self.data['labels']
        parents = self.data['parents']
        values = self.data['values']
        
        fig = go.Figure(go.Treemap(
            labels=labels,
            parents=parents,
            values=values,
            
            # Información mostrada
            textinfo="label+value+percent parent",
            textfont=dict(
                size=13,
                family=self.FONT_FAMILY,
                color='white'
            ),
            
            # Colores profesionales (gradiente azul corporativo)
            marker=dict(
                colorscale=[
                    [0.0, '#BBDEFB'],  # Azul muy claro
                    [0.5, '#5B9BD5'],  # Azul institucional
                    [1.0, '#2B3E6B']   # Navy oscuro
                ],
                line=dict(width=2, color='white'),
                cmid=sum(values) / len(values)  # Centro de escala en promedio
            ),
            
            # Hover mejorado
            hovertemplate='<b>%{label}</b><br>' +
                          'Valor: $%{value:,.0f}<br>' +
                          '%{percentParent} del total<extra></extra>',
            
            # Path bar (navegación)
            pathbar=dict(
                visible=False  # Ocultar para PDF (no es interactivo)
            )
        ))
        
        return fig

