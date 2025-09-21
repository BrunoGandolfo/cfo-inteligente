from sqlalchemy.orm import Session
from app.models import Operacion, TipoOperacion, Moneda, Localidad, DistribucionDetalle, Area
from app.schemas.operacion import IngresoCreate, GastoCreate, RetiroCreate, DistribucionCreate
from decimal import Decimal
import uuid

def calcular_montos(monto_original: Decimal, moneda_original: str, tipo_cambio: Decimal):
    if moneda_original == "UYU":
        return monto_original, monto_original / tipo_cambio
    else:  # USD
        return monto_original * tipo_cambio, monto_original

def crear_ingreso(db: Session, data: IngresoCreate):
    monto_uyu, monto_usd = calcular_montos(data.monto_original, data.moneda_original, data.tipo_cambio)
    
    operacion = Operacion(
        tipo_operacion=TipoOperacion.INGRESO,
        fecha=data.fecha,
        monto_original=data.monto_original,
        moneda_original=Moneda[data.moneda_original],
        tipo_cambio=data.tipo_cambio,
        monto_uyu=monto_uyu,
        monto_usd=monto_usd,
        area_id=data.area_id,
        localidad=Localidad[data.localidad.upper().replace(" ", "_")],
        descripcion=data.descripcion,
        cliente=data.cliente
    )
    
    db.add(operacion)
    db.commit()
    db.refresh(operacion)
    return operacion

def crear_gasto(db: Session, data: GastoCreate):
    monto_uyu, monto_usd = calcular_montos(data.monto_original, data.moneda_original, data.tipo_cambio)
    
    operacion = Operacion(
        tipo_operacion=TipoOperacion.GASTO,
        fecha=data.fecha,
        monto_original=data.monto_original,
        moneda_original=Moneda[data.moneda_original],
        tipo_cambio=data.tipo_cambio,
        monto_uyu=monto_uyu,
        monto_usd=monto_usd,
        area_id=data.area_id,
        localidad=Localidad[data.localidad.upper().replace(" ", "_")],
        descripcion=data.descripcion,
        proveedor=data.proveedor
    )
    
    db.add(operacion)
    db.commit()
    db.refresh(operacion)
    return operacion

def crear_retiro(db: Session, data: RetiroCreate):
    # Retiro de efectivo de la empresa
    # Obtener área "Gastos Generales" para retiros
    area_gastos = db.query(Area).filter(Area.nombre == "Gastos Generales").first()
    if not area_gastos:
        raise ValueError("No se encontró el área Gastos Generales")
    
    # Determinar montos y moneda principal
    if data.monto_uyu and data.monto_usd:
        monto_uyu = data.monto_uyu
        monto_usd = data.monto_usd
        monto_original = data.monto_uyu  # Por defecto usamos UYU como referencia
        moneda_original = Moneda.UYU
    elif data.monto_uyu:
        monto_uyu = data.monto_uyu
        monto_usd = data.monto_uyu / data.tipo_cambio
        monto_original = data.monto_uyu
        moneda_original = Moneda.UYU
    else:  # solo USD
        monto_usd = data.monto_usd
        monto_uyu = data.monto_usd * data.tipo_cambio
        monto_original = data.monto_usd
        moneda_original = Moneda.USD
    
    operacion = Operacion(
        tipo_operacion=TipoOperacion.RETIRO,
        fecha=data.fecha,
        monto_original=monto_original,
        moneda_original=moneda_original,
        tipo_cambio=data.tipo_cambio,
        monto_uyu=monto_uyu,
        monto_usd=monto_usd,
        area_id=area_gastos.id,
        localidad=Localidad[data.localidad.upper().replace(" ", "_")],
        descripcion=data.concepto or "Retiro de efectivo"
    )
    
    db.add(operacion)
    db.commit()
    db.refresh(operacion)
    return operacion

def crear_distribucion(db: Session, data: DistribucionCreate):
    # Distribución de utilidades entre socios
    area_gastos = db.query(Area).filter(Area.nombre == "Gastos Generales").first()
    if not area_gastos:
        raise ValueError("No se encontró el área Gastos Generales")
    
    # Calcular totales
    total_uyu = sum(d.get("monto_uyu", 0) or 0 for d in data.distribuciones)
    total_usd = sum(d.get("monto_usd", 0) or 0 for d in data.distribuciones)
    
    # Determinar monto y moneda principal
    if total_uyu > 0:
        monto_original = total_uyu
        moneda_original = Moneda.UYU
    else:
        monto_original = total_usd
        moneda_original = Moneda.USD
    
    operacion = Operacion(
        tipo_operacion=TipoOperacion.DISTRIBUCION,
        fecha=data.fecha,
        monto_original=monto_original,
        moneda_original=moneda_original,
        tipo_cambio=data.tipo_cambio,
        monto_uyu=total_uyu,
        monto_usd=total_usd,
        area_id=area_gastos.id,
        localidad=Localidad[data.localidad.upper().replace(" ", "_")],
        descripcion=data.descripcion or "Distribución de utilidades"
    )
    
    db.add(operacion)
    db.flush()
    
    # Crear detalles por socio
    for dist in data.distribuciones:
        detalle = DistribucionDetalle(
            operacion_id=operacion.id,
            socio_id=dist["socio_id"],
            monto_uyu=dist.get("monto_uyu", 0) or 0,
            monto_usd=dist.get("monto_usd", 0) or 0,
            porcentaje=dist.get("porcentaje", 20.0)
        )
        db.add(detalle)
    
    db.commit()
    db.refresh(operacion)
    return operacion
