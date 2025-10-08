"""
Tests para Validators

Tests unitarios para validadores de request y data.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

import pytest
from datetime import date
from unittest.mock import Mock

from app.services.validators.request_validator import (
    validate_dates,
    validate_period,
    validate_comparison,
    validate_options
)
from app.services.validators.data_validator import (
    validate_sufficient_data,
    validate_data_quality
)
from app.core.exceptions import InvalidDateRangeError, InsufficientDataError
from app.schemas.report.request import PeriodConfig, ComparisonConfig, ReportOptions


# ═══════════════════════════════════════════════════════════════
# TESTS: validate_dates
# ═══════════════════════════════════════════════════════════════

def test_validate_dates_valid():
    """Test: validate_dates con fechas válidas."""
    # Usar fechas pasadas (septiembre 2025)
    validate_dates(date(2025, 9, 1), date(2025, 9, 30))
    # No debe lanzar excepción


def test_validate_dates_fin_antes_inicio():
    """Test: validate_dates rechaza fecha_fin < fecha_inicio."""
    with pytest.raises(InvalidDateRangeError, match="debe ser mayor"):
        validate_dates(date(2025, 10, 31), date(2025, 10, 1))


def test_validate_dates_futuras():
    """Test: validate_dates rechaza fechas futuras."""
    futuro = date(2099, 12, 31)
    
    with pytest.raises(InvalidDateRangeError, match="futura"):
        validate_dates(futuro, futuro)


def test_validate_dates_excede_maximo():
    """Test: validate_dates rechaza rango > max_days."""
    # Usar fechas pasadas pero con rango largo
    with pytest.raises(InvalidDateRangeError, match="excede máximo"):
        validate_dates(
            date(2024, 1, 1),
            date(2025, 6, 30),  # Más de 365 días
            max_days=365
        )


# ═══════════════════════════════════════════════════════════════
# TESTS: validate_period
# ═══════════════════════════════════════════════════════════════

def test_validate_period_predefinido():
    """Test: validate_period con tipo predefinido."""
    period = PeriodConfig(tipo='mes_actual')
    validate_period(period)
    # No debe lanzar


def test_validate_period_custom_valid():
    """Test: validate_period custom válido."""
    # Usar fechas pasadas
    period = PeriodConfig(
        tipo='custom',
        fecha_inicio=date(2025, 9, 1),
        fecha_fin=date(2025, 9, 30)
    )
    validate_period(period)


def test_validate_period_custom_sin_fechas():
    """Test: validate_period custom sin fechas lanza error."""
    period = PeriodConfig(tipo='custom')
    
    with pytest.raises(InvalidDateRangeError, match="requiere"):
        validate_period(period)


# ═══════════════════════════════════════════════════════════════
# TESTS: validate_options
# ═══════════════════════════════════════════════════════════════

def test_validate_options_valid():
    """Test: validate_options con opciones válidas."""
    options = ReportOptions(
        formato='ejecutivo',
        paleta='moderna_2024'
    )
    validate_options(options)


# ═══════════════════════════════════════════════════════════════
# TESTS: validate_sufficient_data
# ═══════════════════════════════════════════════════════════════

def test_validate_sufficient_data_ok():
    """Test: validate_sufficient_data con datos suficientes."""
    ops = [Mock() for _ in range(25)]
    validate_sufficient_data(ops, minimo_requerido=20)
    # No debe lanzar


def test_validate_sufficient_data_insuficientes():
    """Test: validate_sufficient_data rechaza datos insuficientes."""
    ops = [Mock() for _ in range(15)]
    
    with pytest.raises(InsufficientDataError):
        validate_sufficient_data(ops, minimo_requerido=20)


# ═══════════════════════════════════════════════════════════════
# TESTS: validate_data_quality
# ═══════════════════════════════════════════════════════════════

def test_validate_data_quality():
    """Test: validate_data_quality retorna reporte."""
    ops = []
    for i in range(10):
        op = Mock()
        op.area_id = 'uuid' if i < 8 else None
        op.descripcion = 'Desc' if i < 5 else None
        ops.append(op)
    
    report = validate_data_quality(ops)
    
    assert report['total'] == 10
    assert report['con_area'] == 8
    assert report['sin_area'] == 2
    assert len(report['warnings']) > 0

