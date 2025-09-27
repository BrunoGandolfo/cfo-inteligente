#!/usr/bin/env python3
"""
Script para generar 600+ operaciones con alta variedad
para entrenar Vanna AI efectivamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Areas por tipo de operación
AREAS_INGRESO = {
    "d3aff49c-748c-4d1d-bc47-cdda1cfb913d": "Jurídica",
    "53ba7821-8836-4e74-ad56-a288d290881d": "Notarial", 
    "14700c01-3b3d-49c6-8e2e-f3ebded1b1bb": "Contable",
    "11c64c64-c7f6-4e85-9c26-b577c3d7a5b7": "Recuperación",
    "651dfb5c-15d8-41e2-8339-785b137f44f2": "Otros"
}

AREAS_GASTO = {
    "d3aff49c-748c-4d1d-bc47-cdda1cfb913d": "Jurídica",
    "53ba7821-8836-4e74-ad56-a288d290881d": "Notarial",
    "14700c01-3b3d-49c6-8e2e-f3ebded1b1bb": "Contable",
    "11c64c64-c7f6-4e85-9c26-b577c3d7a5b7": "Recuperación",
    "b11006d3-6cfc-4766-9201-ab56274401a6": "Gastos Generales"
}

AREA_RETIRO_DISTRIBUCION = "b11006d3-6cfc-4766-9201-ab56274401a6"

# 50+ clientes variados
CLIENTES = [
    # Empresas constructoras
    "Constructora Silva SA", "Edificaciones del Sur", "Obras y Proyectos SRL",
    "Construcciones Modernas", "Grupo Constructor Oriental",
    # Estudios jurídicos
    "Estudio Jurídico González", "Bufete Rodríguez & Asoc", "Estudio Legal Martínez",
    "Abogados Unidos", "Estudio Pérez y Socios",
    # Inmobiliarias
    "Inmobiliaria del Este", "Propiedades del Centro", "Inmobiliaria Costa",
    "Remax Uruguay", "Century 21 Montevideo",
    # Comercios
    "Comercio López Hnos", "Supermercado El Dorado", "Farmacia Nueva",
    "Ferretería Industrial", "Tienda La Española",
    # Empresas varias
    "Importadora Sur", "Exportadora Nacional", "Distribuidora Central",
    "Logística Express", "Transporte Seguro SA",
    # Fábricas
    "Fábrica Nacional", "Industrias Reunidas", "Manufactura UY",
    "Plásticos del Uruguay", "Metalúrgica San José",
    # Servicios profesionales
    "Consultora Internacional", "Asesoría Empresarial", "Marketing Digital UY",
    "Desarrollo Web Solutions", "Consultoría Estratégica",
    # Cooperativas
    "Cooperativa Local", "Cooperativa Agraria", "Cooperativa de Ahorro",
    "Cooperativa de Vivienda", "Cooperativa de Consumo",
    # Particulares
    "Juan Pérez", "María García", "Carlos Rodríguez", "Ana Martínez",
    "Luis Fernández", "Patricia López", "Roberto Díaz", "Claudia Silva"
]

# 50+ proveedores
PROVEEDORES = [
    # Servicios públicos
    "DGI", "BPS", "UTE", "OSE", "ANTEL", "Intendencia de Montevideo",
    "Intendencia de Soriano", "MTSS", "MEF", "MGAP",
    # Servicios oficina
    "Papelería Central", "Librería Universitaria", "Office Max",
    "Insumos de Oficina", "Papelería del Centro",
    # Limpieza y mantenimiento
    "Limpieza Express", "Servicios de Limpieza Total", "Mantenimiento Integral",
    "Limpieza Profesional", "Higiene y Servicios",
    # Seguridad
    "Seguridad Total", "Prosegur Uruguay", "G4S", "Securitas",
    "Vigilancia Privada del Este",
    # IT y tecnología
    "Mantenimiento IT", "Soporte Técnico 24/7", "Soluciones Informáticas",
    "Hardware & Software SA", "Reparación PC",
    # Alquileres
    "Alquiler Oficina Centro", "Inmuebles Comerciales", "Alquiler Mercedes",
    "Propiedades Comerciales", "Alquileres Montevideo",
    # Profesionales
    "Contador Pérez", "Estudio Contable García", "Escribano Rodríguez",
    "Arquitecto Martínez", "Ingeniero López",
    # Proveedores varios
    "Imprenta Nacional", "Gráfica Oriental", "Publicidad Creativa",
    "Marketing y Diseño", "Comunicación Visual",
    # Transporte
    "Taxi Company", "Uber Empresarial", "Remises VIP",
    "Transporte de Carga", "Mudanzas Express",
    # Otros servicios
    "Cafetería Central", "Restaurant Ejecutivo", "Catering Service",
    "Agua Mineral", "Café & Té Premium"
]

print(f"Base de datos preparada:")
print(f"- {len(CLIENTES)} clientes diferentes")
print(f"- {len(PROVEEDORES)} proveedores diferentes")
print(f"- Generaremos 600 operaciones mínimo")

from datetime import date, timedelta
from decimal import Decimal
import random
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.operacion import Operacion, TipoOperacion, Moneda, Localidad
from app.services.operacion_service import crear_ingreso, crear_gasto, crear_retiro, crear_distribucion
from app.schemas.operacion import IngresoCreate, GastoCreate, RetiroCreate, DistribucionCreate

def generar_tipo_cambio(fecha):
    """Genera tipo de cambio realista basado en fecha"""
    base = 39.5
    # Variación pequeña por día
    dias_desde_inicio = (fecha - date(2025, 1, 1)).days
    variacion = random.uniform(-0.02, 0.02) * (dias_desde_inicio % 30)
    return Decimal(str(round(base + variacion, 2)))

def generar_operaciones():
    """Genera 600+ operaciones variadas"""
    db = SessionLocal()
    contador = {
        'ingresos': 0,
        'gastos': 0,
        'retiros': 0,
        'distribuciones': 0
    }
    
    try:
        fecha_inicio = date.today() - timedelta(days=180)  # 6 meses atrás
        
        print(f"\nIniciando generación desde {fecha_inicio}")
        print("-" * 50)
        
        # Generar operaciones día por día
        for dias in range(180):
            fecha_actual = fecha_inicio + timedelta(days=dias)
            tipo_cambio = generar_tipo_cambio(fecha_actual)
            
            # 3-5 operaciones por día (promedio)
            operaciones_dia = random.randint(2, 6)
            
            for _ in range(operaciones_dia):
                tipo = random.choices(
                    ['ingreso', 'gasto', 'retiro', 'distribucion'],
                    weights=[40, 35, 15, 10]  # Proporción realista
                )[0]
                
                localidad = random.choice(['Montevideo', 'Mercedes'])
                
                if tipo == 'ingreso':
                    # Generar ingreso
                    area_id = random.choice(list(AREAS_INGRESO.keys()))
                    moneda = random.choice(['UYU', 'USD'])
                    monto = Decimal(str(random.randint(5000, 500000) if moneda == 'UYU' else random.randint(100, 10000)))
                    
                    contador['ingresos'] += 1
                    print(f"Generando ingreso #{contador['ingresos']}", end='\r')
                
                elif tipo == 'gasto':
                    # Generar gasto
                    area_id = random.choice(list(AREAS_GASTO.keys()))
                    moneda = random.choice(['UYU', 'USD'])
                    monto = Decimal(str(random.randint(2000, 200000) if moneda == 'UYU' else random.randint(50, 5000)))
                    
                    contador['gastos'] += 1
                    print(f"Generando gasto #{contador['gastos']}", end='\r')
                
                elif tipo == 'retiro':
                    # Generar retiro (puede ser UYU, USD o ambos)
                    monto_uyu = None
                    monto_usd = None
                    if random.random() > 0.3:  # 70% tiene UYU
                        monto_uyu = Decimal(str(random.randint(10000, 100000)))
                    if random.random() > 0.5:  # 50% tiene USD
                        monto_usd = Decimal(str(random.randint(200, 2000)))
                    
                    contador['retiros'] += 1
                    print(f"Generando retiro #{contador['retiros']}", end='\r')
                
                else:  # distribucion
                    # Generar distribución entre socios
                    total_uyu = Decimal(str(random.randint(50000, 300000)))
                    total_usd = Decimal(str(random.randint(1000, 8000)))
                    
                    # Distribuir entre los 5 socios (proporciones aleatorias)
                    porcentajes = [random.uniform(0.15, 0.25) for _ in range(5)]
                    suma = sum(porcentajes)
                    porcentajes = [p/suma for p in porcentajes]  # Normalizar a 100%
                    
                    contador['distribuciones'] += 1
                    print(f"Generando distribución #{contador['distribuciones']}", end='\r')
        
        print("\n" + "=" * 50)
        print(f"RESUMEN DE GENERACIÓN:")
        print(f"- Ingresos: {contador['ingresos']}")
        print(f"- Gastos: {contador['gastos']}")
        print(f"- Retiros: {contador['retiros']}")
        print(f"- Distribuciones: {contador['distribuciones']}")
        print(f"- TOTAL: {sum(contador.values())}")
        
    finally:
        db.close()

if __name__ == "__main__":
    generar_operaciones()
