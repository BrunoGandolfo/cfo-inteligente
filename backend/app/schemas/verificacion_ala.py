"""
Schemas Pydantic para el módulo ALA (Anti-Lavado de Activos).

Define los modelos de validación y respuesta para:
- Verificar personas/entidades (POST /verificar)
- Actualizar observaciones Art. 44 C.4 (PATCH)
- Respuesta completa de verificación
"""

from pydantic import BaseModel, field_validator
from datetime import date, datetime
from typing import Optional
from uuid import UUID


class ResultadoListaSchema(BaseModel):
    """Resultado de consulta a una lista (PEP, ONU, OFAC, UE, GAFI). Reutilizable."""
    checked: bool
    hits: int = 0
    mejor_match: Optional[str] = None
    similitud: Optional[float] = None
    timestamp: str
    hash_lista: Optional[str] = None
    error: Optional[str] = None


class VerificacionALACreate(BaseModel):
    """Schema para el endpoint POST /verificar."""
    nombre_completo: str
    tipo_documento: Optional[str] = "CI"
    numero_documento: Optional[str] = None
    nacionalidad: Optional[str] = "UY"
    fecha_nacimiento: Optional[date] = None
    es_persona_juridica: bool = False
    razon_social: Optional[str] = None
    expediente_id: Optional[UUID] = None
    contrato_id: Optional[UUID] = None

    @field_validator("nombre_completo")
    @classmethod
    def nombre_longitud(cls, v):
        if not v or not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        if len(v) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres")
        if len(v) > 300:
            raise ValueError("El nombre no puede exceder 300 caracteres")
        return v.strip()

    @field_validator("tipo_documento")
    @classmethod
    def tipo_documento_valido(cls, v):
        if v is not None and v not in ("CI", "RUT", "PASAPORTE"):
            raise ValueError("tipo_documento debe ser CI, RUT o PASAPORTE")
        return v

    @field_validator("nacionalidad")
    @classmethod
    def nacionalidad_max(cls, v):
        if v is not None and len(v) > 3:
            raise ValueError("La nacionalidad no puede exceder 3 caracteres (código ISO)")
        return v


class VerificacionALAUpdate(BaseModel):
    """Schema para PATCH observaciones Art. 44 C.4."""
    busqueda_google_realizada: Optional[bool] = None
    busqueda_google_observaciones: Optional[str] = None
    busqueda_news_realizada: Optional[bool] = None
    busqueda_news_observaciones: Optional[str] = None
    busqueda_wikipedia_realizada: Optional[bool] = None
    busqueda_wikipedia_observaciones: Optional[str] = None


class VerificacionALAResponse(BaseModel):
    """Schema de respuesta completa para una verificación ALA."""
    id: UUID
    nombre_completo: str
    tipo_documento: Optional[str] = None
    numero_documento: Optional[str] = None
    nacionalidad: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    es_persona_juridica: bool
    razon_social: Optional[str] = None
    nivel_diligencia: str
    nivel_riesgo: str
    es_pep: bool
    resultado_onu: Optional[ResultadoListaSchema] = None
    resultado_pep: Optional[ResultadoListaSchema] = None
    resultado_ofac: Optional[ResultadoListaSchema] = None
    resultado_ue: Optional[ResultadoListaSchema] = None
    resultado_gafi: Optional[ResultadoListaSchema] = None
    busqueda_google_realizada: bool
    busqueda_google_observaciones: Optional[str] = None
    busqueda_news_realizada: bool
    busqueda_news_observaciones: Optional[str] = None
    busqueda_wikipedia_realizada: bool
    busqueda_wikipedia_observaciones: Optional[str] = None
    hash_verificacion: str
    certificado_pdf_path: Optional[str] = None
    expediente_id: Optional[UUID] = None
    contrato_id: Optional[UUID] = None
    usuario_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Pydantic v2 - permite ORM mode
