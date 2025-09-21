from sqlalchemy import Column, String, DateTime, Numeric, Date, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime
import enum

class TipoOperacion(enum.Enum):
    INGRESO = "ingreso"
    GASTO = "gasto"
    RETIRO = "retiro"
    DISTRIBUCION = "distribucion"

class Moneda(enum.Enum):
    UYU = "UYU"
    USD = "USD"

class Localidad(enum.Enum):
    MONTEVIDEO = "Montevideo"
    MERCEDES = "Mercedes"

class Operacion(Base):
    __tablename__ = "operaciones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo_operacion = Column(Enum(TipoOperacion), nullable=False)
    fecha = Column(Date, nullable=False)
    monto_original = Column(Numeric(15, 2), nullable=False)
    moneda_original = Column(Enum(Moneda), nullable=False)
    tipo_cambio = Column(Numeric(10, 4), nullable=False)
    monto_uyu = Column(Numeric(15, 2), nullable=False)
    monto_usd = Column(Numeric(15, 2), nullable=False)
    area_id = Column(UUID(as_uuid=True), ForeignKey("areas.id"), nullable=False)
    localidad = Column(Enum(Localidad), nullable=False)
    descripcion = Column(String(500))
    cliente = Column(String(200))
    proveedor = Column(String(200))
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    area = relationship("Area", backref="operaciones")
