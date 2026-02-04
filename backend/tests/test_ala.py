"""
Suite de Tests para Módulo ALA (Anti-Lavado de Activos) - Sistema CFO Inteligente

Tests completos para:
1. Parser de listas (funciones puras, sin BD, sin red)
2. Verificaciones con listas mock
3. Clasificación de riesgo
4. Endpoints REST

Ejecutar:
    cd backend
    pytest tests/test_ala.py -v
    pytest tests/test_ala.py -v --cov=app.services.ala_list_parser --cov=app.services.ala_service --cov=app.api.ala

Autor: Sistema CFO Inteligente
Fecha: Febrero 2026
"""

import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
from datetime import datetime, timezone, date

from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.core.security import get_current_user
from app.services.ala_list_parser import (
    normalizar_texto,
    normalizar_ci,
    similitud_nombres,
    verificar_pais_gafi,
    verificar_pep,
    verificar_onu,
    verificar_ofac,
    verificar_ue,
    UMBRAL_SIMILITUD,
)
from app.services.ala_service import _clasificar_riesgo


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_usuario_socio():
    """Mock de usuario socio para endpoints"""
    usuario = Mock()
    usuario.id = uuid4()
    usuario.email = "socio@grupoconexion.uy"
    usuario.nombre = "Socio Test"
    usuario.es_socio = True
    usuario.activo = True
    return usuario


@pytest.fixture
def mock_usuario_colaborador():
    """Mock de usuario colaborador (no socio) para endpoints"""
    usuario = Mock()
    usuario.id = uuid4()
    usuario.email = "colaborador@grupoconexion.uy"
    usuario.nombre = "Colaborador Test"
    usuario.es_socio = False
    usuario.activo = True
    return usuario


@pytest.fixture
def client_socio(mock_usuario_socio):
    """Cliente de FastAPI con usuario socio mockeado"""
    mock_db = Mock()
    
    def override_get_db():
        return mock_db
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: mock_usuario_socio
    
    with TestClient(app) as test_client:
        yield test_client, mock_db, mock_usuario_socio
    
    app.dependency_overrides.clear()


@pytest.fixture
def client_colaborador(mock_usuario_colaborador):
    """Cliente de FastAPI con usuario colaborador mockeado"""
    mock_db = Mock()
    
    def override_get_db():
        return mock_db
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: mock_usuario_colaborador
    
    with TestClient(app) as test_client:
        yield test_client, mock_db, mock_usuario_colaborador
    
    app.dependency_overrides.clear()


@pytest.fixture
def client_sin_auth():
    """Cliente de FastAPI sin autenticación"""
    app.dependency_overrides.clear()
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def lista_pep_mock():
    """Lista PEP mock para tests"""
    return {
        "registros": [
            {"CI": "12345678", "NOMBRE": "JUAN PEREZ GARCIA", "CARGO": "Director", "ORGANISMO": "BPS"},
            {"CI": "99999999", "NOMBRE": "MARIA RODRIGUEZ LOPEZ", "CARGO": "Gerente", "ORGANISMO": "MEF"},
            {"CI": "11111111", "NOMBRE": "CARLOS ALBERTO GONZALEZ", "CARGO": "Asesor", "ORGANISMO": "BCU"},
        ],
        "hash": "abc123mock",
        "total": 3
    }


@pytest.fixture
def lista_onu_mock():
    """Lista ONU mock con elementos XML simulados como dicts de nombres"""
    # Simulamos la estructura de individuos procesados
    return {
        "individuos": [
            Mock(**{"iter": lambda self=None: iter([
                Mock(tag="FIRST_NAME", text="MOHAMMED"),
                Mock(tag="SECOND_NAME", text="AL"),
                Mock(tag="THIRD_NAME", text="RASHID"),
            ])}),
        ],
        "hash": "onu123mock",
        "total": 1
    }


