"""
Suite de Tests para AIOrchestrator - Sistema CFO Inteligente

Tests del orquestador de IA con fallback multi-proveedor.
Valida inicialización, fallback Claude→OpenAI→Gemini, y manejo de errores.

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
        """Solo Claude disponible debe inicializarse correctamente"""
        # Arrange
        mock_settings.anthropic_api_key = "sk-ant-test-key"
        mock_settings.openai_api_key = None
        mock_settings.google_ai_key = None
        
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        
        # Act
        from app.services.ai.ai_orchestrator import AIOrchestrator
        orchestrator = AIOrchestrator()
        
        # Assert
        assert orchestrator._claude_client is not None
        assert orchestrator._openai_client is None
        assert orchestrator._gemini_model is None
        assert orchestrator.get_available_providers() == ["claude"]
    
    @patch('app.services.ai.ai_orchestrator.settings')
    @patch('openai.OpenAI')
    def test_init_con_openai_disponible(self, mock_openai, mock_settings):
        """Solo OpenAI disponible debe inicializarse correctamente"""
        # Arrange
        mock_settings.anthropic_api_key = None
        mock_settings.openai_api_key = "sk-openai-test-key"
        mock_settings.google_ai_key = None
        
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Act
        from app.services.ai.ai_orchestrator import AIOrchestrator
        orchestrator = AIOrchestrator()
        
        # Assert
        assert orchestrator._claude_client is None
        assert orchestrator._openai_client is not None
        assert orchestrator._gemini_model is None
        assert orchestrator.get_available_providers() == ["openai"]
    
    @patch('app.services.ai.ai_orchestrator.settings')
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_init_con_gemini_disponible(self, mock_genai_model, mock_genai_config, mock_settings):
        """Solo Gemini disponible debe inicializarse correctamente"""
        # Arrange
        mock_settings.anthropic_api_key = None
        mock_settings.openai_api_key = None
        mock_settings.google_ai_key = "google-ai-test-key"
        
        mock_model = Mock()
        mock_genai_model.return_value = mock_model
        
        # Act
        from app.services.ai.ai_orchestrator import AIOrchestrator
        orchestrator = AIOrchestrator()
        
        # Assert
        assert orchestrator._claude_client is None
        assert orchestrator._openai_client is None
        assert orchestrator._gemini_model is not None
        assert orchestrator.get_available_providers() == ["gemini"]
    
    @patch('app.services.ai.ai_orchestrator.settings')
    def test_init_sin_proveedores_disponibles(self, mock_settings):
        """Sin API keys debe inicializarse sin proveedores"""
        # Arrange
        mock_settings.anthropic_api_key = None
        mock_settings.openai_api_key = None
        mock_settings.google_ai_key = None
        
        # Act
        from app.services.ai.ai_orchestrator import AIOrchestrator
        orchestrator = AIOrchestrator()
        
        # Assert
        assert orchestrator._claude_client is None
        assert orchestrator._openai_client is None
        assert orchestrator._gemini_model is None
        assert orchestrator.get_available_providers() == []
        assert orchestrator.is_available() is False
    
    @patch('app.services.ai.ai_orchestrator.settings')
    @patch('anthropic.Anthropic')
    @patch('openai.OpenAI')
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_init_con_todos_proveedores(self, mock_genai_model, mock_genai_config, 
                                         mock_openai, mock_anthropic, mock_settings):
        """Con todas las API keys debe inicializar todos los proveedores"""
        # Arrange
        mock_settings.anthropic_api_key = "sk-ant-test"
        mock_settings.openai_api_key = "sk-openai-test"
        mock_settings.google_ai_key = "google-ai-test"
        
        # Act
        from app.services.ai.ai_orchestrator import AIOrchestrator
        orchestrator = AIOrchestrator()
        
        # Assert
        assert orchestrator._claude_client is not None
        assert orchestrator._openai_client is not None
        assert orchestrator._gemini_model is not None
        assert len(orchestrator.get_available_providers()) == 3
        assert orchestrator.is_available() is True


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
            mock_settings.openai_api_key = None
            mock_settings.google_ai_key = None
            
            from app.services.ai.ai_orchestrator import AIOrchestrator
            orchestrator = AIOrchestrator()
        
        # Act
        providers = orchestrator.get_available_providers()
        
        # Assert
        assert isinstance(providers, list)
    
    def test_is_available_true_con_al_menos_uno(self):
        """is_available debe retornar True si hay al menos un proveedor"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = "test-key"
            mock_settings.openai_api_key = None
            mock_settings.google_ai_key = None
            
            with patch('anthropic.Anthropic'):
                from app.services.ai.ai_orchestrator import AIOrchestrator
                orchestrator = AIOrchestrator()
        
        # Assert
        assert orchestrator.is_available() is True
    
    def test_is_available_false_sin_proveedores(self):
        """is_available debe retornar False sin proveedores"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = None
            mock_settings.openai_api_key = None
            mock_settings.google_ai_key = None
            
            from app.services.ai.ai_orchestrator import AIOrchestrator
            orchestrator = AIOrchestrator()
        
        # Assert
        assert orchestrator.is_available() is False


# ══════════════════════════════════════════════════════════════
# GRUPO 3: TESTS DE complete() - FLUJO NORMAL
# ══════════════════════════════════════════════════════════════

class TestAIOrchestatorComplete:
    """Tests del método complete() - flujo normal"""
    
    def test_complete_usa_claude_primero(self):
        """complete() debe intentar Claude primero"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = "test"
            mock_settings.openai_api_key = "test"
            mock_settings.google_ai_key = None
            
            with patch('anthropic.Anthropic') as mock_anthropic:
                with patch('openai.OpenAI'):
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
            mock_settings.openai_api_key = None
            mock_settings.google_ai_key = None
            
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
        """complete() debe pasar max_tokens al proveedor"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = "test"
            mock_settings.openai_api_key = None
            mock_settings.google_ai_key = None
            
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
        """complete() debe pasar temperature al proveedor"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = "test"
            mock_settings.openai_api_key = None
            mock_settings.google_ai_key = None
            
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
# GRUPO 4: TESTS DE FALLBACK
# ══════════════════════════════════════════════════════════════

