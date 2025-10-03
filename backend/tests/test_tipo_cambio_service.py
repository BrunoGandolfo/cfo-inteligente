"""
Suite de Tests para TipoCambioService - Sistema CFO Inteligente

Tests del servicio de tipo de cambio USD/UYU.
Valida cache, llamadas API DolarApi, y fallback en caso de error.

Ejecutar:
    cd backend
    pytest tests/test_tipo_cambio_service.py -v
    pytest tests/test_tipo_cambio_service.py --cov=app/services/tipo_cambio_service --cov-report=term-missing

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from app.services import tipo_cambio_service
from app.services.tipo_cambio_service import obtener_tipo_cambio_actual


# ══════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def limpiar_cache():
    """Fixture que limpia el cache antes de cada test"""
    tipo_cambio_service._cache = {
        "compra": None,
        "venta": None,
        "promedio": None,
        "timestamp": None,
        "fuente": None
    }
    yield
    # Cleanup después del test
    tipo_cambio_service._cache = {
        "compra": None,
        "venta": None,
        "promedio": None,
        "timestamp": None,
        "fuente": None
    }


# ══════════════════════════════════════════════════════════════
# TESTS: Cache - Sistema de caché 24 horas
# ══════════════════════════════════════════════════════════════

class TestCache:
    """Tests del sistema de caché de tipo de cambio"""
    
    @patch('requests.get')
    def test_cache_evita_llamada_api_repetida(self, mock_get):
        """Segunda llamada debe usar cache sin llamar API"""
        # Mock de respuesta API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "compra": 40.10,
            "venta": 40.60
        }
        mock_get.return_value = mock_response
        
        # Primera llamada - debe llamar API
        resultado1 = obtener_tipo_cambio_actual()
        assert mock_get.call_count == 1
        assert resultado1['promedio'] == 40.35  # (40.10 + 40.60) / 2
        assert resultado1['fuente'] == 'DolarApi'
        
        # Segunda llamada - debe usar cache
        resultado2 = obtener_tipo_cambio_actual()
        assert mock_get.call_count == 1  # NO aumenta
        assert resultado2['promedio'] == 40.35
        assert resultado2['fuente'] == 'DolarApi'
    
    @patch('requests.get')
    def test_cache_expira_despues_24_horas(self, mock_get):
        """Cache debe expirar después de 24 horas"""
        # Mock respuesta API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"compra": 40.00, "venta": 40.50}
        mock_get.return_value = mock_response
        
        # Primera llamada
        resultado1 = obtener_tipo_cambio_actual()
        assert mock_get.call_count == 1
        
        # Simular que pasaron 25 horas
        tipo_cambio_service._cache["timestamp"] = datetime.now() - timedelta(hours=25)
        
        # Segunda llamada - debe llamar API de nuevo
        resultado2 = obtener_tipo_cambio_actual()
        assert mock_get.call_count == 2  # Llamó API de nuevo
    
    def test_cache_retorna_todos_valores(self):
        """Cache debe retornar compra, venta, promedio, fuente, actualizado"""
        # Setear cache manualmente
        tipo_cambio_service._cache = {
            "compra": 40.10,
            "venta": 40.60,
            "promedio": 40.35,
            "timestamp": datetime.now(),
            "fuente": "DolarApi"
        }
        
        resultado = obtener_tipo_cambio_actual()
        
        assert "compra" in resultado
        assert "venta" in resultado
        assert "promedio" in resultado
        assert "fuente" in resultado
        assert "actualizado" in resultado
        assert resultado['compra'] == 40.10
        assert resultado['venta'] == 40.60
        assert resultado['promedio'] == 40.35


# ══════════════════════════════════════════════════════════════
# TESTS: API DolarApi - Llamadas HTTP
# ══════════════════════════════════════════════════════════════

class TestAPIDolarApi:
    """Tests de integración con DolarApi"""
    
    @patch('requests.get')
    def test_llamada_api_exitosa(self, mock_get):
        """Debe parsear correctamente respuesta DolarApi"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "compra": 40.20,
            "venta": 40.70,
            "fecha": "2025-10-03"
        }
        mock_get.return_value = mock_response
        
        resultado = obtener_tipo_cambio_actual()
        
        assert resultado['compra'] == 40.20
        assert resultado['venta'] == 40.70
        assert resultado['promedio'] == 40.45  # (40.20 + 40.70) / 2
        assert resultado['fuente'] == 'DolarApi'
        
        # Verificar que se llamó al endpoint correcto
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "uy.dolarapi.com" in args[0]
        assert "timeout" in kwargs
    
    @patch('requests.get')
    def test_api_actualiza_cache(self, mock_get):
        """Llamada exitosa debe actualizar cache"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "compra": 39.90,
            "venta": 40.40
        }
        mock_get.return_value = mock_response
        
        # Llamar API
        resultado = obtener_tipo_cambio_actual()
        
        # Verificar que cache se actualizó
        assert tipo_cambio_service._cache['compra'] == 39.90
        assert tipo_cambio_service._cache['venta'] == 40.40
        assert tipo_cambio_service._cache['promedio'] == 40.15
        assert tipo_cambio_service._cache['fuente'] == 'DolarApi'
        assert tipo_cambio_service._cache['timestamp'] is not None
    
    @patch('requests.get')
    def test_api_calcula_promedio_correcto(self, mock_get):
        """Promedio debe ser (compra + venta) / 2"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "compra": 38.50,
            "venta": 39.50
        }
        mock_get.return_value = mock_response
        
        resultado = obtener_tipo_cambio_actual()
        
        # (38.50 + 39.50) / 2 = 39.00
        assert resultado['promedio'] == 39.00


