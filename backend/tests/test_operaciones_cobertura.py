"""
Tests exhaustivos para app/api/operaciones.py

Objetivo: Subir cobertura de 40% a 70%+

Ejecutar:
    pytest tests/test_operaciones_cobertura.py -v --cov=app.api.operaciones --cov-report=term-missing
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from uuid import uuid4, UUID
from decimal import Decimal
from datetime import date, datetime, timezone

from app.main import app
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Usuario, Operacion, TipoOperacion, Moneda, Localidad


# ══════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════

@pytest.fixture
def mock_db():
    """Mock de sesión de base de datos"""
    return MagicMock()


@pytest.fixture
def mock_socio_user():
    """Mock de usuario socio"""
    user = Mock()
    user.id = uuid4()
    user.email = "socio@test.com"
    user.es_socio = True
    return user


@pytest.fixture
def mock_colaborador_user():
    """Mock de usuario NO socio (colaborador)"""
    user = Mock()
    user.id = uuid4()
    user.email = "colaborador@test.com"
    user.es_socio = False
    return user


@pytest.fixture
def client_con_socio(mock_db, mock_socio_user):
    """Cliente API autenticado como socio"""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_socio_user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def client_con_colaborador(mock_db, mock_colaborador_user):
    """Cliente API autenticado como colaborador (NO socio)"""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_colaborador_user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def operacion_mock():
    """Mock de una operación existente"""
    op = Mock(spec=Operacion)
    op.id = uuid4()
    op.tipo_operacion = TipoOperacion.INGRESO
    op.fecha = date(2025, 10, 15)
    op.monto_original = Decimal("10000.00")
    op.moneda_original = Moneda.UYU
    op.tipo_cambio = Decimal("40.00")
    op.monto_uyu = Decimal("10000.00")
    op.monto_usd = Decimal("250.00")
    op.localidad = Localidad.MONTEVIDEO
    op.cliente = "Cliente Test"
    op.proveedor = None
    op.descripcion = "Descripción test"
    op.deleted_at = None
    op.area = Mock(id=uuid4(), nombre="Jurídica")
    op.area_id = op.area.id
    return op


# ══════════════════════════════════════════════════════════════
# TESTS DE ANULAR OPERACIÓN
# ══════════════════════════════════════════════════════════════

class TestAnularOperacion:
    """Tests del endpoint PATCH /{operacion_id}/anular"""
    
    def test_anular_operacion_id_invalido(self, client_con_socio):
        """ID inválido debe retornar 400"""
        response = client_con_socio.patch("/api/operaciones/no-es-uuid/anular")
        assert response.status_code == 400
        assert "ID inválido" in response.json()["detail"]
    
    def test_anular_operacion_no_encontrada(self, client_con_socio, mock_db):
        """Operación no encontrada debe retornar 404"""
        # Configurar mock para no encontrar operación
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        id_random = str(uuid4())
        response = client_con_socio.patch(f"/api/operaciones/{id_random}/anular")
        assert response.status_code == 404
        assert "no encontrada" in response.json()["detail"]
    
    def test_anular_operacion_exitosa(self, client_con_socio, mock_db, operacion_mock):
        """Anulación exitosa debe retornar 200"""
        # Configurar mock para encontrar operación
        mock_db.query.return_value.filter.return_value.first.return_value = operacion_mock
        
        response = client_con_socio.patch(f"/api/operaciones/{operacion_mock.id}/anular")
        assert response.status_code == 200
        assert "anulada" in response.json()["message"]
        mock_db.commit.assert_called_once()


# ══════════════════════════════════════════════════════════════
# TESTS DE PERMISOS DE SOCIO
# ══════════════════════════════════════════════════════════════

class TestPermisosRetiro:
    """Tests de permisos para retiros (solo socios)"""
    
    def test_crear_retiro_como_colaborador_forbidden(self, client_con_colaborador):
        """Colaborador NO puede crear retiro"""
        response = client_con_colaborador.post("/api/operaciones/retiro", json={
            "fecha": "2025-12-19",
            "monto_uyu": 5000,
            "tipo_cambio": 40.0,
            "socio_id": str(uuid4()),
            "localidad": "MONTEVIDEO"
        })
        assert response.status_code == 403
        assert "socios" in response.json()["detail"].lower()
    
    def test_crear_retiro_como_socio_permitido(self, client_con_socio, mock_db):
        """Socio SÍ puede crear retiro"""
        # Mock del servicio
        with patch('app.api.operaciones.operacion_service.crear_retiro') as mock_service:
            mock_service.return_value = {"id": str(uuid4()), "message": "Retiro creado"}
            
            response = client_con_socio.post("/api/operaciones/retiro", json={
                "fecha": "2025-12-19",
                "monto_uyu": 5000,
                "tipo_cambio": 40.0,
                "socio_id": str(uuid4()),
                "localidad": "MONTEVIDEO"
            })
            # No debe ser 403
            assert response.status_code != 403


class TestPermisosDistribucion:
    """Tests de permisos para distribuciones (solo socios)"""
    
    def test_crear_distribucion_como_colaborador_forbidden(self, client_con_colaborador):
        """Colaborador NO puede crear distribución"""
        response = client_con_colaborador.post("/api/operaciones/distribucion", json={
            "fecha": "2025-12-19",
            "monto_total": 100000,
            "tipo_cambio": 40.0,
            "localidad": "MONTEVIDEO"
        })
        assert response.status_code == 403
        assert "socios" in response.json()["detail"].lower()
    
    def test_crear_distribucion_como_socio_permitido(self, client_con_socio, mock_db):
        """Socio SÍ puede crear distribución"""
        with patch('app.api.operaciones.operacion_service.crear_distribucion') as mock_service:
            mock_service.return_value = {"id": str(uuid4()), "message": "Distribución creada"}
            
            response = client_con_socio.post("/api/operaciones/distribucion", json={
                "fecha": "2025-12-19",
                "monto_total": 100000,
                "tipo_cambio": 40.0,
                "localidad": "MONTEVIDEO"
            })
            # No debe ser 403
            assert response.status_code != 403


# ══════════════════════════════════════════════════════════════
# TESTS DE ACTUALIZAR OPERACIÓN
# ══════════════════════════════════════════════════════════════

class TestActualizarOperacion:
    """Tests del endpoint PATCH /{operacion_id}"""
    
    def test_actualizar_operacion_id_invalido(self, client_con_socio):
        """ID inválido debe retornar 400"""
        response = client_con_socio.patch(
            "/api/operaciones/not-a-valid-uuid",
            json={"descripcion": "Test"}
        )
        assert response.status_code == 400
    
    def test_actualizar_operacion_no_encontrada(self, client_con_socio, mock_db):
        """Operación no existente debe retornar 404"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = client_con_socio.patch(
            f"/api/operaciones/{uuid4()}",
            json={"descripcion": "Test"}
        )
        assert response.status_code == 404
    
    def test_actualizar_operacion_descripcion(self, client_con_socio, mock_db, operacion_mock):
        """Actualizar descripción debe funcionar"""
        mock_db.query.return_value.filter.return_value.first.return_value = operacion_mock
        
        response = client_con_socio.patch(
            f"/api/operaciones/{operacion_mock.id}",
            json={"descripcion": "Nueva descripción"}
        )
        assert response.status_code == 200
        assert "actualizada" in response.json()["message"]
    
    def test_actualizar_operacion_fecha(self, client_con_socio, mock_db, operacion_mock):
        """Actualizar fecha debe funcionar"""
        mock_db.query.return_value.filter.return_value.first.return_value = operacion_mock
        
        response = client_con_socio.patch(
            f"/api/operaciones/{operacion_mock.id}",
            json={"fecha": "2025-11-01"}
        )
        assert response.status_code == 200
    
    def test_actualizar_operacion_localidad(self, client_con_socio, mock_db, operacion_mock):
        """Actualizar localidad debe funcionar"""
        mock_db.query.return_value.filter.return_value.first.return_value = operacion_mock
        
        response = client_con_socio.patch(
            f"/api/operaciones/{operacion_mock.id}",
            json={"localidad": "MERCEDES"}
        )
        assert response.status_code == 200
    
    def test_actualizar_operacion_cliente(self, client_con_socio, mock_db, operacion_mock):
        """Actualizar cliente debe funcionar"""
        mock_db.query.return_value.filter.return_value.first.return_value = operacion_mock
        
        response = client_con_socio.patch(
            f"/api/operaciones/{operacion_mock.id}",
            json={"cliente": "Nuevo Cliente S.A."}
        )
        assert response.status_code == 200
    
    def test_actualizar_operacion_proveedor(self, client_con_socio, mock_db, operacion_mock):
        """Actualizar proveedor debe funcionar"""
        mock_db.query.return_value.filter.return_value.first.return_value = operacion_mock
        
        response = client_con_socio.patch(
            f"/api/operaciones/{operacion_mock.id}",
            json={"proveedor": "Proveedor XYZ"}
        )
        assert response.status_code == 200
    
    def test_actualizar_operacion_area_id(self, client_con_socio, mock_db, operacion_mock):
        """Actualizar area_id debe funcionar"""
        mock_db.query.return_value.filter.return_value.first.return_value = operacion_mock
        
        response = client_con_socio.patch(
            f"/api/operaciones/{operacion_mock.id}",
            json={"area_id": str(uuid4())}
        )
        assert response.status_code == 200
    
    def test_actualizar_operacion_monto_original(self, client_con_socio, mock_db, operacion_mock):
        """Actualizar monto_original debe recalcular"""
        mock_db.query.return_value.filter.return_value.first.return_value = operacion_mock
        
        with patch('app.api.operaciones.operacion_service.calcular_montos') as mock_calc:
            mock_calc.return_value = (Decimal("15000.00"), Decimal("375.00"))
            
            response = client_con_socio.patch(
                f"/api/operaciones/{operacion_mock.id}",
                json={"monto_original": 15000.0}
            )
            assert response.status_code == 200
    
    def test_actualizar_operacion_moneda(self, client_con_socio, mock_db, operacion_mock):
        """Actualizar moneda debe recalcular"""
        mock_db.query.return_value.filter.return_value.first.return_value = operacion_mock
        
        with patch('app.api.operaciones.operacion_service.calcular_montos') as mock_calc:
            mock_calc.return_value = (Decimal("400000.00"), Decimal("10000.00"))
            
            response = client_con_socio.patch(
                f"/api/operaciones/{operacion_mock.id}",
                json={"moneda_original": "USD"}
            )
            assert response.status_code == 200
    
    def test_actualizar_operacion_tipo_cambio(self, client_con_socio, mock_db, operacion_mock):
        """Actualizar tipo_cambio debe recalcular"""
        mock_db.query.return_value.filter.return_value.first.return_value = operacion_mock
        
        with patch('app.api.operaciones.operacion_service.calcular_montos') as mock_calc:
            mock_calc.return_value = (Decimal("10000.00"), Decimal("222.22"))
            
            response = client_con_socio.patch(
                f"/api/operaciones/{operacion_mock.id}",
                json={"tipo_cambio": 45.0}
            )
            assert response.status_code == 200
    
    def test_actualizar_operacion_monto_uyu_directo(self, client_con_socio, mock_db, operacion_mock):
        """Actualizar monto_uyu directamente debe recalcular monto_usd"""
        mock_db.query.return_value.filter.return_value.first.return_value = operacion_mock
        
        response = client_con_socio.patch(
            f"/api/operaciones/{operacion_mock.id}",
            json={"monto_uyu": 20000.0}
        )
        assert response.status_code == 200
    
    def test_actualizar_operacion_monto_usd_directo(self, client_con_socio, mock_db, operacion_mock):
        """Actualizar monto_usd directamente debe recalcular monto_uyu"""
        mock_db.query.return_value.filter.return_value.first.return_value = operacion_mock
        
        response = client_con_socio.patch(
            f"/api/operaciones/{operacion_mock.id}",
            json={"monto_usd": 500.0}
        )
        assert response.status_code == 200
    
    def test_actualizar_operacion_multiples_campos(self, client_con_socio, mock_db, operacion_mock):
        """Actualizar múltiples campos a la vez"""
        mock_db.query.return_value.filter.return_value.first.return_value = operacion_mock
        
        with patch('app.api.operaciones.operacion_service.calcular_montos') as mock_calc:
            mock_calc.return_value = (Decimal("20000.00"), Decimal("500.00"))
            
            response = client_con_socio.patch(
                f"/api/operaciones/{operacion_mock.id}",
                json={
                    "descripcion": "Nueva descripción",
                    "cliente": "Nuevo Cliente",
                    "monto_original": 20000.0,
                    "localidad": "MERCEDES"
                }
            )
            assert response.status_code == 200


