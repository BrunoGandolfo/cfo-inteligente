from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.core.database import get_db
from app.models import Usuario
from app.core.security import verify_password, create_access_token, hash_password, get_current_user

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    nombre: str
    es_socio: bool

# === REGISTRO ===
class RegisterRequest(BaseModel):
    email: EmailStr
    nombre: str
    password: str

class RegisterResponse(BaseModel):
    message: str
    email: str

# === CAMBIO DE CONTRASEÑA ===
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ChangePasswordResponse(BaseModel):
    message: str

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    # Buscar usuario
    usuario = db.query(Usuario).filter(Usuario.email == request.email).first()
    
    if not usuario or not verify_password(request.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos"
        )
    
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado"
        )
    
    # Crear token
    access_token = create_access_token(
        data={"sub": str(usuario.id), "es_socio": usuario.es_socio}
    )
    
    return LoginResponse(
        access_token=access_token,
        nombre=usuario.nombre,
        es_socio=usuario.es_socio
    )

# Lista de prefijos de email autorizados como socios
SOCIOS_AUTORIZADOS = ["aborio", "falgorta", "vcaresani", "gtaborda", "bgandolfo"]

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: RegisterRequest, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Registrar nuevo usuario.
    SOLO SOCIOS pueden crear nuevos usuarios.
    """
    # Verificar que el usuario actual sea socio
    if not current_user.es_socio:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los socios pueden crear usuarios"
        )
    
    # Verificar que el email no exista
    existing = db.query(Usuario).filter(Usuario.email == request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con ese email"
        )
    
    # Determinar rol según prefijo del email
    prefijo_email = request.email.split("@")[0].lower()
    es_socio = prefijo_email in SOCIOS_AUTORIZADOS
    
    # Crear usuario
    nuevo_usuario = Usuario(
        email=request.email,
        nombre=request.nombre,
        password_hash=hash_password(request.password),
        es_socio=es_socio,
        activo=True
    )
    
    db.add(nuevo_usuario)
    db.commit()
    
    return RegisterResponse(
        message=f"Usuario registrado exitosamente como {'socio' if es_socio else 'colaborador'}",
        email=request.email
    )


@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Cambiar contraseña del usuario autenticado.
    Requiere la contraseña actual para verificación.
    """
    # Verificar contraseña actual
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta"
        )
    
    # Validar que la nueva contraseña sea diferente
    if request.current_password == request.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña debe ser diferente a la actual"
        )
    
    # Hashear y guardar nueva contraseña
    current_user.password_hash = hash_password(request.new_password)
    db.commit()
    
    return ChangePasswordResponse(message="Contraseña actualizada correctamente")
