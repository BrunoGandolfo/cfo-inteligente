"""Add contratos table

Revision ID: f1a2b3c4d5e6
Revises: e5bf217a90fb
Create Date: 2026-01-16 10:30:00.000000

Tabla para gestión de contratos y modelos notariales.
Almacena plantillas DOCX de contratos para el módulo notarial.
Fuente inicial: estudionotarialmachado.com (133 modelos)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'e5bf217a90fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### TABLA: contratos ###
    op.create_table(
        'contratos',
        
        # Identificación
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, 
                  server_default=sa.text('gen_random_uuid()')),
        
        # Información básica
        sa.Column('titulo', sa.String(255), nullable=False),
        sa.Column('categoria', sa.String(100), nullable=False),
        sa.Column('subcategoria', sa.String(100), nullable=True),
        sa.Column('descripcion', sa.Text(), nullable=True),
        
        # Contenido del contrato
        sa.Column('contenido_docx', sa.LargeBinary(), nullable=True),
        sa.Column('contenido_texto', sa.Text(), nullable=True),
        
        # Metadata de campos editables (JSON)
        sa.Column('campos_editables', postgresql.JSON(), nullable=True),
        
        # Trazabilidad de origen
        sa.Column('fuente_original', sa.String(100), server_default='machado'),
        sa.Column('archivo_original', sa.String(255), nullable=True),
        
        # Estado
        sa.Column('activo', sa.Boolean(), server_default='true'),
        
        # Auditoría estándar del sistema
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
    )
    
    # Índices para búsquedas frecuentes
    op.create_index('idx_contrato_categoria', 'contratos', ['categoria'])
    op.create_index('idx_contrato_titulo', 'contratos', ['titulo'])
    op.create_index('idx_contrato_activo', 'contratos', ['activo', 'deleted_at'])
    
    # Índice para búsqueda full-text (opcional, para PostgreSQL)
    # op.execute("CREATE INDEX idx_contrato_texto_gin ON contratos USING gin(to_tsvector('spanish', contenido_texto))")


def downgrade() -> None:
    # Eliminar índice full-text si existe
    # op.execute("DROP INDEX IF EXISTS idx_contrato_texto_gin")
    
    # Eliminar índices
    op.drop_index('idx_contrato_activo', table_name='contratos')
    op.drop_index('idx_contrato_titulo', table_name='contratos')
    op.drop_index('idx_contrato_categoria', table_name='contratos')
    
    # Eliminar tabla
    op.drop_table('contratos')
