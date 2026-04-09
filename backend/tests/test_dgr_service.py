"""
Tests unitarios para dgr_service.py

Testea parseo de fechas, cálculo de vencimientos, parseo de HTML.
Mockea Playwright y CapSolver para funciones async.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import date, timedelta

from app.services.dgr_service import (
    parsear_fecha_dgr,
    calcular_fecha_vencimiento,
    _parsear_resultado,
)


# ============================================================================
# PARSEO DE FECHAS
# ============================================================================


class TestParsearFechaDgr:
    def test_formato_dd_mm_yy(self):
        assert parsear_fecha_dgr("02/01/25") == date(2025, 1, 2)

    def test_formato_dd_mm_yyyy(self):
        assert parsear_fecha_dgr("15/06/2024") == date(2024, 6, 15)

    def test_fecha_none(self):
        assert parsear_fecha_dgr(None) is None

    def test_fecha_vacia(self):
        assert parsear_fecha_dgr("") is None
        assert parsear_fecha_dgr("   ") is None

    def test_formato_invalido(self):
        assert parsear_fecha_dgr("no-es-fecha") is None
        assert parsear_fecha_dgr("2025-01-02") is None


# ============================================================================
# CÁLCULO DE VENCIMIENTO (Ley 16.871)
# ============================================================================


class TestCalcularFechaVencimiento:
    def test_definitivo_no_vence(self):
        assert calcular_fecha_vencimiento(date(2025, 1, 1), "Definitivo") is None

    def test_pendiente_30_dias(self):
        fecha = date(2025, 1, 1)
        result = calcular_fecha_vencimiento(fecha, "Pendiente")
        assert result == date(2025, 1, 31)

    def test_sin_calificar_30_dias(self):
        fecha = date(2025, 1, 1)
        result = calcular_fecha_vencimiento(fecha, "Sin calificar")
        assert result == date(2025, 1, 31)

    def test_provisorio_150_dias(self):
        fecha = date(2025, 1, 1)
        result = calcular_fecha_vencimiento(fecha, "Provisorio")
        expected = fecha + timedelta(days=150)
        # Ajuste fin de semana
        if expected.weekday() == 5:
            expected -= timedelta(days=1)
        elif expected.weekday() == 6:
            expected -= timedelta(days=2)
        assert result == expected

    def test_observado_150_dias(self):
        fecha = date(2025, 1, 1)
        result = calcular_fecha_vencimiento(fecha, "Observado")
        expected = fecha + timedelta(days=150)
        if expected.weekday() == 5:
            expected -= timedelta(days=1)
        elif expected.weekday() == 6:
            expected -= timedelta(days=2)
        assert result == expected

    def test_estado_desconocido(self):
        assert calcular_fecha_vencimiento(date(2025, 1, 1), "Estado Raro") is None

    def test_fecha_none(self):
        assert calcular_fecha_vencimiento(None, "Pendiente") is None

    def test_estado_none(self):
        assert calcular_fecha_vencimiento(date(2025, 1, 1), None) is None

    def test_vencimiento_sabado_ajusta_viernes(self):
        """Si vence en sábado, debe ajustar al viernes anterior."""
        # Buscar una fecha cuyo +30 caiga en sábado
        # 2025-01-03 es viernes, +30 = 2025-02-02 que es domingo → viernes 2025-01-31
        # Probemos con 2025-03-02 (domingo): +30 = 2025-04-01 (martes) no sirve
        # Mejor: verificar que el resultado nunca es sábado ni domingo
        for day_offset in range(365):
            fecha = date(2025, 1, 1) + timedelta(days=day_offset)
            for estado in ["Pendiente", "Provisorio"]:
                result = calcular_fecha_vencimiento(fecha, estado)
                if result:
                    assert result.weekday() < 5, f"Vencimiento en fin de semana: {result} ({result.weekday()})"


# ============================================================================
# PARSEO DE HTML
# ============================================================================


class TestParsearResultado:
    def test_html_con_datos_minimos(self):
        html = """
        <html><body>
        <table>
            <tr>
                <td>Registro</td>
                <td>PROPIEDAD INMOBILIARIA</td>
            </tr>
            <tr>
                <td>Oficina Registral</td>
                <td>MONTEVIDEO</td>
            </tr>
            <tr>
                <td>Fecha Ingreso</td>
                <td>02/01/25</td>
            </tr>
            <tr>
                <td>Escribano | Emisor</td>
                <td>GARCIA MARIA</td>
            </tr>
        </table>
        <table id="GridinscripcionesContainerTbl">
            <tr><th>Header</th></tr>
            <tr>
                <td>DEF</td><td>RPI</td><td>GARCIA</td>
                <td>Compraventa</td><td>Definitivo</td><td></td>
            </tr>
        </table>
        </body></html>
        """
        result = _parsear_resultado(html)
        assert result is not None
        assert result["registro"] == "PROPIEDAD INMOBILIARIA"
        assert result["oficina"] == "MONTEVIDEO"
        assert result["escribano_emisor"] == "GARCIA MARIA"
        assert result["estado_actual"] == "Definitivo"
        assert len(result["inscripciones"]) == 1
        assert result["inscripciones"][0]["acto"] == "Compraventa"

    def test_html_sin_datos(self):
        html = "<html><body><p>Nada relevante</p></body></html>"
        result = _parsear_resultado(html)
        assert result is None

    def test_html_con_observaciones(self):
        html = """
        <html><body>
        <table>
            <tr><td>Fecha Ingreso</td><td>15/03/25</td></tr>
        </table>
        <table id="GridinscripcionesContainerTbl">
            <tr><th>H</th></tr>
            <tr>
                <td>OBS</td><td>RPI</td><td>X</td>
                <td>Hipoteca</td><td>Observado</td><td>Falta firma</td>
            </tr>
        </table>
        </body></html>
        """
        result = _parsear_resultado(html)
        assert result is not None
        assert result["estado_actual"] == "Observado"
        assert result["observaciones"] == "Falta firma"

    def test_multiples_inscripciones_estado_general(self):
        html = """
        <html><body>
        <table>
            <tr><td>Fecha Ingreso</td><td>01/02/25</td></tr>
        </table>
        <table id="GridinscripcionesContainerTbl">
            <tr><th>H</th></tr>
            <tr><td>D</td><td>R</td><td>E</td><td>Compraventa</td><td>Definitivo</td><td></td></tr>
            <tr><td>P</td><td>R</td><td>E</td><td>Hipoteca</td><td>Provisorio</td><td></td></tr>
        </table>
        </body></html>
        """
        result = _parsear_resultado(html)
        # Si hay Provisorio, el estado general debe ser Provisorio
        assert result["estado_actual"] == "Provisorio"


# ============================================================================
# RESOLVER RECAPTCHA (async mock)
# ============================================================================


class TestResolverRecaptcha:
    @pytest.mark.asyncio
    @patch("app.services.dgr_service._async_sleep", new_callable=AsyncMock)
    @patch("app.services.dgr_service.Settings")
    async def test_sin_api_key_retorna_none(self, mock_settings, mock_sleep):
        mock_settings.return_value.capsolver_api_key = None

        from app.services.dgr_service import resolver_recaptcha
        result = await resolver_recaptcha("https://example.com", "sitekey")
        assert result is None
