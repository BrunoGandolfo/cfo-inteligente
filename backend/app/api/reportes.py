from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from datetime import date, timedelta
from typing import Tuple
from app.core.database import get_db
from app.models import Operacion, TipoOperacion, Area, Localidad

router = APIRouter()

def _calcular_rango_mes(mes: int, anio: int) -> Tuple[date, date]:
    """
    Calcula el primer y último día del mes especificado.
    Helper para evitar duplicación en endpoints de reportes.
    """
    fecha_inicio = date(anio, mes, 1)
    if mes == 12:
        fecha_fin = date(anio + 1, 1, 1) - timedelta(days=1)
    else:
        fecha_fin = date(anio, mes + 1, 1) - timedelta(days=1)
    return fecha_inicio, fecha_fin

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
    
    fecha_inicio, fecha_fin = _calcular_rango_mes(mes, anio)
    
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
    
    fecha_inicio, fecha_fin = _calcular_rango_mes(mes, anio)
    
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
    
    fecha_inicio, fecha_fin = _calcular_rango_mes(mes, anio)
    
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

@router.get("/operaciones-grafico")
def operaciones_para_graficos(
    fecha_desde: date = Query(...),
    fecha_hasta: date = Query(...),
    localidad: str | None = Query(None),
    db: Session = Depends(get_db)
):
    """
    Retorna operaciones filtradas para visualización en gráficos.
    
    Endpoint diseñado específicamente para gráficos del dashboard:
    - Acepta filtros de fecha y localidad (igual que dashboard_report)
    - Retorna operaciones individuales con sus relaciones (area, cliente, proveedor)
    - Límite configurable (default: 100) para cargar más datos que el CRUD
    
    Patrón arquitectónico:
    - /api/operaciones: CRUD básico (últimas 50, sin filtros)
    - /api/reportes/dashboard: Métricas agregadas
    - /api/reportes/operaciones-grafico: Operaciones para visualización (este endpoint)
    """
    # Construir filtros dinámicos (patrón dashboard_report)
    filtros = [
        Operacion.fecha >= fecha_desde,
        Operacion.fecha <= fecha_hasta,
        Operacion.deleted_at == None
    ]
    
    # Filtro de localidad opcional (patrón dashboard_report)
    if localidad and localidad != "Todas":
        localidad_map = {
            "Montevideo": Localidad.MONTEVIDEO,
            "MONTEVIDEO": Localidad.MONTEVIDEO,
            "Mercedes": Localidad.MERCEDES,
            "MERCEDES": Localidad.MERCEDES,
        }
        enum_loc = localidad_map.get(localidad)
        if enum_loc:
            filtros.append(Operacion.localidad == enum_loc)
    
    # Query con joinedload para incluir relaciones (patrón operaciones.py)
    operaciones = db.query(Operacion)\
        .options(joinedload(Operacion.area))\
        .filter(and_(*filtros))\
        .order_by(Operacion.fecha)\
        .all()
    
    # Serialización completa (patrón operaciones.py)
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
            "area_id": str(op.area_id) if op.area_id else None,
            "area": {
                "id": str(op.area.id),
                "nombre": op.area.nombre
            } if op.area else None,
            "localidad": op.localidad.value if op.localidad else None,
            "cliente": op.cliente,
            "proveedor": op.proveedor,
            "descripcion": op.descripcion
        })
    
    return {
        "operaciones": result,
        "cantidad": len(result),
        "filtros_aplicados": {
            "fecha_desde": fecha_desde.isoformat(),
            "fecha_hasta": fecha_hasta.isoformat(),
            "localidad": localidad or "Todas"
        }
    }
