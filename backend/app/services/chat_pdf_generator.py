"""
Chat PDF Generator - Versión Pandoc/WeasyPrint
Convierte markdown del chat a PDF directamente.
"""

import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from app.core.logger import get_logger

logger = get_logger(__name__)


class ChatPDFGenerator:
    """Generador de PDF usando Pandoc + WeasyPrint."""
    
    OUTPUT_DIR = Path(__file__).parent.parent.parent / "output" / "chat_exports"
    
    def __init__(self):
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    def generar(
        self,
        contenido_markdown: str,
        titulo_override: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Genera PDF desde markdown usando Pandoc."""
        start = datetime.now()
        
        titulo = titulo_override or "Reporte CFO AI"
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        # Markdown con metadata
        markdown_final = f"""---
title: "{titulo}"
subtitle: "Conexión Consultora"
date: "{fecha}"
---

{contenido_markdown}
"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chat_export_{timestamp}.pdf"
        pdf_path = self.OUTPUT_DIR / filename
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(markdown_final)
            md_path = f.name
        
        try:
            result = subprocess.run(
                ['pandoc', md_path, '-o', str(pdf_path), '--pdf-engine=weasyprint'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            Path(md_path).unlink(missing_ok=True)
            
            if result.returncode != 0:
                logger.error(f"Pandoc error: {result.stderr}")
                raise Exception(f"Error generando PDF: {result.stderr}")
            
            size_kb = pdf_path.stat().st_size / 1024
            elapsed_ms = int((datetime.now() - start).total_seconds() * 1000)
            
            logger.info(f"PDF generado: {filename} ({size_kb:.1f} KB) en {elapsed_ms}ms")
            
            return {
                'pdf_path': str(pdf_path),
                'filename': filename,
                'size_kb': round(size_kb, 2),
                'tiempo_generacion_ms': elapsed_ms
            }
            
        except subprocess.TimeoutExpired:
            Path(md_path).unlink(missing_ok=True)
            raise Exception("Timeout generando PDF")
        except FileNotFoundError:
            raise Exception("Pandoc no instalado. Ejecutar: sudo apt install pandoc")


def generar_pdf_desde_chat(markdown: str, titulo: Optional[str] = None) -> str:
    """Helper - retorna path del PDF."""
    return ChatPDFGenerator().generar(markdown, titulo)['pdf_path']
