"""
Resumen diario de actividad de registro: quién creó, editó y anuló
operaciones en un día, y qué localidades llevan días sin cargas.

Solo obtiene datos (PostgreSQL agrega, Python calcula). Armar y enviar el
mail es responsabilidad de otras piezas.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AccionActividad, Localidad, Operacion, OperacionActividad, Usuario

TZ_URUGUAY = ZoneInfo("America/Montevideo")

# Una localidad sin operaciones cargadas en más de estos días genera alerta
DIAS_SIN_CARGA_ALERTA = 5


@dataclass(frozen=True)
class ActividadUsuario:
    nombre: str
    creadas: int
    editadas: int
    anuladas: int


@dataclass(frozen=True)
class AlertaLocalidad:
    localidad: str
    ultima_carga: date | None  # None = nunca se cargó nada
    dias_sin_carga: int | None


@dataclass(frozen=True)
class ResumenActividad:
    dia: date
    usuarios: list[ActividadUsuario]
    alertas: list[AlertaLocalidad]

    @property
    def sin_actividad(self) -> bool:
        return not self.usuarios


def _limites_del_dia(dia: date) -> tuple[datetime, datetime]:
    """Medianoche a medianoche en hora de Uruguay, como instantes con zona."""
    inicio = datetime.combine(dia, time.min, tzinfo=TZ_URUGUAY)
    return inicio, inicio + timedelta(days=1)


def obtener_actividad_por_usuario(db: Session, dia: date) -> list[ActividadUsuario]:
    """Cuenta, por usuario, las acciones registradas en el día (hora Uruguay)."""
    inicio, fin = _limites_del_dia(dia)
    accion = OperacionActividad.accion

    filas = db.execute(
        select(
            Usuario.nombre,
            func.count().filter(accion == AccionActividad.CREAR.value),
            func.count().filter(accion == AccionActividad.EDITAR.value),
            func.count().filter(accion == AccionActividad.ANULAR.value),
        )
        .join(Usuario, Usuario.id == OperacionActividad.usuario_id)
        .where(OperacionActividad.created_at >= inicio, OperacionActividad.created_at < fin)
        .group_by(Usuario.id, Usuario.nombre)
        .order_by(Usuario.nombre)
    ).all()

    return [ActividadUsuario(nombre, creadas, editadas, anuladas)
            for nombre, creadas, editadas, anuladas in filas]


def obtener_alertas_localidad(db: Session, dia: date) -> list[AlertaLocalidad]:
    """
    Localidades cuya última operación cargada (vigente) es de hace más de
    DIAS_SIN_CARGA_ALERTA días al cierre de `dia`.

    Usa operaciones.created_at (fecha de carga, guardada en UTC sin zona),
    que existe desde el inicio del sistema: la alerta funciona desde el
    primer día, sin esperar a que se llene el registro de actividad.
    """
    filas = dict(db.execute(
        select(Operacion.localidad, func.max(Operacion.created_at))
        .where(Operacion.deleted_at.is_(None))
        .group_by(Operacion.localidad)
    ).all())

    alertas = []
    for localidad in Localidad:
        ultima = filas.get(localidad)
        if ultima is None:
            alertas.append(AlertaLocalidad(localidad.value, None, None))
            continue
        ultima_dia = ultima.replace(tzinfo=timezone.utc).astimezone(TZ_URUGUAY).date()
        dias = (dia - ultima_dia).days
        if dias > DIAS_SIN_CARGA_ALERTA:
            alertas.append(AlertaLocalidad(localidad.value, ultima_dia, dias))
    return alertas


def obtener_resumen_diario(db: Session, dia: date) -> ResumenActividad:
    """Resumen completo del día: actividad por usuario + alertas de localidad."""
    return ResumenActividad(
        dia=dia,
        usuarios=obtener_actividad_por_usuario(db, dia),
        alertas=obtener_alertas_localidad(db, dia),
    )
