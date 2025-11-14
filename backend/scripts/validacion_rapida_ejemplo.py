"""
Ejemplo de Validación Rápida - CFO Inteligente

Script de ejemplo que valida las 2 queries problemáticas conocidas
sin necesidad de interacción manual.

Uso: python validacion_rapida_ejemplo.py
"""

import psycopg2
from decimal import Decimal


def ejecutar_query(sql: str) -> list:
    """Ejecuta query y retorna resultados"""
    conn = psycopg2.connect(
        "postgresql://postgres:postgres@localhost:5432/cfo_inteligente"
    )
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def validar_query_distribuciones_2024():
    """Valida Query 1: Distribuciones 2024 por socio"""
    print("=" * 80)
    print("🔍 VALIDACIÓN QUERY 1: ¿Quién recibió MENOS distribuciones en 2024?")
    print("=" * 80)
    print()
    
    # SQL INCORRECTO (generado originalmente)
    sql_incorrecto = """
WITH distribuciones_2024 AS (
    SELECT
        s.nombre AS socio,
        COALESCE(SUM(dd.monto_uyu), 0) AS total_distribuido
    FROM socios s
    LEFT JOIN distribuciones_detalle dd ON s.id = dd.socio_id
    LEFT JOIN operaciones o ON dd.operacion_id = o.id
        AND o.tipo_operacion = 'DISTRIBUCION'
        AND o.deleted_at IS NULL
        AND EXTRACT(YEAR FROM o.fecha) = 2024
    GROUP BY s.nombre
)
SELECT socio, total_distribuido
FROM distribuciones_2024
ORDER BY total_distribuido ASC
LIMIT 1;
"""
    
    # SQL CORRECTO
    sql_correcto = """
SELECT 
  s.nombre AS socio,
  SUM(dd.monto_uyu) AS total_distribuido
FROM distribuciones_detalle dd
INNER JOIN operaciones o ON dd.operacion_id = o.id
INNER JOIN socios s ON dd.socio_id = s.id
WHERE o.tipo_operacion = 'DISTRIBUCION'
  AND o.deleted_at IS NULL
  AND EXTRACT(YEAR FROM o.fecha) = 2024
GROUP BY s.nombre
ORDER BY total_distribuido ASC
LIMIT 1;
"""
    
    print("🔄 Ejecutando SQL INCORRECTO (LEFT JOIN)...")
    resultado_incorrecto = ejecutar_query(sql_incorrecto)
    print(f"   Resultado: {resultado_incorrecto[0][0]} - ${resultado_incorrecto[0][1]:,.2f}")
    
    print("\n🔄 Ejecutando SQL CORRECTO (INNER JOIN)...")
    resultado_correcto = ejecutar_query(sql_correcto)
    print(f"   Resultado: {resultado_correcto[0][0]} - ${resultado_correcto[0][1]:,.2f}")
    
    # Comparar
    diferencia = Decimal(resultado_incorrecto[0][1]) - Decimal(resultado_correcto[0][1])
    porcentaje_error = (diferencia / Decimal(resultado_correcto[0][1])) * 100
    
    print("\n📊 COMPARACIÓN:")
    print(f"   SQL Incorrecto: ${resultado_incorrecto[0][1]:,.2f}")
    print(f"   SQL Correcto:   ${resultado_correcto[0][1]:,.2f}")
    print(f"   Diferencia:     ${diferencia:,.2f}")
    print(f"   % Error:        {porcentaje_error:,.1f}%")
    
    if abs(diferencia) > 100:
        print(f"\n   ❌ ERROR CONFIRMADO: Diferencia de ${diferencia:,.2f}")
        return False
    else:
        print("\n   ✅ RESULTADOS SIMILARES")
        return True


