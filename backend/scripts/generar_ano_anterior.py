#!/usr/bin/env python3
"""
Generar datos del año 2024 completo para comparaciones año contra año
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, timedelta
from decimal import Decimal
import random
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.operacion import Operacion, TipoOperacion, Moneda, Localidad
from app.services.operacion_service import crear_ingreso, crear_gasto, crear_retiro, crear_distribucion
from app.schemas.operacion import IngresoCreate, GastoCreate, RetiroCreate, DistribucionCreate

print("=== GENERANDO AÑO 2024 COMPLETO ===")
print("Para poder hacer comparaciones año contra año")
print("-" * 50)

# Generar desde enero 2024 hasta diciembre 2024
fecha_inicio = date(2024, 1, 1)
fecha_fin = date(2024, 12, 31)

print(f"Generando desde {fecha_inicio} hasta {fecha_fin}")
