from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.models.operacion import Operacion
from app.models.area import Area
from app.models.socio import Socio
from app.models.cliente import Cliente
from app.models.proveedor import Proveedor
from app.schemas.operacion import (
    IngresoCreate, GastoCreate, RetiroCreate, DistribucionCreate
)
from app.services import operacion_service
import uuid

router = APIRouter()

@router.get("/")
def get_operaciones(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100)
):
    """Listar operaciones con todos los campos necesarios"""
    operaciones = db.query(Operacion)\
        .options(joinedload(Operacion.area))\
        .filter(Operacion.deleted_at.is_(None))\
        .order_by(desc(Operacion.fecha), desc(Operacion.created_at))\
        .limit(limit)\
        .all()
    
    result = []
    for op in operaciones:
        result.append({
            "id": str(op.id),
            "tipo_operacion": op.tipo_operacion.value if op.tipo_operacion else None,
            "fecha": op.fecha.isoformat() if op.fecha else None,
            "monto_original": float(op.monto_original) if op.monto_original else 0,
            "moneda_original": op.moneda_original.value if op.moneda_original else None,
            "tipo_cambio": float(op.tipo_cambio) if op.tipo_cambio else 0,
            "monto_uyu": float(op.monto_uyu) if op.monto_uyu else 0,
            "monto_usd": float(op.monto_usd) if op.monto_usd else 0,
            "area": {
                "id": str(op.area.id),
                "nombre": op.area.nombre
            } if op.area else None,
            "localidad": op.localidad.value if op.localidad else None,
            "cliente": op.cliente,
            "proveedor": op.proveedor,
            "descripcion": op.descripcion
        })
    
    return result

@router.patch("/{operacion_id}/anular")
def anular_operacion(
    operacion_id: str,
    db: Session = Depends(get_db)
):
    """Anular operación (soft delete)"""
    try:
        op_uuid = uuid.UUID(operacion_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    operacion = db.query(Operacion).filter(
        Operacion.id == op_uuid,
        Operacion.deleted_at.is_(None)
    ).first()
    
    if not operacion:
        raise HTTPException(status_code=404, detail="Operación no encontrada")
    
    operacion.deleted_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Operación anulada"}

@router.post("/ingreso")
def crear_ingreso(data: IngresoCreate, db: Session = Depends(get_db)):
    return operacion_service.crear_ingreso(db, data)

@router.post("/gasto")  
def crear_gasto(data: GastoCreate, db: Session = Depends(get_db)):
    return operacion_service.crear_gasto(db, data)

@router.post("/retiro")
def crear_retiro(data: RetiroCreate, db: Session = Depends(get_db)):
    return operacion_service.crear_retiro(db, data)

@router.post("/distribucion")
def crear_distribucion(data: DistribucionCreate, db: Session = Depends(get_db)):
    return operacion_service.crear_distribucion(db, data)

@router.get("/clientes/buscar")
def buscar_clientes(q: str = "", db: Session = Depends(get_db)):
    clientes = db.query(Cliente).filter(
        Cliente.nombre.ilike(f"%{q}%")
    ).limit(10).all()
    
    return [{"id": str(c.id), "nombre": c.nombre} for c in clientes]

@router.get("/proveedores/buscar")
def buscar_proveedores(q: str = "", db: Session = Depends(get_db)):
    proveedores = db.query(Proveedor).filter(
        Proveedor.nombre.ilike(f"%{q}%")
    ).limit(10).all()
    
    return [{"id": str(p.id), "nombre": p.nombre} for p in proveedores]
