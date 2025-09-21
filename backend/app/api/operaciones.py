from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.operacion import IngresoCreate, GastoCreate
from app.services.operacion_service import crear_ingreso, crear_gasto

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

@router.get("/")
def listar_operaciones(db: Session = Depends(get_db)):
    from app.models import Operacion
    operaciones = db.query(Operacion).filter(Operacion.deleted_at == None).limit(20).all()
    return [
        {
            "id": str(op.id),
            "tipo": op.tipo_operacion.value,
            "fecha": op.fecha,
            "monto_uyu": float(op.monto_uyu),
            "monto_usd": float(op.monto_usd),
            "descripcion": op.descripcion
        }
        for op in operaciones
    ]
