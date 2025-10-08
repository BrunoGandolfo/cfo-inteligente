"""
Custom Exceptions - Sistema de Reportes CFO

Define excepciones específicas del dominio para mejor manejo de errores.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from fastapi import HTTPException, status


class InsufficientDataError(HTTPException):
    """
    Se lanza cuando no hay suficientes datos para generar reporte.
    
    Ejemplo: Período con <20 operaciones.
    """
    
    def __init__(self, operaciones_encontradas: int, minimo_requerido: int = 20):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "insufficient_data",
                "message": "Datos insuficientes para generar reporte",
                "operaciones_encontradas": operaciones_encontradas,
                "minimo_requerido": minimo_requerido,
                "sugerencia": "Amplíe el rango de fechas o seleccione un período con más actividad"
            }
        )


class ClaudeTimeoutError(Exception):
    """
    Se lanza cuando Claude API no responde en tiempo esperado.
    
    NO es HTTPException - se maneja internamente con fallback.
    """
    
    def __init__(self, timeout_seconds: int):
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Claude API timeout después de {timeout_seconds}s")


class PDFGenerationError(HTTPException):
    """
    Se lanza cuando falla generación de PDF.
    
    Ejemplo: Error WeasyPrint, template no encontrado, etc.
    """
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "pdf_generation_failed",
                "message": "Error al generar PDF",
                "detail": detail
            }
        )


class InvalidDateRangeError(HTTPException):
    """
    Se lanza cuando rango de fechas es inválido.
    
    Ejemplo: fecha_fin < fecha_inicio, rango > 365 días, fechas futuras.
    """
    
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_date_range",
                "message": message
            }
        )


class ChartGenerationError(Exception):
    """
    Se lanza cuando falla generación de gráfico.
    
    NO es HTTPException - el reporte puede continuar sin algunos gráficos.
    """
    
    def __init__(self, chart_type: str, detail: str):
        self.chart_type = chart_type
        super().__init__(f"Error generando gráfico {chart_type}: {detail}")


class TemplateNotFoundError(PDFGenerationError):
    """Se lanza cuando template Jinja2 no existe."""
    
    def __init__(self, template_name: str):
        super().__init__(f"Template no encontrado: {template_name}")


class MetadataError(Exception):
    """
    Se lanza cuando falla agregar metadata a PDF.
    
    NO es HTTPException - el PDF se puede retornar sin metadata.
    """
    
    def __init__(self, detail: str):
        super().__init__(f"Error agregando metadata: {detail}")

