"""
Schemas Pydantic para gestión de casos legales.

Define los modelos de validación y respuesta para:
- Crear casos legales
- Actualizar casos
- Respuestas de API
- Listado de casos
"""

from pydantic import BaseModel, field_validator
from datetime import date, datetime
from typing import Optional
from uuid import UUID
from app.models.caso import EstadoCaso, PrioridadCaso


class CasoBase(BaseModel):
    """Campos comunes para casos."""
    titulo: str
    estado: EstadoCaso
    prioridad: PrioridadCaso
    fecha_vencimiento: Optional[date] = None
    responsable_id: UUID
    expediente_id: Optional[UUID] = None
    
    @field_validator('titulo')
    @classmethod
    def titulo_no_vacio(cls, v):
        if not v or not v.strip():
            raise ValueError('El título no puede estar vacío')
        if len(v) > 300:
            raise ValueError('El título no puede exceder 300 caracteres')
        return v.strip()


class CasoCreate(CasoBase):
    """Schema para crear un caso."""
    responsable_id: Optional[UUID] = None


class CasoUpdate(BaseModel):
    """Schema para actualizar un caso (todos los campos opcionales)."""
    titulo: Optional[str] = None
    estado: Optional[EstadoCaso] = None
    prioridad: Optional[PrioridadCaso] = None
    fecha_vencimiento: Optional[date] = None
    responsable_id: Optional[UUID] = None
    expediente_id: Optional[UUID] = None
    
    @field_validator('titulo')
    @classmethod
    def titulo_no_vacio(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('El título no puede estar vacío')
            if len(v) > 300:
                raise ValueError('El título no puede exceder 300 caracteres')
            return v.strip()
        return v


class CasoResponse(CasoBase):
    """Schema de respuesta para un caso."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Pydantic v2 - permite ORM mode


class CasoList(BaseModel):
    """Respuesta paginada para listado de casos."""
    total: int
    casos: list[CasoResponse]
    
    @field_validator('total')
    @classmethod
    def total_no_negativo(cls, v):
        if v < 0:
            raise ValueError('El total no puede ser negativo')
        return v
