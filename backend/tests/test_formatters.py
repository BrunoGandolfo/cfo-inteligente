"""
Tests para Formatters

Tests unitarios para funciones de formateo.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

import pytest
from datetime import date
from decimal import Decimal

from app.utils.formatters import (
    format_currency,
    format_percentage,
    format_date_es,
    format_variacion,
    format_number
)


# ═══════════════════════════════════════════════════════════════
# TESTS: format_currency
# ═══════════════════════════════════════════════════════════════

def test_format_currency_normal():
    """Test: format_currency formatea con separador de miles."""
    assert format_currency(1234567.89) == '$1,234,568'


def test_format_currency_short_millions():
    """Test: format_currency modo short con millones."""
    assert format_currency(1234567.89, short=True) == '$1.2M'


def test_format_currency_short_thousands():
    """Test: format_currency modo short con miles."""
    assert format_currency(150000, short=True) == '$150K'


def test_format_currency_short_small():
    """Test: format_currency modo short con valores pequeños."""
    assert format_currency(500, short=True) == '$500'


def test_format_currency_without_symbol():
    """Test: format_currency sin símbolo $."""
    assert format_currency(1000, include_currency=False) == '1,000'


# ═══════════════════════════════════════════════════════════════
# TESTS: format_percentage
# ═══════════════════════════════════════════════════════════════

def test_format_percentage_default():
    """Test: format_percentage con defaults."""
    assert format_percentage(33.456) == '33.46%'


def test_format_percentage_decimals():
    """Test: format_percentage con decimales custom."""
    assert format_percentage(100.0, decimals=1) == '100.0%'


def test_format_percentage_negative():
    """Test: format_percentage con negativo."""
    assert format_percentage(-5.5, decimals=0) == '-6%'


def test_format_percentage_without_symbol():
    """Test: format_percentage sin símbolo %."""
    assert format_percentage(50.0, include_symbol=False) == '50.00'


# ═══════════════════════════════════════════════════════════════
# TESTS: format_date_es
# ═══════════════════════════════════════════════════════════════

def test_format_date_es_completo():
    """Test: format_date_es formato completo."""
    fecha = date(2025, 10, 7)
    assert format_date_es(fecha, 'completo') == '07 de Octubre de 2025'


def test_format_date_es_corto():
    """Test: format_date_es formato corto."""
    fecha = date(2025, 10, 7)
    assert format_date_es(fecha, 'corto') == '07/10/2025'


def test_format_date_es_mes_anio():
    """Test: format_date_es formato mes_anio."""
    fecha = date(2025, 10, 7)
    assert format_date_es(fecha, 'mes_anio') == 'Octubre 2025'


# ═══════════════════════════════════════════════════════════════
# TESTS: format_variacion
# ═══════════════════════════════════════════════════════════════

def test_format_variacion_positiva():
    """Test: format_variacion con aumento."""
    result = format_variacion(120, 100, 'porcentual')
    assert '+20.0%' in result
    assert '↗' in result


def test_format_variacion_negativa():
    """Test: format_variacion con descenso."""
    result = format_variacion(80, 100, 'porcentual')
    assert '-20.0%' in result
    assert '↘' in result


def test_format_variacion_puntos():
    """Test: format_variacion tipo puntos."""
    result = format_variacion(65.5, 75.0, 'puntos')
    assert '-9.5pp' in result
    assert '↘' in result


def test_format_variacion_division_por_cero():
    """Test: format_variacion maneja división por cero."""
    result = format_variacion(100, 0, 'porcentual')
    assert result == 'N/A'


# ═══════════════════════════════════════════════════════════════
# TESTS: format_number
# ═══════════════════════════════════════════════════════════════

def test_format_number_default():
    """Test: format_number con defaults."""
    assert format_number(1234567) == '1,234,567'


def test_format_number_decimals():
    """Test: format_number con decimales."""
    assert format_number(1234.56789, decimals=2) == '1,234.57'

