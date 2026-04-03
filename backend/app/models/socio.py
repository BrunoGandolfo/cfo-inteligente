"""Modelo de socios del estudio con porcentaje de participación societaria."""

from sqlalchemy import Column, String, Boolean, DateTime, Numeric
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base, utc_now
import uuid

class Socio(Base):
    """Socio del estudio. Define participación porcentual para distribuciones."""

    __tablename__ = "socios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(100), nullable=False, unique=True)
    porcentaje_participacion = Column(Numeric(5, 2), nullable=False)  # Ej: 20.00
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
