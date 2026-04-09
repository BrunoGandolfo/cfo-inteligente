"""Schemas Pydantic para expedientes judiciales."""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ExpedienteCreate(BaseModel):
    """Schema para crear/sincronizar un expediente."""

    iue: str = Field(..., description="IUE en formato Sede-Numero/Año (ej: 2-12345/2023)")
    cliente_id: Optional[str] = Field(None, description="UUID del cliente asociado")
    area_id: Optional[str] = Field(None, description="UUID del área")
    responsable_id: Optional[str] = Field(None, description="UUID del usuario responsable")


class MovimientoResponse(BaseModel):
    """Schema de respuesta para un movimiento."""

    id: str
    fecha: Optional[date]
    tipo: Optional[str]
    decreto: Optional[str]
    vencimiento: Optional[date]
    sede: Optional[str]
    notificado: bool
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class ExpedienteResponse(BaseModel):
    """Schema de respuesta para un expediente."""

    id: str
    iue: str
    iue_sede: int
    iue_numero: int
    iue_anio: int
    caratula: Optional[str]
    origen: Optional[str]
    abogado_actor: Optional[str]
    abogado_demandado: Optional[str]
    cliente_id: Optional[str]
    area_id: Optional[str]
    responsable_id: Optional[str]
    ultimo_movimiento: Optional[date]
    cantidad_movimientos: int
    ultima_sincronizacion: Optional[datetime]
    activo: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    movimientos: Optional[List[MovimientoResponse]] = None

    class Config:
        from_attributes = True


class ExpedienteListResponse(BaseModel):
    """Schema de respuesta para lista paginada de expedientes."""

    total: int
    limit: int
    offset: int
    expedientes: List[ExpedienteResponse]


class SincronizacionResponse(BaseModel):
    """Schema de respuesta para sincronización."""

    expediente: ExpedienteResponse
    nuevos_movimientos: int
    mensaje: str


class MovimientoPendienteResponse(BaseModel):
    """Schema para movimientos pendientes de notificación."""

    movimiento_id: str
    expediente_id: str
    iue: str
    caratula: Optional[str]
    fecha: Optional[date]
    tipo: Optional[str]
    decreto: Optional[str]
    vencimiento: Optional[date]
    sede: Optional[str]
    responsable_id: Optional[str]


class ErrorSincronizacion(BaseModel):
    """Detalle de error en sincronización."""

    iue: str
    error: str


class SincronizacionMasivaResponse(BaseModel):
    """Schema de respuesta para sincronización masiva de expedientes."""

    total_expedientes: int
    sincronizados_ok: int
    con_nuevos_movimientos: int
    total_nuevos_movimientos: int
    errores: int
    detalle_errores: List[ErrorSincronizacion]
    inicio: datetime
    fin: datetime
    duracion_segundos: float


class ResumenSincronizacionResponse(BaseModel):
    """Schema de respuesta para estadísticas de sincronización."""

    total_expedientes_activos: int
    sincronizados_hoy: int
    movimientos_sin_notificar: int
    ultima_sincronizacion_global: Optional[datetime]


class NotificacionRequest(BaseModel):
    """Schema para enviar notificación WhatsApp."""

    numero: str = Field(..., description="Número WhatsApp en formato internacional (ej: +59899123456)")


class NotificacionResponse(BaseModel):
    """Schema de respuesta para notificación."""

    exito: bool
    mensaje: str
    sid: Optional[str] = None
    detalles: Optional[dict] = None


class HistoriaResponse(BaseModel):
    """Schema de respuesta para historia del expediente."""

    expediente_id: str
    iue: str
    caratula: Optional[str]
    resumen: str
    total_movimientos: int
    generado_en: datetime
