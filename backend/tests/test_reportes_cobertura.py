"""
Tests de cobertura exhaustiva para reportes.py
Objetivo: Llevar cobertura de 22% a 60%+

Endpoints cubiertos:
1. GET /resumen-mensual
2. GET /por-area
3. GET /rentabilidad
4. GET /operaciones-grafico
"""
import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date
from uuid import uuid4
import os

from app.main import app
from app.core.config import settings

# URL de BD de test
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    settings.database_url.replace('/cfo_inteligente', '/cfo_test')
)


# ══════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════

@pytest.fixture(scope="function")
def db_session():
    """Fixture que proporciona sesión de BD real"""
    engine = create_engine(TEST_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="function")
def mock_user(db_session):
    """Usuario real de la BD para autenticación"""
    from app.models import Usuario
    
    usuario = db_session.query(Usuario).first()
    if usuario:
        return usuario
    else:
        user = Mock()
        user.id = uuid4()
        user.email = "test@conexion.uy"
        user.es_socio = True
        return user


@pytest.fixture(scope="function")
def client_api(mock_user, db_session):
    """Cliente de FastAPI con autenticación"""
    from app.core.security import get_current_user
    from app.core.database import get_db
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()


# ══════════════════════════════════════════════════════════════
# TESTS DE FUNCIÓN HELPER
# ══════════════════════════════════════════════════════════════

class TestCalcularRangoMes:
    """Tests de la función _calcular_rango_mes"""
    
    def test_calcular_rango_enero(self):
        """Enero 2025 debe ir del 1 al 31"""
        from app.api.reportes import _calcular_rango_mes
        
        inicio, fin = _calcular_rango_mes(1, 2025)
        
        assert inicio == date(2025, 1, 1)
        assert fin == date(2025, 1, 31)
    
    def test_calcular_rango_febrero_bisiesto(self):
        """Febrero 2024 (bisiesto) debe ir del 1 al 29"""
        from app.api.reportes import _calcular_rango_mes
        
        inicio, fin = _calcular_rango_mes(2, 2024)
        
        assert inicio == date(2024, 2, 1)
        assert fin == date(2024, 2, 29)
    
    def test_calcular_rango_febrero_no_bisiesto(self):
        """Febrero 2025 (no bisiesto) debe ir del 1 al 28"""
        from app.api.reportes import _calcular_rango_mes
        
        inicio, fin = _calcular_rango_mes(2, 2025)
        
        assert inicio == date(2025, 2, 1)
        assert fin == date(2025, 2, 28)
    
    def test_calcular_rango_diciembre(self):
        """Diciembre 2025 debe ir del 1 al 31 (fin de año)"""
        from app.api.reportes import _calcular_rango_mes
        
        inicio, fin = _calcular_rango_mes(12, 2025)
        
        assert inicio == date(2025, 12, 1)
        assert fin == date(2025, 12, 31)
    
    def test_calcular_rango_abril(self):
        """Abril 2025 debe ir del 1 al 30 (mes de 30 días)"""
        from app.api.reportes import _calcular_rango_mes
        
        inicio, fin = _calcular_rango_mes(4, 2025)
        
        assert inicio == date(2025, 4, 1)
        assert fin == date(2025, 4, 30)


