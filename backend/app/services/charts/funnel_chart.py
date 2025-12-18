"""
FunnelChart - Gráfico embudo para conversión/pipeline

Visualiza etapas secuenciales con reducción (embudo de ventas, pipeline).
Ideal para mostrar proceso con pérdidas en cada etapa.

Autor: Sistema CFO Inteligente
Fecha: Noviembre 2025
"""

import plotly.graph_objects as go

from .base_chart import BaseChart


class FunnelChart(BaseChart):
    """
    Gráfico embudo profesional para etapas/conversión.
    
    Casos de uso:
    - Pipeline de oportunidades (leads → clientes)
    - Proceso de facturación (propuesta → cobro)
    - Cualquier flujo con conversión entre etapas
    
    Estructura de datos esperada:
    {
        'stages': ['Oportunidades', 'Propuestas', 'Contratos', 'Facturado', 'Cobrado'],
        'values': [100, 75, 50, 45, 40]
    }
    
    Notas:
    - stages: nombres de las etapas (de más amplia a más específica)
    - values: valores en cada etapa (deben ser decrecientes o iguales)
    - Muestra % de conversión entre etapas
    
    Uso típico:
        data = {
            'stages': ['Leads', 'Propuestas', 'Contratos', 'Pagos'],
            'values': [150, 100, 60, 55]
        }
        config = {'title': 'Pipeline de Facturación'}
        chart = FunnelChart(data, config)
        chart.generate('output/funnel.png')
    """
    
    def validate_data(self) -> None:
        """Valida estructura de datos para funnel chart"""
        if 'stages' not in self.data:
            raise ValueError("Datos deben contener 'stages'")
        
        if 'values' not in self.data:
            raise ValueError("Datos deben contener 'values'")
        
        if len(self.data['stages']) != len(self.data['values']):
            raise ValueError(
                f"stages ({len(self.data['stages'])}) y values "
                f"({len(self.data['values'])}) deben tener la misma longitud"
            )
        
        if len(self.data['stages']) < 2:
            raise ValueError("Debe haber al menos 2 etapas")
        
        # Validar que valores sean positivos
        if any(v < 0 for v in self.data['values']):
            raise ValueError("Todos los valores deben ser positivos")
    
    def create_figure(self) -> go.Figure:
        """
        Crea figura de Plotly con funnel.
        
        Returns:
            go.Figure configurada con funnel
        """
        stages = self.data['stages']
        values = self.data['values']
        
        # Calcular % de conversión entre etapas
        conversion_rates = []
        for i in range(len(values)):
            if i == 0:
                conversion_rates.append(100.0)
            else:
                rate = (values[i] / values[0] * 100) if values[0] > 0 else 0
                conversion_rates.append(rate)
        
        # Crear textos personalizados
        text_labels = []
        for i, (stage, val, rate) in enumerate(zip(stages, values, conversion_rates)):
            if i == 0:
                text_labels.append(f"{self.format_currency(val)}<br>100%")
            else:
                text_labels.append(f"{self.format_currency(val)}<br>{rate:.1f}%")
        
        fig = go.Figure(go.Funnel(
            y=stages,
            x=values,
            
            # Textos personalizados
            text=text_labels,
            textposition="inside",
            textfont=dict(
                size=14,
                color='white',
                family=self.FONT_FAMILY
            ),
            
            # Colores profesionales (gradiente azul)
            marker=dict(
                color=self.EXTENDED_PALETTE[:len(stages)],
                line=dict(width=2, color='white')
            ),
            
            # Info adicional
            textinfo="text",
            
            # Hover
            hovertemplate='<b>%{y}</b><br>' +
                          'Valor: $%{x:,.0f}<br>' +
                          '%{percentInitial} del inicial<extra></extra>',
            
            # Conector entre etapas
            connector=dict(
                line=dict(
                    color='rgba(209, 213, 219, 0.5)',
                    width=1,
                    dash='dot'
                )
            )
        ))
        
        # Configuración adicional
        fig.update_layout(
            funnelmode="stack"  # Más compacto visualmente
        )
        
        return fig

