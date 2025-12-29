from sqlalchemy.orm import Session
from app.models import Operacion, TipoOperacion, Moneda, Localidad, DistribucionDetalle, Socio
from app.schemas.operacion import IngresoCreate, GastoCreate, RetiroCreate, DistribucionCreate
from decimal import Decimal
from typing import Optional

def calcular_montos(monto_original: Decimal, moneda_original: str, tipo_cambio: Decimal):
    if moneda_original == "UYU":
        return monto_original, monto_original / tipo_cambio
    else:  # USD
        return monto_original * tipo_cambio, monto_original

def _crear_operacion_base(
    db: Session,
    tipo_operacion: TipoOperacion,
    fecha,
    monto_original: Decimal,
    moneda_original: str,
    tipo_cambio: Decimal,
    area_id,
    localidad: str,
    descripcion: str,
    cliente: Optional[str] = None,
    proveedor: Optional[str] = None
):
    """
    Función base para crear operaciones de tipo ingreso/gasto.
    Elimina duplicación entre crear_ingreso y crear_gasto.
    """
    monto_uyu, monto_usd = calcular_montos(monto_original, moneda_original, tipo_cambio)
    
    # Para INGRESO/GASTO, los totales son iguales (ya están convertidos)
    total_pesificado = monto_uyu
    total_dolarizado = monto_usd
    
    operacion = Operacion(
        tipo_operacion=tipo_operacion,
        fecha=fecha,
        monto_original=monto_original,
        moneda_original=Moneda[moneda_original],
        tipo_cambio=tipo_cambio,
        monto_uyu=monto_uyu,
        monto_usd=monto_usd,
        total_pesificado=total_pesificado,
        total_dolarizado=total_dolarizado,
        area_id=area_id,
        localidad=Localidad[localidad.upper().replace(" ", "_")],
        descripcion=descripcion,
        cliente=cliente,
        proveedor=proveedor
    )
    
    db.add(operacion)
    db.commit()
    db.refresh(operacion)
    return operacion

def crear_ingreso(db: Session, data: IngresoCreate):
    return _crear_operacion_base(
        db=db,
        tipo_operacion=TipoOperacion.INGRESO,
        fecha=data.fecha,
        monto_original=data.monto_original,
        moneda_original=data.moneda_original,
        tipo_cambio=data.tipo_cambio,
        area_id=data.area_id,
        localidad=data.localidad,
        descripcion=data.descripcion,
        cliente=data.cliente
    )

def crear_gasto(db: Session, data: GastoCreate):
    return _crear_operacion_base(
        db=db,
        tipo_operacion=TipoOperacion.GASTO,
        fecha=data.fecha,
        monto_original=data.monto_original,
        moneda_original=data.moneda_original,
        tipo_cambio=data.tipo_cambio,
        area_id=data.area_id,
        localidad=data.localidad,
        descripcion=data.descripcion,
        proveedor=data.proveedor
    )

def crear_retiro(db: Session, data: RetiroCreate):
    """
    Crear retiro de efectivo (movimiento financiero).
    
    RETIRO no necesita área - es un movimiento de caja, no una operación operativa.
    Filosofía DHH: NULL = no aplica, no forzar "Gastos Generales".
    """
    # Determinar montos
    if data.monto_uyu and data.monto_usd:
        monto_uyu = data.monto_uyu
        monto_usd = data.monto_usd
        monto_original = data.monto_uyu
        moneda_original = Moneda.UYU
    elif data.monto_uyu:
        monto_uyu = data.monto_uyu
        monto_usd = data.monto_uyu / data.tipo_cambio
        monto_original = data.monto_uyu
        moneda_original = Moneda.UYU
    else:
        monto_usd = data.monto_usd
        monto_uyu = data.monto_usd * data.tipo_cambio
        monto_original = data.monto_usd
        moneda_original = Moneda.USD
    
    # Para RETIRO, calcular totales sumando ambos componentes pesificados/dolarizados
    total_pesificado = monto_uyu + (monto_usd * data.tipo_cambio)
    total_dolarizado = monto_usd + (monto_uyu / data.tipo_cambio)
    
    operacion = Operacion(
        tipo_operacion=TipoOperacion.RETIRO,
        fecha=data.fecha,
        monto_original=monto_original,
        moneda_original=moneda_original,
        tipo_cambio=data.tipo_cambio,
        monto_uyu=monto_uyu,
        monto_usd=monto_usd,
        total_pesificado=total_pesificado,
        total_dolarizado=total_dolarizado,
        area_id=None,  # RETIRO no necesita área
        localidad=Localidad[data.localidad.upper().replace(" ", "_")],
        descripcion=data.descripcion
    )
    
    db.add(operacion)
    db.commit()
    db.refresh(operacion)
    return operacion

def crear_distribucion(db: Session, data: DistribucionCreate):
    """
    Crear distribución de utilidades a socios (movimiento financiero).
    
    DISTRIBUCION no necesita área - es reparto de efectivo, no una operación operativa.
    Filosofía DHH: NULL = no aplica, no forzar "Gastos Generales".
    """
    # Calcular totales sumando todos los montos de los 5 socios
    total_uyu = (
        (data.agustina_uyu or 0) +
        (data.viviana_uyu or 0) +
        (data.gonzalo_uyu or 0) +
        (data.pancho_uyu or 0) +
        (data.bruno_uyu or 0)
    )
    
    total_usd = (
        (data.agustina_usd or 0) +
        (data.viviana_usd or 0) +
        (data.gonzalo_usd or 0) +
        (data.pancho_usd or 0) +
        (data.bruno_usd or 0)
    )
    
    if total_uyu > 0:
        monto_original = total_uyu
        moneda_original = Moneda.UYU
    else:
        monto_original = total_usd
        moneda_original = Moneda.USD
    
    # Para DISTRIBUCION, calcular totales sumando ambos componentes pesificados/dolarizados
    total_pesificado = total_uyu + (total_usd * data.tipo_cambio)
    total_dolarizado = total_usd + (total_uyu / data.tipo_cambio)
    
    operacion = Operacion(
        tipo_operacion=TipoOperacion.DISTRIBUCION,
        fecha=data.fecha,
        monto_original=monto_original,
        moneda_original=moneda_original,
        tipo_cambio=data.tipo_cambio,
        monto_uyu=total_uyu,
        monto_usd=total_usd,
        total_pesificado=total_pesificado,
        total_dolarizado=total_dolarizado,
        area_id=None,  # DISTRIBUCION no necesita área
        localidad=Localidad[data.localidad.upper().replace(" ", "_")],
        descripcion="Distribución de utilidades"
    )
    
    db.add(operacion)
    db.flush()
    
    # Crear detalle para cada socio
    socios_montos = [
        ("Agustina", data.agustina_uyu, data.agustina_usd),
        ("Viviana", data.viviana_uyu, data.viviana_usd),
        ("Gonzalo", data.gonzalo_uyu, data.gonzalo_usd),
        ("Pancho", data.pancho_uyu, data.pancho_usd),
        ("Bruno", data.bruno_uyu, data.bruno_usd)
    ]
    
    for nombre, monto_uyu, monto_usd in socios_montos:
        socio = db.query(Socio).filter(Socio.nombre == nombre).first()
        if socio and (monto_uyu or monto_usd):
            detalle = DistribucionDetalle(
                operacion_id=operacion.id,
                socio_id=socio.id,
                monto_uyu=monto_uyu or 0,
                monto_usd=monto_usd or 0,
                porcentaje=20.0
            )
            db.add(detalle)
    
    db.commit()
    db.refresh(operacion)
    return operacion
