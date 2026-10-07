"""
Tests del resumen diario de actividad: conteo por usuario, corte de días en
hora de Uruguay y alertas de localidades sin cargas.
"""

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.models import (
    AccionActividad,
    Localidad,
    Moneda,
    Operacion,
    OperacionActividad,
    TipoOperacion,
    Usuario,
)
from app.services.resumen_actividad_service import (
    DIAS_SIN_CARGA_ALERTA,
    TZ_URUGUAY,
    obtener_actividad_por_usuario,
    obtener_alertas_localidad,
    obtener_resumen_diario,
)

DIA = date(2026, 10, 7)


def _uy(dia: date, hora: int, minuto: int = 0) -> datetime:
    return datetime(dia.year, dia.month, dia.day, hora, minuto, tzinfo=TZ_URUGUAY)


def _crear_usuario(db, nombre):
    usuario = Usuario(
        id=uuid.uuid4(),
        email=f"{nombre.lower()}-{uuid.uuid4().hex[:6]}@test.com",
        nombre=nombre,
        es_socio=False,
        activo=True,
    )
    db.add(usuario)
    db.flush()
    return usuario


def _crear_operacion(db, localidad=Localidad.MONTEVIDEO, cargada_utc=None, anulada=False):
    op = Operacion(
        id=uuid.uuid4(),
        tipo_operacion=TipoOperacion.GASTO,
        fecha=DIA,
        monto_original=Decimal("100.00"),
        moneda_original=Moneda.UYU,
        tipo_cambio=Decimal("40.0000"),
        monto_uyu=Decimal("100.00"),
        monto_usd=Decimal("2.50"),
        total_pesificado=Decimal("100.00"),
        total_dolarizado=Decimal("2.50"),
        localidad=localidad,
        descripcion="Op resumen test",
        deleted_at=datetime(2026, 10, 1) if anulada else None,
    )
    if cargada_utc is not None:
        op.created_at = cargada_utc  # naive UTC, como en producción
    db.add(op)
    db.flush()
    return op


def _registrar(db, operacion, usuario, accion, cuando):
    db.add(OperacionActividad(
        operacion_id=operacion.id,
        usuario_id=usuario.id,
        accion=accion.value,
        created_at=cuando,
    ))
    db.flush()


@pytest.fixture
def ana_y_juan(db_session):
    return _crear_usuario(db_session, "Ana"), _crear_usuario(db_session, "Juan")


class TestActividadPorUsuario:

    def test_cuenta_por_usuario_y_accion(self, db_session, ana_y_juan):
        ana, juan = ana_y_juan
        op = _crear_operacion(db_session)
        for _ in range(3):
            _registrar(db_session, op, ana, AccionActividad.CREAR, _uy(DIA, 10))
        _registrar(db_session, op, ana, AccionActividad.EDITAR, _uy(DIA, 11))
        _registrar(db_session, op, juan, AccionActividad.ANULAR, _uy(DIA, 15))

        resultado = obtener_actividad_por_usuario(db_session, DIA)

        assert [(u.nombre, u.creadas, u.editadas, u.anuladas) for u in resultado] == [
            ("Ana", 3, 1, 0),
            ("Juan", 0, 0, 1),
        ]

    def test_corta_el_dia_en_hora_de_uruguay(self, db_session, ana_y_juan):
        """23:30 en Uruguay ya es el día siguiente en UTC, pero cuenta para hoy."""
        ana, _ = ana_y_juan
        op = _crear_operacion(db_session)
        _registrar(db_session, op, ana, AccionActividad.CREAR, _uy(DIA, 23, 30))
        _registrar(db_session, op, ana, AccionActividad.CREAR, _uy(DIA + timedelta(days=1), 0, 10))
        _registrar(db_session, op, ana, AccionActividad.CREAR, _uy(DIA, 0, 0))

        hoy = obtener_actividad_por_usuario(db_session, DIA)
        manana = obtener_actividad_por_usuario(db_session, DIA + timedelta(days=1))

        assert hoy[0].creadas == 2
        assert manana[0].creadas == 1

    def test_dia_sin_actividad(self, db_session):
        resumen = obtener_resumen_diario(db_session, DIA)
        assert resumen.usuarios == []
        assert resumen.sin_actividad is True


class TestAlertasLocalidad:

    def _cierre_utc(self, dias_antes):
        """Mediodía en Uruguay N días antes de DIA, expresado en UTC naive."""
        momento = _uy(DIA - timedelta(days=dias_antes), 12)
        return momento.astimezone(timezone.utc).replace(tzinfo=None)

    def test_alerta_localidad_sin_cargas_recientes(self, db_session):
        _crear_operacion(db_session, Localidad.MONTEVIDEO, self._cierre_utc(10))
        _crear_operacion(db_session, Localidad.MERCEDES, self._cierre_utc(0))

        alertas = obtener_alertas_localidad(db_session, DIA)

        assert len(alertas) == 1
        assert alertas[0].localidad == "Montevideo"
        assert alertas[0].dias_sin_carga == 10
        assert alertas[0].ultima_carga == DIA - timedelta(days=10)

    def test_en_el_limite_no_alerta(self, db_session):
        _crear_operacion(db_session, Localidad.MONTEVIDEO, self._cierre_utc(DIAS_SIN_CARGA_ALERTA))
        _crear_operacion(db_session, Localidad.MERCEDES, self._cierre_utc(0))

        assert obtener_alertas_localidad(db_session, DIA) == []

    def test_ignora_operaciones_anuladas(self, db_session):
        _crear_operacion(db_session, Localidad.MONTEVIDEO, self._cierre_utc(20))
        _crear_operacion(db_session, Localidad.MONTEVIDEO, self._cierre_utc(0), anulada=True)
        _crear_operacion(db_session, Localidad.MERCEDES, self._cierre_utc(0))

        alertas = obtener_alertas_localidad(db_session, DIA)

        assert [(a.localidad, a.dias_sin_carga) for a in alertas] == [("Montevideo", 20)]

    def test_localidad_sin_ninguna_carga(self, db_session):
        _crear_operacion(db_session, Localidad.MERCEDES, self._cierre_utc(0))

        alertas = obtener_alertas_localidad(db_session, DIA)

        assert [(a.localidad, a.ultima_carga, a.dias_sin_carga) for a in alertas] == [
            ("Montevideo", None, None),
        ]
