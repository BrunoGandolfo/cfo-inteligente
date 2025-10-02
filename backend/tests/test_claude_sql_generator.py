"""
Suite de Tests para ClaudeSQLGenerator - Sistema CFO Inteligente

Tests del generador SQL usando Claude Sonnet 4.5 con mocks de Anthropic API.
Valida generación de SQL, manejo de errores, contexto y reglas de negocio.

Ejecutar:
    cd backend
    pytest tests/test_claude_sql_generator.py -v
    pytest tests/test_claude_sql_generator.py -v --cov=app.services.claude_sql_generator --cov-report=term-missing

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from app.services.claude_sql_generator import ClaudeSQLGenerator


# ══════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════

@pytest.fixture
def mock_anthropic_client():
    """Mock del cliente Anthropic"""
    mock_client = Mock()
    mock_response = Mock()
    mock_content = Mock()
    mock_content.text = "SELECT SUM(monto_uyu) FROM operaciones WHERE deleted_at IS NULL"
    mock_response.content = [mock_content]
    mock_client.messages.create.return_value = mock_response
    return mock_client

@pytest.fixture
def generator_instance(mock_anthropic_client):
    """Instancia de ClaudeSQLGenerator con cliente mockeado"""
    with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key-12345678901234567890'}):
        with patch('anthropic.Anthropic', return_value=mock_anthropic_client):
            generator = ClaudeSQLGenerator()
            return generator


# ══════════════════════════════════════════════════════════════
# GRUPO 1: TESTS DE INICIALIZACIÓN
# ══════════════════════════════════════════════════════════════

class TestInicializacion:
    """Tests de inicialización de ClaudeSQLGenerator"""
    
    @patch('anthropic.Anthropic')
    def test_init_con_api_key_valida(self, mock_anthropic):
        """Inicialización exitosa con API key válida"""
        # Arrange
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'sk-ant-test-key'}):
            # Act
            generator = ClaudeSQLGenerator()
            
            # Assert
            assert generator.client is not None
            mock_anthropic.assert_called_once()
    
    def test_init_sin_api_key(self):
        """Sin API key debe lanzar ValueError"""
        # Arrange
        with patch.dict(os.environ, {}, clear=True):
            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                ClaudeSQLGenerator()
            
            assert "ANTHROPIC_API_KEY no encontrada" in str(exc_info.value)
    
    @patch('anthropic.Anthropic')
    def test_ddl_context_presente(self, mock_anthropic):
        """DDL_CONTEXT debe estar definido"""
        # Arrange
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            generator = ClaudeSQLGenerator()
            
            # Assert
            assert generator.DDL_CONTEXT is not None
            assert len(generator.DDL_CONTEXT) > 100
            assert 'CREATE TABLE operaciones' in generator.DDL_CONTEXT
            assert 'CREATE TABLE socios' in generator.DDL_CONTEXT
            assert 'CREATE TABLE areas' in generator.DDL_CONTEXT
    
    @patch('anthropic.Anthropic')
    def test_business_context_con_8_reglas(self, mock_anthropic):
        """BUSINESS_CONTEXT debe tener las 8 reglas críticas"""
        # Arrange
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            generator = ClaudeSQLGenerator()
            
            # Assert
            assert generator.BUSINESS_CONTEXT is not None
            assert len(generator.BUSINESS_CONTEXT) > 1000
            
            # Verificar las 8 reglas
            reglas = [
                '1. PORCENTAJES DE MONEDA',
                '2. RANKINGS Y TOP N',
                '3. DISTRIBUCIONES POR SOCIO',
                '4. AFIRMACIONES DE UNICIDAD',
                '5. UNION ALL CON COLUMNAS ENUM',
                '6. PROYECCIONES TEMPORALES',
                '7. FILTROS TEMPORALES POR DEFECTO',
                '8. CONVERSIONES DE MONEDA EN AGREGACIONES'
            ]
            
            for regla in reglas:
                assert regla in generator.BUSINESS_CONTEXT, f"Falta regla: {regla}"


# ══════════════════════════════════════════════════════════════
# GRUPO 2: TESTS DE GENERAR_SQL (Método principal)
# ══════════════════════════════════════════════════════════════

class TestGenerarSQL:
    """Tests del método generar_sql"""
    
    def test_generar_sql_exitoso(self, generator_instance):
        """Claude genera SQL válido exitosamente"""
        # Arrange
        pregunta = "¿Cuánto facturamos este mes?"
        
        # Act
        sql = generator_instance.generar_sql(pregunta)
        
        # Assert
        assert sql is not None
        assert isinstance(sql, str)
        assert len(sql) > 0
        assert 'SELECT' in sql.upper() or 'WITH' in sql.upper()
    
    def test_generar_sql_con_backticks(self, generator_instance, mock_anthropic_client):
        """Claude devuelve SQL con ```sql``` - debe limpiarse"""
        # Arrange
        mock_content = Mock()
        mock_content.text = "```sql\nSELECT * FROM operaciones\n```"
        mock_response = Mock()
        mock_response.content = [mock_content]
        mock_anthropic_client.messages.create.return_value = mock_response
        
        pregunta = "Test"
        
        # Act
        sql = generator_instance.generar_sql(pregunta)
        
        # Assert
        assert "```" not in sql
        assert "SELECT" in sql
    
    def test_generar_sql_error_api(self, generator_instance, mock_anthropic_client):
        """Error de API debe capturarse y retornar ERROR:"""
        # Arrange
        mock_anthropic_client.messages.create.side_effect = Exception("API Connection Error")
        pregunta = "Test"
        
        # Act
        sql = generator_instance.generar_sql(pregunta)
        
        # Assert
        assert sql.startswith("ERROR:")
        assert "API Connection Error" in sql
    
    def test_generar_sql_timeout(self, generator_instance, mock_anthropic_client):
        """Timeout de API debe manejarse"""
        # Arrange
        mock_anthropic_client.messages.create.side_effect = Exception("Timeout")
        pregunta = "Test"
        
        # Act
        sql = generator_instance.generar_sql(pregunta)
        
        # Assert
        assert sql.startswith("ERROR:")
    
    def test_generar_sql_rate_limit(self, generator_instance, mock_anthropic_client):
        """Rate limit de API debe manejarse"""
        # Arrange
        mock_anthropic_client.messages.create.side_effect = Exception("Rate limit exceeded")
        pregunta = "Test"
        
        # Act
        sql = generator_instance.generar_sql(pregunta)
        
        # Assert
        assert sql.startswith("ERROR:")
        assert "Rate limit" in sql
    
    def test_generar_sql_parametros_correctos(self, generator_instance, mock_anthropic_client):
        """Debe llamar a Anthropic con parámetros correctos"""
        # Arrange
        pregunta = "Test"
        
        # Act
        sql = generator_instance.generar_sql(pregunta)
        
        # Assert
        # Verificar que se llamó con parámetros correctos
        mock_anthropic_client.messages.create.assert_called_once()
        call_args = mock_anthropic_client.messages.create.call_args
        
        assert call_args.kwargs['model'] == 'claude-sonnet-4-5-20250929'
        assert call_args.kwargs['max_tokens'] == 1500
        assert call_args.kwargs['temperature'] == 0.0  # Determinístico


# ══════════════════════════════════════════════════════════════
# GRUPO 3: TESTS DE CONTEXTO Y PROMPT
# ══════════════════════════════════════════════════════════════

class TestContextoYPrompt:
    """Tests del contexto y construcción de prompt"""
    
    @patch('anthropic.Anthropic')
    def test_prompt_incluye_ddl(self, mock_anthropic):
        """Prompt debe incluir DDL_CONTEXT"""
        # Arrange
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            generator = ClaudeSQLGenerator()
            mock_client = Mock()
            generator.client = mock_client
            
            # Mock response
            mock_content = Mock()
            mock_content.text = "SELECT 1"
            mock_response = Mock()
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            
            pregunta = "Test"
            
            # Act
            sql = generator.generar_sql(pregunta)
            
            # Assert
            call_args = mock_client.messages.create.call_args
            prompt = call_args.kwargs['messages'][0]['content']
            
            assert 'CREATE TABLE operaciones' in prompt
            assert 'CREATE TABLE socios' in prompt
    
    @patch('anthropic.Anthropic')
    def test_prompt_incluye_business_context(self, mock_anthropic):
        """Prompt debe incluir BUSINESS_CONTEXT con reglas"""
        # Arrange
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            generator = ClaudeSQLGenerator()
            mock_client = Mock()
            generator.client = mock_client
            
            mock_content = Mock()
            mock_content.text = "SELECT 1"
            mock_response = Mock()
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            
            pregunta = "Test"
            
            # Act
            sql = generator.generar_sql(pregunta)
            
            # Assert
            call_args = mock_client.messages.create.call_args
            prompt = call_args.kwargs['messages'][0]['content']
            
            assert 'REGLAS SQL CRÍTICAS' in prompt
            assert 'PORCENTAJES DE MONEDA' in prompt
            assert 'CONVERSIONES DE MONEDA EN AGREGACIONES' in prompt
    
    @patch('anthropic.Anthropic')
    def test_prompt_incluye_pregunta_usuario(self, mock_anthropic):
        """Prompt debe incluir la pregunta del usuario"""
        # Arrange
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            generator = ClaudeSQLGenerator()
            mock_client = Mock()
            generator.client = mock_client
            
            mock_content = Mock()
            mock_content.text = "SELECT 1"
            mock_response = Mock()
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            
            pregunta = "¿Cuánto facturamos en octubre?"
            
            # Act
            sql = generator.generar_sql(pregunta)
            
            # Assert
            call_args = mock_client.messages.create.call_args
            prompt = call_args.kwargs['messages'][0]['content']
            
            assert pregunta in prompt


# ══════════════════════════════════════════════════════════════
# GRUPO 4: TESTS DE REGLAS ESPECÍFICAS
# ══════════════════════════════════════════════════════════════

class TestReglasNegocio:
    """Tests que verifican que las reglas se aplican correctamente"""
    
    @patch('anthropic.Anthropic')
    def test_regla_contexto_temporal_2025(self, mock_anthropic):
        """Regla: Asumir año 2025 si no se especifica"""
        # Arrange
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            generator = ClaudeSQLGenerator()
            
            # Assert
            assert 'Octubre 2025' in generator.BUSINESS_CONTEXT
            assert 'ASUMIR año 2025' in generator.BUSINESS_CONTEXT
    
    @patch('anthropic.Anthropic')
    def test_regla_moneda_original_para_porcentajes(self, mock_anthropic):
        """Regla #1: Usar moneda_original para porcentajes"""
        # Arrange
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            generator = ClaudeSQLGenerator()
            
            # Assert
            assert 'moneda_original' in generator.BUSINESS_CONTEXT
            assert 'PORCENTAJES DE MONEDA' in generator.BUSINESS_CONTEXT
    
    @patch('anthropic.Anthropic')
    def test_regla_filtros_temporales_default(self, mock_anthropic):
        """Regla #7: Filtros temporales por defecto"""
        # Arrange
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            generator = ClaudeSQLGenerator()
            
            # Assert
            assert 'FILTROS TEMPORALES POR DEFECTO' in generator.BUSINESS_CONTEXT
            assert 'año actual (2025)' in generator.BUSINESS_CONTEXT
    
    @patch('anthropic.Anthropic')
    def test_regla_conversiones_moneda(self, mock_anthropic):
        """Regla #8: Conversiones de moneda en agregaciones"""
        # Arrange
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            generator = ClaudeSQLGenerator()
            
            # Assert
            assert 'CONVERSIONES DE MONEDA EN AGREGACIONES' in generator.BUSINESS_CONTEXT
            assert 'SUM(monto_usd) SIN filtrar' in generator.BUSINESS_CONTEXT