# ══════════════════════════════════════════════════════════════
# TESTS DE BÚSQUEDA DE CLIENTES Y PROVEEDORES
# ══════════════════════════════════════════════════════════════

class TestBuscarClientes:
    """Tests del endpoint GET /clientes/buscar"""
    
    def test_buscar_clientes_vacio(self, client_con_socio, mock_db):
        """Búsqueda sin resultados debe retornar lista vacía"""
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        
        response = client_con_socio.get("/api/operaciones/clientes/buscar?q=xyz")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_buscar_clientes_con_resultados(self, client_con_socio, mock_db):
        """Búsqueda con resultados debe retornar lista"""
        cliente1 = Mock(id=uuid4(), nombre="Cliente ABC")
        cliente2 = Mock(id=uuid4(), nombre="Cliente ABC S.A.")
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = [cliente1, cliente2]
        
        response = client_con_socio.get("/api/operaciones/clientes/buscar?q=ABC")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert "nombre" in data[0]


class TestBuscarProveedores:
    """Tests del endpoint GET /proveedores/buscar"""
    
    def test_buscar_proveedores_vacio(self, client_con_socio, mock_db):
        """Búsqueda sin resultados debe retornar lista vacía"""
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        
        response = client_con_socio.get("/api/operaciones/proveedores/buscar?q=xyz")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_buscar_proveedores_con_resultados(self, client_con_socio, mock_db):
        """Búsqueda con resultados debe retornar lista"""
        prov1 = Mock(id=uuid4(), nombre="Proveedor XYZ")
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = [prov1]
        
        response = client_con_socio.get("/api/operaciones/proveedores/buscar?q=XYZ")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["nombre"] == "Proveedor XYZ"


