"""
Servicio para consulta y sincronización de expedientes judiciales.

Integración con el Web Service del Poder Judicial de Uruguay.
WSDL: http://expedientes.poderjudicial.gub.uy/wsConsultaIUE.php?wsdl

Solo socios pueden gestionar expedientes.
"""

import logging
import json
from datetime import datetime, timezone
from typing import Optional, Dict, List, Tuple, Any

from zeep import Client, Settings
from zeep.helpers import serialize_object
from zeep.exceptions import Fault, TransportError
from sqlalchemy.orm import Session

from app.models.expediente import (
    Expediente, 
    ExpedienteMovimiento, 
    parsear_iue, 
    generar_hash_movimiento
)

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

WSDL_URL = "http://expedientes.poderjudicial.gub.uy/wsConsultaIUE.php?wsdl"
TIMEOUT_SEGUNDOS = 15

# Estados conocidos del Web Service
ESTADO_NO_ENCONTRADO = "EL EXPEDIENTE NO SE ENCUENTRA EN EL SISTEMA"
ESTADO_DATOS_EXPEDIENTE = "DATOS DEL EXPEDIENTE"

# ============================================================================
# CACHE DEL CLIENTE SOAP
# ============================================================================

_soap_client: Optional[Client] = None


def _obtener_cliente_soap() -> Client:
    """
    Obtiene el cliente SOAP, creándolo si no existe.
    El cliente se cachea para reutilizar la conexión.
    """
    global _soap_client
    
    if _soap_client is None:
        logger.info(f"Inicializando cliente SOAP: {WSDL_URL}")
        settings = Settings(
            strict=False,
            xml_huge_tree=True
        )
        _soap_client = Client(WSDL_URL, settings=settings)
        logger.info("Cliente SOAP inicializado correctamente")
    
    return _soap_client


def _resetear_cliente_soap():
    """Resetea el cliente SOAP (útil si hay errores de conexión)."""
    global _soap_client
    _soap_client = None
    logger.info("Cliente SOAP reseteado")


# ============================================================================
# CONSULTA AL WEB SERVICE
# ============================================================================

def consultar_expediente_ws(iue: str) -> Optional[Dict[str, Any]]:
    """
    Consulta un expediente en el Web Service del Poder Judicial.
    
    Args:
        iue: Identificador Único de Expediente (formato: "Sede-Numero/Año")
        
    Returns:
        Dict con datos del expediente si existe, None si no se encuentra.
        Estructura:
        {
            "estado": str,
            "origen": str | None,
            "expediente": str | None,
            "caratula": str | None,
            "abogado_actor": str | None,
            "abogado_demandante": str | None,
            "movimientos": List[Dict] | None
        }
        
    Raises:
        ConnectionError: Si no se puede conectar al servicio
        TimeoutError: Si la consulta excede el timeout
        ValueError: Si el formato del IUE es inválido
    """
    # Validar formato IUE
    try:
        parsear_iue(iue)
    except ValueError as e:
        logger.error(f"Formato de IUE inválido: {iue}")
        raise
    
    logger.info(f"Consultando expediente: {iue}")
    
    try:
        client = _obtener_cliente_soap()
        
        # Llamar al método del Web Service
        resultado = client.service.consultaIUE(iue)
        
        # Serializar respuesta a dict
        data = serialize_object(resultado)
        
        # Si es string JSON, parsearlo
        if isinstance(data, str):
            data = json.loads(data)
        
        estado = data.get("estado", "")
        
        # Verificar si el expediente existe
        if ESTADO_NO_ENCONTRADO in estado.upper():
            logger.info(f"Expediente no encontrado: {iue}")
            return None
        
        logger.info(f"Expediente encontrado: {iue} - Estado: {estado}")
        return data
        
    except TransportError as e:
        logger.error(f"Error de conexión al WS Poder Judicial: {e}")
        _resetear_cliente_soap()
        raise ConnectionError(f"No se pudo conectar al Poder Judicial: {e}") from e
        
    except Fault as e:
        logger.error(f"Error SOAP: {e}")
        raise ConnectionError(f"Error en el servicio SOAP: {e}") from e
        
    except Exception as e:
        logger.error(f"Error inesperado consultando expediente {iue}: {e}")
        _resetear_cliente_soap()
        raise


# ============================================================================
# SINCRONIZACIÓN CON BASE DE DATOS
# ============================================================================

def _parsear_fecha(fecha_str: str) -> Optional[datetime]:
    """Parsea fecha del WS (formato DD/MM/YYYY) a datetime."""
    if not fecha_str:
        return None
    try:
        return datetime.strptime(fecha_str, "%d/%m/%Y").date()
    except ValueError:
        logger.warning(f"Formato de fecha inválido: {fecha_str}")
        return None