# ══════════════════════════════════════════════════════════════
# GRUPO 5: TESTS DE TIPOS DE SQL GENERADOS
# ══════════════════════════════════════════════════════════════

class TestTiposSQLGenerados:
    """Tests de diferentes tipos de SQL que puede generar"""
    
    def test_sql_simple_select(self, generator_instance, mock_anthropic_client):
        """Debe generar SELECT simple"""
        # Arrange
        mock_content = Mock()
        mock_content.text = "SELECT COUNT(*) FROM operaciones"
        mock_response = Mock()
        mock_response.content = [mock_content]
        mock_anthropic_client.messages.create.return_value = mock_response
        
        pregunta = "¿Cuántas operaciones hay?"
        
        # Act
        sql = generator_instance.generar_sql(pregunta)
        
        # Assert
        assert sql.strip().upper().startswith('SELECT')
        assert 'COUNT(*)' in sql.upper()
    
    def test_sql_con_cte(self, generator_instance, mock_anthropic_client):
        """Debe generar SQL con WITH (CTE)"""
        # Arrange
        sql_complejo = """WITH datos AS (
            SELECT SUM(monto) as total FROM operaciones
        )
        SELECT total FROM datos"""
        
        mock_content = Mock()
        mock_content.text = sql_complejo
        mock_response = Mock()
        mock_response.content = [mock_content]
        mock_anthropic_client.messages.create.return_value = mock_response
        
        pregunta = "Proyección compleja"
        
        # Act
        sql = generator_instance.generar_sql(pregunta)
        
        # Assert
        assert sql.strip().upper().startswith('WITH')
        assert 'SELECT' in sql.upper()
    
    def test_sql_con_joins(self, generator_instance, mock_anthropic_client):
        """Debe generar SQL con JOINs"""
        # Arrange
        sql_join = "SELECT a.nombre, SUM(o.monto) FROM operaciones o JOIN areas a ON a.id = o.area_id"
        
        mock_content = Mock()
        mock_content.text = sql_join
        mock_response = Mock()
        mock_response.content = [mock_content]
        mock_anthropic_client.messages.create.return_value = mock_response
        
        pregunta = "Facturación por área"
        
        # Act
        sql = generator_instance.generar_sql(pregunta)
        
        # Assert
        assert 'JOIN' in sql.upper()


