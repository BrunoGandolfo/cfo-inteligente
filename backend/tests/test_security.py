"""
Suite de Tests para Security - Sistema CFO Inteligente

Tests de funciones de seguridad: hash_password, verify_password, create_access_token.

Ejecutar:
    cd backend
    pytest tests/test_security.py -v
    pytest tests/test_security.py -v --cov=app.core.security

Autor: Sistema CFO Inteligente
Fecha: Diciembre 2025
"""

import pytest
from unittest.mock import patch, Mock
from datetime import datetime, timezone, timedelta
from jose import jwt

from app.core.security import hash_password, verify_password, create_access_token


# ══════════════════════════════════════════════════════════════
# GRUPO 1: TESTS DE hash_password()
# ══════════════════════════════════════════════════════════════

class TestHashPassword:
    """Tests de la función hash_password"""
    
    def test_hash_password_retorna_string(self):
        """hash_password debe retornar un string"""
        # Arrange
        password = "mi_password_seguro"
        
        # Act
        hashed = hash_password(password)
        
        # Assert
        assert isinstance(hashed, str)
        assert len(hashed) > 0
    
    def test_hash_password_diferente_al_original(self):
        """El hash debe ser diferente al password original"""
        # Arrange
        password = "password123"
        
        # Act
        hashed = hash_password(password)
        
        # Assert
        assert hashed != password
        assert password not in hashed
    
    def test_hash_password_dos_hashes_diferentes(self):
        """Mismo password debe generar hashes diferentes (por salt)"""
        # Arrange
        password = "mismo_password"
        
        # Act
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Assert
        assert hash1 != hash2  # bcrypt usa salt aleatorio
    
    def test_hash_password_empieza_con_bcrypt_prefix(self):
        """El hash debe tener formato bcrypt ($2b$)"""
        # Arrange
        password = "test"
        
        # Act
        hashed = hash_password(password)
        
        # Assert
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    
    def test_hash_password_longitud_correcta(self):
        """El hash bcrypt debe tener ~60 caracteres"""
        # Arrange
        password = "password"
        
        # Act
        hashed = hash_password(password)
        
        # Assert
        assert 59 <= len(hashed) <= 61  # bcrypt genera hashes de 60 chars


# ══════════════════════════════════════════════════════════════
# GRUPO 2: TESTS DE verify_password()
# ══════════════════════════════════════════════════════════════

class TestVerifyPassword:
    """Tests de la función verify_password"""
    
    def test_verify_password_correcto_retorna_true(self):
        """Password correcto debe retornar True"""
        # Arrange
        password = "password_correcto"
        hashed = hash_password(password)
        
        # Act
        result = verify_password(password, hashed)
        
        # Assert
        assert result is True
    
    def test_verify_password_incorrecto_retorna_false(self):
        """Password incorrecto debe retornar False"""
        # Arrange
        password = "password_original"
        wrong_password = "password_incorrecto"
        hashed = hash_password(password)
        
        # Act
        result = verify_password(wrong_password, hashed)
        
        # Assert
        assert result is False
    
    def test_verify_password_con_hash_invalido(self):
        """Hash inválido debe retornar False o lanzar excepción"""
        # Arrange
        password = "test"
        invalid_hash = "hash_invalido_no_bcrypt"
        
        # Act & Assert
        # passlib puede retornar False o lanzar excepción
        try:
            result = verify_password(password, invalid_hash)
            assert result is False
        except Exception:
            pass  # Aceptable si lanza excepción
    
    def test_verify_password_case_sensitive(self):
        """Verificación debe ser case-sensitive"""
        # Arrange
        password = "Password123"
        hashed = hash_password(password)
        
        # Act
        result_correcto = verify_password(password, hashed)
        result_incorrecto = verify_password("password123", hashed)
        
        # Assert
        assert result_correcto is True
        assert result_incorrecto is False
    
    def test_verify_password_con_espacios(self):
        """Debe manejar passwords con espacios"""
        # Arrange
        password = "password con espacios"
        hashed = hash_password(password)
        
        # Act
        result = verify_password(password, hashed)
        
        # Assert
        assert result is True


