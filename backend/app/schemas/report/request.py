"""
Request Schemas - Reportes PDF

Define estructura de requests para generación de reportes.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Optional, Literal


class ComparisonConfig(BaseModel):
    """
    Configuración de comparación entre períodos.
    
    Ejemplo:
        {
            "activo": true,
            "tipo": "periodo_anterior",
            "fecha_inicio": "2025-09-01",
            "fecha_fin": "2025-09-30"
        }
    """
    
    activo: bool = Field(default=False, description="Si está activa la comparación")
    tipo: Literal['periodo_anterior', 'mismo_periodo_año_pasado', 'custom'] = Field(
        default='periodo_anterior',
        description="Tipo de comparación automática o custom"
    )
    fecha_inicio: Optional[date] = Field(default=None, description="Solo si tipo=custom")
    fecha_fin: Optional[date] = Field(default=None, description="Solo si tipo=custom")
    
    @field_validator('fecha_fin')
    def validate_fecha_fin(cls, v, info):
        """Valida que fecha_fin > fecha_inicio si son custom"""
        if v and info.data.get('fecha_inicio') and v < info.data['fecha_inicio']:
            raise ValueError('fecha_fin debe ser mayor que fecha_inicio')
        return v


class ReportOptions(BaseModel):
    """
    Opciones avanzadas del reporte.
    
    Permite personalizar contenido y estilo.
    """
    
    incluir_proyecciones: bool = Field(
        default=True,
        description="Incluir proyecciones con regresión lineal"
    )
    incluir_insights_ia: bool = Field(
        default=True,
        description="Incluir insights generados por Claude Sonnet 4.5"
    )
    incluir_escenarios: bool = Field(
        default=False,
        description="Incluir escenarios stress (optimista/base/conservador)"
    )
    formato: Literal['ejecutivo', 'completo', 'resumido'] = Field(
        default='ejecutivo',
        description="Formato del reporte (10 páginas ejecutivo por defecto)"
    )
    paleta: Literal['institucional', 'moderna_2024'] = Field(
        default='moderna_2024',
        description="Paleta de colores para gráficos"
    )


class PeriodConfig(BaseModel):
    """
    Configuración del período del reporte.
    
    Soporta períodos predefinidos (mes_actual, trimestre) o custom.
    """
    
    tipo: Literal['mes_actual', 'mes_anterior', 'trimestre_actual', 
                  'semestre_actual', 'anio_2025', 'custom'] = Field(
        default='mes_actual',
        description="Tipo de período predefinido o custom"
    )
    fecha_inicio: Optional[date] = Field(
        default=None,
        description="Requerido si tipo=custom, ignorado si predefinido"
    )
    fecha_fin: Optional[date] = Field(
        default=None,
        description="Requerido si tipo=custom, ignorado si predefinido"
    )


class ReportRequest(BaseModel):
    """
    Request completo para generación de reporte PDF.
    
    Ejemplo completo:
        {
            "period": {
                "tipo": "mes_actual"
            },
            "comparison": {
                "activo": true,
                "tipo": "periodo_anterior"
            },
            "options": {
                "incluir_proyecciones": true,
                "incluir_insights_ia": true,
                "paleta": "moderna_2024"
            }
        }
    """
    
    period: PeriodConfig = Field(
        description="Configuración del período principal"
    )
    comparison: Optional[ComparisonConfig] = Field(
        default=None,
        description="Configuración de comparación (opcional)"
    )
    options: ReportOptions = Field(
        default_factory=ReportOptions,
        description="Opciones del reporte"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "period": {
                    "tipo": "mes_actual"
                },
                "comparison": {
                    "activo": True,
                    "tipo": "periodo_anterior"
                },
                "options": {
                    "incluir_proyecciones": True,
                    "incluir_insights_ia": True,
                    "incluir_escenarios": False,
                    "formato": "ejecutivo",
                    "paleta": "moderna_2024"
                }
            }
        }

