"""
Tests del mail diario de actividad: armado del mensaje (asunto, HTML, texto)
y la tarea programada. El envío se simula; no sale ningún mail real.
"""

from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import resumen_actividad_notificacion as notif
from app.services.resumen_actividad_notificacion import (
    construir_mail,
    enviar_resumen_actividad,
    tarea_enviar_resumen_actividad,
)
from app.services.resumen_actividad_service import (
    TZ_URUGUAY,
    ActividadUsuario,
    AlertaLocalidad,
    ResumenActividad,
)

HASTA = datetime(2026, 10, 7, 20, 0, tzinfo=TZ_URUGUAY)   # miércoles
DESDE = datetime(2026, 10, 6, 20, 0, tzinfo=TZ_URUGUAY)   # martes


def _resumen(usuarios=(), alertas=()):
    return ResumenActividad(desde=DESDE, hasta=HASTA, usuarios=list(usuarios), alertas=list(alertas))


class TestConstruirMail:

    def test_con_actividad(self):
        mail = construir_mail(_resumen([
            ActividadUsuario("Ana", 12, 2, 0),
            ActividadUsuario("Juan", 3, 0, 1),
        ]))

        assert mail.asunto == "Actividad de registro — miércoles 7/10"
        assert "Del martes 6/10 20:00 al miércoles 7/10 20:00" in mail.texto
        assert "Ana — cargadas: 12 · editadas: 2 · anuladas: 0" in mail.texto
        assert "Juan — cargadas: 3 · editadas: 0 · anuladas: 1" in mail.texto
        assert "<td" in mail.html and "Ana" in mail.html

    def test_sin_actividad_lo_dice_en_el_asunto(self):
        mail = construir_mail(_resumen())

        assert mail.asunto.endswith("(sin actividad)")
        assert "Sin actividad en el período." in mail.texto
        assert "Sin actividad en el período." in mail.html

    def test_alertas_de_localidad(self):
        mail = construir_mail(_resumen(alertas=[
            AlertaLocalidad("Montevideo", date(2026, 9, 27), 10),
            AlertaLocalidad("Mercedes", None, None),
        ]))

        assert "⚠️" in mail.asunto
        assert "Montevideo: sin cargas hace 10 días (última: 27/9)" in mail.texto
        assert "Mercedes: nunca tuvo operaciones cargadas" in mail.texto
        assert "Montevideo: sin cargas hace 10 días" in mail.html

    def test_escapa_html_en_nombres(self):
        mail = construir_mail(_resumen([ActividadUsuario("<script>x</script>", 1, 0, 0)]))

        assert "<script>" not in mail.html
        assert "&lt;script&gt;" in mail.html


class TestEnvio:

    @pytest.mark.asyncio
    async def test_envia_al_destinatario_configurado(self):
        db = MagicMock()
        with patch.object(notif, "obtener_resumen", return_value=_resumen()) as obtener, \
             patch.object(notif, "enviar_email", new=AsyncMock(return_value=True)) as enviar, \
             patch.object(notif.settings, "email_resumen_actividad", "bruno@test.com"):
            ok = await enviar_resumen_actividad(db, HASTA)

        assert ok is True
        obtener.assert_called_once_with(db, HASTA)
        destinatario, asunto, html, texto = enviar.call_args.args
        assert destinatario == "bruno@test.com"
        assert asunto.startswith("Actividad de registro")

    def test_tarea_cierra_la_sesion(self):
        db = MagicMock()
        with patch.object(notif, "SessionLocal", return_value=db), \
             patch.object(notif, "enviar_resumen_actividad", new=AsyncMock(return_value=True)):
            tarea_enviar_resumen_actividad()

        db.close.assert_called_once()

    def test_tarea_no_propaga_errores_y_cierra_la_sesion(self):
        db = MagicMock()
        with patch.object(notif, "SessionLocal", return_value=db), \
             patch.object(notif, "enviar_resumen_actividad",
                          new=AsyncMock(side_effect=RuntimeError("falla"))):
            tarea_enviar_resumen_actividad()  # no debe lanzar

        db.close.assert_called_once()
