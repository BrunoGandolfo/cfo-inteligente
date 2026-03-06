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
from sqlalchemy import text
from unittest.mock import Mock, patch

from app.main import app
from app.core.database import get_db
from app.services.sql_router import generar_sql_inteligente
from app.services.validador_sql import ValidadorSQL


# SQLs válidos para el pipeline actual (evitan rechazo de validación pre-SQL)
SQL_VALIDO_CONTEO = """
SELECT COUNT(*) as total
FROM operaciones
WHERE deleted_at IS NULL
  AND DATE_TRUNC('year', fecha) = DATE_TRUNC('year', CURRENT_DATE)
"""

SQL_VALIDO_FACTURACION = """
SELECT SUM(monto_uyu) as total
FROM operaciones
WHERE tipo_operacion = 'INGRESO'
  AND deleted_at IS NULL
  AND DATE_TRUNC('year', fecha) = DATE_TRUNC('year', CURRENT_DATE)
"""

SQL_VALIDO_RENTABILIDAD = """
SELECT
    ROUND(
        (
            (SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END) -
             SUM(CASE WHEN tipo_operacion='GASTO' THEN monto_uyu ELSE 0 END))
            / NULLIF(SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END), 0)
        ) * 100,
        2
    ) AS rentabilidad
FROM operaciones
WHERE deleted_at IS NULL
  AND DATE_TRUNC('year', fecha) = DATE_TRUNC('year', CURRENT_DATE)
"""


# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE BD DE TEST
# ══════════════════════════════════════════════════════════════

@pytest.fixture(scope="function")
def client_api(usuario_test, db_session):
    """
    Fixture que proporciona cliente de FastAPI con autenticación y BD mockeadas
    """
    from app.core.security import get_current_user
    from app.core.database import get_db
    
    app.dependency_overrides[get_current_user] = lambda: usuario_test
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()


# ══════════════════════════════════════════════════════════════
# GRUPO 3: TESTS DE SQL ROUTER CON BD
# ══════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestSQLRouterIntegration:
    """Tests del SQL Router con BD real"""
    
    @patch('app.services.claude_sql_generator.ClaudeSQLGenerator.generar_sql')
    def test_sql_ejecutable_en_bd(self, mock_claude_gen, db_session, operaciones_test):
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
# GRUPO 6: TESTS DE QUERIES REALES
# ══════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestQueriesReales:
    """Tests con queries reales que ejecutan en BD"""
    
    def test_query_conteo_operaciones(self, db_session, operaciones_test):
        """Query de conteo debe retornar número correcto"""
        # Act
        sql = "SELECT COUNT(*) as total FROM operaciones WHERE deleted_at IS NULL"
        result = db_session.execute(text(sql))
        row = result.fetchone()
        
        # Assert
        assert row is not None
        total = row[0]
        assert total > 0  # Al menos hay operaciones en la BD
    
    def test_query_sum_ingresos(self, db_session, operaciones_test):
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
        assert total > 500_000  # Al menos 500K (ajustado para datos de prueba)
    
    def test_query_distribuciones_por_socio(self, db_session, operaciones_test):
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
# GRUPO 9: TESTS VALIDADOR POST-SQL CON DATOS REALES (4 tests)
# ══════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestValidadorPostSQLReal:
    """Tests de validación post-SQL con resultados reales"""
    
    def test_porcentaje_usd_uyu_real(self, db_session, operaciones_test):
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
# MARKS PARA pytest.ini
# ══════════════════════════════════════════════════════════════

# Configurado en pytest.ini
