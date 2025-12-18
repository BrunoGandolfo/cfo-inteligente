"""
Suite de Tests para Auth Endpoints - Sistema CFO Inteligente

Tests de endpoints de autenticación: /login, /register
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


# ══════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════

@pytest.fixture
def client():
    """Cliente de FastAPI con BD mockeada usando dependency_overrides"""
    from app.core.security import get_current_user
    from app.models import Usuario
    
    # Mock de sesión de BD
    mock_db = Mock()
    
    # Mock de usuario autenticado (para endpoints que requieren auth)
    mock_user = Mock(spec=Usuario)
    mock_user.id = "e85916c0-898a-46e0-84a5-c9c2ff92eaea"
    mock_user.email = "admin@conexion.uy"
    mock_user.nombre = "Admin"
    mock_user.es_socio = True
    mock_user.activo = True
    
    def override_get_db():
        return mock_db
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with TestClient(app) as test_client:
        yield test_client, mock_db
    
    # Limpiar override después del test
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


# ══════════════════════════════════════════════════════════════
# GRUPO 1: TESTS DE LOGIN
# ══════════════════════════════════════════════════════════════

class TestLogin:
    """Tests del endpoint POST /login"""
    
    def test_login_exitoso_retorna_token(self, client, mock_usuario_activo):
        """Login exitoso debe retornar access_token"""
        # Arrange
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = mock_usuario_activo
        
        # Act
        response = test_client.post("/api/auth/login", json={
            "email": "test@grupoconexion.uy",
            "password": "password123"
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["nombre"] == "Usuario Test"
        assert data["es_socio"] is False
    
    def test_login_email_incorrecto_retorna_401(self, client):
        """Email incorrecto debe retornar 401"""
        # Arrange
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        response = test_client.post("/api/auth/login", json={
            "email": "noexiste@email.com",
            "password": "password123"
        })
        
        # Assert
        assert response.status_code == 401
        assert "Email o contraseña incorrectos" in response.json()["detail"]
    
    def test_login_password_incorrecto_retorna_401(self, client, mock_usuario_activo):
        """Password incorrecto debe retornar 401"""
        # Arrange
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = mock_usuario_activo
        
        # Act
        response = test_client.post("/api/auth/login", json={
            "email": "test@grupoconexion.uy",
            "password": "password_incorrecto"
        })
        
        # Assert
        assert response.status_code == 401
        assert "Email o contraseña incorrectos" in response.json()["detail"]
    
    def test_login_usuario_inactivo_retorna_403(self, client, mock_usuario_inactivo):
        """Usuario inactivo debe retornar 403"""
        # Arrange
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = mock_usuario_inactivo
        
        # Act
        response = test_client.post("/api/auth/login", json={
            "email": "inactivo@grupoconexion.uy",
            "password": "password123"
        })
        
        # Assert
        assert response.status_code == 403
        assert "desactivado" in response.json()["detail"].lower()
    
    def test_login_socio_retorna_es_socio_true(self, client, mock_usuario_socio):
        """Login de socio debe retornar es_socio=True"""
        # Arrange
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = mock_usuario_socio
        
        # Act
        response = test_client.post("/api/auth/login", json={
            "email": "aborio@grupoconexion.uy",
            "password": "password123"
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["es_socio"] is True


# ══════════════════════════════════════════════════════════════
# GRUPO 2: TESTS DE REGISTER
# ══════════════════════════════════════════════════════════════

class TestRegister:
    """Tests del endpoint POST /register"""
    
    def test_register_exitoso_crea_usuario(self, client):
        """Registro exitoso debe crear usuario"""
        # Arrange
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        response = test_client.post("/api/auth/register", json={
            "email": "nuevo@grupoconexion.uy",
            "nombre": "Nuevo Usuario",
            "password": "password123"
        })
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "nuevo@grupoconexion.uy"
        assert "registrado exitosamente" in data["message"]
        
        # Verificar que se llamó db.add
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_register_email_duplicado_retorna_400(self, client, mock_usuario_activo):
        """Email duplicado debe retornar 400"""
        # Arrange
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = mock_usuario_activo
        
        # Act
        response = test_client.post("/api/auth/register", json={
            "email": "test@grupoconexion.uy",
            "nombre": "Usuario Duplicado",
            "password": "password123"
        })
        
        # Assert
        assert response.status_code == 400
        assert "Ya existe un usuario" in response.json()["detail"]
    
    def test_register_asigna_rol_socio_si_email_autorizado(self, client):
        """Email autorizado debe asignar es_socio=True"""
        # Arrange
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Emails autorizados: aborio, falgorta, vcaresani, gtaborda
        
        # Act
        response = test_client.post("/api/auth/register", json={
            "email": "aborio@grupoconexion.uy",
            "nombre": "Aborio Socio",
            "password": "password123"
        })
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "socio" in data["message"]
        
        # Verificar que el usuario se creó con es_socio=True
        usuario_creado = mock_db.add.call_args[0][0]
        assert usuario_creado.es_socio is True
    
    def test_register_asigna_rol_colaborador_si_email_no_autorizado(self, client):
        """Email no autorizado debe asignar es_socio=False"""
        # Arrange
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        response = test_client.post("/api/auth/register", json={
            "email": "colaborador@grupoconexion.uy",
            "nombre": "Colaborador Normal",
            "password": "password123"
        })
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "colaborador" in data["message"]
        
        # Verificar que el usuario se creó con es_socio=False
        usuario_creado = mock_db.add.call_args[0][0]
        assert usuario_creado.es_socio is False
    
    def test_register_password_se_hashea(self, client):
        """El password debe guardarse hasheado, no en texto plano"""
        # Arrange
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        password_plano = "mi_password_secreto"
        
        # Act
        response = test_client.post("/api/auth/register", json={
            "email": "nuevo@grupoconexion.uy",
            "nombre": "Nuevo Usuario",
            "password": password_plano
        })
        
        # Assert
        assert response.status_code == 201
        
        # Verificar que el password se hasheó
        usuario_creado = mock_db.add.call_args[0][0]
        assert usuario_creado.password_hash != password_plano
        assert usuario_creado.password_hash.startswith("$2b$")  # bcrypt
    
    def test_register_usuario_activo_por_defecto(self, client):
        """Usuario nuevo debe estar activo por defecto"""
        # Arrange
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        response = test_client.post("/api/auth/register", json={
            "email": "nuevo@grupoconexion.uy",
            "nombre": "Nuevo Usuario",
            "password": "password123"
        })
        
        # Assert
        assert response.status_code == 201
        
        usuario_creado = mock_db.add.call_args[0][0]
        assert usuario_creado.activo is True


# ══════════════════════════════════════════════════════════════
# GRUPO 3: TESTS DE VALIDACIÓN
# ══════════════════════════════════════════════════════════════

class TestAuthValidation:
    """Tests de validación de datos de entrada"""
    
    def test_login_sin_email_retorna_422(self, client):
        """Login sin email debe retornar 422"""
        # Arrange
        test_client, mock_db = client
        
        # Act
        response = test_client.post("/api/auth/login", json={
            "password": "password123"
        })
        
        # Assert
        assert response.status_code == 422
    
    def test_login_sin_password_retorna_422(self, client):
        """Login sin password debe retornar 422"""
        # Arrange
        test_client, mock_db = client
        
        # Act
        response = test_client.post("/api/auth/login", json={
            "email": "test@email.com"
        })
        
        # Assert
        assert response.status_code == 422
    
    def test_register_email_invalido_retorna_422(self, client):
        """Register con email inválido debe retornar 422"""
        # Arrange
        test_client, mock_db = client
        
        # Act
        response = test_client.post("/api/auth/register", json={
            "email": "email_invalido",
            "nombre": "Test",
            "password": "password123"
        })
        
        # Assert
        assert response.status_code == 422
    
    def test_register_sin_nombre_retorna_422(self, client):
        """Register sin nombre debe retornar 422"""
        # Arrange
        test_client, mock_db = client
        
        # Act
        response = test_client.post("/api/auth/register", json={
            "email": "test@email.com",
            "password": "password123"
        })
        
        # Assert
        assert response.status_code == 422


# ══════════════════════════════════════════════════════════════
# GRUPO 4: TESTS DE SOCIOS_AUTORIZADOS
# ══════════════════════════════════════════════════════════════

class TestSociosAutorizados:
    """Tests de la lista de socios autorizados"""
    
    @pytest.mark.parametrize("prefijo", ["aborio", "falgorta", "vcaresani", "gtaborda"])
    def test_todos_los_socios_autorizados_son_socios(self, client, prefijo):
        """Todos los prefijos en SOCIOS_AUTORIZADOS deben crear socio"""
        # Arrange
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        response = test_client.post("/api/auth/register", json={
            "email": f"{prefijo}@grupoconexion.uy",
            "nombre": f"Socio {prefijo}",
            "password": "password123"
        })
        
        # Assert
        assert response.status_code == 201
        usuario_creado = mock_db.add.call_args[0][0]
        assert usuario_creado.es_socio is True, f"Prefijo {prefijo} debería ser socio"
    
    def test_prefijo_case_insensitive(self, client):
        """El prefijo debe ser case-insensitive"""
        # Arrange
        test_client, mock_db = client
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act - Usar mayúsculas
        response = test_client.post("/api/auth/register", json={
            "email": "ABORIO@grupoconexion.uy",
            "nombre": "Aborio Mayusculas",
            "password": "password123"
        })
        
        # Assert
        assert response.status_code == 201
        usuario_creado = mock_db.add.call_args[0][0]
        assert usuario_creado.es_socio is True
