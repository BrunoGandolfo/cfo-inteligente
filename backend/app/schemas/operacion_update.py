"""
Schemas para actualización de operaciones - Sistema CFO Inteligente
Permite editar operaciones manteniendo auditoría (updated_at)
"""
from pydantic import BaseModel, validator
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID


class IngresoUpdate(BaseModel):
    """Schema para actualizar un ingreso existente"""
    fecha: Optional[date] = None
    cliente: Optional[str] = None
    area_id: Optional[UUID] = None
    localidad: Optional[str] = None
    monto_original: Optional[Decimal] = None
    moneda_original: Optional[str] = None
    tipo_cambio: Optional[Decimal] = None
    descripcion: Optional[str] = None
    
    @validator('fecha')
    def fecha_no_futura(cls, v):
        if v and v > date.today():
            raise ValueError('La fecha no puede ser futura')
        return v
    
    @validator('monto_original')
    def monto_positivo(cls, v):
        if v is not None and v <= 0:
            raise ValueError('El monto debe ser positivo')
        return v


class GastoUpdate(BaseModel):
    """Schema para actualizar un gasto existente"""
    fecha: Optional[date] = None
    proveedor: Optional[str] = None
    area_id: Optional[UUID] = None
    localidad: Optional[str] = None
    monto_original: Optional[Decimal] = None
    moneda_original: Optional[str] = None
    tipo_cambio: Optional[Decimal] = None
    descripcion: Optional[str] = None
    
    @validator('fecha')
    def fecha_no_futura(cls, v):
        if v and v > date.today():
            raise ValueError('La fecha no puede ser futura')
        return v
    
    @validator('monto_original')
    def monto_positivo(cls, v):
        if v is not None and v <= 0:
            raise ValueError('El monto debe ser positivo')
        return v


class RetiroUpdate(BaseModel):
    """Schema para actualizar un retiro existente"""
    fecha: Optional[date] = None
    localidad: Optional[str] = None
    monto_uyu: Optional[Decimal] = None
    monto_usd: Optional[Decimal] = None
    tipo_cambio: Optional[Decimal] = None
    descripcion: Optional[str] = None
    
    @validator('fecha')
    def fecha_no_futura(cls, v):
        if v and v > date.today():
            raise ValueError('La fecha no puede ser futura')
        return v

