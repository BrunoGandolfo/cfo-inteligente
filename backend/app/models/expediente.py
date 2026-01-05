"""
Modelos para gestión de expedientes judiciales.

Integración con el Web Service del Poder Judicial de Uruguay.
WSDL: http://expedientes.poderjudicial.gub.uy/wsConsultaIUE.php?wsdl

Solo socios pueden gestionar expedientes.
"""

from sqlalchemy import Column, String, Boolean, DateTime, Date, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Tuple


def utc_now():
    return datetime.now(timezone.utc)


def parsear_iue(iue: str) -> Tuple[int, int, int]:
    """
    Parsea un IUE en sus componentes.
    
    Args:
        iue: String en formato "Sede-Numero/Año" (ej: "2-12345/2023")
        
    Returns:
        Tuple (sede, numero, año)
        
    Raises:
        ValueError: Si el formato es inválido
        
    Example:
        >>> parsear_iue("2-12345/2023")
        (2, 12345, 2023)
    """
    try:
        # Formato: "Sede-Numero/Año"
        sede_numero, anio = iue.split("/")
        sede, numero = sede_numero.split("-")
        return int(sede.strip()), int(numero.strip()), int(anio.strip())
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Formato de IUE inválido: '{iue}'. Esperado: 'Sede-Numero/Año'") from e


def generar_hash_movimiento(expediente_id: str, fecha: str, tipo: str, sede: str) -> str:
    """
    Genera un hash único para un movimiento para evitar duplicados.
    
    Args:
        expediente_id: UUID del expediente
        fecha: Fecha del movimiento (string)
        tipo: Tipo de movimiento
        sede: Sede del movimiento
        
    Returns:
        Hash SHA256 de 64 caracteres
    """
    contenido = f"{expediente_id}|{fecha}|{tipo}|{sede}"
    return hashlib.sha256(contenido.encode()).hexdigest()


class Expediente(Base):
    """
    Expediente judicial del Poder Judicial de Uruguay.
    
    Atributos principales:
    - iue: Identificador Único de Expediente (formato: "Sede-Numero/Año")
    - caratula: Título/descripción del caso
    - movimientos: Historial de movimientos procesales
    
    Relaciones opcionales:
    - cliente: Cliente asociado al expediente
    - area: Área de negocio (Jurídica, Notarial, etc.)
    - socio_responsable: Socio a cargo del caso
    """
    __tablename__ = "expedientes"

    # Identificación
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iue = Column(String(50), unique=True, nullable=False, index=True)  # "2-12345/2023"
    iue_sede = Column(Integer, nullable=False)      # 2
    iue_numero = Column(Integer, nullable=False)    # 12345
    iue_anio = Column(Integer, nullable=False)      # 2023
    
    # Datos del expediente (del Web Service)
    caratula = Column(String(500), nullable=True)
    origen = Column(String(200), nullable=True)
    abogado_actor = Column(String(200), nullable=True)
    abogado_demandado = Column(String(200), nullable=True)
    
    # Relaciones con entidades del sistema
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=True)
    area_id = Column(UUID(as_uuid=True), ForeignKey("areas.id"), nullable=True)
    socio_responsable_id = Column(UUID(as_uuid=True), ForeignKey("socios.id"), nullable=True)
    
    # Estado de sincronización
    ultimo_movimiento = Column(Date, nullable=True)
    cantidad_movimientos = Column(Integer, default=0)
    ultima_sincronizacion = Column(DateTime, nullable=True)
    
    # Control
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete
    
    # Relaciones
    movimientos = relationship(
        "ExpedienteMovimiento", 
        back_populates="expediente",
        cascade="all, delete-orphan",
        order_by="desc(ExpedienteMovimiento.fecha)"
    )
    cliente = relationship("Cliente", backref="expedientes")
    area = relationship("Area", backref="expedientes")
    socio_responsable = relationship("Socio", backref="expedientes_responsable")
    
    @classmethod
    def from_iue(cls, iue: str, **kwargs) -> "Expediente":
        """
        Crea un expediente parseando automáticamente el IUE.
        
        Example:
            >>> exp = Expediente.from_iue("2-12345/2023", caratula="CASO X")
        """
        sede, numero, anio = parsear_iue(iue)
        return cls(
            iue=iue,
            iue_sede=sede,
            iue_numero=numero,
            iue_anio=anio,
            **kwargs
        )
    
    def __repr__(self):
        return f"<Expediente(iue='{self.iue}', caratula='{self.caratula[:30] if self.caratula else ''}...')>"


class ExpedienteMovimiento(Base):
    """
    Movimiento procesal de un expediente.
    
    Cada movimiento representa un evento en el expediente judicial:
    - Presentaciones, notificaciones, decretos, audiencias, etc.
    
    El hash_movimiento previene duplicados durante la sincronización.
    """
    __tablename__ = "expedientes_movimientos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expediente_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("expedientes.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Datos del movimiento (del Web Service)
    fecha = Column(Date, nullable=False)
    tipo = Column(String(100), nullable=True)      # "Archivo", "NOTI", "OFAC", etc.
    decreto = Column(String(50), nullable=True)    # "586/2023"
    vencimiento = Column(Date, nullable=True)
    sede = Column(String(200), nullable=True)      # "Jdo.Ldo. Canelones 2º T"
    
    # Control de duplicados
    hash_movimiento = Column(String(64), unique=True, nullable=False, index=True)
    
    # Notificaciones
    notificado = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=utc_now)
    
    # Relación
    expediente = relationship("Expediente", back_populates="movimientos")
    
    @classmethod
    def crear_con_hash(
        cls, 
        expediente_id: str,
        fecha: str,
        tipo: str = None,
        decreto: str = None,
        vencimiento: str = None,
        sede: str = None
    ) -> "ExpedienteMovimiento":
        """
        Crea un movimiento generando automáticamente el hash.
        
        Args:
            expediente_id: UUID del expediente padre
            fecha: Fecha del movimiento (formato DD/MM/YYYY)
            tipo: Tipo de movimiento
            decreto: Número de decreto
            vencimiento: Fecha de vencimiento (formato DD/MM/YYYY)
            sede: Sede del juzgado
            
        Returns:
            Instancia de ExpedienteMovimiento con hash calculado
        """
        from datetime import datetime as dt
        
        # Parsear fecha
        fecha_obj = dt.strptime(fecha, "%d/%m/%Y").date() if fecha else None
        vencimiento_obj = dt.strptime(vencimiento, "%d/%m/%Y").date() if vencimiento else None
        
        # Generar hash único
        hash_mov = generar_hash_movimiento(str(expediente_id), fecha, tipo or "", sede or "")
        
        return cls(
            expediente_id=expediente_id,
            fecha=fecha_obj,
            tipo=tipo,
            decreto=decreto,
            vencimiento=vencimiento_obj,
            sede=sede,
            hash_movimiento=hash_mov
        )
    
    def __repr__(self):
        return f"<ExpedienteMovimiento(fecha='{self.fecha}', tipo='{self.tipo}')>"