class TestAIOrchestatorFallback:
    """Tests del mecanismo de fallback"""
    
    def test_complete_fallback_a_openai_si_claude_falla(self):
        """Si Claude falla, debe intentar OpenAI"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = "test"
            mock_settings.openai_api_key = "test"
            mock_settings.google_ai_key = None
            
            with patch('anthropic.Anthropic') as mock_anthropic:
                with patch('openai.OpenAI') as mock_openai:
                    # Claude falla
                    mock_claude_client = Mock()
                    mock_claude_client.messages.create.side_effect = Exception("Claude error")
                    mock_anthropic.return_value = mock_claude_client
                    
                    # OpenAI responde
                    mock_openai_client = Mock()
                    mock_openai_response = Mock()
                    mock_openai_choice = Mock()
                    mock_openai_message = Mock()
                    mock_openai_message.content = "Respuesta de OpenAI"
                    mock_openai_choice.message = mock_openai_message
                    mock_openai_response.choices = [mock_openai_choice]
                    mock_openai_client.chat.completions.create.return_value = mock_openai_response
                    mock_openai.return_value = mock_openai_client
                    
                    from app.services.ai.ai_orchestrator import AIOrchestrator
                    orchestrator = AIOrchestrator()
        
        # Act
        result = orchestrator.complete("Test prompt")
        
        # Assert
        assert result == "Respuesta de OpenAI"
        mock_claude_client.messages.create.assert_called_once()
        mock_openai_client.chat.completions.create.assert_called_once()
    
    def test_complete_fallback_a_gemini_si_openai_falla(self):
        """Si Claude y OpenAI fallan, debe intentar Gemini"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = "test"
            mock_settings.openai_api_key = "test"
            mock_settings.google_ai_key = "test"
            
            with patch('anthropic.Anthropic') as mock_anthropic:
                with patch('openai.OpenAI') as mock_openai:
                    with patch('google.generativeai.configure'):
                        with patch('google.generativeai.GenerativeModel') as mock_genai:
                            # Claude falla
                            mock_claude_client = Mock()
                            mock_claude_client.messages.create.side_effect = Exception("Claude error")
                            mock_anthropic.return_value = mock_claude_client
                            
                            # OpenAI falla
                            mock_openai_client = Mock()
                            mock_openai_client.chat.completions.create.side_effect = Exception("OpenAI error")
                            mock_openai.return_value = mock_openai_client
                            
                            # Gemini responde
                            mock_gemini_model = Mock()
                            mock_gemini_response = Mock()
                            mock_gemini_response.text = "Respuesta de Gemini"
                            mock_gemini_model.generate_content.return_value = mock_gemini_response
                            mock_genai.return_value = mock_gemini_model
                            
                            from app.services.ai.ai_orchestrator import AIOrchestrator
                            orchestrator = AIOrchestrator()
        
        # Act
        result = orchestrator.complete("Test prompt")
        
        # Assert
        assert result == "Respuesta de Gemini"
        mock_gemini_model.generate_content.assert_called_once()
    
    def test_complete_retorna_none_si_todos_fallan(self):
        """Si todos los proveedores fallan, debe retornar None"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = "test"
            mock_settings.openai_api_key = "test"
            mock_settings.google_ai_key = "test"
            
            with patch('anthropic.Anthropic') as mock_anthropic:
                with patch('openai.OpenAI') as mock_openai:
                    with patch('google.generativeai.configure'):
                        with patch('google.generativeai.GenerativeModel') as mock_genai:
                            # Todos fallan
                            mock_claude_client = Mock()
                            mock_claude_client.messages.create.side_effect = Exception("Claude error")
                            mock_anthropic.return_value = mock_claude_client
                            
                            mock_openai_client = Mock()
                            mock_openai_client.chat.completions.create.side_effect = Exception("OpenAI error")
                            mock_openai.return_value = mock_openai_client
                            
                            mock_gemini_model = Mock()
                            mock_gemini_model.generate_content.side_effect = Exception("Gemini error")
                            mock_genai.return_value = mock_gemini_model
                            
                            from app.services.ai.ai_orchestrator import AIOrchestrator
                            orchestrator = AIOrchestrator()
        
        # Act
        result = orchestrator.complete("Test prompt")
        
        # Assert
        assert result is None
    
    def test_complete_sin_proveedores_retorna_none(self):
        """Sin proveedores disponibles debe retornar None"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = None
            mock_settings.openai_api_key = None
            mock_settings.google_ai_key = None
            
            from app.services.ai.ai_orchestrator import AIOrchestrator
            orchestrator = AIOrchestrator()
        
        # Act
        result = orchestrator.complete("Test prompt")
        
        # Assert
        assert result is None


