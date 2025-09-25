#!/usr/bin/env python3
"""
Preguntas COMPUESTAS y COMPARATIVAS reales de Conexión Consultora
"""

# PREGUNTAS COMPUESTAS (múltiples análisis en una)
preguntas_compuestas = [
    # Análisis completo por área
    ("¿Cómo viene el área Jurídica?",
     """-- Análisis completo del área Jurídica
     SELECT 
        'Jurídica' as area,
        SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END) as ingresos,
        SUM(CASE WHEN tipo_operacion='GASTO' THEN monto_uyu ELSE 0 END) as gastos,
        ((SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END) - 
          SUM(CASE WHEN tipo_operacion='GASTO' THEN monto_uyu ELSE 0 END)) / 
         NULLIF(SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END), 0)) * 100 as rentabilidad
     FROM operaciones o JOIN areas a ON o.area_id=a.id
     WHERE a.nombre='Jurídica' AND fecha <= CURRENT_DATE"""),
    
    # Comparación entre localidades
    ("¿Cómo viene Montevideo comparado con Mercedes?",
     """-- Comparación completa Montevideo vs Mercedes
     SELECT 
        localidad,
        SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END) as ingresos,
        SUM(CASE WHEN tipo_operacion='GASTO' THEN monto_uyu ELSE 0 END) as gastos,
        ((SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END) - 
          SUM(CASE WHEN tipo_operacion='GASTO' THEN monto_uyu ELSE 0 END)) / 
         NULLIF(SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END), 0)) * 100 as rentabilidad,
        COUNT(DISTINCT CASE WHEN cliente IS NOT NULL THEN cliente END) as cantidad_clientes
     FROM operaciones 
     GROUP BY localidad
     ORDER BY rentabilidad DESC"""),
]

print(f"Preguntas compuestas para entrenar: {len(preguntas_compuestas)}")

# PREGUNTAS SIMPLES (una métrica)
preguntas_simples = [
    ("¿Cuánto facturamos este mes?",
     "SELECT SUM(monto_uyu) FROM operaciones WHERE tipo_operacion='INGRESO' AND DATE_TRUNC('month', fecha)=DATE_TRUNC('month', CURRENT_DATE)"),
    
    ("¿Cuál es el cliente que más facturó?",
     "SELECT cliente, SUM(monto_uyu) as total FROM operaciones WHERE tipo_operacion='INGRESO' AND cliente IS NOT NULL GROUP BY cliente ORDER BY total DESC LIMIT 1"),
]

# VARIACIONES DE "CÓMO VIENE/VENIMOS"
preguntas_como_viene = [
    ("¿Cómo venimos?",
     """-- Análisis general de la empresa
     SELECT 
        SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END) as ingresos_totales,
        SUM(CASE WHEN tipo_operacion='GASTO' THEN monto_uyu ELSE 0 END) as gastos_totales,
        ((SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END) - 
          SUM(CASE WHEN tipo_operacion='GASTO' THEN monto_uyu ELSE 0 END)) / 
         NULLIF(SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END), 0)) * 100 as rentabilidad
     FROM operaciones WHERE fecha <= CURRENT_DATE"""),
]

print(f"Total: {len(preguntas_compuestas) + len(preguntas_simples) + len(preguntas_como_viene)} preguntas mixtas")