# ══════════════════════════════════════════════════════════════
# TESTS DE GET /resumen-mensual
# ══════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestResumenMensual:
    """Tests del endpoint /resumen-mensual"""
    
    def test_resumen_mensual_mes_actual(self, client_api):
        """Resumen sin parámetros debe usar mes actual"""
        response = client_api.get("/api/reportes/resumen-mensual")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura de respuesta
        assert "periodo" in data
        assert "cantidad_operaciones" in data
        assert "ingresos" in data
        assert "gastos" in data
        assert "rentabilidad" in data
        
        # Ingresos y gastos deben tener uyu y usd
        assert "uyu" in data["ingresos"]
        assert "usd" in data["ingresos"]
    
    def test_resumen_mensual_mes_especifico(self, client_api):
        """Resumen con mes/año específico"""
        response = client_api.get("/api/reportes/resumen-mensual?mes=10&anio=2025")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["periodo"] == "10/2025"
    
    def test_resumen_mensual_diciembre(self, client_api):
        """Diciembre es edge case (fin de año)"""
        response = client_api.get("/api/reportes/resumen-mensual?mes=12&anio=2024")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["periodo"] == "12/2024"
    
    def test_resumen_mensual_formato_numeros(self, client_api):
        """Los montos deben ser números (float)"""
        response = client_api.get("/api/reportes/resumen-mensual?mes=10&anio=2025")
        
        data = response.json()
        
        assert isinstance(data["ingresos"]["uyu"], (int, float))
        assert isinstance(data["ingresos"]["usd"], (int, float))
        assert isinstance(data["rentabilidad"]["uyu"], (int, float))


# ══════════════════════════════════════════════════════════════
# TESTS DE GET /por-area
# ══════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestReportePorArea:
    """Tests del endpoint /por-area"""
    
    def test_por_area_mes_actual(self, client_api):
        """Reporte por área sin parámetros usa mes actual"""
        response = client_api.get("/api/reportes/por-area")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "periodo" in data
        assert "areas" in data
        assert isinstance(data["areas"], list)
    
    def test_por_area_mes_especifico(self, client_api):
        """Reporte por área con mes específico"""
        response = client_api.get("/api/reportes/por-area?mes=10&anio=2025")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["periodo"] == "10/2025"
    
    def test_por_area_estructura_area(self, client_api):
        """Cada área debe tener estructura correcta"""
        response = client_api.get("/api/reportes/por-area?mes=10&anio=2025")
        
        data = response.json()
        
        if data["areas"]:  # Si hay áreas
            area = data["areas"][0]
            assert "area" in area
            assert "cantidad_operaciones" in area
            assert "ingresos_uyu" in area
            assert "gastos_uyu" in area
            assert "balance_uyu" in area


# ══════════════════════════════════════════════════════════════
# TESTS DE GET /rentabilidad
# ══════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestRentabilidad:
    """Tests del endpoint /rentabilidad"""
    
    def test_rentabilidad_mes_actual(self, client_api):
        """Rentabilidad sin parámetros usa mes actual"""
        response = client_api.get("/api/reportes/rentabilidad")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "periodo" in data
        assert "margen_operativo_porcentaje" in data
        assert "margen_neto_porcentaje" in data
    
    def test_rentabilidad_mes_especifico(self, client_api):
        """Rentabilidad con mes específico"""
        response = client_api.get("/api/reportes/rentabilidad?mes=10&anio=2025")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["periodo"] == "10/2025"
    
    def test_rentabilidad_estructura_completa(self, client_api):
        """Verificar todos los campos de rentabilidad"""
        response = client_api.get("/api/reportes/rentabilidad?mes=10&anio=2025")
        
        data = response.json()
        
        campos_requeridos = [
            "periodo", "ingresos_uyu", "gastos_uyu", 
            "retiros_uyu", "distribuciones_uyu",
            "resultado_operativo", "resultado_neto",
            "margen_operativo_porcentaje", "margen_neto_porcentaje"
        ]
        
        for campo in campos_requeridos:
            assert campo in data, f"Falta campo: {campo}"
    
    def test_rentabilidad_porcentajes_correctos(self, client_api):
        """Porcentajes deben ser números razonables"""
        response = client_api.get("/api/reportes/rentabilidad?mes=10&anio=2025")
        
        data = response.json()
        
        # Margen operativo puede ser negativo pero no extremo
        assert -1000 < data["margen_operativo_porcentaje"] < 1000
        assert -1000 < data["margen_neto_porcentaje"] < 1000


