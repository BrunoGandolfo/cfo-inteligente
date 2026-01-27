"""Hacer password_hash nullable para flujo de primer registro

Revision ID: h2i3j4k5l6m7
Revises: g1h2i3j4k5l6
Create Date: 2026-01-27
"""
from alembic import op
import sqlalchemy as sa

revision = 'h2i3j4k5l6m7'
down_revision = 'g1h2i3j4k5l6'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('usuarios', 'password_hash',
                    existing_type=sa.VARCHAR(255),
                    nullable=True)


def downgrade():
    op.alter_column('usuarios', 'password_hash',
                    existing_type=sa.VARCHAR(255),
                    nullable=False)
