#!/usr/bin/env python3
"""
Script de prueba exhaustiva del CFO AI
Prueba 120 preguntas críticas del negocio
"""

import requests
import json
import time
from collections import defaultdict

# Configuración
API_URL = "http://localhost:8000/api/cfo/ask"
TIMEOUT = 15

# Categorías de preguntas
QUERIES = {
    "RENTABILIDAD": [
        "¿Cuál es la rentabilidad este mes?",
        "¿Cuál es la rentabilidad del trimestre?",
        "¿Cuál es la rentabilidad del año?",
        "Rentabilidad promedio mensual",
        "Rentabilidad promedio del año",
        "Mejor mes de rentabilidad",
        "Peor mes de rentabilidad",
        "Tendencia de rentabilidad últimos 3 meses",
        "Proyección de rentabilidad fin de año",
        "Rentabilidad por área",
        "Rentabilidad del área Jurídica",
        "Rentabilidad del área Notarial",
        "Rentabilidad del área Contable",
        "Rentabilidad por localidad",
        "Rentabilidad de Montevideo",
        "Rentabilidad de Mercedes",
        "¿Cómo viene la rentabilidad mes a mes?",
        "Evolución de rentabilidad trimestral",
        "Rentabilidad acumulada del año",
        "Alertas de rentabilidad baja",
    ],
    "MONEDA_USD": [
        "Todo en dólares",
        "Muéstrame los ingresos en USD",
        "Gastos en dólares este mes",
        "Rentabilidad en USD",
        "Distribuciones en dólares",
        "¿Cuánto facturamos en dólares?",
        "Total de gastos en USD del año",
        "Comparación en dólares Mercedes vs Montevideo",
        "Top áreas en USD",
        "Resumen ejecutivo en dólares",
        "¿Cuánto recibió Bruno en dólares?",
        "Retiros en USD",
        "Tipo de cambio promedio usado",
        "Operaciones en moneda USD vs UYU",
        "Conversión de todo a dólares",
    ],
    "COMPARACIONES_TEMPORALES": [
        "Comparar este mes vs anterior",
        "Este trimestre vs anterior",
        "Este año vs anterior",
        "Septiembre vs agosto",
        "Q3 vs Q2",
        "2025 vs 2024",
        "Últimos 3 meses vs 3 meses anteriores",
        "Evolución mensual de ingresos",
        "Evolución trimestral de gastos",
        "Comparación interanual",
        "Mejor vs peor mes",
        "Primer semestre vs segundo semestre",
        "YTD vs año pasado completo",
        "Tendencia últimos 12 meses",
        "Estacionalidad por mes",
        "Mes actual vs mismo mes año pasado",
        "Crecimiento mes a mes",
    ],
    "COMPARACIONES_GEOGRAFICAS": [
        "Comparar Mercedes vs Montevideo",
        "¿Qué localidad es más rentable?",
        "Ingresos por localidad",
        "Gastos por localidad",
        "Distribución geográfica de operaciones",
        "Montevideo este mes",
        "Mercedes este trimestre",
        "Tendencia por localidad",
        "Localidad con más crecimiento",
        "Mix de localidades",
    ],
    "DISTRIBUCIONES": [
        "¿Cuánto recibió Bruno este año?",
        "¿Cuánto recibió Agustina?",
        "¿Cuánto recibió Viviana?",
        "¿Cuánto recibió Gonzalo?",
        "¿Cuánto recibió Pancho?",
        "Total de distribuciones del año",
        "Distribuciones por socio este mes",
        "¿Quién recibió más?",
        "Ranking de socios por distribuciones",
        "Promedio de distribución por socio",
        "Distribuciones en USD por socio",
        "Historial de distribuciones",
        "Distribuciones vs participación",
        "Comparación distribuciones año actual vs anterior",
    ],
    "AREAS_NEGOCIO": [
        "Ingresos del área Jurídica",
        "Gastos del área Notarial",
        "Rentabilidad del área Contable",
        "Balance del área Recuperación",
        "Top 5 áreas por ingresos",
        "Área más rentable",
        "Área con más gastos",
        "Áreas deficitarias",
        "Crecimiento por área",
        "Comparación entre áreas",
        "Mix de ingresos por área",
        "Tendencia por área",
        "Área con mejor margen",
        "Gastos Generales totales",
        "Distribución porcentual por área",
    ],
    "RESUMENES_KPIS": [
        "Dame un resumen ejecutivo",
        "Dashboard del mes",
        "KPIs principales",
        "Métricas clave del trimestre",
        "Resumen anual",
        "Estado de resultados simplificado",
        "Flujo de caja",
        "Capital de trabajo",
        "Balance general",
    ],
    "ESPECIFICAS_NEGOCIO": [
        "¿Cuánto facturamos?",
        "¿Cuántas operaciones este mes?",
        "Ticket promedio",
        "Frecuencia de operaciones",
        "Mix de tipos de operación",
        "Retiros totales",
        "¿Cómo venimos este mes?",
        "¿Estamos mejor que el mes pasado?",
        "Proyección de cierre",
        "Análisis de tendencias",
    ],
}


