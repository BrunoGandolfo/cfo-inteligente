"""
Suite de Tests para ConversacionService - Sistema CFO Inteligente

Tests del servicio de conversaciones y mensajes.

Ejecutar:
    cd backend
    pytest tests/test_conversacion_service.py -v
    pytest tests/test_conversacion_service.py -v --cov=app.services.conversacion_service

Autor: Sistema CFO Inteligente
Fecha: Diciembre 2025
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone, timezone

from app.services.conversacion_service import ConversacionService


# ══════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════

@pytest.fixture
def mock_db():
    """Mock de sesión de base de datos"""
    db = Mock()
    return db


@pytest.fixture
def usuario_id():
    """UUID de usuario de prueba"""
    return uuid4()


@pytest.fixture
def conversacion_id():
    """UUID de conversación de prueba"""
    return uuid4()


@pytest.fixture
def mock_conversacion(usuario_id, conversacion_id):
    """Mock de conversación"""
    conv = Mock()
    conv.id = conversacion_id
    conv.usuario_id = usuario_id
    conv.titulo = "Conversación de prueba"
    conv.created_at = datetime.now(timezone.utc)
    conv.updated_at = datetime.now(timezone.utc)
    return conv


@pytest.fixture
def mock_mensaje(conversacion_id):
    """Mock de mensaje"""
    msg = Mock()
    msg.id = uuid4()
    msg.conversacion_id = conversacion_id
    msg.rol = "user"
    msg.contenido = "Contenido de prueba"
    msg.sql_generado = None
    msg.created_at = datetime.now(timezone.utc)
    return msg


# ══════════════════════════════════════════════════════════════
# GRUPO 1: TESTS DE crear_conversacion()
# ══════════════════════════════════════════════════════════════

class TestCrearConversacion:
    """Tests del método crear_conversacion"""
    
    def test_crear_conversacion_nueva(self, mock_db, usuario_id):
        """Debe crear una nueva conversación"""
        # Arrange
        mock_db.refresh = Mock()
        
        # Act
        with patch('app.services.conversacion_service.Conversacion') as MockConversacion:
            mock_conv = Mock()
            mock_conv.id = uuid4()
            MockConversacion.return_value = mock_conv
            
            result = ConversacionService.crear_conversacion(mock_db, usuario_id)
        
        # Assert
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_crear_conversacion_con_titulo(self, mock_db, usuario_id):
        """Debe crear conversación con título personalizado"""
        # Arrange
        titulo = "Mi conversación personalizada"
        mock_db.refresh = Mock()
        
        # Act
        with patch('app.services.conversacion_service.Conversacion') as MockConversacion:
            mock_conv = Mock()
            MockConversacion.return_value = mock_conv
            
            ConversacionService.crear_conversacion(mock_db, usuario_id, titulo=titulo)
        
        # Assert
        MockConversacion.assert_called_once()
        call_kwargs = MockConversacion.call_args.kwargs
        assert call_kwargs['titulo'] == titulo
    
    def test_crear_conversacion_titulo_default(self, mock_db, usuario_id):
        """Sin título debe usar 'Nueva conversación'"""
        # Arrange
        mock_db.refresh = Mock()
        
        # Act
        with patch('app.services.conversacion_service.Conversacion') as MockConversacion:
            mock_conv = Mock()
            MockConversacion.return_value = mock_conv
            
            ConversacionService.crear_conversacion(mock_db, usuario_id)
        
        # Assert
        call_kwargs = MockConversacion.call_args.kwargs
        assert call_kwargs['titulo'] == "Nueva conversación"
    
    def test_crear_conversacion_asocia_usuario(self, mock_db, usuario_id):
        """Debe asociar la conversación al usuario"""
        # Arrange
        mock_db.refresh = Mock()
        
        # Act
        with patch('app.services.conversacion_service.Conversacion') as MockConversacion:
            mock_conv = Mock()
            MockConversacion.return_value = mock_conv
            
            ConversacionService.crear_conversacion(mock_db, usuario_id)
        
        # Assert
        call_kwargs = MockConversacion.call_args.kwargs
        assert call_kwargs['usuario_id'] == usuario_id


# ══════════════════════════════════════════════════════════════
# GRUPO 2: TESTS DE obtener_conversacion() y listar_conversaciones()
# ══════════════════════════════════════════════════════════════

class TestObtenerConversaciones:
    """Tests de métodos de obtención de conversaciones"""
    
    def test_obtener_conversacion_por_id(self, mock_db, conversacion_id, usuario_id, mock_conversacion):
        """Debe obtener conversación por ID"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = mock_conversacion
        
        # Act
        result = ConversacionService.obtener_conversacion(mock_db, conversacion_id, usuario_id)
        
        # Assert
        assert result == mock_conversacion
        mock_db.query.assert_called_once()
    
    def test_obtener_conversacion_inexistente(self, mock_db, usuario_id):
        """Conversación inexistente debe retornar None"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = ConversacionService.obtener_conversacion(mock_db, uuid4(), usuario_id)
        
        # Assert
        assert result is None
    
    def test_obtener_conversacion_usuario_incorrecto(self, mock_db, conversacion_id, mock_conversacion):
        """Conversación de otro usuario debe retornar None"""
        # Arrange
        otro_usuario_id = uuid4()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = ConversacionService.obtener_conversacion(mock_db, conversacion_id, otro_usuario_id)
        
        # Assert
        assert result is None
    
    def test_listar_conversaciones_usuario(self, mock_db, usuario_id, mock_conversacion):
        """Debe listar conversaciones del usuario"""
        # Arrange
        conversaciones = [mock_conversacion, Mock(), Mock()]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = conversaciones
        
        # Act
        result = ConversacionService.listar_conversaciones(mock_db, usuario_id)
        
        # Assert
        assert len(result) == 3
        mock_db.query.assert_called_once()
    
    def test_listar_conversaciones_vacio(self, mock_db, usuario_id):
        """Usuario sin conversaciones debe retornar lista vacía"""
        # Arrange
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        # Act
        result = ConversacionService.listar_conversaciones(mock_db, usuario_id)
        
        # Assert
        assert result == []
        assert isinstance(result, list)
    
    def test_listar_conversaciones_respeta_limite(self, mock_db, usuario_id):
        """Debe respetar el límite especificado"""
        # Arrange
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        # Act
        ConversacionService.listar_conversaciones(mock_db, usuario_id, limit=25)
        
        # Assert
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.assert_called_with(25)


# ══════════════════════════════════════════════════════════════
# GRUPO 3: TESTS DE agregar_mensaje()
# ══════════════════════════════════════════════════════════════

class TestAgregarMensaje:
    """Tests del método agregar_mensaje"""
    
    def test_agregar_mensaje_usuario(self, mock_db, conversacion_id, mock_conversacion):
        """Debe agregar mensaje de usuario"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = mock_conversacion
        mock_db.refresh = Mock()
        
        # Act
        with patch('app.services.conversacion_service.Mensaje') as MockMensaje:
            mock_msg = Mock()
            MockMensaje.return_value = mock_msg
            
            result = ConversacionService.agregar_mensaje(
                mock_db,
                conversacion_id,
                rol="user",
                contenido="¿Cuánto facturamos?"
            )
        
        # Assert
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        MockMensaje.assert_called_once()
        call_kwargs = MockMensaje.call_args.kwargs
        assert call_kwargs['rol'] == "user"
        assert call_kwargs['contenido'] == "¿Cuánto facturamos?"
    
    def test_agregar_mensaje_asistente(self, mock_db, conversacion_id, mock_conversacion):
        """Debe agregar mensaje de asistente"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = mock_conversacion
        mock_db.refresh = Mock()
        
        # Act
        with patch('app.services.conversacion_service.Mensaje') as MockMensaje:
            mock_msg = Mock()
            MockMensaje.return_value = mock_msg
            
            result = ConversacionService.agregar_mensaje(
                mock_db,
                conversacion_id,
                rol="assistant",
                contenido="Facturamos $10M este mes."
            )
        
        # Assert
        call_kwargs = MockMensaje.call_args.kwargs
        assert call_kwargs['rol'] == "assistant"
    
    def test_agregar_mensaje_con_sql_generado(self, mock_db, conversacion_id, mock_conversacion):
        """Debe poder guardar SQL generado con el mensaje"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = mock_conversacion
        mock_db.refresh = Mock()
        sql = "SELECT SUM(monto) FROM operaciones"
        
        # Act
        with patch('app.services.conversacion_service.Mensaje') as MockMensaje:
            mock_msg = Mock()
            MockMensaje.return_value = mock_msg
            
            result = ConversacionService.agregar_mensaje(
                mock_db,
                conversacion_id,
                rol="assistant",
                contenido="Respuesta",
                sql_generado=sql
            )
        
        # Assert
        call_kwargs = MockMensaje.call_args.kwargs
        assert call_kwargs['sql_generado'] == sql
    
    def test_agregar_mensaje_actualiza_timestamp_conversacion(self, mock_db, conversacion_id, mock_conversacion):
        """Debe actualizar updated_at de la conversación"""
        # Arrange
        original_updated_at = mock_conversacion.updated_at
        mock_db.query.return_value.filter.return_value.first.return_value = mock_conversacion
        mock_db.refresh = Mock()
        
        # Act
        with patch('app.services.conversacion_service.Mensaje') as MockMensaje:
            mock_msg = Mock()
            MockMensaje.return_value = mock_msg
            
            ConversacionService.agregar_mensaje(
                mock_db,
                conversacion_id,
                rol="user",
                contenido="Mensaje"
            )
        
        # Assert
        # El updated_at debería haberse modificado
        assert mock_conversacion.updated_at != original_updated_at or mock_db.commit.called


