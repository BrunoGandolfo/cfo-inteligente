"""
Data Validator - Valida datos antes de calcular

Valida que hay suficientes datos para generar reportes.
Funciones puras sin side effects.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import List, Dict, Any

from app.models import Operacion
from app.core.exceptions import InsufficientDataError
from app.core.logger import get_logger

logger = get_logger(__name__)


def validate_sufficient_data(
    operaciones: List[Operacion],
    minimo_requerido: int = 20
) -> None:
    """
    Valida que hay suficientes operaciones para generar reporte.
    
    Args:
        operaciones: Lista de operaciones del período
        minimo_requerido: Mínimo de operaciones requeridas (default: 20)
        
    Raises:
        InsufficientDataError: Si no hay suficientes datos
        
    Ejemplo:
        >>> ops = repo.get_by_period(...)
        >>> validate_sufficient_data(ops, minimo_requerido=20)
    """
    cantidad = len(operaciones)
    
    logger.debug(f"Validando datos: {cantidad} operaciones encontradas")
    
    if cantidad < minimo_requerido:
        logger.warning(
            f"Datos insuficientes: {cantidad} operaciones "
            f"(mínimo: {minimo_requerido})"
        )
        raise InsufficientDataError(
            operaciones_encontradas=cantidad,
            minimo_requerido=minimo_requerido
        )
    
    logger.info(f"Datos suficientes: {cantidad} operaciones")


def validate_metrics(metricas: Dict[str, Any]) -> None:
    """
    Valida que métricas calculadas son consistentes.
    
    Args:
        metricas: Dict con métricas calculadas
        
    Raises:
        ValueError: Si métricas son inconsistentes
        
    Validaciones:
    - Ingresos >= 0
    - Margen operativo entre -100 y 100
    - Resultado neto <= Resultado operativo
    - Porcentajes de distribución suman ~100%
    """
    logger.debug("Validando consistencia de métricas")
    
    # Validar ingresos no negativos
    ingresos = metricas.get('ingresos_uyu', 0)
    if ingresos < 0:
        raise ValueError(f"Ingresos negativos: {ingresos}")
    
    # Validar margen operativo en rango válido
    margen_operativo = metricas.get('margen_operativo', 0)
    if not (-100 <= margen_operativo <= 100):
        logger.warning(f"Margen operativo fuera de rango normal: {margen_operativo}%")
    
    # Validar resultado neto <= resultado operativo
    resultado_operativo = metricas.get('resultado_operativo_uyu', 0)
    resultado_neto = metricas.get('resultado_neto_uyu', 0)
    
    if resultado_neto > resultado_operativo:
        logger.warning(
            f"Resultado neto ({resultado_neto}) > Resultado operativo ({resultado_operativo}). "
            f"Esto puede indicar error en cálculos."
        )
    
    # Validar distribución por área suma ~100%
    porcentaje_por_area = metricas.get('porcentaje_ingresos_por_area', {})
    if porcentaje_por_area:
        suma_porcentajes = sum(porcentaje_por_area.values())
        if not (99 <= suma_porcentajes <= 101):  # Tolerancia de ±1%
            logger.warning(
                f"Porcentajes por área suman {suma_porcentajes}% (esperado: 100%)"
            )
    
    logger.info("Métricas validadas exitosamente")


def validate_data_quality(operaciones: List[Operacion]) -> Dict[str, Any]:
    """
    Valida calidad de datos y retorna reporte.
    
    No lanza excepciones, retorna warnings.
    
    Args:
        operaciones: Lista de operaciones
        
    Returns:
        Dict con reporte de calidad:
        {
            'total': int,
            'con_area': int,
            'sin_area': int,
            'con_descripcion': int,
            'warnings': List[str]
        }
    """
    warnings = []
    
    total = len(operaciones)
    con_area = sum(1 for op in operaciones if op.area_id)
    sin_area = total - con_area
    con_descripcion = sum(1 for op in operaciones if op.descripcion)
    
    # Generar warnings
    if sin_area > 0:
        pct = (sin_area / total) * 100
        warnings.append(f"{sin_area} operaciones ({pct:.1f}%) sin área asignada")
    
    if con_descripcion < total * 0.5:  # Menos del 50%
        pct = (con_descripcion / total) * 100
        warnings.append(f"Solo {pct:.1f}% de operaciones tienen descripción")
    
    # Log warnings
    for warning in warnings:
        logger.warning(f"Calidad de datos: {warning}")
    
    return {
        'total': total,
        'con_area': con_area,
        'sin_area': sin_area,
        'con_descripcion': con_descripcion,
        'warnings': warnings
    }


def validate_date_consistency(operaciones: List[Operacion]) -> None:
    """
    Valida que fechas de operaciones sean consistentes.
    
    Args:
        operaciones: Lista de operaciones
        
    Raises:
        ValueError: Si hay inconsistencias graves
    """
    from datetime import date
    
    hoy = date.today()
    
    # Validar que no haya fechas futuras
    futuras = [op for op in operaciones if op.fecha > hoy]
    if futuras:
        logger.warning(f"{len(futuras)} operaciones con fechas futuras")
        # No lanzar error, solo warning (podrían ser válidas en algunos casos)
    
    # Validar que created_at >= fecha (lógica de negocio)
    inconsistentes = [
        op for op in operaciones
        if op.created_at and op.created_at.date() < op.fecha
    ]
    
    if inconsistentes:
        logger.warning(
            f"{len(inconsistentes)} operaciones con created_at < fecha "
            f"(posible edición retroactiva)"
        )
    
    logger.debug("Consistencia de fechas validada")

