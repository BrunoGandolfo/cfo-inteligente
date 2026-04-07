"""Integration tests for scraping tracking service."""

from datetime import date
from decimal import Decimal

import pytest

from app.models.scraping_progress import ScrapingFailure, ScrapingLog, ScrapingProgress
from app.schemas.scraping_progress import (
    ScrapingFailureCreate,
    ScrapingLogCreate,
    ScrapingProgressUpdate,
)
from app.services.scraping_progress_service import ScrapingProgressService


def create_batch(
    db_session,
    *,
    year: int,
    estado: str = "pending",
    pagina_actual: int = 0,
    total_paginas: int | None = None,
    sentencias_descargadas: int = 0,
    sentencias_fallidas: int = 0,
    worker_id: str | None = None,
    error_ultimo: str | None = None,
) -> ScrapingProgress:
    """Creates a persisted batch for test setup."""
    batch = ScrapingProgress(
        fecha_inicio=date(year, 1, 1),
        fecha_fin=date(year, 12, 31),
        estado=estado,
        pagina_actual=pagina_actual,
        total_paginas=total_paginas,
        sentencias_descargadas=sentencias_descargadas,
        sentencias_fallidas=sentencias_fallidas,
        worker_id=worker_id,
        error_ultimo=error_ultimo,
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)
    return batch


class TestInitializePartitions:
    @pytest.mark.integration
    def test_initialize_partitions_creates_yearly_batches(self, db_session):
        ScrapingProgressService.initialize_partitions(db_session, 2022, 2024)

        batches = db_session.query(ScrapingProgress).order_by(ScrapingProgress.fecha_inicio.asc()).all()

        assert len(batches) == 3
        assert [batch.fecha_inicio for batch in batches] == [
            date(2022, 1, 1),
            date(2023, 1, 1),
            date(2024, 1, 1),
        ]
        assert all(batch.estado == "pending" for batch in batches)

    @pytest.mark.integration
    def test_initialize_partitions_is_idempotent(self, db_session):
        ScrapingProgressService.initialize_partitions(db_session, 2024, 2024)
        ScrapingProgressService.initialize_partitions(db_session, 2024, 2024)

        assert db_session.query(ScrapingProgress).count() == 1

    def test_initialize_partitions_rejects_invalid_range(self, db_session):
        with pytest.raises(ValueError, match="year_start"):
            ScrapingProgressService.initialize_partitions(db_session, 2025, 2024)


class TestClaimNextBatch:
    @pytest.mark.integration
    def test_claim_next_batch_marks_pending_batch_in_progress(self, db_session):
        batch = create_batch(db_session, year=2024)

        claimed = ScrapingProgressService.claim_next_batch(db_session, "worker-1")

        assert claimed is not None
        assert claimed.id == batch.id
        assert claimed.estado == "in_progress"
        assert claimed.worker_id == "worker-1"
        assert claimed.ultimo_intento is not None

    @pytest.mark.integration
    def test_claim_next_batch_prioritizes_pending_before_failed(self, db_session):
        failed_batch = create_batch(db_session, year=2023, estado="failed", error_ultimo="timeout")
        pending_batch = create_batch(db_session, year=2024, estado="pending")

        claimed = ScrapingProgressService.claim_next_batch(db_session, "worker-2")

        assert claimed is not None
        assert claimed.id == pending_batch.id
        assert claimed.id != failed_batch.id

    @pytest.mark.integration
    def test_claim_next_batch_returns_none_without_available_batches(self, db_session):
        create_batch(db_session, year=2024, estado="completed")

        claimed = ScrapingProgressService.claim_next_batch(db_session, "worker-3")

        assert claimed is None


class TestUpdateBatchState:
    @pytest.mark.integration
    def test_update_progress_updates_counters_without_overwriting_missing_fields(self, db_session):
        batch = create_batch(db_session, year=2024, total_paginas=12)

        ScrapingProgressService.update_progress(
            db_session,
            batch.id,
            ScrapingProgressUpdate(
                pagina_actual=3,
                sentencias_encontradas=450,
                sentencias_descargadas=198,
            ),
        )

        db_session.refresh(batch)
        assert batch.pagina_actual == 3
        assert batch.total_paginas == 12
        assert batch.sentencias_encontradas == 450
        assert batch.sentencias_descargadas == 198
        assert batch.ultimo_intento is not None

    def test_update_progress_raises_for_missing_batch(self, db_session):
        with pytest.raises(ValueError, match="not found"):
            ScrapingProgressService.update_progress(
                db_session,
                999999,
                ScrapingProgressUpdate(pagina_actual=1),
            )

    @pytest.mark.integration
    def test_complete_batch_marks_batch_as_completed(self, db_session):
        batch = create_batch(
            db_session,
            year=2024,
            estado="in_progress",
            pagina_actual=4,
            total_paginas=10,
            worker_id="worker-1",
            error_ultimo="old error",
        )

        ScrapingProgressService.complete_batch(db_session, batch.id)

        db_session.refresh(batch)
        assert batch.estado == "completed"
        assert batch.worker_id is None
        assert batch.error_ultimo is None
        assert batch.pagina_actual == 10

    @pytest.mark.integration
    def test_fail_batch_marks_batch_as_failed(self, db_session):
        batch = create_batch(db_session, year=2024, estado="in_progress", worker_id="worker-1")

        ScrapingProgressService.fail_batch(db_session, batch.id, "session expired")

        db_session.refresh(batch)
        assert batch.estado == "failed"
        assert batch.worker_id is None
        assert batch.error_ultimo == "session expired"


