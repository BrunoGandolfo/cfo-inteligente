"""
Modelo Sentencia — Jurisprudencia del Poder Judicial de Uruguay.

Almacena sentencias extraídas de la Base de Jurisprudencia Nacional (BJN).
Incluye texto completo y resumen generado por IA (Ollama local).
"""
import uuid

from sqlalchemy import (
    Column, String, Date, Text, DateTime, Integer,
    Index, text
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from app.core.database import Base, utc_now


class Sentencia(Base):
    __tablename__ = "sentencias"

    # PK
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Identificación BJN
    bjn_id = Column(String(50), unique=True, nullable=True, index=True)
    numero = Column(String(100), nullable=True)
    sede = Column(String(200), nullable=True)
    fecha = Column(Date, nullable=True, index=True)
    tipo = Column(String(100), nullable=True)
    importancia = Column(String(50), nullable=True)

    # Clasificación
    materias = Column(ARRAY(Text), nullable=True)
    firmantes = Column(ARRAY(Text), nullable=True)
    abstract = Column(Text, nullable=True)
    descriptores = Column(ARRAY(Text), nullable=True)

    # Contenido
    texto_completo = Column(Text, nullable=True)

    # IA local (Ollama)
    resumen_ia = Column(Text, nullable=True)
    resumen_generado_at = Column(DateTime, nullable=True)

    # Trazabilidad de scraping
    query_origen = Column(String(500), nullable=True)

    # Auditoría
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Índices
    __table_args__ = (
        Index("idx_sentencias_materias", materias, postgresql_using="gin"),
        Index(
            "idx_sentencias_texto_completo",
            text("to_tsvector('spanish', coalesce(texto_completo, ''))"),
            postgresql_using="gin",
        ),
    )

    def __repr__(self):
        return f"<Sentencia {self.numero} - {self.sede}>"
