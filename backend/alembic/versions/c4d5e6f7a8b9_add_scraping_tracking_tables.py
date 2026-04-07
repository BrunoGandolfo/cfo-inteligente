"""add scraping tracking tables

Revision ID: c4d5e6f7a8b9
Revises: f1a2b3c4d5e6, a0c808668e4d
Create Date: 2026-04-06 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, Sequence[str], None] = ("f1a2b3c4d5e6", "a0c808668e4d")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scraping_progress",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("fecha_fin", sa.Date(), nullable=False),
        sa.Column("pagina_actual", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_paginas", sa.Integer(), nullable=True),
        sa.Column("sentencias_encontradas", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sentencias_descargadas", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sentencias_fallidas", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("worker_id", sa.String(length=50), nullable=True),
        sa.Column("ultimo_intento", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_ultimo", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "estado IN ('pending', 'in_progress', 'completed', 'failed', 'paused')",
            name="ck_scraping_progress_estado",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fecha_inicio", "fecha_fin", name="uq_scraping_progress_fecha_rango"),
    )
    op.create_index("idx_scraping_progress_estado", "scraping_progress", ["estado"], unique=False)

    op.create_table(
        "scraping_failures",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("progress_id", sa.Integer(), nullable=False),
        sa.Column("pagina", sa.Integer(), nullable=False),
        sa.Column("posicion_en_pagina", sa.Integer(), nullable=False),
        sa.Column("numero_sentencia", sa.String(length=100), nullable=True),
        sa.Column("sede", sa.String(length=200), nullable=True),
        sa.Column("fecha_sentencia", sa.Date(), nullable=True),
        sa.Column("error_tipo", sa.String(length=50), nullable=False),
        sa.Column("error_mensaje", sa.Text(), nullable=False),
        sa.Column("intentos", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("max_intentos", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("resuelta", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("ultimo_intento", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["progress_id"], ["scraping_progress.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_scraping_failures_progress", "scraping_failures", ["progress_id"], unique=False)
    op.create_index(
        "idx_scraping_failures_resuelta",
        "scraping_failures",
        ["resuelta"],
        unique=False,
        postgresql_where=sa.text("resuelta = FALSE"),
    )

    op.create_table(
        "scraping_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("worker_id", sa.String(length=50), nullable=True),
        sa.Column("progress_id", sa.Integer(), nullable=True),
        sa.Column("nivel", sa.String(length=10), nullable=False),
        sa.Column("evento", sa.String(length=100), nullable=False),
        sa.Column("mensaje", sa.Text(), nullable=False),
        sa.Column("sentencias_por_minuto", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("tiempo_respuesta_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("nivel IN ('info', 'warn', 'error', 'debug')", name="ck_scraping_logs_nivel"),
        sa.ForeignKeyConstraint(["progress_id"], ["scraping_progress.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_scraping_logs_created", "scraping_logs", ["created_at"], unique=False)
    op.create_index(
        "idx_scraping_logs_nivel",
        "scraping_logs",
        ["nivel"],
        unique=False,
        postgresql_where=sa.text("nivel IN ('warn', 'error')"),
    )


def downgrade() -> None:
    op.drop_index("idx_scraping_logs_nivel", table_name="scraping_logs")
    op.drop_index("idx_scraping_logs_created", table_name="scraping_logs")
    op.drop_table("scraping_logs")

    op.drop_index("idx_scraping_failures_resuelta", table_name="scraping_failures")
    op.drop_index("idx_scraping_failures_progress", table_name="scraping_failures")
    op.drop_table("scraping_failures")

    op.drop_index("idx_scraping_progress_estado", table_name="scraping_progress")
    op.drop_table("scraping_progress")
