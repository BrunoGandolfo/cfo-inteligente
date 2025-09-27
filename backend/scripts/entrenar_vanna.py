#!/usr/bin/env python3
"""
Script de entrenamiento de Vanna AI con los datos reales
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import vanna
from vanna.remote import VannaDefault

# Configuración
DB_CONNECTION = "postgresql://cfo_user:cfo_password@localhost:5432/cfo_inteligente"

print("=== ENTRENAMIENTO DE VANNA AI ===")
print("Configurando Vanna con los datos de Conexión Consultora")
print("-" * 50)

# Inicializar Vanna con modelo local (sin API key por ahora)
vn = VannaDefault(model='conexion-cfo', api_key='demo')
vn.connect_to_postgres(host='localhost', dbname='cfo_inteligente', user='cfo_user', password='cfo_password', port=5432)

print("✓ Conexión a PostgreSQL establecida")

# PASO 1: Entrenar con la estructura de tablas
print("\n1. ENTRENANDO ESTRUCTURA DE TABLAS...")

ddl_operaciones = """
CREATE TABLE operaciones (
    id UUID PRIMARY KEY,
    tipo_operacion VARCHAR(20) CHECK (tipo_operacion IN ('INGRESO', 'GASTO', 'RETIRO', 'DISTRIBUCION')),
    fecha DATE NOT NULL,
    monto_original NUMERIC(15,2),
    moneda_original VARCHAR(3),
    tipo_cambio NUMERIC(10,4),
    monto_uyu NUMERIC(15,2),
    monto_usd NUMERIC(15,2),
    area_id UUID REFERENCES areas(id),
    localidad VARCHAR(50),
    cliente VARCHAR(200),
    proveedor VARCHAR(200)
);
"""

vn.train(ddl=ddl_operaciones)
print("✓ Tabla operaciones entrenada")
