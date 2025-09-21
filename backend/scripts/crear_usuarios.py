import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models import Usuario
from app.core.security import hash_password

def crear_usuarios():
    db = SessionLocal()
    try:
        # Verificar si ya hay usuarios
        if db.query(Usuario).count() > 0:
            print("✓ Ya existen usuarios")
            return
        
        # 5 SOCIOS (pueden todo)
        socios = [
            Usuario(email="agustina@conexion.uy", nombre="Agustina", password_hash=hash_password("agustina123"), es_socio=True),
            Usuario(email="viviana@conexion.uy", nombre="Viviana", password_hash=hash_password("viviana123"), es_socio=True),
            Usuario(email="gonzalo@conexion.uy", nombre="Gonzalo", password_hash=hash_password("gonzalo123"), es_socio=True),
            Usuario(email="pancho@conexion.uy", nombre="Pancho", password_hash=hash_password("pancho123"), es_socio=True),
            Usuario(email="bruno@conexion.uy", nombre="Bruno", password_hash=hash_password("bruno123"), es_socio=True)
        ]
        
        # 4 OPERADORES (acceso limitado)
        operadores = [
            Usuario(email="operador1@conexion.uy", nombre="Operador 1", password_hash=hash_password("oper123"), es_socio=False),
            Usuario(email="operador2@conexion.uy", nombre="Operador 2", password_hash=hash_password("oper123"), es_socio=False),
            Usuario(email="operador3@conexion.uy", nombre="Operador 3", password_hash=hash_password("oper123"), es_socio=False),
            Usuario(email="operador4@conexion.uy", nombre="Operador 4", password_hash=hash_password("oper123"), es_socio=False)
        ]
        
        db.add_all(socios + operadores)
        db.commit()
        print(f"✓ {len(socios)} socios creados")
        print(f"✓ {len(operadores)} operadores creados")
        
        print("\nUsuarios creados:")
        print("-" * 40)
        print("SOCIOS (acceso total):")
        for s in socios:
            print(f"  {s.email} / contraseña: {s.nombre.lower()}123")
        print("\nOPERADORES (acceso limitado):")
        for o in operadores:
            print(f"  {o.email} / contraseña: oper123")
            
    finally:
        db.close()

if __name__ == "__main__":
    crear_usuarios()
