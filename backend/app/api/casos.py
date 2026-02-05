"""
API para gestión de casos legales.

Endpoints CRUD para casos legales.
Solo 4 usuarios tienen acceso: Bruno (ve todos), Gonzalo, Pancho, Gerardo (ven solo suyos).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone
from uuid import UUID
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Usuario
from app.models.caso import Caso
from app.models.expediente import Expediente
from app.services import expediente_service
from app.schemas.caso import CasoCreate, CasoUpdate, CasoResponse, CasoList

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/casos", tags=["casos"])


# ============================================================================
# CONFIGURACIÓN DE ACCESO
# ============================================================================

# Usuarios con acceso al módulo de Casos (SOLO estos 4)
USUARIOS_ACCESO_CASOS = [
    "bgandolfo@cgmasociados.com",  # Bruno
    "gtaborda@grupoconexion.uy",   # Gonzalo
    "falgorta@grupoconexion.uy",   # Pancho
    "gferrari@grupoconexion.uy",   # Gerardo
]

# Usuarios que solo ven casos donde ellos son el responsable
# Bruno NO está en esta lista → ve todos
USUARIOS_FILTRO_CASOS = [
    "gtaborda@grupoconexion.uy",
    "falgorta@grupoconexion.uy",
    "gferrari@grupoconexion.uy",
]


# ============================================================================
# HELPERS
# ============================================================================

def _verificar_acceso_casos(current_user: Usuario) -> None:
    """Verifica que el usuario tenga acceso al módulo de Casos, o lanza 403."""
    if current_user.email.lower() in [email.lower() for email in USUARIOS_ACCESO_CASOS]:
        return
    logger.warning(f"Usuario {current_user.email} intentó acceder a casos sin permiso")
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a casos legales"
    )


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
    """
    Lista casos según permisos del usuario.
    
    - Bruno: ve todos los casos
    - Gonzalo, Pancho, Gerardo: ven solo sus casos (responsable_id = current_user.id)
    Filtros opcionales por estado y prioridad.
    """
    _verificar_acceso_casos(current_user)
    
    logger.info(f"Listando casos - Usuario: {current_user.email}")
    
    # Query base: casos no eliminados
    query = db.query(Caso).filter(
        Caso.deleted_at.is_(None)
    )
    
    # Filtrar por responsable solo si el usuario está en USUARIOS_FILTRO_CASOS
    if current_user.email.lower() in [email.lower() for email in USUARIOS_FILTRO_CASOS]:
        query = query.filter(Caso.responsable_id == current_user.id)
    
    # Filtros opcionales
    if estado:
        try:
            from app.models.caso import EstadoCaso
            estado_enum = EstadoCaso(estado)
            query = query.filter(Caso.estado == estado_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Estado inválido: {estado}. Valores válidos: pendiente, en_proceso, requiere_accion, cerrado"
            )
    
    if prioridad:
        try:
            from app.models.caso import PrioridadCaso
            prioridad_enum = PrioridadCaso(prioridad)
            query = query.filter(Caso.prioridad == prioridad_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Prioridad inválida: {prioridad}. Valores válidos: critica, alta, media, baja"
            )
    
    # Contar total (sin paginación)
    total = query.count()
    
    # Aplicar paginación y ordenar por fecha de creación (más recientes primero)
    casos = query.order_by(Caso.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "casos": casos
    }


@router.get("/{caso_id}", response_model=CasoResponse)
def obtener_caso(
    caso_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene un caso por su ID.
    
    - Bruno: puede ver cualquier caso
    - Gonzalo, Pancho, Gerardo: solo pueden ver casos donde son responsables
    """
    _verificar_acceso_casos(current_user)
    
    logger.info(f"Obteniendo caso {caso_id} - Usuario: {current_user.email}")
    
    try:
        caso_uuid = UUID(caso_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"ID de caso inválido: {caso_id}. Formato esperado: UUID"
        )
    
    caso = db.query(Caso).filter(
        Caso.id == caso_uuid,
        Caso.deleted_at.is_(None)
    ).first()
    
    if caso is None:
        raise HTTPException(
            status_code=404,
            detail="Caso no encontrado"
        )
    
    # Verificar permisos: si el usuario está en USUARIOS_FILTRO_CASOS, solo puede ver sus casos
    if current_user.email.lower() in [email.lower() for email in USUARIOS_FILTRO_CASOS]:
        if caso.responsable_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para acceder a este caso"
            )
    
    return caso


