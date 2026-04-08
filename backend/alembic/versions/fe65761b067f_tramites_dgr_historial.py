"""tramites_dgr_historial

Revision ID: fe65761b067f
Revises: e4a4afb1594e
Create Date: 2026-04-08 11:32:48.747441

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "fe65761b067f"
down_revision: Union[str, None] = "e4a4afb1594e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tramites_dgr_historial",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tramite_dgr_id", sa.UUID(), nullable=False),
        sa.Column("campo_modificado", sa.String(length=100), nullable=False),
        sa.Column("valor_anterior", sa.Text(), nullable=True),
        sa.Column("valor_nuevo", sa.Text(), nullable=True),
        sa.Column("detectado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tramite_dgr_id"], ["tramites_dgr.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("tramites_dgr_historial")
