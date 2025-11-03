"""agregar_sistema_conversaciones

Revision ID: 540d4b593c06
Revises: d41b8703364f
Create Date: 2025-11-03 10:15:30.423769

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '540d4b593c06'
down_revision: Union[str, None] = 'd41b8703364f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tabla de conversaciones
    op.create_table('conversaciones',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('usuario_id', UUID(as_uuid=True), nullable=False),
        sa.Column('titulo', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_conversaciones_usuario', 'conversaciones', ['usuario_id'])
    op.create_index('idx_conversaciones_updated', 'conversaciones', ['updated_at'])
    
    # Tabla de mensajes
    op.create_table('mensajes',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('conversacion_id', UUID(as_uuid=True), nullable=False),
        sa.Column('rol', sa.String(20), nullable=False),
        sa.Column('contenido', sa.Text(), nullable=False),
        sa.Column('sql_generado', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['conversacion_id'], ['conversaciones.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_mensajes_conversacion', 'mensajes', ['conversacion_id'])
    op.create_index('idx_mensajes_created', 'mensajes', ['created_at'])


def downgrade() -> None:
    op.drop_index('idx_mensajes_created', table_name='mensajes')
    op.drop_index('idx_mensajes_conversacion', table_name='mensajes')
    op.drop_table('mensajes')
    op.drop_index('idx_conversaciones_updated', table_name='conversaciones')
    op.drop_index('idx_conversaciones_usuario', table_name='conversaciones')
    op.drop_table('conversaciones')
