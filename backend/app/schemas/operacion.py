from pydantic import BaseModel, field_validator, model_validator
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

class OperacionBase(BaseModel):
    fecha: date
    tipo_cambio: Decimal
    localidad: str  # Montevideo o Mercedes
    
    @field_validator('fecha')
    @classmethod
    def fecha_no_futura(cls, v):
        if v > date.today():
            raise ValueError('La fecha no puede ser futura')
        return v

    @field_validator('tipo_cambio')
    @classmethod
    def tipo_cambio_positivo(cls, v):
        if v is None or v <= 0:
            raise ValueError('El tipo de cambio debe ser mayor a 0')
        return v

class IngresoCreate(OperacionBase):
    monto_original: Decimal
    moneda_original: str  # UYU o USD
    area_id: UUID  # Obligatorio para INGRESO
    cliente: Optional[str] = None
    cliente_telefono: Optional[str] = None
    descripcion: Optional[str] = None
    
    @field_validator('monto_original')
    @classmethod
    def monto_positivo(cls, v):
        if v <= 0:
            raise ValueError('El monto debe ser positivo')
        return v
    
    @field_validator('area_id')
    @classmethod
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
    
    @field_validator('monto_original')
    @classmethod
    def monto_positivo(cls, v):
        if v <= 0:
            raise ValueError('El monto debe ser positivo')
        return v
    
    @field_validator('area_id')
    @classmethod
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
    
    @model_validator(mode='after')
    def al_menos_un_monto(self):
        if not self.monto_uyu and not self.monto_usd:
            raise ValueError('Debe ingresar al menos un monto (UYU o USD)')
        if self.monto_usd and self.monto_usd <= 0:
            raise ValueError('El monto USD debe ser positivo')
        if self.monto_uyu and self.monto_uyu <= 0:
            raise ValueError('El monto UYU debe ser positivo')
        return self

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
