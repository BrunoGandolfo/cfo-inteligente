"""regularizar_columnas_totales_pesificado_dolarizado

Revision ID: a8839c0f5f5d
Revises: fe65761b067f
Create Date: 2026-04-09 06:34:30.560847

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'a8839c0f5f5d'
down_revision: Union[str, None] = 'fe65761b067f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    columns_operaciones = [c["name"] for c in inspector.get_columns("operaciones")]

    if "total_pesificado" not in columns_operaciones:
        op.add_column(
            "operaciones",
            sa.Column("total_pesificado", sa.Numeric(15, 2), nullable=False, server_default="0"),
        )

    if "total_dolarizado" not in columns_operaciones:
        op.add_column(
            "operaciones",
            sa.Column("total_dolarizado", sa.Numeric(15, 2), nullable=False, server_default="0"),
        )

    columns_dist = [c["name"] for c in inspector.get_columns("distribuciones_detalle")]

    if "total_pesificado" not in columns_dist:
        op.add_column(
            "distribuciones_detalle",
            sa.Column("total_pesificado", sa.Numeric(15, 2), nullable=False, server_default="0"),
        )

    if "total_dolarizado" not in columns_dist:
        op.add_column(
            "distribuciones_detalle",
            sa.Column("total_dolarizado", sa.Numeric(15, 2), nullable=False, server_default="0"),
        )


def downgrade() -> None:
    # NO eliminamos columnas en downgrade porque tienen datos reales de producción
    pass
