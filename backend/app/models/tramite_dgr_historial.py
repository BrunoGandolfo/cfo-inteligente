"""
Modelo TramiteDgrHistorial — historial de cambios detectados en trámites DGR.

Registra cada cambio relevante detectado por el scheduler para auditoría.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


def utc_now():
    """Retorna datetime actual en UTC para defaults de auditoría."""
    return datetime.now(timezone.utc)


class TramiteDgrHistorial(Base):
    __tablename__ = "tramites_dgr_historial"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tramite_dgr_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tramites_dgr.id"),
        nullable=False,
    )
    campo_modificado = Column(String(100), nullable=False)
    valor_anterior = Column(Text, nullable=True)
    valor_nuevo = Column(Text, nullable=True)
    detectado_en = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    tramite = relationship("TramiteDgr", backref="historial_cambios")

    def __repr__(self):
        return f"<TramiteDgrHistorial {self.tramite_dgr_id} {self.campo_modificado}>"
