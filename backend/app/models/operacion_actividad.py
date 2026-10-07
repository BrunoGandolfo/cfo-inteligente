"""
Modelo OperacionActividad — registro de quién crea, edita o anula operaciones.

Libro de actas append-only: cada acción agrega una fila y ninguna fila se
modifica ni se borra. Por eso no tiene deleted_at: ocultar una entrada
anularía el propósito de auditoría.
"""

import enum

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base, utc_now


class AccionActividad(enum.Enum):
    CREAR = "CREAR"
    EDITAR = "EDITAR"
    ANULAR = "ANULAR"


class OperacionActividad(Base):
    """Una acción de un usuario sobre una operación."""

    __tablename__ = "operaciones_actividad"
    __table_args__ = (
        CheckConstraint(
            "accion IN ('CREAR', 'EDITAR', 'ANULAR')",
            name="ck_operaciones_actividad_accion",
        ),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    operacion_id = Column(
        UUID(as_uuid=True), ForeignKey("operaciones.id"), nullable=False, index=True,
    )
    usuario_id = Column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False, index=True,
    )
    accion = Column(String(20), nullable=False)
    # timestamptz: el resumen diario corta los días en hora de Uruguay
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)

    operacion = relationship("Operacion", foreign_keys=[operacion_id])
    usuario = relationship("Usuario", foreign_keys=[usuario_id])
