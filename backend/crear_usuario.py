import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.usuario import Usuario
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"])
db = SessionLocal()

# Buscar si ya existe
existing = db.query(Usuario).filter(Usuario.email == "bgandolfo@cgmasociados.com").first()
if existing:
    print("El usuario ya existe")
else:
    usuario = Usuario(
        email="bgandolfo@cgmasociados.com",
        nombre_completo="Bruno Gandolfo",
        hashed_password=pwd_context.hash("Hipolito18"),
        es_activo=True,
        es_admin=True
    )
    db.add(usuario)
    db.commit()
    print("Usuario creado: bgandolfo@cgmasociados.com / Hipolito18")

db.close()
