#!/usr/bin/env python3
"""
Vanna con OpenAI GPT-3.5 - Cargando .env correctamente
"""
import os
import sys
from dotenv import load_dotenv

# CARGAR .env en las variables de entorno
load_dotenv()

from vanna.chromadb import ChromaDB_VectorStore
from vanna.openai import OpenAI_Chat

class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY no encontrada en .env")
        OpenAI_Chat.__init__(self, config={'api_key': api_key, 'model': 'gpt-3.5-turbo'})

# Ruta absoluta al ChromaDB (siempre /backend/chroma_db)
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_PATH = os.path.join(BACKEND_DIR, 'chroma_db')

my_vanna = MyVanna(config={'path': CHROMA_PATH})
