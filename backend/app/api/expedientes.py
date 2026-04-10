"""
API para gestión de expedientes judiciales.

Integración con el Web Service del Poder Judicial de Uruguay.
Solo SOCIOS pueden acceder a estos endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, date, timezone
from uuid import UUID
import asyncio
from html import escape
import logging
import json

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Usuario
from app.models.expediente import Expediente, ExpedienteMovimiento
from app.models.telegram_usuario import TelegramUsuario
from app.core.access_control import (
    USUARIOS_ACCESO_EXPEDIENTES, USUARIOS_FILTRO_EXPEDIENTES,
)
from app.schemas.expediente import (
    ErrorSincronizacion,
    ExpedienteCreate,
    ExpedienteListResponse,
    ExpedienteResponse,
    HistoriaResponse,
    MovimientoPendienteResponse,
    NotificacionRequest,
    NotificacionResponse,
    ResumenSincronizacionResponse,
    SincronizacionMasivaResponse,
    SincronizacionResponse,
)
from app.services import expediente_service
from app.services.telegram_service import enviar_mensaje_telegram

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/expedientes", tags=["expedientes"])


# ============================================================================
# HELPERS
# ============================================================================

def _verificar_socio(current_user: Usuario) -> None:
    """Verifica que el usuario tenga acceso al módulo de Expedientes, o lanza 403."""
    if current_user.email.lower() in [email.lower() for email in USUARIOS_ACCESO_EXPEDIENTES]:
        return
    logger.warning(f"Usuario ID: {current_user.id} intentó acceder a expedientes sin permiso")
    raise HTTPException(
        status_code=403, 
        detail="No tienes permiso para acceder a expedientes judiciales"
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
        "responsable_id": str(exp.responsable_id) if exp.responsable_id else None,
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


def _obtener_chat_id_usuario(db: Session, usuario_id: UUID) -> Optional[int]:
    """Obtiene el chat_id activo de Telegram para un usuario interno."""
    telegram_usuario = (
        db.query(TelegramUsuario)
        .filter(
            TelegramUsuario.usuario_id == usuario_id,
            TelegramUsuario.activo == True,
        )
        .first()
    )
    return telegram_usuario.chat_id if telegram_usuario else None


def _formatear_fecha(valor: Optional[date]) -> str:
    """Formatea fechas de expediente para mensajes Telegram."""
    return valor.strftime("%d/%m/%Y") if valor else "Sin fecha"


def _construir_mensaje_movimientos_telegram(movimientos: List[dict]) -> str:
    """Construye un mensaje HTML de Telegram con movimientos pendientes."""
    por_expediente: dict[str, dict] = {}
    for movimiento in movimientos:
        iue = movimiento["iue"]
        if iue not in por_expediente:
            por_expediente[iue] = {
                "caratula": movimiento["caratula"],
                "movimientos": [],
            }
        por_expediente[iue]["movimientos"].append(movimiento)

    lineas = ["<b>CFO Inteligente - Movimientos pendientes</b>", ""]
    for iue, data in por_expediente.items():
        lineas.append(f"<b>{escape(iue)}</b>")
        lineas.append(escape(data["caratula"] or "Sin carátula"))
        for movimiento in data["movimientos"][:3]:
            lineas.append(
                "• "
                f"<b>Fecha:</b> {_formatear_fecha(movimiento.get('fecha'))} | "
                f"<b>Tipo:</b> {escape(movimiento.get('tipo') or 'Sin tipo')} | "
                f"<b>Decreto:</b> {escape(movimiento.get('decreto') or 'Sin decreto')} | "
                f"<b>Vencimiento:</b> {_formatear_fecha(movimiento.get('vencimiento'))}"
            )
        if len(data["movimientos"]) > 3:
            lineas.append(f"... y {len(data['movimientos']) - 3} más")
        lineas.append("")

    return "\n".join(lineas).strip()


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
    
    logger.info(f"Sincronizando expediente {data.iue} - Usuario ID: {current_user.id}")
    
    # Si no se especifica responsable, asignar al usuario actual
    responsable_final = data.responsable_id if data.responsable_id else str(current_user.id)
    
    try:
        expediente, nuevos = expediente_service.sincronizar_expediente(
            db=db,
            iue=data.iue,
            cliente_id=data.cliente_id,
            area_id=data.area_id,
            responsable_id=responsable_final
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
    responsable_id: Optional[str] = Query(None, description="Filtrar por responsable (usuario)"),
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
    
    logger.info(f"Listando expedientes - Usuario ID: {current_user.id}")
    
    # Forzar filtro por responsable para usuarios específicos
    if current_user.email.lower() in USUARIOS_FILTRO_EXPEDIENTES:
        responsable_id = str(current_user.id)
    
    # Obtener expedientes
    expedientes = expediente_service.listar_expedientes_activos(
        db=db,
        responsable_id=responsable_id,
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
    if responsable_id:
        query = query.filter(Expediente.responsable_id == UUID(responsable_id))
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
    
    logger.info(f"🔄 Iniciando sincronización masiva - Usuario ID: {current_user.id}")
    
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
    
    logger.info(f"📊 Consultando resumen de sincronización - Usuario ID: {current_user.id}")
    
    resumen = expediente_service.obtener_resumen_sincronizacion(db)
    
    return resumen


@router.get("/pendientes", response_model=List[MovimientoPendienteResponse])
def listar_movimientos_pendientes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista movimientos pendientes de notificación.
    
    Útil para el sistema de alertas Telegram.
    Solo socios pueden usar este endpoint.
    """
    _verificar_socio(current_user)
    
    logger.info(f"Consultando movimientos pendientes - Usuario ID: {current_user.id}")
    
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
    
    logger.info(f"Marcando {len(movimiento_ids)} movimientos como notificados - Usuario ID: {current_user.id}")
    
    actualizados = expediente_service.marcar_movimientos_notificados(db, movimiento_ids)
    
    return {
        "mensaje": f"{actualizados} movimientos marcados como notificados",
        "actualizados": actualizados
    }


