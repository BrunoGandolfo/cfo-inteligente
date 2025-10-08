"""
Response Schemas - Reportes PDF

Define estructura de responses.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ReportMetadata(BaseModel):
    """
    Metadata del reporte generado.
    
    Se retorna en header o en response alternativo.
    """
    
    filename: str = Field(description="Nombre del archivo PDF")
    size_kb: float = Field(description="Tamaño en KB")
    pages: int = Field(description="Cantidad de páginas")
    generation_time_seconds: float = Field(description="Tiempo de generación")
    period_label: str = Field(description="Etiqueta del período (ej: 'Octubre 2025')")
    fecha_inicio: str = Field(description="Fecha inicio ISO")
    fecha_fin: str = Field(description="Fecha fin ISO")
    generated_at: datetime = Field(description="Timestamp generación")
    has_comparison: bool = Field(description="Si incluye comparación")
    has_projections: bool = Field(description="Si incluye proyecciones")
    has_ai_insights: bool = Field(description="Si incluye insights IA")
    
    class Config:
        json_schema_extra = {
            "example": {
                "filename": "Reporte_CFO_Oct2025_vsSep2025.pdf",
                "size_kb": 687.5,
                "pages": 10,
                "generation_time_seconds": 14.2,
                "period_label": "Octubre 2025",
                "fecha_inicio": "2025-10-01",
                "fecha_fin": "2025-10-31",
                "generated_at": "2025-10-07T19:45:32",
                "has_comparison": True,
                "has_projections": True,
                "has_ai_insights": True
            }
        }


class ProgressUpdate(BaseModel):
    """
    Actualización de progreso durante generación.
    
    Para WebSocket/SSE en futuras versiones.
    """
    
    step: str = Field(description="Paso actual")
    progress_pct: int = Field(ge=0, le=100, description="Porcentaje completado")
    message: str = Field(description="Mensaje descriptivo")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "step": "generating_charts",
                "progress_pct": 60,
                "message": "Generando gráficos profesionales...",
                "timestamp": "2025-10-07T19:45:25"
            }
        }


class ReportResponse(BaseModel):
    """
    Response metadata (sin el PDF en sí).
    
    El PDF se retorna como FileResponse.
    Este schema es para respuestas alternativas (metadata only).
    """
    
    success: bool = Field(description="Si la generación fue exitosa")
    metadata: ReportMetadata = Field(description="Metadata del reporte")
    warnings: Optional[list[str]] = Field(
        default=None,
        description="Warnings no críticos (ej: 'Claude timeout, usando fallback')"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "metadata": {
                    "filename": "Reporte_CFO_Oct2025.pdf",
                    "size_kb": 687.5,
                    "pages": 10,
                    "generation_time_seconds": 14.2,
                    "period_label": "Octubre 2025",
                    "fecha_inicio": "2025-10-01",
                    "fecha_fin": "2025-10-31",
                    "generated_at": "2025-10-07T19:45:32",
                    "has_comparison": False,
                    "has_projections": True,
                    "has_ai_insights": True
                },
                "warnings": [
                    "Claude API timeout - usando insights fallback"
                ]
            }
        }