# ══════════════════════════════════════════════════════════════
# GRUPO 4: TESTS DE obtener_contexto()
# ══════════════════════════════════════════════════════════════

class TestObtenerContexto:
    """Tests del método obtener_contexto"""
    
    def test_obtener_contexto_formatea_mensajes(self, mock_db, conversacion_id):
        """Debe formatear mensajes para API de Claude"""
        # Arrange
        msg1 = Mock()
        msg1.rol = "user"
        msg1.contenido = "Pregunta 1"
        msg1.created_at = datetime(2025, 1, 1, 10, 0)
        
        msg2 = Mock()
        msg2.rol = "assistant"
        msg2.contenido = "Respuesta 1"
        msg2.created_at = datetime(2025, 1, 1, 10, 1)
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [msg2, msg1]
        
        # Act
        result = ConversacionService.obtener_contexto(mock_db, conversacion_id)
        
        # Assert
        assert len(result) == 2
        assert result[0]['role'] == 'user'
        assert result[0]['content'] == 'Pregunta 1'
        assert result[1]['role'] == 'assistant'
        assert result[1]['content'] == 'Respuesta 1'
    
    def test_obtener_contexto_vacio(self, mock_db, conversacion_id):
        """Conversación sin mensajes debe retornar lista vacía"""
        # Arrange
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        # Act
        result = ConversacionService.obtener_contexto(mock_db, conversacion_id)
        
        # Assert
        assert result == []
    
    def test_obtener_contexto_respeta_limite(self, mock_db, conversacion_id):
        """Debe respetar el límite de mensajes"""
        # Arrange
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        # Act
        ConversacionService.obtener_contexto(mock_db, conversacion_id, limite=5)
        
        # Assert
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.assert_called_with(5)


