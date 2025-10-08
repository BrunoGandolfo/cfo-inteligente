"""
Metrics Schemas - Estructura de métricas calculadas

Define estructura de las 29 métricas disponibles organizadas por categoría.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import date


class TotalsMetrics(BaseModel):
    """M1-M8: Totales absolutos en UYU y USD"""
    
    ingresos_uyu: float = Field(description="Total ingresos en UYU")
    ingresos_usd: float = Field(description="Total ingresos en USD")
    gastos_uyu: float = Field(description="Total gastos en UYU")
    gastos_usd: float = Field(description="Total gastos en USD")
    retiros_uyu: float = Field(description="Total retiros en UYU")
    retiros_usd: float = Field(description="Total retiros en USD")
    distribuciones_uyu: float = Field(description="Total distribuciones en UYU")
    distribuciones_usd: float = Field(description="Total distribuciones en USD")


class ResultsMetrics(BaseModel):
    """M9-M10: Resultados operativo y neto"""
    
    resultado_operativo: float = Field(description="Ingresos - Gastos")
    resultado_neto: float = Field(description="Ingresos - Gastos - Retiros - Distribuciones")


class RatiosMetrics(BaseModel):
    """M11-M14: Rentabilidad en porcentaje"""
    
    margen_operativo: float = Field(description="(Resultado Operativo / Ingresos) × 100")
    margen_neto: float = Field(description="(Resultado Neto / Ingresos) × 100")
    rentabilidad_por_area: Dict[str, float] = Field(description="Dict {area: rentabilidad%}")
    rentabilidad_por_localidad: Dict[str, float] = Field(description="Dict {localidad: rentabilidad%}")


class DistributionMetrics(BaseModel):
    """M15-M17: Distribución porcentual"""
    
    porcentaje_ingresos_por_area: Dict[str, float] = Field(description="% ingresos por área")
    porcentaje_ingresos_por_localidad: Dict[str, float] = Field(description="% ingresos por localidad")
    porcentaje_distribucion_por_socio: Dict[str, float] = Field(description="% distribución por socio")


class EfficiencyMetrics(BaseModel):
    """M18-M20: Métricas de eficiencia"""
    
    ticket_promedio_ingreso: float = Field(description="Promedio monto por ingreso")
    ticket_promedio_gasto: float = Field(description="Promedio monto por gasto")
    cantidad_operaciones: int = Field(description="Total operaciones del período")
    cantidad_ingresos: int = Field(description="Cantidad de ingresos")
    cantidad_gastos: int = Field(description="Cantidad de gastos")


class TrendsMetrics(BaseModel):
    """M21-M26: Comparaciones temporales y proyecciones"""
    
    # Comparaciones (si hay período de comparación)
    variacion_mom_ingresos: Optional[float] = Field(default=None, description="% variación MoM ingresos")
    variacion_mom_gastos: Optional[float] = Field(default=None, description="% variación MoM gastos")
    variacion_mom_rentabilidad: Optional[float] = Field(default=None, description="Puntos variación MoM rentabilidad")
    
    # Promedio móvil
    promedio_movil_3m: Optional[float] = Field(default=None, description="Promedio últimos 3 meses")
    promedio_movil_6m: Optional[float] = Field(default=None, description="Promedio últimos 6 meses")
    
    # Proyecciones
    proyeccion_proximos_3m: Optional[float] = Field(default=None, description="Proyección 3 meses (regresión)")
    proyeccion_fin_anio: Optional[float] = Field(default=None, description="Proyección fin año")


class MetricsAggregate(BaseModel):
    """
    Agregado de TODAS las métricas (29 total).
    
    Estructura completa retornada por MetricsAggregator.
    """
    
    # Categorías de métricas
    totals: TotalsMetrics
    results: ResultsMetrics
    ratios: RatiosMetrics
    distribution: DistributionMetrics
    efficiency: EfficiencyMetrics
    trends: TrendsMetrics
    
    # Metadata del cálculo
    period_label: str = Field(description="Etiqueta del período")
    fecha_inicio: date = Field(description="Fecha inicio")
    fecha_fin: date = Field(description="Fecha fin")
    duracion_dias: int = Field(description="Días del período")
    
    # Area líder (M27)
    area_lider: Dict[str, Any] = Field(
        description="Área con más ingresos: {nombre, monto, porcentaje}"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "totals": {
                    "ingresos_uyu": 114941988.84,
                    "gastos_uyu": 76486651.33,
                    # ...
                },
                "results": {
                    "resultado_operativo": 38455337.51,
                    "resultado_neto": 31587340.35
                },
                "ratios": {
                    "margen_operativo": 33.46,
                    "margen_neto": 27.48,
                    "rentabilidad_por_area": {"Notarial": 78.61, "Jurídica": 75.94},
                    "rentabilidad_por_localidad": {"MONTEVIDEO": 77.42, "MERCEDES": 72.11}
                },
                "period_label": "Octubre 2025",
                "fecha_inicio": "2025-10-01",
                "fecha_fin": "2025-10-31",
                "duracion_dias": 31,
                "area_lider": {
                    "nombre": "Notarial",
                    "monto": 35000000.0,
                    "porcentaje": 30.45
                }
            }
        }

