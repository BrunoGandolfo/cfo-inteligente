"""
ComboChart - Gráfico combinado de líneas + barras

Combina barras y líneas en el mismo gráfico.
Ideal para comparar valores reales vs proyecciones.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .base_chart import BaseChart


class ComboChart(BaseChart):
    """
    Gráfico combinado profesional de líneas + barras.
    
    Casos de uso:
    - Valores reales (barras) vs proyección (línea)
    - Ingresos (barras) vs margen % (línea)
    - Múltiples series con diferentes visualizaciones
    
    Estructura de datos esperada:
    {
        'labels': ['Ene', 'Feb', 'Mar', 'Abr', 'May'],
        'bar_series': [
            {
                'name': 'Ingresos Reales',
                'values': [100000, 120000, 115000, 130000, 125000],
                'color': '#10B981'
            }
        ],
        'line_series': [
            {
                'name': 'Proyección',
                'values': [105000, 118000, 120000, 128000, 135000],
                'color': '#3B82F6',
                'dash': 'dash'  # Opcional: 'solid', 'dash', 'dot'
            }
        ]
    }
    
    Configuraciones opcionales:
    - secondary_y: True para eje Y secundario (útil para escalas diferentes)
    - barmode: 'group' | 'stack' para barras agrupadas o apiladas
    
    Uso típico:
        data = {
            'labels': ['Oct', 'Nov', 'Dic', 'Ene (proj)', 'Feb (proj)'],
            'bar_series': [{'name': 'Real', 'values': [100, 120, 115, 0, 0]}],
            'line_series': [{'name': 'Proyección', 'values': [None, None, 115, 130, 140]}]
        }
        config = {'title': 'Ingresos: Real vs Proyección'}
        chart = ComboChart(data, config)
        chart.generate('output/combo.png')
    """
    
    def validate_data(self) -> None:
        """
        Valida estructura de datos para combo chart.
        
        Raises:
            ValueError: Si faltan keys o datos inválidos
        """
        if 'labels' not in self.data:
            raise ValueError("Datos deben contener 'labels'")
        
        if 'bar_series' not in self.data and 'line_series' not in self.data:
            raise ValueError("Debe haber al menos 'bar_series' o 'line_series'")
        
        n_labels = len(self.data['labels'])
        
        # Validar bar_series
        if 'bar_series' in self.data:
            for i, serie in enumerate(self.data['bar_series']):
                if 'name' not in serie:
                    raise ValueError(f"bar_series[{i}] debe tener 'name'")
                if 'values' not in serie:
                    raise ValueError(f"bar_series[{i}] debe tener 'values'")
                if len(serie['values']) != n_labels:
                    raise ValueError(
                        f"bar_series[{i}] '{serie['name']}' tiene "
                        f"{len(serie['values'])} valores pero hay {n_labels} labels"
                    )
        
        # Validar line_series
        if 'line_series' in self.data:
            for i, serie in enumerate(self.data['line_series']):
                if 'name' not in serie:
                    raise ValueError(f"line_series[{i}] debe tener 'name'")
                if 'values' not in serie:
                    raise ValueError(f"line_series[{i}] debe tener 'values'")
                if len(serie['values']) != n_labels:
                    raise ValueError(
                        f"line_series[{i}] '{serie['name']}' tiene "
                        f"{len(serie['values'])} valores pero hay {n_labels} labels"
                    )
    
    def create_figure(self) -> go.Figure:
        """
        Crea figura de Plotly con gráfico combinado.
        
        Returns:
            go.Figure configurada con barras + líneas
        """
        labels = self.data['labels']
        bar_series = self.data.get('bar_series', [])
        line_series = self.data.get('line_series', [])
        
        # Determinar si usar eje Y secundario
        use_secondary_y = self.config.get('secondary_y', False)
        
        # Crear figura (con o sin eje secundario)
        if use_secondary_y:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
        else:
            fig = go.Figure()
        
        # ═══════════════════════════════════════════════════════════════
        # AGREGAR BARRAS
        # ═══════════════════════════════════════════════════════════════
        
        for i, serie in enumerate(bar_series):
            color = serie.get('color', self.EXTENDED_PALETTE[i % len(self.EXTENDED_PALETTE)])
            
            trace = go.Bar(
                name=serie['name'],
                x=labels,
                y=serie['values'],
                marker=dict(
                    color=color,
                    line=dict(color='white', width=1)
                ),
                text=[self.format_currency(v, short=True) if v else '' 
                      for v in serie['values']],
                textposition='outside',
                textfont=dict(size=11),
                hovertemplate='<b>%{x}</b><br>' +
                              f"{serie['name']}: " +
                              '%{y:,.0f}<extra></extra>'
            )
            
            if use_secondary_y:
                # Barras en eje primario
                fig.add_trace(trace, secondary_y=False)
            else:
                fig.add_trace(trace)
        
        # ═══════════════════════════════════════════════════════════════
        # AGREGAR LÍNEAS
        # ═══════════════════════════════════════════════════════════════
        
        for i, serie in enumerate(line_series):
            color = serie.get('color', self.EXTENDED_PALETTE[(len(bar_series) + i) % len(self.EXTENDED_PALETTE)])
            dash = serie.get('dash', 'solid')  # 'solid', 'dash', 'dot'
            
            # Determinar si va en eje secundario
            on_secondary = serie.get('secondary_y', use_secondary_y)
            
            trace = go.Scatter(
                name=serie['name'],
                x=labels,
                y=serie['values'],
                mode='lines+markers',
                line=dict(
                    color=color,
                    width=3,
                    dash=dash
                ),
                marker=dict(
                    size=8,
                    color=color,
                    line=dict(width=2, color='white')
                ),
                hovertemplate='<b>%{x}</b><br>' +
                              f"{serie['name']}: " +
                              '%{y:,.0f}<extra></extra>'
            )
            
            if use_secondary_y:
                fig.add_trace(trace, secondary_y=on_secondary)
            else:
                fig.add_trace(trace)
        
        # ═══════════════════════════════════════════════════════════════
        # CONFIGURACIÓN DE LAYOUT
        # ═══════════════════════════════════════════════════════════════
        
        # Modo de barras (si hay múltiples series de barras)
        if len(bar_series) > 1:
            barmode = self.config.get('barmode', 'group')
            fig.update_layout(barmode=barmode)
        
        # Configurar ejes Y
        if use_secondary_y:
            fig.update_yaxes(
                title_text="Monto (UYU)",
                secondary_y=False
            )
            fig.update_yaxes(
                title_text=self.config.get('secondary_y_title', ""),
                secondary_y=True
            )
        
        return fig

