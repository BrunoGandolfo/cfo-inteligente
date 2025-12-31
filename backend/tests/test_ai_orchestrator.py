"""
Suite de Tests para AIOrchestrator - Sistema CFO Inteligente

Tests del orquestador de IA simplificado (Solo Claude con reintentos).

Ejecutar:
    cd backend
    pytest tests/test_ai_orchestrator.py -v
    pytest tests/test_ai_orchestrator.py -v --cov=app.services.ai.ai_orchestrator

Autor: Sistema CFO Inteligente
Fecha: Diciembre 2025
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


# ══════════════════════════════════════════════════════════════
# GRUPO 1: TESTS DE INICIALIZACIÓN
# ══════════════════════════════════════════════════════════════

class TestAIOrchestatorInit:
    """Tests de inicialización del AIOrchestrator"""
    
    @patch('app.services.ai.ai_orchestrator.settings')
    @patch('anthropic.Anthropic')
    def test_init_con_claude_disponible(self, mock_anthropic, mock_settings):
        """Claude disponible debe inicializarse correctamente"""
        # Arrange
        mock_settings.anthropic_api_key = "sk-ant-test-key"
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        
        # Act
        from app.services.ai.ai_orchestrator import AIOrchestrator
        orchestrator = AIOrchestrator()
        
        # Assert
        assert orchestrator._client is not None
        assert orchestrator._is_available is True
        assert orchestrator.get_available_providers() == ["claude"]
    
    @patch('app.services.ai.ai_orchestrator.settings')
    def test_init_sin_api_key(self, mock_settings):
        """Sin API key debe inicializarse sin proveedores"""
        # Arrange
        mock_settings.anthropic_api_key = None
        
        # Act
        from app.services.ai.ai_orchestrator import AIOrchestrator
        orchestrator = AIOrchestrator()
        
        # Assert
        assert orchestrator._client is None
        assert orchestrator._is_available is False
        assert orchestrator.get_available_providers() == []
        assert orchestrator.is_available() is False
    
    @patch('app.services.ai.ai_orchestrator.settings')
    @patch('anthropic.Anthropic')
    def test_init_error_anthropic(self, mock_anthropic, mock_settings):
        """Error en Anthropic no debe crashear"""
        # Arrange
        mock_settings.anthropic_api_key = "test-key"
        mock_anthropic.side_effect = Exception("Connection error")
        
        # Act
        from app.services.ai.ai_orchestrator import AIOrchestrator
        orchestrator = AIOrchestrator()
        
        # Assert
        assert orchestrator._client is None
        assert orchestrator._is_available is False


# ══════════════════════════════════════════════════════════════
# GRUPO 2: TESTS DE get_available_providers() y is_available()
# ══════════════════════════════════════════════════════════════

class TestAIOrchestatorHelpers:
    """Tests de métodos auxiliares"""
    
    def test_get_available_providers_retorna_lista(self):
        """get_available_providers debe retornar lista"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = None
            
            from app.services.ai.ai_orchestrator import AIOrchestrator
            orchestrator = AIOrchestrator()
        
        # Act
        providers = orchestrator.get_available_providers()
        
        # Assert
        assert isinstance(providers, list)
    
    def test_is_available_true_con_claude(self):
        """is_available debe retornar True si Claude está disponible"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = "test-key"
            
            with patch('anthropic.Anthropic'):
                from app.services.ai.ai_orchestrator import AIOrchestrator
                orchestrator = AIOrchestrator()
        
        # Assert
        assert orchestrator.is_available() is True
    
    def test_is_available_false_sin_proveedores(self):
        """is_available debe retornar False sin Claude"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = None
            
            from app.services.ai.ai_orchestrator import AIOrchestrator
            orchestrator = AIOrchestrator()
        
        # Assert
        assert orchestrator.is_available() is False


# ══════════════════════════════════════════════════════════════
# GRUPO 3: TESTS DE complete() - FLUJO NORMAL
# ══════════════════════════════════════════════════════════════