@pytest.fixture
def lista_ofac_mock():
    """Lista OFAC mock para tests"""
    return {
        "registros": [
            ["KIM", "JONG", "UN"],
            ["VLADIMIR", "IVANOV", "PETROV"],
        ],
        "hash": "ofac123mock",
        "total": 2
    }


@pytest.fixture
def lista_ue_mock():
    """Lista UE mock para tests"""
    return {
        "registros": [
            "VLADIMIR PUTIN",
            "SERGEI LAVROV",
            "ALEXANDER LUKASHENKO",
        ],
        "hash": "ue123mock",
        "total": 3
    }


# =============================================================================
# SECCIÓN 1: Tests del parser (funciones puras, sin BD, sin red)
# =============================================================================

class TestNormalizarTexto:
    """Tests de normalizar_texto"""
    
    def test_normalizar_texto_basico(self):
        """Texto con acentos se normaliza a mayúsculas sin acentos"""
        assert normalizar_texto("José María García") == "JOSE MARIA GARCIA"
    
    def test_normalizar_texto_espacios_multiples(self):
        """Espacios múltiples se reducen a uno"""
        assert normalizar_texto("  Juan   Pedro  ") == "JUAN PEDRO"
    
    def test_normalizar_texto_vacio(self):
        """Texto vacío retorna vacío"""
        assert normalizar_texto("") == ""
    
    def test_normalizar_texto_none(self):
        """None retorna vacío"""
        assert normalizar_texto(None) == ""
    
    def test_normalizar_texto_caracteres_especiales(self):
        """Caracteres especiales se eliminan o normalizan"""
        assert normalizar_texto("María José Ñoño") == "MARIA JOSE NONO"
    
    def test_normalizar_texto_ya_mayusculas(self):
        """Texto ya en mayúsculas sin cambios innecesarios"""
        assert normalizar_texto("JUAN PEREZ") == "JUAN PEREZ"


class TestNormalizarCI:
    """Tests de normalizar_ci"""
    
    def test_normalizar_ci_con_puntos_guion(self):
        """CI con puntos y guión se limpia"""
        assert normalizar_ci("2.867.747-5") == "28677475"
    
    def test_normalizar_ci_solo_digitos(self):
        """CI solo dígitos sin cambios"""
        assert normalizar_ci("28677475") == "28677475"
    
    def test_normalizar_ci_vacia(self):
        """CI vacía retorna vacío"""
        assert normalizar_ci("") == ""
    
    def test_normalizar_ci_none(self):
        """CI None retorna vacío"""
        assert normalizar_ci(None) == ""
    
    def test_normalizar_ci_con_letras(self):
        """CI con letras solo mantiene dígitos"""
        assert normalizar_ci("CI: 12345678") == "12345678"
    
    def test_normalizar_ci_espacios(self):
        """CI con espacios los elimina"""
        assert normalizar_ci("1 234 567 8") == "12345678"


class TestSimilitudNombres:
    """Tests de similitud_nombres (Jaccard sobre palabras)"""
    
    def test_similitud_identicos(self):
        """Nombres idénticos tienen similitud 1.0"""
        assert similitud_nombres("JUAN PEREZ", "JUAN PEREZ") == 1.0
    
    def test_similitud_orden_invertido(self):
        """Orden invertido tiene similitud 1.0 (Jaccard es set)"""
        assert similitud_nombres("JUAN PEREZ", "PEREZ JUAN") == 1.0
    
    def test_similitud_completamente_distintos(self):
        """Nombres completamente distintos tienen similitud 0.0"""
        assert similitud_nombres("JUAN PEREZ", "CARLOS GOMEZ") == 0.0
    
    def test_similitud_parcial(self):
        """Nombres con coincidencia parcial"""
        # JUAN PABLO PEREZ vs JUAN PEREZ
        # Set1: {JUAN, PABLO, PEREZ}, Set2: {JUAN, PEREZ}
        # Intersección: {JUAN, PEREZ} = 2, Unión: {JUAN, PABLO, PEREZ} = 3
        # Jaccard = 2/3 ≈ 0.67
        sim = similitud_nombres("JUAN PABLO PEREZ", "JUAN PEREZ")
        assert 0.6 <= sim <= 0.7
    
    def test_similitud_vacio_vacio(self):
        """Dos vacíos retornan 0.0"""
        assert similitud_nombres("", "") == 0.0
    
    def test_similitud_uno_vacio(self):
        """Un nombre vacío retorna 0.0"""
        assert similitud_nombres("JUAN PEREZ", "") == 0.0
        assert similitud_nombres("", "JUAN PEREZ") == 0.0
    
    def test_similitud_case_insensitive(self):
        """La función normaliza internamente"""
        sim = similitud_nombres("juan perez", "JUAN PEREZ")
        assert sim == 1.0


