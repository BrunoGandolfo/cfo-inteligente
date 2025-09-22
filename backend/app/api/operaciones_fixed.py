from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.models.operacion import Operacion
from app.schemas.operacion import OperacionResponse
import uuid

router = APIRouter()

@router.get("/", response_model=List[dict])
def listar_operaciones(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Listar operaciones con área incluida"""
    operaciones = db.query(Operacion)\
        .options(joinedload(Operacion.area))\
        .filter(Operacion.deleted_at.is_(None))\
        .order_by(desc(Operacion.fecha), desc(Operacion.created_at))\
        .limit(limit)\
        .offset(offset)\
        .all()
    
    # Formatear respuesta incluyendo área
    result = []
    for op in operaciones:
        result.append({
            "id": str(op.id),
            "tipo_operacion": op.tipo_operacion.value,
            "fecha": op.fecha.isoformat(),
            "monto_original": float(op.monto_original),
            "moneda_original": op.moneda_original.value,
            "tipo_cambio": float(op.tipo_cambio),
            "monto_uyu": float(op.monto_uyu),
            "monto_usd": float(op.monto_usd),
            "area": {
                "id": str(op.area.id),
                "nombre": op.area.nombre
            } if op.area else None,
            "localidad": op.localidad.value if op.localidad else None,
            "cliente": op.cliente,
            "proveedor": op.proveedor,
            "descripcion": op.descripcion,
            "created_at": op.created_at.isoformat() if op.created_at else None
        })
    
    return result

@router.patch("/{operacion_id}/anular")
def anular_operacion(
    operacion_id: str,
    db: Session = Depends(get_db)
):
    """Anular operación (soft delete)"""
    try:
        # Convertir string a UUID
        op_uuid = uuid.UUID(operacion_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    operacion = db.query(Operacion).filter(
        Operacion.id == op_uuid,
        Operacion.deleted_at.is_(None)
    ).first()
    
    if not operacion:
        raise HTTPException(status_code=404, detail="Operación no encontrada")
    
    # Soft delete
    operacion.deleted_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Operación anulada exitosamente"}
