"""
Tests unitarios para expediente_service.py

Testea funciones de sincronización, consulta y utilidades.
Mockea SOAP y BD para aislamiento.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from uuid import uuid4
from datetime import datetime, date, timezone

from app.services.expediente_service import (
    consultar_expediente_ws,
    sincronizar_expediente,
    obtener_expediente_por_iue,
    listar_expedientes_activos,
    obtener_movimientos_sin_notificar,
    marcar_movimientos_notificados,
    obtener_resumen_sincronizacion,
    _limpiar_html,
    _parsear_fecha,
    ESTADO_NO_ENCONTRADO,
)


# ============================================================================
# UTILIDADES
# ============================================================================


class TestLimpiarHtml:
    def test_limpia_br_tags(self):
        assert _limpiar_html("Hola<br>mundo") == "Hola mundo"
        assert _limpiar_html("Hola<br/>mundo") == "Hola mundo"
        assert _limpiar_html("Hola<br />mundo") == "Hola mundo"

    def test_limpia_tags_genericos(self):
        assert _limpiar_html("<b>negrita</b>") == "negrita"
        assert _limpiar_html("<span class='x'>texto</span>") == "texto"

    def test_limpia_espacios_multiples(self):
        assert _limpiar_html("  hola   mundo  ") == "hola mundo"

    def test_retorna_none_si_none(self):
        assert _limpiar_html(None) is None

    def test_retorna_vacio_si_vacio(self):
        assert _limpiar_html("") == ""


class TestParsearFecha:
    def test_fecha_valida(self):
        result = _parsear_fecha("15/03/2024")
        assert result == date(2024, 3, 15)

    def test_fecha_invalida(self):
        assert _parsear_fecha("no-es-fecha") is None

    def test_fecha_vacia(self):
        assert _parsear_fecha("") is None
        assert _parsear_fecha(None) is None


# ============================================================================
# CONSULTA WS
# ============================================================================


class TestConsultarExpedienteWs:
    @patch("app.services.expediente_service._obtener_cliente_soap")
    def test_expediente_encontrado(self, mock_soap):
        mock_client = MagicMock()
        mock_client.service.consultaIUE.return_value = {
            "estado": "DATOS DEL EXPEDIENTE",
            "caratula": "PEREZ c/ GOMEZ",
            "origen": "Juzgado Civil 1",
            "movimientos": [],
        }
        mock_soap.return_value = mock_client

        with patch("app.services.expediente_service.serialize_object", side_effect=lambda x: x):
            result = consultar_expediente_ws("2-12345/2023")

        assert result is not None
        assert result["caratula"] == "PEREZ c/ GOMEZ"

    @patch("app.services.expediente_service._obtener_cliente_soap")
    def test_expediente_no_encontrado(self, mock_soap):
        mock_client = MagicMock()
        mock_client.service.consultaIUE.return_value = {
            "estado": "EL EXPEDIENTE NO SE ENCUENTRA EN EL SISTEMA"
        }
        mock_soap.return_value = mock_client

        with patch("app.services.expediente_service.serialize_object", side_effect=lambda x: x):
            result = consultar_expediente_ws("2-99999/2023")

        assert result is None

    def test_iue_formato_invalido(self):
        with pytest.raises(ValueError):
            consultar_expediente_ws("formato-invalido")


# ============================================================================
# SINCRONIZACIÓN
# ============================================================================


class TestSincronizarExpediente:
    @patch("app.services.expediente_service.consultar_expediente_ws")
    def test_crea_expediente_nuevo(self, mock_ws):
        mock_ws.return_value = {
            "estado": "DATOS DEL EXPEDIENTE",
            "caratula": "CASO TEST",
            "origen": "Juzgado 1",
            "abogado_actor": "Dr. Test",
            "abogado_demandante": None,
            "movimientos": [],
        }

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.count.return_value = 0

        exp, nuevos = sincronizar_expediente(db, "2-10000/2024")

        assert db.add.called
        assert db.commit.called

    @patch("app.services.expediente_service.consultar_expediente_ws")
    def test_expediente_no_existe_en_ws(self, mock_ws):
        mock_ws.return_value = None
        db = MagicMock()

        exp, nuevos = sincronizar_expediente(db, "2-99999/2023")

        assert exp is None
        assert nuevos == 0


# ============================================================================
# CONSULTAS BD
# ============================================================================


class TestObtenerExpedientePorIue:
    def test_encuentra_expediente(self):
        mock_exp = MagicMock()
        mock_exp.iue = "2-12345/2023"

        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.first.return_value = mock_exp

        result = obtener_expediente_por_iue(db, "2-12345/2023")
        assert result.iue == "2-12345/2023"

    def test_no_encuentra_expediente(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.first.return_value = None

        result = obtener_expediente_por_iue(db, "2-99999/2023")
        assert result is None


class TestListarExpedientesActivos:
    def test_lista_sin_filtros(self):
        mock_exp = MagicMock()
        db = MagicMock()
        query = db.query.return_value.filter.return_value
        query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_exp]

        result = listar_expedientes_activos(db)
        assert len(result) == 1


class TestObtenerResumenSincronizacion:
    def test_resumen_basico(self):
        db = MagicMock()
        # Mock count() calls
        db.query.return_value.filter.return_value.count.return_value = 5
        db.query.return_value.filter.return_value.filter.return_value.count.return_value = 2
        db.query.return_value.join.return_value.filter.return_value.count.return_value = 1
        db.query.return_value.filter.return_value.scalar.return_value = datetime.now(timezone.utc)

        result = obtener_resumen_sincronizacion(db)
        assert "total_expedientes_activos" in result
        assert "sincronizados_hoy" in result
        assert "movimientos_sin_notificar" in result


class TestMarcarMovimientosNotificados:
    def test_marca_movimientos(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.update.return_value = 3

        result = marcar_movimientos_notificados(db, [str(uuid4()), str(uuid4()), str(uuid4())])
        assert result == 3
        assert db.commit.called

    def test_lista_vacia(self):
        db = MagicMock()
        result = marcar_movimientos_notificados(db, [])
        assert result == 0
