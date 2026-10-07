"""
Tests del registro de actividad: cada creación, edición y anulación de una
operación deja una fila en operaciones_actividad con el usuario que la hizo.

Se ejercitan los servicios y los endpoints reales contra la BD de test.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest

from app.api.operaciones import actualizar_operacion, anular_operacion
from app.models import AccionActividad, Operacion, OperacionActividad
from app.schemas.operacion import (
    DistribucionCreate,
    GastoCreate,
    IngresoCreate,
    OperacionUpdate,
    RetiroCreate,
)
from app.services.operacion_service import (
    crear_distribucion,
    crear_gasto,
    crear_ingreso,
    crear_retiro,
)


def _actividades(db_session, operacion_id):
    return (
        db_session.query(OperacionActividad)
        .filter(OperacionActividad.operacion_id == operacion_id)
        .order_by(OperacionActividad.created_at)
        .all()
    )


@pytest.fixture
def ingreso(db_session, usuario_test, areas_test):
    data = IngresoCreate(
        monto_original=Decimal("5000"),
        moneda_original="UYU",
        tipo_cambio=Decimal("40.00"),
        fecha=date.today(),
        localidad="Montevideo",
        area_id=areas_test["Jurídica"].id,
        cliente="Cliente Actividad",
        descripcion="Ingreso actividad",
    )
    return crear_ingreso(db_session, data, usuario_test.id)


class TestRegistroCreacion:

    def test_ingreso_registra_crear(self, db_session, usuario_test, ingreso):
        actividades = _actividades(db_session, ingreso.id)
        assert len(actividades) == 1
        assert actividades[0].accion == AccionActividad.CREAR.value
        assert actividades[0].usuario_id == usuario_test.id

    def test_gasto_registra_crear(self, db_session, usuario_test, areas_test):
        data = GastoCreate(
            monto_original=Decimal("1200"),
            moneda_original="UYU",
            tipo_cambio=Decimal("40.00"),
            fecha=date.today(),
            localidad="Mercedes",
            area_id=areas_test["Contable"].id,
            proveedor="Proveedor Actividad",
            descripcion="Gasto actividad",
        )
        operacion = crear_gasto(db_session, data, usuario_test.id)

        actividades = _actividades(db_session, operacion.id)
        assert [a.accion for a in actividades] == [AccionActividad.CREAR.value]

    def test_retiro_registra_crear(self, db_session, usuario_test):
        data = RetiroCreate(
            monto_usd=Decimal("1000"),
            tipo_cambio=Decimal("40.00"),
            fecha=date.today(),
            localidad="Montevideo",
            descripcion="Retiro actividad",
        )
        operacion = crear_retiro(db_session, data, usuario_test.id)

        actividades = _actividades(db_session, operacion.id)
        assert [a.accion for a in actividades] == [AccionActividad.CREAR.value]

    def test_distribucion_registra_crear(self, db_session, usuario_test, socios_test):
        data = DistribucionCreate(
            tipo_cambio=Decimal("40.00"),
            fecha=date.today(),
            localidad="Montevideo",
            descripcion="Distribución actividad",
            bruno_usd=Decimal("500"),
        )
        operacion = crear_distribucion(db_session, data, usuario_test.id)

        actividades = _actividades(db_session, operacion.id)
        assert [a.accion for a in actividades] == [AccionActividad.CREAR.value]

    def test_si_falla_la_creacion_no_queda_registro(self, db_session, usuario_test, socios_test):
        """Atomicidad: un error a mitad de camino descarta operación y registro."""
        data = DistribucionCreate(
            tipo_cambio=Decimal("40.00"),
            fecha=date.today(),
            localidad="Montevideo",
            descripcion="Distribución que falla",
            bruno_usd=Decimal("500"),
        )
        antes = db_session.query(OperacionActividad).count()

        with patch(
            "app.services.operacion_service.DistribucionDetalle",
            side_effect=RuntimeError("falla simulada"),
        ):
            with pytest.raises(RuntimeError):
                crear_distribucion(db_session, data, usuario_test.id)

        assert db_session.query(OperacionActividad).count() == antes
        assert (
            db_session.query(Operacion)
            .filter(Operacion.descripcion == "DISTRIBUCIÓN QUE FALLA")
            .count() == 0
        )


class TestRegistroEdicionYAnulacion:

    def test_editar_registra_editar(self, db_session, usuario_test, ingreso):
        actualizar_operacion(
            str(ingreso.id),
            OperacionUpdate(descripcion="Descripción corregida"),
            db_session,
            usuario_test,
        )

        acciones = [a.accion for a in _actividades(db_session, ingreso.id)]
        assert acciones == [AccionActividad.CREAR.value, AccionActividad.EDITAR.value]

    def test_editar_sin_cambios_no_registra(self, db_session, usuario_test, ingreso):
        actualizar_operacion(str(ingreso.id), OperacionUpdate(), db_session, usuario_test)

        acciones = [a.accion for a in _actividades(db_session, ingreso.id)]
        assert acciones == [AccionActividad.CREAR.value]

    def test_anular_registra_anular(self, db_session, usuario_test, ingreso):
        anular_operacion(str(ingreso.id), db_session, usuario_test)

        actividades = _actividades(db_session, ingreso.id)
        assert [a.accion for a in actividades] == [
            AccionActividad.CREAR.value,
            AccionActividad.ANULAR.value,
        ]
        assert actividades[-1].usuario_id == usuario_test.id
