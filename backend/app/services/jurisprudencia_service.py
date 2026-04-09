"""
Servicio de lógica de negocio para jurisprudencia (sentencias del BJN).

Búsqueda full-text en español, filtros por materia/sede/fecha,
CRUD con soft delete y actualización de resúmenes IA.
"""

import uuid
from datetime import datetime, timezone, date
from typing import Optional, Dict, List, Any

from sqlalchemy import func, text, desc
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.logger import get_logger
from app.models.sentencia import Sentencia

logger = get_logger(__name__)


def buscar_sentencias(
    db: Session,
    query: str,
    limit: int = 20,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    Búsqueda combinada: full-text en español sobre texto_completo
    + ILIKE en numero, sede, abstract y coincidencia en materias.

    Primero ranquea resultados full-text por ts_rank, luego agrega
    coincidencias ILIKE que no estén ya incluidas.
    """
    if not query or not query.strip():
        return {"total": 0, "sentencias": [], "query": query, "limit": limit, "offset": offset}

    query_limpio = query.strip()
    patron = f"%{query_limpio}%"

    # --- Full-text search ---
    tsvector = func.to_tsvector("spanish", func.coalesce(Sentencia.texto_completo, ""))
    tsquery = func.plainto_tsquery("spanish", query_limpio)
    rank = func.ts_rank(tsvector, tsquery).label("rank")

    ft_query = (
        db.query(Sentencia, rank)
        .filter(
            Sentencia.deleted_at.is_(None),
            tsvector.op("@@")(tsquery),
        )
        .order_by(desc("rank"))
    )
    ft_results = ft_query.all()
    ft_sentencias = [row[0] for row in ft_results]
    ft_ids = {s.id for s in ft_sentencias}

    # --- ILIKE fallback en campos cortos ---
    ilike_query = (
        db.query(Sentencia)
        .filter(
            Sentencia.deleted_at.is_(None),
            ~Sentencia.id.in_(ft_ids) if ft_ids else True,
        )
        .filter(
            (Sentencia.numero.ilike(patron))
            | (Sentencia.sede.ilike(patron))
            | (Sentencia.abstract.ilike(patron))
            | (Sentencia.materias.any(query_limpio))
        )
    )
    ilike_sentencias = ilike_query.all()

    # Combinar: full-text primero, luego ILIKE extras
    combinadas = ft_sentencias + ilike_sentencias
    total = len(combinadas)

    # Aplicar paginación sobre el resultado combinado
    pagina = combinadas[offset : offset + limit]

    return {
        "total": total,
        "sentencias": pagina,
        "query": query_limpio,
        "limit": limit,
        "offset": offset,
    }


def obtener_sentencia(
    db: Session,
    sentencia_id: uuid.UUID,
) -> Optional[Sentencia]:
    """Obtiene una sentencia por ID, excluyendo eliminadas."""
    return (
        db.query(Sentencia)
        .filter(Sentencia.id == sentencia_id, Sentencia.deleted_at.is_(None))
        .first()
    )


def obtener_por_bjn_id(
    db: Session,
    bjn_id: str,
) -> Optional[Sentencia]:
    """Obtiene una sentencia por su identificador único del BJN."""
    return (
        db.query(Sentencia)
        .filter(Sentencia.bjn_id == bjn_id, Sentencia.deleted_at.is_(None))
        .first()
    )


def listar_sentencias(
    db: Session,
    limit: int = 20,
    offset: int = 0,
    materia: Optional[str] = None,
    sede: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> Dict[str, Any]:
    """
    Lista sentencias con filtros opcionales.

    Ordenadas por fecha DESC NULLS LAST.
    """
    query = db.query(Sentencia).filter(Sentencia.deleted_at.is_(None))

    if materia:
        query = query.filter(Sentencia.materias.any(materia))

    if sede:
        query = query.filter(Sentencia.sede.ilike(f"%{sede}%"))

    if fecha_desde:
        query = query.filter(Sentencia.fecha >= fecha_desde)

    if fecha_hasta:
        query = query.filter(Sentencia.fecha <= fecha_hasta)

    total = query.count()

    sentencias = (
        query.order_by(Sentencia.fecha.desc().nullslast())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "sentencias": sentencias,
        "limit": limit,
        "offset": offset,
    }


def crear_sentencia(
    db: Session,
    datos: Dict[str, Any],
) -> Sentencia:
    """
    Crea una sentencia nueva. Si ya existe una con el mismo bjn_id,
    retorna la existente (upsert por bjn_id).
    """
    bjn_id = datos.get("bjn_id")

    # Upsert: si ya existe por bjn_id, retornar la existente
    if bjn_id:
        existente = (
            db.query(Sentencia)
            .filter(Sentencia.bjn_id == bjn_id, Sentencia.deleted_at.is_(None))
            .first()
        )
        if existente:
            logger.info(f"Sentencia ya existe con bjn_id={bjn_id}, retornando existente")
            return existente

    sentencia = Sentencia(**datos)
    try:
        db.add(sentencia)
        db.flush()
        db.commit()
        db.refresh(sentencia)
        logger.info(f"Sentencia creada: {sentencia.id} (bjn_id={bjn_id})")
        return sentencia
    except IntegrityError:
        db.rollback()
        # Race condition: otra transacción insertó el mismo bjn_id
        if bjn_id:
            existente = (
                db.query(Sentencia)
                .filter(Sentencia.bjn_id == bjn_id)
                .first()
            )
            if existente:
                logger.warning(f"IntegrityError en bjn_id={bjn_id}, retornando existente")
                return existente
        raise


def actualizar_resumen(
    db: Session,
    sentencia_id: uuid.UUID,
    resumen: str,
) -> Optional[Sentencia]:
    """Actualiza resumen_ia y resumen_generado_at de una sentencia."""
    sentencia = (
        db.query(Sentencia)
        .filter(Sentencia.id == sentencia_id, Sentencia.deleted_at.is_(None))
        .first()
    )
    if sentencia is None:
        return None

    sentencia.resumen_ia = resumen
    sentencia.resumen_generado_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(sentencia)
    logger.info(f"Resumen actualizado para sentencia {sentencia_id}")
    return sentencia


def eliminar_sentencia(
    db: Session,
    sentencia_id: uuid.UUID,
) -> bool:
    """Soft delete: setea deleted_at. Retorna True si se eliminó."""
    sentencia = (
        db.query(Sentencia)
        .filter(Sentencia.id == sentencia_id, Sentencia.deleted_at.is_(None))
        .first()
    )
    if sentencia is None:
        return False

    sentencia.deleted_at = datetime.now(timezone.utc)
    db.commit()
    logger.info(f"Sentencia eliminada (soft delete): {sentencia_id}")
    return True