class TestVerificarPaisGafi:
    """Tests de verificar_pais_gafi"""
    
    def test_gafi_alto_riesgo_iran(self):
        """Irán es alto riesgo GAFI"""
        r = verificar_pais_gafi("IR")
        assert r["nivel"] == "ALTO"
        assert r["codigo"] == "IR"
    
    def test_gafi_alto_riesgo_corea_norte(self):
        """Corea del Norte es alto riesgo GAFI"""
        r = verificar_pais_gafi("KP")
        assert r["nivel"] == "ALTO"
    
    def test_gafi_alto_riesgo_myanmar(self):
        """Myanmar es alto riesgo GAFI"""
        r = verificar_pais_gafi("MM")
        assert r["nivel"] == "ALTO"
    
    def test_gafi_grey_list_siria(self):
        """Siria está en grey list"""
        r = verificar_pais_gafi("SY")
        assert r["nivel"] == "MEDIO"
    
    def test_gafi_grey_list_pakistan(self):
        """Pakistán está en grey list"""
        r = verificar_pais_gafi("PK")
        assert r["nivel"] == "MEDIO"
    
    def test_gafi_pais_limpio_uruguay(self):
        """Uruguay no tiene riesgo GAFI"""
        r = verificar_pais_gafi("UY")
        assert r["nivel"] == "NINGUNO"
        assert r["codigo"] == "UY"
    
    def test_gafi_pais_limpio_argentina(self):
        """Argentina no tiene riesgo GAFI"""
        r = verificar_pais_gafi("AR")
        assert r["nivel"] == "NINGUNO"
    
    def test_gafi_none(self):
        """None retorna NINGUNO sin explotar"""
        r = verificar_pais_gafi(None)
        assert r["nivel"] == "NINGUNO"
        assert r["codigo"] == ""
    
    def test_gafi_vacio(self):
        """Código vacío retorna NINGUNO"""
        r = verificar_pais_gafi("")
        assert r["nivel"] == "NINGUNO"
    
    def test_gafi_case_insensitive(self):
        """Código en minúsculas funciona"""
        r = verificar_pais_gafi("ir")
        assert r["nivel"] == "ALTO"


# =============================================================================
# SECCIÓN 2: Tests de verificación con listas mock
# =============================================================================

