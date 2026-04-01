from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from uuid import UUID


class MensajeBase(BaseModel):
    """Campos base de un mensaje en conversación CFO."""
    rol: str
    contenido: str


class MensajeCreate(MensajeBase):
    """Schema para crear un mensaje (incluye SQL generado opcionalmente)."""
    sql_generado: Optional[str] = None


class MensajeResponse(MensajeBase):
    """Schema de respuesta para un mensaje."""
    id: UUID
    conversacion_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ConversacionBase(BaseModel):
    """Campos base de una conversación CFO."""
    titulo: Optional[str] = None


class ConversacionCreate(ConversacionBase):
    """Schema para crear una conversación."""
    pass


class ConversacionResponse(ConversacionBase):
    """Schema de respuesta completa para una conversación con mensajes."""
    id: UUID
    usuario_id: UUID
    created_at: datetime
    updated_at: datetime
    mensajes: List[MensajeResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ConversacionListResponse(BaseModel):
    """Schema de respuesta para listado de conversaciones (sin mensajes)."""
    id: UUID
    titulo: Optional[str] = None
    updated_at: datetime
    cantidad_mensajes: int

    class Config:
        from_attributes = True

