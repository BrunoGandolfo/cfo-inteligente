from datetime import date
#!/usr/bin/env python3
"""
Script completo para generar 600+ operaciones reales en la BD
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

# Areas por tipo
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

print("Script de generación - versión completa")

# Clientes variados (30+)
CLIENTES = [
    "Constructora Silva SA", "Estudio Jurídico González", "Inmobiliaria del Este",
    "Comercio López Hnos", "Importadora Sur", "Consultora Internacional",
    "Grupo Empresarial XYZ", "Cooperativa Local", "Fábrica Nacional",
    "Distribuidora Central", "Logística Express", "Transporte Seguro SA",
    "Juan Pérez", "María García", "Carlos Rodríguez", "Ana Martínez",
    "Empresa ABC", "Servicios Profesionales", "Comercio Exterior SRL",
    "Industrias Reunidas", "Cooperativa Agraria", "Estudio Contable Sur",
    "Inmobiliaria Costa", "Remax Uruguay", "Century 21", "Propiedades del Centro",
    "Supermercado El Dorado", "Farmacia Nueva", "Ferretería Industrial"
]

# Proveedores variados (30+)
PROVEEDORES = [
    "DGI", "BPS", "UTE", "OSE", "ANTEL", "Intendencia de Montevideo",
    "Papelería Central", "Limpieza Express", "Seguridad Total", 
    "Mantenimiento IT", "Alquiler Oficina", "Contador Pérez",
    "Escribano Rodríguez", "Imprenta Nacional", "Gráfica Oriental",
    "Prosegur Uruguay", "G4S", "Securitas", "Vigilancia Privada",
    "Soporte Técnico 24/7", "Hardware & Software SA", "Reparación PC",
    "Cafetería Central", "Restaurant Ejecutivo", "Agua Mineral",
    "Taxi Company", "Uber Empresarial", "Remises VIP", "Mudanzas Express"
]

def generar_tipo_cambio(fecha):
    """Genera tipo de cambio realista basado en fecha"""
    base = 39.75  # Promedio actual
    dias_desde_inicio = (fecha - date(2025, 1, 1)).days
    variacion = random.uniform(-0.5, 0.5)  # Variación de +/- 0.50
    return Decimal(str(round(base + variacion, 2)))

def generar_operaciones():
    """Genera 600+ operaciones variadas"""
    db = SessionLocal()
    contador = {'ingresos': 0, 'gastos': 0, 'retiros': 0, 'distribuciones': 0}
    errores = []
    
    try:
        fecha_inicio = date(2024, 1, 1)  # 6 meses
        print(f"\nIniciando generación desde {fecha_inicio}")
        print("-" * 50)
        
        # Generar operaciones día por día
        for dias in range(365):
            fecha_actual = fecha_inicio + timedelta(days=dias)
            tipo_cambio = generar_tipo_cambio(fecha_actual)
            
            # 3-5 operaciones por día
            operaciones_dia = random.randint(3, 5)
            
            for _ in range(operaciones_dia):
                tipo = random.choices(
                    ['ingreso', 'gasto', 'retiro', 'distribucion'],
                    weights=[40, 35, 15, 10]
                )[0]
                
                localidad = random.choice(['Montevideo', 'Mercedes'])
                
                try:
                    if tipo == 'ingreso':
                        area_id = random.choice(list(AREAS_INGRESO.keys()))
                        ingreso = IngresoCreate(
                            fecha=fecha_actual,
                            tipo_cambio=tipo_cambio,
                            localidad=localidad,
                            monto_original=Decimal(str(random.randint(10000, 500000))),
                            moneda_original='UYU' if random.random() > 0.3 else 'USD',
                            area_id=area_id,
                            cliente=random.choice(CLIENTES),
                            descripcion=f"Servicio profesional - {fecha_actual.strftime('%B %Y')}"
                        )
                        crear_ingreso(db, ingreso)
                        contador['ingresos'] += 1
                    
                    elif tipo == 'gasto':
                        area_id = random.choice(list(AREAS_GASTO.keys()))
                        gasto = GastoCreate(
                            fecha=fecha_actual,
                            tipo_cambio=tipo_cambio,
                            localidad=localidad,
                            monto_original=Decimal(str(random.randint(5000, 200000))),
                            moneda_original='UYU' if random.random() > 0.2 else 'USD',
                            area_id=area_id,
                            proveedor=random.choice(PROVEEDORES),
                            descripcion=f"Pago servicios - {fecha_actual.strftime('%B %Y')}"
                        )
                        crear_gasto(db, gasto)
                        contador['gastos'] += 1
                    
                    elif tipo == 'retiro':
                        monto_uyu = None
                        monto_usd = None
                        if random.random() > 0.3:  # 70% tiene UYU
                            monto_uyu = Decimal(str(random.randint(20000, 150000)))
                        if random.random() > 0.5:  # 50% tiene USD
                            monto_usd = Decimal(str(random.randint(500, 3000)))
                        
                        if monto_uyu or monto_usd:  # Solo crear si hay algún monto
                            retiro = RetiroCreate(
                                fecha=fecha_actual,
                                tipo_cambio=tipo_cambio,
                                localidad=localidad,
                                monto_uyu=monto_uyu,
                                monto_usd=monto_usd,
                                descripcion=f"Retiro socios - {fecha_actual.strftime('%B %Y')}"
                            )
                            crear_retiro(db, retiro)
                            contador['retiros'] += 1
                    
                    else:  # distribucion
                        total_uyu = Decimal(str(random.randint(100000, 500000)))
                        total_usd = Decimal(str(random.randint(2000, 10000)))
                        
                        # Distribuir entre los 5 socios (porcentajes aleatorios)
                        porcentajes = [random.uniform(0.15, 0.25) for _ in range(5)]
                        suma = sum(porcentajes)
                        porcentajes = [p/suma for p in porcentajes]  # Normalizar
                        
                        distribucion = DistribucionCreate(
                            fecha=fecha_actual,
                            tipo_cambio=tipo_cambio,
                            localidad=localidad,
                            agustina_uyu=Decimal(str(int(total_uyu * Decimal(str(porcentajes[0]))))),
                            agustina_usd=Decimal(str(int(total_usd * Decimal(str(porcentajes[0]))))),
                            viviana_uyu=Decimal(str(int(total_uyu * Decimal(str(porcentajes[1]))))),
                            viviana_usd=Decimal(str(int(total_usd * Decimal(str(porcentajes[1]))))),
                            gonzalo_uyu=Decimal(str(int(total_uyu * Decimal(str(porcentajes[2]))))),
                            gonzalo_usd=Decimal(str(int(total_usd * Decimal(str(porcentajes[2]))))),
                            pancho_uyu=Decimal(str(int(total_uyu * Decimal(str(porcentajes[3]))))),
                            pancho_usd=Decimal(str(int(total_usd * Decimal(str(porcentajes[3]))))),
                            bruno_uyu=Decimal(str(int(total_uyu * Decimal(str(porcentajes[4]))))),
                            bruno_usd=Decimal(str(int(total_usd * Decimal(str(porcentajes[4])))))
                        )
                        crear_distribucion(db, distribucion)
                        contador['distribuciones'] += 1
                    
                    print(f"Generadas: I:{contador['ingresos']} G:{contador['gastos']} R:{contador['retiros']} D:{contador['distribuciones']}", end='\r')
                    
                except Exception as e:
                    errores.append(f"Error en {tipo}: {str(e)}")
                    continue
        
        # Commit final
        db.commit()
        
        print("\n" + "=" * 50)
        print("RESUMEN DE GENERACIÓN:")
        print(f"- Ingresos: {contador['ingresos']}")
        print(f"- Gastos: {contador['gastos']}")
        print(f"- Retiros: {contador['retiros']}")
        print(f"- Distribuciones: {contador['distribuciones']}")
        print(f"- TOTAL: {sum(contador.values())} operaciones")
        
        if errores:
            print(f"\nErrores encontrados: {len(errores)}")
            for error in errores[:5]:  # Mostrar solo primeros 5
                print(f"  - {error}")
    
    except Exception as e:
        print(f"Error crítico: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    generar_operaciones()
