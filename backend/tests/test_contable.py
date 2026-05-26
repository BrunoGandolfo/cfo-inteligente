"""
Suite de tests para el módulo Contable (consultas DGI) - CFO Inteligente.

Cobertura objetivo: api/contable.py, services/contable_service.py,
models/consulta_contable.py. Los servicios DGI hacen scraping con CAPTCHA pago,
por lo que la capa de Playwright se mockea por completo — testeamos routing,
RBAC, dispatch, persistencia, soft delete e historial.

Ejecutar:
    cd backend
    pytest tests/test_contable.py -v
    pytest tests/test_contable.py -v \
        --cov=app.api.contable --cov=app.services.contable_service \
        --cov=app.models.consulta_contable
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import get_current_user
from app.main import app
from app.models.consulta_contable import ConsultaContable
from app.services import contable_service


# =============================================================================
# Fixtures de usuarios mockeados
# =============================================================================


@pytest.fixture
def mock_usuario_socio():
    """Socio (es_socio=True). Acceso total sin importar la whitelist."""
    usuario = Mock()
    usuario.id = uuid.uuid4()
    usuario.email = "socio@grupoconexion.uy"  # no está en la whitelist
    usuario.nombre = "Socio Test"
    usuario.es_socio = True
    usuario.activo = True
    return usuario


@pytest.fixture
def mock_usuario_colaborador_autorizado():
    """Colaborador (no socio) que SÍ está en USUARIOS_ACCESO_CONTABLE."""
    usuario = Mock()
    usuario.id = uuid.uuid4()
    usuario.email = "naraujo@grupoconexion.uy"
    usuario.nombre = "Natalia Araujo"
    usuario.es_socio = False
    usuario.activo = True
    return usuario


@pytest.fixture
def mock_usuario_colaborador_no_autorizado():
    """Colaborador (no socio) que NO está en USUARIOS_ACCESO_CONTABLE."""
    usuario = Mock()
    usuario.id = uuid.uuid4()
    usuario.email = "intruso@grupoconexion.uy"
    usuario.nombre = "Intruso"
    usuario.es_socio = False
    usuario.activo = True
    return usuario


# =============================================================================
# Fixtures de clientes HTTP (TestClient con dependency_overrides)
# =============================================================================


def _build_client(usuario):
    mock_db = Mock()

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: usuario
    client = TestClient(app)
    return client, mock_db, usuario


@pytest.fixture
def client_socio(mock_usuario_socio):
    client, mock_db, usuario = _build_client(mock_usuario_socio)
    yield client, mock_db, usuario
    app.dependency_overrides.clear()


@pytest.fixture
def client_colaborador_ok(mock_usuario_colaborador_autorizado):
    client, mock_db, usuario = _build_client(mock_usuario_colaborador_autorizado)
    yield client, mock_db, usuario
    app.dependency_overrides.clear()


@pytest.fixture
def client_colaborador_denegado(mock_usuario_colaborador_no_autorizado):
    client, mock_db, usuario = _build_client(mock_usuario_colaborador_no_autorizado)
    yield client, mock_db, usuario
    app.dependency_overrides.clear()


@pytest.fixture
def client_sin_auth():
    app.dependency_overrides.clear()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# =============================================================================
# Helpers de modelo
# =============================================================================


def _crear_usuario_en_bd(db_session, *, es_socio: bool = True, email: str | None = None):
    """Crea un usuario real en la BD para FKs."""
    from app.models.usuario import Usuario

    if email is None:
        email = f"u-{uuid.uuid4().hex[:8]}@test.local"
    usuario = Usuario(
        id=uuid.uuid4(),
        email=email,
        nombre="Test User",
        password_hash="$2b$12$placeholder",
        es_socio=es_socio,
        activo=True,
    )
    db_session.add(usuario)
    db_session.flush()
    return usuario


def _crear_consulta(db_session, usuario_id, **overrides):
    """Crea una ConsultaContable persistida en la sesión de test."""
    defaults = dict(
        usuario_id=usuario_id,
        servicio="CERTIFICADO_UNICO",
        rut="210000000019",
        ci=None,
        datos_entrada={"rut": "210000000019"},
        exitosa=True,
        resultado_texto="OK vigente",
        resultado_datos={"consultado": True, "resultado_texto": "OK vigente"},
        error=None,
        cliente_nombre="Cliente Test",
        cliente_rut="210000000019",
    )
    defaults.update(overrides)
    consulta = ConsultaContable(**defaults)
    db_session.add(consulta)
    db_session.flush()
    return consulta


# =============================================================================
# SECCIÓN 1: /servicios-disponibles (estático)
# =============================================================================


class TestServiciosDisponibles:
    """GET /api/contable/servicios-disponibles"""

    SERVICIOS_ESPERADOS = {
        "CERTIFICADO_UNICO",
        "DECLARACION_IRPF",
        "AFILIACION_BANCARIA",
        "BORRADORES_IASS",
        "EXONERACION_ARRENDAMIENTOS",
        "ESTADO_TRAMITE",
        "EXPEDIENTE_ADMINISTRATIVO",
        "DEVOLUCION_IVA_GASOIL",
        "CONSTANCIA_PRIMARIA",
        "RESIDENCIA_FISCAL",
    }

    def test_requiere_auth(self, client_sin_auth):
        response = client_sin_auth.get("/api/contable/servicios-disponibles")
        assert response.status_code == 401

    def test_socio_recibe_10_servicios(self, client_socio):
        client, _, _ = client_socio
        response = client.get("/api/contable/servicios-disponibles")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 10
        ids = {s["id"] for s in data}
        assert ids == self.SERVICIOS_ESPERADOS

    def test_estructura_cada_servicio(self, client_socio):
        client, _, _ = client_socio
        response = client.get("/api/contable/servicios-disponibles")
        data = response.json()
        for s in data:
            assert "id" in s and isinstance(s["id"], str)
            assert "nombre" in s and s["nombre"]
            assert "descripcion" in s and s["descripcion"]
            # El endpoint usa la clave "campos" (no "campos_requeridos")
            assert "campos" in s and isinstance(s["campos"], list)
            assert len(s["campos"]) >= 1

    def test_colaborador_no_autorizado_recibe_403(self, client_colaborador_denegado):
        client, _, _ = client_colaborador_denegado
        response = client.get("/api/contable/servicios-disponibles")
        assert response.status_code == 403

    def test_colaborador_autorizado_recibe_200(self, client_colaborador_ok):
        client, _, _ = client_colaborador_ok
        response = client.get("/api/contable/servicios-disponibles")
        assert response.status_code == 200


# =============================================================================
# SECCIÓN 2: RBAC sobre /consultar y /consultas
# =============================================================================


class TestRBAC:
    """Permisos en POST /consultar y GET /consultas según whitelist y es_socio."""

    def test_consultar_sin_auth_es_401(self, client_sin_auth):
        response = client_sin_auth.post(
            "/api/contable/consultar",
            json={"servicio": "CERTIFICADO_UNICO", "rut": "210000000019"},
        )
        assert response.status_code == 401

    def test_listar_sin_auth_es_401(self, client_sin_auth):
        response = client_sin_auth.get("/api/contable/consultas")
        assert response.status_code == 401

    def test_consultar_colaborador_no_autorizado_es_403(self, client_colaborador_denegado):
        client, _, _ = client_colaborador_denegado
        response = client.post(
            "/api/contable/consultar",
            json={"servicio": "CERTIFICADO_UNICO", "rut": "210000000019"},
        )
        assert response.status_code == 403

    def test_listar_colaborador_no_autorizado_es_403(self, client_colaborador_denegado):
        client, _, _ = client_colaborador_denegado
        response = client.get("/api/contable/consultas")
        assert response.status_code == 403

    @patch("app.api.contable._cargar_servicio_contable")
    def test_consultar_colaborador_autorizado_es_200(self, mock_loader, client_colaborador_ok):
        client, _, usuario = client_colaborador_ok
        fake_consulta = Mock(
            id=uuid.uuid4(),
            usuario_id=usuario.id,
            servicio="CERTIFICADO_UNICO",
            rut="210000000019",
            ci=None,
            datos_entrada={"rut": "210000000019"},
            exitosa=True,
            resultado_texto="OK",
            resultado_datos={"consultado": True},
            error=None,
            cliente_nombre=None,
            cliente_rut=None,
            created_at=datetime.now(timezone.utc),
            deleted_at=None,
        )
        mock_service = Mock()
        mock_service.ejecutar_y_registrar = AsyncMock(return_value=fake_consulta)
        mock_loader.return_value = mock_service

        response = client.post(
            "/api/contable/consultar",
            json={"servicio": "CERTIFICADO_UNICO", "rut": "210000000019"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["consulta"]["servicio"] == "CERTIFICADO_UNICO"
        assert body["consulta"]["exitosa"] is True

    @patch("app.api.contable._cargar_servicio_contable")
    def test_socio_fuera_de_whitelist_tiene_acceso(self, mock_loader, client_socio):
        """es_socio=True bypassa USUARIOS_ACCESO_CONTABLE."""
        client, _, usuario = client_socio
        mock_service = Mock()
        mock_service.listar_consultas = Mock(
            return_value={"total": 0, "consultas": [], "limit": 50, "offset": 0}
        )
        mock_loader.return_value = mock_service

        response = client.get("/api/contable/consultas")
        assert response.status_code == 200


# =============================================================================
# SECCIÓN 3: Helpers internos de contable.py y contable_service.py
# =============================================================================


class TestAccessControlHelpers:
    """Funciones internas de control de acceso del router."""

    def test_es_usuario_autorizado_socio(self, mock_usuario_socio):
        from app.api.contable import _es_usuario_autorizado

        assert _es_usuario_autorizado(mock_usuario_socio) is True

    def test_es_usuario_autorizado_colaborador_ok(self, mock_usuario_colaborador_autorizado):
        from app.api.contable import _es_usuario_autorizado

        assert _es_usuario_autorizado(mock_usuario_colaborador_autorizado) is True

    def test_es_usuario_autorizado_colaborador_denegado(
        self, mock_usuario_colaborador_no_autorizado
    ):
        from app.api.contable import _es_usuario_autorizado

        assert _es_usuario_autorizado(mock_usuario_colaborador_no_autorizado) is False

    def test_es_usuario_autorizado_email_case_insensitive(self):
        from app.api.contable import _es_usuario_autorizado

        usuario = Mock()
        usuario.es_socio = False
        usuario.email = "NAraujo@GRUPOconexion.UY"
        assert _es_usuario_autorizado(usuario) is True


class TestNormalizacionService:
    """Helpers de normalización y manejo de resultados del service."""

    def test_normalizar_servicio_aplica_upper_y_trim(self):
        from app.services.contable_service import _normalizar_servicio

        assert _normalizar_servicio("  certificado_unico  ") == "CERTIFICADO_UNICO"
        assert _normalizar_servicio("") == ""
        assert _normalizar_servicio(None) == ""

    def test_limpiar_texto(self):
        from app.services.contable_service import _limpiar_texto

        assert _limpiar_texto("  hola  ") == "hola"
        assert _limpiar_texto("") is None
        assert _limpiar_texto(None) is None
        assert _limpiar_texto(123) == "123"

    def test_resultado_exitosa(self):
        from app.services.contable_service import _resultado_exitosa

        assert _resultado_exitosa({"consultado": True}) is True
        assert _resultado_exitosa({"consultado": False}) is False
        assert _resultado_exitosa({"consultado": True, "error": "X"}) is False
        assert _resultado_exitosa(None) is False
        assert _resultado_exitosa({}) is False

    def test_resultado_texto(self):
        from app.services.contable_service import _resultado_texto

        assert _resultado_texto({"resultado_texto": "OK"}) == "OK"
        assert _resultado_texto({"error": "boom"}) == "boom"
        assert _resultado_texto({}) is None
        assert _resultado_texto(None) is None

    def test_merge_datos_entrada(self):
        from app.services.contable_service import _merge_datos_entrada

        assert _merge_datos_entrada("R", "C", {"x": 1}) == {"rut": "R", "ci": "C", "x": 1}
        # rut explícito no pisa el del extra
        assert _merge_datos_entrada("R", None, {"rut": "OTRO"}) == {"rut": "OTRO"}
        assert _merge_datos_entrada(None, None, None) == {}


# =============================================================================
# SECCIÓN 4: Modelo ConsultaContable (BD real)
# =============================================================================


class TestModeloConsultaContable:
    """CRUD básico y soft delete contra la BD de test."""

    def test_crear_y_leer(self, db_session):
        usuario = _crear_usuario_en_bd(db_session)
        consulta = _crear_consulta(db_session, usuario.id, servicio="DECLARACION_IRPF")

        leida = (
            db_session.query(ConsultaContable)
            .filter(ConsultaContable.id == consulta.id)
            .first()
        )
        assert leida is not None
        assert leida.servicio == "DECLARACION_IRPF"
        assert leida.usuario_id == usuario.id
        assert leida.exitosa is True
        assert leida.deleted_at is None
        assert leida.created_at is not None

    def test_repr_no_explota(self, db_session):
        usuario = _crear_usuario_en_bd(db_session)
        consulta = _crear_consulta(db_session, usuario.id)
        texto = repr(consulta)
        assert "ConsultaContable" in texto
        assert "CERTIFICADO_UNICO" in texto

    def test_soft_delete_marca_deleted_at(self, db_session):
        usuario = _crear_usuario_en_bd(db_session)
        consulta = _crear_consulta(db_session, usuario.id)

        contable_service.eliminar_consulta(db_session, consulta.id)
        db_session.expire_all()

        leida = (
            db_session.query(ConsultaContable)
            .filter(ConsultaContable.id == consulta.id)
            .first()
        )
        assert leida is not None  # no fue borrada físicamente
        assert leida.deleted_at is not None

    def test_obtener_consulta_filtra_deleted_at(self, db_session):
        usuario = _crear_usuario_en_bd(db_session)
        consulta = _crear_consulta(db_session, usuario.id)

        # Antes del delete, la encuentra
        assert contable_service.obtener_consulta(db_session, consulta.id) is not None

        # Después del soft delete, devuelve None
        contable_service.eliminar_consulta(db_session, consulta.id)
        db_session.expire_all()
        assert contable_service.obtener_consulta(db_session, consulta.id) is None

    def test_eliminar_consulta_inexistente_es_noop(self, db_session):
        # No debe lanzar
        contable_service.eliminar_consulta(db_session, uuid.uuid4())


# =============================================================================
# SECCIÓN 5: Service - registrar_consulta y listar_consultas
# =============================================================================


class TestRegistrarConsulta:
    """registrar_consulta: normalización, mapeo de resultado, persistencia."""

    def test_persiste_con_servicio_normalizado(self, db_session):
        usuario = _crear_usuario_en_bd(db_session)
        consulta = contable_service.registrar_consulta(
            db=db_session,
            usuario_id=usuario.id,
            servicio="  certificado_unico  ",
            rut="210000000019",
            ci=None,
            datos_entrada={"rut": "210000000019"},
            resultado={"consultado": True, "resultado_texto": "VIGENTE"},
        )
        assert consulta.servicio == "CERTIFICADO_UNICO"
        assert consulta.exitosa is True
        assert consulta.resultado_texto == "VIGENTE"
        assert consulta.error is None

    def test_persiste_resultado_con_error(self, db_session):
        usuario = _crear_usuario_en_bd(db_session)
        consulta = contable_service.registrar_consulta(
            db=db_session,
            usuario_id=usuario.id,
            servicio="CERTIFICADO_UNICO",
            rut=None,
            ci="12345678",
            datos_entrada={"ci": "12345678"},
            resultado={"consultado": False, "error": "CAPTCHA timeout"},
        )
        assert consulta.exitosa is False
        assert consulta.error == "CAPTCHA timeout"
        assert consulta.resultado_texto == "CAPTCHA timeout"


class TestListarConsultas:
    """Filtros y paginación en listar_consultas (BD real)."""

    def test_filtra_por_usuario(self, db_session):
        u1 = _crear_usuario_en_bd(db_session, es_socio=False)
        u2 = _crear_usuario_en_bd(db_session, es_socio=False)
        _crear_consulta(db_session, u1.id, servicio="CERTIFICADO_UNICO")
        _crear_consulta(db_session, u1.id, servicio="DECLARACION_IRPF")
        _crear_consulta(db_session, u2.id, servicio="CERTIFICADO_UNICO")

        res_u1 = contable_service.listar_consultas(db_session, usuario_id=u1.id)
        res_u2 = contable_service.listar_consultas(db_session, usuario_id=u2.id)
        res_all = contable_service.listar_consultas(db_session)

        assert res_u1["total"] == 2
        assert res_u2["total"] == 1
        assert res_all["total"] == 3

    def test_filtra_por_servicio_normalizado(self, db_session):
        u = _crear_usuario_en_bd(db_session)
        _crear_consulta(db_session, u.id, servicio="CERTIFICADO_UNICO")
        _crear_consulta(db_session, u.id, servicio="DECLARACION_IRPF")

        res = contable_service.listar_consultas(db_session, servicio="declaracion_irpf")
        assert res["total"] == 1
        assert res["consultas"][0].servicio == "DECLARACION_IRPF"

    def test_filtra_por_rut(self, db_session):
        u = _crear_usuario_en_bd(db_session)
        _crear_consulta(db_session, u.id, rut="111111111111")
        _crear_consulta(db_session, u.id, rut="222222222222")

        res = contable_service.listar_consultas(db_session, rut="222222222222")
        assert res["total"] == 1
        assert res["consultas"][0].rut == "222222222222"

    def test_filtra_por_rango_de_fechas(self, db_session):
        u = _crear_usuario_en_bd(db_session)
        ahora = datetime.now(timezone.utc).replace(tzinfo=None)
        antiguo = _crear_consulta(db_session, u.id)
        antiguo.created_at = ahora - timedelta(days=30)
        reciente = _crear_consulta(db_session, u.id)
        reciente.created_at = ahora - timedelta(days=1)
        db_session.flush()

        res = contable_service.listar_consultas(
            db_session,
            fecha_desde=ahora - timedelta(days=7),
            fecha_hasta=ahora + timedelta(days=1),
        )
        # Solo entra la reciente
        ids = {c.id for c in res["consultas"]}
        assert reciente.id in ids
        assert antiguo.id not in ids

    def test_excluye_soft_deleted(self, db_session):
        u = _crear_usuario_en_bd(db_session)
        viva = _crear_consulta(db_session, u.id)
        muerta = _crear_consulta(db_session, u.id)
        muerta.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db_session.flush()

        res = contable_service.listar_consultas(db_session)
        ids = {c.id for c in res["consultas"]}
        assert viva.id in ids
        assert muerta.id not in ids
        assert res["total"] == 1

    def test_paginacion_limit_offset(self, db_session):
        u = _crear_usuario_en_bd(db_session)
        for _ in range(5):
            _crear_consulta(db_session, u.id)

        pag1 = contable_service.listar_consultas(db_session, limit=2, offset=0)
        pag2 = contable_service.listar_consultas(db_session, limit=2, offset=2)
        pag3 = contable_service.listar_consultas(db_session, limit=2, offset=4)

        assert pag1["total"] == 5 and len(pag1["consultas"]) == 2
        assert pag2["total"] == 5 and len(pag2["consultas"]) == 2
        assert pag3["total"] == 5 and len(pag3["consultas"]) == 1


# =============================================================================
# SECCIÓN 6: Dispatch (mock de DGI) — POST /consultar persiste resultado
# =============================================================================


class TestDispatchYPersistencia:
    """POST /consultar dispatch correcto + persistencia del resultado."""

    @pytest.mark.asyncio
    async def test_dispatch_certificado_unico(self):
        """_ejecutar_servicio_dgi rutea a consultar_certificado_unico."""
        fake = AsyncMock(return_value={"consultado": True, "resultado_texto": "VIGENTE"})
        with patch.object(contable_service, "consultar_certificado_unico", fake):
            res = await contable_service._ejecutar_servicio_dgi(
                "CERTIFICADO_UNICO", "210000000019", "", {}
            )
        assert res["consultado"] is True
        fake.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_dispatch_servicio_inexistente(self):
        res = await contable_service._ejecutar_servicio_dgi("NO_EXISTE", None, None, {})
        assert res["consultado"] is False
        assert "no implementado" in res["error"].lower()

    @pytest.mark.asyncio
    async def test_dispatch_servicio_no_cargado(self):
        """Si el módulo DGI no está cargado (=None), devuelve no implementado."""
        with patch.object(contable_service, "consultar_borradores_iass", None):
            res = await contable_service._ejecutar_servicio_dgi(
                "BORRADORES_IASS", None, None, {}
            )
        assert res["consultado"] is False
        assert "no implementado" in res["error"].lower()

    @pytest.mark.asyncio
    async def test_dispatch_estado_tramite_lee_datos_extra(self):
        fake = AsyncMock(return_value={"consultado": True, "resultado_texto": "OK"})
        with patch.object(contable_service, "consultar_estado_tramite", fake):
            await contable_service._ejecutar_servicio_dgi(
                "ESTADO_TRAMITE", None, None, {"nro_tramite": "ABC123"}
            )
        fake.assert_awaited_once_with("ABC123")

    @pytest.mark.asyncio
    async def test_dispatch_declaracion_irpf(self):
        fake = AsyncMock(return_value={"consultado": True, "resultado_texto": "OK"})
        with patch.object(contable_service, "consultar_declaracion_irpf", fake):
            await contable_service._ejecutar_servicio_dgi(
                "DECLARACION_IRPF", None, "12345678", {}
            )
        fake.assert_awaited_once_with("12345678")

    @pytest.mark.asyncio
    async def test_dispatch_afiliacion_bancaria(self):
        fake = AsyncMock(return_value={"consultado": True, "resultado_texto": "OK"})
        with patch.object(contable_service, "consultar_afiliacion_bancaria", fake):
            await contable_service._ejecutar_servicio_dgi(
                "AFILIACION_BANCARIA", "210000000019", None, {}
            )
        fake.assert_awaited_once_with("210000000019")

    @pytest.mark.asyncio
    async def test_dispatch_borradores_iass(self):
        fake = AsyncMock(return_value={"consultado": True, "resultado_texto": "OK"})
        with patch.object(contable_service, "consultar_borradores_iass", fake):
            await contable_service._ejecutar_servicio_dgi(
                "BORRADORES_IASS", "210000000019", None, {}
            )
        fake.assert_awaited_once_with("210000000019")

    @pytest.mark.asyncio
    async def test_dispatch_exoneracion_arrendamientos(self):
        fake = AsyncMock(return_value={"consultado": True, "resultado_texto": "OK"})
        with patch.object(contable_service, "consultar_exoneracion_arrendamientos", fake):
            await contable_service._ejecutar_servicio_dgi(
                "EXONERACION_ARRENDAMIENTOS",
                None,
                None,
                {"tipo_doc": "CI", "numero_doc": "12345678", "pais": "URUGUAY"},
            )
        fake.assert_awaited_once_with("CI", "12345678", "URUGUAY")

    @pytest.mark.asyncio
    async def test_dispatch_expediente_administrativo(self):
        fake = AsyncMock(return_value={"consultado": True, "resultado_texto": "OK"})
        with patch.object(contable_service, "consultar_expediente_administrativo", fake):
            await contable_service._ejecutar_servicio_dgi(
                "EXPEDIENTE_ADMINISTRATIVO", None, None, {"nro_expediente": "E-1"}
            )
        fake.assert_awaited_once_with("E-1")

    @pytest.mark.asyncio
    async def test_dispatch_devolucion_iva_gasoil(self):
        fake = AsyncMock(return_value={"consultado": True, "resultado_texto": "OK"})
        with patch.object(contable_service, "consultar_devolucion_iva_gasoil", fake):
            await contable_service._ejecutar_servicio_dgi(
                "DEVOLUCION_IVA_GASOIL", "210000000019", None, {}
            )
        fake.assert_awaited_once_with("210000000019")

    @pytest.mark.asyncio
    async def test_dispatch_constancia_primaria(self):
        fake = AsyncMock(return_value={"consultado": True, "resultado_texto": "OK"})
        with patch.object(contable_service, "consultar_constancia_primaria", fake):
            await contable_service._ejecutar_servicio_dgi(
                "CONSTANCIA_PRIMARIA", None, None, {"nro_constancia": "C-9"}
            )
        fake.assert_awaited_once_with("C-9")

    @pytest.mark.asyncio
    async def test_dispatch_residencia_fiscal(self):
        fake = AsyncMock(return_value={"consultado": True, "resultado_texto": "OK"})
        with patch.object(contable_service, "consultar_certificado_residencia_fiscal", fake):
            await contable_service._ejecutar_servicio_dgi(
                "RESIDENCIA_FISCAL",
                None,
                None,
                {
                    "nro_solicitud": "S-1",
                    "linea": "1",
                    "tipo": "A",
                    "principio_crc": "X",
                },
            )
        fake.assert_awaited_once_with("S-1", "1", "A", "X")

    @pytest.mark.asyncio
    async def test_ejecutar_y_registrar_persiste_resultado_exitoso(self, db_session):
        usuario = _crear_usuario_en_bd(db_session)
        fake = AsyncMock(return_value={"consultado": True, "resultado_texto": "VIGENTE"})

        with patch.object(contable_service, "consultar_certificado_unico", fake):
            consulta = await contable_service.ejecutar_y_registrar(
                db=db_session,
                usuario_id=usuario.id,
                servicio="CERTIFICADO_UNICO",
                rut="210000000019",
                ci="",
                datos_extra={},
            )

        assert consulta.id is not None
        assert consulta.servicio == "CERTIFICADO_UNICO"
        assert consulta.exitosa is True
        assert consulta.resultado_texto == "VIGENTE"
        assert consulta.datos_entrada == {"rut": "210000000019", "ci": ""}

    @pytest.mark.asyncio
    async def test_ejecutar_y_registrar_persiste_excepcion(self, db_session):
        usuario = _crear_usuario_en_bd(db_session)
        fake = AsyncMock(side_effect=RuntimeError("playwright crash"))

        with patch.object(contable_service, "consultar_certificado_unico", fake):
            consulta = await contable_service.ejecutar_y_registrar(
                db=db_session,
                usuario_id=usuario.id,
                servicio="CERTIFICADO_UNICO",
                rut="X",
                ci="",
                datos_extra={},
            )

        assert consulta.exitosa is False
        assert "playwright crash" in (consulta.error or "")

    @patch("app.api.contable._cargar_servicio_contable")
    def test_endpoint_consultar_pasa_payload_al_service(self, mock_loader, client_socio):
        """El router debe propagar todos los campos del request al service."""
        client, _, usuario = client_socio
        fake_consulta = Mock(
            id=uuid.uuid4(),
            usuario_id=usuario.id,
            servicio="ESTADO_TRAMITE",
            rut=None,
            ci=None,
            datos_entrada={"nro_tramite": "T-9"},
            exitosa=True,
            resultado_texto="En proceso",
            resultado_datos=None,
            error=None,
            cliente_nombre="Cliente X",
            cliente_rut=None,
            created_at=datetime.now(timezone.utc),
            deleted_at=None,
        )
        mock_service = Mock()
        mock_service.ejecutar_y_registrar = AsyncMock(return_value=fake_consulta)
        mock_loader.return_value = mock_service

        response = client.post(
            "/api/contable/consultar",
            json={
                "servicio": "ESTADO_TRAMITE",
                "datos_extra": {"nro_tramite": "T-9"},
                "cliente_nombre": "Cliente X",
            },
        )
        assert response.status_code == 200
        call_kwargs = mock_service.ejecutar_y_registrar.await_args.kwargs
        assert call_kwargs["servicio"] == "ESTADO_TRAMITE"
        assert call_kwargs["datos_extra"] == {"nro_tramite": "T-9"}
        assert call_kwargs["cliente_nombre"] == "Cliente X"
        assert call_kwargs["usuario_id"] == usuario.id


# =============================================================================
# SECCIÓN 7: Historial - GET /consultas (router con BD real)
# =============================================================================


@pytest.fixture
def client_con_db(db_session):
    """Cliente que usa la sesión de BD real para tests de historial."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    def _build(usuario):
        app.dependency_overrides[get_current_user] = lambda: usuario
        return TestClient(app)

    yield _build, db_session
    app.dependency_overrides.clear()


