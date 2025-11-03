from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from uuid import UUID

class MensajeBase(BaseModel):
    rol: str
    contenido: str

class MensajeCreate(MensajeBase):
    sql_generado: Optional[str] = None

class MensajeResponse(MensajeBase):
    id: UUID
    conversacion_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class ConversacionBase(BaseModel):
    titulo: Optional[str] = None

class ConversacionCreate(ConversacionBase):
    pass

class ConversacionResponse(ConversacionBase):
    id: UUID
    usuario_id: UUID
    created_at: datetime
    updated_at: datetime
    mensajes: List[MensajeResponse] = []
    
    class Config:
        from_attributes = True

class ConversacionListResponse(BaseModel):
    id: UUID
    titulo: Optional[str]
    updated_at: datetime
    cantidad_mensajes: int
    
    class Config:
        from_attributes = True

