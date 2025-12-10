from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.operacion import Operacion
from app.models.area import Area
from app.models.socio import Socio
from app.models.cliente import Cliente
from app.models.proveedor import Proveedor
from app.models import Usuario
from app.schemas.operacion import (
    IngresoCreate, GastoCreate, RetiroCreate, DistribucionCreate
)
from app.schemas.operacion_update import (
    IngresoUpdate, GastoUpdate, RetiroUpdate
)
from app.services import operacion_service
import uuid

router = APIRouter()

@router.get("/")
def get_operaciones(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    current_user: Usuario = Depends(get_current_user)
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
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
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
def crear_ingreso(data: IngresoCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    return operacion_service.crear_ingreso(db, data)

@router.post("/gasto")  
def crear_gasto(data: GastoCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    return operacion_service.crear_gasto(db, data)

@router.post("/retiro")
def crear_retiro(data: RetiroCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if not current_user.es_socio:
        raise HTTPException(status_code=403, detail="Solo socios pueden registrar retiros")
    return operacion_service.crear_retiro(db, data)

@router.post("/distribucion")
def crear_distribucion(data: DistribucionCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if not current_user.es_socio:
        raise HTTPException(status_code=403, detail="Solo socios pueden registrar distribuciones")
    return operacion_service.crear_distribucion(db, data)

@router.patch("/{operacion_id}")
def actualizar_operacion(
    operacion_id: str,
    data: dict,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar operación existente"""
    from app.models import Moneda, Localidad
    from app.services.operacion_service import calcular_montos
    
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
    
    # Actualizar campos permitidos
    if 'fecha' in data and data['fecha']:
        operacion.fecha = data['fecha']
    
    if 'descripcion' in data:
        operacion.descripcion = data['descripcion']
    
    if 'localidad' in data and data['localidad']:
        operacion.localidad = Localidad[data['localidad'].upper().replace(" ", "_")]
    
    if 'cliente' in data:
        operacion.cliente = data['cliente']
    
    if 'proveedor' in data:
        operacion.proveedor = data['proveedor']
    
    if 'area_id' in data and data['area_id']:
        operacion.area_id = UUID(data['area_id']) if isinstance(data['area_id'], str) else data['area_id']
    
    # Si cambian monto/moneda/TC, recalcular
    recalcular = False
    if 'monto_original' in data and data['monto_original'] is not None:
        operacion.monto_original = Decimal(str(data['monto_original']))
        recalcular = True
    
    if 'moneda_original' in data and data['moneda_original']:
        operacion.moneda_original = Moneda[data['moneda_original']]
        recalcular = True
    
    if 'tipo_cambio' in data and data['tipo_cambio']:
        operacion.tipo_cambio = Decimal(str(data['tipo_cambio']))
        recalcular = True
    
    # Retiros con montos directos
    if 'monto_uyu' in data and data['monto_uyu'] is not None:
        operacion.monto_uyu = Decimal(str(data['monto_uyu']))
        if operacion.tipo_cambio and operacion.tipo_cambio > 0:
            operacion.monto_usd = operacion.monto_uyu / operacion.tipo_cambio
    
    if 'monto_usd' in data and data['monto_usd'] is not None:
        operacion.monto_usd = Decimal(str(data['monto_usd']))
        if operacion.tipo_cambio and operacion.tipo_cambio > 0:
            operacion.monto_uyu = operacion.monto_usd * operacion.tipo_cambio
    
    # Recalcular montos si aplica
    if recalcular and operacion.monto_original and operacion.moneda_original and operacion.tipo_cambio:
        monto_uyu, monto_usd = calcular_montos(
            operacion.monto_original,
            operacion.moneda_original.value,
            operacion.tipo_cambio
        )
        operacion.monto_uyu = monto_uyu
        operacion.monto_usd = monto_usd
    
    operacion.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(operacion)
    
    return {"message": "Operación actualizada correctamente", "id": str(operacion.id)}

@router.get("/clientes/buscar")
def buscar_clientes(q: str = "", db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    clientes = db.query(Cliente).filter(
        Cliente.nombre.ilike(f"%{q}%")
    ).limit(10).all()
    
    return [{"id": str(c.id), "nombre": c.nombre} for c in clientes]

@router.get("/proveedores/buscar")
def buscar_proveedores(q: str = "", db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    proveedores = db.query(Proveedor).filter(
        Proveedor.nombre.ilike(f"%{q}%")
    ).limit(10).all()
    
    return [{"id": str(p.id), "nombre": p.nombre} for p in proveedores]
