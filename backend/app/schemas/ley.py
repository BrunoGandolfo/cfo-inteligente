"""
Schemas Pydantic para módulo LegalTech - Gestión de Leyes.

Define los modelos de validación y respuesta para:
- Crear leyes desde CSV del Parlamento
- Buscar y listar leyes
- Respuestas de API
"""

from pydantic import BaseModel, field_validator
from datetime import date, datetime
from typing import Optional
from uuid import UUID


class LeyBase(BaseModel):
    """Campos comunes para leyes."""
    numero: int
    anio: int
    titulo: str
    fecha_promulgacion: Optional[date] = None
    url_parlamento: Optional[str] = None
    url_impo: Optional[str] = None
    
    @field_validator('numero')
    @classmethod
    def numero_positivo(cls, v):
        if v <= 0:
            raise ValueError('El número de ley debe ser mayor a 0')
        return v
    
    @field_validator('anio')
    @classmethod
    def anio_valido(cls, v):
        from datetime import datetime
        anio_actual = datetime.now().year
        if v < 1935:
            raise ValueError('El año debe ser >= 1935 (primera ley disponible es 9500 de 1935)')
        if v > anio_actual + 1:
            raise ValueError(f'El año no puede ser mayor a {anio_actual + 1}')
        return v


class LeyCreate(LeyBase):
    """Schema para crear una ley desde CSV del Parlamento."""
    leyes_referenciadas: int = 0
    leyes_que_referencia: int = 0
    
    @field_validator('leyes_referenciadas', 'leyes_que_referencia')
    @classmethod
    def contadores_no_negativos(cls, v):
        if v < 0:
            raise ValueError('Los contadores de referencias no pueden ser negativos')
        return v


class LeyResponse(LeyBase):
    """Schema de respuesta para una ley."""
    id: UUID
    tiene_texto: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Pydantic v2 - permite ORM mode


class LeyBusquedaParams(BaseModel):
    """Parámetros de búsqueda para listar leyes."""
    query: Optional[str] = None  # Búsqueda en título
    numero: Optional[int] = None
    anio: Optional[int] = None
    desde_anio: Optional[int] = None
    hasta_anio: Optional[int] = None
    solo_con_texto: bool = False
    limit: int = 20
    offset: int = 0
    
    @field_validator('numero')
    @classmethod
    def numero_positivo(cls, v):
        if v is not None and v <= 0:
            raise ValueError('El número de ley debe ser mayor a 0')
        return v
    
    @field_validator('anio', 'desde_anio', 'hasta_anio')
    @classmethod
    def anio_valido(cls, v):
        if v is None:
            return v
        from datetime import datetime
        anio_actual = datetime.now().year
        if v < 1935:
            raise ValueError('El año debe ser >= 1935')
        if v > anio_actual + 1:
            raise ValueError(f'El año no puede ser mayor a {anio_actual + 1}')
        return v
    
    @field_validator('limit')
    @classmethod
    def limit_valido(cls, v):
        if v < 1:
            raise ValueError('El límite debe ser >= 1')
        if v > 100:
            raise ValueError('El límite no puede ser mayor a 100')
        return v
    
    @field_validator('offset')
    @classmethod
    def offset_no_negativo(cls, v):
        if v < 0:
            raise ValueError('El offset no puede ser negativo')
        return v


class LeyDetalleResponse(LeyResponse):
    """Respuesta completa con texto de la ley."""
    texto_completo: Optional[str] = None
    leyes_referenciadas: int = 0
    leyes_que_referencia: int = 0


class LeyListResponse(BaseModel):
    """Respuesta paginada para listado de leyes."""
    total: int
    leyes: list[LeyResponse]
    
    @field_validator('total')
    @classmethod
    def total_no_negativo(cls, v):
        if v < 0:
            raise ValueError('El total no puede ser negativo')
        return v

