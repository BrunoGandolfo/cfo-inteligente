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
from typing import Dict, Any, Optional
import plotly.graph_objects as go

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
    # TAREA 3: Paleta muted Big 4
    COLORS = {
        'primary': '#1E3A5F',        # Azul oscuro corporativo
        'primary_dark': '#0F1F33',   # Azul muy oscuro
        'primary_darker': '#0A1422', # Navy profundo
        'success': '#047857',        # Verde apagado
        'success_dark': '#065F46',   # Verde oscuro
        'danger': '#B91C1C',         # Rojo apagado
        'warning': '#B45309',        # Ámbar apagado
        'secondary': '#4F46E5',      # Indigo
        'gray': '#6B7280',           # Gris medio
    }
    
    # Paleta extendida corporativa para gráficos con muchas categorías
    EXTENDED_PALETTE = [
        '#1E3A5F',  # Azul corporativo
        '#047857',  # Verde apagado
        '#B91C1C',  # Rojo apagado
        '#B45309',  # Ámbar apagado
        '#4F46E5',  # Indigo
        '#6B7280',  # Gris medio
        '#374151',  # Gris oscuro
        '#1F2937',  # Gris muy oscuro
    ]
    
    # Tipografía moderna profesional - TAREA 7: Tamaños mínimos para legibilidad PDF
    FONT_FAMILY = "'Inter', 'Helvetica Neue', Arial, sans-serif"
    FONT_SIZE_TITLE = 22
    FONT_SIZE_AXIS = 14
    FONT_SIZE_LEGEND = 14
    
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
    
    @abstractmethod
    def create_figure(self) -> go.Figure:
        """
        Crea la figura de Plotly con los datos.
        Retorna go.Figure configurada.
        """
    
    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS CONCRETOS
    # ═══════════════════════════════════════════════════════════════
    
    def _apply_corporate_layout(self) -> None:
        """
        Aplica tema corporativo estilo reporte impreso ejecutivo.
        
        Diseño Big 4: limpio, profesional, sin estética de dashboard web.
        """
        if not self.figure:
            return
        
        # Forzar template limpio
        self.figure.update_layout(template='plotly_white')
        
        # Layout corporativo estilo reporte impreso
        self.figure.update_layout(
            title=dict(
                text=self.title or "",
                font=dict(
                    family=self.FONT_FAMILY,
                    size=16,
                    color='#1E3A5F'
                ),
                x=0.01,  # Alineado a la izquierda (estilo editorial)
                xanchor='left'
            ),
            font=dict(
                family=self.FONT_FAMILY,
                size=12,
                color='#374151'
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            colorway=self.EXTENDED_PALETTE,
            margin=dict(t=60, r=40, b=60, l=60),
            width=self.width,
            height=self.height,
            showlegend=self.config.get('showlegend', True),
            legend=dict(
                orientation="h",
                x=0.5,
                xanchor="center",
                y=-0.15,
                yanchor="top",
                bgcolor="rgba(255,255,255,0)",
                font=dict(size=10)
            ),
            hoverlabel=dict(
                bgcolor="white",
                font_size=11
            )
        )
        
        # Eje X: línea base, SIN grid (estilo reporte impreso)
        self.figure.update_xaxes(
            showgrid=False,
            showline=True,
            linecolor='#E5E7EB',
            linewidth=1,
            tickfont=dict(size=11),
            title_font=dict(size=12)
        )
        
        # Eje Y: grid sutil, SIN línea lateral
        self.figure.update_yaxes(
            showgrid=True,
            gridcolor='#F3F4F6',
            gridwidth=0.5,
            showline=False,
            tickfont=dict(size=11),
            title_font=dict(size=12),
            tickformat=","
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

