"""
API para gestión de expedientes judiciales.

Integración con el Web Service del Poder Judicial de Uruguay.
Solo SOCIOS pueden acceder a estos endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date, timezone
from uuid import UUID
import logging
import json

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Usuario
from app.models.expediente import Expediente, ExpedienteMovimiento
from app.services import expediente_service
from app.services import twilio_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/expedientes", tags=["expedientes"])


# ============================================================================
# SCHEMAS
# ============================================================================

class ExpedienteCreate(BaseModel):
    """Schema para crear/sincronizar un expediente."""
    iue: str = Field(..., description="IUE en formato Sede-Numero/Año (ej: 2-12345/2023)")
    cliente_id: Optional[str] = Field(None, description="UUID del cliente asociado")
    area_id: Optional[str] = Field(None, description="UUID del área")
    socio_responsable_id: Optional[str] = Field(None, description="UUID del socio responsable")


class MovimientoResponse(BaseModel):
    """Schema de respuesta para un movimiento."""
    id: str
    fecha: Optional[date]
    tipo: Optional[str]
    decreto: Optional[str]
    vencimiento: Optional[date]
    sede: Optional[str]
    notificado: bool
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class ExpedienteResponse(BaseModel):
    """Schema de respuesta para un expediente."""
    id: str
    iue: str
    iue_sede: int
    iue_numero: int
    iue_anio: int
    caratula: Optional[str]
    origen: Optional[str]
    abogado_actor: Optional[str]
    abogado_demandado: Optional[str]
    cliente_id: Optional[str]
    area_id: Optional[str]
    socio_responsable_id: Optional[str]
    ultimo_movimiento: Optional[date]
    cantidad_movimientos: int
    ultima_sincronizacion: Optional[datetime]
    activo: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    movimientos: Optional[List[MovimientoResponse]] = None

    class Config:
        from_attributes = True


class ExpedienteListResponse(BaseModel):
    """Schema de respuesta para lista paginada de expedientes."""
    total: int
    limit: int
    offset: int
    expedientes: List[ExpedienteResponse]


class SincronizacionResponse(BaseModel):
    """Schema de respuesta para sincronización."""
    expediente: ExpedienteResponse
    nuevos_movimientos: int
    mensaje: str


class MovimientoPendienteResponse(BaseModel):
    """Schema para movimientos pendientes de notificación."""
    movimiento_id: str
    expediente_id: str
    iue: str
    caratula: Optional[str]
    fecha: Optional[date]
    tipo: Optional[str]
    decreto: Optional[str]
    vencimiento: Optional[date]
    sede: Optional[str]
    socio_responsable_id: Optional[str]


class ErrorSincronizacion(BaseModel):
    """Detalle de error en sincronización."""
    iue: str
    error: str


class SincronizacionMasivaResponse(BaseModel):
    """Schema de respuesta para sincronización masiva de expedientes."""
    total_expedientes: int
    sincronizados_ok: int
    con_nuevos_movimientos: int
    total_nuevos_movimientos: int
    errores: int
    detalle_errores: List[ErrorSincronizacion]
    inicio: datetime
    fin: datetime
    duracion_segundos: float


class ResumenSincronizacionResponse(BaseModel):
    """Schema de respuesta para estadísticas de sincronización."""
    total_expedientes_activos: int
    sincronizados_hoy: int
    movimientos_sin_notificar: int
    ultima_sincronizacion_global: Optional[datetime]


class NotificacionRequest(BaseModel):
    """Schema para enviar notificación WhatsApp."""
    numero: str = Field(..., description="Número WhatsApp en formato internacional (ej: +59899123456)")


class NotificacionResponse(BaseModel):
    """Schema de respuesta para notificación."""
    exito: bool
    mensaje: str
    sid: Optional[str] = None
    detalles: Optional[dict] = None


class HistoriaResponse(BaseModel):
    """Schema de respuesta para historia del expediente."""
    expediente_id: str
    iue: str
    caratula: Optional[str]
    resumen: str
    total_movimientos: int
    generado_en: datetime


# ============================================================================
# HELPERS
# ============================================================================

def _verificar_socio(current_user: Usuario) -> None:
    """Verifica que el usuario sea socio, o lanza 403."""
    if not current_user.es_socio:
        logger.warning(f"Usuario {current_user.email} intentó acceder a expedientes sin ser socio")
        raise HTTPException(
            status_code=403, 
            detail="Solo socios pueden gestionar expedientes judiciales"
        )


def _expediente_to_response(exp: Expediente, incluir_movimientos: bool = False) -> dict:
    """Convierte un Expediente a diccionario para respuesta."""
    data = {
        "id": str(exp.id),
        "iue": exp.iue,
        "iue_sede": exp.iue_sede,
        "iue_numero": exp.iue_numero,
        "iue_anio": exp.iue_anio,
        "caratula": exp.caratula,
        "origen": exp.origen,
        "abogado_actor": exp.abogado_actor,
        "abogado_demandado": exp.abogado_demandado,
        "cliente_id": str(exp.cliente_id) if exp.cliente_id else None,
        "area_id": str(exp.area_id) if exp.area_id else None,
        "socio_responsable_id": str(exp.socio_responsable_id) if exp.socio_responsable_id else None,
        "ultimo_movimiento": exp.ultimo_movimiento,
        "cantidad_movimientos": exp.cantidad_movimientos or 0,
        "ultima_sincronizacion": exp.ultima_sincronizacion,
        "activo": exp.activo,
        "created_at": exp.created_at,
        "updated_at": exp.updated_at,
    }
    
    if incluir_movimientos and exp.movimientos:
        data["movimientos"] = [
            {
                "id": str(mov.id),
                "fecha": mov.fecha,
                "tipo": mov.tipo,
                "decreto": mov.decreto,
                "vencimiento": mov.vencimiento,
                "sede": mov.sede,
                "notificado": mov.notificado,
                "created_at": mov.created_at
            }
            for mov in exp.movimientos
        ]
    else:
        data["movimientos"] = None
    
    return data


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/sincronizar", response_model=SincronizacionResponse)
def sincronizar_expediente(
    data: ExpedienteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Sincroniza un expediente con el Poder Judicial.
    
    Si el expediente no existe en BD, lo crea.
    Si existe, actualiza datos y agrega nuevos movimientos.
    
    Solo socios pueden usar este endpoint.
    """
    _verificar_socio(current_user)
    
    logger.info(f"Sincronizando expediente {data.iue} - Usuario: {current_user.email}")
    
    try:
        expediente, nuevos = expediente_service.sincronizar_expediente(
            db=db,
            iue=data.iue,
            cliente_id=data.cliente_id,
            area_id=data.area_id,
            socio_responsable_id=data.socio_responsable_id
        )
        
        if expediente is None:
            raise HTTPException(
                status_code=404,
                detail=f"El expediente {data.iue} no existe en el Poder Judicial"
            )
        
        mensaje = (
            f"Expediente sincronizado. {nuevos} nuevos movimientos encontrados."
            if nuevos > 0 
            else "Expediente sincronizado. No hay movimientos nuevos."
        )
        
        return {
            "expediente": _expediente_to_response(expediente, incluir_movimientos=True),
            "nuevos_movimientos": nuevos,
            "mensaje": mensaje
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        logger.error(f"Error de conexión al Poder Judicial: {e}")
        raise HTTPException(
            status_code=503,
            detail="No se pudo conectar al servicio del Poder Judicial. Intente más tarde."
        )


@router.get("/", response_model=ExpedienteListResponse)
def listar_expedientes(
    socio_id: Optional[str] = Query(None, description="Filtrar por socio responsable"),
    area_id: Optional[str] = Query(None, description="Filtrar por área"),
    anio: Optional[int] = Query(None, description="Filtrar por año del IUE"),
    limit: int = Query(20, ge=1, le=100, description="Máximo de resultados"),
    offset: int = Query(0, ge=0, description="Desplazamiento para paginación"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista expedientes activos con filtros opcionales.
    
    Solo socios pueden usar este endpoint.
    """
    _verificar_socio(current_user)
    
    logger.info(f"Listando expedientes - Usuario: {current_user.email}")
    
    # Obtener expedientes
    expedientes = expediente_service.listar_expedientes_activos(
        db=db,
        socio_responsable_id=socio_id,
        area_id=area_id,
        anio=anio,
        limit=limit,
        offset=offset
    )
    
    # Contar total (sin paginación)
    query = db.query(Expediente).filter(
        Expediente.activo == True,
        Expediente.deleted_at.is_(None)
    )
    if socio_id:
        query = query.filter(Expediente.socio_responsable_id == UUID(socio_id))
    if area_id:
        query = query.filter(Expediente.area_id == UUID(area_id))
    if anio:
        query = query.filter(Expediente.iue_anio == anio)
    
    total = query.count()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "expedientes": [_expediente_to_response(exp) for exp in expedientes]
    }


@router.post("/sincronizar-todos", response_model=SincronizacionMasivaResponse)
def sincronizar_todos_expedientes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Sincroniza TODOS los expedientes activos con el Poder Judicial.
    
    ⚠️ ADVERTENCIA: Este endpoint puede demorar varios minutos si hay muchos expedientes.
    Se espera 1 segundo entre cada consulta para no sobrecargar el servicio del PJ.
    
    Solo socios pueden usar este endpoint.
    """
    _verificar_socio(current_user)
    
    logger.info(f"🔄 Iniciando sincronización masiva - Usuario: {current_user.email}")
    
    try:
        resultado = expediente_service.sincronizar_todos_los_expedientes(db)
        
        logger.info(
            f"✅ Sincronización masiva completada: {resultado['sincronizados_ok']}/{resultado['total_expedientes']} "
            f"expedientes, {resultado['total_nuevos_movimientos']} nuevos movimientos"
        )
        
        return resultado
        
    except Exception as e:
        logger.error(f"❌ Error en sincronización masiva: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error durante la sincronización masiva: {str(e)}"
        )


@router.get("/resumen-sincronizacion", response_model=ResumenSincronizacionResponse)
def obtener_resumen_sync(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene estadísticas actuales de sincronización de expedientes.
    
    Incluye: total activos, sincronizados hoy, movimientos pendientes, última sync.
    Solo socios pueden usar este endpoint.
    """
    _verificar_socio(current_user)
    
    logger.info(f"📊 Consultando resumen de sincronización - Usuario: {current_user.email}")
    
    resumen = expediente_service.obtener_resumen_sincronizacion(db)
    
    return resumen


@router.get("/pendientes", response_model=List[MovimientoPendienteResponse])
def listar_movimientos_pendientes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista movimientos pendientes de notificación.
    
    Útil para el sistema de alertas Twilio.
    Solo socios pueden usar este endpoint.
    """
    _verificar_socio(current_user)
    
    logger.info(f"Consultando movimientos pendientes - Usuario: {current_user.email}")
    
    movimientos = expediente_service.obtener_movimientos_sin_notificar(db)
    
    return movimientos


@router.post("/pendientes/marcar-notificados")
def marcar_movimientos_notificados(
    movimiento_ids: List[str],
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Marca movimientos como notificados.
    
    Llamado después de enviar alertas.
    Solo socios pueden usar este endpoint.
    """
    _verificar_socio(current_user)
    
    if not movimiento_ids:
        raise HTTPException(status_code=400, detail="Se requiere al menos un ID de movimiento")
    
    logger.info(f"Marcando {len(movimiento_ids)} movimientos como notificados - Usuario: {current_user.email}")
    
    actualizados = expediente_service.marcar_movimientos_notificados(db, movimiento_ids)
    
    return {
        "mensaje": f"{actualizados} movimientos marcados como notificados",
        "actualizados": actualizados
    }


@router.post("/notificaciones/test", response_model=NotificacionResponse)
def enviar_notificacion_test(
    data: NotificacionRequest,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Envía mensaje de prueba para verificar configuración de WhatsApp.
    
    Solo socios pueden usar este endpoint.
    """
    _verificar_socio(current_user)
    
    logger.info(f"📱 Enviando WhatsApp de prueba a {data.numero} - Usuario: {current_user.email}")
    
    resultado = twilio_service.enviar_test(data.numero)
    
    if resultado["exito"]:
        return {
            "exito": True,
            "mensaje": "Mensaje de prueba enviado correctamente",
            "sid": resultado["sid"],
            "detalles": None
        }
    else:
        return {
            "exito": False,
            "mensaje": f"Error al enviar: {resultado['error']}",
            "sid": None,
            "detalles": {"error": resultado["error"]}
        }


@router.post("/notificaciones/enviar", response_model=NotificacionResponse)
def enviar_notificacion_movimientos(
    data: NotificacionRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Envía notificación de movimientos pendientes via WhatsApp.
    
    Obtiene todos los movimientos sin notificar, los envía y los marca como notificados.
    Solo socios pueden usar este endpoint.
    """
    _verificar_socio(current_user)
    
    logger.info(f"📱 Enviando notificación de movimientos a {data.numero} - Usuario: {current_user.email}")
    
    # Obtener movimientos pendientes
    movimientos = expediente_service.obtener_movimientos_sin_notificar(db)
    
    if not movimientos:
        return {
            "exito": True,
            "mensaje": "No hay movimientos pendientes de notificar",
            "sid": None,
            "detalles": {"total_movimientos": 0}
        }
    
    # Enviar notificación
    resultado = twilio_service.notificar_movimientos_expedientes(movimientos, data.numero)
    
    if resultado.get("exito"):
        # Marcar como notificados
        ids = [m["movimiento_id"] for m in movimientos]
        expediente_service.marcar_movimientos_notificados(db, ids)
        
        return {
            "exito": True,
            "mensaje": f"Notificación enviada: {resultado['total_movimientos']} movimientos de {resultado['total_expedientes']} expedientes",
            "sid": resultado.get("sid"),
            "detalles": {
                "total_movimientos": resultado["total_movimientos"],
                "total_expedientes": resultado["total_expedientes"]
            }
        }
    else:
        return {
            "exito": False,
            "mensaje": f"Error al enviar: {resultado.get('error', 'Error desconocido')}",
            "sid": None,
            "detalles": {"error": resultado.get("error")}
        }


@router.get("/{expediente_id}/historia", response_model=HistoriaResponse)
def obtener_historia_expediente(
    expediente_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Genera resumen inteligente de la historia del expediente usando Claude.
    
    Analiza todos los movimientos procesales y genera un resumen ejecutivo
    con cronología, estado actual, hitos importantes y próximos pasos.
    
    Solo socios pueden usar este endpoint.
    """
    _verificar_socio(current_user)
    
    logger.info(f"Generando historia del expediente {expediente_id} - Usuario: {current_user.email}")
    
    try:
        exp_uuid = UUID(expediente_id)
    except ValueError as e:
        logger.error(f"ID de expediente inválido: {expediente_id} - Error: {e}")
        raise HTTPException(
            status_code=400, 
            detail=f"ID de expediente inválido: {expediente_id}. Formato esperado: UUID"
        )
    
    # Obtener expediente con movimientos
    expediente = db.query(Expediente).filter(
        Expediente.id == exp_uuid,
        Expediente.deleted_at.is_(None)
    ).first()
    
    if expediente is None:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    
    # Obtener todos los movimientos ordenados cronológicamente (más antiguo primero)
    todos_movimientos = db.query(ExpedienteMovimiento).filter(
        ExpedienteMovimiento.expediente_id == exp_uuid
    ).order_by(ExpedienteMovimiento.fecha.asc()).all()
    
    total_movimientos = len(todos_movimientos)
    
    # Si hay más de 35 movimientos, tomar primeros 5 + últimos 30 para evitar timeout
    if total_movimientos > 35:
        movimientos = todos_movimientos[:5] + todos_movimientos[-30:]
        movimientos_omitidos = total_movimientos - 35
    else:
        movimientos = todos_movimientos
        movimientos_omitidos = 0
    
    # Preparar datos para Claude
    movimientos_data = []
    for mov in movimientos:
        movimientos_data.append({
            "fecha": mov.fecha.strftime("%d/%m/%Y") if mov.fecha else "S/F",
            "tipo": mov.tipo or "Sin tipo",
            "decreto": mov.decreto,
            "vencimiento": mov.vencimiento.strftime("%d/%m/%Y") if mov.vencimiento else None,
            "sede": mov.sede
        })
    
    # Construir prompt para Claude
    sede_actual = movimientos[-1].sede if movimientos else "No especificada"
    
    prompt = f"""Eres un asistente legal experto en derecho procesal uruguayo.

Analiza la historia procesal de este expediente y genera un resumen ejecutivo que:

CRONOLOGÍA: Resume las etapas principales del proceso en orden cronológico
ESTADO ACTUAL: Indica claramente dónde está el expediente ahora y qué implica
HITOS IMPORTANTES: Destaca decretos, resoluciones y actuaciones relevantes
PLAZOS: Si hay plazos corriendo o vencidos, mencionarlos
PRÓXIMOS PASOS: Sugiere qué actuaciones podrían corresponder

DATOS DEL EXPEDIENTE:

IUE: {expediente.iue}
Carátula: {expediente.caratula or 'Sin carátula'}
Origen: {expediente.origen or 'No especificado'}
Sede actual: {sede_actual}
Total movimientos: {total_movimientos}
Movimientos mostrados: {len(movimientos)} (primeros 5 + últimos 30)
Movimientos omitidos del medio: {movimientos_omitidos}

MOVIMIENTOS (cronológico):
{json.dumps(movimientos_data, ensure_ascii=False, indent=2)}

Genera un resumen profesional pero accesible, de máximo 1000 palabras.
Usa formato con bullets y secciones para facilitar la lectura."""
    
    try:
        from app.services.ai.claude_client import ClaudeClient
        
        client = ClaudeClient()
        resumen = client.complete(
            prompt=prompt,
            temperature=0.3,
            max_tokens=2000,
            timeout=60
        )
        
        logger.info(f"Historia generada exitosamente para expediente {expediente_id} ({total_movimientos} movimientos totales, {len(movimientos)} mostrados)")
        
        return {
            "expediente_id": str(expediente.id),
            "iue": expediente.iue,
            "caratula": expediente.caratula,
            "resumen": resumen.strip(),
            "total_movimientos": total_movimientos,
            "generado_en": datetime.now(timezone.utc)
        }
        
    except Exception as e:
        logger.error(f"Error generando historia con Claude: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar resumen de historia: {str(e)}"
        )


# ============================================================================
# ENDPOINTS CON PARÁMETROS DINÁMICOS (deben ir al final)
# ============================================================================

@router.get("/iue/{iue:path}", response_model=ExpedienteResponse)
def obtener_por_iue(
    iue: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene un expediente por su IUE.
    
    El IUE tiene formato "Sede-Numero/Año" (ej: 2-12345/2023).
    Solo socios pueden usar este endpoint.
    """
    _verificar_socio(current_user)
    
    logger.info(f"Buscando expediente por IUE: {iue} - Usuario: {current_user.email}")
    
    expediente = expediente_service.obtener_expediente_por_iue(db, iue)
    
    if expediente is None:
        raise HTTPException(
            status_code=404,
            detail=f"Expediente con IUE {iue} no encontrado"
        )
    
    return _expediente_to_response(expediente, incluir_movimientos=True)


@router.get("/{expediente_id}", response_model=ExpedienteResponse)
def obtener_expediente(
    expediente_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene un expediente por su ID con todos sus movimientos.
    
    Solo socios pueden usar este endpoint.
    """
    _verificar_socio(current_user)
    
    logger.info(
        f"Obteniendo expediente - ID recibido: '{expediente_id}' "
        f"(tipo: {type(expediente_id).__name__}, len: {len(expediente_id)}) - "
        f"Usuario: {current_user.email}"
    )
    
    try:
        exp_uuid = UUID(expediente_id)
        logger.debug(f"UUID parseado correctamente: {exp_uuid}")
    except ValueError as e:
        logger.error(f"ID de expediente inválido: {expediente_id} - Error: {e}")
        raise HTTPException(
            status_code=400, 
            detail=f"ID de expediente inválido: {expediente_id}. Formato esperado: UUID"
        )
    
    expediente = db.query(Expediente).filter(
        Expediente.id == exp_uuid,
        Expediente.deleted_at.is_(None)
    ).first()
    
    if expediente is None:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    
    return _expediente_to_response(expediente, incluir_movimientos=True)


@router.post("/{expediente_id}/sincronizar", response_model=SincronizacionResponse)
def resincronizar_expediente(
    expediente_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Re-sincroniza un expediente existente con el Poder Judicial.
    
    Busca nuevos movimientos y actualiza datos.
    Solo socios pueden usar este endpoint.
    """
    _verificar_socio(current_user)
    
    logger.info(f"Re-sincronizando expediente {expediente_id} - Usuario: {current_user.email}")
    
    try:
        exp_uuid = UUID(expediente_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de expediente inválido")
    
    # Buscar expediente existente
    expediente = db.query(Expediente).filter(
        Expediente.id == exp_uuid,
        Expediente.deleted_at.is_(None)
    ).first()
    
    if expediente is None:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    
    try:
        # Re-sincronizar usando el IUE del expediente existente
        expediente_actualizado, nuevos = expediente_service.sincronizar_expediente(
            db=db,
            iue=expediente.iue,
            cliente_id=str(expediente.cliente_id) if expediente.cliente_id else None,
            area_id=str(expediente.area_id) if expediente.area_id else None,
            socio_responsable_id=str(expediente.socio_responsable_id) if expediente.socio_responsable_id else None
        )
        
        mensaje = (
            f"Expediente re-sincronizado. {nuevos} nuevos movimientos encontrados."
            if nuevos > 0 
            else "Expediente re-sincronizado. No hay movimientos nuevos."
        )
        
        return {
            "expediente": _expediente_to_response(expediente_actualizado, incluir_movimientos=True),
            "nuevos_movimientos": nuevos,
            "mensaje": mensaje
        }
        
    except ConnectionError as e:
        logger.error(f"Error de conexión al Poder Judicial: {e}")
        raise HTTPException(
            status_code=503,
            detail="No se pudo conectar al servicio del Poder Judicial. Intente más tarde."
        )


@router.delete("/{expediente_id}")
def eliminar_expediente(
    expediente_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Elimina un expediente (soft delete).
    
    Los movimientos se mantienen pero el expediente queda inactivo.
    Solo socios pueden usar este endpoint.
    """
    _verificar_socio(current_user)
    
    logger.info(f"Eliminando expediente {expediente_id} - Usuario: {current_user.email}")
    
    try:
        exp_uuid = UUID(expediente_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de expediente inválido")
    
    expediente = db.query(Expediente).filter(
        Expediente.id == exp_uuid,
        Expediente.deleted_at.is_(None)
    ).first()
    
    if expediente is None:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    
    # Soft delete
    expediente.deleted_at = datetime.now(timezone.utc)
    expediente.activo = False
    db.commit()
    
    logger.info(f"Expediente {expediente.iue} eliminado (soft delete)")
    
    return {
        "mensaje": f"Expediente {expediente.iue} eliminado",
        "id": str(expediente.id)
    }


@router.patch("/{expediente_id}")
def actualizar_expediente(
    expediente_id: str,
    cliente_id: Optional[str] = None,
    area_id: Optional[str] = None,
    socio_responsable_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualiza las relaciones de un expediente (cliente, área, socio responsable).
    
    Los datos del expediente (carátula, movimientos) se actualizan via sincronización.
    Solo socios pueden usar este endpoint.
    """
    _verificar_socio(current_user)
    
    logger.info(f"Actualizando relaciones expediente {expediente_id} - Usuario: {current_user.email}")
    
    try:
        exp_uuid = UUID(expediente_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de expediente inválido")
    
    expediente = db.query(Expediente).filter(
        Expediente.id == exp_uuid,
        Expediente.deleted_at.is_(None)
    ).first()
    
    if expediente is None:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    
    # Actualizar relaciones
    if cliente_id is not None:
        expediente.cliente_id = UUID(cliente_id) if cliente_id else None
    
    if area_id is not None:
        expediente.area_id = UUID(area_id) if area_id else None
    
    if socio_responsable_id is not None:
        expediente.socio_responsable_id = UUID(socio_responsable_id) if socio_responsable_id else None
    
    expediente.updated_at = datetime.now(timezone.utc)
    db.commit()
    
    return {
        "mensaje": "Expediente actualizado",
        "expediente": _expediente_to_response(expediente)
    }
