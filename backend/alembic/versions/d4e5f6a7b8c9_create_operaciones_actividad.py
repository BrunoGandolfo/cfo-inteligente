"""create_operaciones_actividad

Revision ID: d4e5f6a7b8c9
Revises: a1f2b3c4d5e6
Create Date: 2026-10-07 00:00:00.000000

Registro append-only de quién crea, edita o anula operaciones.
Alimenta el resumen diario de actividad por mail.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'a1f2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table('operaciones_actividad'):
        return

    op.create_table(
        'operaciones_actividad',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('operacion_id', sa.UUID(), nullable=False),
        sa.Column('usuario_id', sa.UUID(), nullable=False),
        sa.Column('accion', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(
            "accion IN ('CREAR', 'EDITAR', 'ANULAR')",
            name='ck_operaciones_actividad_accion',
        ),
        sa.ForeignKeyConstraint(['operacion_id'], ['operaciones.id'], ),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_operaciones_actividad_operacion_id', 'operaciones_actividad', ['operacion_id'], unique=False)
    op.create_index('ix_operaciones_actividad_usuario_id', 'operaciones_actividad', ['usuario_id'], unique=False)
    op.create_index('ix_operaciones_actividad_created_at', 'operaciones_actividad', ['created_at'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table('operaciones_actividad'):
        return
    op.drop_index('ix_operaciones_actividad_created_at', table_name='operaciones_actividad')
    op.drop_index('ix_operaciones_actividad_usuario_id', table_name='operaciones_actividad')
    op.drop_index('ix_operaciones_actividad_operacion_id', table_name='operaciones_actividad')
    op.drop_table('operaciones_actividad')
