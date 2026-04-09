"""
Servicio para gestión de contratos notariales.

Encapsula queries y lógica de negocio del módulo Contratos.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.models.contrato import Contrato

logger = logging.getLogger(__name__)


def listar_categorias(db: Session) -> List[str]:
    """Lista todas las categorías únicas de contratos activos."""
    categorias = db.query(Contrato.categoria).filter(
        Contrato.deleted_at.is_(None),
        Contrato.activo == True,
    ).distinct().all()
    return sorted([cat[0] for cat in categorias])


def listar_contratos(
    db: Session,
    q: Optional[str] = None,
    categoria: Optional[str] = None,
    activo: Optional[bool] = True,
    skip: int = 0,
    limit: int = 50,
) -> Dict[str, Any]:
    """
    Lista contratos con filtros y paginación.

    Returns:
        {"contratos": list[Contrato], "total": int, "categorias": list[str]}
    """
    query = db.query(Contrato).filter(Contrato.deleted_at.is_(None))

    if activo is not None:
        query = query.filter(Contrato.activo == activo)

    if categoria:
        query = query.filter(Contrato.categoria == categoria)

    if q:
        q_lower = f"%{q.lower()}%"
        query = query.filter(
            or_(
                func.lower(Contrato.titulo).like(q_lower),
                func.lower(Contrato.contenido_texto).like(q_lower),
            )
        )

    total = query.count()
    contratos = query.order_by(Contrato.titulo).offset(skip).limit(limit).all()
    categorias = listar_categorias(db)

    return {"contratos": contratos, "total": total, "categorias": categorias}


def buscar_contratos(
    db: Session,
    q: str,
    categoria: Optional[str] = None,
    limit: int = 20,
) -> List[Contrato]:
    """Búsqueda full-text en título y contenido."""
    query = db.query(Contrato).filter(
        Contrato.deleted_at.is_(None),
        Contrato.activo == True,
    )

    if categoria:
        query = query.filter(Contrato.categoria == categoria)

    q_lower = f"%{q.lower()}%"
    query = query.filter(
        or_(
            func.lower(Contrato.titulo).like(q_lower),
            func.lower(Contrato.contenido_texto).like(q_lower),
        )
    )

    return query.order_by(
        func.lower(Contrato.titulo).like(q_lower).desc(),
        Contrato.titulo,
    ).limit(limit).all()


def obtener_contrato(db: Session, contrato_id: UUID) -> Optional[Contrato]:
    """Obtiene un contrato por ID (no eliminado)."""
    return db.query(Contrato).filter(
        Contrato.id == contrato_id,
        Contrato.deleted_at.is_(None),
    ).first()


def crear_contrato(db: Session, **kwargs) -> Contrato:
    """Crea un contrato nuevo y lo persiste."""
    contrato = Contrato(**kwargs)
    db.add(contrato)
    db.commit()
    db.refresh(contrato)
    return contrato


def actualizar_contrato(db: Session, contrato: Contrato, update_data: dict) -> Contrato:
    """Actualiza campos de un contrato existente."""
    for field, value in update_data.items():
        setattr(contrato, field, value)
    db.commit()
    db.refresh(contrato)
    return contrato


def eliminar_contrato(db: Session, contrato: Contrato) -> None:
    """Soft delete de un contrato."""
    contrato.deleted_at = datetime.now(timezone.utc)
    db.commit()


def obtener_contratos_para_extraccion(
    db: Session,
    solo_sin_campos: bool = True,
    max_intentos: int = 2,
    limite: int = 10,
) -> List[Contrato]:
    """Obtiene contratos pendientes de extracción de campos."""
    query = db.query(Contrato).filter(
        Contrato.deleted_at.is_(None),
        Contrato.activo == True,
        Contrato.contenido_texto.isnot(None),
        Contrato.requiere_procesamiento_manual == False,
        Contrato.intentos_extraccion < max_intentos,
    )

    if solo_sin_campos:
        query = query.filter(Contrato.campos_editables.is_(None))

    return query.limit(limite).all()


def contar_contratos_agotados(db: Session, max_intentos: int = 2) -> int:
    """Cuenta contratos que agotaron intentos de extracción."""
    return db.query(Contrato).filter(
        Contrato.deleted_at.is_(None),
        Contrato.activo == True,
        Contrato.campos_editables.is_(None),
        Contrato.intentos_extraccion >= max_intentos,
    ).count()
