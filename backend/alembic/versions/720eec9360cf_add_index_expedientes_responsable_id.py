"""add_index_expedientes_responsable_id

Revision ID: 720eec9360cf
Revises: 3af6f419c712
Create Date: 2026-04-09 17:04:06.412355

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '720eec9360cf'
down_revision: Union[str, None] = '3af6f419c712'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    columns = {column["name"] for column in inspector.get_columns("expedientes")}
    indexes = {index["name"] for index in inspector.get_indexes("expedientes")}
    foreign_keys = {
        fk["name"]: fk
        for fk in inspector.get_foreign_keys("expedientes")
        if fk.get("name")
    }

    if "socio_responsable_id" in columns and "responsable_id" not in columns:
        if "ix_expedientes_socio_responsable" in indexes:
            op.drop_index("ix_expedientes_socio_responsable", table_name="expedientes")

        old_fk = foreign_keys.get("expedientes_socio_responsable_id_fkey")
        if old_fk:
            op.drop_constraint("expedientes_socio_responsable_id_fkey", "expedientes", type_="foreignkey")

        op.alter_column("expedientes", "socio_responsable_id", new_column_name="responsable_id")

        inspector = inspect(bind)
        columns = {column["name"] for column in inspector.get_columns("expedientes")}
        indexes = {index["name"] for index in inspector.get_indexes("expedientes")}
        foreign_keys = {
            fk["name"]: fk
            for fk in inspector.get_foreign_keys("expedientes")
            if fk.get("name")
        }

    fk_responsable = foreign_keys.get("expedientes_responsable_id_fkey")
    if "responsable_id" in columns and (
        not fk_responsable or fk_responsable.get("referred_table") != "usuarios"
    ):
        if fk_responsable:
            op.drop_constraint("expedientes_responsable_id_fkey", "expedientes", type_="foreignkey")
        op.create_foreign_key(
            "expedientes_responsable_id_fkey",
            "expedientes",
            "usuarios",
            ["responsable_id"],
            ["id"],
        )

    if "responsable_id" in columns and "ix_expedientes_responsable_id" not in indexes:
        op.create_index(
            "ix_expedientes_responsable_id",
            "expedientes",
            ["responsable_id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    columns = {column["name"] for column in inspector.get_columns("expedientes")}
    indexes = {index["name"] for index in inspector.get_indexes("expedientes")}
    foreign_keys = {
        fk["name"]: fk
        for fk in inspector.get_foreign_keys("expedientes")
        if fk.get("name")
    }

    if "ix_expedientes_responsable_id" in indexes:
        op.drop_index("ix_expedientes_responsable_id", table_name="expedientes")

    fk_responsable = foreign_keys.get("expedientes_responsable_id_fkey")
    if fk_responsable and "responsable_id" in columns:
        op.drop_constraint("expedientes_responsable_id_fkey", "expedientes", type_="foreignkey")

    if "responsable_id" in columns and "socio_responsable_id" not in columns:
        op.alter_column("expedientes", "responsable_id", new_column_name="socio_responsable_id")

        inspector = inspect(bind)
        columns = {column["name"] for column in inspector.get_columns("expedientes")}
        indexes = {index["name"] for index in inspector.get_indexes("expedientes")}
        foreign_keys = {
            fk["name"]: fk
            for fk in inspector.get_foreign_keys("expedientes")
            if fk.get("name")
        }

    fk_socio = foreign_keys.get("expedientes_socio_responsable_id_fkey")
    if "socio_responsable_id" in columns and (
        not fk_socio or fk_socio.get("referred_table") != "socios"
    ):
        if fk_socio:
            op.drop_constraint("expedientes_socio_responsable_id_fkey", "expedientes", type_="foreignkey")
        op.create_foreign_key(
            "expedientes_socio_responsable_id_fkey",
            "expedientes",
            "socios",
            ["socio_responsable_id"],
            ["id"],
        )

    if "socio_responsable_id" in columns and "ix_expedientes_socio_responsable" not in indexes:
        op.create_index(
            "ix_expedientes_socio_responsable",
            "expedientes",
            ["socio_responsable_id"],
        )