def sincronizar_expediente(
    db: Session, 
    iue: str,
    cliente_id: Optional[str] = None,
    area_id: Optional[str] = None,
    socio_responsable_id: Optional[str] = None
) -> Tuple[Optional[Expediente], int]:
    """
    Sincroniza un expediente con el Web Service del Poder Judicial.
    
    Si el expediente no existe en BD, lo crea.
    Si existe, actualiza sus datos y agrega nuevos movimientos.
    
    Args:
        db: Sesión de SQLAlchemy
        iue: Identificador Único de Expediente
        cliente_id: UUID del cliente asociado (opcional)
        area_id: UUID del área (opcional)
        socio_responsable_id: UUID del socio responsable (opcional)
        
    Returns:
        Tupla (expediente, cantidad_nuevos_movimientos)
        Si el expediente no existe en el WS, retorna (None, 0)
        
    Raises:
        ConnectionError: Si no se puede conectar al WS
    """
    # Consultar Web Service
    datos_ws = consultar_expediente_ws(iue)
    
    if datos_ws is None:
        logger.info(f"Expediente {iue} no existe en el Poder Judicial")
        return None, 0
    
    # Parsear IUE
    sede, numero, anio = parsear_iue(iue)
    
    # Buscar expediente existente en BD
    expediente = db.query(Expediente).filter(
        Expediente.iue == iue,
        Expediente.deleted_at.is_(None)
    ).first()
    
    ahora = datetime.now(timezone.utc)
    
    if expediente is None:
        # Crear nuevo expediente
        logger.info(f"Creando expediente: {iue}")
        expediente = Expediente(
            iue=iue,
            iue_sede=sede,
            iue_numero=numero,
            iue_anio=anio,
            caratula=datos_ws.get("caratula"),
            origen=datos_ws.get("origen"),
            abogado_actor=datos_ws.get("abogado_actor"),
            abogado_demandado=datos_ws.get("abogado_demandante"),  # Nota: el WS usa "demandante"
            cliente_id=cliente_id,
            area_id=area_id,
            socio_responsable_id=socio_responsable_id,
            ultima_sincronizacion=ahora
        )
        db.add(expediente)
        db.flush()  # Para obtener el ID
    else:
        # Actualizar datos básicos
        logger.info(f"Actualizando expediente: {iue}")
        expediente.caratula = datos_ws.get("caratula") or expediente.caratula
        expediente.origen = datos_ws.get("origen") or expediente.origen
        expediente.abogado_actor = datos_ws.get("abogado_actor") or expediente.abogado_actor
        expediente.abogado_demandado = datos_ws.get("abogado_demandante") or expediente.abogado_demandado
        expediente.ultima_sincronizacion = ahora
        
        # Actualizar relaciones solo si se proporcionan
        if cliente_id:
            expediente.cliente_id = cliente_id
        if area_id:
            expediente.area_id = area_id
        if socio_responsable_id:
            expediente.socio_responsable_id = socio_responsable_id
    
    # Sincronizar movimientos
    movimientos_ws = datos_ws.get("movimientos") or []
    nuevos_movimientos = 0
    fecha_ultimo = None
    
    for mov in movimientos_ws:
        fecha_str = mov.get("fecha", "")
        tipo = mov.get("tipo", "")
        sede_mov = mov.get("sede", "")
        
        # Generar hash único para este movimiento
        hash_mov = generar_hash_movimiento(
            str(expediente.id),
            fecha_str,
            tipo,
            sede_mov
        )
        
        # Verificar si ya existe
        existe = db.query(ExpedienteMovimiento).filter(
            ExpedienteMovimiento.hash_movimiento == hash_mov
        ).first()
        
        if existe:
            continue
        
        # Crear nuevo movimiento
        fecha_mov = _parsear_fecha(fecha_str)
        vencimiento_mov = _parsear_fecha(mov.get("vencimiento", ""))
        
        nuevo_mov = ExpedienteMovimiento(
            expediente_id=expediente.id,
            fecha=fecha_mov,
            tipo=tipo,
            decreto=mov.get("decreto"),
            vencimiento=vencimiento_mov,
            sede=sede_mov,
            hash_movimiento=hash_mov,
            notificado=False  # Nuevo = sin notificar
        )
        db.add(nuevo_mov)
        nuevos_movimientos += 1
        
        # Trackear fecha más reciente
        if fecha_mov and (fecha_ultimo is None or fecha_mov > fecha_ultimo):
            fecha_ultimo = fecha_mov
    
    # Actualizar estadísticas del expediente
    total_movimientos = db.query(ExpedienteMovimiento).filter(
        ExpedienteMovimiento.expediente_id == expediente.id
    ).count() + nuevos_movimientos
    
    expediente.cantidad_movimientos = total_movimientos
    
    if fecha_ultimo:
        expediente.ultimo_movimiento = fecha_ultimo
    
    db.commit()
    
    logger.info(
        f"Sincronización completada: {iue} - "
        f"{nuevos_movimientos} nuevos movimientos, "
        f"{total_movimientos} total"
    )
    
    return expediente, nuevos_movimientos


