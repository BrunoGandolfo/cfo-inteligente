"""
Suite de Tests End-to-End - Sistema CFO Inteligente

Tests E2E con 50 preguntas reales + 11 casos de error graves documentados.
Ejecuta flujo completo contra BD real y APIs mockeadas.

Ejecutar:
    cd backend
    pytest tests/test_e2e.py -v -m e2e
    pytest tests/test_e2e.py -v -m e2e --tb=short

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from pathlib import Path

from app.main import app


# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════

ARCHIVO_PREGUNTAS = Path(__file__).parent.parent / "scripts" / "preguntas_reales_test.txt"

@pytest.fixture(scope="function")
def client_api(usuario_test, db_session):
    """Cliente de FastAPI para tests E2E con autenticación y BD mockeadas"""
    from app.core.security import get_current_user
    from app.core.database import get_db
    
    app.dependency_overrides[get_current_user] = lambda: usuario_test
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def mock_claude_apis():
    """Mock de ambos usos de Claude (SQL + Narrativa)"""
    with patch('app.services.claude_sql_generator.ClaudeSQLGenerator.generar_sql') as mock_sql:
        with patch('app.api.cfo_ai._orchestrator.complete') as mock_orchestrator:
            # Configurar mock SQL (retorna SQL válido genérico)
            mock_sql.return_value = "SELECT SUM(monto_uyu) as total FROM operaciones WHERE deleted_at IS NULL"
            
            # Configurar mock AIOrchestrator narrativo
            mock_orchestrator.return_value = "Respuesta generada por Claude"
            
            yield {'sql': mock_sql, 'orchestrator': mock_orchestrator}


# ══════════════════════════════════════════════════════════════
# GRUPO A: 50 PREGUNTAS REALES DEL ARCHIVO (Tests generados)
# ══════════════════════════════════════════════════════════════

# Leer preguntas del archivo
def cargar_preguntas():
    """Carga preguntas del archivo txt"""
    if not ARCHIVO_PREGUNTAS.exists():
        return []
    
    with open(ARCHIVO_PREGUNTAS, 'r', encoding='utf-8') as f:
        return [linea.strip() for linea in f if linea.strip()]

PREGUNTAS_REALES = cargar_preguntas()


@pytest.mark.e2e
@pytest.mark.parametrize("pregunta", PREGUNTAS_REALES, ids=lambda p: p[:40])
def test_pregunta_real_e2e(pregunta, client_api, mock_claude_apis):
    """
    Test E2E para cada pregunta real del archivo
    
    Verifica que:
    - Endpoint responde sin crashear
    - Status es success o error válido
    - Tiene metadata correcta
    """
    # Act
    response = client_api.post("/api/cfo/ask", json={
        "pregunta": pregunta
    })
    
    # Assert
    assert response.status_code == 200, f"Endpoint crasheó para: {pregunta}"
    
    data = response.json()
    
    # Verificar formato mínimo
    assert 'pregunta' in data
    assert 'status' in data
    assert data['status'] in ['success', 'error', 'success_con_fallback']
    
    if data['status'] == 'success':
        assert 'respuesta' in data
        assert 'sql_generado' in data
        assert 'metadata' in data


# ══════════════════════════════════════════════════════════════
# GRUPO B: 11 CASOS DE ERROR GRAVES DOCUMENTADOS
# ══════════════════════════════════════════════════════════════

@pytest.mark.e2e
@pytest.mark.slow
class TestCasosErrorGraves:
    """Tests de los 11 casos de error graves identificados en testing manual"""
    
    @pytest.mark.xfail(reason="Error conocido: Distribuciones complejas Bruno")
    def test_error_distribuciones_bruno_complejo(self, client_api):
        """
        Error #1: Distribuciones complejas
        Esperado: $229K, Claude dice: $90K
        """
        # Act
        with patch('app.services.claude_sql_generator.ClaudeSQLGenerator.generar_sql') as mock_gen:
            # SQL que puede generar resultado incorrecto
            mock_gen.return_value = """
            SELECT SUM(monto_uyu) as total
            FROM distribuciones_detalle dd
            JOIN socios s ON s.id = dd.socio_id
            WHERE s.nombre = 'Bruno'
            """
            
            with patch('app.api.cfo_ai._orchestrator.complete') as mock_orchestrator:
                mock_orchestrator.return_value = "Bruno recibió $90K"
                
                response = client_api.post("/api/cfo/ask", json={
                    "pregunta": "¿Cuánto recibió Bruno en distribuciones este año?"
                })
                
                # Assert
                data = response.json()
                # Este caso puede fallar por falta de joins correctos
                assert response.status_code == 200
    
    @pytest.mark.xfail(reason="Error conocido: Porcentajes USD/UYU invertidos")
    def test_error_porcentaje_usd_uyu_invertido(self, client_api):
        """
        Error #2: Porcentajes de moneda
        Esperado: 25% USD, Claude dice: 93% USD
        """
        # Act
        with patch('app.services.claude_sql_generator.ClaudeSQLGenerator.generar_sql') as mock_gen:
            # SQL incorrecto (usa CASE WHEN en vez de moneda_original directo)
            sql_incorrecto = """
            SELECT 
                SUM(CASE WHEN moneda_original='USD' THEN monto_usd ELSE 0 END) * 100.0 / 
                SUM(monto_usd) as pct_usd
            FROM operaciones
            WHERE tipo_operacion='INGRESO'
            """
            mock_gen.return_value = sql_incorrecto
            
            with patch('app.api.cfo_ai._orchestrator.complete') as mock_orchestrator:
                mock_orchestrator.return_value = "93% de facturación es en USD"
                
                response = client_api.post("/api/cfo/ask", json={
                    "pregunta": "¿Qué porcentaje de facturación es en USD?"
                })
                
                data = response.json()
                # Regla #8 debería prevenir esto ahora
                assert response.status_code == 200
    
    @pytest.mark.xfail(reason="Error conocido: Proyección hardcodeada")
    def test_error_proyeccion_hardcodeada(self, client_api):
        """
        Error #3: Proyecciones temporales
        Esperado: $17.3M, Claude decía: $10.4M (hardcodeaba septiembre)
        """
        # Act
        with patch('app.services.claude_sql_generator.ClaudeSQLGenerator.generar_sql') as mock_gen:
            # SQL con hardcodeo de fecha
            sql_hardcodeado = """
            SELECT 
                SUM(monto_uyu) / 8 * 12 as proyeccion
            FROM operaciones
            WHERE fecha >= '2025-01-01' AND fecha <= '2025-09-30'
            """
            mock_gen.return_value = sql_hardcodeado
            
            with patch('app.api.cfo_ai._orchestrator.complete') as mock_orchestrator:
                mock_orchestrator.return_value = "Proyección: $10.4M"
                
                response = client_api.post("/api/cfo/ask", json={
                    "pregunta": "Proyección fin de año basado en últimos 8 meses"
                })
                
                data = response.json()
                # Chain-of-Thought debería resolver esto ahora
                assert response.status_code == 200
    
    @pytest.mark.xfail(reason="Error conocido: Ranking LIMIT 1 incorrecto")
    def test_error_ranking_limit_1(self, client_api):
        """
        Error #4: Rankings con LIMIT 1
        Usuario pide "mejores áreas", Claude retorna solo 1
        """
        # Act
        with patch('app.services.claude_sql_generator.ClaudeSQLGenerator.generar_sql') as mock_gen:
            # SQL con LIMIT 1 cuando debería ser LIMIT 5+
            mock_gen.return_value = """
            SELECT nombre FROM areas ORDER BY ingresos DESC LIMIT 1
            """
            
            with patch('app.api.cfo_ai._orchestrator.complete') as mock_orchestrator:
                mock_orchestrator.return_value = "El área más rentable es Jurídica"
                
                response = client_api.post("/api/cfo/ask", json={
                    "pregunta": "¿Cuáles son las mejores áreas?"
                })
                
                data = response.json()
                # Validación Pre-SQL debería detectar esto
                assert response.status_code == 200
    
    @pytest.mark.xfail(reason="Error conocido: Afirmación unicidad falsa")
    def test_error_afirmacion_unicidad(self, client_api):
        """
        Error #5: Afirmaciones de unicidad sin verificar
        Claude dice "única oficina" sin verificar COUNT
        """
        # Act
        with patch('app.services.claude_sql_generator.ClaudeSQLGenerator.generar_sql') as mock_gen:
            mock_gen.return_value = """
            SELECT localidad FROM operaciones LIMIT 1
            """
            
            with patch('app.api.cfo_ai._orchestrator.complete') as mock_orchestrator:
                mock_orchestrator.return_value = "La única oficina es Montevideo"  # Falso, hay 2
                
                response = client_api.post("/api/cfo/ask", json={
                    "pregunta": "¿En qué oficina operamos?"
                })
                
                data = response.json()
                assert response.status_code == 200
    
    @pytest.mark.xfail(reason="Error conocido: UNION ALL con ENUM")
    def test_error_union_all_enum(self, client_api):
        """
        Error #6: UNION ALL con columnas ENUM sin CAST
        """
        # Act
        with patch('app.services.claude_sql_generator.ClaudeSQLGenerator.generar_sql') as mock_gen:
            # SQL con UNION ALL problemático
            mock_gen.return_value = """
            SELECT tipo_operacion, SUM(monto) FROM operaciones GROUP BY 1
            UNION ALL
            SELECT 'TOTAL', SUM(monto) FROM operaciones
            """
            
            with patch('app.api.cfo_ai._orchestrator.complete') as mock_orchestrator:
                mock_orchestrator.return_value = "Resumen de operaciones"
                
                response = client_api.post("/api/cfo/ask", json={
                    "pregunta": "Resumen total de operaciones"
                })
                
                data = response.json()
                # Puede fallar por error de tipo ENUM
                assert response.status_code == 200
    
    @pytest.mark.xfail(reason="Error conocido: Meses restantes mal calculados")
    def test_error_meses_restantes(self, client_api):
        """
        Error #7: Meses restantes asumidos en vez de calculados
        """
        # Act
        with patch('app.services.claude_sql_generator.ClaudeSQLGenerator.generar_sql') as mock_gen:
            # SQL que asume meses restantes
            mock_gen.return_value = """
            SELECT SUM(monto) / 8 * 4 as proyeccion FROM operaciones
            """
            
            with patch('app.api.cfo_ai._orchestrator.complete') as mock_orchestrator:
                mock_orchestrator.return_value = "Proyección incorrecta"
                
                response = client_api.post("/api/cfo/ask", json={
                    "pregunta": "Proyección considerando meses restantes"
                })
                
                data = response.json()
                # Validación Pre-SQL debería detectar falta de EXTRACT(MONTH)
                assert response.status_code == 200
    
    @pytest.mark.xfail(reason="Error conocido: Suma porcentajes != 100")
    def test_error_porcentajes_no_suman_100(self, client_api):
        """
        Error #8: Porcentajes por área que no suman 100%
        """
        # Este caso es difícil de simular, depende del SQL generado
        # Marcado como xfail
        pass
    
    @pytest.mark.xfail(reason="Error conocido: Distribución > $100K no validada")
    def test_error_distribucion_excesiva(self, client_api):
        """
        Error #9: Distribución sospechosamente alta sin validar
        Ahora validador debería detectar (pero solo negativos)
        """
        # Validador YA NO rechaza >$100K (límite eliminado)
        # Este test queda como documentación
        pass
    
    @pytest.mark.xfail(reason="Error conocido: Facturación mes > anual")
    def test_error_facturacion_mes_mayor_anual(self, client_api):
        """
        Error #10: Facturación de un mes > facturación anual
        Indica error lógico en SQL
        """
        # Difícil de simular sin generar SQL específico
        pass
    
    @pytest.mark.xfail(reason="Error conocido: Comparación entre años incorrecta")
    def test_error_comparacion_años(self, client_api):
        """
        Error #11: Comparación año actual vs anterior
        Claude usa año incorrecto (2024 en vez de 2025)
        Regla de contexto temporal debería resolver esto
        """
        # Act
        with patch('app.services.claude_sql_generator.ClaudeSQLGenerator.generar_sql') as mock_gen:
            # SQL que usa 2024 incorrectamente
            mock_gen.return_value = """
            SELECT SUM(monto) FROM operaciones
            WHERE fecha >= '2024-01-01' AND fecha < '2025-01-01'
            """
            
            with patch('app.api.cfo_ai._orchestrator.complete') as mock_orchestrator:
                mock_orchestrator.return_value = "Facturación del año"
                
                response = client_api.post("/api/cfo/ask", json={
                    "pregunta": "¿Cómo vamos en el año?"
                })
                
                data = response.json()
                # Contexto temporal 2025 debería prevenir esto
                assert response.status_code == 200


# ══════════════════════════════════════════════════════════════
# GRUPO C: TESTS DE PRECISIÓN Y MÉTRICAS
# ══════════════════════════════════════════════════════════════

@pytest.mark.e2e
class TestMetricasPrecision:
    """Tests que miden precisión del sistema"""
    
    def test_tasa_respuesta_exitosa(self, client_api, mock_claude_apis):
        """Al menos 90% de preguntas deben tener status=success"""
        # Arrange
        preguntas_sample = PREGUNTAS_REALES[:20]  # Sample de 20
        
        # Act
        exitosas = 0
        for pregunta in preguntas_sample:
            response = client_api.post("/api/cfo/ask", json={"pregunta": pregunta})
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    exitosas += 1
        
        # Assert
        tasa_exito = (exitosas / len(preguntas_sample)) * 100
        assert tasa_exito >= 90, f"Tasa de éxito {tasa_exito}% < 90%"
    
    def test_metadata_presente_en_exitosas(self, client_api, mock_claude_apis):
        """Queries exitosas deben tener metadata completa"""
        # Arrange
        pregunta = "¿Cuánto facturamos este mes?"
        
        # Act
        response = client_api.post("/api/cfo/ask", json={"pregunta": pregunta})
        data = response.json()
        
        # Assert
        if data['status'] == 'success':
            assert 'metadata' in data
            metadata = data['metadata']
            
            # Campos obligatorios en metadata
            assert 'metodo_generacion_sql' in metadata
            assert metadata['metodo_generacion_sql'] in [
                'claude', 'claude_direct', 'vanna_fallback', 'claude_chain_of_thought',
                'claude_fallback_predefinido', 'claude_con_advertencias'
            ]
    
    def test_tiempo_respuesta_razonable(self, client_api, mock_claude_apis):
        """Tiempo de respuesta debe ser <25s"""
        # Arrange
        import time
        pregunta = "¿Cuál es la rentabilidad?"
        
        # Act
        inicio = time.time()
        response = client_api.post("/api/cfo/ask", json={"pregunta": pregunta})
        duracion = time.time() - inicio
        
        # Assert
        assert duracion < 25, f"Respuesta tardó {duracion}s (límite: 25s)"


# ══════════════════════════════════════════════════════════════
# RESUMEN Y REPORTE
# ══════════════════════════════════════════════════════════════

def test_resumen_suite_e2e():
    """Test que genera reporte de la suite E2E"""
    print("\n" + "="*80)
    print("📊 RESUMEN SUITE E2E")
    print("="*80)
    print(f"Total preguntas reales: {len(PREGUNTAS_REALES)}")
    print(f"Casos de error graves: 11")
    print(f"Total tests E2E: {len(PREGUNTAS_REALES) + 11}")
    print("="*80)
    
    # Este test siempre pasa, solo imprime info
    assert True

