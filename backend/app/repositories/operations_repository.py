"""
Operations Repository - Acceso a datos de operaciones

Implementa queries optimizados con filtros y paginación.
Hereda de BaseRepository.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func

from app.repositories.base_repository import BaseRepository
from app.models import Operacion, TipoOperacion, Localidad
from app.core.logger import get_logger

logger = get_logger(__name__)


class OperationsRepository(BaseRepository[Operacion]):
    """
    Repositorio para operaciones.
    
    RESPONSABILIDAD: Queries optimizados de operaciones.
    HERENCIA: Implementa métodos abstractos de BaseRepository[Operacion].
    PATRÓN: Repository Pattern.
    
    Features:
    - Query optimizado con eager loading (area)
    - Filtros por fecha, tipo, área, localidad
    - Paginación
    - Aggregations (count, sum)
    
    Ejemplo:
        >>> from app.core.database import get_db
        >>> db = next(get_db())
        >>> repo = OperationsRepository(db)
        >>> ops = repo.get_by_period(date(2025, 10, 1), date(2025, 10, 31))
        >>> print(len(ops))
        245
    """
    
    def get_by_id(self, id: str) -> Optional[Operacion]:
        """
        Obtiene operación por ID.
        
        Args:
            id: UUID de la operación
            
        Returns:
            Operacion o None si no existe
        """
        return self.db.query(Operacion).filter(
            Operacion.id == id,
            Operacion.deleted_at.is_(None)
        ).first()
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[Operacion]:
        """
        Obtiene todas las operaciones con paginación.
        
        Args:
            limit: Máximo de registros
            offset: Offset para paginación
            
        Returns:
            Lista de operaciones (no eliminadas)
        """
        return self.db.query(Operacion).filter(
            Operacion.deleted_at.is_(None)
        ).options(
            joinedload(Operacion.area)  # Eager loading
        ).order_by(
            Operacion.fecha.desc()
        ).limit(limit).offset(offset).all()
    
    def count(self, **filters) -> int:
        """
        Cuenta operaciones con filtros.
        
        Args:
            **filters: Filtros opcionales
                - fecha_inicio: date
                - fecha_fin: date
                - tipo_operacion: TipoOperacion
                - area_id: UUID
                - localidad: Localidad
                
        Returns:
            Cantidad de operaciones
        """
        query = self.db.query(func.count(Operacion.id)).filter(
            Operacion.deleted_at.is_(None)
        )
        
        # Aplicar filtros
        query = self._apply_filters(query, **filters)
        
        return query.scalar()
    
    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS ESPECÍFICOS DE OPERACIONES
    # ═══════════════════════════════════════════════════════════════
    
    def get_by_period(
        self,
        fecha_inicio: date,
        fecha_fin: date,
        tipo_operacion: Optional[TipoOperacion] = None,
        area_id: Optional[str] = None,
        localidad: Optional[Localidad] = None
    ) -> List[Operacion]:
        """
        Obtiene operaciones por período con filtros opcionales.
        
        Query optimizado con eager loading de relaciones.
        
        Args:
            fecha_inicio: Fecha inicio (inclusive)
            fecha_fin: Fecha fin (inclusive)
            tipo_operacion: Filtrar por tipo (opcional)
            area_id: Filtrar por área (opcional)
            localidad: Filtrar por localidad (opcional)
            
        Returns:
            Lista de operaciones ordenadas por fecha DESC
            
        Ejemplo:
            >>> ops = repo.get_by_period(
            ...     fecha_inicio=date(2025, 10, 1),
            ...     fecha_fin=date(2025, 10, 31),
            ...     tipo_operacion=TipoOperacion.INGRESO
            ... )
        """
        logger.debug(
            f"Query operaciones: {fecha_inicio} a {fecha_fin}, "
            f"tipo={tipo_operacion}, area={area_id}, localidad={localidad}"
        )
        
        # Query base con eager loading
        query = self.db.query(Operacion).filter(
            Operacion.deleted_at.is_(None),
            Operacion.fecha >= fecha_inicio,
            Operacion.fecha <= fecha_fin
        ).options(
            joinedload(Operacion.area),  # Eager load area
            joinedload(Operacion.distribuciones)  # Eager load distribuciones si existen
        )
        
        # Filtros opcionales
        if tipo_operacion:
            query = query.filter(Operacion.tipo_operacion == tipo_operacion)
        
        if area_id:
            query = query.filter(Operacion.area_id == area_id)
        
        if localidad:
            query = query.filter(Operacion.localidad == localidad)
        
        # Ordenar por fecha DESC
        query = query.order_by(Operacion.fecha.desc(), Operacion.created_at.desc())
        
        # Ejecutar
        operaciones = query.all()
        
        logger.info(f"Operaciones encontradas: {len(operaciones)}")
        
        return operaciones
    
    def get_ingresos_mensuales_historico(
        self,
        meses: int = 12
    ) -> List[float]:
        """
        Obtiene histórico de ingresos mensuales para proyecciones.
        
        Args:
            meses: Cantidad de meses hacia atrás
            
        Returns:
            Lista de ingresos mensuales (últimos N meses)
            [mes_mas_viejo, ..., mes_mas_reciente]
            
        Ejemplo:
            >>> historico = repo.get_ingresos_mensuales_historico(meses=6)
            >>> print(historico)
            [100000.0, 120000.0, 115000.0, 130000.0, 125000.0, 140000.0]
        """
        from datetime import datetime, timedelta
        from decimal import Decimal
        
        # Calcular fecha inicio (N meses atrás)
        fecha_fin = datetime.now().date()
        fecha_inicio = fecha_fin - timedelta(days=meses * 31)  # Aproximado
        
        # Query agrupado por mes
        query = self.db.query(
            func.date_trunc('month', Operacion.fecha).label('mes'),
            func.sum(Operacion.monto_uyu).label('total_ingresos')
        ).filter(
            Operacion.deleted_at.is_(None),
            Operacion.tipo_operacion == TipoOperacion.INGRESO,
            Operacion.fecha >= fecha_inicio,
            Operacion.fecha <= fecha_fin
        ).group_by(
            func.date_trunc('month', Operacion.fecha)
        ).order_by(
            func.date_trunc('month', Operacion.fecha)
        )
        
        resultados = query.all()
        
        # Convertir a lista de floats
        ingresos_mensuales = [
            float(r.total_ingresos or Decimal('0'))
            for r in resultados
        ]
        
        logger.debug(f"Histórico mensual: {len(ingresos_mensuales)} meses")
        
        return ingresos_mensuales
    
    def get_by_tipo(
        self,
        tipo_operacion: TipoOperacion,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        limit: int = 100
    ) -> List[Operacion]:
        """
        Obtiene operaciones por tipo.
        
        Args:
            tipo_operacion: Tipo de operación
            fecha_inicio: Filtro fecha inicio (opcional)
            fecha_fin: Filtro fecha fin (opcional)
            limit: Máximo de registros
            
        Returns:
            Lista de operaciones
        """
        query = self.db.query(Operacion).filter(
            Operacion.deleted_at.is_(None),
            Operacion.tipo_operacion == tipo_operacion
        )
        
        if fecha_inicio:
            query = query.filter(Operacion.fecha >= fecha_inicio)
        
        if fecha_fin:
            query = query.filter(Operacion.fecha <= fecha_fin)
        
        return query.order_by(Operacion.fecha.desc()).limit(limit).all()
    
    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS PRIVADOS (helpers)
    # ═══════════════════════════════════════════════════════════════
    
    def _apply_filters(self, query, **filters):
        """
        Aplica filtros dinámicos a query.
        
        Helper privado para reutilizar lógica de filtros.
        """
        if 'fecha_inicio' in filters:
            query = query.filter(Operacion.fecha >= filters['fecha_inicio'])
        
        if 'fecha_fin' in filters:
            query = query.filter(Operacion.fecha <= filters['fecha_fin'])
        
        if 'tipo_operacion' in filters:
            query = query.filter(Operacion.tipo_operacion == filters['tipo_operacion'])
        
        if 'area_id' in filters:
            query = query.filter(Operacion.area_id == filters['area_id'])
        
        if 'localidad' in filters:
            query = query.filter(Operacion.localidad == filters['localidad'])
        
        return query

