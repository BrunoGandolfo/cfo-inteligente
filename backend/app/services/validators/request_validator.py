"""
Request Validator - Valida requests de reportes

Valida estructura, fechas, y opciones antes de procesar.
Funciones puras sin side effects.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from datetime import date

from app.schemas.report.request import ReportRequest
from app.core.exceptions import InvalidDateRangeError
from app.core.logger import get_logger

logger = get_logger(__name__)


def validate_request(request: ReportRequest) -> None:
    """
    Valida request completo.
    
    Ejecuta todas las validaciones en secuencia.
    
    Args:
        request: ReportRequest a validar
        
    Raises:
        InvalidDateRangeError: Si alguna validación falla
        
    Ejemplo:
        >>> from app.schemas.report.request import ReportRequest, PeriodConfig
        >>> request = ReportRequest(period=PeriodConfig(tipo='mes_actual'))
        >>> validate_request(request)  # No lanza excepción si válido
    """
    logger.debug("Validando request completo")
    
    # Validar período
    validate_period(request.period)
    
    # Validar comparación si está activa
    if request.comparison and request.comparison.activo:
        validate_comparison(request.comparison, request.period)
    
    # Validar opciones
    validate_options(request.options)
    
    logger.info("Request validado exitosamente")


def validate_period(period) -> None:
    """
    Valida configuración de período.
    
    Args:
        period: PeriodConfig
        
    Raises:
        InvalidDateRangeError: Si período inválido
    """
    # Si es custom, validar que tenga fechas
    if period.tipo == 'custom':
        if not period.fecha_inicio or not period.fecha_fin:
            raise InvalidDateRangeError(
                "Período custom requiere fecha_inicio y fecha_fin"
            )
        
        # Validar que fecha_fin > fecha_inicio
        if period.fecha_fin < period.fecha_inicio:
            raise InvalidDateRangeError(
                f"fecha_fin ({period.fecha_fin}) debe ser mayor que "
                f"fecha_inicio ({period.fecha_inicio})"
            )
        
        # Validar que no sean fechas futuras
        hoy = date.today()
        if period.fecha_inicio > hoy:
            raise InvalidDateRangeError(
                f"fecha_inicio ({period.fecha_inicio}) no puede ser futura"
            )
        
        if period.fecha_fin > hoy:
            raise InvalidDateRangeError(
                f"fecha_fin ({period.fecha_fin}) no puede ser futura"
            )
        
        # Validar duración máxima (365 días)
        duracion = (period.fecha_fin - period.fecha_inicio).days + 1
        if duracion > 365:
            raise InvalidDateRangeError(
                f"Período de {duracion} días excede máximo de 365 días"
            )
        
        logger.debug(f"Período custom válido: {duracion} días")


def validate_comparison(comparison, main_period) -> None:
    """
    Valida configuración de comparación.
    
    Args:
        comparison: ComparisonConfig
        main_period: PeriodConfig del período principal
        
    Raises:
        InvalidDateRangeError: Si comparación inválida
    """
    if not comparison.activo:
        return
    
    logger.debug(f"Validando comparación tipo: {comparison.tipo}")
    
    # Si tipo es custom, validar fechas
    if comparison.tipo == 'custom':
        if not comparison.fecha_inicio or not comparison.fecha_fin:
            raise InvalidDateRangeError(
                "Comparación custom requiere fecha_inicio y fecha_fin"
            )
        
        # Validar que fecha_fin > fecha_inicio
        if comparison.fecha_fin < comparison.fecha_inicio:
            raise InvalidDateRangeError(
                f"Comparación: fecha_fin debe ser mayor que fecha_inicio"
            )
        
        # Validar que no sean fechas futuras
        hoy = date.today()
        if comparison.fecha_inicio > hoy or comparison.fecha_fin > hoy:
            raise InvalidDateRangeError(
                "Fechas de comparación no pueden ser futuras"
            )
        
        # Validar que período de comparación no se solape con principal
        # (esto es opcional, depende de si queremos permitir solapamiento)
        if main_period.tipo == 'custom' and main_period.fecha_inicio:
            if _periods_overlap(
                main_period.fecha_inicio, main_period.fecha_fin,
                comparison.fecha_inicio, comparison.fecha_fin
            ):
                logger.warning("Períodos se solapan - permitido pero inusual")
        
        logger.debug("Comparación custom válida")


def validate_options(options) -> None:
    """
    Valida opciones del reporte.
    
    Args:
        options: ReportOptions
        
    Raises:
        InvalidDateRangeError: Si opciones inválidas
        
    Nota:
        Por ahora todas las opciones son válidas por diseño (Enums + defaults).
        Este método existe para futuras validaciones.
    """
    # Validar formato
    formatos_validos = ['ejecutivo', 'completo', 'resumido']
    if options.formato not in formatos_validos:
        raise InvalidDateRangeError(
            f"Formato '{options.formato}' no válido. "
            f"Válidos: {', '.join(formatos_validos)}"
        )
    
    # Validar paleta
    paletas_validas = ['institucional', 'moderna_2024']
    if options.paleta not in paletas_validas:
        raise InvalidDateRangeError(
            f"Paleta '{options.paleta}' no válida. "
            f"Válidas: {', '.join(paletas_validas)}"
        )
    
    logger.debug(f"Opciones válidas: formato={options.formato}, paleta={options.paleta}")


def validate_dates(
    fecha_inicio: date,
    fecha_fin: date,
    max_days: int = 365
) -> None:
    """
    Valida rango de fechas genérico.
    
    Función helper reutilizable.
    
    Args:
        fecha_inicio: Fecha inicio
        fecha_fin: Fecha fin
        max_days: Máximo días permitidos
        
    Raises:
        InvalidDateRangeError: Si fechas inválidas
    """
    # Validar que fecha_fin > fecha_inicio
    if fecha_fin < fecha_inicio:
        raise InvalidDateRangeError(
            f"fecha_fin ({fecha_fin}) debe ser mayor que fecha_inicio ({fecha_inicio})"
        )
    
    # Validar que no sean futuras
    hoy = date.today()
    if fecha_inicio > hoy:
        raise InvalidDateRangeError(
            f"fecha_inicio ({fecha_inicio}) no puede ser futura"
        )
    
    if fecha_fin > hoy:
        raise InvalidDateRangeError(
            f"fecha_fin ({fecha_fin}) no puede ser futura"
        )
    
    # Validar duración
    duracion = (fecha_fin - fecha_inicio).days + 1
    if duracion > max_days:
        raise InvalidDateRangeError(
            f"Rango de {duracion} días excede máximo de {max_days} días"
        )
    
    if duracion < 1:
        raise InvalidDateRangeError(
            "Rango debe ser al menos de 1 día"
        )


def _periods_overlap(
    start1: date,
    end1: date,
    start2: date,
    end2: date
) -> bool:
    """
    Verifica si dos períodos se solapan.
    
    Helper privado.
    
    Args:
        start1, end1: Período 1
        start2, end2: Período 2
        
    Returns:
        True si se solapan
    """
    return (start1 <= end2) and (end1 >= start2)

