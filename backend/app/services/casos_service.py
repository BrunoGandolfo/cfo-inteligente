"""
Servicio para gestión de casos legales.

Encapsula queries y lógica de negocio del módulo Casos.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.caso import Caso, EstadoCaso, PrioridadCaso

logger = logging.getLogger(__name__)


def listar_casos(
    db: Session,
    responsable_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    Lista casos con filtros opcionales.

    Args:
        responsable_id: Si se pasa, filtra por responsable (para colaboradores).
        estado: Filtro por estado (pendiente, en_proceso, requiere_accion, cerrado).
        prioridad: Filtro por prioridad (critica, alta, media, baja).

    Returns:
        {"total": int, "casos": list[Caso]}

    Raises:
        ValueError: si estado o prioridad son inválidos.
    """
    query = db.query(Caso).filter(Caso.deleted_at.is_(None))

    if responsable_id:
        query = query.filter(Caso.responsable_id == responsable_id)

    if estado:
        try:
            estado_enum = EstadoCaso(estado)
            query = query.filter(Caso.estado == estado_enum)
        except ValueError:
            raise ValueError(
                f"Estado inválido: {estado}. "
                "Valores válidos: pendiente, en_proceso, requiere_accion, cerrado"
            )

    if prioridad:
        try:
            prioridad_enum = PrioridadCaso(prioridad)
            query = query.filter(Caso.prioridad == prioridad_enum)
        except ValueError:
            raise ValueError(
                f"Prioridad inválida: {prioridad}. "
                "Valores válidos: critica, alta, media, baja"
            )

    total = query.count()
    casos = query.order_by(Caso.created_at.desc()).offset(offset).limit(limit).all()

    return {"total": total, "casos": casos}


def obtener_caso(db: Session, caso_id: UUID) -> Optional[Caso]:
    """Obtiene un caso por ID (no eliminado)."""
    return db.query(Caso).filter(
        Caso.id == caso_id,
        Caso.deleted_at.is_(None),
    ).first()


def crear_caso(
    db: Session,
    titulo: str,
    estado: str,
    prioridad: str,
    responsable_id: UUID,
    fecha_vencimiento=None,
    expediente_id: Optional[UUID] = None,
) -> Caso:
    """Crea un nuevo caso y lo persiste."""
    caso = Caso(
        titulo=titulo,
        estado=estado,
        prioridad=prioridad,
        fecha_vencimiento=fecha_vencimiento,
        responsable_id=responsable_id,
        expediente_id=expediente_id,
    )
    db.add(caso)
    db.commit()
    db.refresh(caso)
    return caso


def actualizar_caso(db: Session, caso: Caso, update_data: dict) -> Caso:
    """Actualiza campos de un caso existente."""
    update_data.pop("responsable_id", None)

    for field, value in update_data.items():
        if value is not None:
            setattr(caso, field, value)

    caso.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(caso)
    return caso


def eliminar_caso(db: Session, caso: Caso) -> None:
    """Soft delete de un caso."""
    caso.deleted_at = datetime.now(timezone.utc)
    db.commit()
