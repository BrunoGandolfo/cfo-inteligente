"""create_normas_articulos_relaciones

Revision ID: 35a4e7ff8b0c
Revises: c3d4e5f6a7b8
Create Date: 2026-04-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect

# revision identifiers
revision = '35a4e7ff8b0c'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa_inspect(bind)
    existing_tables = inspector.get_table_names()

    if 'normas' not in existing_tables:
        op.create_table('normas',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('tipo_norma', sa.String(length=50), nullable=False),
            sa.Column('numero', sa.Integer(), nullable=False),
            sa.Column('anio', sa.Integer(), nullable=False),
            sa.Column('nombre', sa.Text(), nullable=True),
            sa.Column('fecha_promulgacion', sa.Date(), nullable=True),
            sa.Column('fecha_publicacion', sa.Date(), nullable=True),
            sa.Column('indexacion', sa.Text(), nullable=True),
            sa.Column('vistos', sa.Text(), nullable=True),
            sa.Column('referencias_norma', sa.Text(), nullable=True),
            sa.Column('url_impo', sa.String(length=500), nullable=True),
            sa.Column('json_original', sa.JSON(), nullable=True),
            sa.Column('descarga_estado', sa.String(length=20), nullable=True),
            sa.Column('descarga_error', sa.Text(), nullable=True),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('tipo_norma', 'numero', 'anio', name='uq_norma_tipo_numero_anio')
        )
        op.create_index('ix_normas_descarga_estado', 'normas', ['descarga_estado'], unique=False)
        op.create_index('ix_normas_nombre', 'normas', ['nombre'], unique=False)
        op.create_index('ix_normas_tipo_numero_anio', 'normas', ['tipo_norma', 'numero', 'anio'], unique=False)

    if 'normas_articulos' not in existing_tables:
        op.create_table('normas_articulos',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('norma_id', sa.UUID(), nullable=False),
            sa.Column('numero_articulo', sa.String(length=20), nullable=False),
            sa.Column('titulo', sa.Text(), nullable=True),
            sa.Column('texto', sa.Text(), nullable=True),
            sa.Column('notas', sa.Text(), nullable=True),
            sa.Column('referencias', sa.Text(), nullable=True),
            sa.Column('indexacion', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['norma_id'], ['normas.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_normas_articulos_norma_id', 'normas_articulos', ['norma_id'], unique=False)

    if 'normas_relaciones' not in existing_tables:
        op.create_table('normas_relaciones',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('norma_origen_id', sa.UUID(), nullable=True),
            sa.Column('norma_destino_id', sa.UUID(), nullable=True),
            sa.Column('tipo_relacion', sa.String(length=50), nullable=False),
            sa.Column('articulo_origen', sa.String(length=50), nullable=True),
            sa.Column('articulo_destino', sa.String(length=50), nullable=True),
            sa.Column('texto_original', sa.Text(), nullable=True),
            sa.Column('norma_destino_ref', sa.String(length=200), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['norma_destino_id'], ['normas.id']),
            sa.ForeignKeyConstraint(['norma_origen_id'], ['normas.id']),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_normas_relaciones_destino', 'normas_relaciones', ['norma_destino_id'], unique=False)
        op.create_index('ix_normas_relaciones_origen', 'normas_relaciones', ['norma_origen_id'], unique=False)
        op.create_index('ix_normas_relaciones_tipo', 'normas_relaciones', ['tipo_relacion'], unique=False)


def downgrade():
    op.drop_index('ix_normas_relaciones_tipo', table_name='normas_relaciones')
    op.drop_index('ix_normas_relaciones_origen', table_name='normas_relaciones')
    op.drop_index('ix_normas_relaciones_destino', table_name='normas_relaciones')
    op.drop_table('normas_relaciones')
    op.drop_index('ix_normas_articulos_norma_id', table_name='normas_articulos')
    op.drop_table('normas_articulos')
    op.drop_index('ix_normas_tipo_numero_anio', table_name='normas')
    op.drop_index('ix_normas_nombre', table_name='normas')
    op.drop_index('ix_normas_descarga_estado', table_name='normas')
    op.drop_table('normas')
