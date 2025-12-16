#!/usr/bin/env python3
"""
Lista modelos disponibles en OpenAI y Gemini
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def listar_openai():
    print("\n" + "=" * 50)
    print("MODELOS OPENAI DISPONIBLES")
    print("=" * 50)
    
    if not settings.openai_api_key:
        print("❌ OPENAI_API_KEY no configurada")
        return
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key.strip())
        models = client.models.list()
        
        # Filtrar solo modelos de chat/completions
        chat_models = [m.id for m in models.data if 'gpt' in m.id.lower()]
        chat_models.sort()
        
        print(f"Encontrados {len(chat_models)} modelos GPT:")
        for model in chat_models[:15]:  # Mostrar primeros 15
            print(f"  - {model}")
        
        if len(chat_models) > 15:
            print(f"  ... y {len(chat_models) - 15} más")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def listar_gemini():
    print("\n" + "=" * 50)
    print("MODELOS GEMINI DISPONIBLES")
    print("=" * 50)
    
    if not settings.google_ai_key:
        print("❌ GOOGLE_AI_KEY no configurada")
        return
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.google_ai_key.strip())
        
        models = genai.list_models()
        
        # Filtrar modelos que soportan generateContent
        gen_models = [m.name for m in models if 'generateContent' in [method.name for method in m.supported_generation_methods]]
        
        print(f"Encontrados {len(gen_models)} modelos para generación:")
        for model in gen_models:
            print(f"  - {model}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    listar_openai()
    listar_gemini()
    print("\n" + "=" * 50)



