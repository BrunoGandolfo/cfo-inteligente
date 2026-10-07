"""
Tests del envío de mails vía Resend. La API se simula con httpx.MockTransport:
ningún test manda un mail real ni necesita la API key verdadera.
"""

import json
from unittest.mock import patch

import httpx
import pytest

from app.services import email_service
from app.services.email_service import RESEND_API_URL, enviar_email


def _cliente_simulado(handler):
    """Reemplaza httpx.AsyncClient por uno que responde con `handler`."""
    real = httpx.AsyncClient

    def fabrica(*args, **kwargs):
        return real(transport=httpx.MockTransport(handler), timeout=kwargs.get("timeout"))

    return patch.object(email_service.httpx, "AsyncClient", side_effect=fabrica)


@pytest.fixture
def con_api_key():
    with patch.object(email_service.settings, "resend_api_key", "re_test_key"), \
         patch.object(email_service.settings, "email_remitente", "CFO <onboarding@resend.dev>"):
        yield


class TestEnviarEmail:

    @pytest.mark.asyncio
    async def test_envio_exitoso_arma_el_pedido_correcto(self, con_api_key):
        pedidos = []

        def handler(request: httpx.Request) -> httpx.Response:
            pedidos.append(request)
            return httpx.Response(200, json={"id": "email-123"})

        with _cliente_simulado(handler):
            ok = await enviar_email("bruno@test.com", "Asunto", "<b>Hola</b>", "Hola")

        assert ok is True
        assert len(pedidos) == 1
        pedido = pedidos[0]
        assert str(pedido.url) == RESEND_API_URL
        assert pedido.headers["Authorization"] == "Bearer re_test_key"
        assert json.loads(pedido.content) == {
            "from": "CFO <onboarding@resend.dev>",
            "to": ["bruno@test.com"],
            "subject": "Asunto",
            "html": "<b>Hola</b>",
            "text": "Hola",
        }

    @pytest.mark.asyncio
    async def test_sin_api_key_no_intenta_enviar(self):
        def handler(request):
            raise AssertionError("No debería llamar a la API sin API key")

        with patch.object(email_service.settings, "resend_api_key", ""), \
             _cliente_simulado(handler):
            assert await enviar_email("bruno@test.com", "A", "<p>x</p>", "x") is False

    @pytest.mark.asyncio
    async def test_error_de_resend_devuelve_false(self, con_api_key):
        def handler(request):
            return httpx.Response(403, json={"message": "API key inválida"})

        with _cliente_simulado(handler):
            assert await enviar_email("bruno@test.com", "A", "<p>x</p>", "x") is False

    @pytest.mark.asyncio
    async def test_falla_de_red_devuelve_false_sin_lanzar(self, con_api_key):
        def handler(request):
            raise httpx.ConnectError("sin conexión", request=request)

        with _cliente_simulado(handler):
            assert await enviar_email("bruno@test.com", "A", "<p>x</p>", "x") is False

    @pytest.mark.asyncio
    async def test_nunca_loguea_la_api_key(self, con_api_key, caplog):
        def handler(request):
            return httpx.Response(500, text="error interno")

        with _cliente_simulado(handler):
            await enviar_email("bruno@test.com", "A", "<p>x</p>", "x")

        assert "re_test_key" not in caplog.text
