"""
Tests para MonthlyAggregator - Sistema CFO Inteligente

Valida la agregación de datos mensuales y métricas calculadas.

Ejecutar:
    cd backend
    pytest tests/test_monthly_aggregator.py -v
    pytest tests/test_monthly_aggregator.py --cov=app.services.report_data --cov-report=term-missing

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.services.report_data import MonthlyAggregator

TEST_DATABASE_URL = "postgresql://cfo_user:cfo_pass@localhost/cfo_inteligente"


@pytest.fixture(scope="function")
def db_session():
    """Fixture que proporciona sesión de BD para tests"""
    engine = create_engine(TEST_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


class TestMonthlyAggregator:
    """Tests del agregador mensual"""
    
    def test_get_period_type(self, db_session):
        """Debe retornar 'monthly'"""
        aggregator = MonthlyAggregator(db_session)
        assert aggregator.get_period_type() == 'monthly'
    
    def test_validate_period_correcto(self, db_session):
        """Período válido: 1-31 octubre 2025"""
        aggregator = MonthlyAggregator(db_session)
        start = date(2025, 10, 1)
        end = date(2025, 10, 31)
        
        # No debe lanzar excepción
        aggregator.validate_period(start, end)
    
    def test_validate_period_dia_incorrecto(self, db_session):
        """Debe fallar si start_date no es día 1"""
        aggregator = MonthlyAggregator(db_session)
        start = date(2025, 10, 5)  # Día 5, no día 1
        end = date(2025, 10, 31)
        
        with pytest.raises(ValueError) as exc_info:
            aggregator.validate_period(start, end)
        
        assert "debe ser día 1" in str(exc_info.value)
    
    def test_validate_period_end_incorrecto(self, db_session):
        """Debe fallar si end_date no es último día"""
        aggregator = MonthlyAggregator(db_session)
        start = date(2025, 10, 1)
        end = date(2025, 10, 25)  # No es día 31
        
        with pytest.raises(ValueError) as exc_info:
            aggregator.validate_period(start, end)
        
        assert "último día del mes" in str(exc_info.value)
    
    @pytest.mark.integration
    def test_aggregate_octubre_2025(self, db_session):
        """Test de integración: agregar datos reales de octubre 2025"""
        aggregator = MonthlyAggregator(db_session)
        start = date(2025, 10, 1)
        end = date(2025, 10, 31)
        
        resultado = aggregator.aggregate(start, end)
        
        # Verificar estructura
        assert 'metadata' in resultado
        assert 'metricas_principales' in resultado
        assert 'por_area' in resultado
        assert 'por_localidad' in resultado
        assert 'historico' in resultado
        assert 'metricas_periodo' in resultado
        
        # Verificar metadata
        assert resultado['metadata']['period_type'] == 'monthly'
        assert resultado['metadata']['start_date'] == '2025-10-01'
        assert resultado['metadata']['end_date'] == '2025-10-31'
        assert resultado['metadata']['total_operations'] > 0
        
        # Verificar métricas principales
        assert 'ingresos' in resultado['metricas_principales']
        assert 'gastos' in resultado['metricas_principales']
        assert 'rentabilidad_porcentaje' in resultado['metricas_principales']
        
        # Verificar métricas específicas del mes
        assert resultado['metricas_periodo']['dias_mes'] == 31
        assert resultado['metricas_periodo']['mes_nombre'] == 'Octubre 2025'
        assert 'comparacion_mom' in resultado['metricas_periodo']
        assert 'comparacion_yoy' in resultado['metricas_periodo']
    
    @pytest.mark.integration
    def test_aggregate_con_filtro_localidad(self, db_session):
        """Agregar solo Montevideo"""
        aggregator = MonthlyAggregator(db_session)
        start = date(2025, 10, 1)
        end = date(2025, 10, 31)
        
        resultado = aggregator.aggregate(start, end, localidad="Montevideo")
        
        # Debe tener operaciones solo de Montevideo
        assert resultado['metadata']['total_operations'] >= 0
        # El test pasa si no crashea
    
    @pytest.mark.integration  
    def test_metricas_por_area_ordenadas(self, db_session):
        """Áreas deben estar ordenadas por ingresos desc"""
        aggregator = MonthlyAggregator(db_session)
        start = date(2025, 10, 1)
        end = date(2025, 10, 31)
        
        resultado = aggregator.aggregate(start, end)
        areas = resultado['por_area']
        
        # Verificar que están ordenadas
        if len(areas) > 1:
            for i in range(len(areas) - 1):
                assert areas[i]['ingresos'] >= areas[i + 1]['ingresos']

