#!/usr/bin/env python3
"""
Test de fallback de IA - Verifica que AIOrchestrator funciona
Ejecutar: python scripts/test_ai_fallback.py
"""

import sys
import os

# Agregar path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ai.ai_orchestrator import AIOrchestrator

def main():
    print("=" * 60)
    print("TEST DE FALLBACK DE IA")
    print("=" * 60)
    
    # 1. Crear orchestrator
    print("\n1. Inicializando AIOrchestrator...")
    orchestrator = AIOrchestrator()
    
    # 2. Mostrar proveedores disponibles
    providers = orchestrator.get_available_providers()
    print(f"\n2. Proveedores disponibles: {providers}")
    
    if not providers:
        print("❌ ERROR: Ningún proveedor configurado")
        return
    
    # 3. Test de llamada simple
    print("\n3. Probando llamada simple...")
    prompt = "Responde solo con 'OK' si funcionas correctamente."
    
    response = orchestrator.complete(
        prompt=prompt,
        max_tokens=10,
        temperature=0.0
    )
    
    if response:
        print(f"✅ Respuesta recibida: {response[:50]}...")
        print("\n✅ FALLBACK FUNCIONANDO CORRECTAMENTE")
    else:
        print("❌ ERROR: No se recibió respuesta")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()