class TestAIOrchestatorComplete:
    """Tests del método complete() - flujo normal"""
    
    def test_complete_usa_claude(self):
        """complete() debe usar Claude"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = "test"
            
            with patch('anthropic.Anthropic') as mock_anthropic:
                # Configurar respuesta de Claude
                mock_client = Mock()
                mock_response = Mock()
                mock_content = Mock()
                mock_content.text = "Respuesta de Claude"
                mock_response.content = [mock_content]
                mock_client.messages.create.return_value = mock_response
                mock_anthropic.return_value = mock_client
                
                from app.services.ai.ai_orchestrator import AIOrchestrator
                orchestrator = AIOrchestrator()
        
        # Act
        result = orchestrator.complete("Test prompt")
        
        # Assert
        assert result == "Respuesta de Claude"
        mock_client.messages.create.assert_called_once()
    
    def test_complete_con_system_prompt(self):
        """complete() debe pasar system_prompt a Claude"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = "test"
            
            with patch('anthropic.Anthropic') as mock_anthropic:
                mock_client = Mock()
                mock_response = Mock()
                mock_content = Mock()
                mock_content.text = "Respuesta"
                mock_response.content = [mock_content]
                mock_client.messages.create.return_value = mock_response
                mock_anthropic.return_value = mock_client
                
                from app.services.ai.ai_orchestrator import AIOrchestrator
                orchestrator = AIOrchestrator()
        
        # Act
        result = orchestrator.complete(
            prompt="Pregunta",
            system_prompt="Eres un asistente"
        )
        
        # Assert
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs['system'] == "Eres un asistente"
    
    def test_complete_respeta_max_tokens(self):
        """complete() debe pasar max_tokens a Claude"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = "test"
            
            with patch('anthropic.Anthropic') as mock_anthropic:
                mock_client = Mock()
                mock_response = Mock()
                mock_content = Mock()
                mock_content.text = "Respuesta"
                mock_response.content = [mock_content]
                mock_client.messages.create.return_value = mock_response
                mock_anthropic.return_value = mock_client
                
                from app.services.ai.ai_orchestrator import AIOrchestrator
                orchestrator = AIOrchestrator()
        
        # Act
        orchestrator.complete(prompt="Test", max_tokens=500)
        
        # Assert
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs['max_tokens'] == 500
    
    def test_complete_respeta_temperature(self):
        """complete() debe pasar temperature a Claude"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = "test"
            
            with patch('anthropic.Anthropic') as mock_anthropic:
                mock_client = Mock()
                mock_response = Mock()
                mock_content = Mock()
                mock_content.text = "Respuesta"
                mock_response.content = [mock_content]
                mock_client.messages.create.return_value = mock_response
                mock_anthropic.return_value = mock_client
                
                from app.services.ai.ai_orchestrator import AIOrchestrator
                orchestrator = AIOrchestrator()
        
        # Act
        orchestrator.complete(prompt="Test", temperature=0.7)
        
        # Assert
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs['temperature'] == 0.7


# ══════════════════════════════════════════════════════════════
# GRUPO 4: TESTS DE REINTENTOS
# ══════════════════════════════════════════════════════════════

