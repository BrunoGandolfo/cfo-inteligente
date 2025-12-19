"""
Helpers compartidos para queries de operaciones.
Extraído para eliminar duplicación entre reportes.py y reportes_dashboard.py
"""
from datetime import date
from typing import Optional, List, Any
from sqlalchemy.orm import Query
from sqlalchemy import and_

from app.models.operacion import Operacion
from app.models import Localidad


def aplicar_filtros_operaciones(
    query: Query,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    localidad: Optional[str] = None,
    excluir_eliminados: bool = True
) -> Query:
    """
    Aplica filtros comunes a queries de operaciones.
    
    Args:
        query: Query base de SQLAlchemy
        fecha_desde: Fecha inicio (inclusive)
        fecha_hasta: Fecha fin (inclusive)
        localidad: 'MONTEVIDEO', 'MERCEDES', 'Montevideo', 'Mercedes' o None para ambas
        excluir_eliminados: Si True, excluye operaciones con deleted_at
    
    Returns:
        Query con filtros aplicados
    
    Example:
        >>> query = db.query(Operacion)
        >>> query = aplicar_filtros_operaciones(query, fecha_desde=date(2025,1,1))
    """
    filtros: List[Any] = []
    
    if excluir_eliminados:
        filtros.append(Operacion.deleted_at.is_(None))
    
    if fecha_desde:
        filtros.append(Operacion.fecha >= fecha_desde)
    
    if fecha_hasta:
        filtros.append(Operacion.fecha <= fecha_hasta)
    
    if localidad and localidad not in ('Todas', 'todas', None):
        # Mapear string a enum de Localidad
        localidad_map = {
            "Montevideo": Localidad.MONTEVIDEO,
            "MONTEVIDEO": Localidad.MONTEVIDEO,
            "Mercedes": Localidad.MERCEDES,
            "MERCEDES": Localidad.MERCEDES,
        }
        enum_loc = localidad_map.get(localidad)
        if enum_loc:
            filtros.append(Operacion.localidad == enum_loc)
    
    if filtros:
        query = query.filter(and_(*filtros))
    
    return query



