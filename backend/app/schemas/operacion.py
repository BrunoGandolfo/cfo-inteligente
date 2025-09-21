from pydantic import BaseModel, validator
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

class OperacionBase(BaseModel):
    fecha: date
    tipo_cambio: Decimal
    localidad: str  # Montevideo o Mercedes
    descripcion: Optional[str] = None
    
    @validator('fecha')
    def fecha_no_futura(cls, v):
        if v > date.today():
            raise ValueError('La fecha no puede ser futura')
        return v

class IngresoCreate(OperacionBase):
    monto_original: Decimal
    moneda_original: str  # UYU o USD
    area_id: UUID
    cliente: Optional[str] = None
    cliente_telefono: Optional[str] = None
    
    @validator('monto_original')
    def monto_positivo(cls, v):
        if v <= 0:
            raise ValueError('El monto debe ser positivo')
        return v

class GastoCreate(OperacionBase):
    monto_original: Decimal
    moneda_original: str  # UYU o USD
    area_id: UUID
    proveedor: Optional[str] = None
    proveedor_telefono: Optional[str] = None
    
    @validator('monto_original')
    def monto_positivo(cls, v):
        if v <= 0:
            raise ValueError('El monto debe ser positivo')
        return v

class RetiroCreate(OperacionBase):
    monto_uyu: Optional[Decimal] = None
    monto_usd: Optional[Decimal] = None
    concepto: Optional[str] = None
    
    @validator('monto_usd')
    def al_menos_un_monto(cls, v, values):
        if not v and not values.get('monto_uyu'):
            raise ValueError('Debe ingresar al menos un monto (UYU o USD)')
        if v and v <= 0:
            raise ValueError('El monto debe ser positivo')
        return v

class DistribucionCreate(OperacionBase):
    distribuciones: list[dict]  
    # [{socio_id: UUID, socio_nombre: str, monto_uyu: Optional[Decimal], monto_usd: Optional[Decimal]}]
