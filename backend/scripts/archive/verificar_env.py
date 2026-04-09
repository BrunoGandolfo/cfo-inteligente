#!/usr/bin/env python3
"""
Verifica la configuración del archivo .env
"""

import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(backend_dir, '.env')

print("="*80)
print("🔍 VERIFICACIÓN DE CONFIGURACIÓN .env")
print("="*80 + "\n")

print(f"📁 Ruta backend: {backend_dir}")
print(f"📄 Ruta .env esperada: {env_path}")
print(f"📋 Archivo existe: {os.path.exists(env_path)}\n")

if os.path.exists(env_path):
    print("✅ Archivo .env encontrado\n")
    print("📋 Contenido (sin valores sensibles):")
    print("-"*80)
    
    with open(env_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    # Ocultar valores sensibles
                    if 'KEY' in key or 'PASSWORD' in key or 'SECRET' in key:
                        masked_value = value[:10] + '...' if len(value) > 10 else '***'
                        print(f"  {key}={masked_value} (longitud: {len(value)})")
                    else:
                        print(f"  {key}={value}")
                else:
                    print(f"  {line}")
            elif line.startswith('#'):
                print(f"  {line}")
    
    print("-"*80 + "\n")
    
    # Cargar y verificar variables específicas
    from dotenv import load_dotenv
    load_dotenv(env_path)
    
    print("🔑 Variables críticas:")
    critical_vars = [
        'ANTHROPIC_API_KEY',
        'OPENAI_API_KEY',
        'DATABASE_URL',
        'POSTGRES_USER',
        'POSTGRES_PASSWORD'
    ]
    
    for var in critical_vars:
        value = os.getenv(var)
        if value:
            if len(value) > 10:
                print(f"  ✅ {var}: Configurada ({len(value)} chars)")
            else:
                print(f"  ⚠️  {var}: Configurada pero sospechosamente corta ({len(value)} chars)")
        else:
            print(f"  ❌ {var}: NO CONFIGURADA")
    
    print("\n" + "="*80)
    print("✅ Verificación completada")
    print("="*80)
    
else:
    print("❌ Archivo .env NO ENCONTRADO\n")
    print("📝 SOLUCIÓN:")
    print("="*80)
    print("Crear el archivo backend/.env con el siguiente contenido:\n")
    print("""# API Keys
ANTHROPIC_API_KEY=sk-ant-api03-tu_key_aqui
OPENAI_API_KEY=sk-tu_key_aqui

# Database (reemplazar con credenciales reales)
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=cfo_inteligente
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
""")
    print("="*80)
    
    # Intentar crear archivo .env template
    response = input("\n¿Deseas crear un archivo .env template ahora? (s/n): ")
    if response.lower() == 's':
        try:
            with open(env_path, 'w') as f:
                f.write("""# API Keys para IA
ANTHROPIC_API_KEY=sk-ant-api03-REEMPLAZAR_CON_TU_KEY
OPENAI_API_KEY=sk-REEMPLAZAR_CON_TU_KEY

# Database PostgreSQL (reemplazar con credenciales reales)
DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/cfo_inteligente
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=cfo_inteligente
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Configuración adicional
ENVIRONMENT=development
""")
            print(f"\n✅ Archivo .env template creado en: {env_path}")
            print("⚠️  IMPORTANTE: Edita el archivo y reemplaza las API keys con las reales")
        except Exception as e:
            print(f"\n❌ Error al crear .env: {e}")

