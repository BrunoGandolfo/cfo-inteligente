"""
Helper para agregar metadata profesional a PDFs generados por WeasyPrint

WeasyPrint genera PDFs excelentes pero sin metadata personalizada.
Este módulo usa pypdf para post-procesar PDFs y agregar:
- Título
- Autor
- Subject
- Keywords
- Producer
- Creator
- Fecha de creación

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from pypdf import PdfWriter, PdfReader
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

from app.core.logger import get_logger

logger = get_logger(__name__)


def add_metadata_to_pdf(
    input_pdf_path: str,
    output_pdf_path: str,
    metadata: Optional[Dict[str, str]] = None
) -> None:
    """
    Agrega metadata profesional a un PDF generado por WeasyPrint.
    
    Args:
        input_pdf_path: Ruta del PDF original (sin metadata)
        output_pdf_path: Ruta donde guardar PDF con metadata
        metadata: Dict con metadata personalizada
            Claves estándar PDF:
            - '/Title': Título del documento
            - '/Author': Autor
            - '/Subject': Asunto/descripción
            - '/Keywords': Palabras clave separadas por comas
            - '/Producer': Software que produce el PDF
            - '/Creator': Software que crea el contenido original
            - '/CreationDate': Fecha de creación (formato PDF)
    
    Ejemplo:
        metadata = {
            '/Title': 'Reporte CFO - Octubre 2025',
            '/Author': 'Bruno Gandolfo - Conexión Consultora',
            '/Subject': 'Análisis Financiero Mensual',
            '/Keywords': 'CFO, Uruguay, Rentabilidad, KPIs',
            '/Producer': 'CFO Inteligente - Bloomberg Terminal AI',
            '/Creator': 'WeasyPrint 66.0'
        }
        add_metadata_to_pdf('report.pdf', 'report_final.pdf', metadata)
    """
    try:
        logger.info(f"Agregando metadata a PDF: {input_pdf_path}")
        
        # Leer PDF original
        reader = PdfReader(input_pdf_path)
        writer = PdfWriter()
        
        # Copiar todas las páginas
        for page in reader.pages:
            writer.add_page(page)
        
        # Agregar metadata si se proporcionó
        if metadata:
            writer.add_metadata(metadata)
            logger.info(f"Metadata agregada: {len(metadata)} campos")
        
        # Guardar PDF con metadata
        with open(output_pdf_path, 'wb') as f:
            writer.write(f)
        
        logger.info(f"PDF con metadata guardado: {output_pdf_path}")
        
    except Exception as e:
        logger.error(f"Error agregando metadata: {str(e)}")
        raise


def get_default_report_metadata(
    report_type: str,
    period_label: str,
    generated_by: str = "CFO Inteligente"
) -> Dict[str, str]:
    """
    Genera metadata por defecto para reportes CFO.
    
    Args:
        report_type: Tipo de reporte (ej: "Mensual", "Trimestral", "Anual")
        period_label: Etiqueta del período (ej: "Octubre 2025", "Q3 2025")
        generated_by: Nombre del sistema o usuario que genera el reporte
    
    Returns:
        Dict con metadata estándar para reportes CFO
        
    Ejemplo:
        metadata = get_default_report_metadata('Mensual', 'Octubre 2025')
        # Retorna:
        # {
        #     '/Title': 'Reporte Mensual - Octubre 2025',
        #     '/Author': 'Conexión Consultora',
        #     '/Subject': 'Análisis Financiero Mensual',
        #     ...
        # }
    """
    return {
        '/Title': f'Reporte {report_type} - {period_label}',
        '/Author': 'Conexión Consultora',
        '/Subject': f'Análisis Financiero {report_type}',
        '/Keywords': 'CFO, Uruguay, Finanzas, Rentabilidad, KPIs, Ingresos, Gastos, Conexión',
        '/Producer': f'{generated_by} - Bloomberg Terminal AI',
        '/Creator': 'WeasyPrint 66.0 + Claude Sonnet 4.5',
        '/CreationDate': datetime.now().strftime("D:%Y%m%d%H%M%S")
    }


def get_custom_metadata(
    title: str,
    author: str = "Conexión Consultora",
    subject: str = "",
    keywords: str = "",
    producer: str = "CFO Inteligente"
) -> Dict[str, str]:
    """
    Genera metadata personalizada con más control.
    
    Args:
        title: Título del PDF
        author: Autor del documento
        subject: Asunto/descripción
        keywords: Palabras clave (separadas por comas)
        producer: Software productor
        
    Returns:
        Dict con metadata personalizada
    """
    metadata = {
        '/Title': title,
        '/Author': author,
        '/Producer': producer,
        '/Creator': 'WeasyPrint 66.0',
        '/CreationDate': datetime.now().strftime("D:%Y%m%d%H%M%S")
    }
    
    if subject:
        metadata['/Subject'] = subject
    
    if keywords:
        metadata['/Keywords'] = keywords
    
    return metadata

