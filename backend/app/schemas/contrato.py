"""
Schemas Pydantic para módulo Notarial - Gestión de Contratos.

Define los modelos de validación y respuesta para:
- Crear y actualizar contratos
- Buscar y listar contratos
- Descargar archivos DOCX
"""

from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, List
from uuid import UUID


class ContratoBase(BaseModel):
    """Campos comunes para contratos."""
    titulo: str
    categoria: str
    subcategoria: Optional[str] = None
    descripcion: Optional[str] = None
    
    @field_validator('titulo')
    @classmethod
    def titulo_no_vacio(cls, v):
        if not v or not v.strip():
            raise ValueError('El título no puede estar vacío')
        return v.strip()
    
    @field_validator('categoria')
    @classmethod
    def categoria_no_vacia(cls, v):
        if not v or not v.strip():
            raise ValueError('La categoría no puede estar vacía')
        return v.strip()


class ContratoCreate(ContratoBase):
    """Schema para crear un contrato."""
    contenido_docx: Optional[bytes] = None
    contenido_texto: Optional[str] = None
    archivo_original: Optional[str] = None
    fuente_original: str = "machado"
    activo: bool = True


class ContratoUpdate(BaseModel):
    """Schema para actualizar un contrato (todos los campos opcionales)."""
    titulo: Optional[str] = None
    categoria: Optional[str] = None
    subcategoria: Optional[str] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None
    
    @field_validator('titulo')
    @classmethod
    def titulo_no_vacio_si_provisto(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('El título no puede estar vacío')
        return v.strip() if v else None
    
    @field_validator('categoria')
    @classmethod
    def categoria_no_vacia_si_provista(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('La categoría no puede estar vacía')
        return v.strip() if v else None


class ContratoResponse(ContratoBase):
    """Schema de respuesta para un contrato (sin contenido_docx)."""
    id: UUID
    fuente_original: str
    archivo_original: Optional[str] = None
    activo: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Pydantic v2 - permite ORM mode


class ContratoBusquedaParams(BaseModel):
    """Parámetros de búsqueda para listar contratos."""
    q: Optional[str] = None  # Búsqueda en titulo y contenido_texto
    categoria: Optional[str] = None
    activo: Optional[bool] = True
    skip: int = 0
    limit: int = 50
    
    @field_validator('skip')
    @classmethod
    def skip_no_negativo(cls, v):
        if v < 0:
            raise ValueError('El skip no puede ser negativo')
        return v
    
    @field_validator('limit')
    @classmethod
    def limit_valido(cls, v):
        if v < 1:
            raise ValueError('El límite debe ser >= 1')
        if v > 100:
            raise ValueError('El límite no puede ser mayor a 100')
        return v


class ContratoListResponse(BaseModel):
    """Respuesta paginada para listado de contratos."""
    contratos: List[ContratoResponse]
    total: int
    categorias: List[str]  # Lista de categorías disponibles
    
    @field_validator('total')
    @classmethod
    def total_no_negativo(cls, v):
        if v < 0:
            raise ValueError('El total no puede ser negativo')
        return v
