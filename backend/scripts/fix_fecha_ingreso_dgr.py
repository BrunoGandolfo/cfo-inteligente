"""Script para actualizar fecha_ingreso de trámites DGR existentes.

Re-consulta la DGR para cada trámite con fecha_ingreso = None
y parsea la fecha correctamente.

Uso:
    cd ~/cfo-inteligente/backend
    source .venv/bin/activate
    python scripts/fix_fecha_ingreso_dgr.py
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# Cargar .env
env_path = BACKEND_DIR / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

from sqlalchemy import text

from app.core.database import SessionLocal
from app.services.dgr_service import consultar_tramite_dgr, parsear_fecha_dgr

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def main():
    db = SessionLocal()
    try:
        rows = db.execute(
            text(
                "SELECT id, registro, oficina, anio, numero_entrada, bis "
                "FROM tramites_dgr "
                "WHERE fecha_ingreso IS NULL AND deleted_at IS NULL AND activo = true"
            )
        ).fetchall()

        logger.info("Trámites con fecha_ingreso NULL: %d", len(rows))

        if not rows:
            logger.info("Nada que actualizar")
            return

        actualizados = 0
        errores = 0

        for row in rows:
            tramite_id, registro, oficina, anio, numero, bis = row
            logger.info(
                "Consultando DGR: %s %s %d/%d (bis=%s)",
                registro, oficina, anio, numero, bis or "",
            )

            resultado = await consultar_tramite_dgr(
                registro=registro,
                oficina=oficina,
                anio=anio,
                numero=numero,
                bis=bis or "",
            )

            if not resultado:
                logger.warning("Sin resultado para trámite %s", tramite_id)
                errores += 1
                continue

            fecha = resultado.get("fecha_ingreso")
            if fecha is None:
                logger.warning("DGR no devolvió fecha_ingreso para %s", tramite_id)
                errores += 1
                continue

            # Si el parser ya devolvió un date, usarlo directo;
            # si por alguna razón es string, parsearlo
            if isinstance(fecha, str):
                fecha = parsear_fecha_dgr(fecha)

            if fecha is None:
                logger.warning("No se pudo parsear fecha para %s", tramite_id)
                errores += 1
                continue

            db.execute(
                text("UPDATE tramites_dgr SET fecha_ingreso = :fecha WHERE id = :id"),
                {"fecha": fecha, "id": tramite_id},
            )
            db.commit()
            actualizados += 1
            logger.info("Actualizado %s → fecha_ingreso = %s", tramite_id, fecha)

        logger.info(
            "Resultado: %d actualizados, %d errores de %d total",
            actualizados, errores, len(rows),
        )

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