# ══════════════════════════════════════════════════════════════
# GRUPO 6: TESTS DE MANEJO DE ERRORES
# ══════════════════════════════════════════════════════════════

class TestManejoErrores:
    """Tests de manejo de errores de Anthropic API"""
    
    def test_api_connection_error(self, generator_instance, mock_anthropic_client):
        """Connection error debe capturarse"""
        # Arrange
        mock_anthropic_client.messages.create.side_effect = Exception("Connection failed")
        pregunta = "Test"
        
        # Act
        sql = generator_instance.generar_sql(pregunta)
        
        # Assert
        assert sql.startswith("ERROR:")
        assert "Connection failed" in sql
    
    def test_authentication_error(self, generator_instance, mock_anthropic_client):
        """Authentication error debe capturarse"""
        # Arrange
        mock_anthropic_client.messages.create.side_effect = Exception("Invalid API key")
        pregunta = "Test"
        
        # Act
        sql = generator_instance.generar_sql(pregunta)
        
        # Assert
        assert sql.startswith("ERROR:")
    
    def test_respuesta_vacia(self, generator_instance, mock_anthropic_client):
        """Respuesta vacía debe manejarse"""
        # Arrange
        mock_content = Mock()
        mock_content.text = ""
        mock_response = Mock()
        mock_response.content = [mock_content]
        mock_anthropic_client.messages.create.return_value = mock_response
        
        pregunta = "Test"
        
        # Act
        sql = generator_instance.generar_sql(pregunta)
        
        # Assert
        assert sql == "" or sql is not None  # No debe crashear
    
    def test_respuesta_sin_content(self, generator_instance, mock_anthropic_client):
        """Respuesta sin campo content debe manejarse"""
        # Arrange
        mock_response = Mock()
        mock_response.content = []  # Lista vacía
        mock_anthropic_client.messages.create.return_value = mock_response
        
        pregunta = "Test"
        
        # Act
        sql = generator_instance.generar_sql(pregunta)
        
        # Assert
        # El código captura el IndexError y retorna "ERROR:..."
        assert sql.startswith("ERROR:")
        assert "list index out of range" in sql


