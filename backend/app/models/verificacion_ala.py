"""
Modelos para el módulo ALA (Anti-Lavado de Activos).

Verificaciones de debida diligencia y metadata de listas consultadas.
"""

from sqlalchemy import Column, String, DateTime, Date, Boolean, Text, ForeignKey, Index, Integer
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc)


class VerificacionALA(Base):
    """
    Registro de una verificación ALA (debida diligencia).

    Almacena resultado de consultas a listas (PEP, ONU, OFAC, UE, GAFI),
    nivel de riesgo/diligencia y referencias opcionales a expediente/contrato.
    """
    __tablename__ = "verificaciones_ala"

    # Identificación
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

    # Datos de la persona/entidad verificada
    nombre_completo = Column(String(300), nullable=False)
    tipo_documento = Column(String(20), nullable=True)  # CI, RUT, PASAPORTE
    numero_documento = Column(String(50), nullable=True)
    nacionalidad = Column(String(3), nullable=True)  # Código ISO: UY, IR, KP
    fecha_nacimiento = Column(Date, nullable=True)
    es_persona_juridica = Column(Boolean, default=False)
    razon_social = Column(String(300), nullable=True)

    # Resultado de la verificación
    nivel_diligencia = Column(String(20), nullable=False)  # SIMPLIFICADA, NORMAL, INTENSIFICADA
    nivel_riesgo = Column(String(20), nullable=False)  # BAJO, MEDIO, ALTO, CRITICO
    es_pep = Column(Boolean, default=False)

    # Resultados por lista (JSONB)
    resultado_onu = Column(JSONB, nullable=True)
    resultado_pep = Column(JSONB, nullable=True)
    resultado_ofac = Column(JSONB, nullable=True)
    resultado_ue = Column(JSONB, nullable=True)
    resultado_gafi = Column(JSONB, nullable=True)

    # Búsquedas complementarias
    busqueda_google_realizada = Column(Boolean, default=False)
    busqueda_google_observaciones = Column(Text, nullable=True)
    busqueda_news_realizada = Column(Boolean, default=False)
    busqueda_news_observaciones = Column(Text, nullable=True)
    busqueda_wikipedia_realizada = Column(Boolean, default=False)
    busqueda_wikipedia_observaciones = Column(Text, nullable=True)

    # Trazabilidad del certificado
    hash_verificacion = Column(String(64), nullable=False)
    certificado_pdf_path = Column(String(500), nullable=True)

    # Relaciones con otras entidades
    expediente_id = Column(UUID(as_uuid=True), ForeignKey("expedientes.id"), nullable=True)
    contrato_id = Column(UUID(as_uuid=True), ForeignKey("contratos.id"), nullable=True)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Auditoría
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    # Índices
    __table_args__ = (
        Index("ix_verificaciones_ala_numero_documento", "numero_documento"),
        Index("ix_verificaciones_ala_nombre_completo", "nombre_completo"),
        Index("ix_verificaciones_ala_nivel_riesgo", "nivel_riesgo"),
        Index("ix_verificaciones_ala_expediente_id", "expediente_id"),
        Index("ix_verificaciones_ala_contrato_id", "contrato_id"),
        Index("ix_verificaciones_ala_usuario_id", "usuario_id"),
        Index("ix_verificaciones_ala_deleted_at", "deleted_at"),
    )

    # Relaciones ORM
    expediente = relationship("Expediente", backref="verificaciones_ala")
    contrato = relationship("Contrato", backref="verificaciones_ala")
    usuario = relationship("Usuario", backref="verificaciones_ala")

    def __repr__(self):
        return (
            f"<VerificacionALA(nombre='{self.nombre_completo[:30] if self.nombre_completo else ''}...', "
            f"riesgo={self.nivel_riesgo})>"
        )


class ListaALAMetadata(Base):
    """
    Metadata de descarga/actualización de listas ALA (ONU, PEP, OFAC, UE, GAFI).

    Registra última descarga, hash del contenido y estado para cache/auditoría.
    """
    __tablename__ = "listas_ala_metadata"

    # Identificación
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

    nombre_lista = Column(String(50), nullable=False)  # ONU, PEP, OFAC, UE, GAFI
    url_fuente = Column(String(500), nullable=True)
    ultima_descarga = Column(DateTime, nullable=True)
    hash_contenido = Column(String(64), nullable=True)
    cantidad_registros = Column(Integer, nullable=True)
    estado = Column(String(20), default="PENDIENTE")  # PENDIENTE, ACTUALIZADA, ERROR
    error_detalle = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utc_now)

    def __repr__(self):
        return f"<ListaALAMetadata(lista='{self.nombre_lista}', estado='{self.estado}')>"
