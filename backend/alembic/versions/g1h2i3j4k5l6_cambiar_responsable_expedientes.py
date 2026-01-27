"""Cambiar socio_responsable_id a responsable_id en expedientes

Revision ID: g1h2i3j4k5l6
Revises: f1a2b3c4d5e6
Create Date: 2026-01-27

Cambia la FK de socios a usuarios para permitir que colaboradores
(como Gerardo) puedan ser responsables de expedientes.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'g1h2i3j4k5l6'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Eliminar FK y columna antigua
    op.drop_constraint('expedientes_socio_responsable_id_fkey', 'expedientes', type_='foreignkey')
    op.drop_column('expedientes', 'socio_responsable_id')

    # 2. Agregar nueva columna con FK a usuarios
    op.add_column('expedientes', sa.Column('responsable_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('expedientes_responsable_id_fkey', 'expedientes', 'usuarios', ['responsable_id'], ['id'])


def downgrade():
    # 1. Eliminar nueva columna
    op.drop_constraint('expedientes_responsable_id_fkey', 'expedientes', type_='foreignkey')
    op.drop_column('expedientes', 'responsable_id')

    # 2. Restaurar columna antigua
    op.add_column('expedientes', sa.Column('socio_responsable_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('expedientes_socio_responsable_id_fkey', 'expedientes', 'socios', ['socio_responsable_id'], ['id'])
