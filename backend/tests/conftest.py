"""
Pytest Configuration

Configuración global y fixtures compartidos.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

import pytest
import sys
from pathlib import Path

# Agregar backend al path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


@pytest.fixture
def sample_metricas():
    """Fixture con métricas sample para tests."""
    from decimal import Decimal
    from datetime import date
    
    return {
        'ingresos_uyu': Decimal('114941988.84'),
        'ingresos_usd': Decimal('2873549.72'),
        'gastos_uyu': Decimal('76486651.33'),
        'gastos_usd': Decimal('1912166.28'),
        'retiros_uyu': Decimal('5000000.00'),
        'retiros_usd': Decimal('125000.00'),
        'distribuciones_uyu': Decimal('1867997.16'),
        'distribuciones_usd': Decimal('46699.93'),
        'resultado_operativo_uyu': Decimal('38455337.51'),
        'resultado_operativo_usd': Decimal('961383.44'),
        'resultado_neto_uyu': Decimal('31587340.35'),
        'resultado_neto_usd': Decimal('789683.51'),
        'margen_operativo': 33.46,
        'margen_neto': 27.48,
        'rentabilidad_por_area': {
            'Notarial': 78.61,
            'Jurídica': 75.94,
            'Contable': 68.23
        },
        'rentabilidad_por_localidad': {
            'MONTEVIDEO': 77.42,
            'MERCEDES': 72.11
        },
        'porcentaje_ingresos_por_area': {
            'Notarial': 45.5,
            'Jurídica': 34.2,
            'Contable': 20.3
        },
        'porcentaje_ingresos_por_localidad': {
            'MONTEVIDEO': 65.0,
            'MERCEDES': 35.0
        },
        'porcentaje_distribucion_por_socio': {},
        'ticket_promedio_ingreso': 12500.50,
        'ticket_promedio_gasto': 8200.30,
        'cantidad_operaciones': 245,
        'cantidad_ingresos': 150,
        'cantidad_gastos': 95,
        'variacion_mom_ingresos': None,
        'variacion_mom_gastos': None,
        'variacion_mom_rentabilidad': None,
        'promedio_movil_3m': None,
        'promedio_movil_6m': None,
        'proyeccion_proximos_3m': None,
        'area_lider': {
            'nombre': 'Notarial',
            'porcentaje': 45.5,
            'rentabilidad': 78.61
        },
        'localidad_lider': {
            'nombre': 'MONTEVIDEO',
            'porcentaje': 65.0
        },
        'fecha_inicio': date(2025, 10, 1),
        'fecha_fin': date(2025, 10, 31),
        'duracion_dias': 31,
        'period_label': 'Octubre 2025',
        'tiene_comparacion': False
    }

