"""
Tests para MetricsAggregator

Tests de integración del agregador de métricas.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import Mock

from app.services.metrics.metrics_aggregator import MetricsAggregator
from app.models import TipoOperacion


@pytest.fixture
def sample_operaciones():
    """Fixture con operaciones sample."""
    ops = []
    
    # 3 ingresos
    for i in range(3):
        op = Mock()
        op.tipo_operacion = TipoOperacion.INGRESO
        op.monto_uyu = Decimal('50000')
        op.monto_usd = Decimal('1250')
        op.area = Mock(nombre='Notarial')
        op.localidad = Mock(value='MONTEVIDEO')
        ops.append(op)
    
    # 2 gastos
    for i in range(2):
        op = Mock()
        op.tipo_operacion = TipoOperacion.GASTO
        op.monto_uyu = Decimal('20000')
        op.monto_usd = Decimal('500')
        op.area = Mock(nombre='Notarial')
        op.localidad = Mock(value='MONTEVIDEO')
        ops.append(op)
    
    return ops


def test_aggregator_calcula_todas_metricas(sample_operaciones):
    """Test: MetricsAggregator calcula todas las métricas."""
    aggregator = MetricsAggregator(
        operaciones=sample_operaciones,
        fecha_inicio=date(2025, 10, 1),
        fecha_fin=date(2025, 10, 31)
    )
    
    metricas = aggregator.aggregate_all()
    
    # Debe tener métricas de todos los calculadores
    assert 'ingresos_uyu' in metricas  # TotalsCalculator
    assert 'resultado_operativo_uyu' in metricas  # ResultsCalculator
    assert 'margen_operativo' in metricas  # RatiosCalculator
    assert 'porcentaje_ingresos_por_area' in metricas  # DistributionCalculator
    assert 'ticket_promedio_ingreso' in metricas  # EfficiencyCalculator
    assert 'variacion_mom_ingresos' in metricas  # TrendsCalculator
    
    # Metadata
    assert 'fecha_inicio' in metricas
    assert 'fecha_fin' in metricas
    assert 'period_label' in metricas


def test_aggregator_totals_correctos(sample_operaciones):
    """Test: Totals correctos."""
    aggregator = MetricsAggregator(
        operaciones=sample_operaciones,
        fecha_inicio=date(2025, 10, 1),
        fecha_fin=date(2025, 10, 31)
    )
    
    metricas = aggregator.aggregate_all()
    
    assert metricas['ingresos_uyu'] == Decimal('150000')  # 3 × 50k
    assert metricas['gastos_uyu'] == Decimal('40000')     # 2 × 20k


def test_aggregator_margen_correcto(sample_operaciones):
    """Test: Margen operativo correcto."""
    aggregator = MetricsAggregator(
        operaciones=sample_operaciones,
        fecha_inicio=date(2025, 10, 1),
        fecha_fin=date(2025, 10, 31)
    )
    
    metricas = aggregator.aggregate_all()
    
    # (150k - 40k) / 150k × 100 = 73.33%
    assert abs(metricas['margen_operativo'] - 73.33) < 0.1


def test_aggregator_area_lider(sample_operaciones):
    """Test: Identifica área líder."""
    aggregator = MetricsAggregator(
        operaciones=sample_operaciones,
        fecha_inicio=date(2025, 10, 1),
        fecha_fin=date(2025, 10, 31)
    )
    
    metricas = aggregator.aggregate_all()
    
    assert metricas['area_lider']['nombre'] == 'Notarial'
    assert metricas['area_lider']['porcentaje'] == 100.0


def test_aggregator_con_comparacion(sample_operaciones):
    """Test: Aggregator con período de comparación."""
    # Operaciones comparación (menores)
    ops_comp = []
    for i in range(2):
        op = Mock()
        op.tipo_operacion = TipoOperacion.INGRESO
        op.monto_uyu = Decimal('40000')
        op.monto_usd = Decimal('1000')
        op.area = Mock(nombre='Notarial')
        op.localidad = Mock(value='MONTEVIDEO')
        ops_comp.append(op)
    
    aggregator = MetricsAggregator(
        operaciones=sample_operaciones,
        fecha_inicio=date(2025, 10, 1),
        fecha_fin=date(2025, 10, 31),
        operaciones_comparacion=ops_comp
    )
    
    metricas = aggregator.aggregate_all()
    
    # Debe tener variaciones calculadas
    assert metricas['variacion_mom_ingresos'] is not None
    assert metricas['variacion_mom_ingresos'] > 0  # Crecimiento

