"""
Modelo para gestión de leyes uruguayas.

Almacena información de leyes del Parlamento de Uruguay e IMPO.
Integración con APIs públicas de legislación.
"""

from sqlalchemy import Column, String, DateTime, Date, Integer, Boolean, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import uuid
from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc)


class Ley(Base):
    """
    Ley del Parlamento de Uruguay.
    
    Almacena información básica de leyes y su contenido completo.
    Integración con IMPO para obtener texto completo.
    """
    __tablename__ = "leyes"

    # Identificación
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    numero = Column(Integer, nullable=False)
    anio = Column(Integer, nullable=False)
    
    # Información básica
    titulo = Column(Text, nullable=False)
    fecha_promulgacion = Column(Date, nullable=True)
    
    # URLs de origen
    url_parlamento = Column(String(500), nullable=True)
    url_impo = Column(String(500), nullable=True)
    
    # Contenido (se llena después con IMPO JSON)
    texto_completo = Column(Text, nullable=True)
    tiene_texto = Column(Boolean, default=False)
    
    # Metadata de referencias
    leyes_referenciadas = Column(Integer, default=0)  # Cuántas leyes referencian esta
    leyes_que_referencia = Column(Integer, default=0)  # Cuántas leyes referencia esta
    
    # Auditoría estándar del sistema
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete
    
    # Constraint único: no puede haber dos leyes con mismo número y año
    __table_args__ = (
        UniqueConstraint('numero', 'anio', name='uq_ley_numero_anio'),
    )
    
    def __repr__(self):
        return f"<Ley(numero={self.numero}, anio={self.anio}, titulo='{self.titulo[:30] if self.titulo else ''}...')>"