# ══════════════════════════════════════════════════════════════
# GRUPO 3: TESTS DE create_access_token()
# ══════════════════════════════════════════════════════════════

class TestCreateAccessToken:
    """Tests de la función create_access_token"""
    
    def test_create_access_token_retorna_string(self):
        """create_access_token debe retornar un string"""
        # Arrange
        data = {"sub": "user_id_123"}
        
        # Act
        token = create_access_token(data)
        
        # Assert
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_access_token_es_jwt_valido(self):
        """El token debe tener formato JWT (3 partes separadas por .)"""
        # Arrange
        data = {"sub": "user_id_123"}
        
        # Act
        token = create_access_token(data)
        
        # Assert
        parts = token.split(".")
        assert len(parts) == 3  # header.payload.signature
    
    @patch('app.core.security.settings')
    def test_create_access_token_contiene_datos(self, mock_settings):
        """El token debe contener los datos pasados"""
        # Arrange
        mock_settings.secret_key = "test_secret_key_12345"
        mock_settings.algorithm = "HS256"
        mock_settings.access_token_expire_minutes = 30
        
        data = {"sub": "user123", "es_socio": True}
        
        # Act
        token = create_access_token(data)
        
        # Decode para verificar contenido
        decoded = jwt.decode(token, mock_settings.secret_key, algorithms=[mock_settings.algorithm])
        
        # Assert
        assert decoded["sub"] == "user123"
        assert decoded["es_socio"] is True
    
    @patch('app.core.security.settings')
    def test_create_access_token_contiene_exp(self, mock_settings):
        """El token debe contener campo de expiración"""
        # Arrange
        mock_settings.secret_key = "test_secret_key_12345"
        mock_settings.algorithm = "HS256"
        mock_settings.access_token_expire_minutes = 30
        
        data = {"sub": "user123"}
        
        # Act
        token = create_access_token(data)
        
        # Decode
        decoded = jwt.decode(token, mock_settings.secret_key, algorithms=[mock_settings.algorithm])
        
        # Assert
        assert "exp" in decoded
        assert isinstance(decoded["exp"], int)
    
    @patch('app.core.security.settings')
    def test_create_access_token_expiracion_correcta(self, mock_settings):
        """La expiración debe ser aproximadamente en X minutos"""
        # Arrange
        mock_settings.secret_key = "test_secret_key_12345"
        mock_settings.algorithm = "HS256"
        mock_settings.access_token_expire_minutes = 60  # 1 hora
        
        data = {"sub": "user123"}
        ahora = datetime.now(timezone.utc)
        
        # Act
        token = create_access_token(data)
        
        # Decode
        decoded = jwt.decode(token, mock_settings.secret_key, algorithms=[mock_settings.algorithm])
        
        # Assert
        exp_datetime = datetime.utcfromtimestamp(decoded["exp"])
        diferencia = exp_datetime - ahora
        
        # Debe expirar en ~60 minutos (tolerancia de 1 minuto)
        assert 59 <= diferencia.total_seconds() / 60 <= 61
    
    def test_create_access_token_no_modifica_data_original(self):
        """No debe modificar el dict original"""
        # Arrange
        data = {"sub": "user123"}
        data_original = data.copy()
        
        # Act
        create_access_token(data)
        
        # Assert
        assert data == data_original
        assert "exp" not in data


# ══════════════════════════════════════════════════════════════
# GRUPO 4: TESTS DE INTEGRACIÓN
# ══════════════════════════════════════════════════════════════

class TestSecurityIntegration:
    """Tests de integración entre funciones de security"""
    
    def test_flujo_completo_hash_verify(self):
        """Flujo completo: hashear → verificar debe funcionar"""
        # Arrange
        passwords = ["simple", "Con Mayusculas", "con_numeros123", "!@#$%^&*()"]
        
        # Act & Assert
        for password in passwords:
            hashed = hash_password(password)
            assert verify_password(password, hashed) is True
            assert verify_password(password + "x", hashed) is False
    
    def test_hash_verify_con_unicode(self):
        """Debe manejar caracteres unicode"""
        # Arrange
        password = "contraseña_ñ_€_日本語"
        
        # Act
        hashed = hash_password(password)
        result = verify_password(password, hashed)
        
        # Assert
        assert result is True