@router.post("/notificaciones/test", response_model=NotificacionResponse)
def enviar_notificacion_test(
    data: NotificacionRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Envía mensaje de prueba para verificar configuración de Telegram.
    
    Solo socios pueden usar este endpoint.
    """
    _verificar_socio(current_user)

    chat_id = _obtener_chat_id_usuario(db, current_user.id)
    if not chat_id:
        return {
            "exito": False,
            "mensaje": "No tienes Telegram vinculado. Enviá /start al bot y volvé a intentar.",
            "sid": None,
            "detalles": {"chat_id": None}
        }

    logger.info(f"📱 Enviando Telegram de prueba a usuario {current_user.id}")

    mensaje = (
        "<b>CFO Inteligente</b>\n\n"
        f"Hola {escape(current_user.nombre)}.\n"
        "La conexión con Telegram quedó verificada correctamente."
    )
    enviado = asyncio.run(enviar_mensaje_telegram(chat_id, mensaje))

    if enviado:
        return {
            "exito": True,
            "mensaje": "Mensaje de prueba enviado correctamente por Telegram",
            "sid": None,
            "detalles": {"chat_id": chat_id}
        }

    return {
        "exito": False,
        "mensaje": "Error al enviar la notificación de prueba por Telegram",
        "sid": None,
        "detalles": {"chat_id": chat_id}
    }


@router.post("/notificaciones/enviar", response_model=NotificacionResponse)
def enviar_notificacion_movimientos(
    data: NotificacionRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Envía notificación de movimientos pendientes via Telegram.
    
    Obtiene todos los movimientos sin notificar, los envía y los marca como notificados.
    Solo socios pueden usar este endpoint.
    """
    _verificar_socio(current_user)

    chat_id = _obtener_chat_id_usuario(db, current_user.id)
    if not chat_id:
        return {
            "exito": False,
            "mensaje": "No tienes Telegram vinculado. Enviá /start al bot y volvé a intentar.",
            "sid": None,
            "detalles": {"chat_id": None}
        }

    logger.info(f"📱 Enviando notificación de movimientos por Telegram a usuario {current_user.id}")

    # Obtener movimientos pendientes
    movimientos = expediente_service.obtener_movimientos_sin_notificar(db)

    if not movimientos:
        return {
            "exito": True,
            "mensaje": "No hay movimientos pendientes de notificar",
            "sid": None,
            "detalles": {"total_movimientos": 0}
        }

    mensaje = _construir_mensaje_movimientos_telegram(movimientos)
    enviado = asyncio.run(enviar_mensaje_telegram(chat_id, mensaje))

    if enviado:
        ids = [movimiento["movimiento_id"] for movimiento in movimientos]
        actualizados = expediente_service.marcar_movimientos_notificados(db, ids)
        expedientes = {movimiento["expediente_id"] for movimiento in movimientos}

        return {
            "exito": True,
            "mensaje": (
                f"Notificación enviada por Telegram: {actualizados} movimientos "
                f"de {len(expedientes)} expedientes"
            ),
            "sid": None,
            "detalles": {
                "total_movimientos": actualizados,
                "total_expedientes": len(expedientes),
                "chat_id": chat_id,
            }
        }

    return {
        "exito": False,
        "mensaje": "Error al enviar la notificación por Telegram",
        "sid": None,
        "detalles": {"chat_id": chat_id}
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
    
    logger.info(f"Generando historia del expediente {expediente_id} - Usuario ID: {current_user.id}")
    
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
    
    logger.info(f"Buscando expediente por IUE: {iue} - Usuario ID: {current_user.id}")
    
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
        f"Usuario ID: {current_user.id}"
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
    
    logger.info(f"Re-sincronizando expediente {expediente_id} - Usuario ID: {current_user.id}")
    
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
            responsable_id=str(expediente.responsable_id) if expediente.responsable_id else None
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
    
    logger.info(f"Eliminando expediente {expediente_id} - Usuario ID: {current_user.id}")
    
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
    responsable_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualiza las relaciones de un expediente (cliente, área, responsable).
    
    Los datos del expediente (carátula, movimientos) se actualizan via sincronización.
    Solo socios pueden usar este endpoint.
    """
    _verificar_socio(current_user)
    
    logger.info(f"Actualizando relaciones expediente {expediente_id} - Usuario ID: {current_user.id}")
    
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
    
    if responsable_id is not None:
        expediente.responsable_id = UUID(responsable_id) if responsable_id else None
    
    expediente.updated_at = datetime.now(timezone.utc)
    db.commit()
    
    return {
        "mensaje": "Expediente actualizado",
        "expediente": _expediente_to_response(expediente)
    }
