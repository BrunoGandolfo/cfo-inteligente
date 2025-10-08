"""
Template Renderer - Wrapper para Jinja2

Renderiza templates HTML con contexto.
Registra filters custom para formateo.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import Dict, Any
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.utils.formatters import format_currency, format_percentage, format_date_es
from app.core.logger import get_logger

logger = get_logger(__name__)


class TemplateRenderer:
    """
    Wrapper profesional para Jinja2.
    
    RESPONSABILIDAD: Renderizar HTML desde templates.
    PATRÓN: Wrapper/Adapter Pattern (envuelve Jinja2).
    
    Features:
    - Auto-escape HTML
    - Filters custom (format_currency, format_percentage, etc)
    - Cache de templates
    - Logging de renders
    
    Ejemplo:
        >>> renderer = TemplateRenderer('backend/app/templates')
        >>> html = renderer.render('reports/ejecutivo_master.html', context)
        >>> print(len(html))
        125000
    """
    
    def __init__(self, templates_dir: str):
        """
        Constructor.
        
        Args:
            templates_dir: Ruta al directorio de templates
            
        Raises:
            FileNotFoundError: Si templates_dir no existe
        """
        templates_path = Path(templates_dir)
        
        if not templates_path.exists():
            raise FileNotFoundError(f"Templates directory no encontrado: {templates_dir}")
        
        # Crear Environment Jinja2
        self.env = Environment(
            loader=FileSystemLoader(str(templates_path)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Registrar filters custom
        self._register_filters()
        
        logger.info(f"TemplateRenderer inicializado: {templates_dir}")
    
    def _register_filters(self) -> None:
        """
        Registra filters custom de Jinja2.
        
        Filters disponibles en templates:
        - {{ value | format_currency }}
        - {{ value | format_currency(short=True) }}
        - {{ value | format_percentage }}
        - {{ fecha | format_date_es('completo') }}
        """
        # Filter: format_currency
        def _format_currency_filter(value, short=False, include_currency=True):
            """Filter para formatear monedas"""
            try:
                return format_currency(value, short=short, include_currency=include_currency)
            except (TypeError, ValueError):
                return str(value)
        
        # Filter: format_percentage
        def _format_percentage_filter(value, decimals=2, include_symbol=True):
            """Filter para formatear porcentajes"""
            try:
                return format_percentage(value, decimals=decimals, include_symbol=include_symbol)
            except (TypeError, ValueError):
                return str(value)
        
        # Filter: format_date_es
        def _format_date_filter(value, formato='completo'):
            """Filter para formatear fechas en español"""
            try:
                return format_date_es(value, formato=formato)
            except (TypeError, ValueError, AttributeError):
                return str(value)
        
        # Registrar filters
        self.env.filters['format_currency'] = _format_currency_filter
        self.env.filters['format_percentage'] = _format_percentage_filter
        self.env.filters['format_date_es'] = _format_date_filter
        
        logger.debug("Filters custom registrados: format_currency, format_percentage, format_date_es")
    
    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Renderiza template con contexto.
        
        Args:
            template_name: Nombre del template (relativo a templates_dir)
                          Ejemplo: 'reports/ejecutivo_master.html'
            context: Dict con variables para el template
            
        Returns:
            String con HTML renderizado
            
        Raises:
            jinja2.TemplateNotFound: Si template no existe
            jinja2.TemplateError: Si hay error en sintaxis template
            
        Ejemplo:
            >>> context = {
            ...     'ingresos_uyu': 100000,
            ...     'margen_operativo': 33.5,
            ...     'period_label': 'Octubre 2025'
            ... }
            >>> html = renderer.render('reports/ejecutivo_master.html', context)
        """
        logger.info(f"Renderizando template: {template_name}")
        logger.debug(f"Context keys: {list(context.keys())}")
        
        try:
            # Obtener template
            template = self.env.get_template(template_name)
            
            # Renderizar
            html = template.render(**context)
            
            logger.info(f"Template renderizado: {len(html)} caracteres")
            
            return html
            
        except Exception as e:
            logger.error(f"Error renderizando template {template_name}: {e}")
            raise
    
    def render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        """
        Renderiza string template (sin archivo).
        
        Útil para templates dinámicos o testing.
        
        Args:
            template_string: String con sintaxis Jinja2
            context: Dict con variables
            
        Returns:
            String con HTML renderizado
        """
        logger.debug("Renderizando template desde string")
        
        try:
            template = self.env.from_string(template_string)
            html = template.render(**context)
            
            logger.debug(f"Template string renderizado: {len(html)} caracteres")
            
            return html
            
        except Exception as e:
            logger.error(f"Error renderizando template string: {e}")
            raise
    
    def get_available_templates(self, pattern: str = '*.html') -> list:
        """
        Lista templates disponibles.
        
        Args:
            pattern: Patrón glob para filtrar (default: '*.html')
            
        Returns:
            Lista de nombres de templates
        """
        templates_path = Path(self.env.loader.searchpath[0])
        templates = list(templates_path.rglob(pattern))
        
        # Convertir a paths relativos
        relative_templates = [
            str(t.relative_to(templates_path))
            for t in templates
        ]
        
        return sorted(relative_templates)

