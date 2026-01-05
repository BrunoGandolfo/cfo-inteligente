"""crear_tablas_expedientes

Revision ID: 387b077e0036
Revises: e7f8a9b2c1d3
Create Date: 2026-01-04 22:24:07.391931

Tablas para gestión de expedientes judiciales del Poder Judicial de Uruguay.
Integración con Web Service: http://expedientes.poderjudicial.gub.uy/wsConsultaIUE.php?wsdl

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '387b077e0036'
down_revision: Union[str, None] = 'e7f8a9b2c1d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### TABLA: expedientes ###
    op.create_table(
        'expedientes',
        # Identificación
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('iue', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('iue_sede', sa.Integer(), nullable=False),
        sa.Column('iue_numero', sa.Integer(), nullable=False),
        sa.Column('iue_anio', sa.Integer(), nullable=False),
        
        # Datos del expediente (del Web Service)
        sa.Column('caratula', sa.String(500), nullable=True),
        sa.Column('origen', sa.String(200), nullable=True),
        sa.Column('abogado_actor', sa.String(200), nullable=True),
        sa.Column('abogado_demandado', sa.String(200), nullable=True),
        
        # Relaciones con entidades del sistema
        sa.Column('cliente_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('clientes.id'), nullable=True),
        sa.Column('area_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('areas.id'), nullable=True),
        sa.Column('socio_responsable_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('socios.id'), nullable=True),
        
        # Estado de sincronización
        sa.Column('ultimo_movimiento', sa.Date(), nullable=True),
        sa.Column('cantidad_movimientos', sa.Integer(), server_default='0'),
        sa.Column('ultima_sincronizacion', sa.DateTime(), nullable=True),
        
        # Control
        sa.Column('activo', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
    )
    
    # Índices adicionales para búsquedas frecuentes
    op.create_index('ix_expedientes_iue_anio', 'expedientes', ['iue_anio'])
    op.create_index('ix_expedientes_socio_responsable', 'expedientes', ['socio_responsable_id'])
    op.create_index('ix_expedientes_cliente', 'expedientes', ['cliente_id'])
    
    # ### TABLA: expedientes_movimientos ###
    op.create_table(
        'expedientes_movimientos',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('expediente_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('expedientes.id', ondelete='CASCADE'), 
                  nullable=False, index=True),
        
        # Datos del movimiento (del Web Service)
        sa.Column('fecha', sa.Date(), nullable=False),
        sa.Column('tipo', sa.String(100), nullable=True),
        sa.Column('decreto', sa.String(50), nullable=True),
        sa.Column('vencimiento', sa.Date(), nullable=True),
        sa.Column('sede', sa.String(200), nullable=True),
        
        # Control de duplicados
        sa.Column('hash_movimiento', sa.String(64), unique=True, nullable=False, index=True),
        
        # Notificaciones
        sa.Column('notificado', sa.Boolean(), server_default='false'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
    )
    
    # Índices adicionales para movimientos
    op.create_index('ix_expedientes_movimientos_fecha', 'expedientes_movimientos', ['fecha'])
    op.create_index('ix_expedientes_movimientos_vencimiento', 'expedientes_movimientos', ['vencimiento'])


def downgrade() -> None:
    # Eliminar índices de movimientos
    op.drop_index('ix_expedientes_movimientos_vencimiento', table_name='expedientes_movimientos')
    op.drop_index('ix_expedientes_movimientos_fecha', table_name='expedientes_movimientos')
    
    # Eliminar tabla movimientos (antes por la FK)
    op.drop_table('expedientes_movimientos')
    
    # Eliminar índices de expedientes
    op.drop_index('ix_expedientes_cliente', table_name='expedientes')
    op.drop_index('ix_expedientes_socio_responsable', table_name='expedientes')
    op.drop_index('ix_expedientes_iue_anio', table_name='expedientes')
    
    # Eliminar tabla expedientes
    op.drop_table('expedientes')