class TestVerificarPEP:
    """Tests de verificar_pep con lista mock"""
    
    def test_verificar_pep_match_ci_exacta(self, lista_pep_mock):
        """Match por CI exacta"""
        resultado = verificar_pep("12345678", "CUALQUIER NOMBRE", lista_pep_mock)
        assert resultado["es_pep"] is True
        assert resultado["match_tipo"] == "CI_EXACTA"
        assert resultado["similitud"] == 1.0
        assert "JUAN PEREZ GARCIA" in resultado["mejor_match"]
    
    def test_verificar_pep_match_ci_con_formato(self, lista_pep_mock):
        """Match por CI con puntos y guión"""
        resultado = verificar_pep("1.234.567-8", "CUALQUIER", lista_pep_mock)
        assert resultado["es_pep"] is True
        assert resultado["match_tipo"] == "CI_EXACTA"
    
    def test_verificar_pep_match_nombre_fuzzy(self, lista_pep_mock):
        """Match por nombre fuzzy cuando CI no coincide"""
        resultado = verificar_pep("00000000", "JUAN PEREZ GARCIA", lista_pep_mock)
        assert resultado["es_pep"] is True
        assert resultado["match_tipo"] == "NOMBRE_FUZZY"
        assert resultado["similitud"] >= UMBRAL_SIMILITUD
    
    def test_verificar_pep_sin_match(self, lista_pep_mock):
        """Sin match cuando no hay coincidencia"""
        resultado = verificar_pep("00000000", "BRUNO GANDOLFO SILVA", lista_pep_mock)
        assert resultado["es_pep"] is False
        assert resultado["match_tipo"] == "NO_MATCH"
    
    def test_verificar_pep_lista_vacia(self):
        """Lista vacía retorna no PEP"""
        lista_mock = {"registros": [], "hash": "abc", "total": 0}
        resultado = verificar_pep("12345678", "JUAN PEREZ", lista_mock)
        assert resultado["es_pep"] is False
        assert resultado["match_tipo"] == "NO_MATCH"
    
    def test_verificar_pep_lista_none(self):
        """Lista None retorna error"""
        resultado = verificar_pep("12345678", "JUAN PEREZ", None)
        assert resultado["es_pep"] is False
        assert resultado["error"] is not None
    
    def test_verificar_pep_sin_registros_key(self):
        """Lista sin key registros retorna error"""
        resultado = verificar_pep("12345678", "JUAN PEREZ", {"hash": "abc"})
        assert resultado["es_pep"] is False
        assert resultado["error"] is not None


class TestVerificarOFAC:
    """Tests de verificar_ofac con lista mock"""
    
    def test_verificar_ofac_match(self, lista_ofac_mock):
        """Match en lista OFAC"""
        resultado = verificar_ofac("KIM JONG UN", lista_ofac_mock)
        assert resultado["en_lista"] is True
        assert resultado["similitud"] >= UMBRAL_SIMILITUD
    
    def test_verificar_ofac_sin_match(self, lista_ofac_mock):
        """Sin match en lista OFAC"""
        resultado = verificar_ofac("BRUNO GANDOLFO", lista_ofac_mock)
        assert resultado["en_lista"] is False
    
    def test_verificar_ofac_lista_none(self):
        """Lista None retorna error"""
        resultado = verificar_ofac("JUAN PEREZ", None)
        assert resultado["en_lista"] is False
        assert resultado["error"] is not None
    
    def test_verificar_ofac_match_parcial_bajo_umbral(self, lista_ofac_mock):
        """Match parcial bajo umbral no cuenta como hit"""
        resultado = verificar_ofac("KIM", lista_ofac_mock)
        # Solo "KIM" no debería alcanzar umbral 0.85
        assert resultado["en_lista"] is False


class TestVerificarUE:
    """Tests de verificar_ue con lista mock"""
    
    def test_verificar_ue_match(self, lista_ue_mock):
        """Match en lista UE"""
        resultado = verificar_ue("VLADIMIR PUTIN", lista_ue_mock)
        assert resultado["en_lista"] is True
        assert resultado["similitud"] >= UMBRAL_SIMILITUD
    
    def test_verificar_ue_sin_match(self, lista_ue_mock):
        """Sin match en lista UE"""
        resultado = verificar_ue("BRUNO GANDOLFO", lista_ue_mock)
        assert resultado["en_lista"] is False
    
    def test_verificar_ue_match_orden_diferente(self, lista_ue_mock):
        """Match con orden de palabras diferente"""
        resultado = verificar_ue("PUTIN VLADIMIR", lista_ue_mock)
        assert resultado["en_lista"] is True
    
    def test_verificar_ue_lista_none(self):
        """Lista None retorna error"""
        resultado = verificar_ue("JUAN PEREZ", None)
        assert resultado["en_lista"] is False
        assert resultado["error"] is not None


# =============================================================================
# SECCIÓN 3: Tests de clasificación de riesgo
# =============================================================================

