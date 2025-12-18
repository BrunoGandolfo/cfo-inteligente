"""
HeatmapChart - Gráfico de mapa de calor (matriz)

Visualiza datos matriciales con colores intensos según valor.
Ideal para mostrar rentabilidad por Área × Mes.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import List
import plotly.graph_objects as go

from .base_chart import BaseChart


class HeatmapChart(BaseChart):
    """
    Gráfico de mapa de calor profesional.
    
    Casos de uso:
    - Rentabilidad por Área × Mes
    - Volumen de operaciones por Localidad × Trimestre
    - Cualquier matriz 2D de valores numéricos
    
    Estructura de datos esperada:
    {
        'x_labels': ['Ene', 'Feb', 'Mar', 'Abr'],  # Columnas
        'y_labels': ['Notarial', 'Jurídica', 'Contable'],  # Filas
        'values': [
            [75.5, 78.2, 80.1, 82.3],  # Notarial por mes
            [70.1, 72.4, 71.8, 73.5],  # Jurídica por mes
            [68.3, 69.1, 70.2, 71.0]   # Contable por mes
        ],
        'value_format': 'percentage'  # 'percentage' | 'currency' | 'number'
    }
    
    Notas:
    - values es matriz de shape (len(y_labels), len(x_labels))
    - Colores automáticos: rojo (bajo) → amarillo → verde (alto)
    - Muestra valores sobre celdas
    
    Uso típico:
        data = {
            'x_labels': ['Ene', 'Feb', 'Mar'],
            'y_labels': ['Notarial', 'Jurídica'],
            'values': [[75.5, 78.2, 80.1], [70.1, 72.4, 71.8]],
            'value_format': 'percentage'
        }
        config = {'title': 'Rentabilidad por Área y Mes'}
        chart = HeatmapChart(data, config)
        chart.generate('output/heatmap.png')
    """
    
    def validate_data(self) -> None:
        """
        Valida estructura de datos para heatmap.
        
        Raises:
            ValueError: Si faltan keys o dimensiones incorrectas
        """
        required_keys = ['x_labels', 'y_labels', 'values']
        
        for key in required_keys:
            if key not in self.data:
                raise ValueError(f"Datos deben contener '{key}'")
        
        n_rows = len(self.data['y_labels'])
        n_cols = len(self.data['x_labels'])
        
        # Validar que values sea matriz
        if not isinstance(self.data['values'], list):
            raise ValueError("'values' debe ser una lista de listas (matriz)")
        
        if len(self.data['values']) != n_rows:
            raise ValueError(
                f"'values' debe tener {n_rows} filas "
                f"(una por cada y_label), tiene {len(self.data['values'])}"
            )
        
        # Validar cada fila
        for i, row in enumerate(self.data['values']):
            if not isinstance(row, list):
                raise ValueError(f"values[{i}] debe ser una lista")
            if len(row) != n_cols:
                raise ValueError(
                    f"values[{i}] debe tener {n_cols} columnas "
                    f"(una por cada x_label), tiene {len(row)}"
                )
    
    def create_figure(self) -> go.Figure:
        """
        Crea figura de Plotly con heatmap.
        
        Returns:
            go.Figure configurada con heatmap
        """
        x_labels = self.data['x_labels']
        y_labels = self.data['y_labels']
        values = self.data['values']
        value_format = self.data.get('value_format', 'number')
        
        # Formatear textos de celdas
        text_values = self._format_cell_texts(values, value_format)
        
        # Crear heatmap
        fig = go.Figure(data=go.Heatmap(
            x=x_labels,
            y=y_labels,
            z=values,
            text=text_values,
            texttemplate='%{text}',
            textfont={'size': 12, 'color': 'white'},
            
            # Escala de colores
            colorscale=self._get_colorscale(),
            
            # Mostrar barra de escala
            colorbar=dict(
                title=self._get_colorbar_title(value_format),
                titleside='right',
                tickmode='linear',
                tick0=0,
                dtick=20 if value_format == 'percentage' else None
            ),
            
            # Hover
            hovertemplate='<b>%{y}</b> - <b>%{x}</b><br>' +
                          'Valor: %{z}<extra></extra>'
        ))
        
        # Configurar ejes
        fig.update_xaxes(
            side='bottom',
            title_text=""
        )
        
        fig.update_yaxes(
            title_text="",
            autorange='reversed'  # Para que primera fila esté arriba
        )
        
        return fig
    
    # ═══════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════
    
    def _format_cell_texts(
        self,
        values: List[List[float]],
        value_format: str
    ) -> List[List[str]]:
        """
        Formatea valores de celdas para mostrar.
        
        Args:
            values: Matriz de valores
            value_format: Tipo de formato ('percentage', 'currency', 'number')
            
        Returns:
            Matriz de strings formateados
        """
        formatted = []
        
        for row in values:
            formatted_row = []
            for val in row:
                if val is None:
                    formatted_row.append('N/A')
                elif value_format == 'percentage':
                    formatted_row.append(f'{val:.1f}%')
                elif value_format == 'currency':
                    if abs(val) >= 1_000_000:
                        formatted_row.append(f'${val/1_000_000:.1f}M')
                    elif abs(val) >= 1_000:
                        formatted_row.append(f'${val/1_000:.0f}K')
                    else:
                        formatted_row.append(f'${val:.0f}')
                else:  # number
                    formatted_row.append(f'{val:,.0f}')
            
            formatted.append(formatted_row)
        
        return formatted
    
    def _get_colorscale(self) -> List:
        """
        Retorna escala de colores para heatmap.
        
        Escala de verde (alto) a rojo (bajo) pasando por amarillo.
        
        Returns:
            Lista de [posición, color] para Plotly
        """
        # Escala custom: rojo → amarillo → verde
        return [
            [0.0, '#EF4444'],   # Rojo (bajo)
            [0.25, '#F59E0B'],  # Ámbar
            [0.5, '#FBBF24'],   # Amarillo (medio)
            [0.75, '#84CC16'],  # Lima
            [1.0, '#10B981']    # Verde (alto)
        ]
    
    def _get_colorbar_title(self, value_format: str) -> str:
        """
        Retorna título para barra de colores según formato.
        
        Args:
            value_format: Tipo de formato
            
        Returns:
            String para título
        """
        if value_format == 'percentage':
            return 'Rentabilidad %'
        elif value_format == 'currency':
            return 'Monto (UYU)'
        else:
            return 'Valor'

