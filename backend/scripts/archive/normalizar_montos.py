#!/usr/bin/env python3
"""
Script de normalización de montos inflados en operaciones

Divide por 100 los montos de INGRESO, GASTO y DISTRIBUCION
que fueron inflados por un bug en el sistema.

RETIROS no se normalizan porque ya están correctos.
"""

import sys
import psycopg2
from psycopg2 import sql
from decimal import Decimal

# Configuración de base de datos
DB_CONFIG = {
    'host': 'localhost',
    'dbname': 'cfo_inteligente',
    'user': 'cfo_user',
    'password': 'cfo_pass',
    'port': 5432
}

def mostrar_metricas(cursor, titulo="MÉTRICAS"):
    """Muestra métricas de montos por tipo de operación en UYU y USD"""
    print("\n" + "=" * 120)
    print(f"{titulo:^120}")
    print("=" * 120)
    
    # Métricas por tipo_operacion en tabla operaciones
    query_operaciones = """
    SELECT 
        tipo_operacion,
        COUNT(*) as cantidad,
        ROUND(AVG(monto_uyu), 2) as promedio_uyu,
        ROUND(MIN(monto_uyu), 2) as minimo_uyu,
        ROUND(MAX(monto_uyu), 2) as maximo_uyu,
        ROUND(AVG(monto_usd), 2) as promedio_usd,
        ROUND(MIN(monto_usd), 2) as minimo_usd,
        ROUND(MAX(monto_usd), 2) as maximo_usd
    FROM operaciones
    WHERE deleted_at IS NULL
    GROUP BY tipo_operacion
    ORDER BY tipo_operacion;
    """
    
    cursor.execute(query_operaciones)
    resultados = cursor.fetchall()
    
    print("\nTABLA: operaciones")
    print("-" * 120)
    print(f"{'Tipo':<15} {'Cant':>6} {'Prom UYU':>14} {'Min UYU':>14} {'Max UYU':>14} {'Prom USD':>14} {'Min USD':>14} {'Max USD':>14}")
    print("-" * 120)
    
    for row in resultados:
        tipo, cant, prom_uyu, min_uyu, max_uyu, prom_usd, min_usd, max_usd = row
        print(f"{tipo:<15} {cant:>6} {prom_uyu:>14,.2f} {min_uyu:>14,.2f} {max_uyu:>14,.2f} {prom_usd:>14,.2f} {min_usd:>14,.2f} {max_usd:>14,.2f}")
    
    print("-" * 120)
    
    # Métricas de distribuciones_detalle
    query_distribuciones = """
    SELECT 
        COUNT(*) as cantidad,
        ROUND(AVG(monto_uyu), 2) as promedio_uyu,
        ROUND(MIN(monto_uyu), 2) as minimo_uyu,
        ROUND(MAX(monto_uyu), 2) as maximo_uyu,
        ROUND(AVG(monto_usd), 2) as promedio_usd,
        ROUND(MIN(monto_usd), 2) as minimo_usd,
        ROUND(MAX(monto_usd), 2) as maximo_usd
    FROM distribuciones_detalle;
    """
    
    cursor.execute(query_distribuciones)
    row = cursor.fetchone()
    
    print("\nTABLA: distribuciones_detalle")
    print("-" * 120)
    print(f"{'Cantidad':<6} {'Prom UYU':>14} {'Min UYU':>14} {'Max UYU':>14} {'Prom USD':>14} {'Min USD':>14} {'Max USD':>14}")
    print("-" * 120)
    
    if row and row[0] > 0:
        cant, prom_uyu, min_uyu, max_uyu, prom_usd, min_usd, max_usd = row
        print(f"{cant:<6} {prom_uyu:>14,.2f} {min_uyu:>14,.2f} {max_uyu:>14,.2f} {prom_usd:>14,.2f} {min_usd:>14,.2f} {max_usd:>14,.2f}")
    else:
        print("(Sin datos)")
    
    print("=" * 120 + "\n")


