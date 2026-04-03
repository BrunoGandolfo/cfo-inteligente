"""Modelo de clientes del estudio, vinculados a operaciones y expedientes."""

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base, utc_now
import uuid

class Cliente(Base):
    """Cliente del estudio. Nombre normalizado a mayúsculas, único."""

    __tablename__ = "clientes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(200), nullable=False, unique=True)
    telefono = Column(String(50), nullable=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