# ══════════════════════════════════════════════════════════════
# GRUPO 5: TESTS DE ERRORES ESPECÍFICOS
# ══════════════════════════════════════════════════════════════

class TestAIOrchestatorErrors:
    """Tests de manejo de errores específicos"""
    
    def test_claude_timeout_dispara_fallback(self):
        """Timeout de Claude debe disparar fallback"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = "test"
            mock_settings.openai_api_key = "test"
            mock_settings.google_ai_key = None
            
            with patch('anthropic.Anthropic') as mock_anthropic:
                with patch('openai.OpenAI') as mock_openai:
                    # Claude timeout
                    mock_claude_client = Mock()
                    mock_claude_client.messages.create.side_effect = TimeoutError("Request timed out")
                    mock_anthropic.return_value = mock_claude_client
                    
                    # OpenAI responde
                    mock_openai_client = Mock()
                    mock_openai_response = Mock()
                    mock_openai_choice = Mock()
                    mock_openai_message = Mock()
                    mock_openai_message.content = "Respuesta OpenAI"
                    mock_openai_choice.message = mock_openai_message
                    mock_openai_response.choices = [mock_openai_choice]
                    mock_openai_client.chat.completions.create.return_value = mock_openai_response
                    mock_openai.return_value = mock_openai_client
                    
                    from app.services.ai.ai_orchestrator import AIOrchestrator
                    orchestrator = AIOrchestrator()
        
        # Act
        result = orchestrator.complete("Test")
        
        # Assert
        assert result == "Respuesta OpenAI"
    
    def test_claude_rate_limit_dispara_fallback(self):
        """Rate limit de Claude debe disparar fallback"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = "test"
            mock_settings.openai_api_key = "test"
            mock_settings.google_ai_key = None
            
            with patch('anthropic.Anthropic') as mock_anthropic:
                with patch('openai.OpenAI') as mock_openai:
                    # Claude rate limit
                    mock_claude_client = Mock()
                    mock_claude_client.messages.create.side_effect = Exception("Rate limit exceeded")
                    mock_anthropic.return_value = mock_claude_client
                    
                    # OpenAI responde
                    mock_openai_client = Mock()
                    mock_openai_response = Mock()
                    mock_openai_choice = Mock()
                    mock_openai_message = Mock()
                    mock_openai_message.content = "Fallback response"
                    mock_openai_choice.message = mock_openai_message
                    mock_openai_response.choices = [mock_openai_choice]
                    mock_openai_client.chat.completions.create.return_value = mock_openai_response
                    mock_openai.return_value = mock_openai_client
                    
                    from app.services.ai.ai_orchestrator import AIOrchestrator
                    orchestrator = AIOrchestrator()
        
        # Act
        result = orchestrator.complete("Test")
        
        # Assert
        assert result == "Fallback response"
    
    def test_respuesta_vacia_de_claude_intenta_siguiente(self):
        """Respuesta vacía de Claude debe intentar siguiente proveedor"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = "test"
            mock_settings.openai_api_key = "test"
            mock_settings.google_ai_key = None
            
            with patch('anthropic.Anthropic') as mock_anthropic:
                with patch('openai.OpenAI') as mock_openai:
                    # Claude responde vacío (simular con excepción)
                    mock_claude_client = Mock()
                    mock_response = Mock()
                    mock_response.content = []  # Lista vacía causa IndexError
                    mock_claude_client.messages.create.return_value = mock_response
                    mock_anthropic.return_value = mock_claude_client
                    
                    # OpenAI responde
                    mock_openai_client = Mock()
                    mock_openai_response = Mock()
                    mock_openai_choice = Mock()
                    mock_openai_message = Mock()
                    mock_openai_message.content = "OpenAI response"
                    mock_openai_choice.message = mock_openai_message
                    mock_openai_response.choices = [mock_openai_choice]
                    mock_openai_client.chat.completions.create.return_value = mock_openai_response
                    mock_openai.return_value = mock_openai_client
                    
                    from app.services.ai.ai_orchestrator import AIOrchestrator
                    orchestrator = AIOrchestrator()
        
        # Act
        result = orchestrator.complete("Test")
        
        # Assert
        # Si Claude responde vacío (IndexError), debe usar fallback
        assert result == "OpenAI response"
    
    def test_api_key_invalida_no_crashea(self):
        """API key inválida no debe crashear el sistema"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = "invalid-key"
            mock_settings.openai_api_key = None
            mock_settings.google_ai_key = None
            
            with patch('anthropic.Anthropic') as mock_anthropic:
                # Simular error de autenticación
                mock_anthropic.side_effect = Exception("Invalid API key")
                
                from app.services.ai.ai_orchestrator import AIOrchestrator
                orchestrator = AIOrchestrator()
        
        # Assert - No debe crashear
        assert orchestrator._claude_client is None
        assert orchestrator.is_available() is False


