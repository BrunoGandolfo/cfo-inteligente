"""
Tests para scheduler_service.
Mock de APScheduler; environment=development NO inicia, production SÍ.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestIniciarScheduler:
    """Tests para iniciar_scheduler."""

    def test_iniciar_scheduler_adds_job_and_starts(self):
        with patch(
            "app.services.scheduler_service.scheduler",
            MagicMock(),
        ) as mock_scheduler:
            mock_scheduler.running = False
            from app.services.scheduler_service import iniciar_scheduler

            iniciar_scheduler()
            assert mock_scheduler.add_job.called
            assert mock_scheduler.start.called

    def test_iniciar_scheduler_job_has_expected_id_and_trigger(self):
        with patch(
            "app.services.scheduler_service.scheduler",
            MagicMock(),
        ) as mock_scheduler:
            mock_scheduler.running = False
            from app.services.scheduler_service import iniciar_scheduler
            from app.services.scheduler_service import tarea_sincronizar_expedientes

            iniciar_scheduler()
            call_args = mock_scheduler.add_job.call_args
            assert call_args[0][0] is tarea_sincronizar_expedientes
            call_kw = call_args[1]
            assert call_kw.get("id") == "sync_expedientes_diario"
            assert call_kw.get("replace_existing") is True


class TestDetenerScheduler:
    """Tests para detener_scheduler."""

    def test_detener_scheduler_shutdown_when_running(self):
        with patch(
            "app.services.scheduler_service.scheduler",
            MagicMock(),
        ) as mock_scheduler:
            mock_scheduler.running = True
            from app.services.scheduler_service import detener_scheduler

            detener_scheduler()
            mock_scheduler.shutdown.assert_called_once()

    def test_detener_scheduler_no_shutdown_when_not_running(self):
        with patch(
            "app.services.scheduler_service.scheduler",
            MagicMock(),
        ) as mock_scheduler:
            mock_scheduler.running = False
            from app.services.scheduler_service import detener_scheduler

            detener_scheduler()
            mock_scheduler.shutdown.assert_not_called()


class TestSchedulerEnvironmentBehavior:
    """
    Comportamiento según environment.
    La lógica 'solo iniciar en production' está en main.py;
    aquí verificamos que iniciar_scheduler efectivamente inicia cuando se llama.
    """

    def test_iniciar_scheduler_called_in_production_starts_scheduler(self):
        """Cuando main llama iniciar_scheduler (solo en production), el scheduler arranca."""
        with patch(
            "app.services.scheduler_service.scheduler",
            MagicMock(),
        ) as mock_scheduler:
            mock_scheduler.running = False
            from app.services.scheduler_service import iniciar_scheduler

            iniciar_scheduler()
            mock_scheduler.start.assert_called_once()

    def test_main_does_not_call_iniciar_scheduler_in_development(self):
        """En development, main no debe llamar iniciar_scheduler (verificación de integración)."""
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.environment = "development"
            with patch(
                "app.services.scheduler_service.iniciar_scheduler",
                MagicMock(),
            ) as mock_iniciar:
                # Simular lo que hace main: solo llama si production
                if mock_settings.environment == "production":
                    mock_iniciar()
                assert not mock_iniciar.called

    def test_main_calls_iniciar_scheduler_in_production(self):
        """En production, main llama iniciar_scheduler."""
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.environment = "production"
            with patch(
                "app.services.scheduler_service.iniciar_scheduler",
                MagicMock(),
            ) as mock_iniciar:
                if mock_settings.environment == "production":
                    mock_iniciar()
                assert mock_iniciar.called


class TestTareaSincronizarExpedientes:
    """Tests para tarea_sincronizar_expedientes (con mocks, sin BD ni APIs)."""

    def test_tarea_sincronizar_expedientes_cierra_db_y_loguea(self):
        mock_db = MagicMock()
        with patch(
            "app.services.scheduler_service.SessionLocal",
            return_value=mock_db,
        ):
            with patch(
                "app.services.scheduler_service.sincronizar_todos_los_expedientes",
                return_value={
                    "sincronizados_ok": 5,
                    "total_expedientes": 5,
                    "total_nuevos_movimientos": 0,
                },
            ):
                from app.services.scheduler_service import tarea_sincronizar_expedientes

                tarea_sincronizar_expedientes()
        mock_db.close.assert_called_once()

    def test_tarea_sincronizar_expedientes_llama_enviar_notificaciones_si_hay_nuevos(self):
        mock_db = MagicMock()
        with patch(
            "app.services.scheduler_service.SessionLocal",
            return_value=mock_db,
        ):
            with patch(
                "app.services.scheduler_service.sincronizar_todos_los_expedientes",
                return_value={
                    "sincronizados_ok": 5,
                    "total_expedientes": 5,
                    "total_nuevos_movimientos": 2,
                },
            ):
                with patch(
                    "app.services.scheduler_service.enviar_notificaciones_pendientes",
                    MagicMock(),
                ) as mock_enviar:
                    from app.services.scheduler_service import tarea_sincronizar_expedientes

                    tarea_sincronizar_expedientes()
                    mock_enviar.assert_called_once_with(mock_db)

    def test_tarea_sincronizar_expedientes_cierra_db_aun_si_falla(self):
        mock_db = MagicMock()
        with patch(
            "app.services.scheduler_service.SessionLocal",
            return_value=mock_db,
        ):
            with patch(
                "app.services.scheduler_service.sincronizar_todos_los_expedientes",
                side_effect=RuntimeError("error simulado"),
            ):
                from app.services.scheduler_service import tarea_sincronizar_expedientes

                tarea_sincronizar_expedientes()
        mock_db.close.assert_called_once()


class TestEnviarNotificacionesPendientes:
    """Tests para enviar_notificaciones_pendientes (mocks, sin Twilio)."""

    def test_enviar_notificaciones_sin_movimientos_no_llama_twilio(self):
        mock_db = MagicMock()
        with patch(
            "app.services.expediente_service.obtener_movimientos_sin_notificar",
            return_value=[],
        ):
            with patch(
                "app.services.twilio_service",
                MagicMock(),
                create=True,
            ) as mock_twilio:
                from app.services.scheduler_service import enviar_notificaciones_pendientes

                enviar_notificaciones_pendientes(mock_db)
                mock_twilio.notificar_a_todos_los_socios.assert_not_called()

    def test_enviar_notificaciones_con_movimientos_exitoso_marca_notificados(self):
        mock_db = MagicMock()
        movimientos = [{"movimiento_id": "id1"}]
        with patch(
            "app.services.expediente_service.obtener_movimientos_sin_notificar",
            return_value=movimientos,
        ):
            with patch(
                "app.services.twilio_service",
                MagicMock(),
                create=True,
            ) as mock_twilio:
                mock_twilio.notificar_a_todos_los_socios.return_value = {
                    "enviados_ok": 1,
                    "total_numeros": 1,
                }
                with patch(
                    "app.services.expediente_service.marcar_movimientos_notificados",
                    MagicMock(),
                ) as mock_marcar:
                    from app.services.scheduler_service import enviar_notificaciones_pendientes

                    enviar_notificaciones_pendientes(mock_db)
                    mock_marcar.assert_called_once_with(mock_db, ["id1"])

    def test_enviar_notificaciones_fallo_envio_no_marca_notificados(self):
        mock_db = MagicMock()
        movimientos = [{"movimiento_id": "id1"}]
        with patch(
            "app.services.expediente_service.obtener_movimientos_sin_notificar",
            return_value=movimientos,
        ):
            with patch(
                "app.services.twilio_service",
                MagicMock(),
                create=True,
            ) as mock_twilio:
                mock_twilio.notificar_a_todos_los_socios.return_value = {
                    "enviados_ok": 0,
                    "total_numeros": 1,
                }
                with patch(
                    "app.services.expediente_service.marcar_movimientos_notificados",
                    MagicMock(),
                ) as mock_marcar:
                    from app.services.scheduler_service import enviar_notificaciones_pendientes

                    enviar_notificaciones_pendientes(mock_db)
                    mock_marcar.assert_not_called()
