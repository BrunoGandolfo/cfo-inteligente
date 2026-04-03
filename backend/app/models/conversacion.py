"""Modelos de conversaciones y mensajes del chat CFO."""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base, utc_now
import uuid

class Conversacion(Base):
    """Hilo de conversación de un usuario con el asistente CFO."""

    __tablename__ = "conversaciones"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    titulo = Column(String(200), nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relaciones
    usuario = relationship("Usuario", back_populates="conversaciones")
    mensajes = relationship("Mensaje", back_populates="conversacion", cascade="all, delete-orphan", order_by="Mensaje.created_at")

class Mensaje(Base):
    """Mensaje individual dentro de una conversación (rol: user o assistant)."""

    __tablename__ = "mensajes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversacion_id = Column(UUID(as_uuid=True), ForeignKey("conversaciones.id", ondelete="CASCADE"), nullable=False)
    rol = Column(String(20), nullable=False)  # 'user' o 'assistant'
    contenido = Column(Text, nullable=False)
    sql_generado = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    
    # Relaciones
    conversacion = relationship("Conversacion", back_populates="mensajes")
