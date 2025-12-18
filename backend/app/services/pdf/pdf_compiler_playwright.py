"""
PDF Compiler Playwright - Wrapper para Playwright Browser

Compila HTML a PDF usando Playwright (Chrome headless).
Alternativa a WeasyPrint con mejor soporte de CSS moderno.

Autor: Sistema CFO Inteligente
Fecha: Noviembre 2025
"""

from typing import Optional, Dict, Any
from pathlib import Path
import tempfile

from playwright.async_api import async_playwright

from app.core.logger import get_logger
from app.core.exceptions import PDFGenerationError

logger = get_logger(__name__)


class PlaywrightPDFCompiler:
    """
    Wrapper profesional para Playwright PDF generation.
    
    RESPONSABILIDAD: Convertir HTML → PDF usando Chrome headless.
    PATRÓN: Wrapper/Adapter Pattern (envuelve Playwright).
    
    Ventajas vs WeasyPrint:
    - Soporta CSS moderno (grid, flexbox)
    - Renderizado exacto igual que Chrome browser
    - Mejor manejo de web fonts
    - JavaScript execution (si necesario)
    
    Desventajas:
    - Más lento (~5-10s vs 2-3s)
    - Requiere Chromium instalado (~500MB)
    - Mayor consumo de recursos
    
    Ejemplo:
        >>> compiler = PlaywrightPDFCompiler()
        >>> pdf_path = await compiler.compile_async(
        ...     html_content='<html>...</html>',
        ...     output_path='output/reporte.pdf'
        ... )
        >>> print(pdf_path)
        'output/reporte.pdf'
    """
    
    def __init__(self):
        """Constructor."""
        logger.info("PlaywrightPDFCompiler inicializado")
    
    async def compile_async(
        self,
        html_content: str,
        output_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Compila HTML a PDF usando Playwright (async).
        
        Args:
            html_content: String con HTML completo
            output_path: Ruta donde guardar PDF
            metadata: Dict con metadata del PDF (opcional)
            
        Returns:
            Ruta del PDF generado
            
        Raises:
            PDFGenerationError: Si falla compilación
        """
        logger.info(f"Compilando PDF con Playwright: {output_path}")
        
        try:
            # Crear archivo temporal con HTML
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.html',
                delete=False,
                encoding='utf-8'
            ) as temp_html:
                temp_html.write(html_content)
                temp_html_path = temp_html.name
            
            # Iniciar Playwright
            async with async_playwright() as p:
                # Lanzar browser (chromium)
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu'
                    ]
                )
                
                # Crear página
                page = await browser.new_page()
                
                # Cargar HTML
                await page.goto(f'file://{temp_html_path}', wait_until='networkidle')
                
                # Configuración profesional de PDF
                pdf_options = {
                    'path': output_path,
                    'format': 'A4',
                    'print_background': True,  # Incluir colores de fondo
                    'margin': {
                        'top': '1.5cm',
                        'right': '1cm',
                        'bottom': '1.5cm',
                        'left': '1cm'
                    },
                    'prefer_css_page_size': False,
                    'display_header_footer': True,
                    'header_template': self._build_header_template(metadata),
                    'footer_template': self._build_footer_template(),
                    'scale': 1.0  # Sin escala (usa tamaño real)
                }
                
                # Generar PDF
                await page.pdf(**pdf_options)
                
                # Cerrar browser
                await browser.close()
            
            # Eliminar archivo temporal
            Path(temp_html_path).unlink()
            
            # Obtener tamaño del PDF
            pdf_size_kb = Path(output_path).stat().st_size / 1024
            
            logger.info(f"✓ PDF generado con Playwright: {pdf_size_kb:.1f} KB")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error compilando PDF con Playwright: {e}")
            raise PDFGenerationError(f"Playwright compilation failed: {str(e)}")
    
    def compile(
        self,
        html_content: str,
        output_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Wrapper síncrono que ejecuta Playwright en thread separado.
        
        Evita conflicto con event loop de FastAPI usando ThreadPoolExecutor.
        Drop-in replacement compatible con PDFCompiler.
        
        Args:
            html_content: String con HTML completo
            output_path: Ruta donde guardar PDF
            metadata: Dict con metadata del PDF (opcional)
            
        Returns:
            Ruta del PDF generado
        """
        from concurrent.futures import ThreadPoolExecutor
        
        def _run_in_thread():
            """Ejecuta Playwright en thread sin event loop."""
            from playwright.sync_api import sync_playwright
            
            try:
                # Crear archivo HTML temporal
                temp_html = Path(output_path).parent / f"temp_{Path(output_path).stem}.html"
                temp_html.write_text(html_content, encoding='utf-8')
                
                logger.info(f"Compilando PDF con Playwright (thread): {output_path}")
                
                with sync_playwright() as p:
                    browser = p.chromium.launch(
                        headless=True,
                        args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
                    )
                    page = browser.new_page()
                    page.goto(f'file://{temp_html.absolute()}')
                    
                    page.pdf(
                        path=str(output_path),
                        format='A4',
                        margin={
                            'top': '1.5cm',
                            'right': '1cm',
                            'bottom': '1.5cm',
                            'left': '1cm'
                        },
                        print_background=True,
                        display_header_footer=False
                    )
                    
                    browser.close()
                
                # Limpiar temporal
                if temp_html.exists():
                    temp_html.unlink()
                
                logger.info(f"✓ PDF generado: {output_path}")
                return str(output_path)
                
            except Exception as e:
                logger.error(f"Error compilando PDF: {e}", exc_info=True)
                raise PDFGenerationError(f"Playwright failed: {str(e)}")
        
        # Ejecutar en thread pool para evitar conflicto con event loop
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_in_thread)
            result = future.result(timeout=120)  # 2 minutos timeout
            return result
    
    def _build_header_template(self, metadata: Optional[Dict[str, Any]]) -> str:
        """
        Construye template HTML para header del PDF.
        
        Args:
            metadata: Dict con metadata del PDF
            
        Returns:
            String con HTML del header
        """
        empresa = 'Conexión Consultora'
        if metadata:
            empresa = metadata.get('author', empresa)
        
        return f'''
        <div style="font-size: 9pt; color: #6B7280; text-align: center; width: 100%; padding: 10px 0;">
            {empresa}
        </div>
        '''
    
    def _build_footer_template(self) -> str:
        """
        Construye template HTML para footer del PDF.
        
        Returns:
            String con HTML del footer
        """
        return '''
        <div style="font-size: 8pt; color: #9CA3AF; text-align: right; width: 100%; padding: 10px 20px;">
            Página <span class="pageNumber"></span> de <span class="totalPages"></span>
        </div>
        '''
    
    def get_pdf_info(self, pdf_path: str) -> Dict[str, Any]:
        """
        Obtiene información del PDF generado.
        
        Args:
            pdf_path: Ruta al PDF
            
        Returns:
            Dict con info del PDF (tamaño, páginas, etc)
        """
        path = Path(pdf_path)
        
        if not path.exists():
            return {'error': 'PDF no encontrado'}
        
        size_bytes = path.stat().st_size
        
        return {
            'size_bytes': size_bytes,
            'size_kb': size_bytes / 1024,
            'size_mb': size_bytes / (1024 * 1024),
            'pages': None,  # Playwright no provee conteo directo
            'path': str(path)
        }

