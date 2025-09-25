#!/usr/bin/env python3
"""
Configuración de Vanna Open Source - Sin API key
Funcionará igual en desarrollo y en la nube
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import vanna as vn
from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore

# Configurar Vanna con ChromaDB local (sin API key)
class VannaLocal(ChromaDB_VectorStore):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)

# Crear instancia de Vanna local
vanna_config = {'path': './chroma_db'}
my_vanna = VannaLocal(config=vanna_config)

# Configurar conexión a PostgreSQL
db_config = {
    'host': 'localhost',
    'dbname': 'cfo_inteligente', 
    'user': 'cfo_user',
    'password': 'cfo_password',
    'port': 5432
}

print("✓ Vanna Open Source configurado")
print("✓ ChromaDB local en ./chroma_db")
print("✓ Listo para entrenar con tus datos")
print("\nEsto funcionará IGUAL en la nube")
