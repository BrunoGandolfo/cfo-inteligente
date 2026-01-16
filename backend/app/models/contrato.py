"""
Modelo para gestión de contratos y modelos notariales.

Almacena plantillas de contratos DOCX para el módulo notarial.
Incluye contenido binario del archivo y texto extraído para búsqueda.

Fuente inicial: estudionotarialmachado.com (133 modelos)
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text, Index, LargeBinary
from sqlalchemy.dialects.postgresql import UUID, JSON
from app.core.database import Base
import uuid
from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc)


class Contrato(Base):
    """
    Modelo/plantilla de contrato notarial.
    
    Almacena plantillas DOCX de contratos que pueden ser:
    - Descargados como archivo DOCX
    - Buscados por texto
    - Filtrados por categoría
    
    Categorías principales:
    - arrendamiento: Contratos de alquiler
    - automotores: Compraventa de vehículos
    - compraventa: Compraventa de inmuebles
    - donaciones: Donaciones con/sin reserva
    - fideicomiso: Fideicomisos de garantía
    - garantias: Prendas, fianzas
    - hipoteca: Hipotecas y cancelaciones
    - otros: Comodatos, permutas, etc.
    - particiones: División de bienes
    - poderes: Poderes generales y especiales
    - societario: Cesiones, contratos SRL
    - sucesiones: Testamentos, herencias
    """
    __tablename__ = "contratos"

    # Identificación
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Información básica
    titulo = Column(String(255), nullable=False)
    categoria = Column(String(100), nullable=False)  # arrendamiento, poderes, etc.
    subcategoria = Column(String(100), nullable=True)
    descripcion = Column(Text, nullable=True)  # Descripción breve del uso
    
    # Contenido del contrato
    contenido_docx = Column(LargeBinary, nullable=True)  # Archivo DOCX binario
    contenido_texto = Column(Text, nullable=True)  # Texto plano para búsqueda full-text
    
    # Metadata de campos editables
    # Formato: [{"nombre": "NOMBRE_COMPRADOR", "tipo": "texto", "descripcion": "..."}]
    campos_editables = Column(JSON, nullable=True)
    
    # Trazabilidad de origen
    fuente_original = Column(String(100), default="machado")  # machado, propio, otro
    archivo_original = Column(String(255), nullable=True)  # Nombre del archivo fuente
    
    # Estado
    activo = Column(Boolean, default=True)
    
    # Auditoría estándar del sistema
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete
    
    # Índices para búsqueda eficiente
    __table_args__ = (
        Index('idx_contrato_categoria', 'categoria'),
        Index('idx_contrato_titulo', 'titulo'),
        Index('idx_contrato_activo', 'activo', 'deleted_at'),
    )
    
    def __repr__(self):
        return f"<Contrato(titulo='{self.titulo[:40] if self.titulo else ''}...', categoria='{self.categoria}')>"
    
    @property
    def nombre_archivo(self) -> str:
        """Genera nombre de archivo seguro para descarga."""
        # Limpiar caracteres no válidos
        nombre = self.titulo.replace(" ", "_").replace("/", "-")
        return f"{nombre}.docx"
    
    @property
    def tiene_contenido(self) -> bool:
        """Verifica si el contrato tiene archivo DOCX cargado."""
        return self.contenido_docx is not None and len(self.contenido_docx) > 0
