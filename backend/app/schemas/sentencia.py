"""Schemas Pydantic para el módulo de Jurisprudencia."""

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SentenciaBase(BaseModel):
    """Campos base de una sentencia."""

    bjn_id: Optional[str] = None
    numero: Optional[str] = None
    sede: Optional[str] = None
    fecha: Optional[date] = None
    tipo: Optional[str] = None
    importancia: Optional[str] = None
    materias: Optional[List[str]] = None
    firmantes: Optional[List[str]] = None
    abstract: Optional[str] = None
    descriptores: Optional[List[str]] = None


class SentenciaResumen(SentenciaBase):
    """Sentencia sin texto completo — para listados."""

    id: UUID
    tiene_resumen_ia: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SentenciaCompleta(SentenciaBase):
    """Sentencia con texto completo y resumen IA."""

    id: UUID
    texto_completo: Optional[str] = None
    resumen_ia: Optional[str] = None
    resumen_generado_at: Optional[datetime] = None
    query_origen: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SentenciaListResponse(BaseModel):
    """Respuesta paginada de sentencias."""

    total: int
    sentencias: List[SentenciaResumen]
    limit: int
    offset: int


class BusquedaResponse(BaseModel):
    """Respuesta de búsqueda de sentencias."""

    total: int
    sentencias: List[SentenciaResumen]
    query: str
    limit: int
    offset: int
