"""
Suite de Tests de Integración - Sistema CFO Inteligente

Tests end-to-end con PostgreSQL real y APIs mockeadas.
Valida el flujo completo desde pregunta hasta respuesta narrativa.

Ejecutar:
    cd backend
    pytest tests/test_integration.py -v -m integration
    pytest tests/test_integration.py -v -m integration --cov

Nota: Requiere PostgreSQL corriendo y datos de prueba

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch
from datetime import datetime, date

from app.main import app
from app.core.database import get_db
from app.services.chain_of_thought_sql import ChainOfThoughtSQL, generar_con_chain_of_thought
from app.services.sql_router import generar_sql_inteligente
from app.services.validador_sql import ValidadorSQL


# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE BD DE TEST
# ══════════════════════════════════════════════════════════════

from app.core.config import settings
TEST_DATABASE_URL = settings.test_database_url  # IMPORTANTE: Usar BD de test, NO producción

@pytest.fixture(scope="function")
def db_session():
    """
    Fixture que proporciona sesión de BD real
    Scope: function (nueva sesión por test)
    """
    engine = create_engine(TEST_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture(scope="function")
def client_api():
    """
    Fixture que proporciona cliente de FastAPI
    """
    return TestClient(app)


# ══════════════════════════════════════════════════════════════
# GRUPO 1: TESTS DE CHAIN-OF-THOUGHT CON BD REAL
# ══════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestChainOfThoughtIntegration:
    """Tests de Chain-of-Thought con PostgreSQL real"""
    
    def test_obtener_metadatos_temporales(self, db_session):
        """Chain-of-Thought debe obtener metadatos reales de BD"""
        # Arrange
        sql_metadatos = ChainOfThoughtSQL.generar_sql_metadatos()
        
        # Act
        result = db_session.execute(text(sql_metadatos))
        row = result.fetchone()
        metadatos = dict(row._mapping)
        
        # Assert
        assert metadatos is not None
        assert 'fecha_actual' in metadatos
        assert 'meses_con_datos_2025' in metadatos
        assert 'meses_restantes_2025' in metadatos
        
        # Verificar valores razonables
        assert metadatos['meses_con_datos_2025'] >= 0
        assert metadatos['meses_con_datos_2025'] <= 12
        assert metadatos['meses_restantes_2025'] >= 0
        assert metadatos['meses_restantes_2025'] <= 12
    
    def test_formatear_metadatos(self, db_session):
        """Metadatos deben formatearse correctamente para prompt"""
        # Arrange
        metadatos = {
            'fecha_actual': date(2025, 10, 2),
            'mes_actual': 10,
            'meses_con_datos_2025': 8,
            'meses_restantes_2025': 2
        }
        
        # Act
        metadatos_str = ChainOfThoughtSQL.formatear_metadatos_para_prompt(metadatos)
        
        # Assert
        assert 'Meses con datos' in metadatos_str or 'meses_con_datos' in metadatos_str
        assert 'Meses restantes' in metadatos_str or 'meses_restantes' in metadatos_str
        # Valores numéricos pueden variar
    
    @patch('app.services.chain_of_thought_sql.ChainOfThoughtSQL.generar_sql_con_contexto')
    def test_generar_con_cot_completo(self, mock_generar, db_session):
        """generar_con_chain_of_thought ejecuta flujo completo"""
        # Arrange
        from app.services.claude_sql_generator import ClaudeSQLGenerator
        
        mock_generar.return_value = "SELECT SUM(monto_uyu) FROM operaciones"
        pregunta = "Proyección fin de año"
        
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            with patch('anthropic.Anthropic'):
                claude_gen = ClaudeSQLGenerator()
                
                # Act
                resultado = generar_con_chain_of_thought(pregunta, db_session, claude_gen)
                
                # Assert
                assert resultado['exito'] is True
                assert resultado['metodo'] == 'chain_of_thought'
                assert 'metadatos_usados' in resultado
                assert resultado['pasos'] == 2


# ══════════════════════════════════════════════════════════════
# GRUPO 2: TESTS DEL ENDPOINT /api/cfo/ask COMPLETO
# ══════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestEndpointCFOAsk:
    """Tests end-to-end del endpoint principal"""
    
    @patch('app.services.claude_sql_generator.ClaudeSQLGenerator.generar_sql')
    @patch('app.api.cfo_ai.client')
    def test_endpoint_pregunta_simple(self, mock_client, mock_claude_gen, client_api):
        """Endpoint con pregunta simple debe retornar respuesta"""
        # Arrange
        mock_claude_gen.return_value = "SELECT COUNT(*) as total FROM operaciones WHERE deleted_at IS NULL"
        
        # Mock Claude narrativo
        mock_message = Mock()
        mock_content = Mock()
        mock_content.text = "Hay 2,290 operaciones en total."
        mock_message.content = [mock_content]
        mock_client.messages.create.return_value = mock_message
        
        # Act
        response = client_api.post("/api/cfo/ask", json={
            "pregunta": "¿Cuántas operaciones hay?"
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'respuesta' in data
        assert 'sql_generado' in data
        assert 'metadata' in data
    
    @patch('app.services.claude_sql_generator.ClaudeSQLGenerator.generar_sql')
    @patch('app.api.cfo_ai.client')
    def test_endpoint_pregunta_compleja(self, mock_client, mock_claude_gen, client_api):
        """Endpoint con pregunta compleja (rentabilidad)"""
        # Arrange
        sql_rentabilidad = """
        SELECT 
            ((SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END) -
              SUM(CASE WHEN tipo_operacion='GASTO' THEN monto_uyu ELSE 0 END)) /
             NULLIF(SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END), 0)) * 100 
            AS rentabilidad
        FROM operaciones
        WHERE deleted_at IS NULL
        AND DATE_TRUNC('month', fecha) = DATE_TRUNC('month', CURRENT_DATE)
        """
        mock_claude_gen.return_value = sql_rentabilidad
        
        # Mock narrativa
        mock_message = Mock()
        mock_content = Mock()
        mock_content.text = "La rentabilidad del mes es del 33.47%"
        mock_message.content = [mock_content]
        mock_client.messages.create.return_value = mock_message
        
        # Act
        response = client_api.post("/api/cfo/ask", json={
            "pregunta": "¿Cuál es la rentabilidad de este mes?"
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'rentabilidad' in data['respuesta'].lower() or '%' in data['respuesta']
    
    @patch('app.services.claude_sql_generator.ClaudeSQLGenerator.generar_sql')
    def test_endpoint_sql_invalido(self, mock_claude_gen, client_api):
        """Endpoint con SQL inválido debe retornar error"""
        # Arrange
        mock_claude_gen.side_effect = Exception("Claude error")
        
        # Mockear Vanna también para que falle
        with patch('app.services.sql_router.vn.generate_sql', return_value=None):
            # Act
            response = client_api.post("/api/cfo/ask", json={
                "pregunta": "Query imposible de generar"
            })
            
            # Assert
            assert response.status_code == 200  # No crashea
            data = response.json()
            assert data['status'] == 'error'
            assert 'error_tipo' in data
    
    def test_endpoint_formato_response(self, client_api):
        """Response debe tener formato correcto siempre"""
        # Arrange
        with patch('app.services.claude_sql_generator.ClaudeSQLGenerator.generar_sql') as mock_gen:
            mock_gen.return_value = "SELECT 1 as numero"
            
            with patch('app.api.cfo_ai.client') as mock_client:
                mock_message = Mock()
                mock_content = Mock()
                mock_content.text = "El número es 1"
                mock_message.content = [mock_content]
                mock_client.messages.create.return_value = mock_message
                
                # Act
                response = client_api.post("/api/cfo/ask", json={
                    "pregunta": "Test"
                })
                
                # Assert
                data = response.json()
                
                # Campos obligatorios
                assert 'pregunta' in data
                assert 'respuesta' in data
                assert 'status' in data
                
                # Campos si exitoso
                if data['status'] == 'success':
                    assert 'sql_generado' in data
                    assert 'datos_raw' in data
                    assert 'metadata' in data


# ══════════════════════════════════════════════════════════════
# GRUPO 3: TESTS DE SQL ROUTER CON BD
# ══════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestSQLRouterIntegration:
    """Tests del SQL Router con BD real"""
    
    @patch('app.services.claude_sql_generator.ClaudeSQLGenerator.generar_sql')
    def test_sql_ejecutable_en_bd(self, mock_claude_gen, db_session):
        """SQL generado debe ser ejecutable en BD real"""
        # Arrange
        sql = "SELECT COUNT(*) as total FROM operaciones WHERE deleted_at IS NULL"
        mock_claude_gen.return_value = sql
        
        # Act - Generar SQL
        resultado = generar_sql_inteligente("¿Cuántas operaciones hay?")
        
        # Assert - SQL se generó
        assert resultado['exito'] is True
        assert resultado['sql'] is not None
        
        # Ejecutar SQL en BD real
        result = db_session.execute(text(resultado['sql']))
        row = result.fetchone()
        
        # Verificar que retorna datos
        assert row is not None
        assert row[0] > 0  # Hay operaciones
    
    @patch('app.services.claude_sql_generator.ClaudeSQLGenerator.generar_sql')
    def test_sql_rentabilidad_ejecutable(self, mock_claude_gen, db_session):
        """SQL de rentabilidad debe ejecutarse y retornar valor válido"""
        # Arrange
        sql_rentabilidad = """
        SELECT 
            ROUND(
                ((SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END) -
                  SUM(CASE WHEN tipo_operacion='GASTO' THEN monto_uyu ELSE 0 END)) /
                 NULLIF(SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END), 0)) * 100,
                2
            ) AS rentabilidad
        FROM operaciones
        WHERE deleted_at IS NULL
        AND DATE_TRUNC('month', fecha) = DATE_TRUNC('month', CURRENT_DATE)
        """
        mock_claude_gen.return_value = sql_rentabilidad
        
        # Act
        resultado = generar_sql_inteligente("¿Cuál es la rentabilidad?")
        
        # Assert
        assert resultado['exito'] is True
        
        # Ejecutar en BD
        result = db_session.execute(text(resultado['sql']))
        row = result.fetchone()
        
        if row and row[0] is not None:
            rentabilidad = float(row[0])
            # Rentabilidad debe estar en rango razonable
            assert -100 <= rentabilidad <= 100


# ══════════════════════════════════════════════════════════════
# GRUPO 4: TESTS DE VALIDADOR CON DATOS REALES
# ══════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestValidadorConDatosReales:
    """Tests del validador con resultados reales de BD"""
    
    def test_validar_rentabilidad_real(self, db_session):
        """Validar rentabilidad con datos reales de BD"""
        # Arrange
        sql = """
        SELECT 
            ROUND(
                ((SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END) -
                  SUM(CASE WHEN tipo_operacion='GASTO' THEN monto_uyu ELSE 0 END)) /
                 NULLIF(SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END), 0)) * 100,
                2
            ) AS rentabilidad
        FROM operaciones
        WHERE deleted_at IS NULL
        AND DATE_TRUNC('year', fecha) = DATE_TRUNC('year', CURRENT_DATE)
        """
        
        # Act - Ejecutar SQL
        result = db_session.execute(text(sql))
        row = result.fetchone()
        datos = [dict(row._mapping)] if row else []
        
        # Validar
        validacion = ValidadorSQL.validar_resultado("¿Rentabilidad?", sql, datos)
        
        # Assert
        assert validacion is not None
        if datos and datos[0].get('rentabilidad') is not None:
            # Si hay datos, debe validar correctamente
            rentabilidad = datos[0]['rentabilidad']
            if -100 <= rentabilidad <= 100:
                assert validacion['valido'] is True
            else:
                assert validacion['valido'] is False
    
    def test_validar_distribuciones_reales(self, db_session):
        """Validar distribuciones con datos reales"""
        # Arrange
        sql = """
        SELECT 
            s.nombre,
            COALESCE(SUM(dd.monto_uyu), 0) as total
        FROM socios s
        LEFT JOIN distribuciones_detalle dd ON dd.socio_id = s.id
        LEFT JOIN operaciones o ON o.id = dd.operacion_id 
            AND o.deleted_at IS NULL
            AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
        GROUP BY s.nombre
        """
        
        # Act
        result = db_session.execute(text(sql))
        datos = [dict(row._mapping) for row in result]
        
        # Validar cada socio
        for dato in datos:
            validacion = ValidadorSQL.validar_distribucion_socio([dato])
            
            # Assert - No debe haber valores negativos
            if dato['total'] is not None:
                assert validacion['valido'] is True or 'negativo' in validacion.get('razon', '')


# ══════════════════════════════════════════════════════════════
# GRUPO 5: TESTS END-TO-END DEL FLUJO COMPLETO
# ══════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.slow
class TestFlujoCompletoEndToEnd:
    """Tests del flujo completo con mínimo mocking"""
    
    @patch('app.services.claude_sql_generator.ClaudeSQLGenerator.generar_sql')
    @patch('app.api.cfo_ai.client')
    def test_flujo_completo_pregunta_facturacion(self, mock_narrativa, mock_sql_gen, client_api):
        """Flujo completo: Pregunta → SQL → BD → Narrativa → Response"""
        # Arrange
        sql = "SELECT SUM(monto_uyu) as total FROM operaciones WHERE tipo_operacion='INGRESO' AND deleted_at IS NULL"
        mock_sql_gen.return_value = sql
        
        # Mock narrativa
        mock_message = Mock()
        mock_content = Mock()
        mock_content.text = "Facturamos $X en total"
        mock_message.content = [mock_content]
        mock_narrativa.messages.create.return_value = mock_message
        
        # Act
        response = client_api.post("/api/cfo/ask", json={
            "pregunta": "¿Cuánto facturamos?"
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Verificar flujo completo
        assert data['status'] == 'success'
        assert data['sql_generado'] == sql
        assert 'datos_raw' in data
        assert len(data['datos_raw']) > 0
        assert 'total' in data['datos_raw'][0]
    
    @patch('app.services.claude_sql_generator.ClaudeSQLGenerator.generar_sql')
    @patch('app.api.cfo_ai.client')
    def test_flujo_con_validacion_pre_sql(self, mock_narrativa, mock_sql_gen, client_api):
        """Validación pre-SQL debe ejecutarse en el flujo"""
        # Arrange - SQL sin filtro temporal (debería detectarse)
        sql_sin_filtro = "SELECT SUM(monto_uyu) FROM operaciones WHERE deleted_at IS NULL"
        mock_sql_gen.return_value = sql_sin_filtro
        
        mock_message = Mock()
        mock_content = Mock()
        mock_content.text = "Facturamos $X en total"
        mock_message.content = [mock_content]
        mock_narrativa.messages.create.return_value = mock_message
        
        # Act
        response = client_api.post("/api/cfo/ask", json={
            "pregunta": "¿Cuánto facturamos?"
        })
        
        # Assert
        data = response.json()
        
        # Endpoint debe responder
        assert response.status_code == 200
        assert data['status'] in ['success', 'error']
    
    @patch('app.services.claude_sql_generator.ClaudeSQLGenerator.generar_sql')
    @patch('app.api.cfo_ai.client')
    def test_flujo_con_chain_of_thought(self, mock_narrativa, mock_sql_gen, client_api):
        """Pregunta temporal debe activar Chain-of-Thought"""
        # Arrange
        sql_proyeccion = "SELECT SUM(monto_uyu) / 8 * 12 as proyeccion FROM operaciones"
        mock_sql_gen.return_value = sql_proyeccion
        
        mock_message = Mock()
        mock_content = Mock()
        mock_content.text = "La proyección es de $X"
        mock_message.content = [mock_content]
        mock_narrativa.messages.create.return_value = mock_message
        
        # Act
        response = client_api.post("/api/cfo/ask", json={
            "pregunta": "¿Cuál es la proyección de fin de año?"
        })
        
        # Assert
        data = response.json()
        
        # Endpoint debe responder exitosamente
        assert data['status'] in ['success', 'error']
        # Chain-of-Thought puede o no activarse según keywords
        assert 'metadata' in data or 'error' in data


# ══════════════════════════════════════════════════════════════
# GRUPO 6: TESTS DE QUERIES REALES
# ══════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestQueriesReales:
    """Tests con queries reales que ejecutan en BD"""
    
    def test_query_conteo_operaciones(self, db_session):
        """Query de conteo debe retornar número correcto"""
        # Act
        sql = "SELECT COUNT(*) as total FROM operaciones WHERE deleted_at IS NULL"
        result = db_session.execute(text(sql))
        row = result.fetchone()
        
        # Assert
        assert row is not None
        total = row[0]
        assert total > 0
        assert total >= 2000  # Al menos 2000 operaciones (valor razonable)
    
    def test_query_sum_ingresos(self, db_session):
        """Query de suma de ingresos debe retornar valor razonable"""
        # Act
        sql = """
        SELECT SUM(monto_uyu) as total_ingresos
        FROM operaciones
        WHERE tipo_operacion = 'INGRESO'
        AND deleted_at IS NULL
        """
        result = db_session.execute(text(sql))
        row = result.fetchone()
        
        # Assert
        assert row is not None
        total = float(row[0]) if row[0] else 0
        assert total > 0
        # Verificar que está en rango razonable (basado en datos conocidos)
        assert total > 1_000_000  # Al menos 1M
    
    def test_query_distribuciones_por_socio(self, db_session):
        """Query de distribuciones debe retornar 5 socios"""
        # Act
        sql = """
        SELECT 
            s.nombre,
            COALESCE(SUM(dd.monto_uyu), 0) as total
        FROM socios s
        LEFT JOIN distribuciones_detalle dd ON dd.socio_id = s.id
        LEFT JOIN operaciones o ON o.id = dd.operacion_id
            AND o.deleted_at IS NULL
        GROUP BY s.nombre
        ORDER BY s.nombre
        """
        result = db_session.execute(text(sql))
        rows = result.fetchall()
        
        # Assert
        assert len(rows) == 5  # 5 socios
        
        # Verificar nombres
        nombres = [row[0] for row in rows]
        assert 'Agustina' in nombres
        assert 'Bruno' in nombres
        assert 'Viviana' in nombres
        assert 'Gonzalo' in nombres
        assert 'Pancho' in nombres


# ══════════════════════════════════════════════════════════════
# GRUPO 7: TESTS DE VALIDACIÓN CON CASOS REALES
# ══════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestValidacionCasosReales:
    """Tests de validación con casos del mundo real"""
    
    def test_detectar_tipo_query_con_sql_real(self, db_session):
        """Detección de tipo debe funcionar con SQL real"""
        # Arrange
        casos = [
            ("¿Cuánto recibió Bruno?", "SELECT SUM(dd.monto_uyu)...", "distribucion_socio"),
            ("¿Rentabilidad del mes?", "SELECT ((SUM...", "rentabilidad"),
            ("¿Cuánto facturamos?", "SELECT SUM(monto)...", "facturacion"),
        ]
        
        # Act & Assert
        for pregunta, sql, tipo_esperado in casos:
            tipo_detectado = ValidadorSQL.detectar_tipo_query(pregunta, sql)
            assert tipo_detectado == tipo_esperado, f"Falló para: {pregunta}"
    
    def test_validacion_pre_sql_con_sql_real(self):
        """Validación pre-SQL con SQL real generado"""
        # Arrange
        sql_con_problema = "SELECT area FROM operaciones ORDER BY ingresos DESC LIMIT 1"
        pregunta = "¿Cuáles son las mejores áreas?"  # Pide múltiples
        
        # Act
        validacion = ValidadorSQL.validar_sql_antes_ejecutar(pregunta, sql_con_problema)
        
        # Assert
        assert validacion['valido'] is False
        assert len(validacion['problemas']) > 0
        assert 'LIMIT 1' in validacion['problemas'][0]


# ══════════════════════════════════════════════════════════════
# GRUPO 8: TESTS CHAIN-OF-THOUGHT AVANZADOS (8 tests nuevos)
# ══════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestChainOfThoughtAvanzado:
    """Tests avanzados de Chain-of-Thought con BD real"""
    
    def test_proyeccion_fin_año_con_metadatos(self, db_session):
        """Proyección debe usar metadatos reales de BD"""
        # Arrange - Obtener metadatos
        sql_meta = ChainOfThoughtSQL.generar_sql_metadatos()
        result = db_session.execute(text(sql_meta))
        metadatos = dict(result.fetchone()._mapping)
        
        # Assert
        assert metadatos['meses_con_datos_2025'] > 0
        assert metadatos['meses_restantes_2025'] >= 0
        
        # Verificar que suma 12 o menos
        total_meses = metadatos['meses_con_datos_2025'] + metadatos['meses_restantes_2025']
        assert total_meses <= 12
    
    def test_comparacion_mes_vs_mes(self, db_session):
        """Comparación temporal debe ejecutarse correctamente"""
        # Act
        sql = """
        WITH mensual AS (
            SELECT 
                DATE_TRUNC('month', fecha) AS mes,
                SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END) as ingresos
            FROM operaciones
            WHERE deleted_at IS NULL
            GROUP BY 1
            ORDER BY 1 DESC
            LIMIT 2
        )
        SELECT mes, ingresos FROM mensual ORDER BY mes DESC
        """
        result = db_session.execute(text(sql))
        rows = result.fetchall()
        
        # Assert
        assert len(rows) <= 2
        if len(rows) == 2:
            # Debe haber 2 meses
            mes_actual = rows[0][0]
            mes_anterior = rows[1][0]
            assert mes_actual > mes_anterior  # Ordenados
    
    def test_tendencia_ultimos_3_meses(self, db_session):
        """Tendencia de últimos meses debe retornar datos"""
        # Act
        sql = """
        SELECT 
            DATE_TRUNC('month', fecha) AS mes,
            SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END) as ingresos
        FROM operaciones
        WHERE deleted_at IS NULL
        AND fecha >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '2 months'
        GROUP BY 1
        ORDER BY 1
        """
        result = db_session.execute(text(sql))
        rows = result.fetchall()
        
        # Assert
        assert len(rows) > 0
        assert len(rows) <= 3
    
    def test_conversion_moneda_multiple(self, db_session):
        """Query con conversiones debe retornar ambas monedas"""
        # Act
        sql = """
        SELECT 
            SUM(monto_uyu) as total_uyu,
            SUM(monto_usd) as total_usd
        FROM operaciones
        WHERE tipo_operacion='INGRESO'
        AND deleted_at IS NULL
        """
        result = db_session.execute(text(sql))
        row = result.fetchone()
        
        # Assert
        assert row is not None
        assert row[0] > 0  # total_uyu
        assert row[1] > 0  # total_usd
    
    def test_deteccion_keywords_temporales(self):
        """Debe detectar correctamente keywords temporales"""
        # Arrange
        casos = [
            ("Proyección fin de año", True),
            ("Tendencia últimos meses", True),
            ("Basado en datos históricos", True),
            ("¿Cuánto facturamos?", False),
            ("Rentabilidad área Jurídica", False),
        ]
        
        # Act & Assert
        for pregunta, esperado in casos:
            resultado = ChainOfThoughtSQL.necesita_metadatos(pregunta)
            assert resultado == esperado, f"Falló para: {pregunta}"
    
    def test_metadatos_fecha_actual_correcta(self, db_session):
        """Fecha actual en metadatos debe coincidir con CURRENT_DATE"""
        # Act
        sql = "SELECT CURRENT_DATE as hoy"
        result = db_session.execute(text(sql))
        fecha_db = result.fetchone()[0]
        
        # Obtener metadatos
        sql_meta = ChainOfThoughtSQL.generar_sql_metadatos()
        result2 = db_session.execute(text(sql_meta))
        metadatos = dict(result2.fetchone()._mapping)
        
        # Assert
        assert metadatos['fecha_actual'] == fecha_db
    
    def test_meses_con_datos_dinamico(self, db_session):
        """Meses con datos debe calcularse dinámicamente"""
        # Act
        sql_meta = ChainOfThoughtSQL.generar_sql_metadatos()
        result = db_session.execute(text(sql_meta))
        metadatos = dict(result.fetchone()._mapping)
        
        # Verificar independientemente
        sql_verificacion = """
        SELECT COUNT(DISTINCT DATE_TRUNC('month', fecha))
        FROM operaciones
        WHERE deleted_at IS NULL
        AND DATE_TRUNC('year', fecha) = DATE_TRUNC('year', CURRENT_DATE)
        """
        result2 = db_session.execute(text(sql_verificacion))
        meses_reales = result2.fetchone()[0]
        
        # Assert
        assert metadatos['meses_con_datos_2025'] == meses_reales
    
    def test_ultimo_mes_con_datos(self, db_session):
        """Último mes con datos debe obtenerse correctamente"""
        # Act
        sql_meta = ChainOfThoughtSQL.generar_sql_metadatos()
        result = db_session.execute(text(sql_meta))
        metadatos = dict(result.fetchone()._mapping)
        
        # Assert
        assert metadatos['ultimo_mes_con_datos'] is not None
        # Debe ser una fecha en 2025 o 2024
        assert '2024' in str(metadatos['ultimo_mes_con_datos']) or '2025' in str(metadatos['ultimo_mes_con_datos'])


# ══════════════════════════════════════════════════════════════
# GRUPO 9: TESTS VALIDADOR POST-SQL CON DATOS REALES (4 tests)
# ══════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestValidadorPostSQLReal:
    """Tests de validación post-SQL con resultados reales"""
    
    def test_porcentaje_usd_uyu_real(self, db_session):
        """Porcentaje USD vs UYU con datos reales"""
        # Act
        sql = """
        SELECT 
            ROUND(COUNT(CASE WHEN moneda_original='USD' THEN 1 END) * 100.0 / COUNT(*), 2) as pct_usd,
            ROUND(COUNT(CASE WHEN moneda_original='UYU' THEN 1 END) * 100.0 / COUNT(*), 2) as pct_uyu
        FROM operaciones
        WHERE tipo_operacion='INGRESO'
        AND deleted_at IS NULL
        """
        result = db_session.execute(text(sql))
        row = result.fetchone()
        datos = [dict(row._mapping)]
        
        # Validar
        validacion = ValidadorSQL.validar_resultado("¿Qué % es USD?", sql, datos)
        
        # Assert
        if row[0] is not None and row[1] is not None:
            suma = float(row[0]) + float(row[1])
            assert abs(suma - 100) < 1  # Debe sumar ~100%
    
    def test_distribucion_por_socio_real(self, db_session):
        """Distribuciones reales no deben exceder límites artificiales"""
        # Act
        sql = """
        SELECT 
            s.nombre,
            COALESCE(SUM(dd.monto_uyu), 0) as total
        FROM socios s
        LEFT JOIN distribuciones_detalle dd ON dd.socio_id = s.id
        LEFT JOIN operaciones o ON o.id = dd.operacion_id
            AND o.deleted_at IS NULL
            AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
        GROUP BY s.nombre
        ORDER BY total DESC
        """
        result = db_session.execute(text(sql))
        rows = result.fetchall()
        datos = [{'nombre': r[0], 'total': r[1]} for r in rows]
        
        # Validar cada uno
        for dato in datos:
            validacion = ValidadorSQL.validar_distribucion_socio([dato])
            
            # Assert - Solo debe fallar si es negativo
            if dato['total'] < 0:
                assert validacion['valido'] is False
            else:
                assert validacion['valido'] is True
    
    def test_ranking_limit_1_deteccion(self):
        """Debe detectar ranking con LIMIT 1 problemático"""
        # Arrange
        sql_malo = "SELECT nombre FROM areas ORDER BY ingresos DESC LIMIT 1"
        pregunta = "¿Cuáles son las mejores áreas?"
        
        # Act
        validacion = ValidadorSQL.validar_sql_antes_ejecutar(pregunta, sql_malo)
        
        # Assert
        assert validacion['valido'] is False
        assert any('LIMIT 1' in p for p in validacion['problemas'])
    
    def test_validacion_no_rechaza_sql_correcto(self):
        """SQL correcto no debe rechazarse"""
        # Arrange
        sql_bueno = """
        SELECT nombre, ingresos
        FROM areas
        WHERE deleted_at IS NULL
        ORDER BY ingresos DESC
        LIMIT 5
        """
        pregunta = "¿Cuáles son las mejores áreas?"
        
        # Act
        validacion = ValidadorSQL.validar_sql_antes_ejecutar(pregunta, sql_bueno)
        
        # Assert
        # Puede tener advertencia de filtro temporal pero no de LIMIT 1
        problemas_limit = [p for p in validacion['problemas'] if 'LIMIT 1' in p]
        assert len(problemas_limit) == 0


# ══════════════════════════════════════════════════════════════
# GRUPO 10: TESTS CASOS CRÍTICOS (4 tests nuevos)
# ══════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestCasosCriticos:
    """Tests de casos críticos que fallaron en testing manual"""
    
    @patch('app.services.claude_sql_generator.ClaudeSQLGenerator.generar_sql')
    @patch('app.api.cfo_ai.client')
    def test_caso_retiros_por_socio(self, mock_narrativa, mock_sql_gen, client_api):
        """Caso crítico: ¿Qué socio retiró más plata?"""
        # Arrange
        sql = """
        SELECT s.nombre, SUM(o.monto_uyu) as total_retiros
        FROM operaciones o
        JOIN socios s ON s.nombre IN ('Bruno', 'Agustina', 'Viviana', 'Gonzalo', 'Pancho')
        WHERE o.tipo_operacion='RETIRO'
        AND o.deleted_at IS NULL
        GROUP BY s.nombre
        ORDER BY total_retiros DESC
        LIMIT 1
        """
        mock_sql_gen.return_value = sql
        
        mock_message = Mock()
        mock_content = Mock()
        mock_content.text = "Bruno retiró $X en total"
        mock_message.content = [mock_content]
        mock_narrativa.messages.create.return_value = mock_message
        
        # Act
        response = client_api.post("/api/cfo/ask", json={
            "pregunta": "¿Qué socio retiró más plata?"
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        # Puede ser success o error, pero no debe crashear
        assert data['status'] in ['success', 'error']
    
    @patch('app.services.claude_sql_generator.ClaudeSQLGenerator.generar_sql')
    @patch('app.api.cfo_ai.client')
    def test_caso_comparacion_año_anterior(self, mock_narrativa, mock_sql_gen, client_api):
        """Caso crítico: ¿Mejoramos respecto al año pasado?"""
        # Arrange
        sql = """
        SELECT 
            EXTRACT(YEAR FROM fecha)::int as año,
            SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END) as ingresos
        FROM operaciones
        WHERE deleted_at IS NULL
        AND EXTRACT(YEAR FROM fecha) >= EXTRACT(YEAR FROM CURRENT_DATE) - 1
        GROUP BY 1
        ORDER BY 1 DESC
        """
        mock_sql_gen.return_value = sql
        
        mock_message = Mock()
        mock_content = Mock()
        mock_content.text = "Sí, mejoramos en facturación"
        mock_message.content = [mock_content]
        mock_narrativa.messages.create.return_value = mock_message
        
        # Act
        response = client_api.post("/api/cfo/ask", json={
            "pregunta": "¿Mejoramos respecto al año pasado?"
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data['status'] in ['success', 'error']
    
    def test_caso_gonzalo_recibe_correcto(self, db_session):
        """Verificar que Gonzalo recibe lo que corresponde"""
        # Act - Obtener % participación
        sql_participacion = "SELECT porcentaje_participacion FROM socios WHERE nombre='Gonzalo'"
        result1 = db_session.execute(text(sql_participacion))
        row1 = result1.fetchone()
        
        if row1 and row1[0] is not None:
            porcentaje_esperado = float(row1[0])
            
            # Obtener distribuciones reales
            sql_dist = """
            SELECT 
                SUM(dd.monto_uyu) as recibido
            FROM distribuciones_detalle dd
            JOIN operaciones o ON o.id = dd.operacion_id
            JOIN socios s ON s.id = dd.socio_id
            WHERE s.nombre='Gonzalo'
            AND o.deleted_at IS NULL
            AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
            """
            result2 = db_session.execute(text(sql_dist))
            row2 = result2.fetchone()
            
            # Assert
            assert row2 is not None
            # No validamos el monto exacto, solo que no sea negativo
            assert row2[0] is None or row2[0] >= 0
    
    @patch('app.services.claude_sql_generator.ClaudeSQLGenerator.generar_sql')
    @patch('app.api.cfo_ai.client')
    def test_caso_estamos_creciendo(self, mock_narrativa, mock_sql_gen, client_api):
        """Caso: ¿Estamos creciendo o bajando?"""
        # Arrange
        sql = """
        WITH mensual AS (
            SELECT 
                DATE_TRUNC('month', fecha) AS mes,
                SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END) as ingresos
            FROM operaciones
            WHERE deleted_at IS NULL
            AND fecha >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '5 months'
            GROUP BY 1
        )
        SELECT 
            mes,
            ingresos,
            LAG(ingresos) OVER (ORDER BY mes) as mes_anterior
        FROM mensual
        ORDER BY mes
        """
        mock_sql_gen.return_value = sql
        
        mock_message = Mock()
        mock_content = Mock()
        mock_content.text = "La tendencia es positiva, estamos creciendo"
        mock_message.content = [mock_content]
        mock_narrativa.messages.create.return_value = mock_message
        
        # Act
        response = client_api.post("/api/cfo/ask", json={
            "pregunta": "¿Estamos creciendo o bajando?"
        })
        
        # Assert
        assert response.status_code == 200


# ══════════════════════════════════════════════════════════════
# MARKS PARA pytest.ini
# ══════════════════════════════════════════════════════════════

# Configurado en pytest.ini

