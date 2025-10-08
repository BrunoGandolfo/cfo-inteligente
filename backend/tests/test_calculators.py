"""
Tests para Calculadores de Métricas

Tests unitarios para TotalsCalculator, ResultsCalculator, RatiosCalculator,
DistributionCalculator, EfficiencyCalculator, TrendsCalculator.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import Mock

from app.services.metrics.totals_calculator import TotalsCalculator
from app.services.metrics.results_calculator import ResultsCalculator
from app.services.metrics.ratios_calculator import RatiosCalculator
from app.services.metrics.distribution_calculator import DistributionCalculator
from app.services.metrics.efficiency_calculator import EfficiencyCalculator
from app.services.metrics.trends_calculator import TrendsCalculator
from app.models import TipoOperacion


# ═══════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def mock_operaciones():
    """Fixture con operaciones mock."""
    ops = []
    
    # 2 ingresos
    for i in range(2):
        op = Mock()
        op.tipo_operacion = TipoOperacion.INGRESO
        op.monto_uyu = Decimal('50000')
        op.monto_usd = Decimal('1250')
        op.area = Mock(nombre='Notarial')
        op.localidad = Mock(value='MONTEVIDEO')
        ops.append(op)
    
    # 1 gasto
    op_gasto = Mock()
    op_gasto.tipo_operacion = TipoOperacion.GASTO
    op_gasto.monto_uyu = Decimal('30000')
    op_gasto.monto_usd = Decimal('750')
    op_gasto.area = Mock(nombre='Notarial')
    op_gasto.localidad = Mock(value='MONTEVIDEO')
    ops.append(op_gasto)
    
    return ops


# ═══════════════════════════════════════════════════════════════
# TESTS: TotalsCalculator
# ═══════════════════════════════════════════════════════════════

def test_totals_calculator_ingresos(mock_operaciones):
    """Test: TotalsCalculator calcula ingresos correctamente."""
    calc = TotalsCalculator(mock_operaciones)
    totals = calc.calculate()
    
    assert totals['ingresos_uyu'] == Decimal('100000')  # 2 × 50000
    assert totals['ingresos_usd'] == Decimal('2500')    # 2 × 1250


def test_totals_calculator_gastos(mock_operaciones):
    """Test: TotalsCalculator calcula gastos correctamente."""
    calc = TotalsCalculator(mock_operaciones)
    totals = calc.calculate()
    
    assert totals['gastos_uyu'] == Decimal('30000')
    assert totals['gastos_usd'] == Decimal('750')


def test_totals_calculator_metric_names():
    """Test: TotalsCalculator retorna metric names correctos."""
    calc = TotalsCalculator([])
    names = calc.get_metric_names()
    
    assert len(names) == 8
    assert 'ingresos_uyu' in names
    assert 'gastos_usd' in names


# ═══════════════════════════════════════════════════════════════
# TESTS: ResultsCalculator
# ═══════════════════════════════════════════════════════════════

def test_results_calculator_operativo():
    """Test: ResultsCalculator calcula resultado operativo."""
    totals = {
        'ingresos_uyu': Decimal('100000'),
        'gastos_uyu': Decimal('30000'),
        'ingresos_usd': Decimal('2500'),
        'gastos_usd': Decimal('750'),
        'retiros_uyu': Decimal('0'),
        'retiros_usd': Decimal('0'),
        'distribuciones_uyu': Decimal('0'),
        'distribuciones_usd': Decimal('0')
    }
    
    calc = ResultsCalculator([], totals)
    results = calc.calculate()
    
    assert results['resultado_operativo_uyu'] == Decimal('70000')  # 100k - 30k


def test_results_calculator_neto():
    """Test: ResultsCalculator calcula resultado neto."""
    totals = {
        'ingresos_uyu': Decimal('100000'),
        'gastos_uyu': Decimal('30000'),
        'retiros_uyu': Decimal('10000'),
        'distribuciones_uyu': Decimal('5000'),
        'ingresos_usd': Decimal('0'),
        'gastos_usd': Decimal('0'),
        'retiros_usd': Decimal('0'),
        'distribuciones_usd': Decimal('0')
    }
    
    calc = ResultsCalculator([], totals)
    results = calc.calculate()
    
    # 100k - 30k - 10k - 5k = 55k
    assert results['resultado_neto_uyu'] == Decimal('55000')


def test_results_calculator_metric_names():
    """Test: ResultsCalculator retorna metric names."""
    calc = ResultsCalculator([], {})
    names = calc.get_metric_names()
    
    assert len(names) == 4
    assert 'resultado_operativo_uyu' in names


# ═══════════════════════════════════════════════════════════════
# TESTS: RatiosCalculator
# ═══════════════════════════════════════════════════════════════

def test_ratios_calculator_margen_operativo():
    """Test: RatiosCalculator calcula margen operativo."""
    totals = {
        'ingresos_uyu': Decimal('100000'),
        'gastos_uyu': Decimal('30000'),
        'retiros_uyu': Decimal('0'),
        'distribuciones_uyu': Decimal('0')
    }
    
    calc = RatiosCalculator([], totals)
    ratios = calc.calculate()
    
    # (100k - 30k) / 100k × 100 = 70%
    assert ratios['margen_operativo'] == 70.0


def test_ratios_calculator_margen_neto():
    """Test: RatiosCalculator calcula margen neto."""
    totals = {
        'ingresos_uyu': Decimal('100000'),
        'gastos_uyu': Decimal('30000'),
        'retiros_uyu': Decimal('10000'),
        'distribuciones_uyu': Decimal('5000')
    }
    
    calc = RatiosCalculator([], totals)
    ratios = calc.calculate()
    
    # (100k - 30k - 10k - 5k) / 100k × 100 = 55%
    assert abs(ratios['margen_neto'] - 55.0) < 0.01  # Tolerancia para floats


def test_ratios_calculator_division_por_cero():
    """Test: RatiosCalculator maneja división por cero."""
    totals = {
        'ingresos_uyu': Decimal('0'),
        'gastos_uyu': Decimal('0'),
        'retiros_uyu': Decimal('0'),
        'distribuciones_uyu': Decimal('0')
    }
    
    calc = RatiosCalculator([], totals)
    ratios = calc.calculate()
    
    assert ratios['margen_operativo'] == 0.0


# ═══════════════════════════════════════════════════════════════
# TESTS: DistributionCalculator
# ═══════════════════════════════════════════════════════════════

def test_distribution_calculator_por_area(mock_operaciones):
    """Test: DistributionCalculator calcula distribución por área."""
    totals = {
        'ingresos_uyu': Decimal('100000'),
        'distribuciones_uyu': Decimal('0')
    }
    
    calc = DistributionCalculator(mock_operaciones, totals)
    dist = calc.calculate()
    
    porcentajes = dist['porcentaje_ingresos_por_area']
    
    # Todos son de Notarial, debe ser 100%
    assert 'Notarial' in porcentajes
    assert porcentajes['Notarial'] == 100.0


def test_distribution_calculator_metric_names():
    """Test: DistributionCalculator retorna metric names."""
    calc = DistributionCalculator([], {})
    names = calc.get_metric_names()
    
    assert len(names) == 3
    assert 'porcentaje_ingresos_por_area' in names


# ═══════════════════════════════════════════════════════════════
# TESTS: EfficiencyCalculator
# ═══════════════════════════════════════════════════════════════

def test_efficiency_calculator_ticket_promedio(mock_operaciones):
    """Test: EfficiencyCalculator calcula ticket promedio."""
    totals = {
        'ingresos_uyu': Decimal('100000'),
        'gastos_uyu': Decimal('30000')
    }
    
    calc = EfficiencyCalculator(mock_operaciones, totals)
    eff = calc.calculate()
    
    # 100k / 2 ingresos = 50k promedio
    assert eff['ticket_promedio_ingreso'] == 50000.0


def test_efficiency_calculator_cantidad_operaciones(mock_operaciones):
    """Test: EfficiencyCalculator cuenta operaciones."""
    totals = {
        'ingresos_uyu': Decimal('100000'),
        'gastos_uyu': Decimal('30000')
    }
    calc = EfficiencyCalculator(mock_operaciones, totals)
    eff = calc.calculate()
    
    assert eff['cantidad_operaciones'] == 3  # 2 ingresos + 1 gasto
    assert eff['cantidad_ingresos'] == 2
    assert eff['cantidad_gastos'] == 1


def test_efficiency_calculator_division_por_cero():
    """Test: EfficiencyCalculator maneja división por cero."""
    totals = {'ingresos_uyu': Decimal('100000'), 'gastos_uyu': Decimal('0')}
    
    calc = EfficiencyCalculator([], totals)  # Sin operaciones
    eff = calc.calculate()
    
    assert eff['ticket_promedio_ingreso'] == 0.0  # No hay ingresos para dividir


# ═══════════════════════════════════════════════════════════════
# TESTS: TrendsCalculator
# ═══════════════════════════════════════════════════════════════

def test_trends_calculator_variacion_mom():
    """Test: TrendsCalculator calcula variación MoM."""
    totals = {'ingresos_uyu': Decimal('120000'), 'gastos_uyu': Decimal('30000')}
    ratios = {'margen_operativo': 75.0}
    
    comp_totals = {'ingresos_uyu': Decimal('100000'), 'gastos_uyu': Decimal('25000')}
    comp_ratios = {'margen_operativo': 75.0}
    
    calc = TrendsCalculator(
        operaciones=[],
        totals=totals,
        ratios=ratios,
        comparacion_totals=comp_totals,
        comparacion_ratios=comp_ratios
    )
    
    trends = calc.calculate()
    
    # (120k - 100k) / 100k × 100 = 20%
    assert trends['variacion_mom_ingresos'] == 20.0


def test_trends_calculator_sin_comparacion():
    """Test: TrendsCalculator retorna None sin comparación."""
    totals = {'ingresos_uyu': Decimal('100000'), 'gastos_uyu': Decimal('30000')}
    ratios = {'margen_operativo': 70.0}
    
    calc = TrendsCalculator(
        operaciones=[],
        totals=totals,
        ratios=ratios,
        comparacion_totals=None,  # Sin comparación
        comparacion_ratios=None
    )
    
    trends = calc.calculate()
    
    assert trends['variacion_mom_ingresos'] is None
    assert trends['variacion_mom_gastos'] is None


def test_trends_calculator_proyeccion():
    """Test: TrendsCalculator calcula proyección."""
    totals = {'ingresos_uyu': Decimal('100000'), 'gastos_uyu': Decimal('30000')}
    ratios = {'margen_operativo': 70.0}
    
    # Histórico de 6 meses
    historico = [Decimal('100000'), Decimal('110000'), Decimal('120000'),
                 Decimal('115000'), Decimal('125000'), Decimal('130000')]
    
    calc = TrendsCalculator(
        operaciones=[],
        totals=totals,
        ratios=ratios,
        historico_mensual=historico
    )
    
    trends = calc.calculate()
    
    # Debe tener proyección (no None)
    assert trends['proyeccion_proximos_3m'] is not None
    assert isinstance(trends['proyeccion_proximos_3m'], float)

