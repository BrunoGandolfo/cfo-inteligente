"""
Tests del modelo OperacionActividad (registro de quién crea, edita o anula).

Valida que la base acepte las tres acciones válidas, rechace cualquier otra
y exija operación y usuario existentes.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import (
    AccionActividad,
    Localidad,
    Moneda,
    Operacion,
    OperacionActividad,
    TipoOperacion,
)


@pytest.fixture
def operacion_simple(db_session, areas_test):
    op = Operacion(
        id=uuid.uuid4(),
        tipo_operacion=TipoOperacion.GASTO,
        fecha=date(2026, 10, 7),
        monto_original=Decimal("1000.00"),
        moneda_original=Moneda.UYU,
        tipo_cambio=Decimal("41.5000"),
        monto_uyu=Decimal("1000.00"),
        monto_usd=Decimal("24.10"),
        total_pesificado=Decimal("1000.00"),
        total_dolarizado=Decimal("24.10"),
        area_id=areas_test["Jurídica"].id,
        localidad=Localidad.MONTEVIDEO,
        descripcion="Gasto test actividad",
    )
    db_session.add(op)
    db_session.flush()
    return op


class TestOperacionActividadModel:

    @pytest.mark.parametrize("accion", list(AccionActividad))
    def test_acepta_acciones_validas(self, db_session, usuario_test, operacion_simple, accion):
        actividad = OperacionActividad(
            operacion_id=operacion_simple.id,
            usuario_id=usuario_test.id,
            accion=accion.value,
        )
        db_session.add(actividad)
        db_session.flush()

        assert actividad.id is not None
        assert actividad.created_at is not None
        assert actividad.created_at.tzinfo is not None

    def test_rechaza_accion_invalida(self, db_session, usuario_test, operacion_simple):
        db_session.add(OperacionActividad(
            operacion_id=operacion_simple.id,
            usuario_id=usuario_test.id,
            accion="BORRAR",
        ))
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_rechaza_operacion_inexistente(self, db_session, usuario_test):
        db_session.add(OperacionActividad(
            operacion_id=uuid.uuid4(),
            usuario_id=usuario_test.id,
            accion=AccionActividad.CREAR.value,
        ))
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_rechaza_usuario_inexistente(self, db_session, operacion_simple):
        db_session.add(OperacionActividad(
            operacion_id=operacion_simple.id,
            usuario_id=uuid.uuid4(),
            accion=AccionActividad.CREAR.value,
        ))
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_relaciones_navegables(self, db_session, usuario_test, operacion_simple):
        actividad = OperacionActividad(
            operacion_id=operacion_simple.id,
            usuario_id=usuario_test.id,
            accion=AccionActividad.EDITAR.value,
        )
        db_session.add(actividad)
        db_session.flush()
        db_session.refresh(actividad)

        assert actividad.usuario.nombre == "Usuario Test"
        assert actividad.operacion.descripcion == "Gasto test actividad"
