"""Service layer for scraping batch progress, failures and crawler logs."""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from sqlalchemy import case
from sqlalchemy.orm import Session

from app.core.database import utc_now
from app.models.scraping_progress import ScrapingFailure, ScrapingLog, ScrapingProgress
from app.schemas.scraping_progress import (
    OverallScrapingProgress,
    ScrapingFailureCreate,
    ScrapingLogCreate,
    ScrapingProgressUpdate,
)

logger = logging.getLogger(__name__)


class ScrapingProgressService:
    """Coordinates crawler progress state across batches, failures and logs."""

    @staticmethod
    def initialize_partitions(db: Session, year_start: int, year_end: int) -> None:
        """Creates yearly batches if they do not exist yet."""
        if year_start > year_end:
            raise ValueError("year_start must be lower than or equal to year_end")

        existing_ranges = {
            (row.fecha_inicio, row.fecha_fin)
            for row in db.query(ScrapingProgress.fecha_inicio, ScrapingProgress.fecha_fin).all()
        }

        for year in range(year_start, year_end + 1):
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
            if (start_date, end_date) in existing_ranges:
                continue

            db.add(
                ScrapingProgress(
                    fecha_inicio=start_date,
                    fecha_fin=end_date,
                )
            )

        db.commit()

    @staticmethod
    def claim_next_batch(db: Session, worker_id: str) -> Optional[ScrapingProgress]:
        """Claims the next available batch using row locking for worker safety."""
        state_priority = case(
            (ScrapingProgress.estado == "pending", 0),
            (ScrapingProgress.estado == "failed", 1),
            else_=2,
        )

        # Para Bruno: skip_locked evita que dos workers reclamen el mismo lote.
        batch = (
            db.query(ScrapingProgress)
            .filter(ScrapingProgress.estado.in_(("pending", "failed")))
            .order_by(state_priority, ScrapingProgress.fecha_inicio.asc(), ScrapingProgress.id.asc())
            .with_for_update(skip_locked=True)
            .first()
        )

        if batch is None:
            return None

        batch.estado = "in_progress"
        batch.worker_id = worker_id
        batch.ultimo_intento = utc_now()
        batch.updated_at = utc_now()

        db.commit()
        db.refresh(batch)
        return batch

    @staticmethod
    def update_progress(db: Session, progress_id: int, data: ScrapingProgressUpdate) -> None:
        """Updates page and counter progress for a claimed batch."""
        batch = db.query(ScrapingProgress).filter(ScrapingProgress.id == progress_id).first()
        if batch is None:
            raise ValueError(f"ScrapingProgress {progress_id} not found")

        batch.pagina_actual = data.pagina_actual
        if data.total_paginas is not None:
            batch.total_paginas = data.total_paginas
        if data.sentencias_encontradas is not None:
            batch.sentencias_encontradas = data.sentencias_encontradas
        if data.sentencias_descargadas is not None:
            batch.sentencias_descargadas = data.sentencias_descargadas

        batch.ultimo_intento = utc_now()
        batch.updated_at = utc_now()

        db.commit()

    @staticmethod
    def complete_batch(db: Session, progress_id: int) -> None:
        """Marks a batch as completed and releases the worker assignment."""
        batch = db.query(ScrapingProgress).filter(ScrapingProgress.id == progress_id).first()
        if batch is None:
            raise ValueError(f"ScrapingProgress {progress_id} not found")

        batch.estado = "completed"
        batch.worker_id = None
        batch.error_ultimo = None
        batch.ultimo_intento = utc_now()
        if batch.total_paginas is not None:
            batch.pagina_actual = batch.total_paginas
        batch.updated_at = utc_now()

        db.commit()

    @staticmethod
    def fail_batch(db: Session, progress_id: int, error: str) -> None:
        """Marks a batch as failed and stores the last batch-level error."""
        batch = db.query(ScrapingProgress).filter(ScrapingProgress.id == progress_id).first()
        if batch is None:
            raise ValueError(f"ScrapingProgress {progress_id} not found")

        batch.estado = "failed"
        batch.worker_id = None
        batch.error_ultimo = error
        batch.ultimo_intento = utc_now()
        batch.updated_at = utc_now()

        db.commit()

    @staticmethod
    def register_failure(db: Session, data: ScrapingFailureCreate) -> ScrapingFailure:
        """Creates or updates a sentence-level failure for later retry."""
        batch = db.query(ScrapingProgress).filter(ScrapingProgress.id == data.progress_id).first()
        if batch is None:
            raise ValueError(f"ScrapingProgress {data.progress_id} not found")

        failure = (
            db.query(ScrapingFailure)
            .filter(
                ScrapingFailure.progress_id == data.progress_id,
                ScrapingFailure.pagina == data.pagina,
                ScrapingFailure.posicion_en_pagina == data.posicion_en_pagina,
                ScrapingFailure.resuelta.is_(False),
            )
            .first()
        )

        now = utc_now()
        if failure is None:
            failure = ScrapingFailure(
                progress_id=data.progress_id,
                pagina=data.pagina,
                posicion_en_pagina=data.posicion_en_pagina,
                numero_sentencia=data.numero_sentencia,
                sede=data.sede,
                fecha_sentencia=data.fecha_sentencia,
                error_tipo=data.error_tipo,
                error_mensaje=data.error_mensaje,
                intentos=1,
                max_intentos=5,
                resuelta=False,
                ultimo_intento=now,
            )
            db.add(failure)
            batch.sentencias_fallidas += 1
        else:
            # Para Bruno: evitamos duplicados por página/fila y contamos reintentos.
            failure.numero_sentencia = data.numero_sentencia or failure.numero_sentencia
            failure.sede = data.sede or failure.sede
            failure.fecha_sentencia = data.fecha_sentencia or failure.fecha_sentencia
            failure.error_tipo = data.error_tipo
            failure.error_mensaje = data.error_mensaje
            failure.intentos += 1
            failure.ultimo_intento = now

        batch.updated_at = now
        db.commit()
        db.refresh(failure)
        return failure

    @staticmethod
    def get_unresolved_failures(
        db: Session, progress_id: Optional[int] = None
    ) -> list[ScrapingFailure]:
        """Returns unresolved failures still eligible for retry."""
        query = db.query(ScrapingFailure).filter(
            ScrapingFailure.resuelta.is_(False),
            ScrapingFailure.intentos < ScrapingFailure.max_intentos,
        )

        if progress_id is not None:
            query = query.filter(ScrapingFailure.progress_id == progress_id)

        return query.order_by(
            ScrapingFailure.progress_id.asc(),
            ScrapingFailure.pagina.asc(),
            ScrapingFailure.posicion_en_pagina.asc(),
        ).all()

    @staticmethod
    def resolve_failure(db: Session, failure_id: int) -> None:
        """Marks a failure as resolved and updates the batch counter."""
        failure = db.query(ScrapingFailure).filter(ScrapingFailure.id == failure_id).first()
        if failure is None:
            raise ValueError(f"ScrapingFailure {failure_id} not found")

        if failure.resuelta:
            return

        failure.resuelta = True
        failure.ultimo_intento = utc_now()

        batch = db.query(ScrapingProgress).filter(ScrapingProgress.id == failure.progress_id).first()
        if batch is not None and batch.sentencias_fallidas > 0:
            batch.sentencias_fallidas -= 1
            batch.updated_at = utc_now()

        db.commit()

    @staticmethod
    def log(db: Session, data: ScrapingLogCreate) -> ScrapingLog:
        """Stores a structured crawler event."""
        log_entry = ScrapingLog(
            worker_id=data.worker_id,
            progress_id=data.progress_id,
            nivel=data.nivel,
            evento=data.evento,
            mensaje=data.mensaje,
            sentencias_por_minuto=data.sentencias_por_minuto,
            tiempo_respuesta_ms=data.tiempo_respuesta_ms,
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry

    @staticmethod
    def get_overall_progress(db: Session) -> dict[str, int]:
        """Aggregates global crawler progress for orchestration dashboards."""
        batches = db.query(ScrapingProgress).all()

        summary = OverallScrapingProgress(
            totalBatches=len(batches),
            completedBatches=sum(1 for batch in batches if batch.estado == "completed"),
            inProgressBatches=sum(1 for batch in batches if batch.estado == "in_progress"),
            pendingBatches=sum(1 for batch in batches if batch.estado == "pending"),
            failedBatches=sum(1 for batch in batches if batch.estado == "failed"),
            totalSentenciasDescargadas=sum(batch.sentencias_descargadas or 0 for batch in batches),
            totalSentenciasFallidas=sum(batch.sentencias_fallidas or 0 for batch in batches),
        )
        return summary.model_dump()
