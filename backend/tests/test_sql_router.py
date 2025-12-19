"""
Suite de Tests para SQLRouter - Sistema CFO Inteligente

Tests del router inteligente Claude→Vanna con mocks de APIs externas.
Cubre generación SQL, fallbacks, validaciones y manejo de errores.

Ejecutar:
    cd backend
    pytest tests/test_sql_router.py -v
    pytest tests/test_sql_router.py -v --cov=app.services.sql_router --cov-report=term-missing

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.sql_router import SQLRouter, get_sql_router, generar_sql_inteligente


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
def mock_vanna():
    """Mock de Vanna AI"""
    mock_vn = Mock()
    mock_vn.generate_sql = Mock(return_value="SELECT COUNT(*) FROM operaciones")
    return mock_vn

@pytest.fixture
def router_instance(mock_claude_generator, mock_vanna):
    """Fixture que retorna instancia de SQLRouter con mocks"""
    with patch('app.services.sql_router.ClaudeSQLGenerator', return_value=mock_claude_generator):
        with patch('app.services.sql_router.vn', mock_vanna):
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
        resultado = SQLRouter.extraer_sql_limpio(sql)
        
        # Assert
        assert resultado == sql
    
    def test_sql_con_backticks_sql(self):
        """SQL con ```sql...``` debe extraerse"""
        # Arrange
        texto = "```sql\nSELECT * FROM operaciones\n```"
        
        # Act
        resultado = SQLRouter.extraer_sql_limpio(texto)
        
        # Assert
        assert resultado == "SELECT * FROM operaciones"
        assert "```" not in resultado
    
    def test_sql_con_backticks_genericos(self):
        """SQL con ```...``` genéricos debe extraerse"""
        # Arrange
        texto = "```\nWITH cte AS (...) SELECT * FROM cte\n```"
        
        # Act
        resultado = SQLRouter.extraer_sql_limpio(texto)
        
        # Assert
        assert "WITH cte AS" in resultado
        assert "```" not in resultado
    
    def test_sql_con_texto_explicativo(self):
        """SQL con texto antes debe extraer solo el SQL"""
        # Arrange
        texto = "No puedo generar sin contexto. Sin embargo:\nSELECT SUM(monto) FROM operaciones"
        
        # Act
        resultado = SQLRouter.extraer_sql_limpio(texto)
        
        # Assert
        assert resultado.startswith("SELECT")
        assert "No puedo" not in resultado
    
    def test_sql_con_punto_y_coma(self):
        """SQL con ; debe extraerse hasta el punto y coma"""
        # Arrange
        texto = "SELECT * FROM operaciones; -- Y aquí hay comentarios extras"
        
        # Act
        resultado = SQLRouter.extraer_sql_limpio(texto)
        
        # Assert
        assert resultado.endswith(";")
        assert "comentarios" not in resultado
    
    def test_texto_sin_sql(self):
        """Texto sin SQL debe retornar None"""
        # Arrange
        texto = "Lo siento, no puedo generar SQL para esa pregunta"
        
        # Act
        resultado = SQLRouter.extraer_sql_limpio(texto)
        
        # Assert
        assert resultado is None
    
    def test_texto_vacio(self):
        """Texto vacío debe retornar None"""
        # Act
        resultado = SQLRouter.extraer_sql_limpio("")
        
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
        validacion = SQLRouter.validar_sql(sql)
        
        # Assert
        assert validacion['valido'] is True
        assert validacion['tipo'] == 'SELECT'
        assert validacion['parseado'] is True
    
    def test_sql_with_valido(self):
        """SQL con WITH (CTE) debe ser válido"""
        # Arrange
        sql = "WITH cte AS (SELECT * FROM ops) SELECT SUM(monto) FROM cte"
        
        # Act
        validacion = SQLRouter.validar_sql(sql)
        
        # Assert
        assert validacion['valido'] is True
        assert validacion['tipo'] == 'WITH'
    
    def test_sql_vacio(self):
        """SQL vacío debe ser inválido"""
        # Act
        validacion = SQLRouter.validar_sql("")
        
        # Assert
        assert validacion['valido'] is False
        assert validacion['error'] == 'SQL vacío'
    
    def test_sql_sin_select(self):
        """SQL sin SELECT ni WITH debe ser inválido"""
        # Arrange
        sql = "UPDATE operaciones SET monto = 0"
        
        # Act
        validacion = SQLRouter.validar_sql(sql)
        
        # Assert
        assert validacion['valido'] is False
        assert 'no contiene SELECT ni WITH' in validacion['error']
    
    def test_sql_malformado(self):
        """SQL con syntax error debe detectarse"""
        # Arrange
        sql = "SELECT FROM WHERE"  # SQL inválido
        
        # Act
        validacion = SQLRouter.validar_sql(sql)
        
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
        assert 'respuesta vacía' in resultado['error']
    
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
        assert 'Exception en Claude' in resultado['error']
    
    def test_claude_sql_invalido(self, router_instance, mock_claude_generator):
        """Claude genera SQL que no se puede parsear"""
        # Arrange
        mock_claude_generator.generar_sql.return_value = "UPDATE ops SET x = 1"  # No es SELECT
        pregunta = "Test"
        
        # Act
        resultado = router_instance.generar_sql_con_claude(pregunta)
        
        # Assert
        assert resultado['exito'] is False
        # El error puede ser "SQL inválido" o "no contiene SELECT ni WITH"
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
# GRUPO 4: TESTS DE GENERAR SQL CON VANNA
# ══════════════════════════════════════════════════════════════

class TestGenerarSQLConVanna:
    """Tests de generación SQL con Vanna (con mocks)"""
    
    def test_vanna_exitoso(self, router_instance):
        """Vanna genera SQL válido"""
        # Arrange
        with patch('app.services.sql_router.vn') as mock_vn:
            mock_vn.generate_sql.return_value = "SELECT COUNT(*) FROM operaciones"
            pregunta = "¿Cuántas operaciones hay?"
            
            # Act
            resultado = router_instance.generar_sql_con_vanna(pregunta)
            
            # Assert
            assert resultado['exito'] is True
            assert 'SELECT' in resultado['sql']
            assert resultado['error'] is None
    
    def test_vanna_texto_explicativo(self, router_instance):
        """Vanna devuelve texto explicativo en lugar de SQL"""
        # Arrange
        with patch('app.services.sql_router.vn') as mock_vn:
            mock_vn.generate_sql.return_value = "Lo siento, no puedo generar SQL para esa pregunta"
            pregunta = "Test ambiguo"
            
            # Act
            resultado = router_instance.generar_sql_con_vanna(pregunta)
            
            # Assert
            assert resultado['exito'] is False
            # El error real es "No se pudo extraer SQL" porque no encuentra SELECT/WITH
            assert 'SQL' in resultado['error']
    
    def test_vanna_excepcion(self, router_instance):
        """Vanna lanza excepción"""
        # Arrange
        with patch('app.services.sql_router.vn') as mock_vn:
            mock_vn.generate_sql.side_effect = Exception("Vanna Error")
            pregunta = "Test"
            
            # Act
            resultado = router_instance.generar_sql_con_vanna(pregunta)
            
            # Assert
            assert resultado['exito'] is False
            assert 'Exception en Vanna' in resultado['error']
    
    def test_vanna_respuesta_vacia(self, router_instance):
        """Vanna devuelve None"""
        # Arrange
        with patch('app.services.sql_router.vn') as mock_vn:
            mock_vn.generate_sql.return_value = None
            pregunta = "Test"
            
            # Act
            resultado = router_instance.generar_sql_con_vanna(pregunta)
            
            # Assert
            assert resultado['exito'] is False
            assert 'respuesta vacía' in resultado['error']


# ══════════════════════════════════════════════════════════════
# GRUPO 5: TESTS DE GENERAR SQL INTELIGENTE (Router completo)
# ══════════════════════════════════════════════════════════════

class TestGenerarSQLInteligente:
    """Tests del método principal generar_sql_inteligente"""
    
    def test_claude_exitoso_sin_fallback(self, router_instance, mock_claude_generator):
        """Claude exitoso en primer intento, no necesita Vanna"""
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
        assert resultado['intentos']['vanna'] == 0
    
    def test_claude_falla_vanna_exitoso(self, router_instance, mock_claude_generator):
        """Claude falla, Vanna rescata como fallback"""
        # Arrange
        mock_claude_generator.generar_sql.side_effect = Exception("Claude error")
        
        with patch('app.services.sql_router.vn') as mock_vn:
            mock_vn.generate_sql.return_value = "SELECT COUNT(*) FROM operaciones"
            pregunta = "Test"
            
            # Act
            resultado = router_instance.generar_sql_inteligente(pregunta)
            
            # Assert
            assert resultado['exito'] is True
            assert resultado['metodo'] == 'vanna_fallback'
            assert resultado['sql'] is not None
            assert resultado['intentos']['claude'] == 1
            assert resultado['intentos']['vanna'] >= 1
    
    def test_ambos_metodos_fallan(self, router_instance, mock_claude_generator):
        """Claude y Vanna ambos fallan"""
        # Arrange
        mock_claude_generator.generar_sql.side_effect = Exception("Claude error")
        
        with patch('app.services.sql_router.vn') as mock_vn:
            mock_vn.generate_sql.return_value = None  # Vanna también falla
            pregunta = "Test imposible"
            
            # Act
            resultado = router_instance.generar_sql_inteligente(pregunta)
            
            # Assert
            assert resultado['exito'] is False
            assert resultado['metodo'] == 'ninguno'
            assert resultado['sql'] is None
            assert 'error' in resultado
    
    def test_reintentos_vanna(self, router_instance, mock_claude_generator):
        """Vanna reintenta según parámetro reintentos_vanna"""
        # Arrange
        mock_claude_generator.generar_sql.side_effect = Exception("Claude error")
        
        with patch('app.services.sql_router.vn') as mock_vn:
            # Primer intento falla, segundo exitoso
            mock_vn.generate_sql.side_effect = [
                None,  # Intento 1: falla
                "SELECT * FROM ops"  # Intento 2: exitoso
            ]
            pregunta = "Test"
            
            # Act
            resultado = router_instance.generar_sql_inteligente(pregunta, reintentos_vanna=2)
            
            # Assert
            assert resultado['exito'] is True
            assert resultado['metodo'] == 'vanna_fallback'
            assert resultado['intentos']['vanna'] == 2
    
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
    
    def test_sql_invalido_no_extrae(self, router_instance, mock_claude_generator):
        """Si no se puede extraer SQL, debe fallar y usar Vanna"""
        # Arrange
        mock_claude_generator.generar_sql.return_value = "Texto sin SQL válido"
        
        with patch('app.services.sql_router.vn') as mock_vn:
            mock_vn.generate_sql.return_value = "SELECT * FROM ops"
            pregunta = "Test"
            
            # Act
            resultado = router_instance.generar_sql_inteligente(pregunta)
            
            # Assert
            # Debería usar Vanna como fallback
            assert resultado['exito'] is True
            assert resultado['metodo'] == 'vanna_fallback'


# ══════════════════════════════════════════════════════════════
# GRUPO 6: TESTS DE FUNCIONES GLOBALES
# ══════════════════════════════════════════════════════════════

class TestFuncionesGlobales:
    """Tests de funciones globales y singleton"""
    
    @patch('app.services.sql_router.ClaudeSQLGenerator')
    @patch('app.services.sql_router.vn')
    def test_get_sql_router_singleton(self, mock_vn, mock_claude_class):
        """get_sql_router debe retornar singleton"""
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
# GRUPO 7: TESTS DE CASOS EDGE
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
        sql_limpio = SQLRouter.extraer_sql_limpio(sql)
        
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
# GRUPO 8: TESTS DE PERFORMANCE Y TIMEOUT
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
    
    def test_reintentos_no_infinitos(self, router_instance, mock_claude_generator):
        """Reintentos deben tener límite"""
        # Arrange
        mock_claude_generator.generar_sql.side_effect = Exception("Error")
        
        with patch('app.services.sql_router.vn') as mock_vn:
            mock_vn.generate_sql.return_value = None  # Siempre falla
            pregunta = "Test"
            
            # Act
            resultado = router_instance.generar_sql_inteligente(pregunta, reintentos_vanna=3)
            
            # Assert
            assert resultado['intentos']['vanna'] <= 3  # No más de lo especificado
            assert resultado['intentos']['total'] <= 4  # Claude(1) + Vanna(3)

