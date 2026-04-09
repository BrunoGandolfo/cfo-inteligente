"""Schemas Pydantic para trámites registrales DGR."""

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


REGISTROS_DGR = {
    "RGI": "Registro Nacional de Actos Personales",
    "RPI": "Registro de la Propiedad, Sección Inmobiliaria",
    "RAE": "Registro de la Propiedad, Sección Mobiliaria, Aeronaves",
    "RA": "Registro de la Propiedad, Sección Mobiliaria, Automotores",
    "PSD": "Registro de la Propiedad, Sección Mobiliaria, Prenda S/Despl.",
    "RCO": "Registro de Personas Jurídicas",
    "ACF": "Registro de Personas Jurídicas Sec. Asoc. Civ. y Fundaciones",
    "RUB": "Registro de Rúbrica de Libros",
}

OFICINAS_DGR = {
    "G": "Artigas",
    "A": "Canelones",
    "E": "Cerro Largo",
    "L": "Colonia",
    "S": "La Costa",
    "Q": "Durazno",
    "N": "Flores",
    "O": "Florida",
    "P": "Lavalleja",
    "B": "Maldonado",
    "X": "Montevideo",
    "W": "Pando",
    "I": "Paysandu",
    "J": "Rio Negro",
    "F": "Rivera",
    "C": "Rocha",
    "H": "Salto",
    "M": "San Jose",
    "K": "Soriano",
    "R": "Tacuarembo",
    "D": "Treinta y Tres",
}


class TramiteDgrCreate(BaseModel):
    """Schema de creación para trámite DGR."""

    registro: str
    oficina: str
    anio: int
    numero_entrada: int
    bis: Optional[str] = ""


class TramiteDgrUpdate(BaseModel):
    """Schema de actualización parcial para trámite DGR."""

    estado_actual: Optional[str] = None
    actos: Optional[str] = None
    observaciones: Optional[str] = None
    fecha_ingreso: Optional[date] = None
    escribano_emisor: Optional[str] = None
    fecha_vencimiento: Optional[date] = None
    ultimo_chequeo: Optional[datetime] = None
    estado_anterior: Optional[str] = None
    cambio_detectado: Optional[bool] = None
    activo: Optional[bool] = None


class TramiteDgrResponse(BaseModel):
    """Schema de respuesta para trámite DGR."""

    id: UUID
    registro: str
    registro_nombre: Optional[str] = None
    oficina: str
    oficina_nombre: Optional[str] = None
    anio: int
    numero_entrada: int
    bis: Optional[str] = None
    fecha_ingreso: Optional[date] = None
    escribano_emisor: Optional[str] = None
    estado_actual: Optional[str] = None
    actos: Optional[str] = None
    observaciones: Optional[str] = None
    fecha_vencimiento: Optional[date] = None
    ultimo_chequeo: Optional[datetime] = None
    estado_anterior: Optional[str] = None
    cambio_detectado: bool
    activo: bool
    responsable_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TramiteListResponse(BaseModel):
    """Respuesta paginada de trámites."""

    total: int
    limit: int
    offset: int
    tramites: List[TramiteDgrResponse]


class MarcarNotificadosRequest(BaseModel):
    """Body para marcar trámites como notificados."""

    ids: List[UUID]
