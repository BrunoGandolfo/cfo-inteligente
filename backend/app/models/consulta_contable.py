"""
Modelo ConsultaContable — registro de consultas DGI realizadas por el área
contable. Trazabilidad de quién consultó qué servicio, con qué datos y qué
resultado obtuvo.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base, utc_now


class ConsultaContable(Base):
    __tablename__ = "consultas_contables"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # Quién consultó
    usuario_id = Column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False,
    )

    # Qué servicio se usó
    # CERTIFICADO_UNICO, DECLARACION_IRPF, AFILIACION_BANCARIA, BORRADORES_IASS,
    # EXONERACION_ARRENDAMIENTOS, ESTADO_TRAMITE, EXPEDIENTE_ADMINISTRATIVO,
    # DEVOLUCION_IVA_GASOIL, CONSTANCIA_PRIMARIA, RESIDENCIA_FISCAL
    servicio = Column(String(50), nullable=False)

    # Datos de entrada
    rut = Column(String(20), nullable=True)
    ci = Column(String(20), nullable=True)
    datos_entrada = Column(JSONB, nullable=True)

    # Resultado
    exitosa = Column(Boolean, default=False, nullable=False)
    resultado_texto = Column(Text, nullable=True)
    resultado_datos = Column(JSONB, nullable=True)
    error = Column(Text, nullable=True)

    # Cliente asociado (opcional, denormalizado)
    cliente_nombre = Column(String(200), nullable=True)
    cliente_rut = Column(String(20), nullable=True)

    # Auditoría
    created_at = Column(DateTime, default=utc_now, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_consultas_contables_usuario_id", "usuario_id"),
        Index("ix_consultas_contables_servicio", "servicio"),
        Index("ix_consultas_contables_rut", "rut"),
        Index("ix_consultas_contables_ci", "ci"),
        Index("ix_consultas_contables_created_at", "created_at"),
        Index("ix_consultas_contables_deleted_at", "deleted_at"),
    )

    usuario = relationship("Usuario", backref="consultas_contables")

    def __repr__(self):
        return (
            f"<ConsultaContable servicio={self.servicio} "
            f"rut={self.rut} exitosa={self.exitosa}>"
        )