def normalizar_montos():
    """Ejecuta la normalización de montos con transacción"""
    
    conn = None
    cursor = None
    
    try:
        # Conectar a la base de datos
        print("Conectando a PostgreSQL...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("✓ Conexión establecida\n")
        
        # Mostrar métricas ANTES
        mostrar_metricas(cursor, "MÉTRICAS ANTES DE NORMALIZACIÓN")
        
        # Iniciar transacción explícita
        print("Iniciando transacción...")
        
        # Query 1: Normalizar operaciones (INGRESO, GASTO, DISTRIBUCION)
        query_operaciones = """
        UPDATE operaciones 
        SET monto_original = monto_original / 100,
            monto_uyu = monto_uyu / 100,
            monto_usd = monto_usd / 100
        WHERE tipo_operacion IN ('INGRESO', 'GASTO', 'DISTRIBUCION')
          AND deleted_at IS NULL;
        """
        
        print("\nEjecutando normalización en tabla 'operaciones'...")
        cursor.execute(query_operaciones)
        rows_operaciones = cursor.rowcount
        print(f"✓ {rows_operaciones} operaciones normalizadas (INGRESO, GASTO, DISTRIBUCION)")
        
        # Query 2: Normalizar distribuciones_detalle
        query_distribuciones = """
        UPDATE distribuciones_detalle
        SET monto_uyu = monto_uyu / 100,
            monto_usd = monto_usd / 100;
        """
        
        print("\nEjecutando normalización en tabla 'distribuciones_detalle'...")
        cursor.execute(query_distribuciones)
        rows_distribuciones = cursor.rowcount
        print(f"✓ {rows_distribuciones} detalles de distribución normalizados")
        
        # Mostrar métricas DESPUÉS
        mostrar_metricas(cursor, "MÉTRICAS DESPUÉS DE NORMALIZACIÓN")
        
        # Confirmación del usuario
        print("\n" + "!" * 80)
        print("ATENCIÓN: Los cambios están pendientes de confirmación")
        print("!" * 80)
        print("\nResumen de cambios:")
        print(f"  • Operaciones normalizadas: {rows_operaciones}")
        print(f"  • Distribuciones normalizadas: {rows_distribuciones}")
        print(f"  • Tipos afectados: INGRESO, GASTO, DISTRIBUCION")
        print(f"  • Tipos NO afectados: RETIRO (ya están correctos)")
        print("\n¿Desea aplicar estos cambios de forma permanente?")
        
        respuesta = input("Escriba 's' para COMMIT o 'n' para ROLLBACK: ").strip().lower()
        
        if respuesta == 's':
            conn.commit()
            print("\n" + "=" * 80)
            print("✓ COMMIT EXITOSO - Cambios aplicados permanentemente")
            print("=" * 80)
            return True
        else:
            conn.rollback()
            print("\n" + "=" * 80)
            print("✗ ROLLBACK - Cambios revertidos, base de datos intacta")
            print("=" * 80)
            return False
            
    except psycopg2.Error as e:
        print(f"\n✗ ERROR de PostgreSQL: {e}")
        if conn:
            conn.rollback()
            print("✓ Rollback automático ejecutado")
        return False
        
    except Exception as e:
        print(f"\n✗ ERROR inesperado: {e}")
        if conn:
            conn.rollback()
            print("✓ Rollback automático ejecutado")
        return False
        
    finally:
        # Cerrar cursor y conexión
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            print("\nConexión cerrada.")


def main():
    """Función principal"""
    print("\n" + "=" * 80)
    print("SCRIPT DE NORMALIZACIÓN DE MONTOS".center(80))
    print("=" * 80)
    print("\nEste script divide por 100 los montos de:")
    print("  • INGRESO")
    print("  • GASTO")
    print("  • DISTRIBUCION")
    print("\nLos RETIROS NO se modifican (ya están correctos).")
    print("\nSe usará una transacción para poder revertir los cambios.")
    print("=" * 80)
    
    input("\nPresione ENTER para continuar...")
    
    exito = normalizar_montos()
    
    if exito:
        print("\n✓ Normalización completada exitosamente")
        sys.exit(0)
    else:
        print("\n✗ Normalización cancelada o fallida")
        sys.exit(1)


if __name__ == "__main__":
    main()

