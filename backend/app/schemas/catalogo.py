"""Schemas Pydantic para catálogos."""

from uuid import UUID

from pydantic import BaseModel


class AreaResponse(BaseModel):
    """Schema de respuesta para un área del estudio."""

    id: UUID
    nombre: str

    class Config:
        from_attributes = True


class SocioResponse(BaseModel):
    """Schema de respuesta para un socio del estudio."""

    id: UUID
    nombre: str
    porcentaje_participacion: float

    class Config:
        from_attributes = True
