"""Add leyes table

Revision ID: a1b2c3d4e5f6
Revises: 387b077e0036
Create Date: 2026-01-15 12:00:00.000000

Tabla para gestión de leyes uruguayas del Parlamento.
Integración con CSV: https://parlamento.gub.uy/transparencia/datos-abiertos/leyes-promulgadas/csv
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '387b077e0036'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### TABLA: leyes ###
    op.create_table(
        'leyes',
        # Identificación
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('numero', sa.Integer(), nullable=False),
        sa.Column('anio', sa.Integer(), nullable=False),
        
        # Información básica
        sa.Column('titulo', sa.Text(), nullable=False),
        sa.Column('fecha_promulgacion', sa.Date(), nullable=True),
        
        # URLs de origen
        sa.Column('url_parlamento', sa.String(500), nullable=True),
        sa.Column('url_impo', sa.String(500), nullable=True),
        
        # Contenido (se llena después con IMPO JSON)
        sa.Column('texto_completo', sa.Text(), nullable=True),
        sa.Column('tiene_texto', sa.Boolean(), server_default='false'),
        
        # Metadata de referencias
        sa.Column('leyes_referenciadas', sa.Integer(), server_default='0'),
        sa.Column('leyes_que_referencia', sa.Integer(), server_default='0'),
        
        # Auditoría estándar del sistema
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),  # Soft delete
        
        # Constraint único: no puede haber dos leyes con mismo número y año
        sa.UniqueConstraint('numero', 'anio', name='uq_ley_numero_anio'),
    )
    
    # Índices para búsquedas frecuentes
    op.create_index('ix_leyes_numero', 'leyes', ['numero'])
    op.create_index('ix_leyes_anio', 'leyes', ['anio'])
    op.create_index('ix_leyes_numero_anio', 'leyes', ['numero', 'anio'])
    op.create_index('ix_leyes_tiene_texto', 'leyes', ['tiene_texto'])


def downgrade() -> None:
    # Eliminar índices
    op.drop_index('ix_leyes_tiene_texto', table_name='leyes')
    op.drop_index('ix_leyes_numero_anio', table_name='leyes')
    op.drop_index('ix_leyes_anio', table_name='leyes')
    op.drop_index('ix_leyes_numero', table_name='leyes')
    
    # Eliminar tabla
    op.drop_table('leyes')

