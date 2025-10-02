#!/usr/bin/env python3
"""
Test Exhaustivo - 50 Preguntas Reales de Negocio
Sistema CFO Inteligente con SQL Router (Claude → Vanna)

Evalúa:
- Tasa de éxito del sistema
- Distribución Claude vs Vanna
- Tiempos de respuesta
- Calidad de SQL generado

Ejecutar:
    cd backend && source venv/bin/activate
    python scripts/test_50_preguntas.py

Salida:
    - Logs en consola (tiempo real)
    - CSV con resultados: scripts/test_50_resultados.csv
    - Resumen estadístico final
"""

import requests
import csv
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════

BASE_URL = "http://localhost:8000"
ENDPOINT = f"{BASE_URL}/api/cfo/ask"
TIMEOUT = 25  # segundos por query (SQL gen: 4-6s + exec: 1-3s + narrativa: 3-5s + margen)
ARCHIVO_PREGUNTAS = Path(__file__).parent / "preguntas_reales_test.txt"
ARCHIVO_CSV = Path(__file__).parent / "test_50_resultados.csv"

# ══════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ══════════════════════════════════════════════════════════════

def verificar_servidor() -> bool:
    """Verifica que el servidor FastAPI esté corriendo"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print(f"✅ Servidor FastAPI activo en {BASE_URL}")
            return True
        else:
            print(f"❌ Servidor responde pero con status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Servidor NO está corriendo en {BASE_URL}")
        print(f"   Error: {e}")
        print(f"\n💡 Iniciar con: uvicorn app.main:app --reload")
        return False

def leer_preguntas(archivo: Path) -> List[str]:
    """Lee preguntas del archivo txt"""
    if not archivo.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {archivo}")
    
    with open(archivo, 'r', encoding='utf-8') as f:
        preguntas = [linea.strip() for linea in f if linea.strip()]
    
    return preguntas

def testear_pregunta(pregunta: str, timeout: int = TIMEOUT) -> Dict[str, Any]:
    """
    Ejecuta una pregunta contra el endpoint y captura métricas
    
    Returns:
        {
            'pregunta': str,
            'status': 'success' | 'error' | 'timeout',
            'metodo': 'claude' | 'vanna_fallback' | 'ninguno' | None,
            'tiempo_respuesta': float,
            'tiempo_generacion_sql': float | None,
            'sql_generado': str | None,
            'sql_preview': str (primeros 80 chars),
            'respuesta': str | None,
            'error': str | None
        }
    """
    inicio = time.time()
    
    try:
        response = requests.post(
            ENDPOINT,
            json={"pregunta": pregunta},
            timeout=timeout
        )
        
        tiempo_respuesta = time.time() - inicio
        
        if response.status_code != 200:
            return {
                'pregunta': pregunta,
                'status': 'error',
                'metodo': None,
                'tiempo_respuesta': tiempo_respuesta,
                'tiempo_generacion_sql': None,
                'sql_generado': None,
                'sql_preview': '',
                'respuesta': None,
                'error': f'HTTP {response.status_code}: {response.text[:100]}'
            }
        
        data = response.json()
        
        # Extraer métricas
        status = data.get('status', 'unknown')
        metodo = data.get('metadata', {}).get('metodo_generacion_sql', None)
        tiempo_sql = data.get('metadata', {}).get('tiempo_generacion_sql', None)
        sql_generado = data.get('sql_generado', None)
        sql_preview = sql_generado[:80] if sql_generado else ''
        respuesta = data.get('respuesta', None)
        error = data.get('error', None) or data.get('metadata', {}).get('error', None)
        
        return {
            'pregunta': pregunta,
            'status': status,
            'metodo': metodo,
            'tiempo_respuesta': tiempo_respuesta,
            'tiempo_generacion_sql': tiempo_sql,
            'sql_generado': sql_generado,
            'sql_preview': sql_preview,
            'respuesta': respuesta,
            'error': error
        }
    
    except requests.Timeout:
        tiempo_respuesta = time.time() - inicio
        return {
            'pregunta': pregunta,
            'status': 'timeout',
            'metodo': None,
            'tiempo_respuesta': tiempo_respuesta,
            'tiempo_generacion_sql': None,
            'sql_generado': None,
            'sql_preview': '',
            'respuesta': None,
            'error': f'Timeout después de {timeout}s'
        }
    
    except Exception as e:
        tiempo_respuesta = time.time() - inicio
        return {
            'pregunta': pregunta,
            'status': 'error',
            'metodo': None,
            'tiempo_respuesta': tiempo_respuesta,
            'tiempo_generacion_sql': None,
            'sql_generado': None,
            'sql_preview': '',
            'respuesta': None,
            'error': f'Exception: {type(e).__name__}: {str(e)[:80]}'
        }

def guardar_csv(resultados: List[Dict[str, Any]], archivo: Path):
    """Guarda resultados en CSV"""
    with open(archivo, 'w', newline='', encoding='utf-8') as f:
        campos = [
            'numero', 'pregunta', 'status', 'metodo', 
            'tiempo_respuesta', 'tiempo_generacion_sql', 
            'sql_preview', 'respuesta_preview', 'error'
        ]
        
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        
        for i, r in enumerate(resultados, 1):
            writer.writerow({
                'numero': i,
                'pregunta': r['pregunta'],
                'status': r['status'],
                'metodo': r['metodo'] or 'N/A',
                'tiempo_respuesta': f"{r['tiempo_respuesta']:.2f}s",
                'tiempo_generacion_sql': f"{r['tiempo_generacion_sql']:.2f}s" if r['tiempo_generacion_sql'] else 'N/A',
                'sql_preview': r['sql_preview'],
                'respuesta_preview': r['respuesta'][:100] if r['respuesta'] else '',
                'error': r['error'] or ''
            })

def calcular_estadisticas(resultados: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calcula estadísticas del test"""
    total = len(resultados)
    exitosos = [r for r in resultados if r['status'] == 'success']
    fallidos = [r for r in resultados if r['status'] != 'success']
    
    # Contar por método
    claude = [r for r in exitosos if r['metodo'] == 'claude']
    vanna = [r for r in exitosos if r['metodo'] == 'vanna_fallback']
    
    # Tiempos
    tiempos_respuesta = [r['tiempo_respuesta'] for r in exitosos]
    tiempo_promedio = sum(tiempos_respuesta) / len(tiempos_respuesta) if tiempos_respuesta else 0
    tiempo_min = min(tiempos_respuesta) if tiempos_respuesta else 0
    tiempo_max = max(tiempos_respuesta) if tiempos_respuesta else 0
    
    return {
        'total': total,
        'exitosos': len(exitosos),
        'fallidos': len(fallidos),
        'tasa_exito': (len(exitosos) / total * 100) if total > 0 else 0,
        'claude_count': len(claude),
        'vanna_count': len(vanna),
        'tiempo_promedio': tiempo_promedio,
        'tiempo_min': tiempo_min,
        'tiempo_max': tiempo_max,
        'lista_fallos': fallidos
    }

# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main():
    print("="*80)
    print("🧪 TEST MASIVO - 50 PREGUNTAS REALES DE NEGOCIO")
    print(f"📅 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Verificar servidor
    if not verificar_servidor():
        return 1
    
    # Leer preguntas
    try:
        preguntas = leer_preguntas(ARCHIVO_PREGUNTAS)
        print(f"\n📋 {len(preguntas)} preguntas cargadas desde {ARCHIVO_PREGUNTAS.name}")
    except Exception as e:
        print(f"\n❌ Error al leer preguntas: {e}")
        return 1
    
    # Ejecutar tests
    print(f"\n🚀 Iniciando tests...")
    print("="*80 + "\n")
    
    resultados = []
    
    for i, pregunta in enumerate(preguntas, 1):
        print(f"[{i:2}/{len(preguntas)}] {pregunta[:60]:60}... ", end='', flush=True)
        
        resultado = testear_pregunta(pregunta)
        resultados.append(resultado)
        
        # Log en consola
        if resultado['status'] == 'success':
            metodo = resultado['metodo'] or 'N/A'
            tiempo = resultado['tiempo_respuesta']
            print(f"✅ {resultado['status']:8} ({metodo:15}, {tiempo:4.1f}s)")
        elif resultado['status'] == 'timeout':
            print(f"⏱️  {resultado['status']:8} (>15s)")
        else:
            error_corto = resultado['error'][:30] if resultado['error'] else 'unknown'
            print(f"❌ {resultado['status']:8} ({error_corto})")
    
    # Guardar CSV
    print(f"\n💾 Guardando resultados en CSV...")
    try:
        guardar_csv(resultados, ARCHIVO_CSV)
        print(f"   ✅ CSV guardado: {ARCHIVO_CSV}")
    except Exception as e:
        print(f"   ❌ Error al guardar CSV: {e}")
    
    # Calcular estadísticas
    stats = calcular_estadisticas(resultados)
    
    # Imprimir resumen
    print("\n" + "="*80)
    print("📊 RESUMEN TEST 50 PREGUNTAS REALES")
    print("="*80)
    print(f"Total queries:        {stats['total']}")
    print(f"Exitosas:             {stats['exitosos']} ({stats['tasa_exito']:.1f}%)")
    print(f"Fallidas:             {stats['fallidos']}")
    print("-"*80)
    print(f"Claude (primary):     {stats['claude_count']} queries ({stats['claude_count']*100//stats['total']}%)")
    print(f"Vanna (fallback):     {stats['vanna_count']} queries ({stats['vanna_count']*100//stats['total']}%)")
    print("-"*80)
    print(f"Tiempo promedio:      {stats['tiempo_promedio']:.2f}s")
    print(f"Tiempo mínimo:        {stats['tiempo_min']:.2f}s")
    print(f"Tiempo máximo:        {stats['tiempo_max']:.2f}s")
    print("="*80)
    
    # Mostrar fallos si hay
    if stats['lista_fallos']:
        print(f"\n⚠️  QUERIES FALLIDAS ({len(stats['lista_fallos'])}):")
        print("-"*80)
        for fallo in stats['lista_fallos']:
            numero = resultados.index(fallo) + 1
            print(f"[{numero:2}] {fallo['pregunta']}")
            print(f"     Status: {fallo['status']}")
            print(f"     Error: {fallo['error'][:100] if fallo['error'] else 'N/A'}")
        print("-"*80)
    
    # Conclusión
    print(f"\n📄 CSV detallado: {ARCHIVO_CSV}")
    print(f"📅 Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Determinar exit code
    if stats['tasa_exito'] >= 95:
        print("\n🎉 ¡EXCELENTE! Tasa de éxito ≥95%")
        return 0
    elif stats['tasa_exito'] >= 85:
        print(f"\n✅ BUENO - Tasa de éxito {stats['tasa_exito']:.1f}% (objetivo: ≥95%)")
        return 0
    else:
        print(f"\n⚠️  INSUFICIENTE - Tasa de éxito {stats['tasa_exito']:.1f}% (objetivo: ≥95%)")
        print("   Revisar queries fallidas y mejorar entrenamiento")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())