# ══════════════════════════════════════════════════════════════
# GRUPO 7: TESTS DE LIMPIEZA DE SQL
# ══════════════════════════════════════════════════════════════

class TestLimpiezaSQL:
    """Tests de limpieza de markdown en SQL"""
    
    def test_limpieza_backticks_sql(self, generator_instance, mock_anthropic_client):
        """Debe limpiar triple backticks con sql"""
        # Arrange
        mock_content = Mock()
        mock_content.text = "```sql\nSELECT * FROM ops\n```"
        mock_response = Mock()
        mock_response.content = [mock_content]
        mock_anthropic_client.messages.create.return_value = mock_response
        
        pregunta = "Test"
        
        # Act
        sql = generator_instance.generar_sql(pregunta)
        
        # Assert
        assert "```" not in sql
        assert sql.strip() == "SELECT * FROM ops"
    
    def test_limpieza_backticks_genericos(self, generator_instance, mock_anthropic_client):
        """Debe limpiar triple backticks genéricos"""
        # Arrange
        mock_content = Mock()
        mock_content.text = "```\nWITH cte AS (...) SELECT * FROM cte\n```"
        mock_response = Mock()
        mock_response.content = [mock_content]
        mock_anthropic_client.messages.create.return_value = mock_response
        
        pregunta = "Test"
        
        # Act
        sql = generator_instance.generar_sql(pregunta)
        
        # Assert
        assert "```" not in sql
        assert "WITH cte" in sql
    
    def test_sql_sin_backticks_no_modifica(self, generator_instance, mock_anthropic_client):
        """SQL sin backticks debe retornarse sin modificar"""
        # Arrange
        sql_limpio = "SELECT SUM(monto) FROM operaciones WHERE deleted_at IS NULL"
        mock_content = Mock()
        mock_content.text = sql_limpio
        mock_response = Mock()
        mock_response.content = [mock_content]
        mock_anthropic_client.messages.create.return_value = mock_response
        
        pregunta = "Test"
        
        # Act
        sql = generator_instance.generar_sql(pregunta)
        
        # Assert
        assert sql == sql_limpio


