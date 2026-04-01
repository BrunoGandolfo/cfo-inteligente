"""add_deleted_at_to_conversaciones

Revision ID: f2a3b4c5d6e7
Revises: e9d89e732e50
Create Date: 2026-04-01 12:00:00.000000

Agrega columna deleted_at a tabla conversaciones para soportar soft delete.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2a3b4c5d6e7'
down_revision: Union[str, None] = 'e9d89e732e50'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('conversaciones', sa.Column('deleted_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('conversaciones', 'deleted_at')
