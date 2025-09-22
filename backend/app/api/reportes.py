from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, date, timedelta
from decimal import Decimal
from app.core.database import get_db
from app.models import Operacion, TipoOperacion, Area

router = APIRouter()

@router.get("/resumen-mensual")
def resumen_mensual(
    mes: int = None,
    anio: int = None,
    db: Session = Depends(get_db)
):
    """Resumen del mes actual o especificado"""
    if not mes or not anio:
        hoy = date.today()
        mes = hoy.month
        anio = hoy.year
    
    fecha_inicio = date(anio, mes, 1)
    if mes == 12:
        fecha_fin = date(anio + 1, 1, 1) - timedelta(days=1)
    else:
        fecha_fin = date(anio, mes + 1, 1) - timedelta(days=1)
    
    operaciones = db.query(Operacion).filter(
        and_(
            Operacion.fecha >= fecha_inicio,
            Operacion.fecha <= fecha_fin,
            Operacion.deleted_at == None
        )
    ).all()
    
    total_ingresos_uyu = sum(op.monto_uyu for op in operaciones if op.tipo_operacion == TipoOperacion.INGRESO) or 0
    total_gastos_uyu = sum(op.monto_uyu for op in operaciones if op.tipo_operacion == TipoOperacion.GASTO) or 0
    total_retiros_uyu = sum(op.monto_uyu for op in operaciones if op.tipo_operacion == TipoOperacion.RETIRO) or 0
    total_distribuciones_uyu = sum(op.monto_uyu for op in operaciones if op.tipo_operacion == TipoOperacion.DISTRIBUCION) or 0
    
    total_ingresos_usd = sum(op.monto_usd for op in operaciones if op.tipo_operacion == TipoOperacion.INGRESO) or 0
    total_gastos_usd = sum(op.monto_usd for op in operaciones if op.tipo_operacion == TipoOperacion.GASTO) or 0
    total_retiros_usd = sum(op.monto_usd for op in operaciones if op.tipo_operacion == TipoOperacion.RETIRO) or 0
    total_distribuciones_usd = sum(op.monto_usd for op in operaciones if op.tipo_operacion == TipoOperacion.DISTRIBUCION) or 0
    
    rentabilidad_uyu = total_ingresos_uyu - total_gastos_uyu - total_retiros_uyu - total_distribuciones_uyu
    rentabilidad_usd = total_ingresos_usd - total_gastos_usd - total_retiros_usd - total_distribuciones_usd
    
    return {
        "periodo": f"{mes}/{anio}",
        "cantidad_operaciones": len(operaciones),
        "ingresos": {"uyu": float(total_ingresos_uyu), "usd": float(total_ingresos_usd)},
        "gastos": {"uyu": float(total_gastos_uyu), "usd": float(total_gastos_usd)},
        "retiros": {"uyu": float(total_retiros_uyu), "usd": float(total_retiros_usd)},
        "distribuciones": {"uyu": float(total_distribuciones_uyu), "usd": float(total_distribuciones_usd)},
        "rentabilidad": {"uyu": float(rentabilidad_uyu), "usd": float(rentabilidad_usd)}
    }

@router.get("/por-area")
def reporte_por_area(
    mes: int = None,
    anio: int = None,
    db: Session = Depends(get_db)
):
    """Distribución de operaciones por área"""
    if not mes or not anio:
        hoy = date.today()
        mes = hoy.month
        anio = hoy.year
    
    fecha_inicio = date(anio, mes, 1)
    if mes == 12:
        fecha_fin = date(anio + 1, 1, 1) - timedelta(days=1)
    else:
        fecha_fin = date(anio, mes + 1, 1) - timedelta(days=1)
    
    areas = db.query(Area).filter(Area.activo == True).all()
    
    resultado = []
    for area in areas:
        operaciones = db.query(Operacion).filter(
            and_(
                Operacion.area_id == area.id,
                Operacion.fecha >= fecha_inicio,
                Operacion.fecha <= fecha_fin,
                Operacion.deleted_at == None
            )
        ).all()
        
        ingresos_uyu = sum(op.monto_uyu for op in operaciones if op.tipo_operacion == TipoOperacion.INGRESO) or 0
        gastos_uyu = sum(op.monto_uyu for op in operaciones if op.tipo_operacion == TipoOperacion.GASTO) or 0
        
        resultado.append({
            "area": area.nombre,
            "cantidad_operaciones": len(operaciones),
            "ingresos_uyu": float(ingresos_uyu),
            "gastos_uyu": float(gastos_uyu),
            "balance_uyu": float(ingresos_uyu - gastos_uyu)
        })
    
    return {"periodo": f"{mes}/{anio}", "areas": resultado}

@router.get("/rentabilidad")
def calcular_rentabilidad(
    mes: int = None,
    anio: int = None,
    db: Session = Depends(get_db)
):
    """Cálculo de rentabilidad (margen sobre ingresos)"""
    if not mes or not anio:
        hoy = date.today()
        mes = hoy.month
        anio = hoy.year
    
    fecha_inicio = date(anio, mes, 1)
    if mes == 12:
        fecha_fin = date(anio + 1, 1, 1) - timedelta(days=1)
    else:
        fecha_fin = date(anio, mes + 1, 1) - timedelta(days=1)
    
    operaciones = db.query(Operacion).filter(
        and_(
            Operacion.fecha >= fecha_inicio,
            Operacion.fecha <= fecha_fin,
            Operacion.deleted_at == None
        )
    ).all()
    
    ingresos_uyu = sum(op.monto_uyu for op in operaciones if op.tipo_operacion == TipoOperacion.INGRESO) or 0
    gastos_uyu = sum(op.monto_uyu for op in operaciones if op.tipo_operacion == TipoOperacion.GASTO) or 0
    retiros_uyu = sum(op.monto_uyu for op in operaciones if op.tipo_operacion == TipoOperacion.RETIRO) or 0
    distribuciones_uyu = sum(op.monto_uyu for op in operaciones if op.tipo_operacion == TipoOperacion.DISTRIBUCION) or 0
    
    resultado_operativo = ingresos_uyu - gastos_uyu
    resultado_neto = resultado_operativo - retiros_uyu - distribuciones_uyu
    
    margen_operativo = 0
    margen_neto = 0
    
    if ingresos_uyu > 0:
        margen_operativo = (resultado_operativo / ingresos_uyu) * 100
        margen_neto = (resultado_neto / ingresos_uyu) * 100
    
    return {
        "periodo": f"{mes}/{anio}",
        "ingresos_uyu": float(ingresos_uyu),
        "gastos_uyu": float(gastos_uyu),
        "retiros_uyu": float(retiros_uyu),
        "distribuciones_uyu": float(distribuciones_uyu),
        "resultado_operativo": float(resultado_operativo),
        "resultado_neto": float(resultado_neto),
        "margen_operativo_porcentaje": round(float(margen_operativo), 2),
        "margen_neto_porcentaje": round(float(margen_neto), 2)
    }