# ══════════════════════════════════════════════════════════════
# TESTS DE GET /operaciones-grafico
# ══════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestOperacionesGrafico:
    """Tests del endpoint /operaciones-grafico"""
    
    def test_operaciones_grafico_basico(self, client_api):
        """Endpoint básico con fechas requeridas"""
        response = client_api.get(
            "/api/reportes/operaciones-grafico"
            "?fecha_desde=2025-01-01&fecha_hasta=2025-12-31"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "operaciones" in data
        assert "cantidad" in data
        assert "filtros_aplicados" in data
    
    def test_operaciones_grafico_filtro_montevideo(self, client_api):
        """Filtro por localidad Montevideo"""
        response = client_api.get(
            "/api/reportes/operaciones-grafico"
            "?fecha_desde=2025-01-01&fecha_hasta=2025-12-31"
            "&localidad=Montevideo"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["filtros_aplicados"]["localidad"] == "Montevideo"
    
    def test_operaciones_grafico_filtro_mercedes(self, client_api):
        """Filtro por localidad Mercedes"""
        response = client_api.get(
            "/api/reportes/operaciones-grafico"
            "?fecha_desde=2025-01-01&fecha_hasta=2025-12-31"
            "&localidad=MERCEDES"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["filtros_aplicados"]["localidad"] == "MERCEDES"
    
    def test_operaciones_grafico_sin_localidad(self, client_api):
        """Sin filtro de localidad debe mostrar 'Todas'"""
        response = client_api.get(
            "/api/reportes/operaciones-grafico"
            "?fecha_desde=2025-01-01&fecha_hasta=2025-12-31"
        )
        
        data = response.json()
        
        assert data["filtros_aplicados"]["localidad"] == "Todas"
    
    def test_operaciones_grafico_estructura_operacion(self, client_api):
        """Verificar estructura de cada operación"""
        response = client_api.get(
            "/api/reportes/operaciones-grafico"
            "?fecha_desde=2025-01-01&fecha_hasta=2025-12-31"
        )
        
        data = response.json()
        
        if data["operaciones"]:
            op = data["operaciones"][0]
            
            # Campos requeridos
            assert "id" in op
            assert "tipo_operacion" in op
            assert "fecha" in op
            assert "monto_uyu" in op
            assert "localidad" in op
    
    def test_operaciones_grafico_fechas_isoformat(self, client_api):
        """Las fechas en filtros deben estar en ISO format"""
        response = client_api.get(
            "/api/reportes/operaciones-grafico"
            "?fecha_desde=2025-01-01&fecha_hasta=2025-12-31"
        )
        
        data = response.json()
        
        assert data["filtros_aplicados"]["fecha_desde"] == "2025-01-01"
        assert data["filtros_aplicados"]["fecha_hasta"] == "2025-12-31"
    
    def test_operaciones_grafico_sin_fechas_error(self, client_api):
        """Sin fechas requeridas debe dar error 422"""
        response = client_api.get("/api/reportes/operaciones-grafico")
        
        # FastAPI devuelve 422 para validación fallida
        assert response.status_code == 422


# ══════════════════════════════════════════════════════════════
# TESTS SIN AUTENTICACIÓN
# ══════════════════════════════════════════════════════════════

class TestReportesAuth:
    """Tests de autenticación en endpoints de reportes"""
    
    def test_resumen_mensual_sin_auth(self):
        """Sin autenticación debe dar 401"""
        client = TestClient(app)
        response = client.get("/api/reportes/resumen-mensual")
        assert response.status_code == 401
    
    def test_por_area_sin_auth(self):
        """Sin autenticación debe dar 401"""
        client = TestClient(app)
        response = client.get("/api/reportes/por-area")
        assert response.status_code == 401
    
    def test_rentabilidad_sin_auth(self):
        """Sin autenticación debe dar 401"""
        client = TestClient(app)
        response = client.get("/api/reportes/rentabilidad")
        assert response.status_code == 401
    
    def test_operaciones_grafico_sin_auth(self):
        """Sin autenticación debe dar 401"""
        client = TestClient(app)
        response = client.get(
            "/api/reportes/operaciones-grafico"
            "?fecha_desde=2025-01-01&fecha_hasta=2025-12-31"
        )
        assert response.status_code == 401




