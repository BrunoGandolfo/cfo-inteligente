"""permitir area null en retiro y distribucion

Revision ID: e7f8a9b2c1d3
Revises: 540d4b593c06
Create Date: 2025-11-14 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e7f8a9b2c1d3'
down_revision: Union[str, None] = '540d4b593c06'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Permitir NULL en area_id para operaciones tipo RETIRO y DISTRIBUCION.
    
    Justificación:
    - RETIRO y DISTRIBUCION son movimientos financieros, no operaciones de áreas
    - Forzar "Gastos Generales" contamina análisis de rentabilidad
    - Filosofía DHH: NULL = no aplica, no inventar abstracciones innecesarias
    """
    # Permitir NULL en area_id
    op.alter_column('operaciones', 'area_id',
                   existing_type=postgresql.UUID(),
                   nullable=True)


def downgrade() -> None:
    """
    Revertir: volver a NOT NULL.
    
    ADVERTENCIA: Solo funciona si todos los registros tienen area_id no nulo.
    Si hay NULLs, primero hay que asignar áreas antes de ejecutar downgrade.
    """
    # Volver a NOT NULL (fallará si hay registros con area_id NULL)
    op.alter_column('operaciones', 'area_id',
                   existing_type=postgresql.UUID(),
                   nullable=False)

