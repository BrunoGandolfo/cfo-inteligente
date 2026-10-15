"""
Tests de los interruptores de funcionalidades externas (DGR, DGI, Telegram)
y del cierre seguro de playwright.

Regla: una funcionalidad se prende solo con flag en true Y credencial
configurada. En producción, sin esas credenciales, las tres están apagadas.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core import funcionalidades
from app.core.config import settings
from app.services.playwright_cierre import cerrar_playwright


def _config(**valores):
    """Parchea varios campos de settings a la vez."""
    parches = [patch.object(settings, k, v) for k, v in valores.items()]
    for p in parches:
        p.start()
    return parches


@pytest.fixture
def config():
    parches = []

    def aplicar(**valores):
        parches.extend(_config(**valores))

    yield aplicar
    for p in parches:
        p.stop()


class TestReglaFlagMasCredencial:

    @pytest.mark.parametrize("flag, clave, esperado", [
        (False, "", False),
        (False, "clave", False),   # credencial sola no prende
        (True, "", False),         # flag solo no prende
        (True, "clave", True),
    ])
    def test_dgr(self, config, flag, clave, esperado):
        config(dgr_habilitado=flag, capsolver_api_key=clave)
        assert funcionalidades.dgr_habilitado() is esperado

    @pytest.mark.parametrize("flag, clave, esperado", [
        (False, "", False), (True, "", False), (False, "clave", False), (True, "clave", True),
    ])
    def test_dgi(self, config, flag, clave, esperado):
        config(dgi_consultas_habilitadas=flag, capsolver_api_key=clave)
        assert funcionalidades.dgi_consultas_habilitadas() is esperado

    @pytest.mark.parametrize("flag, token, esperado", [
        (False, "", False), (True, "", False), (False, "token", False), (True, "token", True),
    ])
    def test_telegram(self, config, flag, token, esperado):
        config(telegram_habilitado=flag, telegram_bot_token=token)
        assert funcionalidades.telegram_habilitado() is esperado

    def test_por_defecto_todo_apagado(self):
        """Los defaults del código dejan todo apagado aunque haya credenciales."""
        campos = settings.model_fields
        assert campos["dgr_habilitado"].default is False
        assert campos["dgi_consultas_habilitadas"].default is False
        assert campos["telegram_habilitado"].default is False


class TestExigirHabilitada:

    @pytest.mark.parametrize("nombre, palabra", [
        ("dgr", "DGR"), ("dgi", "DGI"), ("telegram", "Telegram"),
    ])
    def test_apagada_corta_con_503_y_motivo(self, config, nombre, palabra):
        config(dgr_habilitado=False, dgi_consultas_habilitadas=False, telegram_habilitado=False)
        with pytest.raises(HTTPException) as exc:
            funcionalidades.exigir_habilitada(nombre)
        assert exc.value.status_code == 503
        assert palabra in exc.value.detail

    def test_prendida_no_corta(self, config):
        config(telegram_habilitado=True, telegram_bot_token="token")
        funcionalidades.exigir_habilitada("telegram")  # no lanza

    def test_resumen_estado(self, config):
        config(dgr_habilitado=False, dgi_consultas_habilitadas=False,
               telegram_habilitado=True, telegram_bot_token="token")
        assert funcionalidades.resumen_estado() == {"dgr": False, "dgi": False, "telegram": True}


class TestEndpointsDesactivados:
    """Los endpoints que dependen de servicios apagados no abren nada."""

    def test_sincronizar_tramite_dgr_devuelve_503_sin_consultar(self, config):
        from app.api import tramites_dgr

        config(dgr_habilitado=False)
        with patch.object(tramites_dgr, "consultar_tramite_dgr", new=AsyncMock()) as consultar, \
             patch.object(tramites_dgr, "_obtener_tramite_o_404") as obtener:
            with pytest.raises(HTTPException) as exc:
                asyncio.run(tramites_dgr.sincronizar_tramite("id", MagicMock(), MagicMock()))

        assert exc.value.status_code == 503
        consultar.assert_not_awaited()
        obtener.assert_not_called()

    def test_crear_tramite_dgr_se_registra_sin_consultar(self, config):
        """Con la DGR apagada el trámite se guarda igual, sin abrir el navegador."""
        from app.api import tramites_dgr

        config(dgr_habilitado=False)
        socio = MagicMock(es_socio=True)
        data = MagicMock(registro="R", oficina="O", anio=2026, numero_entrada=1, bis="")
        db = MagicMock()
        with patch.object(tramites_dgr, "consultar_tramite_dgr", new=AsyncMock()) as consultar, \
             patch.object(tramites_dgr.tramites_dgr_service, "verificar_duplicado", return_value=None), \
             patch.object(tramites_dgr.tramites_dgr_service, "crear_tramite") as crear, \
             patch.object(tramites_dgr.tramites_dgr_service, "aplicar_datos_dgr") as aplicar:
            asyncio.run(tramites_dgr.crear_tramite(data, db, socio))

        crear.assert_called_once()
        consultar.assert_not_awaited()
        aplicar.assert_not_called()
        db.commit.assert_called_once()

    def test_vincular_telegram_devuelve_503(self, config):
        from app.api.auth import vincular_telegram

        config(telegram_habilitado=False)
        with pytest.raises(HTTPException) as exc:
            vincular_telegram(MagicMock(), MagicMock(), MagicMock(es_socio=True))
        assert exc.value.status_code == 503

    @pytest.mark.parametrize("endpoint", ["enviar_notificacion_test", "enviar_notificacion_movimientos"])
    def test_notificaciones_expedientes_devuelven_503(self, config, endpoint):
        from app.api import expedientes

        config(telegram_habilitado=False)
        with patch.object(expedientes, "enviar_mensaje_telegram", new=AsyncMock()) as enviar, \
             patch.object(expedientes, "_verificar_socio"):
            with pytest.raises(HTTPException) as exc:
                getattr(expedientes, endpoint)(MagicMock(), MagicMock(), MagicMock(es_socio=True))
        assert exc.value.status_code == 503
        enviar.assert_not_awaited()


class TestCerrarPlaywright:

    def test_cierra_ambos(self):
        browser, pw = MagicMock(close=AsyncMock()), MagicMock(stop=AsyncMock())
        asyncio.run(cerrar_playwright(browser, pw, "test"))
        browser.close.assert_awaited_once()
        pw.stop.assert_awaited_once()

    def test_si_falla_el_navegador_igual_detiene_playwright(self):
        browser = MagicMock(close=AsyncMock(side_effect=RuntimeError("handler is closed")))
        pw = MagicMock(stop=AsyncMock())
        asyncio.run(cerrar_playwright(browser, pw, "test"))  # no lanza
        pw.stop.assert_awaited_once()

    def test_si_falla_detener_no_lanza(self):
        pw = MagicMock(stop=AsyncMock(side_effect=RuntimeError("ya cerrado")))
        asyncio.run(cerrar_playwright(None, pw, "test"))

    def test_sin_nada_que_cerrar(self):
        asyncio.run(cerrar_playwright(None, None, "test"))


@pytest.mark.parametrize("modulo, funcion, args", [
    ("app.services.dgi_service", "consultar_certificado_unico", ("211234560018", "12345678")),
    ("app.services.dgi_afiliacion_service", "consultar_afiliacion_bancaria", ("211234560018",)),
])
def test_consultas_dgi_detienen_playwright_aunque_fallen(modulo, funcion, args):
    """Las dos consultas DGI que antes no llamaban pw.stop() ahora lo hacen."""
    import importlib

    page = MagicMock(goto=AsyncMock(side_effect=TimeoutError("timeout")))
    context = MagicMock(new_page=AsyncMock(return_value=page))
    browser = MagicMock(new_context=AsyncMock(return_value=context), close=AsyncMock())
    pw = MagicMock(stop=AsyncMock())
    pw.chromium.launch = AsyncMock(return_value=browser)
    fabrica = MagicMock()
    fabrica.return_value.start = AsyncMock(return_value=pw)

    mod = importlib.import_module(modulo)
    with patch("playwright.async_api.async_playwright", fabrica):
        asyncio.run(getattr(mod, funcion)(*args))

    pw.stop.assert_awaited_once()


class TestTelegramPuntoUnicoDeSalida:
    """El interruptor se aplica en enviar_mensaje_telegram: ningún llamador lo esquiva."""

    def test_apagado_con_token_no_llama_a_la_api(self, config):
        from app.services import telegram_service

        config(telegram_habilitado=False, telegram_bot_token="token-cargado")
        with patch.object(telegram_service.httpx, "AsyncClient") as cliente:
            enviado = asyncio.run(telegram_service.enviar_mensaje_telegram(123, "alerta DGR"))
        assert enviado is False
        cliente.assert_not_called()

    def test_prendido_envia(self, config):
        import httpx
        from app.services import telegram_service

        config(telegram_habilitado=True, telegram_bot_token="token-cargado")
        real = httpx.AsyncClient
        transporte = httpx.MockTransport(lambda req: httpx.Response(200, json={"ok": True}))
        with patch.object(telegram_service.httpx, "AsyncClient",
                          side_effect=lambda *a, **k: real(transport=transporte)):
            enviado = asyncio.run(telegram_service.enviar_mensaje_telegram(123, "hola"))
        assert enviado is True


def test_con_telegram_prendido_se_envian_pendientes_aunque_no_haya_nuevos():
    """Al prender Telegram, lo acumulado mientras estuvo apagado sale en la próxima corrida."""
    mock_db = MagicMock()
    with patch("app.services.scheduler_service.SessionLocal", return_value=mock_db), \
         patch("app.services.scheduler_service.sincronizar_todos_los_expedientes",
               return_value={"sincronizados_ok": 4, "total_expedientes": 4,
                             "total_nuevos_movimientos": 0}), \
         patch("app.services.scheduler_service.enviar_notificaciones_pendientes") as enviar, \
         patch("app.services.scheduler_service.telegram_habilitado", return_value=True):
        from app.services.scheduler_service import tarea_sincronizar_expedientes
        tarea_sincronizar_expedientes()
    enviar.assert_called_once_with(mock_db)
