"""Registro de actividad sobre operaciones (quién crea, edita o anula)."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models import AccionActividad, OperacionActividad


def registrar_actividad(
    db: Session,
    operacion_id: UUID,
    usuario_id: UUID,
    accion: AccionActividad,
) -> OperacionActividad:
    """
    Agrega una entrada al registro de actividad SIN hacer commit.

    El llamador es dueño de la transacción: la entrada se confirma junto con
    el cambio de la operación, o se descarta con él. Así nunca queda una
    operación sin su registro ni un registro sin su operación.
    """
    actividad = OperacionActividad(
        operacion_id=operacion_id,
        usuario_id=usuario_id,
        accion=accion.value,
    )
    db.add(actividad)
    return actividad
