"""
Tests para Stats Calculator

Tests unitarios para funciones estadísticas.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

import pytest
import numpy as np

from app.utils.stats_calculator import (
    linear_regression_with_confidence,
    calculate_moving_average,
    detect_outliers_iqr,
    calculate_volatility,
    calculate_growth_rate
)


# ═══════════════════════════════════════════════════════════════
# TESTS: linear_regression_with_confidence
# ═══════════════════════════════════════════════════════════════

def test_linear_regression_basic():
    """Test: Regresión lineal básica."""
    x = [1, 2, 3, 4, 5, 6]
    y = [100, 120, 115, 130, 125, 140]
    x_fut = [7, 8, 9]
    
    y_pred, y_upper, y_lower, r2, slope = linear_regression_with_confidence(x, y, x_fut)
    
    assert len(y_pred) == 3
    assert len(y_upper) == 3
    assert len(y_lower) == 3
    assert 0 <= r2 <= 1
    assert isinstance(slope, float)


def test_linear_regression_r_squared():
    """Test: R² entre 0 y 1."""
    x = [1, 2, 3, 4, 5]
    y = [10, 20, 30, 40, 50]
    x_fut = [6]
    
    _, _, _, r2, _ = linear_regression_with_confidence(x, y, x_fut)
    
    assert 0 <= r2 <= 1


# ═══════════════════════════════════════════════════════════════
# TESTS: calculate_moving_average
# ═══════════════════════════════════════════════════════════════

def test_moving_average_window_3():
    """Test: Promedio móvil ventana 3."""
    values = [10, 20, 30, 40, 50]
    result = calculate_moving_average(values, window=3)
    
    assert result[0] is None
    assert result[1] is None
    assert result[2] == 20.0  # (10+20+30)/3
    assert result[3] == 30.0  # (20+30+40)/3
    assert result[4] == 40.0  # (30+40+50)/3


def test_moving_average_insufficient_data():
    """Test: Promedio móvil con datos insuficientes."""
    values = [10, 20]
    result = calculate_moving_average(values, window=3)
    
    assert result[0] is None
    assert result[1] is None


# ═══════════════════════════════════════════════════════════════
# TESTS: detect_outliers_iqr
# ═══════════════════════════════════════════════════════════════

def test_detect_outliers_with_outlier():
    """Test: Detecta outlier correctamente."""
    values = [10, 12, 11, 13, 100, 12, 11]
    outliers = detect_outliers_iqr(values)
    
    assert 4 in outliers  # El valor 100 es outlier


def test_detect_outliers_without_outliers():
    """Test: No detecta outliers en datos normales."""
    values = [10, 12, 11, 13, 12, 11]
    outliers = detect_outliers_iqr(values)
    
    assert len(outliers) == 0


# ═══════════════════════════════════════════════════════════════
# TESTS: calculate_volatility
# ═══════════════════════════════════════════════════════════════

def test_calculate_volatility():
    """Test: Calcula volatilidad."""
    values = [100, 120, 110, 130, 115]
    std_dev, cv = calculate_volatility(values)
    
    assert std_dev > 0
    assert cv > 0
    assert isinstance(std_dev, float)
    assert isinstance(cv, float)


def test_calculate_volatility_cero_mean():
    """Test: Volatilidad con media cero."""
    values = [0, 0, 0]
    std_dev, cv = calculate_volatility(values)
    
    assert std_dev == 0.0
    assert cv == 0.0


# ═══════════════════════════════════════════════════════════════
# TESTS: calculate_growth_rate
# ═══════════════════════════════════════════════════════════════

def test_calculate_growth_rate():
    """Test: Calcula CAGR."""
    cagr = calculate_growth_rate(100, 121, 2)
    
    assert abs(cagr - 10.0) < 0.1  # ~10% CAGR


def test_calculate_growth_rate_invalid_values():
    """Test: CAGR con valores inválidos."""
    cagr = calculate_growth_rate(0, 100, 2)
    assert cagr == 0.0
    
    cagr = calculate_growth_rate(100, 0, 2)
    assert cagr == 0.0

