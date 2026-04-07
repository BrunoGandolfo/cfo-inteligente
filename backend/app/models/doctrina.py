"""
Modelo Doctrina — artículos doctrinarios de revistas jurídicas uruguayas.

Almacena metadata OAI-PMH y contenido enriquecido a partir de PDF/texto.
"""
import uuid

from sqlalchemy import Column, Date, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from app.core.database import Base, utc_now


class Doctrina(Base):
    __tablename__ = "doctrina"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    oai_identifier = Column(String(300), unique=True, nullable=False, index=True)
    titulo = Column(Text, nullable=False)
    autor = Column(String(500), nullable=True)
    fecha_publicacion = Column(Date, nullable=True)
    fuente = Column(String(100), nullable=False)
    revista = Column(String(200), nullable=True)
    url_articulo = Column(String(500), nullable=True)
    url_pdf = Column(String(500), nullable=True)
    abstract = Column(Text, nullable=True)
    texto_completo = Column(Text, nullable=True)
    materias = Column(ARRAY(String), nullable=True)
    idioma = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=utc_now,
        nullable=False,
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Doctrina {self.fuente} - {self.titulo[:50]}>"