class TestClasificarRiesgo:
    """Tests de _clasificar_riesgo"""
    
    def test_clasificar_bajo_limpio(self):
        """Persona limpia = BAJO + SIMPLIFICADA + puede operar"""
        r = _clasificar_riesgo(
            resultado_pep={"es_pep": False},
            resultado_onu={"en_lista": False},
            resultado_ofac={"en_lista": False},
            resultado_ue={"en_lista": False},
            resultado_gafi={"nivel": "NINGUNO"},
            listas_fallidas=[]
        )
        assert r["nivel_riesgo"] == "BAJO"
        assert r["nivel_diligencia"] == "SIMPLIFICADA"
        assert r["puede_operar"] is True
    
    def test_clasificar_pep_puede_operar(self):
        """PEP = ALTO + INTENSIFICADA pero PUEDE operar (Art. 44)"""
        r = _clasificar_riesgo(
            resultado_pep={"es_pep": True},
            resultado_onu={"en_lista": False},
            resultado_ofac={"en_lista": False},
            resultado_ue={"en_lista": False},
            resultado_gafi={"nivel": "NINGUNO"},
            listas_fallidas=[]
        )
        assert r["nivel_riesgo"] == "ALTO"
        assert r["nivel_diligencia"] == "INTENSIFICADA"
        assert r["puede_operar"] is True
        assert any("PEP" in f for f in r["factores"])
    
    def test_clasificar_onu_bloqueo(self):
        """Match ONU = CRITICO + NO puede operar"""
        r = _clasificar_riesgo(
            resultado_pep={"es_pep": False},
            resultado_onu={"en_lista": True},
            resultado_ofac={"en_lista": False},
            resultado_ue={"en_lista": False},
            resultado_gafi={"nivel": "NINGUNO"},
            listas_fallidas=[]
        )
        assert r["nivel_riesgo"] == "CRITICO"
        assert r["puede_operar"] is False
        assert any("ONU" in f for f in r["factores"])
    
    def test_clasificar_ofac_bloqueo(self):
        """Match OFAC = CRITICO + NO puede operar"""
        r = _clasificar_riesgo(
            resultado_pep={"es_pep": False},
            resultado_onu={"en_lista": False},
            resultado_ofac={"en_lista": True},
            resultado_ue={"en_lista": False},
            resultado_gafi={"nivel": "NINGUNO"},
            listas_fallidas=[]
        )
        assert r["nivel_riesgo"] == "CRITICO"
        assert r["puede_operar"] is False
        assert any("OFAC" in f for f in r["factores"])
    
    def test_clasificar_ue_bloqueo(self):
        """Match UE = CRITICO + NO puede operar"""
        r = _clasificar_riesgo(
            resultado_pep={"es_pep": False},
            resultado_onu={"en_lista": False},
            resultado_ofac={"en_lista": False},
            resultado_ue={"en_lista": True},
            resultado_gafi={"nivel": "NINGUNO"},
            listas_fallidas=[]
        )
        assert r["nivel_riesgo"] == "CRITICO"
        assert r["puede_operar"] is False
        assert any("UE" in f for f in r["factores"])
    
    def test_clasificar_gafi_alto(self):
        """País GAFI alto riesgo = ALTO + INTENSIFICADA + puede operar"""
        r = _clasificar_riesgo(
            resultado_pep={"es_pep": False},
            resultado_onu={"en_lista": False},
            resultado_ofac={"en_lista": False},
            resultado_ue={"en_lista": False},
            resultado_gafi={"nivel": "ALTO"},
            listas_fallidas=[]
        )
        assert r["nivel_riesgo"] == "ALTO"
        assert r["nivel_diligencia"] == "INTENSIFICADA"
        assert r["puede_operar"] is True
    
    def test_clasificar_gafi_medio(self):
        """País GAFI grey list = MEDIO + NORMAL + puede operar"""
        r = _clasificar_riesgo(
            resultado_pep={"es_pep": False},
            resultado_onu={"en_lista": False},
            resultado_ofac={"en_lista": False},
            resultado_ue={"en_lista": False},
            resultado_gafi={"nivel": "MEDIO"},
            listas_fallidas=[]
        )
        assert r["nivel_riesgo"] == "MEDIO"
        assert r["nivel_diligencia"] == "NORMAL"
        assert r["puede_operar"] is True
    
    def test_clasificar_bajo_lista_fallida_no_simplificada(self):
        """Si una lista falló, no se otorga SIMPLIFICADA"""
        r = _clasificar_riesgo(
            resultado_pep={"es_pep": False},
            resultado_onu={"en_lista": False},
            resultado_ofac={"en_lista": False},
            resultado_ue={"en_lista": False},
            resultado_gafi={"nivel": "NINGUNO"},
            listas_fallidas=["UE"]
        )
        assert r["nivel_riesgo"] == "BAJO"
        assert r["nivel_diligencia"] == "NORMAL"  # No SIMPLIFICADA
        assert r["puede_operar"] is True
    
    def test_clasificar_multiples_sanciones(self):
        """Múltiples sanciones sigue siendo CRITICO"""
        r = _clasificar_riesgo(
            resultado_pep={"es_pep": True},
            resultado_onu={"en_lista": True},
            resultado_ofac={"en_lista": True},
            resultado_ue={"en_lista": False},
            resultado_gafi={"nivel": "ALTO"},
            listas_fallidas=[]
        )
        assert r["nivel_riesgo"] == "CRITICO"
        assert r["puede_operar"] is False
    
    def test_clasificar_resultados_none(self):
        """Resultados None se manejan sin error"""
        r = _clasificar_riesgo(
            resultado_pep=None,
            resultado_onu=None,
            resultado_ofac=None,
            resultado_ue=None,
            resultado_gafi=None,
            listas_fallidas=["PEP", "ONU", "OFAC", "UE"]
        )
        assert r["nivel_riesgo"] == "BAJO"
        assert r["nivel_diligencia"] == "NORMAL"  # Listas fallidas
        assert r["puede_operar"] is True
    
    def test_clasificar_sancion_prevalece_sobre_pep(self):
        """Sanción (CRITICO) prevalece sobre PEP (ALTO)"""
        r = _clasificar_riesgo(
            resultado_pep={"es_pep": True},
            resultado_onu={"en_lista": True},
            resultado_ofac={"en_lista": False},
            resultado_ue={"en_lista": False},
            resultado_gafi={"nivel": "NINGUNO"},
            listas_fallidas=[]
        )
        assert r["nivel_riesgo"] == "CRITICO"
        assert r["puede_operar"] is False


