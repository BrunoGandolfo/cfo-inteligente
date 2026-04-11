"""create_ala_tables_complete

Revision ID: b2c3d4e5f6a7
Revises: 50b17787a8f8
Create Date: 2026-04-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = '50b17787a8f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NUEVAS_COLUMNAS = [
    ('tipo_operacion_ala', sa.Column('tipo_operacion_ala', sa.String(length=50), nullable=True)),
    ('origen_fondos', sa.Column('origen_fondos', sa.Text(), nullable=True)),
    ('medio_pago', sa.Column('medio_pago', sa.String(length=50), nullable=True)),
    ('monto_operacion', sa.Column('monto_operacion', sa.Numeric(precision=15, scale=2), nullable=True)),
    ('beneficiario_final_nombre', sa.Column('beneficiario_final_nombre', sa.String(length=300), nullable=True)),
    ('beneficiario_final_documento', sa.Column('beneficiario_final_documento', sa.String(length=50), nullable=True)),
    ('observaciones_oficial', sa.Column('observaciones_oficial', sa.Text(), nullable=True)),
]


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'listas_ala_metadata' not in existing_tables:
        op.create_table(
            'listas_ala_metadata',
            sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
            sa.Column('nombre_lista', sa.String(length=50), nullable=False),
            sa.Column('url_fuente', sa.String(length=500), nullable=True),
            sa.Column('ultima_descarga', sa.DateTime(), nullable=True),
            sa.Column('hash_contenido', sa.String(length=64), nullable=True),
            sa.Column('cantidad_registros', sa.Integer(), nullable=True),
            sa.Column('estado', sa.String(length=20), nullable=True),
            sa.Column('error_detalle', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )

    if 'verificaciones_ala' not in existing_tables:
        op.create_table(
            'verificaciones_ala',
            sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
            sa.Column('nombre_completo', sa.String(length=300), nullable=False),
            sa.Column('tipo_documento', sa.String(length=20), nullable=True),
            sa.Column('numero_documento', sa.String(length=50), nullable=True),
            sa.Column('nacionalidad', sa.String(length=3), nullable=True),
            sa.Column('fecha_nacimiento', sa.Date(), nullable=True),
            sa.Column('es_persona_juridica', sa.Boolean(), nullable=True),
            sa.Column('razon_social', sa.String(length=300), nullable=True),
            # Campos nuevos para cumplimiento normativo (Decreto 379/018)
            sa.Column('tipo_operacion_ala', sa.String(length=50), nullable=True),
            sa.Column('origen_fondos', sa.Text(), nullable=True),
            sa.Column('medio_pago', sa.String(length=50), nullable=True),
            sa.Column('monto_operacion', sa.Numeric(precision=15, scale=2), nullable=True),
            sa.Column('beneficiario_final_nombre', sa.String(length=300), nullable=True),
            sa.Column('beneficiario_final_documento', sa.String(length=50), nullable=True),
            sa.Column('observaciones_oficial', sa.Text(), nullable=True),
            sa.Column('nivel_diligencia', sa.String(length=20), nullable=False),
            sa.Column('nivel_riesgo', sa.String(length=20), nullable=False),
            sa.Column('es_pep', sa.Boolean(), nullable=True),
            sa.Column('resultado_onu', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('resultado_pep', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('resultado_ofac', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('resultado_ue', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('resultado_gafi', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('busqueda_google_realizada', sa.Boolean(), nullable=True),
            sa.Column('busqueda_google_observaciones', sa.Text(), nullable=True),
            sa.Column('busqueda_news_realizada', sa.Boolean(), nullable=True),
            sa.Column('busqueda_news_observaciones', sa.Text(), nullable=True),
            sa.Column('busqueda_wikipedia_realizada', sa.Boolean(), nullable=True),
            sa.Column('busqueda_wikipedia_observaciones', sa.Text(), nullable=True),
            sa.Column('hash_verificacion', sa.String(length=64), nullable=False),
            sa.Column('certificado_pdf_path', sa.String(length=500), nullable=True),
            sa.Column('expediente_id', sa.UUID(), nullable=True),
            sa.Column('contrato_id', sa.UUID(), nullable=True),
            sa.Column('usuario_id', sa.UUID(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['contrato_id'], ['contratos.id'], ),
            sa.ForeignKeyConstraint(['expediente_id'], ['expedientes.id'], ),
            sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_verificaciones_ala_contrato_id', 'verificaciones_ala', ['contrato_id'], unique=False)
        op.create_index('ix_verificaciones_ala_deleted_at', 'verificaciones_ala', ['deleted_at'], unique=False)
        op.create_index('ix_verificaciones_ala_expediente_id', 'verificaciones_ala', ['expediente_id'], unique=False)
        op.create_index('ix_verificaciones_ala_nivel_riesgo', 'verificaciones_ala', ['nivel_riesgo'], unique=False)
        op.create_index('ix_verificaciones_ala_nombre_completo', 'verificaciones_ala', ['nombre_completo'], unique=False)
        op.create_index('ix_verificaciones_ala_numero_documento', 'verificaciones_ala', ['numero_documento'], unique=False)
        op.create_index('ix_verificaciones_ala_usuario_id', 'verificaciones_ala', ['usuario_id'], unique=False)
    else:
        # La tabla existe (migración previa). Agregar solo las columnas nuevas que falten.
        existing_cols = {c['name'] for c in inspector.get_columns('verificaciones_ala')}
        for nombre, columna in NUEVAS_COLUMNAS:
            if nombre not in existing_cols:
                op.add_column('verificaciones_ala', columna)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if 'verificaciones_ala' in set(inspector.get_table_names()):
        existing_cols = {c['name'] for c in inspector.get_columns('verificaciones_ala')}
        for nombre, _ in NUEVAS_COLUMNAS:
            if nombre in existing_cols:
                op.drop_column('verificaciones_ala', nombre)
