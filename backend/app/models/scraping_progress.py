"""Scraping tracking models for BJN crawler batches, failures and logs."""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base, utc_now


class ScrapingProgress(Base):
    """Tracks the lifecycle of a crawler batch for a concrete date range."""

    __tablename__ = "scraping_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)

    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)

    pagina_actual = Column(Integer, default=0, nullable=False)
    total_paginas = Column(Integer, nullable=True)

    sentencias_encontradas = Column(Integer, default=0, nullable=False)
    sentencias_descargadas = Column(Integer, default=0, nullable=False)
    sentencias_fallidas = Column(Integer, default=0, nullable=False)

    estado = Column(String(20), default="pending", nullable=False)

    worker_id = Column(String(50), nullable=True)
    ultimo_intento = Column(DateTime(timezone=True), nullable=True)
    error_ultimo = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    failures = relationship("ScrapingFailure", back_populates="progress")
    logs = relationship("ScrapingLog", back_populates="progress")

    __table_args__ = (
        UniqueConstraint("fecha_inicio", "fecha_fin", name="uq_scraping_progress_fecha_rango"),
        CheckConstraint(
            "estado IN ('pending', 'in_progress', 'completed', 'failed', 'paused')",
            name="ck_scraping_progress_estado",
        ),
        Index("idx_scraping_progress_estado", "estado"),
    )

    def __repr__(self) -> str:
        return (
            f"<ScrapingProgress(id={self.id}, rango={self.fecha_inicio}..{self.fecha_fin}, "
            f"estado='{self.estado}')>"
        )


class ScrapingFailure(Base):
    """Stores sentence-level failures to allow retrying later."""

    __tablename__ = "scraping_failures"

    id = Column(Integer, primary_key=True, autoincrement=True)

    progress_id = Column(Integer, ForeignKey("scraping_progress.id"), nullable=False)

    pagina = Column(Integer, nullable=False)
    posicion_en_pagina = Column(Integer, nullable=False)

    numero_sentencia = Column(String(100), nullable=True)
    sede = Column(String(200), nullable=True)
    fecha_sentencia = Column(Date, nullable=True)

    error_tipo = Column(String(50), nullable=False)
    error_mensaje = Column(Text, nullable=False)

    intentos = Column(Integer, default=1, nullable=False)
    max_intentos = Column(Integer, default=5, nullable=False)
    resuelta = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    ultimo_intento = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    progress = relationship("ScrapingProgress", back_populates="failures")

    __table_args__ = (
        Index(
            "idx_scraping_failures_resuelta",
            "resuelta",
            postgresql_where=text("resuelta = FALSE"),
        ),
        Index("idx_scraping_failures_progress", "progress_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<ScrapingFailure(id={self.id}, progress_id={self.progress_id}, pagina={self.pagina}, "
            f"posicion={self.posicion_en_pagina}, resuelta={self.resuelta})>"
        )


class ScrapingLog(Base):
    """Structured events emitted by crawler workers for monitoring."""

    __tablename__ = "scraping_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    worker_id = Column(String(50), nullable=True)
    progress_id = Column(Integer, ForeignKey("scraping_progress.id"), nullable=True)

    nivel = Column(String(10), nullable=False)
    evento = Column(String(100), nullable=False)
    mensaje = Column(Text, nullable=False)

    sentencias_por_minuto = Column(Numeric(6, 2), nullable=True)
    tiempo_respuesta_ms = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    progress = relationship("ScrapingProgress", back_populates="logs")

    __table_args__ = (
        CheckConstraint(
            "nivel IN ('info', 'warn', 'error', 'debug')",
            name="ck_scraping_logs_nivel",
        ),
        Index("idx_scraping_logs_created", "created_at"),
        Index(
            "idx_scraping_logs_nivel",
            "nivel",
            postgresql_where=text("nivel IN ('warn', 'error')"),
        ),
    )

    def __repr__(self) -> str:
        return f"<ScrapingLog(id={self.id}, nivel='{self.nivel}', evento='{self.evento}')>"
