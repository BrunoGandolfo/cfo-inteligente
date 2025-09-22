from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.operacion import IngresoCreate, GastoCreate, RetiroCreate, DistribucionCreate
from app.services.operacion_service import crear_ingreso, crear_gasto, crear_retiro, crear_distribucion

router = APIRouter()

@router.post("/ingreso")
def registrar_ingreso(data: IngresoCreate, db: Session = Depends(get_db)):
    try:
        operacion = crear_ingreso(db, data)
        return {"message": "Ingreso registrado", "id": str(operacion.id)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/gasto")
def registrar_gasto(data: GastoCreate, db: Session = Depends(get_db)):
    try:
        operacion = crear_gasto(db, data)
        return {"message": "Gasto registrado", "id": str(operacion.id)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/retiro")
def registrar_retiro(data: RetiroCreate, db: Session = Depends(get_db)):
    try:
        operacion = crear_retiro(db, data)
        return {"message": "Retiro registrado", "id": str(operacion.id)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/distribucion")
def registrar_distribucion(data: DistribucionCreate, db: Session = Depends(get_db)):
    try:
        operacion = crear_distribucion(db, data)
        return {"message": "Distribución registrada", "id": str(operacion.id)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
def listar_operaciones(db: Session = Depends(get_db)):
    from app.models import Operacion
    operaciones = db.query(Operacion).filter(Operacion.deleted_at == None).order_by(Operacion.fecha.desc()).limit(50).all()
    return [
        {
            "id": str(op.id),
            "tipo": op.tipo_operacion.value,
            "fecha": op.fecha,
            "monto_uyu": float(op.monto_uyu),
            "monto_usd": float(op.monto_usd),
            "descripcion": op.descripcion,
            "cliente": op.cliente,
            "proveedor": op.proveedor
        }
        for op in operaciones
    ]

@router.get("/clientes/buscar")
def buscar_clientes(q: str = "", db: Session = Depends(get_db)):
    """Buscar clientes por nombre para autocomplete"""
    from app.models import Cliente
    
    if len(q) < 2:
        return []
    
    clientes = db.query(Cliente)\
        .filter(Cliente.nombre.ilike(f"%{q}%"))\
        .filter(Cliente.activo == True)\
        .order_by(Cliente.nombre)\
        .limit(10)\
        .all()
    
    return [
        {"id": str(cliente.id), "nombre": cliente.nombre}
        for cliente in clientes
    ]

@router.get("/proveedores/buscar")
def buscar_proveedores(q: str = "", db: Session = Depends(get_db)):
    """Buscar proveedores por nombre para autocomplete"""
    from app.models import Proveedor
    
    if len(q) < 2:
        return []
    
    proveedores = db.query(Proveedor)\
        .filter(Proveedor.nombre.ilike(f"%{q}%"))\
        .filter(Proveedor.activo == True)\
        .order_by(Proveedor.nombre)\
        .limit(10)\
        .all()
    
    return [
        {"id": str(proveedor.id), "nombre": proveedor.nombre}
        for proveedor in proveedores
    ]
