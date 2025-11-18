"""
DonutChart - Gráfico de dona para distribuciones

Similar a PieChart pero con hueco central (más moderno).
Ideal para mostrar distribución por socio con número central.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import Dict, Any, Optional
import plotly.graph_objects as go

from .base_chart import BaseChart


class DonutChart(BaseChart):
    """
    Gráfico de dona profesional para distribuciones.
    
    Diferencia con PieChart:
    - Tiene hueco central (hole=0.5)
    - Puede mostrar valor central (ej: "3 socios")
    - Más moderno visualmente
    
    Estructura de datos esperada:
    {
        'labels': ['Juan Pérez', 'María López', 'Carlos García'],
        'values': [350000, 350000, 300000],
        'colors': ['#10B981', '#3B82F6', '#8B5CF6'],  # Opcional
        'center_text': '3 Socios',  # Opcional, texto en centro
        'center_value': '$1.0M'  # Opcional, valor grande en centro
    }
    
    Uso típico:
        data = {
            'labels': ['Juan Pérez', 'María López', 'Carlos García'],
            'values': [33.33, 33.33, 33.34],
            'center_text': '3 Socios',
            'center_value': '100%'
        }
        config = {'title': 'Distribución por Socio'}
        chart = DonutChart(data, config)
        chart.generate('output/donut.png')
    """
    
    def validate_data(self) -> None:
        """
        Valida estructura de datos para donut chart.
        
        Raises:
            ValueError: Si faltan keys o datos inválidos
        """
        if 'labels' not in self.data:
            raise ValueError("Datos deben contener 'labels'")
        
        if 'values' not in self.data:
            raise ValueError("Datos deben contener 'values'")
        
        if len(self.data['labels']) != len(self.data['values']):
            raise ValueError(
                f"labels ({len(self.data['labels'])}) y values "
                f"({len(self.data['values'])}) deben tener la misma longitud"
            )
        
        if len(self.data['labels']) == 0:
            raise ValueError("Debe haber al menos 1 categoría")
        
        # Validar que valores sean no negativos
        if any(v < 0 for v in self.data['values']):
            raise ValueError("Todos los valores deben ser no negativos")
    
    def create_figure(self) -> go.Figure:
        """
        Crea figura de Plotly con gráfico de dona profesional.
        
        Returns:
            go.Figure configurada con donut
        """
        labels = self.data['labels']
        values = self.data['values']
        colors = self.data.get('colors', self.EXTENDED_PALETTE[:len(labels)])
        
        # Tamaño del hueco (0.4 = 40% = balance profesional)
        hole_size = self.config.get('hole_size', 0.4)
        
        # Explode del segmento principal (destacar líder)
        max_idx = values.index(max(values)) if values else 0
        pull = [0.1 if i == max_idx else 0 for i in range(len(values))]
        
        # Calcular porcentajes para labels
        total = sum(values)
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker=dict(
                colors=colors,
                line=dict(color='white', width=2)
            ),
            
            # Configuración de texto
            textposition='auto',
            textinfo='label+percent',
            textfont=dict(
                size=13,
                color='white',
                family=self.FONT_FAMILY
            ),
            
            # Hover mejorado
            hovertemplate='<b>%{label}</b><br>' +
                          'Monto: $%{value:,.0f}<br>' +
                          'Porcentaje: %{percent}<extra></extra>',
            
            # Hueco central (donut profesional)
            hole=hole_size,
            
            # Explode del segmento líder
            pull=pull
        )])
        
        # ═══════════════════════════════════════════════════════════════
        # TEXTO CENTRAL (opcional)
        # ═══════════════════════════════════════════════════════════════
        
        # Si hay texto central, agregarlo como anotación
        center_text = self.data.get('center_text')
        center_value = self.data.get('center_value')
        
        if center_text or center_value:
            annotations = []
            
            # Valor grande (arriba)
            if center_value:
                annotations.append(dict(
                    text=center_value,
                    x=0.5,
                    y=0.5,
                    font=dict(
                        size=32,
                        color='#1F2937',
                        family=self.FONT_FAMILY
                    ),
                    showarrow=False,
                    xref='paper',
                    yref='paper'
                ))
            
            # Texto descriptivo (abajo)
            if center_text:
                y_pos = 0.42 if center_value else 0.5  # Ajustar si hay valor arriba
                annotations.append(dict(
                    text=center_text,
                    x=0.5,
                    y=y_pos,
                    font=dict(
                        size=16,
                        color='#6B7280',
                        family=self.FONT_FAMILY
                    ),
                    showarrow=False,
                    xref='paper',
                    yref='paper'
                ))
            
            fig.update_layout(annotations=annotations)
        
        return fig

