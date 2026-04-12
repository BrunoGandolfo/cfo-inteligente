import uuid

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Norma(Base):
    __tablename__ = "normas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo_norma = Column(String(50), nullable=False)
    numero = Column(Integer, nullable=False)
    anio = Column(Integer, nullable=False)
    nombre = Column(Text, nullable=True)
    fecha_promulgacion = Column(Date, nullable=True)
    fecha_publicacion = Column(Date, nullable=True)
    indexacion = Column(Text, nullable=True)
    vistos = Column(Text, nullable=True)
    referencias_norma = Column(Text, nullable=True)
    url_impo = Column(String(500), nullable=True)
    json_original = Column(JSON, nullable=True)
    descarga_estado = Column(String(20), default="pending")
    descarga_error = Column(Text, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    articulos = relationship(
        "NormaArticulo",
        back_populates="norma",
        cascade="all, delete-orphan",
    )
    relaciones_origen = relationship(
        "NormaRelacion",
        foreign_keys="NormaRelacion.norma_origen_id",
        back_populates="norma_origen",
    )
    relaciones_destino = relationship(
        "NormaRelacion",
        foreign_keys="NormaRelacion.norma_destino_id",
        back_populates="norma_destino",
    )

    __table_args__ = (
        UniqueConstraint("tipo_norma", "numero", "anio", name="uq_norma_tipo_numero_anio"),
        Index("ix_normas_tipo_numero_anio", "tipo_norma", "numero", "anio"),
        Index("ix_normas_nombre", "nombre"),
        Index("ix_normas_descarga_estado", "descarga_estado"),
    )


class NormaArticulo(Base):
    __tablename__ = "normas_articulos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    norma_id = Column(
        UUID(as_uuid=True),
        ForeignKey("normas.id", ondelete="CASCADE"),
        nullable=False,
    )
    numero_articulo = Column(String(20), nullable=False)
    titulo = Column(Text, nullable=True)
    texto = Column(Text, nullable=True)
    notas = Column(Text, nullable=True)
    referencias = Column(Text, nullable=True)
    indexacion = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    norma = relationship("Norma", back_populates="articulos")

    __table_args__ = (Index("ix_normas_articulos_norma_id", "norma_id"),)


class NormaRelacion(Base):
    __tablename__ = "normas_relaciones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    norma_origen_id = Column(
        UUID(as_uuid=True),
        ForeignKey("normas.id"),
        nullable=True,
    )
    norma_destino_id = Column(
        UUID(as_uuid=True),
        ForeignKey("normas.id"),
        nullable=True,
    )
    tipo_relacion = Column(String(50), nullable=False)
    articulo_origen = Column(String(50), nullable=True)
    articulo_destino = Column(String(50), nullable=True)
    texto_original = Column(Text, nullable=True)
    norma_destino_ref = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=func.now())

    norma_origen = relationship(
        "Norma",
        foreign_keys=[norma_origen_id],
        back_populates="relaciones_origen",
    )
    norma_destino = relationship(
        "Norma",
        foreign_keys=[norma_destino_id],
        back_populates="relaciones_destino",
    )

    __table_args__ = (
        Index("ix_normas_relaciones_origen", "norma_origen_id"),
        Index("ix_normas_relaciones_destino", "norma_destino_id"),
        Index("ix_normas_relaciones_tipo", "tipo_relacion"),
    )
