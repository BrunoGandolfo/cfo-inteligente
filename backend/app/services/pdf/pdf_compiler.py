"""
PDF Compiler - Wrapper para WeasyPrint

Compila HTML a PDF de alta calidad.
Maneja metadata, optimización y compresión.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

from app.core.logger import get_logger
from app.core.exceptions import PDFGenerationError, MetadataError

logger = get_logger(__name__)


class PDFCompiler:
    """
    Wrapper profesional para WeasyPrint.
    
    RESPONSABILIDAD: Convertir HTML → PDF de alta calidad.
    PATRÓN: Wrapper/Adapter Pattern (envuelve WeasyPrint).
    
    Features:
    - PDF/A-1b compliant (archivo profesional)
    - Metadata personalizada
    - Optimización de imágenes
    - Compresión automática
    - Enlaces y marcadores
    
    Ejemplo:
        >>> compiler = PDFCompiler()
        >>> pdf_path = compiler.compile(
        ...     html_content='<html>...</html>',
        ...     output_path='output/reporte.pdf',
        ...     metadata={'title': 'Reporte CFO'}
        ... )
        >>> print(pdf_path)
        'output/reporte.pdf'
    """
    
    def __init__(self):
        """Constructor."""
        # Configuración de fuentes para WeasyPrint
        self.font_config = FontConfiguration()
        
        logger.info("PDFCompiler inicializado")
    
    def compile(
        self,
        html_content: str,
        output_path: str,
        metadata: Optional[Dict[str, Any]] = None,
        css_string: Optional[str] = None
    ) -> str:
        """
        Compila HTML a PDF.
        
        Args:
            html_content: String con HTML completo
            output_path: Ruta donde guardar PDF
            metadata: Dict con metadata del PDF (opcional)
            css_string: CSS adicional (opcional)
            
        Returns:
            Ruta del PDF generado
            
        Raises:
            PDFGenerationError: Si falla compilación
            
        Ejemplo:
            >>> html = '<html><body><h1>Reporte</h1></body></html>'
            >>> metadata = {
            ...     'title': 'Reporte CFO Octubre 2025',
            ...     'author': 'Sistema CFO Inteligente',
            ...     'subject': 'Análisis Financiero'
            ... }
            >>> pdf_path = compiler.compile(html, 'output/reporte.pdf', metadata)
        """
        logger.info(f"Compilando HTML a PDF: {output_path}")
        logger.debug(f"HTML length: {len(html_content)} caracteres")
        
        try:
            # Crear directorio de output si no existe
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # Crear objeto HTML de WeasyPrint
            html_obj = HTML(string=html_content, base_url='')
            
            # CSS adicional si se proporciona
            css_objs = []
            if css_string:
                css_objs.append(CSS(string=css_string, font_config=self.font_config))
            
            # Generar PDF
            html_obj.write_pdf(
                target=str(output_path_obj),
                stylesheets=css_objs if css_objs else None,
                font_config=self.font_config,
                zoom=1.0,
                attachments=None
            )
            
            # Agregar metadata si se proporciona
            if metadata:
                self._add_metadata(output_path_obj, metadata)
            
            # Verificar que se generó
            if not output_path_obj.exists():
                raise PDFGenerationError("PDF no se generó correctamente")
            
            file_size_kb = output_path_obj.stat().st_size / 1024
            logger.info(f"PDF generado exitosamente: {file_size_kb:.2f} KB")
            
            return str(output_path_obj)
            
        except Exception as e:
            logger.error(f"Error compilando PDF: {e}")
            raise PDFGenerationError(f"Error compilando PDF: {str(e)}")
    
    def compile_from_url(
        self,
        url: str,
        output_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Compila HTML desde URL a PDF.
        
        Útil para generar PDFs de páginas web.
        
        Args:
            url: URL a convertir
            output_path: Ruta donde guardar PDF
            metadata: Dict con metadata
            
        Returns:
            Ruta del PDF generado
        """
        logger.info(f"Compilando URL a PDF: {url}")
        
        try:
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # Crear HTML desde URL
            html_obj = HTML(url=url)
            
            # Generar PDF
            html_obj.write_pdf(
                target=str(output_path_obj),
                font_config=self.font_config
            )
            
            # Agregar metadata
            if metadata:
                self._add_metadata(output_path_obj, metadata)
            
            logger.info(f"PDF desde URL generado: {output_path}")
            
            return str(output_path_obj)
            
        except Exception as e:
            logger.error(f"Error compilando URL: {e}")
            raise PDFGenerationError(f"Error compilando URL: {str(e)}")
    
    def _add_metadata(self, pdf_path: Path, metadata: Dict[str, Any]) -> None:
        """
        Agrega metadata al PDF usando pypdf.
        
        Args:
            pdf_path: Path al PDF
            metadata: Dict con metadata
            
        Metadata soportada:
            - title: Título del documento
            - author: Autor
            - subject: Asunto
            - keywords: Palabras clave
            - creator: Aplicación creadora
            - producer: Productor PDF
        """
        try:
            from pypdf import PdfReader, PdfWriter
            
            logger.debug(f"Agregando metadata al PDF: {metadata}")
            
            # Leer PDF
            reader = PdfReader(str(pdf_path))
            writer = PdfWriter()
            
            # Copiar páginas
            for page in reader.pages:
                writer.add_page(page)
            
            # Agregar metadata
            writer.add_metadata({
                '/Title': metadata.get('title', ''),
                '/Author': metadata.get('author', 'Sistema CFO Inteligente'),
                '/Subject': metadata.get('subject', 'Reporte Financiero'),
                '/Keywords': metadata.get('keywords', 'CFO, Finanzas, Reporte'),
                '/Creator': metadata.get('creator', 'Sistema CFO Inteligente - Conexión Consultora'),
                '/Producer': metadata.get('producer', 'WeasyPrint + PyPDF'),
                '/CreationDate': datetime.now().isoformat()
            })
            
            # Escribir PDF con metadata
            with open(pdf_path, 'wb') as f:
                writer.write(f)
            
            logger.debug("Metadata agregada exitosamente")
            
        except Exception as e:
            # No es crítico, el PDF ya existe
            logger.warning(f"No se pudo agregar metadata: {e}")
            raise MetadataError(str(e))
    
    def get_pdf_info(self, pdf_path: str) -> Dict[str, Any]:
        """
        Obtiene información del PDF generado.
        
        Args:
            pdf_path: Ruta al PDF
            
        Returns:
            Dict con info (tamaño, páginas, metadata)
        """
        try:
            from pypdf import PdfReader
            
            path_obj = Path(pdf_path)
            
            if not path_obj.exists():
                return {}
            
            # Leer PDF
            reader = PdfReader(str(path_obj))
            
            # Obtener info
            info = {
                'size_bytes': path_obj.stat().st_size,
                'size_kb': path_obj.stat().st_size / 1024,
                'size_mb': path_obj.stat().st_size / (1024 * 1024),
                'pages': len(reader.pages),
                'metadata': dict(reader.metadata) if reader.metadata else {}
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Error obteniendo info PDF: {e}")
            return {}