@router.post("/", response_model=CasoResponse, status_code=201)
def crear_caso(
    data: CasoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crea un nuevo caso.
    
    El responsable_id del caso se establece automáticamente como current_user.id.
    Si se envía "iue", se busca o crea el expediente y se asocia al caso.
    """
    _verificar_acceso_casos(current_user)
    
    logger.info(f"Creando caso - Usuario: {current_user.email}")
    
    # Manejar vinculación con expediente por IUE
    expediente_id = data.expediente_id  # Por compatibilidad
    
    if data.iue:
        iue = data.iue.strip()
        # Buscar expediente existente
        expediente = db.query(Expediente).filter(
            Expediente.iue == iue,
            Expediente.deleted_at.is_(None)
        ).first()
        
        if not expediente:
            # Crear expediente automáticamente
            try:
                expediente, nuevos_movimientos = expediente_service.sincronizar_expediente(
                    db=db,
                    iue=iue,
                    responsable_id=str(current_user.id)
                )
                # Validar que se encontró en el Poder Judicial
                if not expediente:
                    raise HTTPException(
                        status_code=400,
                        detail=f"El IUE '{iue}' no fue encontrado en el Poder Judicial. Verifique el formato (ej: 2-12345/2023)"
                    )
                logger.info(f"Expediente creado automáticamente: {iue} con {nuevos_movimientos} movimientos")
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error al crear expediente {iue}: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"No se pudo crear el expediente {iue}: {str(e)}"
                )
        
        expediente_id = expediente.id
        # Asegurar que el expediente tenga responsable
        if not expediente.responsable_id:
            expediente.responsable_id = current_user.id
            db.commit()
    
    # Crear caso
    caso = Caso(
        titulo=data.titulo,
        estado=data.estado,
        prioridad=data.prioridad,
        fecha_vencimiento=data.fecha_vencimiento,
        responsable_id=current_user.id,
        expediente_id=expediente_id
    )
    
    db.add(caso)
    db.commit()
    db.refresh(caso)
    
    logger.info(f"Caso creado: {caso.id} - Usuario: {current_user.email}")
    
    return caso


@router.put("/{caso_id}", response_model=CasoResponse)
def actualizar_caso(
    caso_id: str,
    data: CasoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualiza un caso existente.
    
    - Bruno: puede actualizar cualquier caso
    - Gonzalo, Pancho, Gerardo: solo pueden actualizar casos donde son responsables
    Si se envía responsable_id en el update, se ignora.
    """
    _verificar_acceso_casos(current_user)
    
    logger.info(f"Actualizando caso {caso_id} - Usuario: {current_user.email}")
    
    try:
        caso_uuid = UUID(caso_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"ID de caso inválido: {caso_id}. Formato esperado: UUID"
        )
    
    caso = db.query(Caso).filter(
        Caso.id == caso_uuid,
        Caso.deleted_at.is_(None)
    ).first()
    
    if caso is None:
        raise HTTPException(
            status_code=404,
            detail="Caso no encontrado"
        )
    
    # Verificar permisos: si el usuario está en USUARIOS_FILTRO_CASOS, solo puede actualizar sus casos
    if current_user.email.lower() in [email.lower() for email in USUARIOS_FILTRO_CASOS]:
        if caso.responsable_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para actualizar este caso"
            )
    
    # Actualizar solo los campos proporcionados
    update_data = data.model_dump(exclude_unset=True)
    
    # Ignorar responsable_id si se envía (siempre es el usuario actual)
    update_data.pop('responsable_id', None)
    
    for field, value in update_data.items():
        if value is not None:
            setattr(caso, field, value)
    
    caso.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(caso)
    
    logger.info(f"Caso actualizado: {caso.id} - Usuario: {current_user.email}")
    
    return caso


@router.delete("/{caso_id}")
def eliminar_caso(
    caso_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Elimina un caso (soft delete).
    
    - Bruno: puede eliminar cualquier caso
    - Gonzalo, Pancho, Gerardo: solo pueden eliminar casos donde son responsables
    El caso se marca como eliminado pero no se borra físicamente de la BD.
    """
    _verificar_acceso_casos(current_user)
    
    logger.info(f"Eliminando caso {caso_id} - Usuario: {current_user.email}")
    
    try:
        caso_uuid = UUID(caso_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"ID de caso inválido: {caso_id}. Formato esperado: UUID"
        )
    
    caso = db.query(Caso).filter(
        Caso.id == caso_uuid,
        Caso.deleted_at.is_(None)
    ).first()
    
    if caso is None:
        raise HTTPException(
            status_code=404,
            detail="Caso no encontrado"
        )
    
    # Verificar permisos: si el usuario está en USUARIOS_FILTRO_CASOS, solo puede eliminar sus casos
    if current_user.email.lower() in [email.lower() for email in USUARIOS_FILTRO_CASOS]:
        if caso.responsable_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para eliminar este caso"
            )
    
    # Soft delete
    caso.deleted_at = datetime.now(timezone.utc)
    db.commit()
    
    logger.info(f"Caso eliminado (soft delete): {caso.id} - Usuario: {current_user.email}")
    
    return {
        "mensaje": f"Caso '{caso.titulo}' eliminado",
        "id": str(caso.id)
    }
