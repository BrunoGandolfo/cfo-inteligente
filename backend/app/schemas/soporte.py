"""Schemas Pydantic para soporte, chat y streaming CFO."""

from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class MensajeHistorial(BaseModel):
    role: str
    content: str


class SoporteRequest(BaseModel):
    mensaje: str
    historial: Optional[List[Dict[str, str]]] = []
    es_socio: Optional[bool] = True


class SoporteResponse(BaseModel):
    respuesta: str


class PreguntaCFOStream(BaseModel):
    """Payload HTTP del chat CFO con soporte conversacional."""

    pregunta: str
    conversation_id: Optional[UUID] = None


class ExportPDFRequest(BaseModel):
    """Request body para exportar mensaje a PDF."""

    mensaje_id: str
    titulo: Optional[str] = None
    incluir_graficos: bool = True
