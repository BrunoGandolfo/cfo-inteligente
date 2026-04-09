#!/usr/bin/env python3
"""
Script para verificar leyes en producción y sus URLs de IMPO.

Ejecuta consulta SQL y verifica si las URLs devuelven JSON válido.
"""
import os
import sys
import json
import requests
from typing import List, Dict, Any

# Agregar path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# URL de producción Railway (usar variable de entorno si está disponible)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:NLlXASvwKuOHCUsDpdUWcojpPDUDLmzx@shortline.proxy.rlwy.net:50827/railway"
)

def ejecutar_consulta() -> List[Dict[str, Any]]:
    """Ejecuta la consulta SQL en producción."""
    print("🔌 Conectando a base de datos de producción...")
    engine = create_engine(DATABASE_URL)
    
    query = text("""
        SELECT numero, anio, tiene_texto, url_impo 
        FROM leyes 
        WHERE numero IN (19575, 16827, 18719, 17930)
        ORDER BY numero;
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query)
        rows = []
        for row in result:
            rows.append({
                'numero': row.numero,
                'anio': row.anio,
                'tiene_texto': row.tiene_texto,
                'url_impo': row.url_impo
            })
        return rows

def verificar_url_json(url: str) -> Dict[str, Any]:
    """
    Verifica si una URL con ?json=true devuelve JSON válido o HTML.
    
    Returns:
        Dict con 'es_json', 'status_code', 'error' (si hay)
    """
    if not url:
        return {
            'es_json': False,
            'status_code': None,
            'error': 'URL vacía'
        }
    
    # Agregar ?json=true si no está presente
    if '?json=true' not in url:
        if '?' in url:
            url = f"{url}&json=true"
        else:
            url = f"{url}?json=true"
    
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        
        # Verificar Content-Type
        content_type = response.headers.get('Content-Type', '').lower()
        es_json_header = 'application/json' in content_type
        
        # Intentar parsear como JSON
        es_json_valido = False
        try:
            json.loads(response.text)
            es_json_valido = True
        except (json.JSONDecodeError, ValueError):
            es_json_valido = False
        
        # Verificar si es HTML
        es_html = response.text.strip().startswith('<!') or '<html' in response.text.lower()
        
        return {
            'es_json': es_json_valido,
            'es_json_header': es_json_header,
            'es_html': es_html,
            'status_code': response.status_code,
            'content_type': content_type,
            'tamaño_respuesta': len(response.text),
            'error': None
        }
    except requests.exceptions.RequestException as e:
        return {
            'es_json': False,
            'status_code': None,
            'error': str(e)
        }

def main():
    print("=" * 80)
    print("VERIFICACIÓN DE LEYES - IMPO JSON")
    print("=" * 80)
    print()
    
    # Ejecutar consulta
    try:
        leyes = ejecutar_consulta()
        print(f"✅ Consulta ejecutada: {len(leyes)} leyes encontradas")
        print()
    except Exception as e:
        print(f"❌ Error al ejecutar consulta: {e}")
        print(f"   Tipo: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return
    
    if not leyes:
        print("⚠️  No se encontraron leyes con esos números")
        return
    
    # Mostrar resultados de la consulta
    print("RESULTADOS DE LA CONSULTA:")
    print("-" * 80)
    for ley in leyes:
        print(f"Ley {ley['numero']}/{ley['anio']}: tiene_texto={ley['tiene_texto']}, url={ley['url_impo']}")
    print()
    
    # Verificar URLs para las que tienen_texto = false
    leyes_sin_texto = [l for l in leyes if not l['tiene_texto']]
    
    if not leyes_sin_texto:
        print("✅ Todas las leyes tienen tiene_texto=true, no hay URLs que verificar")
        return
    
    print(f"🔍 Verificando {len(leyes_sin_texto)} URLs con tiene_texto=false...")
    print()
    
    resultados_verificacion = []
    
    for ley in leyes_sin_texto:
        print(f"Ley {ley['numero']}/{ley['anio']}:")
        print(f"  URL: {ley['url_impo']}")
        
        resultado = verificar_url_json(ley['url_impo'])
        resultados_verificacion.append({
            'ley': ley,
            'verificacion': resultado
        })
        
        if resultado['error']:
            print(f"  ❌ Error: {resultado['error']}")
        elif resultado['es_json']:
            print(f"  ✅ Devuelve JSON válido (Status: {resultado['status_code']}, Tamaño: {resultado['tamaño_respuesta']} bytes)")
        elif resultado['es_html']:
            print(f"  ⚠️  Devuelve HTML (Status: {resultado['status_code']}, Tamaño: {resultado['tamaño_respuesta']} bytes)")
        else:
            print(f"  ⚠️  No es JSON ni HTML claro (Status: {resultado['status_code']}, Content-Type: {resultado['content_type']})")
        
        print()
    
    # Resumen
    print("=" * 80)
    print("RESUMEN:")
    print("-" * 80)
    
    json_validos = sum(1 for r in resultados_verificacion if r['verificacion']['es_json'])
    html_respuestas = sum(1 for r in resultados_verificacion if r['verificacion']['es_html'])
    errores = sum(1 for r in resultados_verificacion if r['verificacion']['error'])
    
    print(f"Total leyes verificadas: {len(resultados_verificacion)}")
    print(f"✅ JSON válido: {json_validos}")
    print(f"⚠️  HTML: {html_respuestas}")
    print(f"❌ Errores: {errores}")
    print()
    
    # Detalle por ley
    print("DETALLE POR LEY:")
    print("-" * 80)
    for r in resultados_verificacion:
        ley = r['ley']
        ver = r['verificacion']
        estado = "✅ JSON" if ver['es_json'] else ("⚠️ HTML" if ver['es_html'] else "❌ Error")
        status_info = ver.get('error') or f"Status {ver.get('status_code', 'N/A')}"
        print(f"Ley {ley['numero']}/{ley['anio']}: {estado} - {status_info}")

if __name__ == "__main__":
    main()
