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
        # get_db viene de app.core.database; parchear SessionLocal donde se usa
        with patch("app.core.database.SessionLocal", return_value=mock_session):
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
