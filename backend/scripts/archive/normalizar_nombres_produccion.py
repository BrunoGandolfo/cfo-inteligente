"""
Normalizar nombres de clientes y proveedores en producción.

Operaciones:
  1. Unificación de duplicados (reasigna operaciones al registro correcto)
  2. Renombramientos
  3. Eliminaciones (solo si no tienen operaciones vinculadas)
  4. Creación de nuevos proveedores
  5. Conversión masiva a MAYÚSCULA de todos los nombres restantes

Seguridad:
  - Todo en una sola transacción (rollback completo si falla)
  - Idempotente: puede ejecutarse varias veces sin crear duplicados
  - Usa func.lower() para búsquedas case-insensitive
  - No elimina registros con operaciones vinculadas

Uso:
  DATABASE_URL=postgresql://... python backend/scripts/normalizar_nombres_produccion.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timezone
from sqlalchemy import func, text
from app.core.database import SessionLocal
from app.models.operacion import Operacion
from app.models.cliente import Cliente
from app.models.proveedor import Proveedor

# ═══════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE CAMBIOS
# ═══════════════════════════════════════════════════════════════════

CLIENTES_UNIFICAR = [
    # (nombres_a_eliminar, nombre_correcto_en_mayuscula)
    (["banhnof"], "BAHNHOF"),
    (["borio automóviles"], "BORIO AUTOMÓVILES"),
    (["club cannabico estarse", "club cannabis"], "CLUB CANNABICO"),
    (["MERCURIUS CESIÓN CREDITOS PAIGO"], "MERCURIUS FIDEICOMISO"),
    (["CREDIFAMA PERÚ"], "CREDIFAMA"),
    (["Burgos"], "JUAN BURGOS"),
    (["HIPOTECA J. BURIANI"], "JOAQUIN BURIANI"),
]

CLIENTES_RENOMBRAR = [
    # (nombre_actual, nombre_nuevo_en_mayuscula)
    ("gaston Rosas", "GASTÓN ROSAS"),
    ("edificio grito de Asencio", "EDIFICIO GRITO DE ASENCIO"),
    ("G. MORGAN", "GRUPO MORGAN"),
    ("Federico", "FEDERICO MENEGHETTI"),
]

CLIENTES_ELIMINAR = ["Messi"]

PROVEEDORES_UNIFICAR = [
    (["BPS FONASAS"], "BPS"),
    (["CAJA PROF GERARDO SALDO"], "CAJA PROFESIONAL GERARDO"),
    (["OFFICE"], "OFFICE 2000"),
    (["R. MEDEROS"], "RODRIGO MEDEROS"),
]

PROVEEDORES_RENOMBRAR = [
    ("edificio Grito de Asencio", "EDIFICIO GRITO DE ASENCIO"),
]

PROVEEDORES_ELIMINAR = ["Limpieza oficina", "UTE  ANTEL"]

PROVEEDORES_CREAR = ["UTE", "ANTEL"]


# ═══════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ═══════════════════════════════════════════════════════════════════

def buscar_registro(db, modelo, nombre):
    """Busca registro por nombre case-insensitive."""
    return (
        db.query(modelo)
        .filter(func.lower(modelo.nombre) == nombre.lower())
        .first()
    )


def contar_operaciones_por_id(db, campo_id, registro_id):
    """Cuenta operaciones activas vinculadas por FK."""
    return (
        db.query(Operacion)
        .filter(
            campo_id == registro_id,
            Operacion.deleted_at.is_(None),
        )
        .count()
    )


def contar_operaciones_por_string(db, campo_str, nombre):
    """Cuenta operaciones activas vinculadas por string case-insensitive."""
    return (
        db.query(Operacion)
        .filter(
            func.lower(campo_str) == nombre.lower(),
            Operacion.deleted_at.is_(None),
        )
        .count()
    )


def reasignar_operaciones_id(db, campo_id, viejo_id, nuevo_id):
    """Reasigna operaciones de un FK a otro. Devuelve cantidad."""
    ops = (
        db.query(Operacion)
        .filter(campo_id == viejo_id, Operacion.deleted_at.is_(None))
        .all()
    )
    for op in ops:
        if campo_id == Operacion.cliente_id:
            op.cliente_id = nuevo_id
        else:
            op.proveedor_id = nuevo_id
        op.updated_at = datetime.now(timezone.utc)
    return len(ops)


def actualizar_operaciones_string(db, campo_str, nombre_viejo, nombre_nuevo):
    """Actualiza la columna string de operaciones. Devuelve cantidad."""
    ops = (
        db.query(Operacion)
        .filter(
            func.lower(campo_str) == nombre_viejo.lower(),
            Operacion.deleted_at.is_(None),
        )
        .all()
    )
    for op in ops:
        if campo_str == Operacion.cliente:
            op.cliente = nombre_nuevo
        else:
            op.proveedor = nombre_nuevo
        op.updated_at = datetime.now(timezone.utc)
    return len(ops)


# ═══════════════════════════════════════════════════════════════════
# LÓGICA PRINCIPAL
# ═══════════════════════════════════════════════════════════════════

def normalizar():
    db = SessionLocal()
    reporte = []
    errores = []

    def log(msg):
        reporte.append(msg)
        print(f"  {msg}")

    try:
        print("=" * 65)
        print("  NORMALIZACIÓN DE CLIENTES Y PROVEEDORES — PRODUCCIÓN")
        print("=" * 65)

        # ─────────────────────────────────────────────────────────
        # FASE 1: UNIFICAR CLIENTES
        # ─────────────────────────────────────────────────────────
        print("\n── FASE 1: Unificar clientes ──")

        for nombres_eliminar, nombre_correcto in CLIENTES_UNIFICAR:
            # Buscar o crear el registro destino
            destino = buscar_registro(db, Cliente, nombre_correcto)

            if not destino:
                # Intentar renombrar uno de los duplicados
                for ne in nombres_eliminar:
                    candidato = buscar_registro(db, Cliente, ne)
                    if candidato:
                        viejo_nombre = candidato.nombre
                        candidato.nombre = nombre_correcto
                        candidato.updated_at = datetime.now(timezone.utc)
                        destino = candidato
                        log(f"RENOMBRADO cliente '{viejo_nombre}' → '{nombre_correcto}'")
                        nombres_eliminar = [n for n in nombres_eliminar if n.lower() != ne.lower()]
                        break

            if not destino:
                log(f"⚠ No se encontró ningún registro para '{nombre_correcto}' ni para {nombres_eliminar} — omitido")
                continue

            # Si el destino tiene nombre distinto (ya existía pero no en MAYÚSCULA)
            if destino.nombre != nombre_correcto:
                viejo = destino.nombre
                destino.nombre = nombre_correcto
                destino.updated_at = datetime.now(timezone.utc)
                log(f"RENOMBRADO cliente '{viejo}' → '{nombre_correcto}'")

            db.flush()

            # Reasignar operaciones de cada duplicado al destino
            for nombre_dup in nombres_eliminar:
                dup = buscar_registro(db, Cliente, nombre_dup)
                if not dup:
                    continue
                if dup.id == destino.id:
                    continue

                n_id = reasignar_operaciones_id(db, Operacion.cliente_id, dup.id, destino.id)
                n_str = actualizar_operaciones_string(db, Operacion.cliente, nombre_dup, nombre_correcto)
                log(f"UNIFICADO cliente '{dup.nombre}' → '{nombre_correcto}' ({n_id} ops por FK, {n_str} ops por string)")

                # Eliminar duplicado
                db.delete(dup)
                log(f"ELIMINADO cliente duplicado '{nombre_dup}' (id={dup.id})")

            # Actualizar strings restantes que matchean los duplicados ya procesados
            actualizar_operaciones_string(db, Operacion.cliente, nombre_correcto, nombre_correcto)
            db.flush()

        # ─────────────────────────────────────────────────────────
        # FASE 2: RENOMBRAR CLIENTES
        # ─────────────────────────────────────────────────────────
        print("\n── FASE 2: Renombrar clientes ──")

        for nombre_actual, nombre_nuevo in CLIENTES_RENOMBRAR:
            reg = buscar_registro(db, Cliente, nombre_actual)
            if not reg:
                # Ya podría estar renombrado (idempotencia)
                ya_existe = buscar_registro(db, Cliente, nombre_nuevo)
                if ya_existe:
                    log(f"OK (ya existe) '{nombre_nuevo}'")
                else:
                    log(f"⚠ No encontrado cliente '{nombre_actual}' — omitido")
                continue

            viejo = reg.nombre
            reg.nombre = nombre_nuevo
            reg.updated_at = datetime.now(timezone.utc)
            n_str = actualizar_operaciones_string(db, Operacion.cliente, nombre_actual, nombre_nuevo)
            log(f"RENOMBRADO cliente '{viejo}' → '{nombre_nuevo}' ({n_str} ops string actualizadas)")
            db.flush()

        # ─────────────────────────────────────────────────────────
        # FASE 3: ELIMINAR CLIENTES
        # ─────────────────────────────────────────────────────────
        print("\n── FASE 3: Eliminar clientes ──")

        for nombre in CLIENTES_ELIMINAR:
            reg = buscar_registro(db, Cliente, nombre)
            if not reg:
                log(f"OK (no existe) cliente '{nombre}'")
                continue

            n_ops_fk = contar_operaciones_por_id(db, Operacion.cliente_id, reg.id)
            n_ops_str = contar_operaciones_por_string(db, Operacion.cliente, nombre)

            if n_ops_fk > 0 or n_ops_str > 0:
                msg = f"ERROR: No se puede eliminar cliente '{nombre}' — tiene {n_ops_fk} ops por FK y {n_ops_str} ops por string"
                errores.append(msg)
                log(msg)
                continue

            db.delete(reg)
            log(f"ELIMINADO cliente '{nombre}' (id={reg.id})")
            db.flush()

        # ─────────────────────────────────────────────────────────
        # FASE 4: UNIFICAR PROVEEDORES
        # ─────────────────────────────────────────────────────────
        print("\n── FASE 4: Unificar proveedores ──")

        for nombres_eliminar, nombre_correcto in PROVEEDORES_UNIFICAR:
            destino = buscar_registro(db, Proveedor, nombre_correcto)

            if not destino:
                for ne in nombres_eliminar:
                    candidato = buscar_registro(db, Proveedor, ne)
                    if candidato:
                        viejo_nombre = candidato.nombre
                        candidato.nombre = nombre_correcto
                        candidato.updated_at = datetime.now(timezone.utc)
                        destino = candidato
                        log(f"RENOMBRADO proveedor '{viejo_nombre}' → '{nombre_correcto}'")
                        nombres_eliminar = [n for n in nombres_eliminar if n.lower() != ne.lower()]
                        break

            if not destino:
                log(f"⚠ No se encontró ningún registro para '{nombre_correcto}' ni para {nombres_eliminar} — omitido")
                continue

            if destino.nombre != nombre_correcto:
                viejo = destino.nombre
                destino.nombre = nombre_correcto
                destino.updated_at = datetime.now(timezone.utc)
                log(f"RENOMBRADO proveedor '{viejo}' → '{nombre_correcto}'")

            db.flush()

            for nombre_dup in nombres_eliminar:
                dup = buscar_registro(db, Proveedor, nombre_dup)
                if not dup:
                    continue
                if dup.id == destino.id:
                    continue

                n_id = reasignar_operaciones_id(db, Operacion.proveedor_id, dup.id, destino.id)
                n_str = actualizar_operaciones_string(db, Operacion.proveedor, nombre_dup, nombre_correcto)
                log(f"UNIFICADO proveedor '{dup.nombre}' → '{nombre_correcto}' ({n_id} ops por FK, {n_str} ops por string)")

                db.delete(dup)
                log(f"ELIMINADO proveedor duplicado '{nombre_dup}' (id={dup.id})")

            actualizar_operaciones_string(db, Operacion.proveedor, nombre_correcto, nombre_correcto)
            db.flush()

        # ─────────────────────────────────────────────────────────
        # FASE 5: RENOMBRAR PROVEEDORES
        # ─────────────────────────────────────────────────────────
        print("\n── FASE 5: Renombrar proveedores ──")

        for nombre_actual, nombre_nuevo in PROVEEDORES_RENOMBRAR:
            reg = buscar_registro(db, Proveedor, nombre_actual)
            if not reg:
                ya_existe = buscar_registro(db, Proveedor, nombre_nuevo)
                if ya_existe:
                    log(f"OK (ya existe) '{nombre_nuevo}'")
                else:
                    log(f"⚠ No encontrado proveedor '{nombre_actual}' — omitido")
                continue

            viejo = reg.nombre
            reg.nombre = nombre_nuevo
            reg.updated_at = datetime.now(timezone.utc)
            n_str = actualizar_operaciones_string(db, Operacion.proveedor, nombre_actual, nombre_nuevo)
            log(f"RENOMBRADO proveedor '{viejo}' → '{nombre_nuevo}' ({n_str} ops string actualizadas)")
            db.flush()

        # ─────────────────────────────────────────────────────────
        # FASE 6: ELIMINAR PROVEEDORES
        # ─────────────────────────────────────────────────────────
        print("\n── FASE 6: Eliminar proveedores ──")

        for nombre in PROVEEDORES_ELIMINAR:
            reg = buscar_registro(db, Proveedor, nombre)
            if not reg:
                log(f"OK (no existe) proveedor '{nombre}'")
                continue

            n_ops_fk = contar_operaciones_por_id(db, Operacion.proveedor_id, reg.id)
            n_ops_str = contar_operaciones_por_string(db, Operacion.proveedor, nombre)

            if n_ops_fk > 0 or n_ops_str > 0:
                msg = f"ERROR: No se puede eliminar proveedor '{nombre}' — tiene {n_ops_fk} ops por FK y {n_ops_str} ops por string"
                errores.append(msg)
                log(msg)
                continue

            db.delete(reg)
            log(f"ELIMINADO proveedor '{nombre}' (id={reg.id})")
            db.flush()

        # ─────────────────────────────────────────────────────────
        # FASE 7: CREAR PROVEEDORES NUEVOS
        # ─────────────────────────────────────────────────────────
        print("\n── FASE 7: Crear proveedores nuevos ──")

        for nombre in PROVEEDORES_CREAR:
            ya_existe = buscar_registro(db, Proveedor, nombre)
            if ya_existe:
                log(f"OK (ya existe) proveedor '{nombre}'")
                continue
            db.add(Proveedor(nombre=nombre.upper(), activo=True))
            log(f"CREADO proveedor '{nombre.upper()}'")
            db.flush()

        # ─────────────────────────────────────────────────────────
        # FASE 8: MAYÚSCULAS MASIVAS
        # ─────────────────────────────────────────────────────────
        print("\n── FASE 8: Convertir todos los nombres a MAYÚSCULA ──")

        n_clientes = db.execute(text(
            "UPDATE clientes SET nombre = UPPER(nombre), updated_at = NOW() "
            "WHERE nombre != UPPER(nombre)"
        )).rowcount

        n_proveedores = db.execute(text(
            "UPDATE proveedores SET nombre = UPPER(nombre), updated_at = NOW() "
            "WHERE nombre != UPPER(nombre)"
        )).rowcount

        n_ops_cli = db.execute(text(
            "UPDATE operaciones SET cliente = UPPER(cliente), updated_at = NOW() "
            "WHERE cliente IS NOT NULL AND cliente != UPPER(cliente)"
        )).rowcount

        n_ops_prov = db.execute(text(
            "UPDATE operaciones SET proveedor = UPPER(proveedor), updated_at = NOW() "
            "WHERE proveedor IS NOT NULL AND proveedor != UPPER(proveedor)"
        )).rowcount

        log(f"MAYÚSCULAS: {n_clientes} clientes, {n_proveedores} proveedores, "
            f"{n_ops_cli} ops.cliente, {n_ops_prov} ops.proveedor")

        # ─────────────────────────────────────────────────────────
        # COMMIT
        # ─────────────────────────────────────────────────────────
        if errores:
            print(f"\n⚠ HAY {len(errores)} ERROR(ES) — el script continuó con el resto")
            for e in errores:
                print(f"  → {e}")

        db.commit()

        # ─────────────────────────────────────────────────────────
        # REPORTE FINAL
        # ─────────────────────────────────────────────────────────
        print("\n" + "=" * 65)
        print("  NORMALIZACIÓN COMPLETADA — COMMIT OK")
        print("=" * 65)
        print(f"\n  Total acciones: {len(reporte)}")
        print(f"  Errores: {len(errores)}")
        print("\n  Verificar con:")
        print('  psql "$DATABASE_URL" -c "SELECT nombre FROM clientes WHERE activo = true ORDER BY nombre;"')
        print('  psql "$DATABASE_URL" -c "SELECT nombre FROM proveedores WHERE activo = true ORDER BY nombre;"')
        print("=" * 65)

    except Exception as e:
        db.rollback()
        print(f"\n{'=' * 65}")
        print(f"  ROLLBACK — ERROR FATAL: {e}")
        print(f"{'=' * 65}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    normalizar()
