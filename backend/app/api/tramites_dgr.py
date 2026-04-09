"""
API para gestión de trámites registrales DGR.

Seguimiento de documentos ingresados en la Dirección General de Registros.
Solo SOCIOS pueden crear y eliminar trámites.
"""

import logging
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Usuario
from app.schemas.tramite_dgr import (
    MarcarNotificadosRequest,
    TramiteDgrCreate,
    TramiteDgrResponse,
    TramiteListResponse,
)
from app.services import tramites_dgr_service
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


def _verificar_acceso_tramite(tramite, current_user: Usuario) -> None:
    """Verifica que el usuario tenga acceso al trámite (dueño o socio)."""
    if tramite.responsable_id != current_user.id and not current_user.es_socio:
        raise HTTPException(status_code=403, detail="No tienes acceso a este trámite")


def _obtener_tramite_o_404(db: Session, tramite_id: str):
    """Busca un trámite por ID, lanza 404 si no existe."""
    try:
        t_uuid = UUID(tramite_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de trámite inválido")

    tramite = tramites_dgr_service.obtener_tramite(db, t_uuid)
    if tramite is None:
        raise HTTPException(status_code=404, detail="Trámite no encontrado")
    return tramite


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/", response_model=TramiteDgrResponse, status_code=201)
async def crear_tramite(
    data: TramiteDgrCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Crea un trámite DGR nuevo y lo sincroniza con la DGR. Solo socios."""
    _verificar_socio(current_user)

    logger.info(
        f"Creando trámite DGR {data.registro}-{data.oficina} {data.anio}/{data.numero_entrada} "
        f"- Usuario ID: {current_user.id}"
    )

    existente = tramites_dgr_service.verificar_duplicado(
        db, data.registro, data.oficina, data.anio, data.numero_entrada, data.bis or "",
    )
    if existente:
        raise HTTPException(status_code=409, detail="Ya existe un trámite con esos datos de identificación")

    tramite = tramites_dgr_service.crear_tramite(
        db,
        registro=data.registro,
        oficina=data.oficina,
        anio=data.anio,
        numero_entrada=data.numero_entrada,
        responsable_id=current_user.id,
        bis=data.bis or "",
    )

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
        tramites_dgr_service.aplicar_datos_dgr(tramite, datos)

    db.commit()
    db.refresh(tramite)

    logger.info(f"Trámite DGR creado: {tramite.id}")
    return tramite


@router.get("/pendientes", response_model=List[TramiteDgrResponse])
async def listar_pendientes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Lista trámites con cambios detectados sin notificar."""
    return tramites_dgr_service.listar_pendientes(db)


@router.post("/pendientes/marcar-notificados")
async def marcar_notificados(
    data: MarcarNotificadosRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Marca trámites como notificados (cambio_detectado = False)."""
    if not data.ids:
        raise HTTPException(status_code=400, detail="Se requiere al menos un ID")

    actualizados = tramites_dgr_service.marcar_notificados(db, data.ids)

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
    """Lista trámites del usuario autenticado."""
    responsable_id = None if current_user.es_socio else current_user.id

    result = tramites_dgr_service.listar_tramites(
        db, responsable_id=responsable_id, activo=activo, limit=limit, offset=offset,
    )

    return {
        "total": result["total"],
        "limit": limit,
        "offset": offset,
        "tramites": result["tramites"],
    }


@router.get("/{tramite_id}", response_model=TramiteDgrResponse)
async def obtener_tramite(
    tramite_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Obtiene un trámite por su ID."""
    tramite = _obtener_tramite_o_404(db, tramite_id)
    _verificar_acceso_tramite(tramite, current_user)
    return tramite


@router.post("/{tramite_id}/sincronizar", response_model=TramiteDgrResponse)
async def sincronizar_tramite(
    tramite_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Re-sincroniza un trámite existente con la DGR."""
    tramite = _obtener_tramite_o_404(db, tramite_id)
    _verificar_acceso_tramite(tramite, current_user)

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
        raise HTTPException(status_code=503, detail="No se pudo conectar al servicio de la DGR.")

    if datos is None:
        raise HTTPException(status_code=502, detail="La DGR no retornó datos para este trámite.")

    estado_nuevo = datos.get("estado_actual")
    if tramites_dgr_service.detectar_cambio_estado(tramite, estado_nuevo):
        logger.info(f"Cambio detectado en trámite {tramite_id}: {tramite.estado_anterior} -> {estado_nuevo}")

    tramites_dgr_service.aplicar_datos_dgr(tramite, datos)
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
    """Elimina un trámite (soft delete). Solo socios."""
    _verificar_socio(current_user)

    tramite = _obtener_tramite_o_404(db, tramite_id)
    tramites_dgr_service.eliminar_tramite(db, tramite)

    logger.info(f"Trámite DGR {tramite.id} eliminado (soft delete)")
    return {
        "mensaje": f"Trámite {tramite.registro}-{tramite.oficina} {tramite.anio}/{tramite.numero_entrada} eliminado",
        "id": str(tramite.id),
    }
