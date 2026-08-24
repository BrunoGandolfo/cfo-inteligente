"""
Tests para app/services/consultas_financieras_service.py (adaptador read-only del MCP).

Cubre:
- Equivalencia numérica exacta (al centavo) entre metricas_dashboard() y el
  endpoint real /api/metricas/dashboard, para el mismo período/localidad.
- Exclusión de operaciones con soft delete en listar_operaciones().
- Guardarraíl: ni el adaptador ni el servidor MCP importan operacion_service
  ni contienen escrituras a la base (db.add / .commit).

Los datos de estos tests se insertan con commit real (no con el fixture
db_session de rollback) porque el adaptador abre su propia SessionLocal():
una sesión distinta no ve filas de una transacción sin commitear en otra
sesión. Se limpian con delete físico al final — aceptable en la BD de test
(cfo_test), nunca en runtime de producción.
"""

import ast
import inspect
import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal, get_db
from app.core.security import get_current_user
from app.main import app
from app.models.area import Area
from app.models.operacion import Localidad, Moneda, Operacion, TipoOperacion
from app.services import consultas_financieras_service as svc


# ══════════════════════════════════════════════════════════════
# FIXTURE: datos committeados, exclusivos de este módulo de test
# ══════════════════════════════════════════════════════════════

FECHA_DESDE = date(2020, 1, 1)
FECHA_HASTA = date(2020, 1, 31)


@pytest.fixture
def datos_committeados():
    """Crea un área + operaciones (incluida una soft-deleted) con commit real."""
    db = SessionLocal()
    area_nombre = f"MCPTestArea-{uuid.uuid4().hex[:8]}"
    area = Area(id=uuid.uuid4(), nombre=area_nombre, activo=True)
    db.add(area)
    db.flush()

    tc = Decimal("40.00")

    ingreso = Operacion(
        id=uuid.uuid4(),
        tipo_operacion=TipoOperacion.INGRESO,
        fecha=date(2020, 1, 10),
        monto_original=Decimal("100000.37"),
        moneda_original=Moneda.UYU,
        tipo_cambio=tc,
        monto_uyu=Decimal("100000.37"),
        monto_usd=Decimal("2500.01"),
        total_pesificado=Decimal("100000.37"),
        total_dolarizado=Decimal("2500.01"),
        area_id=area.id,
        localidad=Localidad.MONTEVIDEO,
        descripcion="Ingreso MCP test",
        cliente="Cliente MCP",
    )
    gasto = Operacion(
        id=uuid.uuid4(),
        tipo_operacion=TipoOperacion.GASTO,
        fecha=date(2020, 1, 15),
        monto_original=Decimal("40000.13"),
        moneda_original=Moneda.UYU,
        tipo_cambio=tc,
        monto_uyu=Decimal("40000.13"),
        monto_usd=Decimal("1000.00"),
        total_pesificado=Decimal("40000.13"),
        total_dolarizado=Decimal("1000.00"),
        area_id=area.id,
        localidad=Localidad.MONTEVIDEO,
        descripcion="Gasto MCP test",
        proveedor="Proveedor MCP",
    )
    borrada = Operacion(
        id=uuid.uuid4(),
        tipo_operacion=TipoOperacion.INGRESO,
        fecha=date(2020, 1, 20),
        monto_original=Decimal("999999.00"),
        moneda_original=Moneda.UYU,
        tipo_cambio=tc,
        monto_uyu=Decimal("999999.00"),
        monto_usd=Decimal("25000.00"),
        total_pesificado=Decimal("999999.00"),
        total_dolarizado=Decimal("25000.00"),
        area_id=area.id,
        localidad=Localidad.MONTEVIDEO,
        descripcion="Operacion soft-deleted MCP test",
        cliente="Cliente Borrado",
    )
    from app.core.database import utc_now

    db.add_all([ingreso, gasto, borrada])
    db.commit()

    borrada_id = borrada.id
    borrada.deleted_at = utc_now()
    db.commit()

    ids = {"ingreso": ingreso.id, "gasto": gasto.id, "borrada": borrada_id}
    area_id = area.id
    db.close()

    yield {"area_nombre": area_nombre, "area_id": area_id, "ids": ids}

    cleanup = SessionLocal()
    cleanup.query(Operacion).filter(Operacion.area_id == area_id).delete()
    cleanup.query(Area).filter(Area.id == area_id).delete()
    cleanup.commit()
    cleanup.close()


