"""
Report Data Formatters - Preparación de datos para templates PDF.

Extraído de ReportBuilder para reducir God Object.
"""

from typing import Dict, Any, List, Optional


def prepare_summary_metrics(metricas: Dict[str, Any]) -> List[Dict]:
    """Prepara métricas para summary_grid component."""
    return [
        {
            'label': 'Ingresos Totales',
            'valor': metricas.get('ingresos_uyu', 0),
            'tipo': 'currency',
            'variacion': metricas.get('variacion_mom_ingresos'),
            'color': 'var(--primary)'
        },
        {
            'label': 'Gastos Totales',
            'valor': metricas.get('gastos_uyu', 0),
            'tipo': 'currency',
            'variacion': metricas.get('variacion_mom_gastos'),
            'color': 'var(--danger)'
        },
        {
            'label': 'Utilidad Neta',
            'valor': metricas.get('utilidad_neta_uyu', 0),
            'tipo': 'currency',
            'color': 'var(--success)'
        },
        {
            'label': 'Retiros',
            'valor': metricas.get('retiros_uyu', 0),
            'tipo': 'currency',
            'color': 'var(--warning)'
        },
        {
            'label': 'Distribuciones',
            'valor': metricas.get('distribuciones_uyu', 0),
            'tipo': 'currency',
            'color': 'var(--secondary)'
        },
        {
            'label': 'Rentabilidad Neta',
            'valor': metricas.get('rentabilidad_neta', 0),
            'tipo': 'percentage',
            'variacion': metricas.get('variacion_mom_rentabilidad'),
            'color': 'var(--success)'
        },
        {
            'label': 'Ticket Promedio',
            'valor': metricas.get('ticket_promedio_ingreso', 0),
            'tipo': 'currency',
            'color': 'var(--primary)'
        },
        {
            'label': 'Operaciones',
            'valor': metricas.get('cantidad_operaciones', 0),
            'tipo': 'number',
            'color': 'var(--primary)'
        }
    ]


def prepare_kpis(metricas: Dict[str, Any]) -> List[Dict]:
    """Prepara KPIs para kpi_table component."""
    return [
        {
            'nombre': 'Ingresos',
            'valor': metricas.get('ingresos_uyu', 0),
            'tipo': 'currency',
            'valor_anterior': metricas.get('ingresos_uyu_anterior'),
            'variacion': metricas.get('variacion_mom_ingresos')
        },
        {
            'nombre': 'Gastos',
            'valor': metricas.get('gastos_uyu', 0),
            'tipo': 'currency',
            'valor_anterior': metricas.get('gastos_uyu_anterior'),
            'variacion': metricas.get('variacion_mom_gastos')
        },
        {
            'nombre': 'Rentabilidad Neta',
            'valor': metricas.get('rentabilidad_neta', 0),
            'tipo': 'percentage',
            'valor_anterior': metricas.get('rentabilidad_neta_anterior'),
            'variacion': metricas.get('variacion_mom_rentabilidad')
        }
    ]


def prepare_distribution(porcentajes: Dict[str, float], total: float) -> List[Dict]:
    """Prepara datos de distribución para distribution_table component."""
    return [
        {
            'nombre': nombre,
            'porcentaje': pct,
            'valor': (pct / 100) * total
        }
        for nombre, pct in porcentajes.items()
    ]


def prepare_gastos_por_area(metricas: Dict[str, Any]) -> List[Dict]:
    """Prepara gastos por área para templates."""
    gastos_total = metricas.get('gastos_uyu', 0)
    if gastos_total == 0:
        return []
    
    rentabilidad_por_area = metricas.get('rentabilidad_por_area', {})
    porcentaje_ingresos_por_area = metricas.get('porcentaje_ingresos_por_area', {})
    ingresos_total = metricas.get('ingresos_uyu', 0)
    
    if not rentabilidad_por_area or not porcentaje_ingresos_por_area:
        return []
    
    gastos_por_area = []
    
    for area, rent_pct in rentabilidad_por_area.items():
        ing_pct = porcentaje_ingresos_por_area.get(area, 0)
        ing_area = (ing_pct / 100) * ingresos_total
        gas_area = ing_area * (1 - (rent_pct / 100))
        gas_pct = (gas_area / gastos_total * 100) if gastos_total > 0 else 0
        
        gastos_por_area.append({
            'nombre': area,
            'valor': gas_area,
            'porcentaje': gas_pct
        })
    
    return sorted(gastos_por_area, key=lambda x: x['valor'], reverse=True)


def prepare_metadata(metricas: Dict[str, Any]) -> Dict[str, str]:
    """Prepara metadata para el PDF."""
    return {
        'periodo_inicio': metricas.get('periodo_inicio', 'N/D'),
        'periodo_fin': metricas.get('periodo_fin', 'N/D'),
        'localidad': metricas.get('localidad_filtrada', 'Todas'),
        'cantidad_operaciones': str(metricas.get('cantidad_operaciones', 0))
    }


def build_anterior_proxy(metricas: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Construye proxy de período anterior para comparaciones.
    Retorna None si no hay datos anteriores disponibles.
    """
    ingresos_ant = metricas.get('ingresos_uyu_anterior')
    gastos_ant = metricas.get('gastos_uyu_anterior')
    
    if ingresos_ant is None and gastos_ant is None:
        return None
    
    rent_ant = None
    if ingresos_ant and ingresos_ant > 0:
        gastos_ant_val = gastos_ant or 0
        rent_ant = ((ingresos_ant - gastos_ant_val) / ingresos_ant) * 100
    
    return {
        'ingresos_uyu': ingresos_ant or 0,
        'gastos_uyu': gastos_ant or 0,
        'rentabilidad_neta': rent_ant
    }



