"""
Tests para Charts

Tests unitarios para BarChart, LineChart, PieChart, WaterfallChart,
DonutChart, ComboChart, HeatmapChart.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

import pytest
from pathlib import Path
import tempfile
import os

from app.services.charts.bar_chart import BarChart
from app.services.charts.line_chart import LineChart
from app.services.charts.pie_chart import PieChart
from app.services.charts.waterfall_chart import WaterfallChart
from app.services.charts.donut_chart import DonutChart
from app.services.charts.combo_chart import ComboChart
from app.services.charts.heatmap_chart import HeatmapChart
from app.services.charts.chart_factory import ChartFactory


# ═══════════════════════════════════════════════════════════════
# TESTS: BarChart
# ═══════════════════════════════════════════════════════════════

def test_bar_chart_validate_data_valid():
    """Test: BarChart valida datos correctos."""
    data = {
        'categories': ['A', 'B'],
        'series': [
            {'name': 'Serie 1', 'values': [100, 200]}
        ]
    }
    
    chart = BarChart(data, {})
    chart.validate_data()  # No debe lanzar excepción


def test_bar_chart_validate_data_invalid():
    """Test: BarChart rechaza datos inválidos."""
    data = {'categories': ['A', 'B']}  # Falta 'series'
    
    chart = BarChart(data, {})
    
    with pytest.raises(ValueError, match="series"):
        chart.validate_data()


# ═══════════════════════════════════════════════════════════════
# TESTS: LineChart
# ═══════════════════════════════════════════════════════════════

def test_line_chart_validate_data_valid():
    """Test: LineChart valida datos correctos."""
    data = {
        'labels': ['Ene', 'Feb', 'Mar'],
        'series': [
            {'name': 'Ingresos', 'values': [100, 120, 115]}
        ]
    }
    
    chart = LineChart(data, {})
    chart.validate_data()  # No debe lanzar


def test_line_chart_validate_mismatched_lengths():
    """Test: LineChart detecta longitudes diferentes."""
    data = {
        'labels': ['Ene', 'Feb'],
        'series': [
            {'name': 'Ingresos', 'values': [100, 120, 115]}  # 3 valores, 2 labels
        ]
    }
    
    chart = LineChart(data, {})
    
    with pytest.raises(ValueError):
        chart.validate_data()


# ═══════════════════════════════════════════════════════════════
# TESTS: PieChart
# ═══════════════════════════════════════════════════════════════

def test_pie_chart_validate_data_valid():
    """Test: PieChart valida datos correctos."""
    data = {
        'labels': ['A', 'B', 'C'],
        'values': [100, 200, 300]
    }
    
    chart = PieChart(data, {})
    chart.validate_data()


def test_pie_chart_negative_values():
    """Test: PieChart rechaza valores negativos."""
    data = {
        'labels': ['A', 'B'],
        'values': [100, -50]  # Negativo inválido
    }
    
    chart = PieChart(data, {})
    
    with pytest.raises(ValueError, match="positivos"):
        chart.validate_data()


# ═══════════════════════════════════════════════════════════════
# TESTS: WaterfallChart
# ═══════════════════════════════════════════════════════════════

def test_waterfall_chart_validate_data():
    """Test: WaterfallChart valida estructura completa."""
    data = {
        'labels': ['Ingresos', 'Gastos', 'Resultado'],
        'values': [100000, -40000, 60000],
        'measures': ['absolute', 'relative', 'total']
    }
    
    chart = WaterfallChart(data, {})
    chart.validate_data()


def test_waterfall_chart_invalid_measure():
    """Test: WaterfallChart rechaza measures inválidos."""
    data = {
        'labels': ['A'],
        'values': [100],
        'measures': ['invalid']  # No es absolute/relative/total
    }
    
    chart = WaterfallChart(data, {})
    
    with pytest.raises(ValueError, match="inválido"):
        chart.validate_data()


# ═══════════════════════════════════════════════════════════════
# TESTS: DonutChart
# ═══════════════════════════════════════════════════════════════

def test_donut_chart_validate_data():
    """Test: DonutChart valida datos."""
    data = {
        'labels': ['Socio 1', 'Socio 2'],
        'values': [50000, 50000]
    }
    
    chart = DonutChart(data, {})
    chart.validate_data()


# ═══════════════════════════════════════════════════════════════
# TESTS: ComboChart
# ═══════════════════════════════════════════════════════════════

def test_combo_chart_validate_data():
    """Test: ComboChart valida barras + líneas."""
    data = {
        'labels': ['Ene', 'Feb'],
        'bar_series': [{'name': 'Real', 'values': [100, 120]}],
        'line_series': [{'name': 'Proyección', 'values': [110, 130]}]
    }
    
    chart = ComboChart(data, {})
    chart.validate_data()


# ═══════════════════════════════════════════════════════════════
# TESTS: HeatmapChart
# ═══════════════════════════════════════════════════════════════

def test_heatmap_chart_validate_data():
    """Test: HeatmapChart valida matriz."""
    data = {
        'x_labels': ['Ene', 'Feb'],
        'y_labels': ['Notarial', 'Jurídica'],
        'values': [[75.5, 78.2], [70.1, 72.4]]
    }
    
    chart = HeatmapChart(data, {})
    chart.validate_data()


def test_heatmap_chart_invalid_dimensions():
    """Test: HeatmapChart detecta dimensiones incorrectas."""
    data = {
        'x_labels': ['Ene', 'Feb'],
        'y_labels': ['Notarial'],
        'values': [[75.5, 78.2], [70.1, 72.4]]  # 2 filas, 1 y_label
    }
    
    chart = HeatmapChart(data, {})
    
    with pytest.raises(ValueError):
        chart.validate_data()


# ═══════════════════════════════════════════════════════════════
# TESTS: ChartFactory
# ═══════════════════════════════════════════════════════════════

def test_chart_factory_create_bar():
    """Test: ChartFactory crea BarChart."""
    data = {
        'categories': ['A'],
        'series': [{'name': 'S1', 'values': [100]}]
    }
    
    chart = ChartFactory.create('bar', data)
    
    assert isinstance(chart, BarChart)


def test_chart_factory_create_invalid_type():
    """Test: ChartFactory rechaza tipo inválido."""
    with pytest.raises(ValueError, match="no existe"):
        ChartFactory.create('invalid_type', {})


def test_chart_factory_get_available_types():
    """Test: ChartFactory retorna tipos disponibles."""
    types = ChartFactory.get_available_types()
    
    assert 'line' in types
    assert 'bar' in types
    assert 'waterfall' in types
    assert len(types) >= 7

