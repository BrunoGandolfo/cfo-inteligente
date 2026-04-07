"""Pydantic schemas for scraping batches, failures and logs."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


BatchState = Literal["pending", "in_progress", "completed", "failed", "paused"]
LogLevel = Literal["info", "warn", "error", "debug"]


class ScrapingProgressBase(BaseModel):
    """Shared fields for scraping batches."""

    fecha_inicio: date
    fecha_fin: date
    pagina_actual: int = 0
    total_paginas: Optional[int] = None
    sentencias_encontradas: int = 0
    sentencias_descargadas: int = 0
    sentencias_fallidas: int = 0
    estado: BatchState = "pending"
    worker_id: Optional[str] = None
    ultimo_intento: Optional[datetime] = None
    error_ultimo: Optional[str] = None


class ScrapingProgressRead(ScrapingProgressBase):
    """Read model for scraping batches."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScrapingProgressUpdate(BaseModel):
    """Payload accepted by update_progress."""

    pagina_actual: int
    total_paginas: Optional[int] = None
    sentencias_encontradas: Optional[int] = None
    sentencias_descargadas: Optional[int] = None


class ScrapingFailureBase(BaseModel):
    """Shared fields for sentence-level failures."""

    progress_id: int
    pagina: int
    posicion_en_pagina: int
    numero_sentencia: Optional[str] = None
    sede: Optional[str] = None
    fecha_sentencia: Optional[date] = None
    error_tipo: str
    error_mensaje: str
    intentos: int = 1
    max_intentos: int = 5
    resuelta: bool = False


class ScrapingFailureCreate(BaseModel):
    """Payload accepted by register_failure."""

    progress_id: int
    pagina: int
    posicion_en_pagina: int
    numero_sentencia: Optional[str] = None
    sede: Optional[str] = None
    fecha_sentencia: Optional[date] = None
    error_tipo: str
    error_mensaje: str


class ScrapingFailureRead(ScrapingFailureBase):
    """Read model for sentence-level failures."""

    id: int
    created_at: datetime
    ultimo_intento: datetime

    model_config = ConfigDict(from_attributes=True)


class ScrapingLogCreate(BaseModel):
    """Payload accepted by log."""

    worker_id: str
    progress_id: Optional[int] = None
    nivel: LogLevel
    evento: str
    mensaje: str
    sentencias_por_minuto: Optional[Decimal] = None
    tiempo_respuesta_ms: Optional[int] = None


class ScrapingLogRead(ScrapingLogCreate):
    """Read model for crawler events."""

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OverallScrapingProgress(BaseModel):
    """Global summary for orchestrator status panels."""

    totalBatches: int
    completedBatches: int
    inProgressBatches: int
    pendingBatches: int
    failedBatches: int
    totalSentenciasDescargadas: int
    totalSentenciasFallidas: int