class TestHistorialEndpoint:
    """GET /api/contable/consultas con BD real."""

    def test_socio_ve_todas(self, client_con_db):
        build_client, db = client_con_db
        u_socio = _crear_usuario_en_bd(db, es_socio=True)
        u_colab = _crear_usuario_en_bd(db, es_socio=False, email="naraujo@grupoconexion.uy")
        _crear_consulta(db, u_socio.id)
        _crear_consulta(db, u_colab.id)
        _crear_consulta(db, u_colab.id)

        client = build_client(u_socio)
        response = client.get("/api/contable/consultas")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 3

    def test_colaborador_solo_ve_las_suyas(self, client_con_db):
        build_client, db = client_con_db
        u_colab = _crear_usuario_en_bd(db, es_socio=False, email="naraujo@grupoconexion.uy")
        u_otro = _crear_usuario_en_bd(db, es_socio=True)
        _crear_consulta(db, u_colab.id)
        _crear_consulta(db, u_colab.id)
        _crear_consulta(db, u_otro.id)

        client = build_client(u_colab)
        response = client.get("/api/contable/consultas")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 2
        for c in body["consultas"]:
            assert c["usuario_id"] == str(u_colab.id)

    def test_filtro_por_servicio_via_endpoint(self, client_con_db):
        build_client, db = client_con_db
        u = _crear_usuario_en_bd(db, es_socio=True)
        _crear_consulta(db, u.id, servicio="CERTIFICADO_UNICO")
        _crear_consulta(db, u.id, servicio="DECLARACION_IRPF")

        client = build_client(u)
        response = client.get("/api/contable/consultas?servicio=DECLARACION_IRPF")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["consultas"][0]["servicio"] == "DECLARACION_IRPF"

    def test_paginacion_via_endpoint(self, client_con_db):
        build_client, db = client_con_db
        u = _crear_usuario_en_bd(db, es_socio=True)
        for _ in range(4):
            _crear_consulta(db, u.id)
        client = build_client(u)

        r1 = client.get("/api/contable/consultas?limit=2&offset=0")
        r2 = client.get("/api/contable/consultas?limit=2&offset=2")
        assert r1.status_code == 200 and r2.status_code == 200
        assert r1.json()["total"] == 4 and len(r1.json()["consultas"]) == 2
        assert r2.json()["total"] == 4 and len(r2.json()["consultas"]) == 2

    def test_limit_invalido_es_422(self, client_con_db):
        build_client, db = client_con_db
        u = _crear_usuario_en_bd(db, es_socio=True)
        client = build_client(u)
        response = client.get("/api/contable/consultas?limit=999")
        assert response.status_code == 422