# =============================================================================
# SECCIÓN 4: Tests de API endpoints
# =============================================================================

class TestEndpointVerificar:
    """Tests del endpoint POST /api/ala/verificar"""
    
    def test_verificar_requiere_auth(self, client_sin_auth):
        """Sin token retorna 401"""
        response = client_sin_auth.post("/api/ala/verificar", json={
            "nombre_completo": "Juan Perez"
        })
        assert response.status_code == 401
    
    @patch("app.api.ala.ala_service.ejecutar_verificacion_completa")
    def test_verificar_ok(self, mock_ejecutar, client_socio):
        """Verificación exitosa retorna 201"""
        test_client, mock_db, mock_user = client_socio
        
        # Crear mock de verificación completa
        mock_verificacion = Mock()
        mock_verificacion.id = uuid4()
        mock_verificacion.nombre_completo = "Bruno Gandolfo"
        mock_verificacion.tipo_documento = "CI"
        mock_verificacion.numero_documento = "28677475"
        mock_verificacion.nacionalidad = "UY"
        mock_verificacion.fecha_nacimiento = None
        mock_verificacion.es_persona_juridica = False
        mock_verificacion.razon_social = None
        mock_verificacion.nivel_diligencia = "SIMPLIFICADA"
        mock_verificacion.nivel_riesgo = "BAJO"
        mock_verificacion.es_pep = False
        ts = datetime.now(timezone.utc).isoformat()
        mock_verificacion.resultado_onu = {"checked": True, "hits": 0, "timestamp": ts}
        mock_verificacion.resultado_pep = {"checked": True, "hits": 0, "timestamp": ts}
        mock_verificacion.resultado_ofac = {"checked": True, "hits": 0, "timestamp": ts}
        mock_verificacion.resultado_ue = {"checked": True, "hits": 0, "timestamp": ts}
        mock_verificacion.resultado_gafi = {"checked": True, "hits": 0, "timestamp": ts}
        mock_verificacion.busqueda_google_realizada = False
        mock_verificacion.busqueda_google_observaciones = None
        mock_verificacion.busqueda_news_realizada = False
        mock_verificacion.busqueda_news_observaciones = None
        mock_verificacion.busqueda_wikipedia_realizada = False
        mock_verificacion.busqueda_wikipedia_observaciones = None
        mock_verificacion.hash_verificacion = "abc123hash"
        mock_verificacion.certificado_pdf_path = None
        mock_verificacion.expediente_id = None
        mock_verificacion.contrato_id = None
        mock_verificacion.usuario_id = mock_user.id
        mock_verificacion.created_at = datetime.now(timezone.utc)
        mock_verificacion.updated_at = None
        mock_verificacion.deleted_at = None
        
        mock_ejecutar.return_value = mock_verificacion
        
        response = test_client.post("/api/ala/verificar", json={
            "nombre_completo": "Bruno Gandolfo",
            "tipo_documento": "CI",
            "numero_documento": "28677475",
            "nacionalidad": "UY",
            "es_persona_juridica": False
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["nombre_completo"] == "Bruno Gandolfo"
        assert data["nivel_riesgo"] == "BAJO"
    
    def test_verificar_nombre_invalido_muy_corto(self, client_socio):
        """Nombre muy corto retorna 422"""
        test_client, mock_db, mock_user = client_socio
        
        response = test_client.post("/api/ala/verificar", json={
            "nombre_completo": "A"
        })
        
        assert response.status_code == 422
    
    def test_verificar_nombre_vacio(self, client_socio):
        """Nombre vacío retorna 422"""
        test_client, mock_db, mock_user = client_socio
        
        response = test_client.post("/api/ala/verificar", json={
            "nombre_completo": ""
        })
        
        assert response.status_code == 422


class TestEndpointListar:
    """Tests del endpoint GET /api/ala/verificaciones"""
    
    def test_listar_requiere_auth(self, client_sin_auth):
        """Sin token retorna 401"""
        response = client_sin_auth.get("/api/ala/verificaciones")
        assert response.status_code == 401
    
    @patch("app.services.ala_service.listar_verificaciones")
    def test_listar_ok_socio(self, mock_listar, client_socio):
        """Socio puede listar todas"""
        test_client, mock_db, mock_user = client_socio
        
        mock_listar.return_value = {
            "total": 0,
            "verificaciones": [],
            "limit": 50,
            "offset": 0
        }
        
        response = test_client.get("/api/ala/verificaciones")
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "verificaciones" in data
    
    @patch("app.services.ala_service.listar_verificaciones")
    def test_listar_ok_colaborador(self, mock_listar, client_colaborador):
        """Colaborador puede listar las propias"""
        test_client, mock_db, mock_user = client_colaborador
        
        mock_listar.return_value = {
            "total": 0,
            "verificaciones": [],
            "limit": 50,
            "offset": 0
        }
        
        response = test_client.get("/api/ala/verificaciones")
        
        assert response.status_code == 200


class TestEndpointObtener:
    """Tests del endpoint GET /api/ala/verificaciones/{id}"""
    
    def test_obtener_no_existe(self, client_socio):
        """UUID inexistente retorna 404"""
        test_client, mock_db, mock_user = client_socio
        
        with patch("app.services.ala_service.obtener_verificacion") as mock_obtener:
            mock_obtener.return_value = None
            
            response = test_client.get(f"/api/ala/verificaciones/{uuid4()}")
            
            assert response.status_code == 404
    
    def test_obtener_colaborador_sin_permiso(self, client_colaborador):
        """Colaborador no puede ver verificación de otro usuario"""
        test_client, mock_db, mock_user = client_colaborador
        
        mock_verificacion = Mock()
        mock_verificacion.id = uuid4()
        mock_verificacion.usuario_id = uuid4()  # Otro usuario
        
        with patch("app.services.ala_service.obtener_verificacion") as mock_obtener:
            mock_obtener.return_value = mock_verificacion
            
            response = test_client.get(f"/api/ala/verificaciones/{mock_verificacion.id}")
            
            assert response.status_code == 403


class TestEndpointMetadata:
    """Tests del endpoint GET /api/ala/listas/metadata"""
    
    def test_metadata_requiere_socio(self, client_colaborador):
        """Colaborador no puede ver metadata"""
        test_client, mock_db, mock_user = client_colaborador
        
        response = test_client.get("/api/ala/listas/metadata")
        
        assert response.status_code == 403
    
    @patch("app.services.ala_service.obtener_metadata_listas")
    def test_metadata_ok_socio(self, mock_metadata, client_socio):
        """Socio puede ver metadata"""
        test_client, mock_db, mock_user = client_socio
        
        mock_metadata.return_value = []
        
        response = test_client.get("/api/ala/listas/metadata")
        
        assert response.status_code == 200


class TestEndpointEliminar:
    """Tests del endpoint DELETE /api/ala/verificaciones/{id}"""
    
    def test_delete_requiere_socio(self, client_colaborador):
        """Colaborador no puede eliminar"""
        test_client, mock_db, mock_user = client_colaborador
        
        response = test_client.delete(f"/api/ala/verificaciones/{uuid4()}")
        
        assert response.status_code == 403
    
    def test_delete_no_existe(self, client_socio):
        """Eliminar inexistente retorna 404"""
        test_client, mock_db, mock_user = client_socio
        
        with patch("app.services.ala_service.obtener_verificacion") as mock_obtener:
            mock_obtener.return_value = None
            
            response = test_client.delete(f"/api/ala/verificaciones/{uuid4()}")
            
            assert response.status_code == 404
    
    def test_delete_ok_socio(self, client_socio):
        """Socio puede eliminar"""
        test_client, mock_db, mock_user = client_socio
        
        mock_verificacion = Mock()
        mock_verificacion.id = uuid4()
        mock_verificacion.deleted_at = None
        
        with patch("app.services.ala_service.obtener_verificacion") as mock_obtener:
            mock_obtener.return_value = mock_verificacion
            mock_db.commit = Mock()
            
            response = test_client.delete(f"/api/ala/verificaciones/{mock_verificacion.id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["mensaje"] == "Verificación eliminada"


class TestEndpointActualizar:
    """Tests del endpoint PATCH /api/ala/verificaciones/{id}"""
    
    def test_actualizar_no_existe(self, client_socio):
        """Actualizar inexistente retorna 404"""
        test_client, mock_db, mock_user = client_socio
        
        with patch("app.services.ala_service.obtener_verificacion") as mock_obtener:
            mock_obtener.return_value = None
            
            response = test_client.patch(
                f"/api/ala/verificaciones/{uuid4()}",
                json={"busqueda_google_realizada": True}
            )
            
            assert response.status_code == 404
    
    def test_actualizar_colaborador_sin_permiso(self, client_colaborador):
        """Colaborador no puede actualizar verificación de otro"""
        test_client, mock_db, mock_user = client_colaborador
        
        mock_verificacion = Mock()
        mock_verificacion.id = uuid4()
        mock_verificacion.usuario_id = uuid4()  # Otro usuario
        
        with patch("app.services.ala_service.obtener_verificacion") as mock_obtener:
            mock_obtener.return_value = mock_verificacion
            
            response = test_client.patch(
                f"/api/ala/verificaciones/{mock_verificacion.id}",
                json={"busqueda_google_realizada": True}
            )
            
            assert response.status_code == 403