# ══════════════════════════════════════════════════════════════
# GRUPO 6: TESTS DE OPENAI ESPECÍFICOS
# ══════════════════════════════════════════════════════════════

class TestAIOrchestatorOpenAI:
    """Tests específicos de OpenAI"""
    
    def test_openai_recibe_system_prompt_correcto(self):
        """OpenAI debe recibir system prompt en formato correcto"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = None
            mock_settings.openai_api_key = "test"
            mock_settings.google_ai_key = None
            
            with patch('openai.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_response = Mock()
                mock_choice = Mock()
                mock_message = Mock()
                mock_message.content = "Respuesta"
                mock_choice.message = mock_message
                mock_response.choices = [mock_choice]
                mock_client.chat.completions.create.return_value = mock_response
                mock_openai.return_value = mock_client
                
                from app.services.ai.ai_orchestrator import AIOrchestrator
                orchestrator = AIOrchestrator()
        
        # Act
        orchestrator.complete(prompt="Pregunta", system_prompt="Eres experto")
        
        # Assert
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        messages = call_kwargs['messages']
        
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[0]['content'] == 'Eres experto'
        assert messages[1]['role'] == 'user'
        assert messages[1]['content'] == 'Pregunta'


# ══════════════════════════════════════════════════════════════
# GRUPO 7: TESTS DE GEMINI ESPECÍFICOS
# ══════════════════════════════════════════════════════════════

class TestAIOrchestatorGemini:
    """Tests específicos de Gemini"""
    
    def test_gemini_combina_system_y_user_prompt(self):
        """Gemini debe combinar system y user prompt"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = None
            mock_settings.openai_api_key = None
            mock_settings.google_ai_key = "test"
            
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel') as mock_genai:
                    mock_model = Mock()
                    mock_response = Mock()
                    mock_response.text = "Respuesta"
                    mock_model.generate_content.return_value = mock_response
                    mock_genai.return_value = mock_model
                    
                    from app.services.ai.ai_orchestrator import AIOrchestrator
                    orchestrator = AIOrchestrator()
        
        # Act
        orchestrator.complete(prompt="Pregunta", system_prompt="Contexto")
        
        # Assert
        call_args = mock_model.generate_content.call_args
        full_prompt = call_args[0][0]
        
        assert "Contexto" in full_prompt
        assert "Pregunta" in full_prompt
    
    def test_gemini_sin_system_prompt(self):
        """Gemini sin system prompt debe usar solo user prompt"""
        # Arrange
        with patch('app.services.ai.ai_orchestrator.settings') as mock_settings:
            mock_settings.anthropic_api_key = None
            mock_settings.openai_api_key = None
            mock_settings.google_ai_key = "test"
            
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel') as mock_genai:
                    mock_model = Mock()
                    mock_response = Mock()
                    mock_response.text = "Respuesta"
                    mock_model.generate_content.return_value = mock_response
                    mock_genai.return_value = mock_model
                    
                    from app.services.ai.ai_orchestrator import AIOrchestrator
                    orchestrator = AIOrchestrator()
        
        # Act
        orchestrator.complete(prompt="Solo pregunta")
        
        # Assert
        call_args = mock_model.generate_content.call_args
        prompt_enviado = call_args[0][0]
        
        assert prompt_enviado == "Solo pregunta"


