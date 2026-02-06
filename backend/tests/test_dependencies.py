"""
Tests para app.core.dependencies.
Mock de DB session y env donde sea necesario.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.core import dependencies


class TestGetDb:
    """Tests para get_db."""

    def test_get_db_yields_session_and_closes(self):
        mock_session = MagicMock()
        with patch("app.core.dependencies.SessionLocal", return_value=mock_session):
            gen = dependencies.get_db()
            db = next(gen)
            assert db is mock_session
            try:
                next(gen)
            except StopIteration:
                pass
            mock_session.close.assert_called_once()


class TestGetClaudeClient:
    """Tests para get_claude_client (singleton)."""

    def test_get_claude_client_raises_when_no_api_key(self):
        with patch.dict("os.environ", {}, clear=False):
            # Limpiar cache para que lea de nuevo el env
            dependencies.get_claude_client.cache_clear()
            with pytest.raises(ValueError) as exc_info:
                dependencies.get_claude_client()
            assert "ANTHROPIC_API_KEY" in str(exc_info.value)
            dependencies.get_claude_client.cache_clear()

    def test_get_claude_client_returns_client_when_api_key_set(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test-key"}):
            dependencies.get_claude_client.cache_clear()
            with patch("app.core.dependencies.ClaudeClient") as mock_claude:
                mock_instance = MagicMock()
                mock_claude.return_value = mock_instance
                result = dependencies.get_claude_client()
                assert result is mock_instance
                mock_claude.assert_called_once_with(api_key="sk-test-key")
            dependencies.get_claude_client.cache_clear()


class TestGetChartConfig:
    """Tests para get_chart_config."""

    def test_get_chart_config_moderna_2024_returns_expected_keys(self):
        config = dependencies.get_chart_config(paleta="moderna_2024")
        assert "primary" in config
        assert "success" in config
        assert "danger" in config
        assert "warning" in config
        assert "secondary" in config
        assert "extended" in config
        assert "width_default" in config
        assert "height_default" in config
        assert "dpi" in config
        assert config["primary"] == "#3B82F6"

    def test_get_chart_config_institucional_returns_expected_primary(self):
        config = dependencies.get_chart_config(paleta="institucional")
        assert config["primary"] == "#1E40AF"

    def test_get_chart_config_unknown_paleta_defaults_to_moderna_2024(self):
        config = dependencies.get_chart_config(paleta="unknown_palette")
        assert config["primary"] == "#3B82F6"


class TestGetOperationsRepository:
    """Tests para get_operations_repository."""

    def test_get_operations_repository_returns_repository_with_injected_db(self):
        mock_db = MagicMock()
        repo = dependencies.get_operations_repository(db=mock_db)
        from app.repositories.operations_repository import OperationsRepository
        assert isinstance(repo, OperationsRepository)
        assert repo.db is mock_db


class TestGetInsightsOrchestrator:
    """Tests para get_insights_orchestrator."""

    def test_get_insights_orchestrator_returns_orchestrator_with_injected_client(
        self,
    ):
        mock_claude = MagicMock()
        orch = dependencies.get_insights_orchestrator(claude_client=mock_claude)
        from app.services.ai.insights_orchestrator import InsightsOrchestrator
        assert isinstance(orch, InsightsOrchestrator)
        assert orch.claude is mock_claude


class TestCreateMetricsAggregator:
    """Tests para create_metrics_aggregator."""

    def test_create_metrics_aggregator_returns_aggregator_with_args(self):
        from datetime import date
        ops = []
        f_inicio = date(2025, 1, 1)
        f_fin = date(2025, 1, 31)
        agg = dependencies.create_metrics_aggregator(
            operaciones=ops,
            fecha_inicio=f_inicio,
            fecha_fin=f_fin,
        )
        from app.services.metrics.metrics_aggregator import MetricsAggregator
        assert isinstance(agg, MetricsAggregator)
        assert agg.operaciones is ops
        assert agg.fecha_inicio == f_inicio
        assert agg.fecha_fin == f_fin

    def test_create_metrics_aggregator_accepts_optional_args(self):
        from datetime import date
        ops = []
        f_inicio = date(2025, 1, 1)
        f_fin = date(2025, 1, 31)
        agg = dependencies.create_metrics_aggregator(
            operaciones=ops,
            fecha_inicio=f_inicio,
            fecha_fin=f_fin,
            operaciones_comparacion=[],
            historico_mensual=[],
        )
        assert agg is not None


class TestCheckDependencies:
    """Tests para check_dependencies (health check)."""

    def test_check_dependencies_returns_dict_with_expected_keys(self):
        mock_db = MagicMock()
        mock_db.execute = MagicMock(return_value=None)
        mock_db.close = MagicMock()

        def fake_get_db():
            yield mock_db

        mock_path = MagicMock()
        mock_path.return_value.parent.parent.__truediv__.return_value.exists.return_value = True

        with patch("app.core.dependencies.get_db", side_effect=fake_get_db):
            with patch("os.getenv", return_value=None):
                with patch("pathlib.Path", mock_path):
                    status = dependencies.check_dependencies()
        assert "database" in status
        assert "anthropic_api_key" in status
        assert "templates_directory" in status

    def test_check_dependencies_database_false_on_exception(self):
        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("connection failed")
        mock_db.close = MagicMock()

        def fake_get_db():
            yield mock_db

        mock_path = MagicMock()
        mock_path.return_value.parent.parent.__truediv__.return_value.exists.return_value = True

        with patch("app.core.dependencies.get_db", side_effect=fake_get_db):
            with patch("os.getenv", return_value="something"):
                with patch("pathlib.Path", mock_path):
                    status = dependencies.check_dependencies()
        assert status["database"] is False
