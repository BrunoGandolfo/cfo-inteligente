"""create_consultas_contables

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table('consultas_contables'):
        return

    op.create_table(
        'consultas_contables',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('usuario_id', sa.UUID(), nullable=False),
        sa.Column('servicio', sa.String(length=50), nullable=False),
        sa.Column('rut', sa.String(length=20), nullable=True),
        sa.Column('ci', sa.String(length=20), nullable=True),
        sa.Column('datos_entrada', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('exitosa', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('resultado_texto', sa.Text(), nullable=True),
        sa.Column('resultado_datos', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('cliente_nombre', sa.String(length=200), nullable=True),
        sa.Column('cliente_rut', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_consultas_contables_usuario_id', 'consultas_contables', ['usuario_id'], unique=False)
    op.create_index('ix_consultas_contables_servicio', 'consultas_contables', ['servicio'], unique=False)
    op.create_index('ix_consultas_contables_rut', 'consultas_contables', ['rut'], unique=False)
    op.create_index('ix_consultas_contables_ci', 'consultas_contables', ['ci'], unique=False)
    op.create_index('ix_consultas_contables_created_at', 'consultas_contables', ['created_at'], unique=False)
    op.create_index('ix_consultas_contables_deleted_at', 'consultas_contables', ['deleted_at'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table('consultas_contables'):
        return
    op.drop_index('ix_consultas_contables_deleted_at', table_name='consultas_contables')
    op.drop_index('ix_consultas_contables_created_at', table_name='consultas_contables')
    op.drop_index('ix_consultas_contables_ci', table_name='consultas_contables')
    op.drop_index('ix_consultas_contables_rut', table_name='consultas_contables')
    op.drop_index('ix_consultas_contables_servicio', table_name='consultas_contables')
    op.drop_index('ix_consultas_contables_usuario_id', table_name='consultas_contables')
    op.drop_table('consultas_contables')
