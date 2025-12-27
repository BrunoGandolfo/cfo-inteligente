"""
Endpoints para métricas del Dashboard
Reemplaza los endpoints eliminados de reportes_dashboard.py
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from datetime import date
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.operacion import Operacion, TipoOperacion
from app.models import Usuario

router = APIRouter()


@router.get("/dashboard")
def get_dashboard_metrics(
    fecha_desde: date = Query(...),
    fecha_hasta: date = Query(...),
    localidad: str = Query(None),
    moneda_vista: str = Query("UYU"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Métricas principales del dashboard"""
    
    # Base query con área cargada
    query = db.query(Operacion).options(joinedload(Operacion.area)).filter(
        Operacion.deleted_at.is_(None),
        Operacion.fecha >= fecha_desde,
        Operacion.fecha <= fecha_hasta
    )
    
    if localidad and localidad != 'Todas':
        query = query.filter(Operacion.localidad == localidad)
    
    operaciones = query.all()
    
    # Calcular totales
    campo_monto = 'monto_usd' if moneda_vista == 'USD' else 'monto_uyu'
    
    ingresos = sum(
        float(getattr(op, campo_monto) or 0) 
        for op in operaciones 
        if op.tipo_operacion == TipoOperacion.INGRESO
    )
    
    gastos = sum(
        float(getattr(op, campo_monto) or 0) 
        for op in operaciones 
        if op.tipo_operacion == TipoOperacion.GASTO
    )
    
    # Rentabilidad
    rentabilidad = ((ingresos - gastos) / ingresos * 100) if ingresos > 0 else 0
    
    # Área líder (más ingresos)
    areas_ingresos = {}
    for op in operaciones:
        if op.tipo_operacion == TipoOperacion.INGRESO and op.area:
            area_nombre = op.area.nombre
            areas_ingresos[area_nombre] = areas_ingresos.get(area_nombre, 0) + float(getattr(op, campo_monto) or 0)
    
    area_lider = max(areas_ingresos, key=areas_ingresos.get) if areas_ingresos else None
    
    return {
        "metricas": {
            "ingresos": {"valor": round(ingresos, 2), "moneda": moneda_vista},
            "gastos": {"valor": round(gastos, 2), "moneda": moneda_vista},
            "rentabilidad": round(rentabilidad, 2),
            "area_lider": area_lider
        },
        "filtros_aplicados": {
            "fecha_desde": str(fecha_desde),
            "fecha_hasta": str(fecha_hasta),
            "localidad": localidad,
            "moneda_vista": moneda_vista
        }
    }


@router.get("/operaciones-grafico")
def get_operaciones_grafico(
    fecha_desde: date = Query(...),
    fecha_hasta: date = Query(...),
    localidad: str = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Operaciones agrupadas para gráficos"""
    
    query = db.query(Operacion).options(joinedload(Operacion.area)).filter(
        Operacion.deleted_at.is_(None),
        Operacion.fecha >= fecha_desde,
        Operacion.fecha <= fecha_hasta
    )
    
    if localidad and localidad != 'Todas':
        query = query.filter(Operacion.localidad == localidad)
    
    operaciones = query.order_by(Operacion.fecha).all()
    
    result = []
    for op in operaciones:
        result.append({
            "fecha": op.fecha.isoformat() if op.fecha else None,
            "tipo_operacion": op.tipo_operacion.value if op.tipo_operacion else None,
            "monto_uyu": float(op.monto_uyu) if op.monto_uyu else 0,
            "monto_usd": float(op.monto_usd) if op.monto_usd else 0,
            "area": op.area.nombre if op.area else None
        })
    
    return {"operaciones": result}