# ══════════════════════════════════════════════════════════════
# TEST DE EQUIVALENCIA (requisito duro)
# ══════════════════════════════════════════════════════════════

def test_metricas_dashboard_coincide_al_centavo_con_endpoint(datos_committeados):
    """metricas_dashboard() debe dar los mismos números que /api/metricas/dashboard."""
    mock_user = Mock()
    mock_user.email = "test-mcp@cfointeligente.com"
    mock_user.es_socio = True

    app.dependency_overrides[get_db] = lambda: SessionLocal()
    app.dependency_overrides[get_current_user] = lambda: mock_user
    client = TestClient(app)

    try:
        resp = client.get(
            "/api/metricas/dashboard",
            params={
                "fecha_desde": str(FECHA_DESDE),
                "fecha_hasta": str(FECHA_HASTA),
                "moneda_vista": "UYU",
            },
        )
        assert resp.status_code == 200
        endpoint_metricas = resp.json()["metricas"]
    finally:
        app.dependency_overrides.clear()

    adaptador_resultado = svc.metricas_dashboard(
        fecha_desde=FECHA_DESDE,
        fecha_hasta=FECHA_HASTA,
        moneda_vista="UYU",
    )
    adaptador_metricas = adaptador_resultado["metricas"]

    assert adaptador_metricas["ingresos"]["valor"] == endpoint_metricas["ingresos"]["valor"]
    assert adaptador_metricas["gastos"]["valor"] == endpoint_metricas["gastos"]["valor"]
    assert adaptador_metricas["rentabilidad"] == endpoint_metricas["rentabilidad"]
    assert adaptador_metricas["area_lider"] == endpoint_metricas["area_lider"]

    # La operación soft-deleted no debe aparecer en ninguno de los dos cálculos.
    assert endpoint_metricas["ingresos"]["valor"] < 999999.00
    # metricas_extendidas agrega TODO el período (no filtra por área), así que
    # solo verificamos que nuestro ingreso committeado esté incluido en el total.
    assert adaptador_resultado["metricas_extendidas"]["ingresos_uyu"] >= Decimal("100000.37")


def test_metricas_dashboard_incluye_metricas_extendidas(datos_committeados):
    """El bloque metricas_extendidas debe traer la salida completa de MetricsAggregator."""
    resultado = svc.metricas_dashboard(fecha_desde=FECHA_DESDE, fecha_hasta=FECHA_HASTA)
    assert "metricas_extendidas" in resultado
    assert "margen_operativo" in resultado["metricas_extendidas"] or "rentabilidad_por_area" in resultado["metricas_extendidas"] or len(resultado["metricas_extendidas"]) > 10


# ══════════════════════════════════════════════════════════════
# TEST: soft delete excluido de listar_operaciones
# ══════════════════════════════════════════════════════════════

def test_listar_operaciones_excluye_soft_deleted(datos_committeados):
    resultado = svc.listar_operaciones(
        limit=100,
        fecha_desde=FECHA_DESDE,
        fecha_hasta=FECHA_HASTA,
        area=datos_committeados["area_nombre"],
    )
    ids_presentes = {op["id"] for op in resultado}

    assert str(datos_committeados["ids"]["ingreso"]) in ids_presentes
    assert str(datos_committeados["ids"]["gasto"]) in ids_presentes
    assert str(datos_committeados["ids"]["borrada"]) not in ids_presentes


