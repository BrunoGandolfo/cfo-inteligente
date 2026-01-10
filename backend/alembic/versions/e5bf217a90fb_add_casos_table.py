"""add_casos_table

Revision ID: e5bf217a90fb
Revises: a1b2c3d4e5f6
Create Date: 2026-01-10 20:04:25.683571

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5bf217a90fb'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('casos',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('titulo', sa.String(length=300), nullable=False),
        sa.Column('estado', sa.Enum('PENDIENTE', 'EN_PROCESO', 'REQUIERE_ACCION', 'CERRADO', name='estadocaso'), nullable=False),
        sa.Column('prioridad', sa.Enum('CRITICA', 'ALTA', 'MEDIA', 'BAJA', name='prioridadcaso'), nullable=False),
        sa.Column('fecha_vencimiento', sa.Date(), nullable=True),
        sa.Column('responsable_id', sa.UUID(), nullable=False),
        sa.Column('expediente_id', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['expediente_id'], ['expedientes.id'], ),
        sa.ForeignKeyConstraint(['responsable_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('casos')
    op.execute('DROP TYPE IF EXISTS estadocaso')
    op.execute('DROP TYPE IF EXISTS prioridadcaso')
