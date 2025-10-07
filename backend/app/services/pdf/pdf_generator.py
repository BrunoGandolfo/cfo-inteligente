"""
PDFGenerator - Genera PDFs profesionales con WeasyPrint

Convierte templates HTML+CSS a PDF de alta calidad.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from pathlib import Path
from typing import Dict, Any
from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader
import base64

from app.core.logger import get_logger

logger = get_logger(__name__)


class PDFGenerator:
    """Genera PDFs desde templates HTML usando WeasyPrint"""
    
    def __init__(self, templates_dir: str = None):
        """
        Args:
            templates_dir: Directorio de templates (default: backend/templates/reports)
        """
        if templates_dir is None:
            templates_dir = str(Path(__file__).parent.parent.parent.parent / "templates" / "reports")
        
        self.templates_dir = Path(templates_dir)
        self.env = Environment(loader=FileSystemLoader(str(self.templates_dir)))
        
        # Agregar funciones helper a Jinja2
        self.env.globals['format_currency'] = self._format_currency
        self.env.globals['format_percentage'] = self._format_percentage
    
    def generate(
        self, 
        template_name: str,
        context: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        Genera PDF desde template.
        
        Args:
            template_name: Nombre del template (ej: 'monthly_report.html')
            context: Dict con datos para el template
            output_path: Ruta donde guardar PDF
            
        Returns:
            Ruta del archivo generado
        """
        logger.info(f"Generando PDF: {template_name} → {output_path}")
        
        # Renderizar HTML
        template = self.env.get_template(template_name)
        html_content = template.render(**context)
        
        # Convertir a PDF
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        HTML(string=html_content, base_url=str(self.templates_dir)).write_pdf(
            str(output_file)
        )
        
        logger.info(f"PDF generado: {output_file}")
        return str(output_file)
    
    @staticmethod
    def _format_currency(value: float) -> str:
        """Helper para templates"""
        return f"${value:,.0f}"
    
    @staticmethod
    def _format_percentage(value: float) -> str:
        """Helper para templates"""
        return f"{value:.1f}%"

