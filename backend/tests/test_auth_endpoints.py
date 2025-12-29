"""
Suite de Tests para Auth Endpoints - Sistema CFO Inteligente

Tests de endpoints de autenticacion: /login, /register
Usa dependency_overrides de FastAPI para mockear la base de datos.

Ejecutar:
    cd backend
    pytest tests/test_auth_endpoints.py -v
    pytest tests/test_auth_endpoints.py -v --cov=app.api.auth

Autor: Sistema CFO Inteligente
Fecha: Diciembre 2025
"""

import pytest
from unittest.mock import Mock
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app
from app.core.database import get_db
from app.core.security import hash_password


@pytest.fixture
def client():
    """Cliente de FastAPI con BD mockeada usando dependency_overrides"""
    from app.core.security import get_current_user
    from app.models import Usuario
    
    mock_db = Mock()
    
    mock_user = Mock(spec=Usuario)
    mock_user.id = "e85916c0-898a-46e0-84a5-c9c2ff92eaea"
    mock_user.email = "admin@grupoconexion.uy"
    mock_user.nombre = "Admin"
    mock_user.es_socio = True
    mock_user.activo = True
    
    def override_get_db():
        return mock_db
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with TestClient(app) as test_client:
        yield test_client, mock_db
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_usuario_activo():
    """Mock de usuario activo"""
    usuario = Mock()
    usuario.id = uuid4()
    usuario.email = "test@grupoconexion.uy"
    usuario.nombre = "Usuario Test"
    usuario.password_hash = hash_password("password123")
    usuario.es_socio = False
    usuario.activo = True
    return usuario


@pytest.fixture
def mock_usuario_socio():
    """Mock de usuario socio"""
    usuario = Mock()
    usuario.id = uuid4()
    usuario.email = "aborio@grupoconexion.uy"
    usuario.nombre = "Socio Test"
    usuario.password_hash = hash_password("password123")
    usuario.es_socio = True
    usuario.activo = True
    return usuario


@pytest.fixture
def mock_usuario_inactivo():
    """Mock de usuario inactivo"""
    usuario = Mock()
    usuario.id = uuid4()
    usuario.email = "inactivo@grupoconexion.uy"
    usuario.nombre = "Usuario Inactivo"
    usuario.password_hash = hash_password("password123")
    usuario.es_socio = False
    usuario.activo = False
    return usuario


