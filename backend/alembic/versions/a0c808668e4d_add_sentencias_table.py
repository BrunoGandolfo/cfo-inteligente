"""add sentencias table

Revision ID: a0c808668e4d
Revises: f2a3b4c5d6e7
Create Date: 2026-04-03 20:19:44.312926

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a0c808668e4d'
down_revision: Union[str, None] = 'f2a3b4c5d6e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'sentencias',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('bjn_id', sa.String(length=50), nullable=True),
        sa.Column('numero', sa.String(length=100), nullable=True),
        sa.Column('sede', sa.String(length=200), nullable=True),
        sa.Column('fecha', sa.Date(), nullable=True),
        sa.Column('tipo', sa.String(length=100), nullable=True),
        sa.Column('importancia', sa.String(length=50), nullable=True),
        sa.Column('materias', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('firmantes', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('descriptores', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('texto_completo', sa.Text(), nullable=True),
        sa.Column('resumen_ia', sa.Text(), nullable=True),
        sa.Column('resumen_generado_at', sa.DateTime(), nullable=True),
        sa.Column('query_origen', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sentencias_bjn_id'), 'sentencias', ['bjn_id'], unique=True)
    op.create_index(op.f('ix_sentencias_fecha'), 'sentencias', ['fecha'], unique=False)
    op.create_index('idx_sentencias_materias', 'sentencias', ['materias'], unique=False, postgresql_using='gin')
    op.create_index(
        'idx_sentencias_texto_completo',
        'sentencias',
        [sa.text("to_tsvector('spanish', coalesce(texto_completo, ''))")],
        unique=False,
        postgresql_using='gin',
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_sentencias_fecha'), table_name='sentencias')
    op.drop_index(op.f('ix_sentencias_bjn_id'), table_name='sentencias')
    op.drop_index('idx_sentencias_texto_completo', table_name='sentencias', postgresql_using='gin')
    op.drop_index('idx_sentencias_materias', table_name='sentencias', postgresql_using='gin')
    op.drop_table('sentencias')