class TestAIOrchestatorRetries:
    """Tests del mecanismo de reintentos"""
    
    @patch('app.services.ai.ai_orchestrator.time.sleep')
    def test_reintenta_en_error(self, mock_sleep):
        """Claude debe reintentar si falla"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = "test"
            
            with patch('anthropic.Anthropic') as mock_anthropic:
                mock_client = Mock()
                
                # Primera llamada falla, segunda exitosa
                mock_response = Mock()
                mock_content = Mock()
                mock_content.text = "Éxito en intento 2"
                mock_response.content = [mock_content]
                
                mock_client.messages.create.side_effect = [
                    Exception("Error temporal"),
                    mock_response
                ]
                mock_anthropic.return_value = mock_client
                
                from app.services.ai.ai_orchestrator import AIOrchestrator
                orchestrator = AIOrchestrator()
        
        # Act
        result = orchestrator.complete("Test")
        
        # Assert
        assert result == "Éxito en intento 2"
        assert mock_client.messages.create.call_count == 2
        mock_sleep.assert_called_once()  # Delay entre reintentos
    
    @patch('app.services.ai.ai_orchestrator.time.sleep')
    def test_retorna_none_despues_de_max_reintentos(self, mock_sleep):
        """Debe retornar None si todos los reintentos fallan"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = "test"
            
            with patch('anthropic.Anthropic') as mock_anthropic:
                mock_client = Mock()
                mock_client.messages.create.side_effect = Exception("Error permanente")
                mock_anthropic.return_value = mock_client
                
                from app.services.ai.ai_orchestrator import AIOrchestrator
                orchestrator = AIOrchestrator()
        
        # Act
        result = orchestrator.complete("Test")
        
        # Assert
        assert result is None
        assert mock_client.messages.create.call_count == 3  # MAX_RETRIES = 3
    
    def test_sin_claude_retorna_none_inmediatamente(self):
        """Sin Claude disponible debe retornar None sin reintentos"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = None
            
            from app.services.ai.ai_orchestrator import AIOrchestrator
            orchestrator = AIOrchestrator()
        
        # Act
        result = orchestrator.complete("Test")
        
        # Assert
        assert result is None


# ══════════════════════════════════════════════════════════════
# GRUPO 5: TESTS DE ERRORES ESPECÍFICOS
# ══════════════════════════════════════════════════════════════

class TestAIOrchestatorErrors:
    """Tests de manejo de errores específicos"""
    
    @patch('app.services.ai.ai_orchestrator.time.sleep')
    def test_timeout_dispara_reintento(self, mock_sleep):
        """Timeout debe disparar reintento"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = "test"
            
            with patch('anthropic.Anthropic') as mock_anthropic:
                mock_client = Mock()
                
                mock_response = Mock()
                mock_content = Mock()
                mock_content.text = "OK"
                mock_response.content = [mock_content]
                
                mock_client.messages.create.side_effect = [
                    TimeoutError("Timeout"),
                    mock_response
                ]
                mock_anthropic.return_value = mock_client
                
                from app.services.ai.ai_orchestrator import AIOrchestrator
                orchestrator = AIOrchestrator()
        
        # Act
        result = orchestrator.complete("Test")
        
        # Assert
        assert result == "OK"
    
    def test_api_key_invalida_no_crashea(self):
        """API key inválida no debe crashear el sistema"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = "invalid-key"
            
            with patch('anthropic.Anthropic') as mock_anthropic:
                mock_anthropic.side_effect = Exception("Invalid API key")
                
                from app.services.ai.ai_orchestrator import AIOrchestrator
                orchestrator = AIOrchestrator()
        
        # Assert - No debe crashear
        assert orchestrator._client is None
        assert orchestrator.is_available() is False


# ══════════════════════════════════════════════════════════════
# GRUPO 6: TESTS DE CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════

class TestAIOrchestatorConfig:
    """Tests de configuración del orchestrator"""
    
    def test_claude_modelo_correcto(self):
        """Claude debe usar el modelo configurado"""
        from app.services.ai.ai_orchestrator import AIOrchestrator
        
        assert AIOrchestrator.CLAUDE_MODEL == "claude-sonnet-4-20250514"
    
    def test_max_retries_es_3(self):
        """Max retries debe ser 3"""
        from app.services.ai.ai_orchestrator import AIOrchestrator
        
        assert AIOrchestrator.MAX_RETRIES == 3
    
    def test_retry_delay_es_2(self):
        """Retry delay debe ser 2 segundos"""
        from app.services.ai.ai_orchestrator import AIOrchestrator
        
        assert AIOrchestrator.RETRY_DELAY == 2
    
    def test_default_timeout_es_45(self):
        """Timeout por defecto debe ser 45 segundos"""
        from app.services.ai.ai_orchestrator import AIOrchestrator
        
        assert AIOrchestrator.DEFAULT_TIMEOUT == 45


# ══════════════════════════════════════════════════════════════
# GRUPO 7: TESTS DE get_last_error()
# ══════════════════════════════════════════════════════════════

class TestAIOrchestatorGetLastError:
    """Tests del método get_last_error()"""
    
    def test_get_last_error_sin_api_key(self):
        """Sin API key debe retornar error apropiado"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = None
            
            from app.services.ai.ai_orchestrator import AIOrchestrator
            orchestrator = AIOrchestrator()
        
        # Assert
        error = orchestrator.get_last_error()
        # Puede retornar "API_KEY no configurada" o "no pudo inicializarse"
        assert error is not None
        assert "API_KEY" in error or "inicializar" in error
    
    def test_get_last_error_disponible(self):
        """Con Claude disponible debe retornar None"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = "test"
            
            with patch('anthropic.Anthropic'):
                from app.services.ai.ai_orchestrator import AIOrchestrator
                orchestrator = AIOrchestrator()
        
        # Assert
        assert orchestrator.get_last_error() is None
