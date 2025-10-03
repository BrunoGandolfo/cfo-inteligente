"""
Suite de Tests para OperacionService - Sistema CFO Inteligente

Tests del servicio de operaciones financieras (CRUD).
Valida cálculos de montos, creación de operaciones y lógica de negocio.

Ejecutar:
    cd backend
    pytest tests/test_operacion_service.py -v
    pytest tests/test_operacion_service.py --cov=app/services/operacion_service --cov-report=term-missing

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from app.services.operacion_service import (
    calcular_montos,
    _crear_operacion_base,
    crear_ingreso,
    crear_gasto,
    crear_retiro,
    crear_distribucion
)
from app.schemas.operacion import IngresoCreate, GastoCreate, RetiroCreate, DistribucionCreate
from app.models import Operacion, TipoOperacion, Moneda, Localidad, Area, Socio, DistribucionDetalle


# ══════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════

TEST_DATABASE_URL = "postgresql://cfo_user:cfo_pass@localhost/cfo_inteligente"

@pytest.fixture(scope="function")
def db_session():
    """Fixture que proporciona sesión de BD real para tests"""
    engine = create_engine(TEST_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture(scope="function")
def area_test(db_session):
    """Fixture que retorna un área de prueba"""
    area = db_session.query(Area).filter(Area.nombre == "Jurídica").first()
    if not area:
        # Si no existe, usar cualquier área activa
        area = db_session.query(Area).filter(Area.activo == True).first()
    return area


@pytest.fixture(scope="function")
def socios_test(db_session):
    """Fixture que retorna los 5 socios del sistema"""
    socios = {}
    for nombre in ['Agustina', 'Viviana', 'Gonzalo', 'Pancho', 'Bruno']:
        socio = db_session.query(Socio).filter(Socio.nombre == nombre).first()
        if socio:
            socios[nombre.lower()] = socio
    return socios


# ══════════════════════════════════════════════════════════════
# TESTS: calcular_montos() - CRÍTICO (DINERO REAL)
# ══════════════════════════════════════════════════════════════

class TestCalcularMontos:
    """Tests del cálculo de conversión de monedas"""
    
    def test_calcular_montos_uyu_to_usd(self):
        """40,500 UYU = 1,000 USD con TC 40.50"""
        monto_uyu, monto_usd = calcular_montos(
            monto_original=Decimal('40500'),
            moneda_original='UYU',
            tipo_cambio=Decimal('40.50')
        )
        
        assert monto_uyu == Decimal('40500')
        assert abs(monto_usd - Decimal('1000')) < Decimal('0.01')
    
    def test_calcular_montos_usd_to_uyu(self):
        """1,000 USD = 40,500 UYU con TC 40.50"""
        monto_uyu, monto_usd = calcular_montos(
            monto_original=Decimal('1000'),
            moneda_original='USD',
            tipo_cambio=Decimal('40.50')
        )
        
        assert monto_usd == Decimal('1000')
        assert monto_uyu == Decimal('40500')
    
    def test_calcular_montos_precision_decimal(self):
        """Verificar precisión en cálculos con decimales"""
        monto_uyu, monto_usd = calcular_montos(
            monto_original=Decimal('12345.67'),
            moneda_original='UYU',
            tipo_cambio=Decimal('40.25')
        )
        
        # 12345.67 / 40.25 ≈ 306.78
        esperado_usd = Decimal('12345.67') / Decimal('40.25')
        assert abs(monto_usd - esperado_usd) < Decimal('0.01')
        assert monto_uyu == Decimal('12345.67')
    
    def test_calcular_montos_tc_alto(self):
        """Tipo de cambio alto (48.00) debe calcular correctamente"""
        monto_uyu, monto_usd = calcular_montos(
            monto_original=Decimal('48000'),
            moneda_original='UYU',
            tipo_cambio=Decimal('48.00')
        )
        
        assert monto_uyu == Decimal('48000')
        assert monto_usd == Decimal('1000')
    
    def test_calcular_montos_tc_bajo(self):
        """Tipo de cambio bajo (38.00) debe calcular correctamente"""
        monto_uyu, monto_usd = calcular_montos(
            monto_original=Decimal('2000'),
            moneda_original='USD',
            tipo_cambio=Decimal('38.00')
        )
        
        assert monto_usd == Decimal('2000')
        assert monto_uyu == Decimal('76000')
    
    def test_calcular_montos_valores_pequenos(self):
        """Valores pequeños (100 UYU) deben funcionar"""
        monto_uyu, monto_usd = calcular_montos(
            monto_original=Decimal('100'),
            moneda_original='UYU',
            tipo_cambio=Decimal('40.00')
        )
        
        assert monto_uyu == Decimal('100')
        assert abs(monto_usd - Decimal('2.50')) < Decimal('0.01')


# ══════════════════════════════════════════════════════════════
# TESTS: _crear_operacion_base() - FUNCIÓN REFACTORIZADA
# ══════════════════════════════════════════════════════════════

class TestCrearOperacionBase:
    """Tests de la función base refactorizada (elimina duplicación)"""
    
    @pytest.mark.integration
    def test_crear_operacion_base_ingreso(self, db_session, area_test):
        """Función base debe crear ingreso correctamente"""
        operacion = _crear_operacion_base(
            db=db_session,
            tipo_operacion=TipoOperacion.INGRESO,
            fecha=date.today(),
            monto_original=Decimal('10000'),
            moneda_original='UYU',
            tipo_cambio=Decimal('40.00'),
            area_id=area_test.id,
            localidad='Montevideo',
            descripcion='Test ingreso',
            cliente='Cliente Test',
            proveedor=None
        )
        
        assert operacion.id is not None
        assert operacion.tipo_operacion == TipoOperacion.INGRESO
        assert operacion.cliente == 'Cliente Test'
        assert operacion.proveedor is None
        assert operacion.monto_original == Decimal('10000')
        assert operacion.moneda_original == Moneda.UYU
        assert operacion.monto_uyu == Decimal('10000')
        assert operacion.monto_usd == Decimal('250')  # 10000/40
    
    @pytest.mark.integration
    def test_crear_operacion_base_gasto(self, db_session, area_test):
        """Función base debe crear gasto correctamente"""
        operacion = _crear_operacion_base(
            db=db_session,
            tipo_operacion=TipoOperacion.GASTO,
            fecha=date.today(),
            monto_original=Decimal('500'),
            moneda_original='USD',
            tipo_cambio=Decimal('40.00'),
            area_id=area_test.id,
            localidad='Mercedes',
            descripcion='Test gasto',
            cliente=None,
            proveedor='Proveedor Test'
        )
        
        assert operacion.id is not None
        assert operacion.tipo_operacion == TipoOperacion.GASTO
        assert operacion.cliente is None
        assert operacion.proveedor == 'Proveedor Test'
        assert operacion.monto_original == Decimal('500')
        assert operacion.moneda_original == Moneda.USD
        assert operacion.monto_usd == Decimal('500')
        assert operacion.monto_uyu == Decimal('20000')  # 500*40
    
    @pytest.mark.integration
    def test_crear_operacion_base_localidad_normalizada(self, db_session, area_test):
        """Localidad debe normalizarse correctamente"""
        operacion = _crear_operacion_base(
            db=db_session,
            tipo_operacion=TipoOperacion.INGRESO,
            fecha=date.today(),
            monto_original=Decimal('1000'),
            moneda_original='UYU',
            tipo_cambio=Decimal('40.00'),
            area_id=area_test.id,
            localidad='montevideo',  # Minúsculas
            descripcion='Test',
            cliente='Test'
        )
        
        # Debe convertir 'montevideo' a MONTEVIDEO enum
        assert operacion.localidad == Localidad.MONTEVIDEO


# ══════════════════════════════════════════════════════════════
# TESTS: crear_ingreso() - Wrapper de función base
# ══════════════════════════════════════════════════════════════

class TestCrearIngreso:
    """Tests de crear_ingreso (usa función base)"""
    
    @pytest.mark.integration
    def test_crear_ingreso_uyu(self, db_session, area_test):
        """Crear ingreso en pesos uruguayos"""
        data = IngresoCreate(
            cliente="Cliente Test",
            area_id=area_test.id,
            monto_original=Decimal('15000'),
            moneda_original='UYU',
            tipo_cambio=Decimal('40.00'),
            fecha=date.today(),
            localidad='Montevideo',
            descripcion='Factura servicios jurídicos'
        )
        
        operacion = crear_ingreso(db_session, data)
        
        assert operacion.tipo_operacion == TipoOperacion.INGRESO
        assert operacion.cliente == 'Cliente Test'
        assert operacion.monto_uyu == Decimal('15000')
        assert operacion.monto_usd == Decimal('375')  # 15000/40
    
    @pytest.mark.integration
    def test_crear_ingreso_usd(self, db_session, area_test):
        """Crear ingreso en dólares"""
        data = IngresoCreate(
            cliente="Cliente USA",
            area_id=area_test.id,
            monto_original=Decimal('2500'),
            moneda_original='USD',
            tipo_cambio=Decimal('40.50'),
            fecha=date.today(),
            localidad='Mercedes',
            descripcion='Servicios internacionales'
        )
        
        operacion = crear_ingreso(db_session, data)
        
        assert operacion.tipo_operacion == TipoOperacion.INGRESO
        assert operacion.cliente == 'Cliente USA'
        assert operacion.monto_usd == Decimal('2500')
        assert operacion.monto_uyu == Decimal('101250')  # 2500*40.50


# ══════════════════════════════════════════════════════════════
# TESTS: crear_gasto() - Wrapper de función base
# ══════════════════════════════════════════════════════════════

class TestCrearGasto:
    """Tests de crear_gasto (usa función base)"""
    
    @pytest.mark.integration
    def test_crear_gasto_uyu(self, db_session, area_test):
        """Crear gasto en pesos uruguayos"""
        data = GastoCreate(
            proveedor="Proveedor Test",
            area_id=area_test.id,
            monto_original=Decimal('8000'),
            moneda_original='UYU',
            tipo_cambio=Decimal('40.00'),
            fecha=date.today(),
            localidad='Montevideo',
            descripcion='Material de oficina'
        )
        
        operacion = crear_gasto(db_session, data)
        
        assert operacion.tipo_operacion == TipoOperacion.GASTO
        assert operacion.proveedor == 'Proveedor Test'
        assert operacion.monto_uyu == Decimal('8000')
        assert operacion.monto_usd == Decimal('200')  # 8000/40
    
    @pytest.mark.integration
    def test_crear_gasto_usd(self, db_session, area_test):
        """Crear gasto en dólares"""
        data = GastoCreate(
            proveedor="AWS Inc",
            area_id=area_test.id,
            monto_original=Decimal('350'),
            moneda_original='USD',
            tipo_cambio=Decimal('40.00'),
            fecha=date.today(),
            localidad='Montevideo',
            descripcion='Hosting mensual'
        )
        
        operacion = crear_gasto(db_session, data)
        
        assert operacion.tipo_operacion == TipoOperacion.GASTO
        assert operacion.proveedor == 'AWS Inc'
        assert operacion.monto_usd == Decimal('350')
        assert operacion.monto_uyu == Decimal('14000')  # 350*40


# ══════════════════════════════════════════════════════════════
# TESTS: crear_retiro() - Lógica compleja con 2 monedas
# ══════════════════════════════════════════════════════════════

class TestCrearRetiro:
    """Tests de crear_retiro (maneja ambas monedas)"""
    
    @pytest.mark.integration
    def test_crear_retiro_solo_uyu(self, db_session):
        """Retiro solo en UYU debe calcular USD"""
        data = RetiroCreate(
            monto_uyu=Decimal('10000'),
            monto_usd=None,
            tipo_cambio=Decimal('40.00'),
            fecha=date.today(),
            localidad='Montevideo',
            descripcion='Retiro efectivo Bruno'
        )
        
        operacion = crear_retiro(db_session, data)
        
        assert operacion.tipo_operacion == TipoOperacion.RETIRO
        assert operacion.monto_uyu == Decimal('10000')
        assert operacion.monto_usd == Decimal('250')  # 10000/40
        assert operacion.monto_original == Decimal('10000')
        assert operacion.moneda_original == Moneda.UYU
    
    @pytest.mark.integration
    def test_crear_retiro_solo_usd(self, db_session):
        """Retiro solo en USD debe calcular UYU"""
        data = RetiroCreate(
            monto_uyu=None,
            monto_usd=Decimal('500'),
            tipo_cambio=Decimal('40.00'),
            fecha=date.today(),
            localidad='Mercedes',
            descripcion='Retiro USD Agustina'
        )
        
        operacion = crear_retiro(db_session, data)
        
        assert operacion.tipo_operacion == TipoOperacion.RETIRO
        assert operacion.monto_usd == Decimal('500')
        assert operacion.monto_uyu == Decimal('20000')  # 500*40
        assert operacion.monto_original == Decimal('500')
        assert operacion.moneda_original == Moneda.USD
    
    @pytest.mark.integration
    def test_crear_retiro_ambas_monedas(self, db_session):
        """Retiro con ambos montos debe usar valores exactos"""
        data = RetiroCreate(
            monto_uyu=Decimal('12000'),
            monto_usd=Decimal('300'),
            tipo_cambio=Decimal('40.00'),
            fecha=date.today(),
            localidad='Montevideo',
            descripcion='Retiro mixto'
        )
        
        operacion = crear_retiro(db_session, data)
        
        assert operacion.tipo_operacion == TipoOperacion.RETIRO
        assert operacion.monto_uyu == Decimal('12000')
        assert operacion.monto_usd == Decimal('300')
        # Cuando hay ambos, prioriza UYU como monto_original
        assert operacion.monto_original == Decimal('12000')
        assert operacion.moneda_original == Moneda.UYU
    
    @pytest.mark.integration
    def test_crear_retiro_asigna_area_gastos(self, db_session):
        """Retiro debe asignarse automáticamente a Gastos Generales"""
        data = RetiroCreate(
            monto_uyu=Decimal('5000'),
            monto_usd=None,
            tipo_cambio=Decimal('40.00'),
            fecha=date.today(),
            localidad='Montevideo',
            descripcion='Test'
        )
        
        operacion = crear_retiro(db_session, data)
        
        # Debe buscar área "Gastos Generales"
        assert operacion.area_id is not None
        area = db_session.query(Area).filter(Area.id == operacion.area_id).first()
        assert area.nombre == "Gastos Generales"


# ══════════════════════════════════════════════════════════════
# TESTS: crear_distribucion() - Lógica compleja 5 socios
# ══════════════════════════════════════════════════════════════

class TestCrearDistribucion:
    """Tests de crear_distribucion (5 socios)"""
    
    @pytest.mark.integration
    def test_crear_distribucion_5_socios_completa(self, db_session, socios_test):
        """Distribución con los 5 socios debe crear operación + 5 detalles"""
        if len(socios_test) < 5:
            pytest.skip("No hay 5 socios en BD de test")
        
        data = DistribucionCreate(
            fecha=date.today(),
            tipo_cambio=Decimal('40.00'),
            localidad='Montevideo',
            agustina_uyu=Decimal('5000'),
            agustina_usd=Decimal('125'),
            viviana_uyu=Decimal('5000'),
            viviana_usd=Decimal('125'),
            gonzalo_uyu=Decimal('5000'),
            gonzalo_usd=Decimal('125'),
            pancho_uyu=Decimal('5000'),
            pancho_usd=Decimal('125'),
            bruno_uyu=Decimal('5000'),
            bruno_usd=Decimal('125')
        )
        
        operacion = crear_distribucion(db_session, data)
        
        assert operacion.tipo_operacion == TipoOperacion.DISTRIBUCION
        assert operacion.monto_uyu == Decimal('25000')  # 5*5000
        assert operacion.monto_usd == Decimal('625')    # 5*125
        assert operacion.descripcion == "Distribución de utilidades"
        
        # Verificar que se crearon 5 detalles
        detalles = db_session.query(DistribucionDetalle)\
            .filter(DistribucionDetalle.operacion_id == operacion.id)\
            .all()
        
        assert len(detalles) == 5
    
    @pytest.mark.integration
    def test_crear_distribucion_parcial_3_socios(self, db_session, socios_test):
        """Distribución solo a 3 socios debe crear solo 3 detalles"""
        if len(socios_test) < 3:
            pytest.skip("No hay suficientes socios en BD de test")
        
        data = DistribucionCreate(
            fecha=date.today(),
            tipo_cambio=Decimal('40.00'),
            localidad='Montevideo',
            agustina_uyu=Decimal('10000'),
            agustina_usd=None,
            viviana_uyu=Decimal('10000'),
            viviana_usd=None,
            bruno_uyu=Decimal('10000'),
            bruno_usd=None,
            gonzalo_uyu=None,
            gonzalo_usd=None,
            pancho_uyu=None,
            pancho_usd=None
        )
        
        operacion = crear_distribucion(db_session, data)
        
        assert operacion.monto_uyu == Decimal('30000')  # 3*10000
        
        # Verificar solo 3 detalles creados
        detalles = db_session.query(DistribucionDetalle)\
            .filter(DistribucionDetalle.operacion_id == operacion.id)\
            .all()
        
        assert len(detalles) == 3
    
    @pytest.mark.integration
    def test_crear_distribucion_detecta_moneda_original(self, db_session, socios_test):
        """Si total_uyu > 0, moneda_original debe ser UYU"""
        if len(socios_test) < 2:
            pytest.skip("No hay suficientes socios")
        
        data = DistribucionCreate(
            fecha=date.today(),
            tipo_cambio=Decimal('40.00'),
            localidad='Montevideo',
            agustina_uyu=Decimal('8000'),
            agustina_usd=None,
            viviana_uyu=Decimal('8000'),
            viviana_usd=None,
            bruno_uyu=None,
            bruno_usd=None,
            gonzalo_uyu=None,
            gonzalo_usd=None,
            pancho_uyu=None,
            pancho_usd=None
        )
        
        operacion = crear_distribucion(db_session, data)
        
        assert operacion.monto_original == Decimal('16000')
        assert operacion.moneda_original == Moneda.UYU
    
    @pytest.mark.integration
    def test_crear_distribucion_asigna_area_gastos(self, db_session, socios_test):
        """Distribución debe asignarse a Gastos Generales"""
        if len(socios_test) < 1:
            pytest.skip("No hay socios")
        
        data = DistribucionCreate(
            fecha=date.today(),
            tipo_cambio=Decimal('40.00'),
            localidad='Montevideo',
            bruno_uyu=Decimal('5000'),
            bruno_usd=None,
            agustina_uyu=None,
            agustina_usd=None,
            viviana_uyu=None,
            viviana_usd=None,
            gonzalo_uyu=None,
            gonzalo_usd=None,
            pancho_uyu=None,
            pancho_usd=None
        )
        
        operacion = crear_distribucion(db_session, data)
        
        area = db_session.query(Area).filter(Area.id == operacion.area_id).first()
        assert area.nombre == "Gastos Generales"
    
    @pytest.mark.integration
    def test_crear_distribucion_porcentaje_20(self, db_session, socios_test):
        """Cada detalle debe tener 20% (5 socios = 100%)"""
        if len(socios_test) < 1:
            pytest.skip("No hay socios")
        
        data = DistribucionCreate(
            fecha=date.today(),
            tipo_cambio=Decimal('40.00'),
            localidad='Montevideo',
            bruno_uyu=Decimal('5000'),
            bruno_usd=Decimal('125'),
            agustina_uyu=None,
            agustina_usd=None,
            viviana_uyu=None,
            viviana_usd=None,
            gonzalo_uyu=None,
            gonzalo_usd=None,
            pancho_uyu=None,
            pancho_usd=None
        )
        
        operacion = crear_distribucion(db_session, data)
        
        detalles = db_session.query(DistribucionDetalle)\
            .filter(DistribucionDetalle.operacion_id == operacion.id)\
            .all()
        
        for detalle in detalles:
            assert detalle.porcentaje == 20.0


# ══════════════════════════════════════════════════════════════
# TESTS: Casos edge y validaciones
# ══════════════════════════════════════════════════════════════

class TestCasosEdge:
    """Tests de casos extremos y validaciones"""
    
    def test_calcular_montos_monto_cero(self):
        """Monto cero debe retornar cero en ambas monedas"""
        monto_uyu, monto_usd = calcular_montos(
            monto_original=Decimal('0'),
            moneda_original='UYU',
            tipo_cambio=Decimal('40.00')
        )
        
        assert monto_uyu == Decimal('0')
        assert monto_usd == Decimal('0')
    
    def test_calcular_montos_tipo_cambio_alto(self):
        """TC muy alto (50.00) debe funcionar"""
        monto_uyu, monto_usd = calcular_montos(
            monto_original=Decimal('50000'),
            moneda_original='UYU',
            tipo_cambio=Decimal('50.00')
        )
        
        assert monto_uyu == Decimal('50000')
        assert monto_usd == Decimal('1000')
    
    @pytest.mark.integration
    def test_crear_ingreso_sin_cliente(self, db_session, area_test):
        """Ingreso sin cliente debe funcionar (cliente puede ser null)"""
        data = IngresoCreate(
            cliente=None,
            area_id=area_test.id,
            monto_original=Decimal('5000'),
            moneda_original='UYU',
            tipo_cambio=Decimal('40.00'),
            fecha=date.today(),
            localidad='Montevideo',
            descripcion='Ingreso sin cliente específico'
        )
        
        operacion = crear_ingreso(db_session, data)
        
        assert operacion.cliente is None
        assert operacion.tipo_operacion == TipoOperacion.INGRESO