# ============================================================================
# CONSULTAS DE NOTIFICACIONES
# ============================================================================

def obtener_movimientos_sin_notificar(db: Session) -> List[Dict[str, Any]]:
    """
    Obtiene todos los movimientos pendientes de notificación.
    
    Args:
        db: Sesión de SQLAlchemy
        
    Returns:
        Lista de dicts con datos del movimiento y su expediente:
        [
            {
                "movimiento_id": str,
                "expediente_id": str,
                "iue": str,
                "caratula": str,
                "fecha": date,
                "tipo": str,
                "decreto": str,
                "vencimiento": date | None,
                "sede": str,
                "socio_responsable_id": str | None
            }
        ]
    """
    resultados = db.query(
        ExpedienteMovimiento,
        Expediente
    ).join(
        Expediente,
        ExpedienteMovimiento.expediente_id == Expediente.id
    ).filter(
        ExpedienteMovimiento.notificado == False,
        Expediente.activo == True,
        Expediente.deleted_at.is_(None)
    ).order_by(
        ExpedienteMovimiento.fecha.desc()
    ).all()
    
    movimientos = []
    for mov, exp in resultados:
        movimientos.append({
            "movimiento_id": str(mov.id),
            "expediente_id": str(exp.id),
            "iue": exp.iue,
            "caratula": exp.caratula,
            "fecha": mov.fecha,
            "tipo": mov.tipo,
            "decreto": mov.decreto,
            "vencimiento": mov.vencimiento,
            "sede": mov.sede,
            "socio_responsable_id": str(exp.socio_responsable_id) if exp.socio_responsable_id else None
        })
    
    logger.info(f"Movimientos sin notificar: {len(movimientos)}")
    return movimientos


def marcar_movimientos_notificados(
    db: Session, 
    movimiento_ids: List[str]
) -> int:
    """
    Marca movimientos como notificados.
    
    Args:
        db: Sesión de SQLAlchemy
        movimiento_ids: Lista de UUIDs de movimientos
        
    Returns:
        Cantidad de movimientos actualizados
    """
    if not movimiento_ids:
        return 0
    
    from uuid import UUID
    
    actualizados = db.query(ExpedienteMovimiento).filter(
        ExpedienteMovimiento.id.in_([UUID(mid) for mid in movimiento_ids])
    ).update(
        {ExpedienteMovimiento.notificado: True},
        synchronize_session=False
    )
    
    db.commit()
    logger.info(f"Movimientos marcados como notificados: {actualizados}")
    
    return actualizados


# ============================================================================
# UTILIDADES
# ============================================================================

def obtener_expediente_por_iue(
    db: Session, 
    iue: str, 
    incluir_eliminados: bool = False
) -> Optional[Expediente]:
    """
    Obtiene un expediente de la BD por su IUE.
    
    Args:
        db: Sesión de SQLAlchemy
        iue: Identificador Único de Expediente
        incluir_eliminados: Si True, incluye expedientes con soft delete
        
    Returns:
        Expediente o None si no existe
    """
    query = db.query(Expediente).filter(Expediente.iue == iue)
    
    if not incluir_eliminados:
        query = query.filter(Expediente.deleted_at.is_(None))
    
    return query.first()


def listar_expedientes_activos(
    db: Session,
    socio_responsable_id: Optional[str] = None,
    area_id: Optional[str] = None,
    anio: Optional[int] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Expediente]:
    """
    Lista expedientes activos con filtros opcionales.
    
    Args:
        db: Sesión de SQLAlchemy
        socio_responsable_id: Filtrar por socio responsable
        area_id: Filtrar por área
        anio: Filtrar por año del IUE
        limit: Máximo de resultados
        offset: Desplazamiento para paginación
        
    Returns:
        Lista de Expedientes
    """
    from uuid import UUID
    
    query = db.query(Expediente).filter(
        Expediente.activo == True,
        Expediente.deleted_at.is_(None)
    )
    
    if socio_responsable_id:
        query = query.filter(Expediente.socio_responsable_id == UUID(socio_responsable_id))
    
    if area_id:
        query = query.filter(Expediente.area_id == UUID(area_id))
    
    if anio:
        query = query.filter(Expediente.iue_anio == anio)
    
    return query.order_by(
        Expediente.ultimo_movimiento.desc().nullslast()
    ).offset(offset).limit(limit).all()
