from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Operacion, TipoOperacion, Area, Usuario
from app.utils.query_helpers import aplicar_filtros_operaciones

router = APIRouter()


@router.get("/dashboard")
def dashboard_report(
    fecha_desde: date = Query(...),
    fecha_hasta: date = Query(...),
    localidad: str | None = Query(None),
    moneda_vista: str = Query("UYU"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Dashboard con métricas principales usando helpers para reducir complejidad."""
    query = aplicar_filtros_operaciones(db.query(Operacion), fecha_desde, fecha_hasta, localidad)
    operaciones = query.all()
    
    # Calcular totales usando helper
    totales = _calcular_totales(operaciones, moneda_vista)
    rentabilidad = ((totales['ingresos'] - totales['gastos']) / totales['ingresos'] * 100) if totales['ingresos'] > 0 else 0.0
    
    # Área líder
    area_lider = _calcular_area_lider(db, operaciones, moneda_vista)
    
    return {
        "metricas": {
            "ingresos": {"valor": totales['ingresos'], "moneda": moneda_vista},
            "gastos": {"valor": totales['gastos'], "moneda": moneda_vista},
            "rentabilidad": round(rentabilidad, 2),
            "area_lider": area_lider,
        },
        "filtros_aplicados": {
            "fecha_desde": fecha_desde.isoformat(),
            "fecha_hasta": fecha_hasta.isoformat(),
            "localidad": localidad or "Todas",
            "moneda_vista": moneda_vista,
        },
    }


def _calcular_totales(operaciones: List[Operacion], moneda: str) -> dict:
    """Calcula totales por tipo de operación."""
    def pick(op): return float(op.monto_uyu if moneda == "UYU" else op.monto_usd)
    
    return {
        'ingresos': sum(pick(op) for op in operaciones if op.tipo_operacion == TipoOperacion.INGRESO) or 0.0,
        'gastos': sum(pick(op) for op in operaciones if op.tipo_operacion == TipoOperacion.GASTO) or 0.0,
    }


def _calcular_area_lider(db: Session, operaciones: List[Operacion], moneda: str) -> dict:
    """Calcula área con más ingresos."""
    def pick(op): return float(op.monto_uyu if moneda == "UYU" else op.monto_usd)
    
    ingresos_por_area = {}
    for op in operaciones:
        if op.tipo_operacion == TipoOperacion.INGRESO and op.area_id:
            key = str(op.area_id)
            ingresos_por_area[key] = ingresos_por_area.get(key, 0.0) + pick(op)
    
    if not ingresos_por_area:
        return {"nombre": None, "monto": 0.0, "porcentaje": 0.0, "moneda": moneda}
    
    total = sum(ingresos_por_area.values()) or 1.0
    area_id_max = max(ingresos_por_area, key=ingresos_por_area.get)
    monto_max = ingresos_por_area[area_id_max]
    area = db.query(Area).filter(Area.id == area_id_max).first()
    
    return {
        "nombre": area.nombre if area else "N/D",
        "monto": float(monto_max),
        "porcentaje": round((monto_max / total) * 100.0, 2),
        "moneda": moneda,
    }