def validar_query_distribuciones_trimestre():
    """Valida Query 2: Distribuciones del trimestre"""
    print("\n" + "=" * 80)
    print("🔍 VALIDACIÓN QUERY 2: Distribuciones del último trimestre")
    print("=" * 80)
    print()
    
    # SQL INCORRECTO
    sql_incorrecto = """
WITH distribuciones_trimestre AS (
    SELECT o.id, o.monto_uyu, o.monto_usd, o.fecha
    FROM operaciones o
    WHERE o.tipo_operacion = 'DISTRIBUCION'
    AND o.deleted_at IS NULL
    AND o.fecha >= DATE_TRUNC('quarter', CURRENT_DATE - INTERVAL '3 months')
    AND o.fecha < DATE_TRUNC('quarter', CURRENT_DATE)
)
SELECT
    s.nombre AS socio,
    COALESCE(SUM(dd.monto_uyu), 0) AS total_distribuido_uyu
FROM socios s
LEFT JOIN distribuciones_detalle dd ON s.id = dd.socio_id
LEFT JOIN distribuciones_trimestre dt ON dd.operacion_id = dt.id
GROUP BY s.nombre
ORDER BY socio
LIMIT 1;
"""
    
    # SQL CORRECTO
    sql_correcto = """
WITH distribuciones_trimestre AS (
    SELECT o.id
    FROM operaciones o
    WHERE o.tipo_operacion = 'DISTRIBUCION'
    AND o.deleted_at IS NULL
    AND o.fecha >= DATE_TRUNC('quarter', CURRENT_DATE - INTERVAL '3 months')
    AND o.fecha < DATE_TRUNC('quarter', CURRENT_DATE)
)
SELECT
    s.nombre AS socio,
    SUM(dd.monto_uyu) AS total_distribuido_uyu
FROM distribuciones_detalle dd
INNER JOIN distribuciones_trimestre dt ON dd.operacion_id = dt.id
INNER JOIN socios s ON dd.socio_id = s.id
GROUP BY s.nombre
ORDER BY socio
LIMIT 1;
"""
    
    print("🔄 Ejecutando SQL INCORRECTO (LEFT JOIN)...")
    resultado_incorrecto = ejecutar_query(sql_incorrecto)
    print(f"   Resultado: {resultado_incorrecto[0][0]} - ${resultado_incorrecto[0][1]:,.2f}")
    
    print("\n🔄 Ejecutando SQL CORRECTO (INNER JOIN)...")
    resultado_correcto = ejecutar_query(sql_correcto)
    print(f"   Resultado: {resultado_correcto[0][0]} - ${resultado_correcto[0][1]:,.2f}")
    
    # Comparar
    diferencia = Decimal(resultado_incorrecto[0][1]) - Decimal(resultado_correcto[0][1])
    porcentaje_error = (diferencia / Decimal(resultado_correcto[0][1])) * 100
    
    print("\n📊 COMPARACIÓN:")
    print(f"   SQL Incorrecto: ${resultado_incorrecto[0][1]:,.2f}")
    print(f"   SQL Correcto:   ${resultado_correcto[0][1]:,.2f}")
    print(f"   Diferencia:     ${diferencia:,.2f}")
    print(f"   % Error:        {porcentaje_error:,.1f}%")
    
    if abs(diferencia) > 100:
        print(f"\n   ❌ ERROR CONFIRMADO: Diferencia de ${diferencia:,.2f}")
        return False
    else:
        print("\n   ✅ RESULTADOS SIMILARES")
        return True


def main():
    """Función principal"""
    print("🔍 VALIDACIÓN RÁPIDA - QUERIES PROBLEMÁTICAS CONOCIDAS")
    print()
    
    resultados = []
    
    try:
        # Validar Query 1
        resultado1 = validar_query_distribuciones_2024()
        resultados.append(('Query 1 - Distribuciones 2024', resultado1))
        
        # Validar Query 2
        resultado2 = validar_query_distribuciones_trimestre()
        resultados.append(('Query 2 - Distribuciones trimestre', resultado2))
        
        # Resumen
        print("\n" + "=" * 80)
        print("📊 RESUMEN DE VALIDACIÓN")
        print("=" * 80)
        print()
        
        for nombre, resultado in resultados:
            estado = "✅ OK" if resultado else "❌ ERROR"
            print(f"   {estado}  {nombre}")
        
        errores = sum(1 for _, r in resultados if not r)
        total = len(resultados)
        
        print()
        print(f"   Total: {total - errores}/{total} correctas")
        print(f"   Confianza: {((total - errores) / total * 100):.1f}%")
        
        if errores > 0:
            print(f"\n   ⚠️  {errores} queries con errores confirmados")
            print("   Acción: Actualizar REGLA 12 en claude_sql_generator.py")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

