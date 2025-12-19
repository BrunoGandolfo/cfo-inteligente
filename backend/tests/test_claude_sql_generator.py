"""
Suite de Tests para ClaudeSQLGenerator - Sistema CFO Inteligente

Tests del generador SQL usando AIOrchestrator (fallback multi-proveedor).
Valida generación de SQL, manejo de errores, contexto y reglas de negocio.

Ejecutar:
    cd backend
    pytest tests/test_claude_sql_generator.py -v
    pytest tests/test_claude_sql_generator.py -v --cov=app.services.claude_sql_generator --cov-report=term-missing

Autor: Sistema CFO Inteligente
Fecha: Diciembre 2024
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from app.services.claude_sql_generator import ClaudeSQLGenerator


# ══════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════

@pytest.fixture
def mock_orchestrator():
    """Mock del AIOrchestrator"""
    with patch('app.services.claude_sql_generator.AIOrchestrator') as MockOrch:
        mock_instance = Mock()
        mock_instance.complete.return_value = "SELECT SUM(monto_uyu) FROM operaciones WHERE deleted_at IS NULL"
        MockOrch.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def generator_with_mock(mock_orchestrator):
    """Instancia de ClaudeSQLGenerator con orchestrator mockeado"""
    generator = ClaudeSQLGenerator()
    return generator


# ══════════════════════════════════════════════════════════════
# GRUPO 1: TESTS DE INICIALIZACIÓN
# ══════════════════════════════════════════════════════════════

class TestInicializacion:
    """Tests de inicialización de ClaudeSQLGenerator"""
    
    def test_init_crea_orchestrator(self, mock_orchestrator):
        """Inicialización crea AIOrchestrator"""
        generator = ClaudeSQLGenerator()
        assert generator._orchestrator is not None
    
    def test_ddl_context_presente(self, mock_orchestrator):
        """DDL_CONTEXT debe estar definido"""
        generator = ClaudeSQLGenerator()
        
        assert generator.DDL_CONTEXT is not None
        assert len(generator.DDL_CONTEXT) > 100
        assert 'CREATE TABLE operaciones' in generator.DDL_CONTEXT
        assert 'CREATE TABLE socios' in generator.DDL_CONTEXT
        assert 'CREATE TABLE areas' in generator.DDL_CONTEXT
    
    def test_business_context_presente(self, mock_orchestrator):
        """BUSINESS_CONTEXT debe estar definido"""
        generator = ClaudeSQLGenerator()
        
        assert generator.BUSINESS_CONTEXT is not None
        assert len(generator.BUSINESS_CONTEXT) > 500
    
    def test_business_context_tiene_reglas_criticas(self, mock_orchestrator):
        """BUSINESS_CONTEXT debe tener reglas críticas"""
        generator = ClaudeSQLGenerator()
        
        # Verificar reglas importantes
        reglas_esperadas = [
            'PORCENTAJES DE MONEDA',
            'RANKINGS',
            'DISTRIBUCIONES',
            'deleted_at IS NULL',
        ]
        
        for regla in reglas_esperadas:
            assert regla in generator.BUSINESS_CONTEXT, f"Falta regla: {regla}"


# ══════════════════════════════════════════════════════════════
# GRUPO 2: TESTS DE GENERAR_SQL (Método principal)
# ══════════════════════════════════════════════════════════════

class TestGenerarSQL:
    """Tests del método generar_sql"""
    
    def test_generar_sql_exitoso(self, mock_orchestrator):
        """Genera SQL válido exitosamente"""
        generator = ClaudeSQLGenerator()
        pregunta = "¿Cuánto facturamos este mes?"
        
        sql = generator.generar_sql(pregunta)
        
        assert sql is not None
        assert isinstance(sql, str)
        assert len(sql) > 0
        assert 'SELECT' in sql.upper()
    
    def test_generar_sql_llama_orchestrator(self, mock_orchestrator):
        """Debe llamar al orchestrator con prompt"""
        generator = ClaudeSQLGenerator()
        pregunta = "Test query"
        
        sql = generator.generar_sql(pregunta)
        
        mock_orchestrator.complete.assert_called_once()
        call_kwargs = mock_orchestrator.complete.call_args.kwargs
        assert 'prompt' in call_kwargs
        assert pregunta in call_kwargs['prompt']
    
    def test_generar_sql_incluye_ddl_en_prompt(self, mock_orchestrator):
        """Prompt debe incluir DDL_CONTEXT"""
        generator = ClaudeSQLGenerator()
        pregunta = "Test"
        
        generator.generar_sql(pregunta)
        
        call_kwargs = mock_orchestrator.complete.call_args.kwargs
        prompt = call_kwargs['prompt']
        assert 'CREATE TABLE operaciones' in prompt
    
    def test_generar_sql_incluye_business_context(self, mock_orchestrator):
        """Prompt debe incluir BUSINESS_CONTEXT"""
        generator = ClaudeSQLGenerator()
        pregunta = "Test"
        
        generator.generar_sql(pregunta)
        
        call_kwargs = mock_orchestrator.complete.call_args.kwargs
        prompt = call_kwargs['prompt']
        assert 'deleted_at IS NULL' in prompt
    
    def test_generar_sql_con_contexto(self, mock_orchestrator):
        """Genera SQL con contexto de conversación"""
        generator = ClaudeSQLGenerator()
        pregunta = "¿Y del mes anterior?"
        contexto = [
            {"role": "user", "content": "¿Cuánto facturamos?"},
            {"role": "assistant", "content": "SELECT SUM(monto_uyu)..."}
        ]
        
        sql = generator.generar_sql(pregunta, contexto=contexto)
        
        call_kwargs = mock_orchestrator.complete.call_args.kwargs
        prompt = call_kwargs['prompt']
        # Debe incluir contexto previo
        assert '¿Cuánto facturamos?' in prompt or 'contexto' in prompt.lower()
    
    def test_generar_sql_error_orchestrator_none(self, mock_orchestrator):
        """Si orchestrator retorna None, maneja el error"""
        mock_orchestrator.complete.return_value = None
        generator = ClaudeSQLGenerator()
        pregunta = "Test"
        
        sql = generator.generar_sql(pregunta)
        
        # Debe retornar algo (error o SQL vacío)
        assert sql is not None
    
    def test_generar_sql_error_exception(self, mock_orchestrator):
        """Si orchestrator lanza excepción, la maneja"""
        mock_orchestrator.complete.side_effect = Exception("API Error")
        generator = ClaudeSQLGenerator()
        pregunta = "Test"
        
        sql = generator.generar_sql(pregunta)
        
        assert sql is not None
        assert 'ERROR' in sql.upper() or sql == ""
    
    def test_generar_sql_limpia_backticks(self, mock_orchestrator):
        """SQL con ```sql``` debe limpiarse"""
        mock_orchestrator.complete.return_value = "```sql\nSELECT * FROM operaciones\n```"
        generator = ClaudeSQLGenerator()
        pregunta = "Test"
        
        sql = generator.generar_sql(pregunta)
        
        assert "```" not in sql
        assert "SELECT" in sql


# ══════════════════════════════════════════════════════════════
# GRUPO 3: TESTS DE CONTEXTO Y PROMPT
# ══════════════════════════════════════════════════════════════

class TestContextoYPrompt:
    """Tests del contexto y construcción de prompt"""
    
    def test_prompt_usa_temperatura_baja(self, mock_orchestrator):
        """Debe usar temperatura baja para SQL determinístico"""
        generator = ClaudeSQLGenerator()
        generator.generar_sql("Test")
        
        call_kwargs = mock_orchestrator.complete.call_args.kwargs
        # Temperatura debe ser baja (0-0.3) para SQL
        assert call_kwargs.get('temperature', 0) <= 0.3
    
    def test_prompt_usa_max_tokens_suficientes(self, mock_orchestrator):
        """Debe usar suficientes tokens para SQL complejo"""
        generator = ClaudeSQLGenerator()
        generator.generar_sql("Test")
        
        call_kwargs = mock_orchestrator.complete.call_args.kwargs
        assert call_kwargs.get('max_tokens', 0) >= 500


# ══════════════════════════════════════════════════════════════
# GRUPO 4: TESTS DE MANEJO DE ERRORES
# ══════════════════════════════════════════════════════════════

class TestManejoErrores:
    """Tests de manejo de errores"""
    
    def test_error_timeout(self, mock_orchestrator):
        """Timeout debe manejarse gracefully"""
        mock_orchestrator.complete.side_effect = TimeoutError("Timeout")
        generator = ClaudeSQLGenerator()
        
        sql = generator.generar_sql("Test")
        
        assert sql is not None
    
    def test_error_conexion(self, mock_orchestrator):
        """Error de conexión debe manejarse"""
        mock_orchestrator.complete.side_effect = ConnectionError("No connection")
        generator = ClaudeSQLGenerator()
        
        sql = generator.generar_sql("Test")
        
        assert sql is not None
    
    def test_respuesta_vacia(self, mock_orchestrator):
        """Respuesta vacía debe manejarse"""
        mock_orchestrator.complete.return_value = ""
        generator = ClaudeSQLGenerator()
        
        sql = generator.generar_sql("Test")
        
        assert sql is not None
        assert isinstance(sql, str)


# ══════════════════════════════════════════════════════════════
# GRUPO 5: TESTS DE REGLAS DE NEGOCIO
# ══════════════════════════════════════════════════════════════

class TestReglasNegocio:
    """Tests de reglas de negocio en SQL generado"""
    
    def test_regla_deleted_at_en_contexto(self, mock_orchestrator):
        """Contexto debe mencionar deleted_at IS NULL"""
        generator = ClaudeSQLGenerator()
        generator.generar_sql("Test")
        
        call_kwargs = mock_orchestrator.complete.call_args.kwargs
        prompt = call_kwargs['prompt']
        
        assert 'deleted_at IS NULL' in prompt
    
    def test_regla_tipo_operacion_en_contexto(self, mock_orchestrator):
        """Contexto debe explicar tipos de operación"""
        generator = ClaudeSQLGenerator()
        generator.generar_sql("Test")
        
        call_kwargs = mock_orchestrator.complete.call_args.kwargs
        prompt = call_kwargs['prompt']
        
        assert 'INGRESO' in prompt or 'tipo_operacion' in prompt
    
    def test_regla_monedas_en_contexto(self, mock_orchestrator):
        """Contexto debe explicar manejo de monedas"""
        generator = ClaudeSQLGenerator()
        generator.generar_sql("Test")
        
        call_kwargs = mock_orchestrator.complete.call_args.kwargs
        prompt = call_kwargs['prompt']
        
        assert 'UYU' in prompt or 'monto_uyu' in prompt


# ══════════════════════════════════════════════════════════════
# GRUPO 6: TESTS DE INTEGRACIÓN LIGERA
# ══════════════════════════════════════════════════════════════

class TestIntegracionLigera:
    """Tests de integración sin APIs externas"""
    
    def test_multiples_llamadas_consistentes(self, mock_orchestrator):
        """Múltiples llamadas deben ser consistentes"""
        generator = ClaudeSQLGenerator()
        
        sql1 = generator.generar_sql("¿Cuántas operaciones?")
        sql2 = generator.generar_sql("¿Total facturado?")
        
        assert sql1 is not None
        assert sql2 is not None
        assert mock_orchestrator.complete.call_count == 2
    
    def test_preguntas_diferentes_prompts_diferentes(self, mock_orchestrator):
        """Preguntas diferentes deben generar prompts diferentes"""
        generator = ClaudeSQLGenerator()
        
        generator.generar_sql("¿Cuántas operaciones?")
        prompt1 = mock_orchestrator.complete.call_args.kwargs['prompt']
        
        generator.generar_sql("¿Total facturado?")
        prompt2 = mock_orchestrator.complete.call_args.kwargs['prompt']
        
        # Los prompts deben ser diferentes (contienen preguntas diferentes)
        assert prompt1 != prompt2
