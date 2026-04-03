"""API para consulta y gestión de jurisprudencia."""

import logging
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.access_control import USUARIOS_ACCESO_JURISPRUDENCIA, tiene_acceso
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Usuario
from app.models.sentencia import Sentencia
from app.schemas.sentencia import (
    BusquedaResponse,
    SentenciaCompleta,
    SentenciaListResponse,
    SentenciaResumen,
)
from app.services import jurisprudencia_service

logger = logging.getLogger(__name__)

router = APIRouter()


def _verificar_acceso_jurisprudencia(current_user: Usuario) -> None:
    """Valida acceso al módulo de jurisprudencia."""
    if not current_user.es_socio and not tiene_acceso(
        current_user.email,
        USUARIOS_ACCESO_JURISPRUDENCIA,
    ):
        raise HTTPException(
            status_code=403,
            detail="Sin acceso al módulo de Jurisprudencia",
        )


def _to_resumen(sentencia: Sentencia) -> SentenciaResumen:
    """Convierte una sentencia ORM a schema resumido."""
    sentencia_resumen = SentenciaResumen.model_validate(sentencia)
    sentencia_resumen.tiene_resumen_ia = sentencia.resumen_ia is not None
    return sentencia_resumen


@router.get("/buscar", response_model=BusquedaResponse)
def buscar_sentencias(
    q: str = Query(..., description="Texto a buscar"),
    limit: int = Query(20, ge=1, le=100, description="Máximo de resultados"),
    offset: int = Query(0, ge=0, description="Desplazamiento para paginación"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Busca sentencias por texto libre."""
    _verificar_acceso_jurisprudencia(current_user)

    resultado = jurisprudencia_service.buscar_sentencias(db, q, limit, offset)
    return BusquedaResponse(
        total=resultado["total"],
        sentencias=[_to_resumen(sentencia) for sentencia in resultado["sentencias"]],
        query=resultado["query"],
        limit=resultado["limit"],
        offset=resultado["offset"],
    )


@router.get("/", response_model=SentenciaListResponse)
def listar_sentencias(
    limit: int = Query(20, ge=1, le=100, description="Máximo de resultados"),
    offset: int = Query(0, ge=0, description="Desplazamiento para paginación"),
    materia: Optional[str] = Query(None, description="Filtrar por materia"),
    sede: Optional[str] = Query(None, description="Filtrar por sede"),
    fecha_desde: Optional[date] = Query(None, description="Filtrar desde fecha"),
    fecha_hasta: Optional[date] = Query(None, description="Filtrar hasta fecha"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Lista sentencias con filtros opcionales."""
    _verificar_acceso_jurisprudencia(current_user)

    resultado = jurisprudencia_service.listar_sentencias(
        db=db,
        limit=limit,
        offset=offset,
        materia=materia,
        sede=sede,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    return SentenciaListResponse(
        total=resultado["total"],
        sentencias=[_to_resumen(sentencia) for sentencia in resultado["sentencias"]],
        limit=resultado["limit"],
        offset=resultado["offset"],
    )


@router.get("/bjn/{bjn_id}", response_model=SentenciaCompleta)
def obtener_sentencia_por_bjn_id(
    bjn_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Obtiene una sentencia por su identificador BJN."""
    _verificar_acceso_jurisprudencia(current_user)

    sentencia = jurisprudencia_service.obtener_por_bjn_id(db, bjn_id)
    if sentencia is None:
        raise HTTPException(status_code=404, detail="Sentencia no encontrada")

    return SentenciaCompleta.model_validate(sentencia)


@router.get("/{sentencia_id}", response_model=SentenciaCompleta)
def obtener_sentencia(
    sentencia_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Obtiene una sentencia completa por ID."""
    _verificar_acceso_jurisprudencia(current_user)

    sentencia = jurisprudencia_service.obtener_sentencia(db, sentencia_id)
    if sentencia is None:
        raise HTTPException(status_code=404, detail="Sentencia no encontrada")

    return SentenciaCompleta.model_validate(sentencia)


@router.delete("/{sentencia_id}")
def eliminar_sentencia(
    sentencia_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Realiza soft delete de una sentencia."""
    _verificar_acceso_jurisprudencia(current_user)
    if not current_user.es_socio:
        raise HTTPException(
            status_code=403,
            detail="Solo socios pueden eliminar sentencias",
        )

    eliminada = jurisprudencia_service.eliminar_sentencia(db, sentencia_id)
    if not eliminada:
        raise HTTPException(status_code=404, detail="Sentencia no encontrada")

    logger.info("Sentencia eliminada: %s por usuario %s", sentencia_id, current_user.id)
    return {"mensaje": "Sentencia eliminada", "id": str(sentencia_id)}