def test_listar_operaciones_respeta_limit(datos_committeados):
    resultado = svc.listar_operaciones(
        limit=1,
        fecha_desde=FECHA_DESDE,
        fecha_hasta=FECHA_HASTA,
        area=datos_committeados["area_nombre"],
    )
    assert len(resultado) == 1


def test_listar_operaciones_filtra_por_localidad_inexistente(datos_committeados):
    resultado = svc.listar_operaciones(
        limit=100,
        fecha_desde=FECHA_DESDE,
        fecha_hasta=FECHA_HASTA,
        area=datos_committeados["area_nombre"],
        localidad="MERCEDES",
    )
    assert resultado == []


# ══════════════════════════════════════════════════════════════
# TESTS DE CATÁLOGOS E INDICADORES (cobertura del resto del adaptador)
# ══════════════════════════════════════════════════════════════

def test_listar_areas_retorna_lista_de_dicts():
    resultado = svc.listar_areas()
    assert isinstance(resultado, list)
    if resultado:
        assert set(resultado[0].keys()) == {"id", "nombre"}


def test_listar_socios_retorna_lista_de_dicts():
    resultado = svc.listar_socios()
    assert isinstance(resultado, list)
    if resultado:
        assert set(resultado[0].keys()) == {"id", "nombre"}


def test_obtener_operaciones_periodo_filtra_por_localidad(datos_committeados):
    ops = svc.obtener_operaciones_periodo(FECHA_DESDE, FECHA_HASTA, localidad="MONTEVIDEO")
    ids = {op.id for op in ops}
    assert datos_committeados["ids"]["ingreso"] in ids
    assert datos_committeados["ids"]["borrada"] not in ids


def test_obtener_operaciones_periodo_localidad_todas_no_filtra(datos_committeados):
    ops_todas = svc.obtener_operaciones_periodo(FECHA_DESDE, FECHA_HASTA, localidad="Todas")
    ops_sin_filtro = svc.obtener_operaciones_periodo(FECHA_DESDE, FECHA_HASTA)
    assert len(ops_todas) == len(ops_sin_filtro)


# ══════════════════════════════════════════════════════════════
# TEST GUARDARRAÍL: adaptador y servidor MCP son solo-lectura
# ══════════════════════════════════════════════════════════════

def _fuente_sin_comentarios_ni_strings(modulo):
    """
    Devuelve el árbol AST del módulo — inspeccionar el AST en vez del texto
    crudo evita falsos positivos con la palabra 'commit'/'add' dentro de
    docstrings o comentarios (como los de este mismo archivo).
    """
    codigo = inspect.getsource(modulo)
    return ast.parse(codigo), codigo


def test_adaptador_no_importa_operacion_service():
    _, codigo = _fuente_sin_comentarios_ni_strings(svc)
    tree = ast.parse(codigo)
    imports = [
        n.names[0].name if isinstance(n, ast.Import) else n.module
        for n in ast.walk(tree)
        if isinstance(n, (ast.Import, ast.ImportFrom))
    ]
    assert not any(i and "operacion_service" in i for i in imports)


def test_adaptador_no_contiene_llamadas_de_escritura():
    tree, _ = _fuente_sin_comentarios_ni_strings(svc)
    llamadas_prohibidas = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"add", "add_all", "commit", "delete", "flush", "execute"}:
                llamadas_prohibidas.add(node.func.attr)
    assert llamadas_prohibidas == set()


def test_mcp_server_no_importa_operacion_service_ni_escribe():
    import mcp_server.cfo_financiero_mcp as mcp_mod

    tree, _ = _fuente_sin_comentarios_ni_strings(mcp_mod)
    imports = [
        n.names[0].name if isinstance(n, ast.Import) else n.module
        for n in ast.walk(tree)
        if isinstance(n, (ast.Import, ast.ImportFrom))
    ]
    assert not any(i and "operacion_service" in i for i in imports)

    llamadas_prohibidas = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"add", "add_all", "commit", "delete", "flush", "execute"}:
                llamadas_prohibidas.add(node.func.attr)
    assert llamadas_prohibidas == set()
