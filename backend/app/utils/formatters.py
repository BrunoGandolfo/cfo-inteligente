"""
Formatters - Funciones puras de formateo

Formatean números, monedas, fechas y porcentajes.
Sin side effects, fáciles de testear.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from decimal import Decimal
from datetime import date, datetime
from typing import Union


def format_currency(
    value: Union[float, Decimal, int],
    short: bool = False,
    include_currency: bool = True
) -> str:
    """
    Formatea valor monetario.
    
    Args:
        value: Valor numérico
        short: Si True usa K/M (ej: $1.2M), si False usa completo ($1,234,567)
        include_currency: Si incluye símbolo $
        
    Returns:
        String formateado
        
    Ejemplos:
        >>> format_currency(1234567.89)
        '$1,234,568'
        >>> format_currency(1234567.89, short=True)
        '$1.2M'
        >>> format_currency(150000, short=True)
        '$150K'
        >>> format_currency(500, short=True)
        '$500'
    """
    value = float(value)
    prefix = "$" if include_currency else ""
    
    if short:
        if abs(value) >= 1_000_000:
            return f"{prefix}{value/1_000_000:.1f}M"
        elif abs(value) >= 1_000:
            return f"{prefix}{value/1_000:.0f}K"
        else:
            return f"{prefix}{value:.0f}"
    else:
        return f"{prefix}{value:,.0f}"


def format_percentage(
    value: Union[float, Decimal],
    decimals: int = 2,
    include_symbol: bool = True
) -> str:
    """
    Formatea porcentaje.
    
    Args:
        value: Valor porcentual (ej: 33.456)
        decimals: Cantidad de decimales
        include_symbol: Si incluye símbolo %
        
    Returns:
        String formateado
        
    Ejemplos:
        >>> format_percentage(33.456)
        '33.46%'
        >>> format_percentage(100.0, decimals=1)
        '100.0%'
        >>> format_percentage(-5.5, decimals=0)
        '-6%'
    """
    value = float(value)
    suffix = "%" if include_symbol else ""
    return f"{value:.{decimals}f}{suffix}"


def format_date_es(fecha: Union[date, datetime], formato: str = 'completo') -> str:
    """
    Formatea fecha en español.
    
    Args:
        fecha: Fecha a formatear
        formato: 'completo' | 'corto' | 'mes_anio'
        
    Returns:
        String formateado en español
        
    Ejemplos:
        >>> format_date_es(date(2025, 10, 7), 'completo')
        '07 de Octubre de 2025'
        >>> format_date_es(date(2025, 10, 7), 'corto')
        '07/10/2025'
        >>> format_date_es(date(2025, 10, 7), 'mes_anio')
        'Octubre 2025'
    """
    if isinstance(fecha, datetime):
        fecha = fecha.date()
    
    meses_es = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ]
    
    if formato == 'completo':
        return f"{fecha.day:02d} de {meses_es[fecha.month - 1]} de {fecha.year}"
    elif formato == 'mes_anio':
        return f"{meses_es[fecha.month - 1]} {fecha.year}"
    else:  # 'corto'
        return fecha.strftime('%d/%m/%Y')


def format_variacion(
    valor_actual: Union[float, Decimal],
    valor_anterior: Union[float, Decimal],
    tipo: str = 'porcentual'
) -> str:
    """
    Formatea variación entre dos valores.
    
    Args:
        valor_actual: Valor del período actual
        valor_anterior: Valor del período anterior
        tipo: 'porcentual' | 'absoluta' | 'puntos' (para rentabilidad)
        
    Returns:
        String formateado con signo y flecha
        
    Ejemplos:
        >>> format_variacion(120, 100, 'porcentual')
        '+20.0% ↗'
        >>> format_variacion(80, 100, 'porcentual')
        '-20.0% ↘'
        >>> format_variacion(65.5, 75.0, 'puntos')
        '-9.5pp ↘'
    """
    actual = float(valor_actual)
    anterior = float(valor_anterior)
    
    if tipo == 'porcentual':
        if anterior == 0:
            return "N/A"
        variacion = ((actual - anterior) / anterior) * 100
        texto = f"{variacion:+.1f}%"
    elif tipo == 'puntos':
        variacion = actual - anterior
        texto = f"{variacion:+.1f}pp"
    else:  # absoluta
        variacion = actual - anterior
        texto = f"{variacion:+,.0f}"
    
    # Agregar flecha
    if variacion > 0:
        return f"{texto} ↗"
    elif variacion < 0:
        return f"{texto} ↘"
    else:
        return f"{texto} →"


def format_number(
    value: Union[float, Decimal, int],
    decimals: int = 0,
    thousands_sep: bool = True
) -> str:
    """
    Formatea número genérico.
    
    Args:
        value: Valor numérico
        decimals: Cantidad de decimales
        thousands_sep: Si usa separador de miles
        
    Returns:
        String formateado
        
    Ejemplos:
        >>> format_number(1234567)
        '1,234,567'
        >>> format_number(1234.56789, decimals=2)
        '1,234.57'
    """
    value = float(value)
    
    if thousands_sep:
        return f"{value:,.{decimals}f}"
    else:
        return f"{value:.{decimals}f}"

