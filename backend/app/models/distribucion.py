from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime

class DistribucionDetalle(Base):
    __tablename__ = "distribuciones_detalle"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operacion_id = Column(UUID(as_uuid=True), ForeignKey("operaciones.id"), nullable=False)
    socio_id = Column(UUID(as_uuid=True), ForeignKey("socios.id"), nullable=False)
    monto_uyu = Column(Numeric(15, 2), nullable=False)
    monto_usd = Column(Numeric(15, 2), nullable=False)
    porcentaje = Column(Numeric(5, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    operacion = relationship("Operacion", backref="distribuciones")
    socio = relationship("Socio", backref="distribuciones")
