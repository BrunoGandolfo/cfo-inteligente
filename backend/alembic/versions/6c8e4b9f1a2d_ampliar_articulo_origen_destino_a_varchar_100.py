"""ampliar articulo origen destino a varchar 100

Revision ID: 6c8e4b9f1a2d
Revises: 35a4e7ff8b0c
Create Date: 2026-04-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6c8e4b9f1a2d"
down_revision: Union[str, None] = "35a4e7ff8b0c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "normas_relaciones",
        "articulo_origen",
        type_=sa.String(100),
        existing_type=sa.String(50),
    )
    op.alter_column(
        "normas_relaciones",
        "articulo_destino",
        type_=sa.String(100),
        existing_type=sa.String(50),
    )


def downgrade() -> None:
    op.alter_column(
        "normas_relaciones",
        "articulo_destino",
        type_=sa.String(50),
        existing_type=sa.String(100),
    )
    op.alter_column(
        "normas_relaciones",
        "articulo_origen",
        type_=sa.String(50),
        existing_type=sa.String(100),
    )
