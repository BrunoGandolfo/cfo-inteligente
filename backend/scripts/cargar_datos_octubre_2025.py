#!/usr/bin/env python3
"""
Script para copiar datos existentes a octubre 2025
para poder probar el CFO AI con datos actuales
"""
from sqlalchemy import create_engine, text
from datetime import datetime
import sys

def cargar_datos_octubre():
    """Copia datos de un mes histórico a octubre 2025"""
    
    engine = create_engine('postgresql://cfo_user:cfo_pass@localhost/cfo_inteligente')
    
    print("\n" + "=" * 80)
    print(" 📅 CARGANDO DATOS EN OCTUBRE 2025 ".center(80))
    print("=" * 80 + "\n")
    
    try:
        with engine.connect() as conn:
            # 1. Identificar el mes con más datos
            result = conn.execute(text("""
                SELECT 
                    DATE_TRUNC('month', fecha) as mes,
                    COUNT(*) as cantidad
                FROM operaciones 
                WHERE deleted_at IS NULL
                GROUP BY 1
                ORDER BY 2 DESC
                LIMIT 1
            """))
            
            row = result.fetchone()
            mes_origen = row[0]
            cantidad_origen = row[1]
            
            print(f"📊 Mes con más datos: {mes_origen.strftime('%Y-%m')}")
            print(f"   Operaciones: {cantidad_origen}")
            print()
            
            # 2. Verificar si ya hay datos en octubre 2025
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM operaciones 
                WHERE deleted_at IS NULL
                  AND DATE_TRUNC('month', fecha) = DATE_TRUNC('month', '2025-10-01'::date)
            """))
            
            existentes = result.fetchone()[0]
            
            if existentes > 0:
                print(f"⚠️  Ya hay {existentes} operaciones en octubre 2025")
                respuesta = input("¿Desea eliminarlas y recargar? (s/n): ").strip().lower()
                if respuesta != 's':
                    print("Cancelado.")
                    return
                
                # Eliminar existentes
                conn.execute(text("""
                    DELETE FROM distribuciones_detalle 
                    WHERE operacion_id IN (
                        SELECT id FROM operaciones 
                        WHERE DATE_TRUNC('month', fecha) = DATE_TRUNC('month', '2025-10-01'::date)
                    )
                """))
                conn.execute(text("""
                    DELETE FROM operaciones 
                    WHERE DATE_TRUNC('month', fecha) = DATE_TRUNC('month', '2025-10-01'::date)
                """))
                conn.commit()
                print("✅ Datos anteriores eliminados")
            
            print("\n🔄 Copiando operaciones...")
            
            # 3. Copiar operaciones a octubre 2025
            result = conn.execute(text("""
                INSERT INTO operaciones (
                    id, tipo_operacion, fecha, monto_original, 
                    moneda_original, tipo_cambio, monto_usd, monto_uyu,
                    area_id, localidad, descripcion, cliente, proveedor,
                    created_at, updated_at
                )
                SELECT 
                    gen_random_uuid(),
                    tipo_operacion,
                    ('2025-10-' || EXTRACT(DAY FROM fecha)::text)::date,
                    monto_original,
                    moneda_original,
                    tipo_cambio,
                    monto_usd,
                    monto_uyu,
                    area_id,
                    localidad,
                    COALESCE(descripcion, '') || ' (Oct 2025)',
                    cliente,
                    proveedor,
                    NOW(),
                    NOW()
                FROM operaciones
                WHERE deleted_at IS NULL
                  AND DATE_TRUNC('month', fecha) = :mes_origen
            """), {"mes_origen": mes_origen})
            
            operaciones_copiadas = result.rowcount
            print(f"✅ {operaciones_copiadas} operaciones copiadas")
            
            conn.commit()
            
            # 4. Copiar distribuciones si las hay
            print("\n🔄 Copiando distribuciones...")
            
            result = conn.execute(text("""
                WITH operaciones_octubre AS (
                    SELECT id, descripcion
                    FROM operaciones
                    WHERE DATE_TRUNC('month', fecha) = DATE_TRUNC('month', '2025-10-01'::date)
                      AND deleted_at IS NULL
                ), operaciones_origen AS (
                    SELECT id, descripcion
                    FROM operaciones
                    WHERE DATE_TRUNC('month', fecha) = :mes_origen
                      AND deleted_at IS NULL
                )
                INSERT INTO distribuciones_detalle (
                    id, operacion_id, socio_id, monto_uyu, monto_usd, porcentaje
                )
                SELECT 
                    gen_random_uuid(),
                    oo.id,
                    dd.socio_id,
                    dd.monto_uyu,
                    dd.monto_usd,
                    dd.porcentaje
                FROM distribuciones_detalle dd
                JOIN operaciones_origen oo_orig ON oo_orig.id = dd.operacion_id
                JOIN operaciones_octubre oo ON oo.descripcion = oo_orig.descripcion
                RETURNING id
            """), {"mes_origen": mes_origen})
            
            distribuciones_copiadas = result.rowcount
            print(f"✅ {distribuciones_copiadas} distribuciones copiadas")
            
            conn.commit()
            
            # 5. Verificar resultados
            print("\n" + "=" * 80)
            print(" 📊 VERIFICACIÓN DE DATOS EN OCTUBRE 2025 ".center(80))
            print("=" * 80 + "\n")
            
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END) as ingresos,
                    SUM(CASE WHEN tipo_operacion='GASTO' THEN monto_uyu ELSE 0 END) as gastos,
                    SUM(CASE WHEN tipo_operacion='RETIRO' THEN monto_uyu ELSE 0 END) as retiros,
                    SUM(CASE WHEN tipo_operacion='DISTRIBUCION' THEN monto_uyu ELSE 0 END) as distribuciones
                FROM operaciones
                WHERE deleted_at IS NULL
                  AND DATE_TRUNC('month', fecha) = DATE_TRUNC('month', '2025-10-01'::date)
            """))
            
            datos = result.fetchone()
            total, ingresos, gastos, retiros, distribuciones = datos
            
            if ingresos and gastos:
                rentabilidad = ((ingresos - gastos) / ingresos * 100) if ingresos > 0 else 0
            else:
                rentabilidad = 0
            
            print(f"Total de operaciones: {total}")
            print(f"Ingresos:             $ {ingresos:,.2f}")
            print(f"Gastos:               $ {gastos:,.2f}")
            print(f"Retiros:              $ {retiros:,.2f}")
            print(f"Distribuciones:       $ {distribuciones:,.2f}")
            print(f"Rentabilidad:         {rentabilidad:.2f}%")
            
            # Verificar por localidad
            print("\n📍 Por localidad:")
            result = conn.execute(text("""
                SELECT 
                    localidad,
                    SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END) as ingresos
                FROM operaciones
                WHERE deleted_at IS NULL
                  AND DATE_TRUNC('month', fecha) = DATE_TRUNC('month', '2025-10-01'::date)
                GROUP BY localidad
                ORDER BY ingresos DESC
            """))
            
            for row in result:
                print(f"   {row[0]:<15} $ {row[1]:,.2f}")
            
            # Verificar distribuciones por socio
            print("\n👥 Distribuciones por socio:")
            result = conn.execute(text("""
                SELECT 
                    s.nombre,
                    COALESCE(SUM(dd.monto_uyu), 0) as total
                FROM socios s
                LEFT JOIN distribuciones_detalle dd ON dd.socio_id = s.id
                LEFT JOIN operaciones o ON o.id = dd.operacion_id 
                    AND o.deleted_at IS NULL 
                    AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', '2025-10-01'::date)
                GROUP BY s.nombre
                ORDER BY total DESC
            """))
            
            for row in result:
                if row[1] > 0:
                    print(f"   {row[0]:<15} $ {row[1]:,.2f}")
            
            print("\n" + "=" * 80)
            print(" ✅ DATOS CARGADOS EXITOSAMENTE ".center(80))
            print("=" * 80)
            print()
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    cargar_datos_octubre()

