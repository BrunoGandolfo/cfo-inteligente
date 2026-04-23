"""add resultado_uk to verificaciones_ala

Revision ID: a1f2b3c4d5e6
Revises: 6c8e4b9f1a2d
Create Date: 2026-04-23 17:00:00.000000
"""
from typing import Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = 'a1f2b3c4d5e6'
down_revision: Union[str, None] = '6c8e4b9f1a2d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('verificaciones_ala', sa.Column('resultado_uk', JSONB, nullable=True))


def downgrade():
    op.drop_column('verificaciones_ala', 'resultado_uk')