class TestFailureLifecycle:
    @pytest.mark.integration
    def test_register_failure_creates_row_and_increments_batch_counter(self, db_session):
        batch = create_batch(db_session, year=2024)

        failure = ScrapingProgressService.register_failure(
            db_session,
            ScrapingFailureCreate(
                progress_id=batch.id,
                pagina=2,
                posicion_en_pagina=7,
                numero_sentencia="123/2024",
                sede="TAC 1o",
                fecha_sentencia=date(2024, 3, 10),
                error_tipo="timeout",
                error_mensaje="popup did not open",
            ),
        )

        db_session.refresh(batch)
        assert failure.id is not None
        assert failure.intentos == 1
        assert batch.sentencias_fallidas == 1

    @pytest.mark.integration
    def test_register_failure_reuses_unresolved_slot_and_increments_attempts(self, db_session):
        batch = create_batch(db_session, year=2024)

        first = ScrapingProgressService.register_failure(
            db_session,
            ScrapingFailureCreate(
                progress_id=batch.id,
                pagina=1,
                posicion_en_pagina=0,
                error_tipo="timeout",
                error_mensaje="first try",
            ),
        )
        second = ScrapingProgressService.register_failure(
            db_session,
            ScrapingFailureCreate(
                progress_id=batch.id,
                pagina=1,
                posicion_en_pagina=0,
                numero_sentencia="555/2024",
                error_tipo="network_error",
                error_mensaje="second try",
            ),
        )

        db_session.refresh(batch)
        assert second.id == first.id
        assert second.intentos == 2
        assert second.numero_sentencia == "555/2024"
        assert batch.sentencias_fallidas == 1
        assert db_session.query(ScrapingFailure).count() == 1

    @pytest.mark.integration
    def test_get_unresolved_failures_filters_by_batch_and_retry_budget(self, db_session):
        batch_a = create_batch(db_session, year=2023)
        batch_b = create_batch(db_session, year=2024)

        eligible = ScrapingFailure(
            progress_id=batch_a.id,
            pagina=1,
            posicion_en_pagina=0,
            error_tipo="timeout",
            error_mensaje="retry me",
            intentos=2,
            max_intentos=5,
            resuelta=False,
        )
        exhausted = ScrapingFailure(
            progress_id=batch_a.id,
            pagina=2,
            posicion_en_pagina=0,
            error_tipo="timeout",
            error_mensaje="stop retrying",
            intentos=5,
            max_intentos=5,
            resuelta=False,
        )
        resolved = ScrapingFailure(
            progress_id=batch_b.id,
            pagina=1,
            posicion_en_pagina=1,
            error_tipo="timeout",
            error_mensaje="already solved",
            intentos=1,
            max_intentos=5,
            resuelta=True,
        )
        db_session.add_all([eligible, exhausted, resolved])
        db_session.commit()

        failures = ScrapingProgressService.get_unresolved_failures(db_session, progress_id=batch_a.id)

        assert [failure.id for failure in failures] == [eligible.id]

    @pytest.mark.integration
    def test_resolve_failure_marks_row_resolved_and_decrements_batch_counter(self, db_session):
        batch = create_batch(db_session, year=2024, sentencias_fallidas=1)
        failure = ScrapingFailure(
            progress_id=batch.id,
            pagina=3,
            posicion_en_pagina=4,
            error_tipo="parse_error",
            error_mensaje="missing sentencia body",
            intentos=1,
            max_intentos=5,
            resuelta=False,
        )
        db_session.add(failure)
        db_session.commit()
        db_session.refresh(failure)

        ScrapingProgressService.resolve_failure(db_session, failure.id)

        db_session.refresh(failure)
        db_session.refresh(batch)
        assert failure.resuelta is True
        assert batch.sentencias_fallidas == 0


class TestLogAndSummary:
    @pytest.mark.integration
    def test_log_creates_structured_entry(self, db_session):
        batch = create_batch(db_session, year=2024)

        log_entry = ScrapingProgressService.log(
            db_session,
            ScrapingLogCreate(
                worker_id="worker-9",
                progress_id=batch.id,
                nivel="info",
                evento="page_scraped",
                mensaje="Processed page 12",
                sentencias_por_minuto=Decimal("31.50"),
                tiempo_respuesta_ms=7200,
            ),
        )

        stored = db_session.query(ScrapingLog).filter(ScrapingLog.id == log_entry.id).first()
        assert stored is not None
        assert stored.worker_id == "worker-9"
        assert stored.evento == "page_scraped"
        assert stored.sentencias_por_minuto == Decimal("31.50")

    @pytest.mark.integration
    def test_get_overall_progress_aggregates_batch_metrics(self, db_session):
        create_batch(db_session, year=2022, estado="completed", sentencias_descargadas=200)
        create_batch(db_session, year=2023, estado="in_progress", sentencias_descargadas=80, sentencias_fallidas=3)
        create_batch(db_session, year=2024, estado="pending", sentencias_descargadas=0)
        create_batch(db_session, year=2025, estado="failed", sentencias_descargadas=15, sentencias_fallidas=2)

        summary = ScrapingProgressService.get_overall_progress(db_session)

        assert summary == {
            "totalBatches": 4,
            "completedBatches": 1,
            "inProgressBatches": 1,
            "pendingBatches": 1,
            "failedBatches": 1,
            "totalSentenciasDescargadas": 295,
            "totalSentenciasFallidas": 5,
        }