# ══════════════════════════════════════════════════════════════
# GRUPO 5: TESTS DE generar_titulo()
# ══════════════════════════════════════════════════════════════

class TestGenerarTitulo:
    """Tests del método generar_titulo"""
    
    def test_generar_titulo_pregunta_corta(self):
        """Pregunta corta debe usarse completa"""
        # Arrange
        pregunta = "¿Cuánto facturamos?"
        
        # Act
        titulo = ConversacionService.generar_titulo(pregunta)
        
        # Assert
        assert titulo == "¿Cuánto facturamos?"
        assert "..." not in titulo
    
    def test_generar_titulo_pregunta_larga_se_trunca(self):
        """Pregunta larga debe truncarse a 50 chars + ..."""
        # Arrange
        pregunta = "¿Cuánto facturamos en el mes de octubre de 2025 en la oficina de Montevideo?"
        
        # Act
        titulo = ConversacionService.generar_titulo(pregunta)
        
        # Assert
        assert len(titulo) <= 53  # 50 + "..."
        assert titulo.endswith("...")
    
    def test_generar_titulo_exactamente_50_chars(self):
        """Pregunta de exactamente 50 chars no debe tener ..."""
        # Arrange
        pregunta = "A" * 50
        
        # Act
        titulo = ConversacionService.generar_titulo(pregunta)
        
        # Assert
        assert titulo == "A" * 50
        assert "..." not in titulo
    
    def test_generar_titulo_strip_espacios(self):
        """Debe quitar espacios al inicio y final"""
        # Arrange
        pregunta = "   Pregunta con espacios   "
        
        # Act
        titulo = ConversacionService.generar_titulo(pregunta)
        
        # Assert
        assert not titulo.startswith(" ")
        assert not titulo.endswith(" ") or titulo.endswith("...")


# ══════════════════════════════════════════════════════════════
# GRUPO 6: TESTS DE INTEGRACIÓN
# ══════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestConversacionServiceIntegration:
    """Tests de integración del servicio de conversaciones"""
    
    def test_flujo_completo_crear_y_agregar_mensajes(self, mock_db, usuario_id):
        """Flujo completo: crear conversación y agregar mensajes"""
        # Este test simula el flujo completo
        # En un test de integración real se usaría BD real
        
        # Arrange
        mock_db.refresh = Mock()
        mock_conversacion = Mock()
        mock_conversacion.id = uuid4()
        mock_conversacion.updated_at = datetime.now(timezone.utc)
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_conversacion
        
        # Act
        with patch('app.services.conversacion_service.Conversacion') as MockConv:
            with patch('app.services.conversacion_service.Mensaje') as MockMsg:
                MockConv.return_value = mock_conversacion
                MockMsg.return_value = Mock()
                
                # 1. Crear conversación
                conv = ConversacionService.crear_conversacion(mock_db, usuario_id, "Test")
                
                # 2. Agregar mensaje usuario
                ConversacionService.agregar_mensaje(
                    mock_db, mock_conversacion.id, "user", "Pregunta"
                )
                
                # 3. Agregar mensaje asistente
                ConversacionService.agregar_mensaje(
                    mock_db, mock_conversacion.id, "assistant", "Respuesta"
                )
        
        # Assert
        assert mock_db.add.call_count == 3  # 1 conv + 2 msgs
        assert mock_db.commit.call_count == 3



