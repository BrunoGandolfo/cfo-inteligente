"""regularizar_columnas_extraccion_contratos

Revision ID: 3af6f419c712
Revises: a8839c0f5f5d
Create Date: 2026-04-09 06:44:42.732082

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '3af6f419c712'
down_revision: Union[str, None] = 'a8839c0f5f5d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    columns_contratos = [c["name"] for c in inspector.get_columns("contratos")]

    if "intentos_extraccion" not in columns_contratos:
        op.add_column(
            "contratos",
            sa.Column("intentos_extraccion", sa.Integer(), nullable=False, server_default="0"),
        )

    if "ultimo_error_extraccion" not in columns_contratos:
        op.add_column(
            "contratos",
            sa.Column("ultimo_error_extraccion", sa.Text(), nullable=True),
        )

    if "requiere_procesamiento_manual" not in columns_contratos:
        op.add_column(
            "contratos",
            sa.Column("requiere_procesamiento_manual", sa.Boolean(), nullable=False, server_default="false"),
        )


def downgrade() -> None:
    pass
