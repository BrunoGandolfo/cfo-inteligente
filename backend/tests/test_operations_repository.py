"""
Tests para OperationsRepository.
Usa fixtures: db_session, operaciones_test, areas_test, socios_test.
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from app.repositories.operations_repository import OperationsRepository
from app.models import Operacion, TipoOperacion, Localidad, Moneda
from app.models.area import Area
import uuid


class TestOperationsRepositoryGetById:
    """Tests para get_by_id."""

    def test_get_by_id_returns_operacion_when_exists(
        self, db_session, operaciones_test
    ):
        op = operaciones_test[0]
        repo = OperationsRepository(db_session)
        found = repo.get_by_id(str(op.id))
        assert found is not None
        assert found.id == op.id
        assert found.descripcion == op.descripcion

    def test_get_by_id_returns_none_when_not_exists(self, db_session):
        repo = OperationsRepository(db_session)
        found = repo.get_by_id(str(uuid.uuid4()))
        assert found is None


class TestOperationsRepositoryGetAll:
    """Tests para get_all con paginación."""

    def test_get_all_returns_operaciones_ordered_by_fecha_desc(
        self, db_session, operaciones_test
    ):
        repo = OperationsRepository(db_session)
        all_ops = repo.get_all(limit=20, offset=0)
        assert len(all_ops) > 0
        assert len(all_ops) <= 20
        # Debe venir ordenado por fecha desc
        for i in range(len(all_ops) - 1):
            assert all_ops[i].fecha >= all_ops[i + 1].fecha

    def test_get_all_respects_limit(self, db_session, operaciones_test):
        repo = OperationsRepository(db_session)
        page = repo.get_all(limit=3, offset=0)
        assert len(page) <= 3

    def test_get_all_respects_offset(self, db_session, operaciones_test):
        repo = OperationsRepository(db_session)
        first = repo.get_all(limit=2, offset=0)
        second = repo.get_all(limit=2, offset=2)
        if len(first) == 2 and len(second) >= 1:
            assert first[0].id != second[0].id or first[1].id != second[0].id

    def test_get_all_eager_loads_area(self, db_session, operaciones_test):
        repo = OperationsRepository(db_session)
        all_ops = repo.get_all(limit=5, offset=0)
        for op in all_ops:
            if op.area_id:
                assert op.area is not None
                assert hasattr(op.area, "nombre")


class TestOperationsRepositoryCount:
    """Tests para count con filtros."""

    def test_count_returns_total_without_filters(
        self, db_session, operaciones_test
    ):
        repo = OperationsRepository(db_session)
        total = repo.count()
        assert total == len(operaciones_test)

    def test_count_with_fecha_inicio_fin(
        self, db_session, operaciones_test
    ):
        repo = OperationsRepository(db_session)
        hoy = date.today()
        mes_pasado = hoy - timedelta(days=30)
        c = repo.count(fecha_inicio=mes_pasado, fecha_fin=hoy)
        assert c >= 0
        assert c <= len(operaciones_test)

    def test_count_with_tipo_operacion(self, db_session, operaciones_test):
        repo = OperationsRepository(db_session)
        c_ingreso = repo.count(tipo_operacion=TipoOperacion.INGRESO)
        c_gasto = repo.count(tipo_operacion=TipoOperacion.GASTO)
        assert c_ingreso >= 0
        assert c_gasto >= 0
        assert c_ingreso + c_gasto <= len(operaciones_test)

    def test_count_with_area_id(self, db_session, operaciones_test, areas_test):
        repo = OperationsRepository(db_session)
        area_id = areas_test["Jurídica"].id
        c = repo.count(area_id=str(area_id))
        assert c >= 0

    def test_count_with_localidad(self, db_session, operaciones_test):
        repo = OperationsRepository(db_session)
        c = repo.count(localidad=Localidad.MONTEVIDEO)
        assert c >= 0


class TestOperationsRepositoryGetByPeriod:
    """Tests para get_by_period."""

    def test_get_by_period_returns_operaciones_in_range(
        self, db_session, operaciones_test
    ):
        hoy = date.today()
        hace_90 = hoy - timedelta(days=90)
        repo = OperationsRepository(db_session)
        ops = repo.get_by_period(fecha_inicio=hace_90, fecha_fin=hoy)
        assert len(ops) == len(operaciones_test)
        for op in ops:
            assert hace_90 <= op.fecha <= hoy

    def test_get_by_period_with_tipo_filter(
        self, db_session, operaciones_test
    ):
        hoy = date.today()
        hace_90 = hoy - timedelta(days=90)
        repo = OperationsRepository(db_session)
        ops = repo.get_by_period(
            fecha_inicio=hace_90,
            fecha_fin=hoy,
            tipo_operacion=TipoOperacion.INGRESO,
        )
        for op in ops:
            assert op.tipo_operacion == TipoOperacion.INGRESO

    def test_get_by_period_with_area_id(
        self, db_session, operaciones_test, areas_test
    ):
        hoy = date.today()
        hace_90 = hoy - timedelta(days=90)
        repo = OperationsRepository(db_session)
        area_id = areas_test["Jurídica"].id
        ops = repo.get_by_period(
            fecha_inicio=hace_90,
            fecha_fin=hoy,
            area_id=str(area_id),
        )
        for op in ops:
            assert op.area_id == area_id

    def test_get_by_period_with_localidad(
        self, db_session, operaciones_test
    ):
        hoy = date.today()
        hace_90 = hoy - timedelta(days=90)
        repo = OperationsRepository(db_session)
        ops = repo.get_by_period(
            fecha_inicio=hace_90,
            fecha_fin=hoy,
            localidad=Localidad.MERCEDES,
        )
        for op in ops:
            assert op.localidad == Localidad.MERCEDES

    def test_get_by_period_empty_range_returns_empty(self, db_session):
        repo = OperationsRepository(db_session)
        d = date(2000, 1, 1)
        ops = repo.get_by_period(fecha_inicio=d, fecha_fin=d)
        assert ops == []


class TestOperationsRepositoryGetIngresosMensualesHistorico:
    """Tests para get_ingresos_mensuales_historico."""

    def test_get_ingresos_mensuales_historico_returns_list(
        self, db_session, operaciones_test
    ):
        repo = OperationsRepository(db_session)
        fecha_fin = date.today()
        historico = repo.get_ingresos_mensuales_historico(
            fecha_fin_reporte=fecha_fin, meses=12
        )
        assert isinstance(historico, list)
        assert all(isinstance(x, (int, float)) for x in historico)

    def test_get_ingresos_mensuales_historico_respects_meses(
        self, db_session, operaciones_test
    ):
        repo = OperationsRepository(db_session)
        fecha_fin = date.today()
        historico = repo.get_ingresos_mensuales_historico(
            fecha_fin_reporte=fecha_fin, meses=6
        )
        assert len(historico) <= 6


class TestOperationsRepositoryGetTopOperaciones:
    """Tests para get_top_operaciones."""

    def test_get_top_operaciones_returns_list_of_dicts(
        self, db_session, operaciones_test
    ):
        hoy = date.today()
        hace_90 = hoy - timedelta(days=90)
        repo = OperationsRepository(db_session)
        top = repo.get_top_operaciones(
            fecha_inicio=hace_90,
            fecha_fin=hoy,
            tipo_operacion=TipoOperacion.INGRESO,
            limit=5,
        )
        assert isinstance(top, list)
        for item in top:
            assert isinstance(item, dict)
            assert "fecha" in item
            assert "concepto" in item
            assert "area" in item
            assert "monto_uyu" in item
            assert "monto_usd" in item

    def test_get_top_operaciones_respects_limit(
        self, db_session, operaciones_test
    ):
        hoy = date.today()
        hace_90 = hoy - timedelta(days=90)
        repo = OperationsRepository(db_session)
        top = repo.get_top_operaciones(
            fecha_inicio=hace_90,
            fecha_fin=hoy,
            tipo_operacion=TipoOperacion.INGRESO,
            limit=2,
        )
        assert len(top) <= 2


class TestOperationsRepositoryGetByTipo:
    """Tests para get_by_tipo."""

    def test_get_by_tipo_returns_operaciones_of_type(
        self, db_session, operaciones_test
    ):
        repo = OperationsRepository(db_session)
        ops = repo.get_by_tipo(TipoOperacion.INGRESO, limit=20)
        for op in ops:
            assert op.tipo_operacion == TipoOperacion.INGRESO

    def test_get_by_tipo_with_fecha_filters(
        self, db_session, operaciones_test
    ):
        hoy = date.today()
        mes_pasado = hoy - timedelta(days=30)
        repo = OperationsRepository(db_session)
        ops = repo.get_by_tipo(
            TipoOperacion.GASTO,
            fecha_inicio=mes_pasado,
            fecha_fin=hoy,
            limit=20,
        )
        for op in ops:
            assert op.tipo_operacion == TipoOperacion.GASTO
            assert mes_pasado <= op.fecha <= hoy

    def test_get_by_tipo_respects_limit(
        self, db_session, operaciones_test
    ):
        repo = OperationsRepository(db_session)
        ops = repo.get_by_tipo(TipoOperacion.INGRESO, limit=3)
        assert len(ops) <= 3
