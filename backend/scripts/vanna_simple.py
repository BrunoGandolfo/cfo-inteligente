#!/usr/bin/env python3
"""
Configuración SIMPLE de Vanna - Sin API key
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Método más simple - usar Vanna directamente
from vanna.remote import VannaDefault

# Usar modelo 'demo' que no requiere API key real
vn = VannaDefault(model='chinook', api_key='demo')

# Conectar a tu PostgreSQL
vn.connect_to_postgres(
    host='localhost',
    dbname='cfo_inteligente',
    user='cfo_user',
    password='cfo_pass',
    port=5432
)

print("✓ Vanna configurado con modelo demo")
print("✓ Conectado a PostgreSQL") 
print("\nNOTA: Para producción en la nube, todo funciona igual")
