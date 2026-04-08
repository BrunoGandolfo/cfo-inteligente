"""
API para gestión de trámites registrales DGR.

Seguimiento de documentos ingresados en la Dirección General de Registros.
Solo SOCIOS pueden crear y eliminar trámites.
"""

import json
import logging
from datetime import datetime, date, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Usuario
from app.models.tramite_dgr import TramiteDgr
from app.schemas.tramite_dgr import (
    OFICINAS_DGR,
    REGISTROS_DGR,
    TramiteDgrCreate,
    TramiteDgrResponse,
)
from app.services.dgr_service import consultar_tramite_dgr

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# HELPERS
# ============================================================================

def _verificar_socio(current_user: Usuario) -> None:
    """Verifica que el usuario sea socio, o lanza 403."""
    if current_user.es_socio:
        return
    logger.warning(f"Usuario ID: {current_user.id} intentó acceso de socio a tramites-dgr sin permiso")
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para realizar esta acción. Solo socios.",
    )


def _obtener_tramite(db: Session, tramite_id: str, current_user: Usuario) -> TramiteDgr:
    """Busca un trámite por ID, verifica pertenencia o rol socio. Retorna el trámite o lanza 404/403."""
    try:
        t_uuid = UUID(tramite_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de trámite inválido")

    tramite = db.query(TramiteDgr).filter(
        TramiteDgr.id == t_uuid,
        TramiteDgr.deleted_at.is_(None),
    ).first()

    if tramite is None:
        raise HTTPException(status_code=404, detail="Trámite no encontrado")

    # Verificar que pertenece al usuario o que es socio
    if tramite.responsable_id != current_user.id and not current_user.es_socio:
        raise HTTPException(status_code=403, detail="No tienes acceso a este trámite")

    return tramite


def _aplicar_datos_dgr(tramite: TramiteDgr, datos: dict) -> None:
    """Aplica datos obtenidos de la DGR al modelo del trámite."""
    from app.services.dgr_service import parsear_fecha_dgr, calcular_fecha_vencimiento

    # fecha_ingreso puede venir como date (del service) o como string (legacy)
    fecha = datos.get("fecha_ingreso")
    if fecha is not None:
        if isinstance(fecha, str):
            tramite.fecha_ingreso = parsear_fecha_dgr(fecha)
        else:
            tramite.fecha_ingreso = fecha

    tramite.escribano_emisor = datos.get("escribano_emisor")
    tramite.estado_actual = datos.get("estado_actual")
    tramite.observaciones = datos.get("observaciones")

    inscripciones = datos.get("inscripciones")
    if inscripciones:
        tramite.actos = json.dumps(inscripciones, ensure_ascii=False)

    tramite.ultimo_chequeo = datetime.now(timezone.utc)
    tramite.fecha_vencimiento = calcular_fecha_vencimiento(
        tramite.fecha_ingreso, tramite.estado_actual
    )


# ============================================================================
# SCHEMAS AUXILIARES
# ============================================================================

class TramiteListResponse(BaseModel):
    """Respuesta paginada de trámites."""
    total: int
    limit: int
    offset: int
    tramites: List[TramiteDgrResponse]


class MarcarNotificadosRequest(BaseModel):
    """Body para marcar trámites como notificados."""
    ids: List[UUID]


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/", response_model=TramiteDgrResponse, status_code=201)
async def crear_tramite(
    data: TramiteDgrCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Crea un trámite DGR nuevo y lo sincroniza con la DGR.

    Solo socios pueden crear trámites.
    """
    _verificar_socio(current_user)

    logger.info(
        f"Creando trámite DGR {data.registro}-{data.oficina} {data.anio}/{data.numero_entrada} "
        f"- Usuario ID: {current_user.id}"
    )

    # Verificar duplicado (UniqueConstraint)
    existente = db.query(TramiteDgr).filter(
        TramiteDgr.registro == data.registro,
        TramiteDgr.oficina == data.oficina,
        TramiteDgr.anio == data.anio,
        TramiteDgr.numero_entrada == data.numero_entrada,
        TramiteDgr.bis == (data.bis or ""),
        TramiteDgr.deleted_at.is_(None),
    ).first()

    if existente:
        raise HTTPException(
            status_code=409,
            detail="Ya existe un trámite con esos datos de identificación",
        )

    # Crear registro
    tramite = TramiteDgr(
        registro=data.registro,
        oficina=data.oficina,
        anio=data.anio,
        numero_entrada=data.numero_entrada,
        bis=data.bis or "",
        responsable_id=current_user.id,
        registro_nombre=REGISTROS_DGR.get(data.registro),
        oficina_nombre=OFICINAS_DGR.get(data.oficina),
    )

    db.add(tramite)
    db.flush()  # obtener ID antes de consultar DGR

    # Consultar DGR para obtener datos actuales
    try:
        datos = await consultar_tramite_dgr(
            registro=data.registro,
            oficina=data.oficina,
            anio=data.anio,
            numero=data.numero_entrada,
            bis=data.bis or "",
        )
    except Exception as e:
        logger.warning(f"No se pudo consultar DGR al crear trámite: {e}")
        datos = None

    if datos:
        _aplicar_datos_dgr(tramite, datos)

    db.commit()
    db.refresh(tramite)

    logger.info(f"Trámite DGR creado: {tramite.id}")

    return tramite


@router.get("/pendientes", response_model=List[TramiteDgrResponse])
async def listar_pendientes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Lista trámites con cambios detectados sin notificar.
    """
    logger.info(f"Consultando trámites pendientes - Usuario ID: {current_user.id}")

    tramites = db.query(TramiteDgr).filter(
        TramiteDgr.cambio_detectado == True,
        TramiteDgr.deleted_at.is_(None),
    ).order_by(TramiteDgr.ultimo_chequeo.desc()).all()

    return tramites


@router.post("/pendientes/marcar-notificados")
async def marcar_notificados(
    data: MarcarNotificadosRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Marca trámites como notificados (cambio_detectado = False).
    """
    if not data.ids:
        raise HTTPException(status_code=400, detail="Se requiere al menos un ID")

    logger.info(
        f"Marcando {len(data.ids)} trámites como notificados - Usuario ID: {current_user.id}"
    )

    actualizados = 0
    for tramite_id in data.ids:
        tramite = db.query(TramiteDgr).filter(
            TramiteDgr.id == tramite_id,
            TramiteDgr.deleted_at.is_(None),
        ).first()
        if tramite:
            tramite.cambio_detectado = False
            actualizados += 1

    db.commit()

    return {
        "mensaje": f"{actualizados} trámites marcados como notificados",
        "actualizados": actualizados,
    }


@router.get("/", response_model=TramiteListResponse)
async def listar_tramites(
    activo: bool = Query(True, description="Filtrar por activo/inactivo"),
    limit: int = Query(50, ge=1, le=200, description="Máximo de resultados"),
    offset: int = Query(0, ge=0, description="Desplazamiento para paginación"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Lista trámites del usuario autenticado.
    """
    logger.info(f"Listando trámites DGR - Usuario ID: {current_user.id}")

    if current_user.es_socio:
        base_query = db.query(TramiteDgr).filter(
            TramiteDgr.deleted_at.is_(None),
        )
    else:
        base_query = db.query(TramiteDgr).filter(
            TramiteDgr.responsable_id == current_user.id,
            TramiteDgr.deleted_at.is_(None),
        )

    if activo is not None:
        base_query = base_query.filter(TramiteDgr.activo == activo)

    total = base_query.count()

    tramites = base_query.order_by(
        TramiteDgr.created_at.desc()
    ).offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "tramites": tramites,
    }


@router.get("/{tramite_id}", response_model=TramiteDgrResponse)
async def obtener_tramite(
    tramite_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Obtiene un trámite por su ID.

    El usuario debe ser el responsable o un socio.
    """
    logger.info(f"Obteniendo trámite DGR {tramite_id} - Usuario ID: {current_user.id}")

    tramite = _obtener_tramite(db, tramite_id, current_user)

    return tramite


@router.post("/{tramite_id}/sincronizar", response_model=TramiteDgrResponse)
async def sincronizar_tramite(
    tramite_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Re-sincroniza un trámite existente con la DGR.

    Compara estado nuevo con el anterior y marca cambio_detectado si difiere.
    """
    logger.info(f"Sincronizando trámite DGR {tramite_id} - Usuario ID: {current_user.id}")

    tramite = _obtener_tramite(db, tramite_id, current_user)

    # Consultar DGR
    try:
        datos = await consultar_tramite_dgr(
            registro=tramite.registro,
            oficina=tramite.oficina,
            anio=tramite.anio,
            numero=tramite.numero_entrada,
            bis=tramite.bis or "",
        )
    except Exception as e:
        logger.error(f"Error consultando DGR para trámite {tramite_id}: {e}")
        raise HTTPException(
            status_code=503,
            detail="No se pudo conectar al servicio de la DGR. Intente más tarde.",
        )

    if datos is None:
        raise HTTPException(
            status_code=502,
            detail="La DGR no retornó datos para este trámite.",
        )

    # Detectar cambio de estado
    estado_nuevo = datos.get("estado_actual")
    if estado_nuevo and estado_nuevo != tramite.estado_actual:
        tramite.estado_anterior = tramite.estado_actual
        tramite.cambio_detectado = True
        logger.info(
            f"Cambio detectado en trámite {tramite_id}: "
            f"{tramite.estado_actual} -> {estado_nuevo}"
        )

    # Aplicar datos nuevos
    _aplicar_datos_dgr(tramite, datos)

    tramite.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(tramite)

    return tramite


@router.delete("/{tramite_id}")
async def eliminar_tramite(
    tramite_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Elimina un trámite (soft delete).

    Solo socios pueden eliminar trámites.
    """
    _verificar_socio(current_user)

    logger.info(f"Eliminando trámite DGR {tramite_id} - Usuario ID: {current_user.id}")

    tramite = _obtener_tramite(db, tramite_id, current_user)

    # Soft delete
    tramite.deleted_at = datetime.now(timezone.utc)
    tramite.activo = False
    db.commit()

    logger.info(f"Trámite DGR {tramite.id} eliminado (soft delete)")

    return {
        "mensaje": f"Trámite {tramite.registro}-{tramite.oficina} {tramite.anio}/{tramite.numero_entrada} eliminado",
        "id": str(tramite.id),
    }
