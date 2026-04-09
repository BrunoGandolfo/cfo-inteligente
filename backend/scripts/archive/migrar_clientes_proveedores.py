"""
Migrar clientes y proveedores desde operaciones (texto libre) a tablas normalizadas.

Lee operaciones.cliente y operaciones.proveedor, crea registros en las tablas
clientes/proveedores, y vincula cada operación con su cliente_id/proveedor_id.

Idempotente: si se ejecuta dos veces, no crea duplicados.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.operacion import Operacion
from app.models.cliente import Cliente
from app.models.proveedor import Proveedor


def migrar():
    db = SessionLocal()
    try:
        # ── 1. Clientes ──────────────────────────────────────────────
        # Nombres únicos en operaciones.cliente (case-insensitive)
        rows = (
            db.query(Operacion.cliente)
            .filter(
                Operacion.cliente.isnot(None),
                Operacion.cliente != "",
                Operacion.deleted_at.is_(None),
            )
            .distinct()
            .all()
        )
        nombres_cliente_raw = [r[0].strip() for r in rows if r[0] and r[0].strip()]

        # Agrupar por lowercase para detectar duplicados case-insensitive
        grupos_cliente = {}  # lower_name -> primer nombre original
        unificados_cliente = []
        for nombre in nombres_cliente_raw:
            key = nombre.lower()
            if key not in grupos_cliente:
                grupos_cliente[key] = nombre
            else:
                unificados_cliente.append((nombre, grupos_cliente[key]))

        # Crear clientes que no existan
        clientes_creados = 0
        for key, nombre_canonical in grupos_cliente.items():
            existe = (
                db.query(Cliente)
                .filter(func.lower(Cliente.nombre) == key)
                .first()
            )
            if not existe:
                db.add(Cliente(nombre=nombre_canonical, activo=True))
                clientes_creados += 1

        db.flush()

        # Mapa lower_name -> cliente_id
        todos_clientes = db.query(Cliente).all()
        mapa_cliente = {c.nombre.lower(): c.id for c in todos_clientes}

        # Vincular operaciones
        ops_vinculadas_cliente = 0
        operaciones_con_cliente = (
            db.query(Operacion)
            .filter(
                Operacion.cliente.isnot(None),
                Operacion.cliente != "",
                Operacion.deleted_at.is_(None),
            )
            .all()
        )
        for op in operaciones_con_cliente:
            cid = mapa_cliente.get(op.cliente.strip().lower())
            if cid and op.cliente_id != cid:
                op.cliente_id = cid
                ops_vinculadas_cliente += 1

        # ── 2. Proveedores ────────────────────────────────────────────
        rows = (
            db.query(Operacion.proveedor)
            .filter(
                Operacion.proveedor.isnot(None),
                Operacion.proveedor != "",
                Operacion.deleted_at.is_(None),
            )
            .distinct()
            .all()
        )
        nombres_prov_raw = [r[0].strip() for r in rows if r[0] and r[0].strip()]

        grupos_prov = {}
        unificados_prov = []
        for nombre in nombres_prov_raw:
            key = nombre.lower()
            if key not in grupos_prov:
                grupos_prov[key] = nombre
            else:
                unificados_prov.append((nombre, grupos_prov[key]))

        proveedores_creados = 0
        for key, nombre_canonical in grupos_prov.items():
            existe = (
                db.query(Proveedor)
                .filter(func.lower(Proveedor.nombre) == key)
                .first()
            )
            if not existe:
                db.add(Proveedor(nombre=nombre_canonical, activo=True))
                proveedores_creados += 1

        db.flush()

        todos_proveedores = db.query(Proveedor).all()
        mapa_prov = {p.nombre.lower(): p.id for p in todos_proveedores}

        ops_vinculadas_prov = 0
        operaciones_con_prov = (
            db.query(Operacion)
            .filter(
                Operacion.proveedor.isnot(None),
                Operacion.proveedor != "",
                Operacion.deleted_at.is_(None),
            )
            .all()
        )
        for op in operaciones_con_prov:
            pid = mapa_prov.get(op.proveedor.strip().lower())
            if pid and op.proveedor_id != pid:
                op.proveedor_id = pid
                ops_vinculadas_prov += 1

        # ── 3. Commit ────────────────────────────────────────────────
        db.commit()

        # ── 4. Reporte ───────────────────────────────────────────────
        print("=" * 55)
        print("  MIGRACIÓN CLIENTES / PROVEEDORES — REPORTE")
        print("=" * 55)
        print(f"  Clientes creados:              {clientes_creados}")
        print(f"  Proveedores creados:           {proveedores_creados}")
        print(f"  Operaciones → cliente_id:      {ops_vinculadas_cliente}")
        print(f"  Operaciones → proveedor_id:    {ops_vinculadas_prov}")

        if unificados_cliente:
            print(f"\n  Clientes unificados (case-insensitive):")
            for dup, canon in unificados_cliente:
                print(f"    '{dup}' → '{canon}'")

        if unificados_prov:
            print(f"\n  Proveedores unificados (case-insensitive):")
            for dup, canon in unificados_prov:
                print(f"    '{dup}' → '{canon}'")

        print("=" * 55)
        print("  OK — migración completada")
        print("=" * 55)

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrar()
