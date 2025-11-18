"""
BaseChart - Clase abstracta para gráficos corporativos

Define configuración común y estilos de marca para todos los gráficos.
Usa Plotly para generación profesional con exportación PNG de alta calidad.

Principios SOLID:
- Single Responsibility: Solo genera gráficos, no maneja datos
- Open/Closed: Extensible vía herencia
- Liskov: Todos los charts son intercambiables
- Interface Segregation: Interface mínima

Requiere:
    pip install plotly kaleido

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from app.core.logger import get_logger

logger = get_logger(__name__)


class BaseChart(ABC):
    """
    Clase base abstracta para gráficos corporativos.
    
    Configuración de marca Conexión Consultora:
    - Colores corporativos
    - Tipografía profesional
    - Tamaños estandarizados
    - Exportación alta calidad (300 DPI)
    """
    
    # ═══════════════════════════════════════════════════════════════
    # CONFIGURACIÓN CORPORATIVA
    # ═══════════════════════════════════════════════════════════════
    
    # Paleta corporativa Conexión Consultora (del logo institucional)
    COLORS = {
        'primary': '#5B9BD5',        # Azul claro institucional
        'primary_dark': '#4472C4',   # Azul medio institucional
        'primary_darker': '#2B3E6B', # Navy oscuro institucional
        'success': '#70AD47',        # Verde institucional
        'success_dark': '#5A8C3A',   # Verde oscuro
        'danger': '#E74C3C',         # Rojo institucional
        'warning': '#F39C12',        # Ámbar cálido
        'secondary': '#8B5CF6',      # Violeta (mantener)
        'gray': '#7F8C8D',           # Gris neutro
    }
    
    # Paleta extendida corporativa para gráficos con muchas categorías
    EXTENDED_PALETTE = [
        '#5B9BD5',  # Azul institucional
        '#70AD47',  # Verde institucional
        '#4472C4',  # Azul medio
        '#E74C3C',  # Rojo institucional
        '#F39C12',  # Ámbar
        '#8B5CF6',  # Violeta
        '#42A5F5',  # Azul claro
        '#66BB6A',  # Verde claro
    ]
    
    # Tipografía moderna profesional
    FONT_FAMILY = "'Inter', 'Segoe UI', 'Roboto', -apple-system, sans-serif"
    FONT_SIZE_TITLE = 20
    FONT_SIZE_AXIS = 13
    FONT_SIZE_LEGEND = 12
    
    # Dimensiones (en píxeles) - Optimizado para 300 DPI en PDF A4
    WIDTH_DEFAULT = 1400  # 300 DPI × 8.27" / 3 (con scale=3 → 4200px)
    HEIGHT_DEFAULT = 925   # 300 DPI × 5.51" / 3 (con scale=3 → 2775px)
    DPI = 300  # Alta calidad para impresión
    
    # Márgenes
    MARGIN = dict(l=60, r=30, t=80, b=60)
    
    def __init__(self, data: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
        """
        Args:
            data: Datos para el gráfico (estructura depende del tipo)
            config: Configuración opcional que sobreescribe defaults
        """
        self.data = data
        self.config = config or {}
        self.figure = None
        self.logger = logger
        
        # Aplicar configuración personalizada
        self.width = self.config.get('width', self.WIDTH_DEFAULT)
        self.height = self.config.get('height', self.HEIGHT_DEFAULT)
        self.title = self.config.get('title', '')
    
    # ═══════════════════════════════════════════════════════════════
    # TEMPLATE METHOD
    # ═══════════════════════════════════════════════════════════════
    
    def generate(self, output_path: str) -> str:
        """
        Template Method: Genera y guarda el gráfico.
        
        Flujo:
        1. Validar datos
        2. Crear figura (abstracto)
        3. Aplicar estilos corporativos
        4. Exportar a PNG
        
        Args:
            output_path: Ruta donde guardar PNG
            
        Returns:
            Ruta del archivo generado
            
        Raises:
            ValueError: Si datos son inválidos
        """
        self.logger.info(f"Generando {self.__class__.__name__}: {self.title}")
        
        # PASO 1: Validar datos
        self.validate_data()
        
        # PASO 2: Crear figura (implementado por subclases)
        self.figure = self.create_figure()
        
        # PASO 3: Aplicar layout corporativo
        self._apply_corporate_layout()
        
        # PASO 4: Exportar
        output_file = self.save(output_path)
        
        self.logger.info(f"Gráfico guardado: {output_file}")
        return output_file
    
    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS ABSTRACTOS
    # ═══════════════════════════════════════════════════════════════
    
    @abstractmethod
    def validate_data(self) -> None:
        """
        Valida que self.data tiene la estructura correcta.
        Debe lanzar ValueError si datos son inválidos.
        """
        pass
    
    @abstractmethod
    def create_figure(self) -> go.Figure:
        """
        Crea la figura de Plotly con los datos.
        Retorna go.Figure configurada.
        """
        pass
    
    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS CONCRETOS
    # ═══════════════════════════════════════════════════════════════
    
    def _apply_corporate_layout(self) -> None:
        """Aplica layout y estilos corporativos a la figura"""
        if not self.figure:
            return
        
        # Forzar template limpio (elimina TODOS los defaults de Plotly)
        self.figure.update_layout(template='plotly_white')
        
        self.figure.update_layout(
            title={
                'text': self.title,
                'font': {
                    'family': self.FONT_FAMILY,
                    'size': self.FONT_SIZE_TITLE,
                    'color': '#1F2937'  # Gray-800
                },
                'x': 0.5,  # Centrado
                'xanchor': 'center'
            },
            font={
                'family': self.FONT_FAMILY,
                'size': self.FONT_SIZE_AXIS,
                'color': '#4B5563'  # Gray-600
            },
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=self.MARGIN,
            width=self.width,
            height=self.height,
            showlegend=self.config.get('showlegend', True),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(size=self.FONT_SIZE_LEGEND)
            )
        )
        
        # Grid casi invisible (estilo Big 4)
        self.figure.update_xaxes(
            showgrid=True,
            gridwidth=0.3,
            gridcolor='rgba(229, 231, 235, 0.2)',  # Casi invisible
            griddash='solid',
            zeroline=True,
            zerolinewidth=1,
            zerolinecolor='rgba(107, 114, 128, 0.2)',
            showline=True,
            linewidth=1,
            linecolor='#E5E7EB',
            mirror=False
        )
        
        self.figure.update_yaxes(
            showgrid=True,
            gridwidth=0.3,
            gridcolor='rgba(229, 231, 235, 0.2)',
            griddash='solid',
            zeroline=True,
            zerolinewidth=1,
            zerolinecolor='rgba(107, 114, 128, 0.2)',
            showline=True,
            linewidth=1,
            linecolor='#E5E7EB',
            mirror=False
        )
    
    def save(self, output_path: str) -> str:
        """
        Exporta gráfico a PNG de alta calidad.
        
        Args:
            output_path: Ruta del archivo (con o sin extensión)
            
        Returns:
            Ruta completa del archivo guardado
        """
        if not self.figure:
            raise RuntimeError("Figura no creada. Llamar create_figure() primero.")
        
        # Asegurar extensión .png
        path = Path(output_path)
        if path.suffix != '.png':
            path = path.with_suffix('.png')
        
        # Crear directorio si no existe
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Exportar con kaleido (backend estático)
        self.figure.write_image(
            str(path),
            format='png',
            width=self.width,
            height=self.height,
            scale=3  # 3x para calidad offset printing (450 DPI efectivo)
        )
        
        return str(path)
    
    def add_value_annotations(
        self,
        trace_index: int = 0,
        highlight_max: bool = True,
        highlight_min: bool = False,
        highlight_avg: bool = False
    ) -> None:
        """
        Agrega anotaciones automáticas de valores clave.
        
        Args:
            trace_index: Índice del trace a anotar
            highlight_max: Anotar valor máximo
            highlight_min: Anotar valor mínimo
            highlight_avg: Agregar línea de promedio
        """
        if not self.figure or not self.figure.data:
            return
        
        trace = self.figure.data[trace_index]
        values = list(trace.y)
        labels = list(trace.x) if hasattr(trace, 'x') else list(range(len(values)))
        
        if not values:
            return
        
        # Máximo
        if highlight_max:
            max_val = max(values)
            max_idx = values.index(max_val)
            
            self.figure.add_annotation(
                x=labels[max_idx],
                y=max_val,
                text=f"Máximo<br>{self.format_currency(max_val)}",
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor=self.COLORS['success'],
                ax=0,
                ay=-40,
                font=dict(size=10, color=self.COLORS['success'], weight='bold'),
                bgcolor='white',
                bordercolor=self.COLORS['success'],
                borderwidth=2,
                borderpad=4
            )
        
        # Mínimo
        if highlight_min:
            min_val = min(values)
            min_idx = values.index(min_val)
            
            if max_idx != min_idx:  # Solo si no es el mismo punto
                self.figure.add_annotation(
                    x=labels[min_idx],
                    y=min_val,
                    text=f"Mínimo<br>{self.format_currency(min_val)}",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=2,
                    arrowcolor=self.COLORS['danger'],
                    ax=0,
                    ay=40,
                    font=dict(size=10, color=self.COLORS['danger'], weight='bold'),
                    bgcolor='white',
                    bordercolor=self.COLORS['danger'],
                    borderwidth=2,
                    borderpad=4
                )
        
        # Línea de promedio
        if highlight_avg:
            avg_val = sum(values) / len(values)
            self.figure.add_hline(
                y=avg_val,
                line_dash="dash",
                line_width=1,
                line_color=self.COLORS['gray'],
                annotation_text=f"Promedio: {self.format_currency(avg_val)}",
                annotation_position="right",
                annotation_font_size=9,
                annotation_font_color=self.COLORS['gray']
            )
    
    # ═══════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════
    
    def format_currency(self, value: float, short: bool = False) -> str:
        """
        Formatea valor monetario.
        
        Args:
            value: Valor numérico
            short: Si True, usa K/M (ej: $1.2M), si False usa completo
            
        Returns:
            String formateado (ej: '$1,234,567' o '$1.2M')
        """
        if short:
            if value >= 1_000_000:
                return f"${value/1_000_000:.1f}M"
            elif value >= 1_000:
                return f"${value/1_000:.0f}K"
            else:
                return f"${value:.0f}"
        else:
            return f"${value:,.0f}"

