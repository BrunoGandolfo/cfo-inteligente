"""
Tests para AI Components

Tests unitarios para parsers, prompts, y generators.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

import pytest
import json

from app.services.ai.response_parser import parse_insights_response, validate_insights
from app.services.ai.fallback_generator import (
    generate_operativo_fallback,
    generate_estrategico_fallback
)


# ═══════════════════════════════════════════════════════════════
# TESTS: parse_insights_response
# ═══════════════════════════════════════════════════════════════

def test_parse_insights_json_directo():
    """Test: Parser maneja JSON directo."""
    response = '{"insight_1": "Texto insight 1", "insight_2": "Texto 2"}'
    
    insights = parse_insights_response(response)
    
    assert insights['insight_1'] == 'Texto insight 1'
    assert insights['insight_2'] == 'Texto 2'


def test_parse_insights_json_markdown():
    """Test: Parser maneja JSON en markdown."""
    response = '''```json
{
  "insight_1": "Texto 1",
  "insight_2": "Texto 2"
}
```'''
    
    insights = parse_insights_response(response)
    
    assert 'insight_1' in insights
    assert 'insight_2' in insights


def test_parse_insights_texto_plano():
    """Test: Parser maneja texto plano como fallback."""
    response = "1. Insight uno\n2. Insight dos"
    
    insights = parse_insights_response(response)
    
    # Debe retornar algo (aunque sea con 'error' key)
    assert isinstance(insights, dict)


def test_parse_insights_response_vacia():
    """Test: Parser maneja response vacía."""
    insights = parse_insights_response('')
    
    assert 'error' in insights


# ═══════════════════════════════════════════════════════════════
# TESTS: validate_insights
# ═══════════════════════════════════════════════════════════════

def test_validate_insights_valid():
    """Test: validate_insights con insights válidos."""
    insights = {'insight_1': 'Texto', 'insight_2': 'Texto 2'}
    
    assert validate_insights(insights) is True


def test_validate_insights_required_keys():
    """Test: validate_insights con keys requeridas."""
    insights = {'insight_1': 'Texto'}
    
    assert validate_insights(insights, required_keys=['insight_1']) is True
    assert validate_insights(insights, required_keys=['insight_2']) is False


def test_validate_insights_invalid():
    """Test: validate_insights rechaza inválidos."""
    assert validate_insights(None) is False
    assert validate_insights({}) is False
    assert validate_insights("string") is False


# ═══════════════════════════════════════════════════════════════
# TESTS: generate_operativo_fallback
# ═══════════════════════════════════════════════════════════════

def test_fallback_operativo_genera_insights():
    """Test: Fallback operativo genera insights."""
    metricas = {
        'ingresos_uyu': 100000.0,
        'gastos_uyu': 30000.0,
        'margen_operativo': 70.0,
        'margen_neto': 55.0,
        'area_lider': {'nombre': 'Notarial', 'porcentaje': 45.0},
        'ticket_promedio_ingreso': 12500.0,
        'cantidad_operaciones': 8
    }
    
    insights = generate_operativo_fallback(metricas)
    
    assert 'insight_1' in insights
    assert 'insight_2' in insights
    assert 'insight_3' in insights
    assert '_generated_by' in insights
    assert insights['_generated_by'] == 'fallback_operativo'


def test_fallback_operativo_menciona_numeros():
    """Test: Fallback operativo menciona números concretos."""
    metricas = {
        'ingresos_uyu': 100000.0,
        'gastos_uyu': 30000.0,
        'rentabilidad_neta': 70.0,
        'area_lider': {'nombre': 'Notarial', 'porcentaje': 45.0},
        'ticket_promedio_ingreso': 12500.0,
        'cantidad_operaciones': 8
    }
    
    insights = generate_operativo_fallback(metricas)
    
    # Debe mencionar porcentaje
    assert '70' in insights['insight_1'] or '70.0' in insights['insight_1']


# ═══════════════════════════════════════════════════════════════
# TESTS: generate_estrategico_fallback
# ═══════════════════════════════════════════════════════════════

def test_fallback_estrategico_genera_insights():
    """Test: Fallback estratégico genera insights."""
    metricas = {
        'ingresos_uyu': 500000.0,
        'rentabilidad_neta': 35.0,
        'duracion_dias': 90,
        'rentabilidad_por_area': {'Notarial': 78.5, 'Jurídica': 65.2},
        'porcentaje_ingresos_por_area': {'Notarial': 55.0, 'Jurídica': 45.0}
    }
    
    insights = generate_estrategico_fallback(metricas)
    
    assert 'tendencia' in insights
    assert 'patron' in insights
    assert 'oportunidad' in insights
    assert 'riesgo' in insights
    assert '_generated_by' in insights


def test_fallback_estrategico_identifica_disparidad():
    """Test: Fallback estratégico identifica disparidad en áreas."""
    metricas = {
        'ingresos_uyu': 500000.0,
        'rentabilidad_neta': 35.0,
        'duracion_dias': 90,
        'rentabilidad_por_area': {'Notarial': 80.0, 'Jurídica': 40.0},  # Brecha grande
        'porcentaje_ingresos_por_area': {'Notarial': 50.0, 'Jurídica': 50.0}
    }
    
    insights = generate_estrategico_fallback(metricas)
    
    # Debe mencionar disparidad
    assert 'Notarial' in insights['patron']
    assert 'Jurídica' in insights['patron']