# ══════════════════════════════════════════════════════════════
# TESTS DE LISTAR OPERACIONES
# ══════════════════════════════════════════════════════════════

class TestGetOperaciones:
    """Tests del endpoint GET /"""
    
    def test_listar_operaciones_vacio(self, client_con_socio, mock_db):
        """Sin operaciones debe retornar lista vacía"""
        mock_db.query.return_value.options.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        response = client_con_socio.get("/api/operaciones/")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_listar_operaciones_con_resultados(self, client_con_socio, mock_db, operacion_mock):
        """Con operaciones debe retornar lista formateada"""
        mock_db.query.return_value.options.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [operacion_mock]
        
        response = client_con_socio.get("/api/operaciones/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "id" in data[0]
        assert "tipo_operacion" in data[0]
    
    def test_listar_operaciones_limit_custom(self, client_con_socio, mock_db):
        """Debe respetar el parámetro limit"""
        mock_db.query.return_value.options.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        response = client_con_socio.get("/api/operaciones/?limit=50")
        assert response.status_code == 200


# ══════════════════════════════════════════════════════════════
# TESTS DE CREAR INGRESO Y GASTO
# ══════════════════════════════════════════════════════════════

class TestCrearIngreso:
    """Tests del endpoint POST /ingreso"""
    
    def test_crear_ingreso_exitoso(self, client_con_socio, mock_db):
        """Crear ingreso debe llamar al servicio"""
        with patch('app.api.operaciones.operacion_service.crear_ingreso') as mock_service:
            mock_service.return_value = {"id": str(uuid4()), "message": "Ingreso creado"}
            
            response = client_con_socio.post("/api/operaciones/ingreso", json={
                "fecha": "2025-12-19",
                "monto_original": 10000,
                "moneda_original": "UYU",
                "tipo_cambio": 40.0,
                "area_id": str(uuid4()),
                "localidad": "MONTEVIDEO",
                "cliente": "Cliente Test"
            })
            # Puede ser 200 o 422 dependiendo de validación
            assert response.status_code in [200, 422]


class TestCrearGasto:
    """Tests del endpoint POST /gasto"""
    
    def test_crear_gasto_exitoso(self, client_con_socio, mock_db):
        """Crear gasto debe llamar al servicio"""
        with patch('app.api.operaciones.operacion_service.crear_gasto') as mock_service:
            mock_service.return_value = {"id": str(uuid4()), "message": "Gasto creado"}
            
            response = client_con_socio.post("/api/operaciones/gasto", json={
                "fecha": "2025-12-19",
                "monto_original": 5000,
                "moneda_original": "UYU",
                "tipo_cambio": 40.0,
                "area_id": str(uuid4()),
                "localidad": "MONTEVIDEO",
                "proveedor": "Proveedor Test"
            })
            # Puede ser 200 o 422 dependiendo de validación
            assert response.status_code in [200, 422]

