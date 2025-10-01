#!/usr/bin/env python3
"""
Test completo del endpoint /api/cfo/ask con Claude narrativo
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

print("="*80)
print("🧪 TEST COMPLETO DEL ENDPOINT CFO AI")
print("="*80 + "\n")

# Verificar que el servidor esté corriendo
try:
    response = requests.get(f"{BASE_URL}/health", timeout=2)
    print(f"✅ Servidor FastAPI corriendo")
    print(f"   Status: {response.json()}")
except Exception as e:
    print(f"❌ Servidor NO está corriendo en {BASE_URL}")
    print(f"   Error: {e}")
    print("\n💡 Iniciar con: cd backend && source venv/bin/activate && uvicorn app.main:app --reload")
    sys.exit(1)

# Test 1: Pregunta simple - Contador de retiros
print("\n" + "="*80)
print("TEST 1: ¿Cuántos retiros hicimos este año?")
print("="*80)

try:
    response = requests.post(
        f"{BASE_URL}/api/cfo/ask",
        json={"pregunta": "¿Cuántos retiros hicimos este año?"},
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Status: {data.get('status')}")
        print(f"📝 Respuesta narrativa:")
        print(f"   {data.get('respuesta')}")
        print(f"\n📊 Datos raw: {data.get('datos_raw')}")
        print(f"\n🔍 SQL generado:")
        print(f"   {data.get('sql_generado')}")
        
        # Verificar que NO sea JSON crudo
        respuesta = data.get('respuesta', '')
        if respuesta.startswith('Resultado:') or '[{' in respuesta:
            print("\n❌ ERROR: La respuesta sigue siendo JSON crudo, NO narrativa")
        else:
            print("\n✅ ÉXITO: Respuesta es narrativa, no JSON")
    else:
        print(f"❌ Error HTTP {response.status_code}")
        print(f"   {response.text}")
        
except Exception as e:
    print(f"❌ Error en request: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Pregunta de rentabilidad
print("\n" + "="*80)
print("TEST 2: ¿Cuál es la rentabilidad de este mes?")
print("="*80)

try:
    response = requests.post(
        f"{BASE_URL}/api/cfo/ask",
        json={"pregunta": "¿Cuál es la rentabilidad de este mes?"},
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Status: {data.get('status')}")
        print(f"📝 Respuesta narrativa:")
        print(f"   {data.get('respuesta')}")
        
        respuesta = data.get('respuesta', '')
        if respuesta.startswith('Resultado:') or '[{' in respuesta:
            print("\n❌ ERROR: La respuesta sigue siendo JSON crudo")
        else:
            print("\n✅ ÉXITO: Respuesta es narrativa")
    else:
        print(f"❌ Error HTTP {response.status_code}")
        print(f"   {response.text}")
        
except Exception as e:
    print(f"❌ Error en request: {e}")

# Test 3: Pregunta compleja
print("\n" + "="*80)
print("TEST 3: ¿Cómo venimos este mes?")
print("="*80)

try:
    response = requests.post(
        f"{BASE_URL}/api/cfo/ask",
        json={"pregunta": "¿Cómo venimos este mes?"},
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Status: {data.get('status')}")
        print(f"📝 Respuesta narrativa:")
        print(f"   {data.get('respuesta')}")
        
        respuesta = data.get('respuesta', '')
        if respuesta.startswith('Resultado:') or '[{' in respuesta:
            print("\n❌ ERROR: La respuesta sigue siendo JSON crudo")
        else:
            print("\n✅ ÉXITO: Respuesta es narrativa")
    else:
        print(f"❌ Error HTTP {response.status_code}")
        print(f"   {response.text}")
        
except Exception as e:
    print(f"❌ Error en request: {e}")

print("\n" + "="*80)
print("🎉 TESTS COMPLETADOS")
print("="*80)
print("\n💡 Revisar los logs del servidor para ver los mensajes de diagnóstico detallados")
print("   Los logs mostrarán:")
print("   - Si la API key está cargada")
print("   - Si Claude responde")
print("   - Dónde falla si hay error")