class TestLogin:
    """Tests del endpoint POST /login"""
    
    def test_login_exitoso_retorna_token(self, client, mock_usuario_activo):
        """Login exitoso debe retornar access_token"""
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = mock_usuario_activo
        
        response = test_client.post("/api/auth/login", json={
            "email": "test@grupoconexion.uy",
            "password": "password123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["nombre"] == "Usuario Test"
        assert data["es_socio"] is False
    
    def test_login_email_incorrecto_retorna_401(self, client):
        """Email incorrecto debe retornar 401"""
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = test_client.post("/api/auth/login", json={
            "email": "noexiste@email.com",
            "password": "password123"
        })
        
        assert response.status_code == 401
    
    def test_login_password_incorrecto_retorna_401(self, client, mock_usuario_activo):
        """Password incorrecto debe retornar 401"""
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = mock_usuario_activo
        
        response = test_client.post("/api/auth/login", json={
            "email": "test@grupoconexion.uy",
            "password": "password_incorrecto"
        })
        
        assert response.status_code == 401
    
    def test_login_usuario_inactivo_retorna_403(self, client, mock_usuario_inactivo):
        """Usuario inactivo debe retornar 403"""
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = mock_usuario_inactivo
        
        response = test_client.post("/api/auth/login", json={
            "email": "inactivo@grupoconexion.uy",
            "password": "password123"
        })
        
        assert response.status_code == 403
        assert "desactivado" in response.json()["detail"].lower()
    
    def test_login_socio_retorna_es_socio_true(self, client, mock_usuario_socio):
        """Login de socio debe retornar es_socio=True"""
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = mock_usuario_socio
        
        response = test_client.post("/api/auth/login", json={
            "email": "aborio@grupoconexion.uy",
            "password": "password123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["es_socio"] is True


class TestRegister:
    """Tests del endpoint POST /register con nuevo schema (prefijo_email)"""
    
    def test_register_exitoso_crea_usuario(self, client):
        """Registro exitoso debe crear usuario con dominio auto-completado"""
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = test_client.post("/api/auth/register", json={
            "prefijo_email": "nuevo",
            "nombre": "Nuevo Usuario",
            "password": "password123"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "nuevo@grupoconexion.uy"
        assert "exitosamente" in data["message"]
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_register_email_duplicado_retorna_400(self, client, mock_usuario_activo):
        """Prefijo duplicado debe retornar 400"""
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = mock_usuario_activo
        
        response = test_client.post("/api/auth/register", json={
            "prefijo_email": "test",
            "nombre": "Usuario Duplicado",
            "password": "password123"
        })
        
        assert response.status_code == 400
        assert "ya" in response.json()["detail"].lower()
    
    def test_register_asigna_rol_socio_si_email_autorizado(self, client):
        """Prefijo autorizado debe asignar es_socio=True"""
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = test_client.post("/api/auth/register", json={
            "prefijo_email": "aborio",
            "nombre": "Aborio Socio",
            "password": "password123"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert "socio" in data["message"]
        assert data["es_socio"] is True
        
        usuario_creado = mock_db.add.call_args[0][0]
        assert usuario_creado.es_socio is True
    
    def test_register_asigna_rol_colaborador_si_email_no_autorizado(self, client):
        """Prefijo no autorizado debe asignar es_socio=False"""
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = test_client.post("/api/auth/register", json={
            "prefijo_email": "colaborador",
            "nombre": "Colaborador Normal",
            "password": "password123"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert "colaborador" in data["message"]
        assert data["es_socio"] is False
        
        usuario_creado = mock_db.add.call_args[0][0]
        assert usuario_creado.es_socio is False
    
    def test_register_password_se_hashea(self, client):
        """El password debe guardarse hasheado, no en texto plano"""
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        password_plano = "mi_password_secreto"
        
        response = test_client.post("/api/auth/register", json={
            "prefijo_email": "nuevo",
            "nombre": "Nuevo Usuario",
            "password": password_plano
        })
        
        assert response.status_code == 201
        
        usuario_creado = mock_db.add.call_args[0][0]
        assert usuario_creado.password_hash != password_plano
        assert usuario_creado.password_hash.startswith("$2b$")
    
    def test_register_usuario_activo_por_defecto(self, client):
        """Usuario nuevo debe estar activo por defecto"""
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = test_client.post("/api/auth/register", json={
            "prefijo_email": "nuevo",
            "nombre": "Nuevo Usuario",
            "password": "password123"
        })
        
        assert response.status_code == 201
        
        usuario_creado = mock_db.add.call_args[0][0]
        assert usuario_creado.activo is True
    
    def test_register_password_corto_retorna_400(self, client):
        """Password menor a 6 caracteres debe retornar 400"""
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = test_client.post("/api/auth/register", json={
            "prefijo_email": "nuevo",
            "nombre": "Nuevo Usuario",
            "password": "12345"
        })
        
        assert response.status_code == 400
        assert "6 caracteres" in response.json()["detail"]


class TestAuthValidation:
    """Tests de validacion de datos de entrada"""
    
    def test_login_sin_email_retorna_422(self, client):
        """Login sin email debe retornar 422"""
        test_client, mock_db = client
        
        response = test_client.post("/api/auth/login", json={
            "password": "password123"
        })
        
        assert response.status_code == 422
    
    def test_login_sin_password_retorna_422(self, client):
        """Login sin password debe retornar 422"""
        test_client, mock_db = client
        
        response = test_client.post("/api/auth/login", json={
            "email": "test@email.com"
        })
        
        assert response.status_code == 422
    
    def test_register_prefijo_con_arroba_retorna_400(self, client):
        """Prefijo con @ debe retornar 400"""
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = test_client.post("/api/auth/register", json={
            "prefijo_email": "usuario@dominio.com",
            "nombre": "Test",
            "password": "password123"
        })
        
        assert response.status_code == 400
        assert "sin @" in response.json()["detail"]
    
    def test_register_sin_nombre_retorna_422(self, client):
        """Register sin nombre debe retornar 422"""
        test_client, mock_db = client
        
        response = test_client.post("/api/auth/register", json={
            "prefijo_email": "test",
            "password": "password123"
        })
        
        assert response.status_code == 422
    
    def test_register_prefijo_vacio_retorna_400(self, client):
        """Prefijo vacio debe retornar 400"""
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = test_client.post("/api/auth/register", json={
            "prefijo_email": "",
            "nombre": "Test",
            "password": "password123"
        })
        
        assert response.status_code == 400
        assert "requerido" in response.json()["detail"]


class TestSociosAutorizados:
    """Tests de la lista de socios autorizados"""
    
    @pytest.mark.parametrize("prefijo", ["aborio", "falgorta", "vcaresani", "gtaborda", "bgandolfo"])
    def test_todos_los_socios_autorizados_son_socios(self, client, prefijo):
        """Todos los prefijos en SOCIOS_AUTORIZADOS deben crear socio"""
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = test_client.post("/api/auth/register", json={
            "prefijo_email": prefijo,
            "nombre": f"Socio {prefijo}",
            "password": "password123"
        })
        
        assert response.status_code == 201
        usuario_creado = mock_db.add.call_args[0][0]
        assert usuario_creado.es_socio is True, f"Prefijo {prefijo} deberia ser socio"
    
    def test_prefijo_case_insensitive(self, client):
        """El prefijo debe ser case-insensitive"""
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = test_client.post("/api/auth/register", json={
            "prefijo_email": "ABORIO",
            "nombre": "Aborio Mayusculas",
            "password": "password123"
        })
        
        assert response.status_code == 201
        usuario_creado = mock_db.add.call_args[0][0]
        assert usuario_creado.es_socio is True
    
    def test_bgandolfo_usa_dominio_cgmasociados(self, client):
        """bgandolfo debe usar dominio cgmasociados.com"""
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = test_client.post("/api/auth/register", json={
            "prefijo_email": "bgandolfo",
            "nombre": "Bruno Gandolfo",
            "password": "password123"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "bgandolfo@cgmasociados.com"
        assert data["es_socio"] is True
