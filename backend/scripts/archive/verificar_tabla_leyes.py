#!/usr/bin/env python3
"""
Script para verificar si existe la tabla leyes y qué datos tiene.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, inspect

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:NLlXASvwKuOHCUsDpdUWcojpPDUDLmzx@shortline.proxy.rlwy.net:50827/railway"
)

def main():
    print("=" * 80)
    print("VERIFICACIÓN DE TABLA LEYES")
    print("=" * 80)
    print()
    
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    # Listar todas las tablas
    print("📋 Tablas en la base de datos:")
    print("-" * 80)
    tablas = inspector.get_table_names()
    for tabla in sorted(tablas):
        print(f"  - {tabla}")
    print()
    
    # Verificar si existe tabla leyes
    if 'leyes' not in tablas:
        print("❌ La tabla 'leyes' NO existe en la base de datos")
        print()
        print("Tablas similares encontradas:")
        similares = [t for t in tablas if 'ley' in t.lower() or 'impo' in t.lower()]
        if similares:
            for t in similares:
                print(f"  - {t}")
        else:
            print("  (ninguna)")
        return
    
    print("✅ La tabla 'leyes' existe")
    print()
    
    # Obtener estructura de la tabla
    print("📐 Estructura de la tabla 'leyes':")
    print("-" * 80)
    columnas = inspector.get_columns('leyes')
    for col in columnas:
        print(f"  - {col['name']}: {col['type']} (nullable={col.get('nullable', True)})")
    print()
    
    # Contar registros
    with engine.connect() as conn:
        count_result = conn.execute(text("SELECT COUNT(*) FROM leyes"))
        total = count_result.scalar()
        print(f"📊 Total de registros: {total}")
        print()
        
        if total == 0:
            print("⚠️  La tabla está vacía")
            return
        
        # Buscar las leyes específicas
        print("🔍 Buscando leyes específicas:")
        print("-" * 80)
        query = text("""
            SELECT numero, anio, tiene_texto, url_impo 
            FROM leyes 
            WHERE numero IN (19575, 16827, 18719, 17930)
            ORDER BY numero;
        """)
        result = conn.execute(query)
        encontradas = []
        for row in result:
            encontradas.append({
                'numero': row.numero,
                'anio': row.anio,
                'tiene_texto': row.tiene_texto,
                'url_impo': row.url_impo
            })
        
        if encontradas:
            print(f"✅ Encontradas {len(encontradas)} leyes:")
            for ley in encontradas:
                print(f"  - Ley {ley['numero']}/{ley['anio']}: tiene_texto={ley['tiene_texto']}")
        else:
            print("❌ No se encontraron leyes con esos números")
            print()
            print("Algunas leyes disponibles (primeras 10):")
            query_all = text("SELECT numero, anio FROM leyes ORDER BY numero LIMIT 10")
            result_all = conn.execute(query_all)
            for row in result_all:
                print(f"  - Ley {row.numero}/{row.anio}")

if __name__ == "__main__":
    main()
