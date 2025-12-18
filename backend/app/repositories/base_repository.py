"""
Base Repository - Interface para repositorios

Define contrato común para acceso a datos.

Principio: Repository Pattern
Ventaja: Abstrae SQLAlchemy - fácil cambiar a otra BD

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from abc import ABC, abstractmethod
from typing import List, Any, Generic, TypeVar
from sqlalchemy.orm import Session

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    Contrato base para repositorios.
    
    Generic[T] permite tipar modelo específico:
    - OperationsRepository(BaseRepository[Operacion])
    - AreasRepository(BaseRepository[Area])
    
    Encapsula queries SQLAlchemy.
    """
    
    def __init__(self, db: Session):
        """
        Args:
            db: Sesión SQLAlchemy inyectada
        """
        self.db = db
    
    @abstractmethod
    def get_by_id(self, id: Any) -> T:
        """
        Obtiene entidad por ID.
        
        Args:
            id: ID de la entidad
            
        Returns:
            Entidad o None si no existe
        """
    
    @abstractmethod
    def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        Obtiene todas las entidades (con paginación).
        
        Args:
            limit: Máximo de registros
            offset: Offset para paginación
            
        Returns:
            Lista de entidades
        """
    
    @abstractmethod
    def count(self, **filters) -> int:
        """
        Cuenta entidades que cumplen filtros.
        
        Args:
            **filters: Filtros específicos del repositorio
            
        Returns:
            Cantidad de registros
        """

