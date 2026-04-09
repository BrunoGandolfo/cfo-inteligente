"""
API para gestión de casos legales.

Endpoints CRUD para casos legales.
Solo 4 usuarios tienen acceso: Bruno (ve todos), Gonzalo, Pancho, Gerardo (ven solo suyos).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Usuario
from app.models.expediente import Expediente
from app.services import expediente_service
from app.services import casos_service
from app.schemas.caso import CasoCreate, CasoUpdate, CasoResponse, CasoList
from app.core.access_control import USUARIOS_ACCESO_CASOS, USUARIOS_FILTRO_CASOS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/casos", tags=["casos"])


# ============================================================================
# HELPERS
# ============================================================================

def _verificar_acceso_casos(current_user: Usuario) -> None:
    """Verifica que el usuario tenga acceso al módulo de Casos, o lanza 403."""
    if current_user.email.lower() in [email.lower() for email in USUARIOS_ACCESO_CASOS]:
        return
    logger.warning(f"Usuario ID: {current_user.id} intentó acceder a casos sin permiso")
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a casos legales"
    )


def _es_usuario_filtrado(current_user: Usuario) -> bool:
    """Retorna True si el usuario solo puede ver sus propios casos."""
    return current_user.email.lower() in [email.lower() for email in USUARIOS_FILTRO_CASOS]


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/", response_model=CasoList)
def listar_casos(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    prioridad: Optional[str] = Query(None, description="Filtrar por prioridad"),
    limit: int = Query(20, ge=1, le=100, description="Máximo de resultados"),
    offset: int = Query(0, ge=0, description="Desplazamiento para paginación"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista casos según permisos del usuario."""
    _verificar_acceso_casos(current_user)

    responsable_id = current_user.id if _es_usuario_filtrado(current_user) else None

    try:
        return casos_service.listar_casos(
            db,
            responsable_id=responsable_id,
            estado=estado,
            prioridad=prioridad,
            limit=limit,
            offset=offset,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{caso_id}", response_model=CasoResponse)
def obtener_caso(
    caso_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene un caso por su ID."""
    _verificar_acceso_casos(current_user)

    try:
        caso_uuid = UUID(caso_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"ID de caso inválido: {caso_id}. Formato esperado: UUID"
        )

    caso = casos_service.obtener_caso(db, caso_uuid)
    if caso is None:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    if _es_usuario_filtrado(current_user) and caso.responsable_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para acceder a este caso")

    return caso


@router.post("/", response_model=CasoResponse, status_code=201)
def crear_caso(
    data: CasoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea un nuevo caso. Si se envía IUE, busca o crea el expediente."""
    _verificar_acceso_casos(current_user)

    expediente_id = data.expediente_id

    if data.iue:
        iue = data.iue.strip()
        expediente = db.query(Expediente).filter(
            Expediente.iue == iue,
            Expediente.deleted_at.is_(None)
        ).first()

        if not expediente:
            try:
                expediente, _ = expediente_service.sincronizar_expediente(
                    db=db, iue=iue, responsable_id=str(current_user.id)
                )
                if not expediente:
                    raise HTTPException(
                        status_code=400,
                        detail=f"El IUE '{iue}' no fue encontrado en el Poder Judicial."
                    )
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"No se pudo crear el expediente {iue}: {e}")

        expediente_id = expediente.id
        if not expediente.responsable_id:
            expediente.responsable_id = current_user.id
            db.commit()

    caso = casos_service.crear_caso(
        db,
        titulo=data.titulo,
        estado=data.estado,
        prioridad=data.prioridad,
        responsable_id=current_user.id,
        fecha_vencimiento=data.fecha_vencimiento,
        expediente_id=expediente_id,
    )

    logger.info(f"Caso creado: {caso.id} - Usuario ID: {current_user.id}")
    return caso


@router.put("/{caso_id}", response_model=CasoResponse)
def actualizar_caso(
    caso_id: str,
    data: CasoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza un caso existente."""
    _verificar_acceso_casos(current_user)

    try:
        caso_uuid = UUID(caso_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"ID de caso inválido: {caso_id}")

    caso = casos_service.obtener_caso(db, caso_uuid)
    if caso is None:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    if _es_usuario_filtrado(current_user) and caso.responsable_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para actualizar este caso")

    update_data = data.model_dump(exclude_unset=True)
    caso = casos_service.actualizar_caso(db, caso, update_data)

    logger.info(f"Caso actualizado: {caso.id} - Usuario ID: {current_user.id}")
    return caso


@router.delete("/{caso_id}")
def eliminar_caso(
    caso_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina un caso (soft delete)."""
    _verificar_acceso_casos(current_user)

    try:
        caso_uuid = UUID(caso_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"ID de caso inválido: {caso_id}")

    caso = casos_service.obtener_caso(db, caso_uuid)
    if caso is None:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    if _es_usuario_filtrado(current_user) and caso.responsable_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar este caso")

    casos_service.eliminar_caso(db, caso)

    logger.info(f"Caso eliminado (soft delete): {caso.id} - Usuario ID: {current_user.id}")
    return {"mensaje": f"Caso '{caso.titulo}' eliminado", "id": str(caso.id)}
