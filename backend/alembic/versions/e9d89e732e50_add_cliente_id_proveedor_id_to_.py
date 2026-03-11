"""add_cliente_id_proveedor_id_to_operaciones

Revision ID: e9d89e732e50
Revises: eee195db727f
Create Date: 2026-03-11 06:58:46.856483

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'e9d89e732e50'
down_revision: Union[str, None] = 'eee195db727f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('operaciones', sa.Column('cliente_id', UUID(as_uuid=True), sa.ForeignKey('clientes.id'), nullable=True))
    op.add_column('operaciones', sa.Column('proveedor_id', UUID(as_uuid=True), sa.ForeignKey('proveedores.id'), nullable=True))
    op.create_index('ix_operaciones_cliente_id', 'operaciones', ['cliente_id'])
    op.create_index('ix_operaciones_proveedor_id', 'operaciones', ['proveedor_id'])


def downgrade() -> None:
    op.drop_index('ix_operaciones_proveedor_id', 'operaciones')
    op.drop_index('ix_operaciones_cliente_id', 'operaciones')
    op.drop_column('operaciones', 'proveedor_id')
    op.drop_column('operaciones', 'cliente_id')
