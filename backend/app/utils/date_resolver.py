"""
Date Resolver - Resolución de períodos a fechas

Funciones puras para resolver períodos predefinidos (mes_actual, trimestre, etc)
a rangos de fechas concretas.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from datetime import date, timedelta
from typing import Tuple, Literal
from calendar import monthrange
from app.utils.formatters import format_date_es


PeriodType = Literal['mes_actual', 'mes_anterior', 'trimestre_actual', 
                      'semestre_actual', 'anio_2025', 'custom']


def resolve_period(
    tipo: PeriodType,
    fecha_ref: date = None,
    fecha_inicio_custom: date = None,
    fecha_fin_custom: date = None
) -> Tuple[date, date]:
    """
    Resuelve un tipo de período a rango de fechas.
    
    Args:
        tipo: Tipo de período predefinido o 'custom'
        fecha_ref: Fecha de referencia (default: hoy)
        fecha_inicio_custom: Solo si tipo='custom'
        fecha_fin_custom: Solo si tipo='custom'
        
    Returns:
        Tupla (fecha_inicio, fecha_fin) inclusive
        
    Raises:
        ValueError: Si tipo='custom' y faltan fechas custom
        
    Ejemplos:
        >>> resolve_period('mes_actual', date(2025, 10, 15))
        (date(2025, 10, 1), date(2025, 10, 31))
        >>> resolve_period('trimestre_actual', date(2025, 10, 15))
        (date(2025, 10, 1), date(2025, 12, 31))
    """
    if fecha_ref is None:
        fecha_ref = date.today()
    
    if tipo == 'mes_actual':
        return _get_month_range(fecha_ref.year, fecha_ref.month)
    
    elif tipo == 'mes_anterior':
        if fecha_ref.month == 1:
            return _get_month_range(fecha_ref.year - 1, 12)
        else:
            return _get_month_range(fecha_ref.year, fecha_ref.month - 1)
    
    elif tipo == 'trimestre_actual':
        return _get_quarter_range(fecha_ref.year, _get_quarter(fecha_ref.month))
    
    elif tipo == 'semestre_actual':
        semestre = 1 if fecha_ref.month <= 6 else 2
        if semestre == 1:
            return date(fecha_ref.year, 1, 1), date(fecha_ref.year, 6, 30)
        else:
            return date(fecha_ref.year, 7, 1), date(fecha_ref.year, 12, 31)
    
    elif tipo == 'anio_2025':
        return date(2025, 1, 1), date(2025, 12, 31)
    
    elif tipo == 'custom':
        if not fecha_inicio_custom or not fecha_fin_custom:
            raise ValueError("tipo='custom' requiere fecha_inicio_custom y fecha_fin_custom")
        return fecha_inicio_custom, fecha_fin_custom
    
    else:
        raise ValueError(f"Tipo de período desconocido: {tipo}")


def get_comparison_period(
    fecha_inicio: date,
    fecha_fin: date,
    tipo_comparacion: Literal['periodo_anterior', 'mismo_periodo_año_pasado', 'custom'],
    fecha_inicio_custom: date = None,
    fecha_fin_custom: date = None
) -> Tuple[date, date]:
    """
    Calcula período de comparación automáticamente.
    
    Args:
        fecha_inicio: Inicio del período principal
        fecha_fin: Fin del período principal
        tipo_comparacion: Tipo de comparación
        fecha_inicio_custom: Solo si tipo='custom'
        fecha_fin_custom: Solo si tipo='custom'
        
    Returns:
        Tupla (fecha_inicio_comp, fecha_fin_comp)
        
    Ejemplos:
        >>> get_comparison_period(date(2025, 10, 1), date(2025, 10, 31), 'periodo_anterior')
        (date(2025, 9, 1), date(2025, 9, 30))
        >>> get_comparison_period(date(2025, 10, 1), date(2025, 10, 31), 'mismo_periodo_año_pasado')
        (date(2024, 10, 1), date(2024, 10, 31))
    """
    if tipo_comparacion == 'custom':
        if not fecha_inicio_custom or not fecha_fin_custom:
            raise ValueError("tipo='custom' requiere fechas custom")
        return fecha_inicio_custom, fecha_fin_custom
    
    duracion_dias = (fecha_fin - fecha_inicio).days + 1  # +1 para incluir último día
    
    if tipo_comparacion == 'periodo_anterior':
        # Retroceder exactamente la duración del período
        fecha_fin_comp = fecha_inicio - timedelta(days=1)
        fecha_inicio_comp = fecha_fin_comp - timedelta(days=duracion_dias - 1)
        return fecha_inicio_comp, fecha_fin_comp
    
    elif tipo_comparacion == 'mismo_periodo_año_pasado':
        # Mismo rango pero año anterior
        try:
            fecha_inicio_comp = fecha_inicio.replace(year=fecha_inicio.year - 1)
            fecha_fin_comp = fecha_fin.replace(year=fecha_fin.year - 1)
            return fecha_inicio_comp, fecha_fin_comp
        except ValueError:
            # Edge case: 29 feb en año no bisiesto
            fecha_inicio_comp = date(fecha_inicio.year - 1, fecha_inicio.month, 28)
            fecha_fin_comp = date(fecha_fin.year - 1, fecha_fin.month, 28)
            return fecha_inicio_comp, fecha_fin_comp
    
    else:
        raise ValueError(f"Tipo comparación desconocido: {tipo_comparacion}")


def _get_month_range(year: int, month: int) -> Tuple[date, date]:
    """
    Retorna primer y último día del mes.
    
    Helper privado.
    """
    first_day = date(year, month, 1)
    last_day_num = monthrange(year, month)[1]
    last_day = date(year, month, last_day_num)
    return first_day, last_day


def _get_quarter(month: int) -> int:
    """
    Retorna número de trimestre (1-4) para un mes.
    
    Helper privado.
    """
    return ((month - 1) // 3) + 1


def _get_quarter_range(year: int, quarter: int) -> Tuple[date, date]:
    """
    Retorna primer y último día del trimestre.
    
    Helper privado.
    
    Q1: Ene-Mar
    Q2: Abr-Jun
    Q3: Jul-Sep
    Q4: Oct-Dic
    """
    if quarter == 1:
        return date(year, 1, 1), date(year, 3, 31)
    elif quarter == 2:
        return date(year, 4, 1), date(year, 6, 30)
    elif quarter == 3:
        return date(year, 7, 1), date(year, 9, 30)
    elif quarter == 4:
        return date(year, 10, 1), date(year, 12, 31)
    else:
        raise ValueError(f"Trimestre inválido: {quarter}")


def get_period_label(fecha_inicio: date, fecha_fin: date) -> str:
    """
    Genera etiqueta descriptiva del período.
    
    Args:
        fecha_inicio: Fecha inicio
        fecha_fin: Fecha fin
        
    Returns:
        String descriptivo
        
    Ejemplos:
        >>> get_period_label(date(2025, 10, 1), date(2025, 10, 31))
        'Octubre 2025'
        >>> get_period_label(date(2025, 10, 1), date(2025, 12, 31))
        'Q4 2025'
        >>> get_period_label(date(2025, 1, 1), date(2025, 12, 31))
        'Año 2025'
    """
    meses_es = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ]
    
    # Mismo mes completo
    if (fecha_inicio.day == 1 and 
        fecha_inicio.month == fecha_fin.month and
        fecha_inicio.year == fecha_fin.year and
        fecha_fin.day == monthrange(fecha_fin.year, fecha_fin.month)[1]):
        return f"{meses_es[fecha_inicio.month - 1]} {fecha_inicio.year}"
    
    # Año completo
    if fecha_inicio == date(fecha_inicio.year, 1, 1) and fecha_fin == date(fecha_inicio.year, 12, 31):
        return f"Año {fecha_inicio.year}"
    
    # Trimestre
    if fecha_inicio.day == 1:
        quarter = _get_quarter(fecha_inicio.month)
        expected_inicio, expected_fin = _get_quarter_range(fecha_inicio.year, quarter)
        if fecha_inicio == expected_inicio and fecha_fin == expected_fin:
            return f"Q{quarter} {fecha_inicio.year}"
    
    # Rango custom
    return f"{format_date_es(fecha_inicio, 'corto')} - {format_date_es(fecha_fin, 'corto')}"

