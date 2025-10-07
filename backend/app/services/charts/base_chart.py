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
    
    # Paleta de colores (consistente con dashboard)
    COLORS = {
        'primary': '#3B82F6',      # Azul principal
        'success': '#10B981',      # Verde (ingresos)
        'danger': '#EF4444',       # Rojo (gastos)
        'warning': '#F59E0B',      # Ámbar (alertas)
        'secondary': '#8B5CF6',    # Violeta (secundario)
        'gray': '#6B7280',         # Gris (neutro)
    }
    
    # Paleta extendida para gráficos con muchas categorías
    EXTENDED_PALETTE = [
        '#10B981',  # Verde
        '#3B82F6',  # Azul
        '#EF4444',  # Rojo
        '#F59E0B',  # Ámbar
        '#8B5CF6',  # Violeta
        '#EC4899',  # Rosa
    ]
    
    # Tipografía
    FONT_FAMILY = 'Arial, sans-serif'
    FONT_SIZE_TITLE = 18
    FONT_SIZE_AXIS = 12
    FONT_SIZE_LEGEND = 11
    
    # Dimensiones (en píxeles)
    WIDTH_DEFAULT = 800
    HEIGHT_DEFAULT = 500
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
        
        # Grid sutil
        self.figure.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='#E5E7EB'  # Gray-200
        )
        
        self.figure.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='#E5E7EB'
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
            scale=2  # 2x para alta resolución
        )
        
        return str(path)
    
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

