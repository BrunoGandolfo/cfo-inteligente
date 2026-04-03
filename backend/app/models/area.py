"""Modelo de áreas de negocio del estudio (Jurídica, Notarial, Contable, etc.)."""

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base, utc_now
import uuid

class Area(Base):
    """Área funcional del estudio. Cada operación y expediente se asocia a un área."""

    __tablename__ = "areas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(String(255))
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