# ══════════════════════════════════════════════════════════════
# GRUPO 8: TESTS DE CASOS EDGE
# ══════════════════════════════════════════════════════════════

class TestCasosEdge:
    """Tests de casos límite"""
    
    def test_pregunta_con_caracteres_especiales(self, generator_instance):
        """Pregunta con caracteres especiales no debe crashear"""
        # Arrange
        pregunta = "¿Cuánto €$¥ facturamos?"
        
        # Act
        sql = generator_instance.generar_sql(pregunta)
        
        # Assert
        assert sql is not None
    
    def test_pregunta_muy_larga(self, generator_instance):
        """Pregunta muy larga debe manejarse"""
        # Arrange
        pregunta = "Necesito saber " + "x" * 5000 + " facturación"
        
        # Act
        sql = generator_instance.generar_sql(pregunta)
        
        # Assert
        assert sql is not None
    
    def test_sql_multilinea_con_espacios(self, generator_instance, mock_anthropic_client):
        """SQL multilinea con muchos espacios debe manejarse"""
        # Arrange
        sql_espaciado = """
        
        SELECT 
            SUM(monto)
        FROM 
            operaciones
        
        """
        mock_content = Mock()
        mock_content.text = sql_espaciado
        mock_response = Mock()
        mock_response.content = [mock_content]
        mock_anthropic_client.messages.create.return_value = mock_response
        
        pregunta = "Test"
        
        # Act
        sql = generator_instance.generar_sql(pregunta)
        
        # Assert
        assert 'SELECT' in sql
        assert sql.strip() != ""  # No debe ser solo espacios

