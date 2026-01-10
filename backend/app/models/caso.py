"""
Modelos para gestión de casos legales.
"""

from sqlalchemy import Column, String, DateTime, Date, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
import enum
from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc)


class EstadoCaso(enum.Enum):
    PENDIENTE = "pendiente"
    EN_PROCESO = "en_proceso"
    REQUIERE_ACCION = "requiere_accion"
    CERRADO = "cerrado"


class PrioridadCaso(enum.Enum):
    CRITICA = "critica"
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


class Caso(Base):
    """
    Caso legal para gestión y seguimiento.
    
    Atributos principales:
    - titulo: Título/descripción del caso
    - estado: Estado actual del caso (pendiente, en_proceso, requiere_accion, cerrado)
    - prioridad: Nivel de prioridad (critica, alta, media, baja)
    - fecha_vencimiento: Fecha límite para acciones requeridas
    
    Relaciones:
    - responsable: Usuario responsable del caso
    - expediente: Expediente judicial asociado (opcional)
    """
    __tablename__ = "casos"

    # Identificación
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Datos del caso
    titulo = Column(String(300), nullable=False)
    estado = Column(Enum(EstadoCaso), nullable=False, default=EstadoCaso.PENDIENTE)
    prioridad = Column(Enum(PrioridadCaso), nullable=False, default=PrioridadCaso.MEDIA)
    fecha_vencimiento = Column(Date, nullable=True)
    
    # Relaciones
    responsable_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    expediente_id = Column(UUID(as_uuid=True), ForeignKey("expedientes.id"), nullable=True)
    
    # Control
    deleted_at = Column(DateTime, nullable=True)  # Soft delete
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    
    # Relaciones ORM
    responsable = relationship("Usuario", backref="casos")
    expediente = relationship("Expediente", backref="casos")
    
    def __repr__(self):
        return f"<Caso(titulo='{self.titulo[:30] if self.titulo else ''}...', estado='{self.estado.value if self.estado else ''}')>"
