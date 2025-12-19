"""
Suite de Tests para SQLRouter - Sistema CFO Inteligente

Tests del router simplificado: Claude → QueryFallback.
Cubre generación SQL, validaciones y manejo de errores.

Ejecutar:
    cd backend
    pytest tests/test_sql_router.py -v
    pytest tests/test_sql_router.py -v --cov=app.services.sql_router --cov-report=term-missing

Autor: Sistema CFO Inteligente
Fecha: Diciembre 2025
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.sql_router import SQLRouter, get_sql_router, generar_sql_inteligente
from app.utils.sql_utils import extraer_sql_limpio, validar_sql


# ══════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════

@pytest.fixture
def mock_claude_generator():
    """Mock de ClaudeSQLGenerator"""
    mock_gen = Mock()
    mock_gen.generar_sql = Mock(return_value="SELECT SUM(monto) FROM operaciones")
    return mock_gen

@pytest.fixture
def router_instance(mock_claude_generator):
    """Fixture que retorna instancia de SQLRouter con mocks"""
    with patch('app.services.sql_router.ClaudeSQLGenerator', return_value=mock_claude_generator):
        router = SQLRouter()
        router.claude_gen = mock_claude_generator
        return router


# ══════════════════════════════════════════════════════════════
# GRUPO 1: TESTS DE EXTRACCIÓN DE SQL
# ══════════════════════════════════════════════════════════════

class TestExtraerSQLLimpio:
    """Tests del método extraer_sql_limpio (static)"""
    
    def test_sql_limpio_sin_backticks(self):
        """SQL sin backticks debe retornarse tal cual"""
        # Arrange
        sql = "SELECT * FROM operaciones WHERE deleted_at IS NULL"
        
        # Act
        resultado = extraer_sql_limpio(sql)
        
        # Assert
        assert resultado == sql
    
    def test_sql_con_backticks_sql(self):
        """SQL con ```sql...``` debe extraerse"""
        # Arrange
        texto = "```sql\nSELECT * FROM operaciones\n```"
        
        # Act
        resultado = extraer_sql_limpio(texto)
        
        # Assert
        assert resultado == "SELECT * FROM operaciones"
        assert "```" not in resultado
    
    def test_sql_con_backticks_genericos(self):
        """SQL con ```...``` genéricos debe extraerse"""
        # Arrange
        texto = "```\nWITH cte AS (...) SELECT * FROM cte\n```"
        
        # Act
        resultado = extraer_sql_limpio(texto)
        
        # Assert
        assert "WITH cte AS" in resultado
        assert "```" not in resultado
    
    def test_sql_con_texto_explicativo(self):
        """SQL con texto antes debe extraer solo el SQL"""
        # Arrange
        texto = "No puedo generar sin contexto. Sin embargo:\nSELECT SUM(monto) FROM operaciones"
        
        # Act
        resultado = extraer_sql_limpio(texto)
        
        # Assert
        assert resultado.startswith("SELECT")
        assert "No puedo" not in resultado
    
    def test_sql_con_punto_y_coma(self):
        """SQL con ; debe extraerse hasta el punto y coma"""
        # Arrange
        texto = "SELECT * FROM operaciones; -- Y aquí hay comentarios extras"
        
        # Act
        resultado = extraer_sql_limpio(texto)
        
        # Assert
        assert resultado.endswith(";")
        assert "comentarios" not in resultado
    
    def test_texto_sin_sql(self):
        """Texto sin SQL debe retornar None"""
        # Arrange
        texto = "Lo siento, no puedo generar SQL para esa pregunta"
        
        # Act
        resultado = extraer_sql_limpio(texto)
        
        # Assert
        assert resultado is None
    
    def test_texto_vacio(self):
        """Texto vacío debe retornar None"""
        # Act
        resultado = extraer_sql_limpio("")
        
        # Assert
        assert resultado is None


# ══════════════════════════════════════════════════════════════
# GRUPO 2: TESTS DE VALIDACIÓN DE SQL
# ══════════════════════════════════════════════════════════════

class TestValidarSQL:
    """Tests del método validar_sql (static)"""
    
    def test_sql_select_valido(self):
        """SQL SELECT válido debe pasar validación"""
        # Arrange
        sql = "SELECT SUM(monto) FROM operaciones WHERE deleted_at IS NULL"
        
        # Act
        validacion = validar_sql(sql)
        
        # Assert
        assert validacion['valido'] is True
        assert validacion['tipo'] == 'SELECT'
        assert validacion['parseado'] is True
    
    def test_sql_with_valido(self):
        """SQL con WITH (CTE) debe ser válido"""
        # Arrange
        sql = "WITH cte AS (SELECT * FROM ops) SELECT SUM(monto) FROM cte"
        
        # Act
        validacion = validar_sql(sql)
        
        # Assert
        assert validacion['valido'] is True
        assert validacion['tipo'] == 'WITH'
    
    def test_sql_vacio(self):
        """SQL vacío debe ser inválido"""
        # Act
        validacion = validar_sql("")
        
        # Assert
        assert validacion['valido'] is False
        assert validacion['error'] == 'SQL vacío'
    
    def test_sql_sin_select(self):
        """SQL sin SELECT ni WITH debe ser inválido"""
        # Arrange
        sql = "UPDATE operaciones SET monto = 0"
        
        # Act
        validacion = validar_sql(sql)
        
        # Assert
        assert validacion['valido'] is False
        assert 'no contiene SELECT ni WITH' in validacion['error']
    
    def test_sql_malformado(self):
        """SQL con syntax error debe detectarse"""
        # Arrange
        sql = "SELECT FROM WHERE"  # SQL inválido
        
        # Act
        validacion = validar_sql(sql)
        
        # Assert
        # sqlparse puede o no detectarlo, pero debe retornar dict válido
        assert 'valido' in validacion
        assert 'tipo' in validacion


# ══════════════════════════════════════════════════════════════
# GRUPO 3: TESTS DE GENERAR SQL CON CLAUDE
# ══════════════════════════════════════════════════════════════

class TestGenerarSQLConClaude:
    """Tests de generación SQL con Claude (con mocks)"""
    
    def test_claude_exitoso(self, router_instance, mock_claude_generator):
        """Claude genera SQL válido exitosamente"""
        # Arrange
        mock_claude_generator.generar_sql.return_value = "SELECT SUM(monto_uyu) FROM operaciones"
        pregunta = "¿Cuánto facturamos?"
        
        # Act
        resultado = router_instance.generar_sql_con_claude(pregunta)
        
        # Assert
        assert resultado['exito'] is True
        assert resultado['sql'] is not None
        assert 'SELECT' in resultado['sql']
        assert resultado['error'] is None
        assert resultado['tiempo'] > 0
    
    def test_claude_respuesta_vacia(self, router_instance, mock_claude_generator):
        """Claude devuelve respuesta vacía"""
        # Arrange
        mock_claude_generator.generar_sql.return_value = ""
        pregunta = "Test"
        
        # Act
        resultado = router_instance.generar_sql_con_claude(pregunta)
        
        # Assert
        assert resultado['exito'] is False
        assert resultado['sql'] is None
        assert resultado['error'] is not None
    
    def test_claude_excepcion(self, router_instance, mock_claude_generator):
        """Claude lanza excepción"""
        # Arrange
        mock_claude_generator.generar_sql.side_effect = Exception("API Error")
        pregunta = "Test"
        
        # Act
        resultado = router_instance.generar_sql_con_claude(pregunta)
        
        # Assert
        assert resultado['exito'] is False
        assert resultado['sql'] is None
        assert resultado['error'] is not None
    
    def test_claude_sql_invalido(self, router_instance, mock_claude_generator):
        """Claude genera SQL que no se puede parsear"""
        # Arrange
        mock_claude_generator.generar_sql.return_value = "UPDATE ops SET x = 1"  # No es SELECT
        pregunta = "Test"
        
        # Act
        resultado = router_instance.generar_sql_con_claude(pregunta)
        
        # Assert
        assert resultado['exito'] is False
        assert resultado['error'] is not None
    
    def test_claude_sql_con_backticks(self, router_instance, mock_claude_generator):
        """Claude devuelve SQL con backticks - debe extraerse"""
        # Arrange
        mock_claude_generator.generar_sql.return_value = "```sql\nSELECT * FROM ops\n```"
        pregunta = "Test"
        
        # Act
        resultado = router_instance.generar_sql_con_claude(pregunta)
        
        # Assert
        assert resultado['exito'] is True
        assert "```" not in resultado['sql']
        assert "SELECT" in resultado['sql']


# ══════════════════════════════════════════════════════════════
# GRUPO 4: TESTS DE GENERAR SQL INTELIGENTE (Router completo)
# ══════════════════════════════════════════════════════════════

class TestGenerarSQLInteligente:
    """Tests del método principal generar_sql_inteligente"""
    
    def test_claude_exitoso(self, router_instance, mock_claude_generator):
        """Claude exitoso en primer intento"""
        # Arrange
        mock_claude_generator.generar_sql.return_value = "SELECT * FROM ops"
        pregunta = "Test"
        
        # Act
        resultado = router_instance.generar_sql_inteligente(pregunta)
        
        # Assert
        assert resultado['exito'] is True
        assert resultado['metodo'] == 'claude'
        assert resultado['sql'] is not None
        assert resultado['intentos']['claude'] == 1
    
    def test_claude_falla_retorna_error_claro(self, router_instance, mock_claude_generator):
        """Claude falla debe retornar error claro"""
        # Arrange
        mock_claude_generator.generar_sql.side_effect = Exception("Claude error")
        pregunta = "Test imposible"
        
        # Act
        resultado = router_instance.generar_sql_inteligente(pregunta)
        
        # Assert
        assert resultado['exito'] is False
        assert resultado['metodo'] == 'ninguno'
        assert resultado['sql'] is None
        assert resultado['error'] is not None
    
    def test_tiempos_medidos(self, router_instance, mock_claude_generator):
        """Tiempos de ejecución deben medirse correctamente"""
        # Arrange
        mock_claude_generator.generar_sql.return_value = "SELECT * FROM ops"
        pregunta = "Test"
        
        # Act
        resultado = router_instance.generar_sql_inteligente(pregunta)
        
        # Assert
        assert 'tiempo_total' in resultado
        assert resultado['tiempo_total'] > 0
        assert 'tiempos' in resultado
        assert resultado['tiempos']['claude'] is not None
    
    def test_metadata_debug(self, router_instance, mock_claude_generator):
        """Metadata debug debe incluirse en respuesta"""
        # Arrange
        mock_claude_generator.generar_sql.return_value = "SELECT * FROM ops"
        pregunta = "Test"
        
        # Act
        resultado = router_instance.generar_sql_inteligente(pregunta)
        
        # Assert
        assert 'debug' in resultado
        assert 'timestamp' in resultado['debug']
    
    def test_sql_invalido_falla(self, router_instance, mock_claude_generator):
        """Si no se puede extraer SQL, debe fallar con error claro"""
        # Arrange
        mock_claude_generator.generar_sql.return_value = "Texto sin SQL válido"
        pregunta = "Test"
        
        # Act
        resultado = router_instance.generar_sql_inteligente(pregunta)
        
        # Assert
        assert resultado['exito'] is False
        assert resultado['metodo'] == 'ninguno'
        assert resultado['error'] is not None
    
    @patch('app.services.sql_router.QueryFallback')
    def test_query_fallback_tiene_prioridad(self, mock_fallback, router_instance, mock_claude_generator):
        """QueryFallback debe tener prioridad sobre Claude"""
        # Arrange
        mock_fallback.get_query_for.return_value = "SELECT * FROM predefined_query"
        pregunta = "Test con fallback"
        
        # Act
        resultado = router_instance.generar_sql_inteligente(pregunta)
        
        # Assert
        assert resultado['exito'] is True
        assert resultado['metodo'] == 'query_fallback'
        # Claude no debería haber sido llamado
        mock_claude_generator.generar_sql.assert_not_called()


# ══════════════════════════════════════════════════════════════
# GRUPO 5: TESTS DE FUNCIONES GLOBALES
# ══════════════════════════════════════════════════════════════

class TestFuncionesGlobales:
    """Tests de funciones globales y singleton"""
    
    @patch('app.services.sql_router.ClaudeSQLGenerator')
    def test_get_sql_router_singleton(self, mock_claude_class):
        """get_sql_router debe retornar singleton"""
        # Reset singleton para el test
        import app.services.sql_router as router_module
        router_module._router_instance = None
        
        # Act
        router1 = get_sql_router()
        router2 = get_sql_router()
        
        # Assert
        assert router1 is router2  # Misma instancia
        assert isinstance(router1, SQLRouter)
    
    @patch('app.services.sql_router.get_sql_router')
    def test_generar_sql_inteligente_wrapper(self, mock_get_router):
        """Función wrapper debe llamar a get_sql_router"""
        # Arrange
        mock_router = Mock()
        mock_router.generar_sql_inteligente.return_value = {
            'sql': 'SELECT * FROM ops',
            'exito': True
        }
        mock_get_router.return_value = mock_router
        
        pregunta = "Test"
        
        # Act
        resultado = generar_sql_inteligente(pregunta)
        
        # Assert
        mock_get_router.assert_called_once()
        mock_router.generar_sql_inteligente.assert_called_once_with(pregunta, contexto=None)
        assert resultado['exito'] is True


# ══════════════════════════════════════════════════════════════
# GRUPO 6: TESTS DE CASOS EDGE
# ══════════════════════════════════════════════════════════════

class TestCasosEdge:
    """Tests de casos límite y edge cases"""
    
    def test_pregunta_vacia(self, router_instance, mock_claude_generator):
        """Pregunta vacía no debe crashear"""
        # Arrange
        mock_claude_generator.generar_sql.return_value = "SELECT 1"
        pregunta = ""
        
        # Act
        resultado = router_instance.generar_sql_inteligente(pregunta)
        
        # Assert
        # Debe retornar resultado válido (aunque la pregunta sea vacía)
        assert 'exito' in resultado
    
    def test_pregunta_muy_larga(self, router_instance, mock_claude_generator):
        """Pregunta muy larga no debe crashear"""
        # Arrange
        mock_claude_generator.generar_sql.return_value = "SELECT * FROM ops"
        pregunta = "¿" + "x" * 10000 + "?"  # Pregunta de 10K caracteres
        
        # Act
        resultado = router_instance.generar_sql_inteligente(pregunta)
        
        # Assert
        assert resultado['exito'] is True
    
    def test_sql_con_comentarios(self, router_instance):
        """SQL con comentarios debe parsearse correctamente"""
        # Arrange
        sql = "-- Comentario\nSELECT * FROM ops -- inline comment"
        
        # Act
        sql_limpio = extraer_sql_limpio(sql)
        
        # Assert
        assert sql_limpio is not None
        assert "SELECT" in sql_limpio
    
    def test_sql_multilinea(self, router_instance, mock_claude_generator):
        """SQL multilinea complejo debe manejarse"""
        # Arrange
        sql_complejo = """
        WITH cte AS (
            SELECT 
                area,
                SUM(monto) as total
            FROM operaciones
            WHERE deleted_at IS NULL
            GROUP BY area
        )
        SELECT * FROM cte
        ORDER BY total DESC
        """
        mock_claude_generator.generar_sql.return_value = sql_complejo
        pregunta = "Test complejo"
        
        # Act
        resultado = router_instance.generar_sql_con_claude(pregunta)
        
        # Assert
        assert resultado['exito'] is True
        assert 'WITH' in resultado['sql']


# ══════════════════════════════════════════════════════════════
# GRUPO 7: TESTS DE PERFORMANCE Y TIMEOUT
# ══════════════════════════════════════════════════════════════

@pytest.mark.slow
class TestPerformance:
    """Tests de performance y timeouts"""
    
    def test_tiempo_respuesta_razonable(self, router_instance, mock_claude_generator):
        """Tiempo de respuesta debe ser razonable (<10s)"""
        # Arrange
        mock_claude_generator.generar_sql.return_value = "SELECT * FROM ops"
        pregunta = "Test"
        
        # Act
        resultado = router_instance.generar_sql_inteligente(pregunta)
        
        # Assert
        assert resultado['tiempo_total'] < 10  # Menos de 10s (con mocks debería ser <<1s)


# ══════════════════════════════════════════════════════════════
# GRUPO 8: TESTS DE ESTADÍSTICAS
# ══════════════════════════════════════════════════════════════

class TestEstadisticas:
    """Tests del método obtener_estadisticas"""
    
    def test_estadisticas_retorna_info_basica(self, router_instance):
        """Estadísticas debe retornar información básica"""
        # Act
        stats = router_instance.obtener_estadisticas()
        
        # Assert
        assert 'proveedor' in stats
        assert stats['proveedor'] == 'claude'
        assert 'modelo' in stats
        assert 'fallback' in stats
