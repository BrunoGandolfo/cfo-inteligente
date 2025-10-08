"""
WaterfallChart - Gráfico cascada para flujo de rentabilidad

Muestra el flujo desde ingresos hasta resultado neto paso a paso.
Ideal para visualizar cómo se llega al resultado final.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import Dict, Any
import plotly.graph_objects as go

from .base_chart import BaseChart


class WaterfallChart(BaseChart):
    """
    Gráfico cascada profesional para flujo de rentabilidad.
    
    Estructura de datos esperada:
    {
        'labels': ['Ingresos', 'Gastos', 'Resultado Operativo', 
                   'Retiros', 'Distribuciones', 'Resultado Neto'],
        'values': [100000, -40000, 60000, -15000, -10000, 35000],
        'measures': ['absolute', 'relative', 'total', 'relative', 'relative', 'total']
    }
    
    Tipos de measure:
    - 'absolute': Barra desde 0 (solo primer valor)
    - 'relative': Barra incremental/decremental desde valor anterior
    - 'total': Barra de total acumulado (resultados finales)
    
    Uso típico:
        data = {
            'labels': ['Ingresos', 'Gastos', 'Retiros', 'Distribuciones', 'Resultado'],
            'values': [1000000, -400000, -150000, -100000, 350000],
            'measures': ['absolute', 'relative', 'relative', 'relative', 'total']
        }
        config = {'title': 'Flujo de Rentabilidad Octubre 2025'}
        chart = WaterfallChart(data, config)
        chart.generate('output/waterfall.png')
    """
    
    def validate_data(self) -> None:
        """
        Valida estructura de datos para waterfall chart.
        
        Raises:
            ValueError: Si faltan keys o longitudes no coinciden
        """
        required_keys = ['labels', 'values', 'measures']
        
        for key in required_keys:
            if key not in self.data:
                raise ValueError(f"Datos deben contener '{key}'")
        
        # Validar longitudes
        n_labels = len(self.data['labels'])
        n_values = len(self.data['values'])
        n_measures = len(self.data['measures'])
        
        if not (n_labels == n_values == n_measures):
            raise ValueError(
                f"Longitudes deben coincidir: labels={n_labels}, "
                f"values={n_values}, measures={n_measures}"
            )
        
        # Validar measures válidas
        valid_measures = {'absolute', 'relative', 'total'}
        for measure in self.data['measures']:
            if measure not in valid_measures:
                raise ValueError(
                    f"Measure inválido '{measure}'. "
                    f"Válidos: {', '.join(valid_measures)}"
                )
    
    def create_figure(self) -> go.Figure:
        """
        Crea figura de Plotly con gráfico waterfall.
        
        Returns:
            go.Figure configurada con waterfall
        """
        labels = self.data['labels']
        values = self.data['values']
        measures = self.data['measures']
        
        # Crear figura waterfall
        fig = go.Figure(go.Waterfall(
            name="Flujo",
            orientation="v",
            x=labels,
            y=values,
            measure=measures,
            
            # Colores por tipo
            increasing={
                'marker': {
                    'color': self.COLORS['success'],  # Verde para ingresos
                    'line': {'color': 'white', 'width': 2}
                }
            },
            decreasing={
                'marker': {
                    'color': self.COLORS['danger'],  # Rojo para gastos
                    'line': {'color': 'white', 'width': 2}
                }
            },
            totals={
                'marker': {
                    'color': self.COLORS['primary'],  # Azul para totales
                    'line': {'color': 'white', 'width': 2}
                }
            },
            
            # Conectores
            connector={
                'line': {
                    'color': self.COLORS['gray'],
                    'width': 2,
                    'dash': 'dot'
                }
            },
            
            # Textos sobre barras
            text=[self._format_value_text(v) for v in values],
            textposition="outside",
            textfont={'size': 12, 'color': '#1F2937'},
            
            # Hover info
            hovertemplate='<b>%{x}</b><br>' +
                          'Monto: $%{y:,.0f}<extra></extra>'
        ))
        
        # Configuración de ejes
        fig.update_yaxes(
            title_text="Monto (UYU)",
            title_font={'size': 14},
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='#E5E7EB'
        )
        
        fig.update_xaxes(
            title_text="",
            tickangle=-45
        )
        
        return fig
    
    # ═══════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════
    
    def _format_value_text(self, value: float) -> str:
        """
        Formatea valor para mostrar sobre barra.
        
        Args:
            value: Valor numérico
            
        Returns:
            String formateado (ej: "+$1.2M", "-$450K", "$2.5M")
        """
        # Signo para valores relativos
        sign = '+' if value > 0 else ''
        
        # Formatear con K/M
        if abs(value) >= 1_000_000:
            formatted = f"{value/1_000_000:.1f}M"
        elif abs(value) >= 1_000:
            formatted = f"{value/1_000:.0f}K"
        else:
            formatted = f"{value:.0f}"
        
        return f"{sign}${formatted}"

