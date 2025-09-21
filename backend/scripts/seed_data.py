import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine, Base
from app.models import Area, Socio

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

def seed_areas():
    db = SessionLocal()
    try:
        # Verificar si ya hay áreas
        if db.query(Area).count() > 0:
            print("✓ Áreas ya existen")
            return
        
        areas = [
            Area(nombre="Jurídica", descripcion="Servicios jurídicos"),
            Area(nombre="Notarial", descripcion="Servicios notariales"),
            Area(nombre="Contable", descripcion="Servicios contables"),
            Area(nombre="Recuperación", descripcion="Recuperación de deudas"),
            Area(nombre="Gastos Generales", descripcion="Gastos operativos generales")
        ]
        
        db.add_all(areas)
        db.commit()
        print(f"✓ {len(areas)} áreas creadas")
    finally:
        db.close()

def seed_socios():
    db = SessionLocal()
    try:
        # Verificar si ya hay socios
        if db.query(Socio).count() > 0:
            print("✓ Socios ya existen")
            return
        
        socios = [
            Socio(nombre="Agustina", porcentaje_participacion=20.00),
            Socio(nombre="Viviana", porcentaje_participacion=20.00),
            Socio(nombre="Gonzalo", porcentaje_participacion=20.00),
            Socio(nombre="Pancho", porcentaje_participacion=20.00),
            Socio(nombre="Bruno", porcentaje_participacion=20.00)
        ]
        
        db.add_all(socios)
        db.commit()
        print(f"✓ {len(socios)} socios creados")
    finally:
        db.close()

if __name__ == "__main__":
    print("Iniciando seeds...")
    seed_areas()
    seed_socios()
    print("✓ Seeds completados")
