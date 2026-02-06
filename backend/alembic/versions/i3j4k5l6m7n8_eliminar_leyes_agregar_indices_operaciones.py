"""eliminar_leyes_agregar_indices_operaciones

Revision ID: i3j4k5l6m7n8
Revises: e0b459903d90
Create Date: 2026-02-06

- Elimina la tabla leyes (módulo de leyes removido del sistema).
- Agrega índices en operaciones para consultas por deleted_at, fecha y tipo_operacion.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'i3j4k5l6m7n8'
down_revision: Union[str, None] = 'e0b459903d90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Eliminar tabla leyes (IF EXISTS por seguridad)
    op.drop_table('leyes', if_exists=True)

    # Índices para operaciones (solo filas no eliminadas)
    op.create_index(
        'idx_operaciones_deleted_fecha',
        'operaciones',
        ['deleted_at', 'fecha'],
        postgresql_where=sa.text('deleted_at IS NULL'),
        postgresql_ops={'fecha': 'DESC'},
    )
    op.create_index(
        'idx_operaciones_deleted_tipo',
        'operaciones',
        ['deleted_at', 'tipo_operacion'],
        postgresql_where=sa.text('deleted_at IS NULL'),
    )


def downgrade() -> None:
    op.drop_index('idx_operaciones_deleted_tipo', table_name='operaciones')
    op.drop_index('idx_operaciones_deleted_fecha', table_name='operaciones')
    # NO recrear tabla leyes en downgrade (decisión de negocio)
