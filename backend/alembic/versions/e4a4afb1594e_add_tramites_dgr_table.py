"""add tramites_dgr table

Revision ID: e4a4afb1594e
Revises: 124a7e5316b2
Create Date: 2026-04-07 10:42:17.524002

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e4a4afb1594e'
down_revision: Union[str, None] = '124a7e5316b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tramites_dgr',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('registro', sa.String(length=10), nullable=False),
    sa.Column('registro_nombre', sa.String(length=200), nullable=True),
    sa.Column('oficina', sa.String(length=5), nullable=False),
    sa.Column('oficina_nombre', sa.String(length=100), nullable=True),
    sa.Column('anio', sa.Integer(), nullable=False),
    sa.Column('numero_entrada', sa.Integer(), nullable=False),
    sa.Column('bis', sa.String(length=10), nullable=True),
    sa.Column('fecha_ingreso', sa.Date(), nullable=True),
    sa.Column('escribano_emisor', sa.String(length=300), nullable=True),
    sa.Column('estado_actual', sa.String(length=50), nullable=True),
    sa.Column('actos', sa.Text(), nullable=True),
    sa.Column('observaciones', sa.Text(), nullable=True),
    sa.Column('fecha_vencimiento', sa.Date(), nullable=True),
    sa.Column('ultimo_chequeo', sa.DateTime(timezone=True), nullable=True),
    sa.Column('estado_anterior', sa.String(length=50), nullable=True),
    sa.Column('cambio_detectado', sa.Boolean(), nullable=True),
    sa.Column('activo', sa.Boolean(), nullable=True),
    sa.Column('responsable_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['responsable_id'], ['usuarios.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('registro', 'oficina', 'anio', 'numero_entrada', 'bis', name='uq_tramite_dgr_identificacion')
    )
    op.create_index('ix_tramites_dgr_activo', 'tramites_dgr', ['activo', 'deleted_at'], unique=False)
    op.create_index('ix_tramites_dgr_responsable', 'tramites_dgr', ['responsable_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_tramites_dgr_responsable', table_name='tramites_dgr')
    op.drop_index('ix_tramites_dgr_activo', table_name='tramites_dgr')
    op.drop_table('tramites_dgr')
