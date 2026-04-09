"""
Servicio para gestión de trámites DGR en base de datos.

Encapsula queries y lógica de negocio del módulo Trámites DGR.
El scraping real está en dgr_service.py (consultar_tramite_dgr).
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.tramite_dgr import TramiteDgr
from app.schemas.tramite_dgr import REGISTROS_DGR, OFICINAS_DGR

logger = logging.getLogger(__name__)


def verificar_duplicado(
    db: Session,
    registro: str,
    oficina: str,
    anio: int,
    numero_entrada: int,
    bis: str = "",
) -> Optional[TramiteDgr]:
    """Busca un trámite existente con los mismos datos de identificación."""
    return db.query(TramiteDgr).filter(
        TramiteDgr.registro == registro,
        TramiteDgr.oficina == oficina,
        TramiteDgr.anio == anio,
        TramiteDgr.numero_entrada == numero_entrada,
        TramiteDgr.bis == bis,
        TramiteDgr.deleted_at.is_(None),
    ).first()


def crear_tramite(
    db: Session,
    registro: str,
    oficina: str,
    anio: int,
    numero_entrada: int,
    responsable_id: UUID,
    bis: str = "",
) -> TramiteDgr:
    """Crea un nuevo trámite DGR en BD."""
    tramite = TramiteDgr(
        registro=registro,
        oficina=oficina,
        anio=anio,
        numero_entrada=numero_entrada,
        bis=bis,
        responsable_id=responsable_id,
        registro_nombre=REGISTROS_DGR.get(registro),
        oficina_nombre=OFICINAS_DGR.get(oficina),
    )
    db.add(tramite)
    db.flush()
    return tramite


def aplicar_datos_dgr(tramite: TramiteDgr, datos: dict) -> None:
    """Aplica datos obtenidos de la DGR al modelo del trámite."""
    fecha_str = datos.get("fecha_ingreso")
    if fecha_str:
        try:
            tramite.fecha_ingreso = datetime.strptime(fecha_str, "%d/%m/%y").date()
        except (ValueError, TypeError):
            pass

    tramite.escribano_emisor = datos.get("escribano_emisor")
    tramite.estado_actual = datos.get("estado_actual")
    tramite.observaciones = datos.get("observaciones")

    inscripciones = datos.get("inscripciones")
    if inscripciones:
        tramite.actos = json.dumps(inscripciones, ensure_ascii=False)

    tramite.ultimo_chequeo = datetime.now(timezone.utc)


def obtener_tramite(
    db: Session,
    tramite_id: UUID,
) -> Optional[TramiteDgr]:
    """Obtiene un trámite por ID (no eliminado)."""
    return db.query(TramiteDgr).filter(
        TramiteDgr.id == tramite_id,
        TramiteDgr.deleted_at.is_(None),
    ).first()


def listar_tramites(
    db: Session,
    responsable_id: Optional[UUID] = None,
    activo: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """Lista trámites con filtros opcionales."""
    if responsable_id:
        base_query = db.query(TramiteDgr).filter(
            TramiteDgr.responsable_id == responsable_id,
            TramiteDgr.deleted_at.is_(None),
        )
    else:
        base_query = db.query(TramiteDgr).filter(
            TramiteDgr.deleted_at.is_(None),
        )

    if activo is not None:
        base_query = base_query.filter(TramiteDgr.activo == activo)

    total = base_query.count()
    tramites = base_query.order_by(TramiteDgr.created_at.desc()).offset(offset).limit(limit).all()

    return {"total": total, "tramites": tramites}


def listar_pendientes(db: Session) -> List[TramiteDgr]:
    """Lista trámites con cambios detectados sin notificar."""
    return db.query(TramiteDgr).filter(
        TramiteDgr.cambio_detectado == True,
        TramiteDgr.deleted_at.is_(None),
    ).order_by(TramiteDgr.ultimo_chequeo.desc()).all()


def marcar_notificados(db: Session, ids: List[UUID]) -> int:
    """Marca trámites como notificados. Retorna cantidad actualizada."""
    actualizados = 0
    for tramite_id in ids:
        tramite = db.query(TramiteDgr).filter(
            TramiteDgr.id == tramite_id,
            TramiteDgr.deleted_at.is_(None),
        ).first()
        if tramite:
            tramite.cambio_detectado = False
            actualizados += 1
    db.commit()
    return actualizados


def detectar_cambio_estado(tramite: TramiteDgr, estado_nuevo: Optional[str]) -> bool:
    """Compara estado nuevo con actual, marca cambio si difiere. Retorna True si cambió."""
    if estado_nuevo and estado_nuevo != tramite.estado_actual:
        tramite.estado_anterior = tramite.estado_actual
        tramite.cambio_detectado = True
        return True
    return False


def eliminar_tramite(db: Session, tramite: TramiteDgr) -> None:
    """Soft delete de un trámite."""
    tramite.deleted_at = datetime.now(timezone.utc)
    tramite.activo = False
    db.commit()
