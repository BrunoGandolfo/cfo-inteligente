"""
Pytest Configuration - CFO Inteligente
Fixtures centralizadas con BD de test aislada y rollback automático.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.core.database import Base
from app.models.usuario import Usuario
from app.models.area import Area
from app.models.socio import Socio
import uuid

# ============================================================
# VALIDACIÓN DE SEGURIDAD - NO EJECUTAR TESTS CONTRA PRODUCCIÓN
# ============================================================
_test_url = settings.test_database_url
if "railway" in _test_url or "rlwy.net" in _test_url:
    raise RuntimeError(
        "ABORTADO: TEST_DATABASE_URL apunta a producción (Railway). "
        "Configurar una BD de test local en .env"
    )

# ============================================================
# ENGINE Y TABLAS (scope=session, se ejecuta una vez)
# ============================================================
_engine = create_engine(_test_url)
_TestSessionLocal = sessionmaker(bind=_engine)

@pytest.fixture(scope="session", autouse=True)
def crear_tablas():
    """Crea todas las tablas al inicio, las elimina al final."""
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)

# ============================================================
# SESIÓN CON ROLLBACK AUTOMÁTICO (scope=function)
# ============================================================
@pytest.fixture(scope="function")
def db_session():
    """Sesión de BD que hace rollback automático después de cada test."""
    connection = _engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

# ============================================================
# FIXTURES DE DATOS BASE
# ============================================================
@pytest.fixture
def usuario_test(db_session):
    """Usuario socio para tests."""
    usuario = Usuario(
        id=uuid.uuid4(),
        email="test@cfointeligente.com",
        nombre="Usuario Test",
        password_hash="$2b$12$test_hash_placeholder",
        es_socio=True,
        activo=True
    )
    db_session.add(usuario)
    db_session.flush()
    return usuario

@pytest.fixture
def areas_test(db_session):
    """Las 5 áreas del negocio."""
    nombres = ["Jurídica", "Contable", "Notarial", "Recuperación", "Gastos Generales"]
    areas = []
    for nombre in nombres:
        area = Area(id=uuid.uuid4(), nombre=nombre, activo=True)
        db_session.add(area)
        areas.append(area)
    db_session.flush()
    return {a.nombre: a for a in areas}

@pytest.fixture
def socios_test(db_session):
    """Los 5 socios con participación igualitaria."""
    nombres = ["Agustina", "Viviana", "Gonzalo", "Pancho", "Bruno"]
    socios = []
    for nombre in nombres:
        socio = Socio(
            id=uuid.uuid4(),
            nombre=nombre,
            porcentaje_participacion=20.00,
            activo=True
        )
        db_session.add(socio)
        socios.append(socio)
    db_session.flush()
    return {s.nombre: s for s in socios}

# ============================================================
# FIXTURE EXISTENTE (mantener compatibilidad)
# ============================================================
@pytest.fixture
def sample_metricas():
    """Fixture con métricas sample para tests."""
    return {
        "ingresos_totales": 1500000,
        "gastos_totales": 800000,
        "rentabilidad": 46.67,
        "area_lider": "Jurídica",
        "ingresos_por_area": {"Jurídica": 600000, "Contable": 400000, "Notarial": 300000, "Recuperación": 200000},
        "gastos_por_area": {"Jurídica": 200000, "Contable": 250000, "Notarial": 200000, "Recuperación": 150000},
        "operaciones_count": 150,
        "ticket_promedio": 10000,
    }

@pytest.fixture
def operaciones_test(db_session, usuario_test, areas_test, socios_test):
    """Set mínimo de operaciones para tests que consultan datos."""
    from app.models.operacion import Operacion, TipoOperacion, Moneda, Localidad
    from app.models.distribucion import DistribucionDetalle
    from datetime import date, timedelta
    from decimal import Decimal
    
    hoy = date.today()
    mes_pasado = hoy - timedelta(days=30)
    hace_2_meses = hoy - timedelta(days=60)
    hace_3_meses = hoy - timedelta(days=90)
    tc = Decimal("42.50")
    
    operaciones = []
    
    # Ingresos variados (3 meses, 2 áreas, 2 monedas)
    datos_ingresos = [
        (hoy, Decimal("100000"), Moneda.UYU, areas_test["Jurídica"], Localidad.MONTEVIDEO, "Cliente A"),
        (hoy, Decimal("5000"), Moneda.USD, areas_test["Contable"], Localidad.MERCEDES, "Cliente B"),
        (mes_pasado, Decimal("200000"), Moneda.UYU, areas_test["Notarial"], Localidad.MONTEVIDEO, "Cliente C"),
        (mes_pasado, Decimal("3000"), Moneda.USD, areas_test["Jurídica"], Localidad.MERCEDES, "Cliente D"),
        (hace_2_meses, Decimal("150000"), Moneda.UYU, areas_test["Recuperación"], Localidad.MONTEVIDEO, "Cliente E"),
        (hace_3_meses, Decimal("80000"), Moneda.UYU, areas_test["Jurídica"], Localidad.MONTEVIDEO, "Cliente F"),
    ]
    
    for fecha, monto, moneda, area, localidad, cliente in datos_ingresos:
        if moneda == Moneda.UYU:
            monto_uyu = monto
            monto_usd = (monto / tc).quantize(Decimal("0.01"))
        else:
            monto_usd = monto
            monto_uyu = (monto * tc).quantize(Decimal("0.01"))
        
        op = Operacion(
            id=uuid.uuid4(),
            tipo_operacion=TipoOperacion.INGRESO,
            fecha=fecha,
            monto_original=monto,
            moneda_original=moneda,
            tipo_cambio=tc,
            monto_uyu=monto_uyu,
            monto_usd=monto_usd,
            total_pesificado=monto_uyu,
            total_dolarizado=monto_usd,
            area_id=area.id,
            localidad=localidad,
            descripcion=f"Ingreso test {cliente}",
            cliente=cliente,
        )
        db_session.add(op)
        operaciones.append(op)
    
    # Gastos (2 meses)
    datos_gastos = [
        (hoy, Decimal("50000"), Moneda.UYU, areas_test["Jurídica"], Localidad.MONTEVIDEO, "Proveedor A"),
        (mes_pasado, Decimal("1000"), Moneda.USD, areas_test["Contable"], Localidad.MERCEDES, "Proveedor B"),
        (hace_2_meses, Decimal("30000"), Moneda.UYU, areas_test["Notarial"], Localidad.MONTEVIDEO, "Proveedor C"),
    ]
    
    for fecha, monto, moneda, area, localidad, proveedor in datos_gastos:
        if moneda == Moneda.UYU:
            monto_uyu = monto
            monto_usd = (monto / tc).quantize(Decimal("0.01"))
        else:
            monto_usd = monto
            monto_uyu = (monto * tc).quantize(Decimal("0.01"))
        
        op = Operacion(
            id=uuid.uuid4(),
            tipo_operacion=TipoOperacion.GASTO,
            fecha=fecha,
            monto_original=monto,
            moneda_original=moneda,
            tipo_cambio=tc,
            monto_uyu=monto_uyu,
            monto_usd=monto_usd,
            total_pesificado=monto_uyu,
            total_dolarizado=monto_usd,
            area_id=area.id,
            localidad=localidad,
            descripcion=f"Gasto test {proveedor}",
            proveedor=proveedor,
        )
        db_session.add(op)
        operaciones.append(op)
    
    # 1 Distribución con detalle por socio
    op_dist = Operacion(
        id=uuid.uuid4(),
        tipo_operacion=TipoOperacion.DISTRIBUCION,
        fecha=hoy,
        monto_original=Decimal("500000"),
        moneda_original=Moneda.UYU,
        tipo_cambio=tc,
        monto_uyu=Decimal("500000"),
        monto_usd=(Decimal("500000") / tc).quantize(Decimal("0.01")),
        total_pesificado=Decimal("500000"),
        total_dolarizado=(Decimal("500000") / tc).quantize(Decimal("0.01")),
        localidad=Localidad.MONTEVIDEO,
        descripcion="Distribución test",
    )
    db_session.add(op_dist)
    operaciones.append(op_dist)
    
    for nombre, socio in socios_test.items():
        detalle = DistribucionDetalle(
            id=uuid.uuid4(),
            operacion_id=op_dist.id,
            socio_id=socio.id,
            monto_uyu=Decimal("100000"),
            monto_usd=(Decimal("100000") / tc).quantize(Decimal("0.01")),
            porcentaje=Decimal("20.00"),
            total_pesificado=Decimal("100000"),
            total_dolarizado=(Decimal("100000") / tc).quantize(Decimal("0.01")),
        )
        db_session.add(detalle)
    
    db_session.flush()
    return operaciones