# =============================================================================
# SECCIÓN 8: GET / DELETE /consultas/{id} con BD real
# =============================================================================


class TestObtenerYEliminarPorId:

    def test_get_consulta_existente_socio(self, client_con_db):
        build_client, db = client_con_db
        u = _crear_usuario_en_bd(db, es_socio=True)
        consulta = _crear_consulta(db, u.id)

        client = build_client(u)
        response = client.get(f"/api/contable/consultas/{consulta.id}")
        assert response.status_code == 200
        assert response.json()["consulta"]["id"] == str(consulta.id)

    def test_get_consulta_inexistente_es_404(self, client_con_db):
        build_client, db = client_con_db
        u = _crear_usuario_en_bd(db, es_socio=True)
        client = build_client(u)
        response = client.get(f"/api/contable/consultas/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_get_colaborador_no_puede_ver_consulta_ajena(self, client_con_db):
        build_client, db = client_con_db
        u_colab = _crear_usuario_en_bd(db, es_socio=False, email="naraujo@grupoconexion.uy")
        u_otro = _crear_usuario_en_bd(db, es_socio=True)
        consulta_ajena = _crear_consulta(db, u_otro.id)

        client = build_client(u_colab)
        response = client.get(f"/api/contable/consultas/{consulta_ajena.id}")
        assert response.status_code == 403

    def test_delete_marca_soft_delete(self, client_con_db):
        build_client, db = client_con_db
        u = _crear_usuario_en_bd(db, es_socio=True)
        consulta = _crear_consulta(db, u.id)
        consulta_id = consulta.id

        client = build_client(u)
        response = client.delete(f"/api/contable/consultas/{consulta_id}")
        assert response.status_code == 200
        assert response.json() == {"ok": True}

        # Refrescar sesión y verificar que NO fue borrada físicamente
        db.expire_all()
        leida = (
            db.query(ConsultaContable)
            .filter(ConsultaContable.id == consulta_id)
            .first()
        )
        assert leida is not None
        assert leida.deleted_at is not None

    def test_delete_inexistente_es_404(self, client_con_db):
        build_client, db = client_con_db
        u = _crear_usuario_en_bd(db, es_socio=True)
        client = build_client(u)
        response = client.delete(f"/api/contable/consultas/{uuid.uuid4()}")
        assert response.status_code == 404


# =============================================================================
# SECCIÓN 9: Endpoints stub (501)
# =============================================================================


class TestEndpointsStub:
    """Endpoints de exportación todavía no implementados (501)."""

    def test_exportar_excel_es_501(self, client_socio):
        client, _, _ = client_socio
        response = client.post("/api/contable/consultas/exportar-excel")
        assert response.status_code == 501

    def test_exportar_pdf_es_501(self, client_socio):
        client, _, _ = client_socio
        response = client.post(f"/api/contable/consultas/{uuid.uuid4()}/exportar-pdf")
        assert response.status_code == 501

    def test_exportar_excel_colaborador_denegado_es_403(self, client_colaborador_denegado):
        client, _, _ = client_colaborador_denegado
        response = client.post("/api/contable/consultas/exportar-excel")
        assert response.status_code == 403