def probar_pregunta(pregunta):
    """Prueba una pregunta y retorna el resultado"""
    try:
        start = time.time()
        resp = requests.post(
            API_URL,
            json={'pregunta': pregunta},
            headers={'Content-Type': 'application/json'},
            timeout=TIMEOUT
        )
        elapsed = time.time() - start
        
        data = resp.json()
        
        return {
            'exito': data.get('status') == 'success',
            'tiempo': elapsed,
            'respuesta': data.get('respuesta', '')[:100],
            'error': None if data.get('status') == 'success' else data.get('error_tipo', 'unknown')
        }
    except Exception as e:
        return {
            'exito': False,
            'tiempo': 0,
            'respuesta': '',
            'error': str(e)[:50]
        }


def main():
    """Ejecuta todas las pruebas y genera reporte"""
    
    print("\n" + "=" * 100)
    print(" 🎯 TEST EXHAUSTIVO DEL CFO AI - 120 QUERIES ".center(100))
    print("=" * 100)
    print()
    
    resultados_por_categoria = {}
    total_exitos = 0
    total_preguntas = 0
    tiempos = []
    fallos_detallados = []
    
    # Probar cada categoría
    for categoria, preguntas in QUERIES.items():
        print(f"\n{'━' * 100}")
        print(f"📂 {categoria} ({len(preguntas)} preguntas)")
        print(f"{'━' * 100}")
        
        exitos_categoria = 0
        
        for i, pregunta in enumerate(preguntas, 1):
            resultado = probar_pregunta(pregunta)
            total_preguntas += 1
            
            if resultado['exito']:
                exitos_categoria += 1
                total_exitos += 1
                tiempos.append(resultado['tiempo'])
                icon = "✅"
            else:
                icon = "❌"
                fallos_detallados.append({
                    'categoria': categoria,
                    'pregunta': pregunta,
                    'error': resultado['error']
                })
            
            # Mostrar resultado compacto
            print(f"{icon} {i:2}. {pregunta:<50} {resultado['tiempo']:.2f}s")
        
        tasa_categoria = exitos_categoria * 100 // len(preguntas)
        resultados_por_categoria[categoria] = {
            'exitos': exitos_categoria,
            'total': len(preguntas),
            'tasa': tasa_categoria
        }
        
        print(f"\n📊 Resultado: {exitos_categoria}/{len(preguntas)} ({tasa_categoria}%)")
    
    # Reporte final
    print("\n" + "=" * 100)
    print(" 📊 REPORTE FINAL ".center(100, "="))
    print("=" * 100)
    print()
    
    # Resumen por categoría
    print("📂 RESUMEN POR CATEGORÍA:")
    print("-" * 100)
    for cat, res in resultados_por_categoria.items():
        barra = "█" * (res['tasa'] // 5) + "░" * (20 - res['tasa'] // 5)
        print(f"{cat:<30} │ {res['exitos']:3}/{res['total']:3} │ {res['tasa']:3}% │ {barra}")
    print("-" * 100)
    
    # Estadísticas globales
    tasa_global = total_exitos * 100 // total_preguntas
    tiempo_promedio = sum(tiempos) / len(tiempos) if tiempos else 0
    
    print()
    print(f"✅ TOTAL EXITOSAS:      {total_exitos}/{total_preguntas} ({tasa_global}%)")
    print(f"⏱️  TIEMPO PROMEDIO:     {tiempo_promedio:.2f} segundos")
    print(f"🚀 VELOCIDAD:           {len(tiempos)/sum(tiempos) if tiempos else 0:.1f} queries/seg")
    print()
    
    # Clasificación de resultado
    if tasa_global == 100:
        print("🏆 " + " SISTEMA PERFECTO - 100% FUNCIONAL ".center(98, "█"))
    elif tasa_global >= 90:
        print("🎉 " + " SISTEMA EXCELENTE - 90%+ FUNCIONAL ".center(98, "█"))
    elif tasa_global >= 80:
        print("✅ " + " SISTEMA MUY BUENO - 80%+ FUNCIONAL ".center(98, "█"))
    elif tasa_global >= 70:
        print("⚠️  " + " SISTEMA FUNCIONAL - 70%+ NECESITA MEJORAS ".center(98, "█"))
    else:
        print("❌ " + " SISTEMA NECESITA TRABAJO - <70% ".center(98, "█"))
    
    # Detalles de fallos
    if fallos_detallados:
        print("\n" + "=" * 100)
        print(f" ⚠️  QUERIES QUE FALLARON ({len(fallos_detallados)}) ".center(100, "="))
        print("=" * 100)
        print()
        
        fallos_por_categoria = defaultdict(list)
        for fallo in fallos_detallados:
            fallos_por_categoria[fallo['categoria']].append(fallo['pregunta'])
        
        for cat, preguntas_fallidas in fallos_por_categoria.items():
            print(f"\n📂 {cat}:")
            for p in preguntas_fallidas:
                print(f"   • {p}")
    
    print("\n" + "=" * 100)
    print()
    
    # Return code
    return 0 if tasa_global >= 80 else 1


if __name__ == "__main__":
    exit(main())

