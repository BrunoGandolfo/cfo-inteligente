"""Schemas Pydantic para artículos doctrinarios."""

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DoctrinaBase(BaseModel):
    """Campos base de un artículo doctrinario."""

    oai_identifier: str
    titulo: str
    autor: Optional[str] = None
    fecha_publicacion: Optional[date] = None
    fuente: str
    revista: Optional[str] = None
    url_articulo: Optional[str] = None
    url_pdf: Optional[str] = None
    abstract: Optional[str] = None
    texto_completo: Optional[str] = None
    materias: Optional[List[str]] = None
    idioma: Optional[str] = None


class DoctrinaCreate(DoctrinaBase):
    """Schema de creación para doctrina."""


class DoctrinaResponse(DoctrinaBase):
    """Schema de respuesta para doctrina."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
