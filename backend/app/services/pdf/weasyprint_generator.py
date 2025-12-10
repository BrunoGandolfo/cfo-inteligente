"""
Generador de PDFs con WeasyPrint - Sistema CFO Inteligente
Basado en: ESPECIFICACION_TECNICA_REPORTE_BIG4.md (Secciones 10-13)

Stack: WeasyPrint + Jinja2 + FastAPI
"""

from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import tempfile
import logging

logger = logging.getLogger(__name__)


# ============================================================
# FILTROS JINJA2 (Sección 11.2)
# ============================================================

def format_currency(value):
    """Formatea número como moneda: $27,769,510"""
    if value is None:
        return "Sin Datos"
    try:
        return f"${float(value):,.0f}"
    except (ValueError, TypeError):
        return "Sin Datos"


def format_currency_short(value):
    """Formatea como $27.8M"""
    if value is None:
        return "Sin Datos"
    try:
        num = float(value)
        if abs(num) >= 1_000_000:
            return f"${num/1_000_000:.1f}M"
        elif abs(num) >= 1_000:
            return f"${num/1_000:.1f}K"
        return f"${num:.0f}"
    except (ValueError, TypeError):
        return "Sin Datos"


def format_percent(value):
    """Formatea como 88.9%"""
    if value is None:
        return "Sin Datos"
    try:
        return f"{float(value):.1f}%"
    except (ValueError, TypeError):
        return "Sin Datos"


# ============================================================
# GENERADOR PDF (Sección 10.2)
# ============================================================

class PDFGenerator:
    """Generador de PDFs con WeasyPrint."""
    
    def __init__(self, templates_dir: str = None):
        if templates_dir is None:
            base = Path(__file__).parent.parent
            templates_dir = base / "templates" / "reports_big4"
        
        self.templates_dir = Path(templates_dir)
        self.env = Environment(loader=FileSystemLoader(str(self.templates_dir)))
        
        # Registrar filtros
        self.env.filters['format_currency'] = format_currency
        self.env.filters['format_currency_short'] = format_currency_short
        self.env.filters['format_percent'] = format_percent
        self.env.filters['abs'] = abs
        self.env.filters['round'] = round
    
    def generar_pdf(self, html_path: str, pdf_path: str):
        """Genera PDF desde archivo HTML."""
        HTML(html_path).write_pdf(pdf_path)
    
    def generar_pdf_desde_template(self, template_name: str, datos: dict, pdf_path: str = None) -> bytes:
        """Genera PDF desde template Jinja2 con datos dinámicos."""
        template = self.env.get_template(template_name)
        html_content = template.render(**datos)
        
        if pdf_path:
            HTML(string=html_content).write_pdf(pdf_path)
            with open(pdf_path, 'rb') as f:
                return f.read()
        else:
            return HTML(string=html_content).write_pdf()


# ============================================================
# FUNCIÓN SIMPLE
# ============================================================

def generar_pdf(html_path: str, pdf_path: str):
    """Genera PDF desde HTML usando WeasyPrint."""
    HTML(html_path).write_pdf(pdf_path)


# ============================================================
# USO DIRECTO
# ============================================================

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) >= 3:
        html_input = sys.argv[1]
        pdf_output = sys.argv[2]
        generar_pdf(html_input, pdf_output)
        print(f"PDF generado: {pdf_output}")
    else:
        print("Uso: python weasyprint_generator.py <archivo.html> <salida.pdf>")
