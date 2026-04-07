"""
Modelo TramiteDgr — trámites registrales de la DGR (Dirección General de Registros).

Almacena estado y seguimiento de documentos ingresados en la DGR por escribanos.
"""
import uuid

from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Index, Integer,
    String, Text, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base, utc_now


class TramiteDgr(Base):
    __tablename__ = "tramites_dgr"

    # PK
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Identificación del trámite (campos del formulario DGR)
    registro = Column(String(10), nullable=False)
    registro_nombre = Column(String(200), nullable=True)
    oficina = Column(String(5), nullable=False)
    oficina_nombre = Column(String(100), nullable=True)
    anio = Column(Integer, nullable=False)
    numero_entrada = Column(Integer, nullable=False)
    bis = Column(String(10), default="")

    # Datos obtenidos de la DGR
    fecha_ingreso = Column(Date, nullable=True)
    escribano_emisor = Column(String(300), nullable=True)
    estado_actual = Column(String(50), nullable=True)
    actos = Column(Text, nullable=True)
    observaciones = Column(Text, nullable=True)
    fecha_vencimiento = Column(Date, nullable=True)

    # Monitoreo
    ultimo_chequeo = Column(DateTime(timezone=True), nullable=True)
    estado_anterior = Column(String(50), nullable=True)
    cambio_detectado = Column(Boolean, default=False)
    activo = Column(Boolean, default=True)

    # Relaciones
    responsable_id = Column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False,
    )

    # Auditoría
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=utc_now,
        nullable=False,
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Constraints e índices
    __table_args__ = (
        UniqueConstraint(
            "registro", "oficina", "anio", "numero_entrada", "bis",
            name="uq_tramite_dgr_identificacion",
        ),
        Index("ix_tramites_dgr_responsable", "responsable_id"),
        Index("ix_tramites_dgr_activo", "activo", "deleted_at"),
    )

    def __repr__(self):
        return f"<TramiteDgr {self.registro}-{self.oficina} {self.anio}/{self.numero_entrada}>"
