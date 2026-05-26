"""
Schemas Pydantic para el módulo Contable (consultas DGI).

Define los modelos de validación y respuesta para:
- Ejecutar una consulta DGI (POST /consultar)
- Listar consultas con paginación (GET /consultas)
- Obtener detalle de una consulta (GET /consultas/{id})
- Catálogo de servicios disponibles (GET /servicios-disponibles)
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


SERVICIOS_DGI_VALIDOS = (
    "CERTIFICADO_UNICO",
    "DECLARACION_IRPF",
    "AFILIACION_BANCARIA",
    "BORRADORES_IASS",
    "EXONERACION_ARRENDAMIENTOS",
    "ESTADO_TRAMITE",
    "EXPEDIENTE_ADMINISTRATIVO",
    "DEVOLUCION_IVA_GASOIL",
    "CONSTANCIA_PRIMARIA",
    "RESIDENCIA_FISCAL",
)


class ConsultaContableRequest(BaseModel):
    """Schema para POST /api/contable/consultar."""

    servicio: str
    rut: Optional[str] = None
    ci: Optional[str] = None
    datos_extra: Dict[str, Any] = Field(default_factory=dict)
    cliente_nombre: Optional[str] = None
    cliente_rut: Optional[str] = None

    @field_validator("servicio")
    @classmethod
    def servicio_valido(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("El servicio no puede estar vacío")
        normalizado = v.strip().upper()
        if normalizado not in SERVICIOS_DGI_VALIDOS:
            raise ValueError(
                f"servicio debe ser uno de: {', '.join(SERVICIOS_DGI_VALIDOS)}"
            )
        return normalizado


class ConsultaContableResponse(BaseModel):
    """Schema de respuesta para una consulta contable persistida."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    usuario_id: UUID
    servicio: str
    rut: Optional[str] = None
    ci: Optional[str] = None
    datos_entrada: Optional[Dict[str, Any]] = None
    exitosa: bool
    resultado_texto: Optional[str] = None
    resultado_datos: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    cliente_nombre: Optional[str] = None
    cliente_rut: Optional[str] = None
    created_at: datetime
    deleted_at: Optional[datetime] = None


class ConsultaContableSingleResponse(BaseModel):
    """Wrapper para endpoints que devuelven una sola consulta."""

    consulta: ConsultaContableResponse


class ConsultaContableListResponse(BaseModel):
    """Respuesta paginada para GET /api/contable/consultas."""

    total: int
    consultas: List[ConsultaContableResponse]
    limit: int
    offset: int

    @field_validator("total")
    @classmethod
    def total_no_negativo(cls, v: int) -> int:
        if v < 0:
            raise ValueError("El total no puede ser negativo")
        return v


class ServicioDGIResponse(BaseModel):
    """Entrada del catálogo de servicios DGI disponibles."""

    id: str
    nombre: str
    descripcion: str
    campos: List[str]


class EliminarConsultaResponse(BaseModel):
    """Respuesta para DELETE /api/contable/consultas/{id}."""

    ok: bool = True
