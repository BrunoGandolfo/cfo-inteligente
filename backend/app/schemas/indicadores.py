"""
Schemas Pydantic para módulo de Indicadores Económicos de Uruguay.

Define los modelos de respuesta para:
- UI (Unidad Indexada)
- UR (Unidad Reajustable)
- IPC (Índice de Precios al Consumo)
- BPC (Base de Prestaciones y Contribuciones)
- Cotizaciones (USD, EUR, BRL)
"""

from pydantic import BaseModel
from typing import Optional


class IndicadorResponse(BaseModel):
    """Respuesta para un indicador individual (UI, UR, IPC, BPC)."""
    valor: float
    fecha: Optional[str] = None
    fuente: str


class CotizacionResponse(BaseModel):
    """Cotización de una moneda con compra y venta."""
    compra: float
    venta: float


class CotizacionesResponse(BaseModel):
    """Todas las cotizaciones de monedas."""
    usd: CotizacionResponse
    eur: CotizacionResponse
    brl: CotizacionResponse
    timestamp: str


class IndicadoresTodosResponse(BaseModel):
    """Respuesta con todos los indicadores económicos."""
    ui: IndicadorResponse
    ur: IndicadorResponse
    ipc: IndicadorResponse
    bpc: IndicadorResponse
    inflacion: IndicadorResponse
    cotizaciones: CotizacionesResponse
    actualizado: str
