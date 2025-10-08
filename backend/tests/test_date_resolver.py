"""
Tests para Date Resolver

Tests unitarios para resolución de períodos.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

import pytest
from datetime import date

from app.utils.date_resolver import (
    resolve_period,
    get_comparison_period,
    get_period_label
)


# ═══════════════════════════════════════════════════════════════
# TESTS: resolve_period
# ═══════════════════════════════════════════════════════════════

def test_resolve_period_mes_actual():
    """Test: resolve_period mes_actual."""
    fecha_ref = date(2025, 10, 15)
    inicio, fin = resolve_period('mes_actual', fecha_ref=fecha_ref)
    
    assert inicio == date(2025, 10, 1)
    assert fin == date(2025, 10, 31)


def test_resolve_period_mes_anterior():
    """Test: resolve_period mes_anterior."""
    fecha_ref = date(2025, 10, 15)
    inicio, fin = resolve_period('mes_anterior', fecha_ref=fecha_ref)
    
    assert inicio == date(2025, 9, 1)
    assert fin == date(2025, 9, 30)


def test_resolve_period_trimestre_actual():
    """Test: resolve_period trimestre_actual."""
    fecha_ref = date(2025, 10, 15)  # Q4
    inicio, fin = resolve_period('trimestre_actual', fecha_ref=fecha_ref)
    
    assert inicio == date(2025, 10, 1)
    assert fin == date(2025, 12, 31)


def test_resolve_period_custom():
    """Test: resolve_period custom."""
    inicio, fin = resolve_period(
        'custom',
        fecha_inicio_custom=date(2025, 5, 1),
        fecha_fin_custom=date(2025, 5, 31)
    )
    
    assert inicio == date(2025, 5, 1)
    assert fin == date(2025, 5, 31)


def test_resolve_period_custom_sin_fechas():
    """Test: resolve_period custom sin fechas lanza error."""
    with pytest.raises(ValueError, match="requiere"):
        resolve_period('custom')


# ═══════════════════════════════════════════════════════════════
# TESTS: get_comparison_period
# ═══════════════════════════════════════════════════════════════

def test_get_comparison_period_anterior():
    """Test: get_comparison_period período anterior."""
    inicio, fin = get_comparison_period(
        fecha_inicio=date(2025, 10, 1),
        fecha_fin=date(2025, 10, 31),
        tipo_comparacion='periodo_anterior'
    )
    
    # El período es de 31 días (Oct 1-31)
    # Retrocede 31 días desde Oct 1: Sep 30 hacia atrás
    # fecha_fin_comp = Sep 30, fecha_inicio_comp = Aug 31
    assert inicio == date(2025, 8, 31)
    assert fin == date(2025, 9, 30)


def test_get_comparison_period_año_pasado():
    """Test: get_comparison_period mismo período año pasado."""
    inicio, fin = get_comparison_period(
        fecha_inicio=date(2025, 10, 1),
        fecha_fin=date(2025, 10, 31),
        tipo_comparacion='mismo_periodo_año_pasado'
    )
    
    assert inicio == date(2024, 10, 1)
    assert fin == date(2024, 10, 31)


# ═══════════════════════════════════════════════════════════════
# TESTS: get_period_label
# ═══════════════════════════════════════════════════════════════

def test_get_period_label_mes_completo():
    """Test: get_period_label identifica mes completo."""
    label = get_period_label(date(2025, 10, 1), date(2025, 10, 31))
    assert label == 'Octubre 2025'


def test_get_period_label_trimestre():
    """Test: get_period_label identifica trimestre."""
    label = get_period_label(date(2025, 10, 1), date(2025, 12, 31))
    assert label == 'Q4 2025'


def test_get_period_label_año():
    """Test: get_period_label identifica año completo."""
    label = get_period_label(date(2025, 1, 1), date(2025, 12, 31))
    assert label == 'Año 2025'

