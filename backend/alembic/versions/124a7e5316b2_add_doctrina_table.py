"""add doctrina table

Revision ID: 124a7e5316b2
Revises: c4d5e6f7a8b9
Create Date: 2026-04-07 01:58:15.179893

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '124a7e5316b2'
down_revision: Union[str, None] = 'c4d5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('doctrina',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('oai_identifier', sa.String(length=300), nullable=False),
    sa.Column('titulo', sa.Text(), nullable=False),
    sa.Column('autor', sa.String(length=500), nullable=True),
    sa.Column('fecha_publicacion', sa.Date(), nullable=True),
    sa.Column('fuente', sa.String(length=100), nullable=False),
    sa.Column('revista', sa.String(length=200), nullable=True),
    sa.Column('url_articulo', sa.String(length=500), nullable=True),
    sa.Column('url_pdf', sa.String(length=500), nullable=True),
    sa.Column('abstract', sa.Text(), nullable=True),
    sa.Column('texto_completo', sa.Text(), nullable=True),
    sa.Column('materias', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('idioma', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_doctrina_oai_identifier'), 'doctrina', ['oai_identifier'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_doctrina_oai_identifier'), table_name='doctrina')
    op.drop_table('doctrina')
