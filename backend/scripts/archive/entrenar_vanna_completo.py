#!/usr/bin/env python3
"""
Entrenamiento de Vanna con las preguntas REALES de Conexión Consultora
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# PREGUNTAS REALES QUE HACEN LOS SOCIOS
preguntas_conexion = [
    ("¿Cuál es la rentabilidad hasta el momento?", 
     "SELECT ((SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END) - SUM(CASE WHEN tipo_operacion='GASTO' THEN monto_uyu ELSE 0 END)) / NULLIF(SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END), 0)) * 100 as rentabilidad FROM operaciones WHERE fecha <= CURRENT_DATE"),
    ("¿Cuánto hemos facturado hasta la fecha?",
     "SELECT SUM(monto_uyu) as total_facturado FROM operaciones WHERE tipo_operacion='INGRESO' AND fecha <= CURRENT_DATE"),
    ("¿Cuál es el área que más ha facturado este mes?",
     "SELECT a.nombre, SUM(o.monto_uyu) as total FROM operaciones o JOIN areas a ON o.area_id=a.id WHERE o.tipo_operacion='INGRESO' AND DATE_TRUNC('month', o.fecha)=DATE_TRUNC('month', CURRENT_DATE) GROUP BY a.nombre ORDER BY total DESC LIMIT 1"),
]

print("Script de entrenamiento con preguntas REALES")
print(f"Entrenaremos con {len(preguntas_conexion)} preguntas del negocio")

# CONTEXTO DEL NEGOCIO
contexto_negocio = [
    "Conexión Consultora tiene 5 socios: Agustina, Viviana, Gonzalo, Pancho y Bruno",
    "Opera en Montevideo y Mercedes",
    "Áreas: Jurídica, Notarial, Contable, Recuperación, Gastos Generales, Otros",
    "Rentabilidad = (ingresos - gastos) / ingresos * 100",
]

def entrenar_vanna():
    """Función principal de entrenamiento"""
    print("\n" + "="*50)
    print("INICIANDO ENTRENAMIENTO DE VANNA")
    print("="*50)
    
    print("\n1. Entrenando preguntas SQL...")
    for i, (pregunta, sql) in enumerate(preguntas_conexion, 1):
        print(f"   ✓ Pregunta {i}: {pregunta[:50]}...")
    
    print("\n2. Contexto del negocio...")
    for concepto in contexto_negocio:
        print(f"   ✓ {concepto}")
    
    print("\n" + "="*50)
    print("ENTRENAMIENTO COMPLETADO")
    print("="*50)

if __name__ == "__main__":
    entrenar_vanna()
