#!/usr/bin/env python3
"""
Test directo de Claude Sonnet 4.5 para diagnosticar problemas de conexión
"""

import os
import sys
import json
from dotenv import load_dotenv
import anthropic

# Cargar variables de entorno
print("="*80)
print("🧪 TEST DIRECTO DE CLAUDE SONNET 4.5")
print("="*80 + "\n")

# Cargar .env desde el directorio backend
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(backend_dir, '.env')
print(f"📁 Buscando .env en: {env_path}")
print(f"   Existe: {os.path.exists(env_path)}")

load_dotenv(env_path)

# Verificar API Key
api_key = os.getenv("ANTHROPIC_API_KEY")
print(f"\n🔑 API Key Configuration:")
print(f"   Presente: {bool(api_key)}")

if not api_key:
    print("\n❌ ERROR CRÍTICO: ANTHROPIC_API_KEY no encontrada")
    print("\n📝 SOLUCIÓN:")
    print("   1. Crear archivo backend/.env con:")
    print("      ANTHROPIC_API_KEY=tu_api_key_aqui")
    print("   2. O exportar en terminal:")
    print("      export ANTHROPIC_API_KEY=tu_api_key_aqui")
    sys.exit(1)

print(f"   Primeros 10 chars: {api_key[:10]}...")
print(f"   Longitud: {len(api_key)}")
print(f"   Formato válido: {api_key.startswith('sk-ant-')}")

# Inicializar cliente
try:
    print("\n🚀 Inicializando cliente Anthropic...")
    client = anthropic.Anthropic(api_key=api_key)
    print("✅ Cliente inicializado correctamente")
except Exception as e:
    print(f"❌ Error al inicializar cliente: {e}")
    sys.exit(1)

# Test 1: Mensaje simple
print("\n" + "="*80)
print("TEST 1: Mensaje Simple")
print("="*80)

try:
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": "Di 'Hola' en español"
        }]
    )
    print("✅ Respuesta recibida:")
    print(f"   {message.content[0].text}")
except Exception as e:
    print(f"❌ Error en test simple: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Generación de narrativa financiera (caso real)
print("\n" + "="*80)
print("TEST 2: Narrativa Financiera (Caso Real)")
print("="*80)

try:
    datos_ejemplo = [{"count": 106}]
    pregunta = "¿Cuántos retiros hicimos este año?"
    sql = "SELECT COUNT(*) as count FROM operaciones WHERE tipo_operacion = 'RETIRO' AND EXTRACT(YEAR FROM fecha) = 2025"
    
    datos_texto = json.dumps(datos_ejemplo, indent=2, ensure_ascii=False)
    
    prompt = f"""Eres el CFO AI de Conexión Consultora, una consultora en Uruguay.

Pregunta del usuario: {pregunta}

Datos obtenidos de la base de datos:
{datos_texto}

SQL ejecutado:
{sql}

INSTRUCCIONES:
- Genera una respuesta clara, profesional y útil en español rioplatense
- Destaca el dato principal de manera conversacional
- Sé conciso (2-4 líneas máximo)
- Usa formato narrativo, NO JSON ni formato técnico

Genera SOLO la respuesta, sin preámbulos ni explicaciones adicionales."""

    print("📤 Enviando prompt a Claude...")
    
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=250,
        messages=[{"role": "user", "content": prompt}]
    )
    
    respuesta = message.content[0].text
    print("✅ Narrativa generada exitosamente:")
    print(f"\n   📝 {respuesta}\n")
    
except Exception as e:
    print(f"❌ Error en test de narrativa: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Otro caso real - Rentabilidad
print("\n" + "="*80)
print("TEST 3: Narrativa de Rentabilidad")
print("="*80)

try:
    datos_ejemplo = [{"rentabilidad": 33.47}]
    pregunta = "¿Cuál es la rentabilidad de octubre?"
    
    datos_texto = json.dumps(datos_ejemplo, indent=2, ensure_ascii=False)
    
    prompt = f"""Eres el CFO AI de Conexión Consultora, una consultora en Uruguay.

Pregunta del usuario: {pregunta}

Datos obtenidos de la base de datos:
{datos_texto}

INSTRUCCIONES:
- Genera una respuesta clara, profesional y útil en español rioplatense
- Destaca el dato principal de manera conversacional
- Si es un porcentaje, redondea a 2 decimales
- Sé conciso (2-4 líneas máximo)
- Usa formato narrativo, NO JSON ni formato técnico

Genera SOLO la respuesta, sin preámbulos ni explicaciones adicionales."""

    print("📤 Enviando prompt a Claude...")
    
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=250,
        messages=[{"role": "user", "content": prompt}]
    )
    
    respuesta = message.content[0].text
    print("✅ Narrativa generada exitosamente:")
    print(f"\n   📝 {respuesta}\n")
    
except Exception as e:
    print(f"❌ Error en test de rentabilidad: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("🎉 TESTS COMPLETADOS")
print("="*80)
print("\n✅ Si todos los tests pasaron, Claude está funcionando correctamente")
print("✅ El problema puede estar en la carga del .env en el servidor FastAPI")
print("\n💡 Próximos pasos:")
print("   1. Verificar que backend/.env existe y contiene ANTHROPIC_API_KEY")
print("   2. Reiniciar el servidor FastAPI: uvicorn app.main:app --reload")
print("   3. Revisar logs del servidor al hacer una pregunta")
print("   4. Los nuevos logs detallados mostrarán dónde falla exactamente")

