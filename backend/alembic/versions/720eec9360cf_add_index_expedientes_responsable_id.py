"""add_index_expedientes_responsable_id

Revision ID: 720eec9360cf
Revises: 3af6f419c712
Create Date: 2026-04-09 17:04:06.412355

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '720eec9360cf'
down_revision: Union[str, None] = '3af6f419c712'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_expedientes_responsable_id",
        "expedientes",
        ["responsable_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_expedientes_responsable_id", table_name="expedientes")
