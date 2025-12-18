from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Operacion, TipoOperacion, Area, Localidad, Usuario

router = APIRouter()


@router.get("/dashboard")
def dashboard_report(
    fecha_desde: date = Query(...),
    fecha_hasta: date = Query(...),
    localidad: str | None = Query(None),  # "Montevideo" | "Mercedes" | None | "Todas"
    moneda_vista: str = Query("UYU"),     # "UYU" | "USD"
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    filtros = [
        Operacion.fecha >= fecha_desde,
        Operacion.fecha <= fecha_hasta,
        Operacion.deleted_at == None
    ]
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

    operaciones = db.query(Operacion).filter(and_(*filtros)).all()

    def pick_monto(op: Operacion) -> float:
        return float(op.monto_uyu) if moneda_vista == "UYU" else float(op.monto_usd)

    ingresos = sum(pick_monto(op) for op in operaciones if op.tipo_operacion == TipoOperacion.INGRESO) or 0.0
    gastos = sum(pick_monto(op) for op in operaciones if op.tipo_operacion == TipoOperacion.GASTO) or 0.0
    # retiros y distribuciones calculados para futura expansión del dashboard
    _retiros = sum(pick_monto(op) for op in operaciones if op.tipo_operacion == TipoOperacion.RETIRO) or 0.0  # noqa: F841
    _distribuciones = sum(pick_monto(op) for op in operaciones if op.tipo_operacion == TipoOperacion.DISTRIBUCION) or 0.0  # noqa: F841

    # Margen Operativo: solo ingresos vs gastos (no incluye retiros ni distribuciones)
    rentabilidad = 0.0
    if ingresos > 0:
        rentabilidad = ((ingresos - gastos) / ingresos) * 100.0

    # Área líder por ingresos
    ingresos_por_area: dict[str, float] = {}
    for op in operaciones:
        if op.tipo_operacion != TipoOperacion.INGRESO or not op.area_id:
            continue
        key = str(op.area_id)
        ingresos_por_area[key] = ingresos_por_area.get(key, 0.0) + pick_monto(op)

    area_lider = {"nombre": None, "monto": 0.0, "porcentaje": 0.0, "moneda": moneda_vista}
    if ingresos_por_area:
        total_ingresos = sum(ingresos_por_area.values()) or 1.0
        area_id_max = max(ingresos_por_area, key=lambda k: ingresos_por_area[k])
        monto_max = ingresos_por_area[area_id_max]
        area = db.query(Area).filter(Area.id == area_id_max).first()
        area_lider = {
            "nombre": area.nombre if area else "N/D",
            "monto": float(monto_max),
            "porcentaje": round(float((monto_max / total_ingresos) * 100.0), 2),
            "moneda": moneda_vista,
        }

    return {
        "metricas": {
            "ingresos": {"valor": float(ingresos), "moneda": moneda_vista},
            "gastos": {"valor": float(gastos), "moneda": moneda_vista},
            "rentabilidad": round(float(rentabilidad), 2),
            "area_lider": area_lider,
        },
        "filtros_aplicados": {
            "fecha_desde": fecha_desde.isoformat(),
            "fecha_hasta": fecha_hasta.isoformat(),
            "localidad": localidad or "Todas",
            "moneda_vista": moneda_vista,
        },
    }