# ══════════════════════════════════════════════════════════════
# GRUPO 8: TESTS DE MODELOS
# ══════════════════════════════════════════════════════════════

class TestAIOrchestatorModels:
    """Tests de configuración de modelos"""
    
    def test_claude_usa_modelo_correcto(self):
        """Claude debe usar el modelo configurado"""
        from app.services.ai.ai_orchestrator import AIOrchestrator
        
        assert AIOrchestrator.CLAUDE_MODEL == "claude-sonnet-4-5-20250929"
    
    def test_openai_usa_modelo_correcto(self):
        """OpenAI debe usar el modelo configurado"""
        from app.services.ai.ai_orchestrator import AIOrchestrator
        
        assert AIOrchestrator.OPENAI_MODEL == "gpt-3.5-turbo"
    
    def test_gemini_usa_modelo_correcto(self):
        """Gemini debe usar el modelo configurado"""
        from app.services.ai.ai_orchestrator import AIOrchestrator
        
        assert AIOrchestrator.GEMINI_MODEL == "gemini-1.5-flash"
    
    def test_default_timeout_es_30_segundos(self):
        """Timeout por defecto debe ser 30 segundos"""
        from app.services.ai.ai_orchestrator import AIOrchestrator
        
        assert AIOrchestrator.DEFAULT_TIMEOUT == 30



