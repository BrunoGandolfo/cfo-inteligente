"""fix_drop_leyes_indices_operaciones

Revision ID: eee195db727f
Revises: i3j4k5l6m7n8
Create Date: 2026-02-06 19:26:56.099227

Correctiva: drop tabla leyes e índices operaciones con SQL directo.
op.drop_table(if_exists=True) y postgresql_ops no funcionaron en la migración anterior.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'eee195db727f'
down_revision: Union[str, None] = 'i3j4k5l6m7n8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop leyes con SQL directo (alembic no soporta if_exists)
    op.execute('DROP TABLE IF EXISTS leyes CASCADE')

    # Índices parciales en operaciones con SQL directo
    op.execute('''
        CREATE INDEX IF NOT EXISTS idx_operaciones_deleted_fecha
        ON operaciones (fecha DESC)
        WHERE deleted_at IS NULL
    ''')
    op.execute('''
        CREATE INDEX IF NOT EXISTS idx_operaciones_deleted_tipo
        ON operaciones (tipo_operacion)
        WHERE deleted_at IS NULL
    ''')


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS idx_operaciones_deleted_tipo')
    op.execute('DROP INDEX IF EXISTS idx_operaciones_deleted_fecha')