# ══════════════════════════════════════════════════════════════
# TESTS: Fallback - Cuando API falla
# ══════════════════════════════════════════════════════════════

class TestFallback:
    """Tests de mecanismo de fallback cuando API falla"""
    
    @patch('requests.get')
    def test_fallback_si_api_timeout(self, mock_get):
        """Si API hace timeout, usar fallback"""
        mock_get.side_effect = requests.exceptions.Timeout("API timeout")
        
        resultado = obtener_tipo_cambio_actual()
        
        # Debe retornar valores fallback
        assert resultado['compra'] == 40.00
        assert resultado['venta'] == 40.50
        assert resultado['promedio'] == 40.25
        assert resultado['fuente'] == 'fallback'
    
    @patch('requests.get')
    def test_fallback_si_api_connection_error(self, mock_get):
        """Si no hay conexión, usar fallback"""
        mock_get.side_effect = requests.exceptions.ConnectionError("No internet")
        
        resultado = obtener_tipo_cambio_actual()
        
        assert resultado['compra'] == 40.00
        assert resultado['venta'] == 40.50
        assert resultado['promedio'] == 40.25
        assert resultado['fuente'] == 'fallback'
    
    @patch('requests.get')
    def test_fallback_si_api_500(self, mock_get):
        """Si API retorna 500, usar fallback"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        resultado = obtener_tipo_cambio_actual()
        
        assert resultado['promedio'] == 40.25
        assert resultado['fuente'] == 'fallback'
    
    @patch('requests.get')
    def test_fallback_si_api_response_invalida(self, mock_get):
        """Si respuesta JSON inválida, usar fallback"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("JSON inválido")
        mock_get.return_value = mock_response
        
        resultado = obtener_tipo_cambio_actual()
        
        assert resultado['promedio'] == 40.25
        assert resultado['fuente'] == 'fallback'
    
    @patch('requests.get')
    def test_fallback_valores_razonables(self, mock_get):
        """Valores fallback deben estar en rango razonable (30-50)"""
        mock_get.side_effect = Exception("API caída")
        
        resultado = obtener_tipo_cambio_actual()
        
        assert 30 < resultado['compra'] < 50
        assert 30 < resultado['venta'] < 50
        assert 30 < resultado['promedio'] < 50


# ══════════════════════════════════════════════════════════════
# TESTS: Casos Edge
# ══════════════════════════════════════════════════════════════

class TestCasosEdge:
    """Tests de casos extremos"""
    
    @patch('requests.get')
    def test_api_retorna_valores_none(self, mock_get):
        """Si API retorna None en campos, usar fallback"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "compra": None,
            "venta": None
        }
        mock_get.return_value = mock_response
        
        resultado = obtener_tipo_cambio_actual()
        
        # Debe usar valores fallback porque compra/venta son None
        # O usar .get(key, default) en el código
        assert resultado['promedio'] > 0
    
    @patch('requests.get')
    def test_api_retorna_json_vacio(self, mock_get):
        """Si API retorna JSON vacío, usar fallback"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response
        
        resultado = obtener_tipo_cambio_actual()
        
        # Código usa .get(key, default) entonces debería funcionar
        assert resultado['promedio'] > 0
    
    def test_cache_timestamp_none_no_crashea(self):
        """Si timestamp es None, debe funcionar"""
        tipo_cambio_service._cache["promedio"] = 40.25
        tipo_cambio_service._cache["timestamp"] = None
        
        # No debe usar cache si timestamp es None
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"compra": 40.00, "venta": 40.50}
            mock_get.return_value = mock_response
            
            resultado = obtener_tipo_cambio_actual()
            
            # Debe haber llamado API (no usó cache inválido)
            assert mock_get.called

