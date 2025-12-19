"""
Period Comparator - Utilidades de comparación de períodos

Extraído de report_orchestrator.py para reducir su tamaño.
Contiene lógica de detección de períodos comparables (YoY, QoQ).

Autor: Sistema CFO Inteligente
Fecha: Diciembre 2025
"""
from datetime import date
from calendar import monthrange
from typing import Tuple, Optional


def is_period_comparable_yoy(fecha_inicio: date, fecha_fin: date) -> bool:
    """
    Verifica si el período es comparable YoY (mes/trimestre/año completo).
    
    Args:
        fecha_inicio: Fecha inicio del período
        fecha_fin: Fecha fin del período
        
    Returns:
        True si es mes completo, trimestre completo o año completo
    """
    # Mes completo
    if fecha_inicio.day == 1:
        ultimo_dia = monthrange(fecha_fin.year, fecha_fin.month)[1]
        if fecha_fin.day == ultimo_dia and fecha_inicio.month == fecha_fin.month:
            return True
    
    # Trimestre completo (inicia en ene/abr/jul/oct y dura 3 meses)
    if fecha_inicio.day == 1 and fecha_inicio.month in [1, 4, 7, 10]:
        if fecha_fin.day in [31, 30] and (fecha_fin.month - fecha_inicio.month) == 2:
            return True
    
    # Año completo
    if fecha_inicio == date(fecha_inicio.year, 1, 1) and \
       fecha_fin == date(fecha_fin.year, 12, 31):
        return True
    
    return False


def is_period_comparable_qoq(fecha_inicio: date, fecha_fin: date) -> bool:
    """
    Verifica si el período es un trimestre completo.
    
    Args:
        fecha_inicio: Fecha inicio del período
        fecha_fin: Fecha fin del período
        
    Returns:
        True si es un trimestre completo
    """
    if fecha_inicio.day == 1 and fecha_inicio.month in [1, 4, 7, 10]:
        if fecha_fin.day in [31, 30] and (fecha_fin.month - fecha_inicio.month) == 2:
            return True
    return False


def get_quarter_before(fecha_inicio: date, fecha_fin: date) -> Tuple[Optional[date], Optional[date]]:
    """
    Calcula el trimestre anterior a un período dado.
    
    Args:
        fecha_inicio: Fecha inicio del trimestre actual
        fecha_fin: Fecha fin del trimestre actual (no usado, para consistencia de interfaz)
        
    Returns:
        Tupla (fecha_inicio, fecha_fin) del trimestre anterior, o (None, None)
    """
    if fecha_inicio.month == 1:
        # Q1 → Q4 año anterior
        return date(fecha_inicio.year - 1, 10, 1), date(fecha_inicio.year - 1, 12, 31)
    elif fecha_inicio.month == 4:
        # Q2 → Q1
        return date(fecha_inicio.year, 1, 1), date(fecha_inicio.year, 3, 31)
    elif fecha_inicio.month == 7:
        # Q3 → Q2
        return date(fecha_inicio.year, 4, 1), date(fecha_inicio.year, 6, 30)
    elif fecha_inicio.month == 10:
        # Q4 → Q3
        return date(fecha_inicio.year, 7, 1), date(fecha_inicio.year, 9, 30)
    
    return None, None


def get_year_before(fecha_inicio: date, fecha_fin: date) -> Tuple[date, date]:
    """
    Calcula el mismo período del año anterior.
    
    Args:
        fecha_inicio: Fecha inicio del período actual
        fecha_fin: Fecha fin del período actual
        
    Returns:
        Tupla (fecha_inicio, fecha_fin) del año anterior
    """
    return (
        date(fecha_inicio.year - 1, fecha_inicio.month, fecha_inicio.day),
        date(fecha_fin.year - 1, fecha_fin.month, fecha_fin.day)
    )



