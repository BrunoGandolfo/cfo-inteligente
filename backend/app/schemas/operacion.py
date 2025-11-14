from pydantic import BaseModel, validator, field_validator
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID
from app.models.operacion import TipoOperacion

class OperacionBase(BaseModel):
    fecha: date
    tipo_cambio: Decimal
    localidad: str  # Montevideo o Mercedes
    
    @validator('fecha')
    def fecha_no_futura(cls, v):
        if v > date.today():
            raise ValueError('La fecha no puede ser futura')
        return v

class IngresoCreate(OperacionBase):
    monto_original: Decimal
    moneda_original: str  # UYU o USD
    area_id: UUID  # Obligatorio para INGRESO
    cliente: Optional[str] = None
    cliente_telefono: Optional[str] = None
    descripcion: Optional[str] = None
    
    @validator('monto_original')
    def monto_positivo(cls, v):
        if v <= 0:
            raise ValueError('El monto debe ser positivo')
        return v
    
    @validator('area_id')
    def area_obligatoria_ingreso(cls, v):
        """
        Regla de negocio: INGRESO debe tener área asignada.
        Filosofía DHH: Validación explícita en el lugar correcto.
        """
        if v is None:
            raise ValueError('INGRESO debe tener área asignada')
        return v

class GastoCreate(OperacionBase):
    monto_original: Decimal
    moneda_original: str  # UYU o USD
    area_id: UUID  # Obligatorio para GASTO
    proveedor: Optional[str] = None
    proveedor_telefono: Optional[str] = None
    descripcion: Optional[str] = None
    
    @validator('monto_original')
    def monto_positivo(cls, v):
        if v <= 0:
            raise ValueError('El monto debe ser positivo')
        return v
    
    @validator('area_id')
    def area_obligatoria_gasto(cls, v):
        """
        Regla de negocio: GASTO debe tener área asignada.
        Filosofía DHH: Validación explícita en el lugar correcto.
        """
        if v is None:
            raise ValueError('GASTO debe tener área asignada')
        return v

class RetiroCreate(OperacionBase):
    monto_uyu: Optional[Decimal] = None
    monto_usd: Optional[Decimal] = None
    descripcion: Optional[str] = None
    
    @validator('monto_usd')
    def al_menos_un_monto(cls, v, values):
        if not v and not values.get('monto_uyu'):
            raise ValueError('Debe ingresar al menos un monto (UYU o USD)')
        if v and v <= 0:
            raise ValueError('El monto debe ser positivo')
        return v

class SocioDistribucion(BaseModel):
    socio_nombre: str  # Agustina, Viviana, Gonzalo, Pancho, Bruno
    monto_uyu: Optional[Decimal] = None
    monto_usd: Optional[Decimal] = None

class DistribucionCreate(OperacionBase):
    agustina_uyu: Optional[Decimal] = None
    agustina_usd: Optional[Decimal] = None
    viviana_uyu: Optional[Decimal] = None
    viviana_usd: Optional[Decimal] = None
    gonzalo_uyu: Optional[Decimal] = None
    gonzalo_usd: Optional[Decimal] = None
    pancho_uyu: Optional[Decimal] = None
    pancho_usd: Optional[Decimal] = None
    bruno_uyu: Optional[Decimal] = None
    bruno_usd: Optional[Decimal] = None
