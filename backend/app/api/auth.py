from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.core.database import get_db
from app.models import Usuario
from app.core.security import verify_password, create_access_token, hash_password, get_current_user

router = APIRouter()

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE DOMINIOS Y SOCIOS
# ═══════════════════════════════════════════════════════════════

# Dominio por defecto y excepciones
DOMINIO_DEFAULT = "grupoconexion.uy"
DOMINIOS_EXCEPCION = {
    "bgandolfo": "cgmasociados.com"
}

# Lista de prefijos de email autorizados como socios
SOCIOS_AUTORIZADOS = ["aborio", "falgorta", "vcaresani", "gtaborda", "bgandolfo"]

def construir_email(prefijo: str) -> str:
    """Construye el email completo según el prefijo."""
    prefijo_lower = prefijo.lower().strip()
    dominio = DOMINIOS_EXCEPCION.get(prefijo_lower, DOMINIO_DEFAULT)
    return f"{prefijo_lower}@{dominio}"

# ═══════════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    nombre: str
    es_socio: bool

class RegisterRequest(BaseModel):
    prefijo_email: str  # Solo el prefijo, sin @
    nombre: str
    password: str

class RegisterResponse(BaseModel):
    message: str
    email: str
    es_socio: bool

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ChangePasswordResponse(BaseModel):
    message: str

# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Iniciar sesión con email y contraseña."""
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


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Registro público - cualquiera puede crear su cuenta.
    El dominio del email se asigna automáticamente según el prefijo.
    """
    # Validar que el prefijo no esté vacío
    prefijo = request.prefijo_email.lower().strip()
    if not prefijo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario de email es requerido"
        )
    
    # Validar que no contenga @
    if "@" in prefijo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo ingresa tu usuario, sin @"
        )
    
    # Construir email completo
    email = construir_email(prefijo)
    
    # Verificar que el email no exista
    existing = db.query(Usuario).filter(Usuario.email == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este usuario ya está registrado"
        )
    
    # Validar contraseña mínima
    if len(request.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos 6 caracteres"
        )
    
    # Determinar si es socio según SOCIOS_AUTORIZADOS
    es_socio = prefijo in SOCIOS_AUTORIZADOS
    
    # Crear usuario
    nuevo_usuario = Usuario(
        email=email,
        nombre=request.nombre.strip(),
        password_hash=hash_password(request.password),
        es_socio=es_socio,
        activo=True
    )
    
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    
    return RegisterResponse(
        message=f"Usuario creado exitosamente como {'socio' if es_socio else 'colaborador'}",
        email=email,
        es_socio=es_socio
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
    
    # Validar longitud mínima
    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña debe tener al menos 6 caracteres"
        )
    
    # Hashear y guardar nueva contraseña
    current_user.password_hash = hash_password(request.new_password)
    db.commit()
    
    return ChangePasswordResponse(message="Contraseña actualizada correctamente")


# ═══════════════════════════════════════════════════════════════
# ADMINISTRACIÓN DE USUARIOS (SOLO SOCIOS)
# ═══════════════════════════════════════════════════════════════

class UsuarioResponse(BaseModel):
    id: str
    email: str
    nombre: str
    es_socio: bool

class ResetPasswordResponse(BaseModel):
    message: str
    temp_password: str


@router.get("/usuarios", response_model=list[UsuarioResponse])
def listar_usuarios(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista todos los usuarios activos (solo socios pueden ver)."""
    if not current_user.es_socio:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo socios pueden ver la lista de usuarios"
        )
    
    usuarios = db.query(Usuario).filter(Usuario.activo == True).all()
    return [
        UsuarioResponse(
            id=str(u.id),
            email=u.email,
            nombre=u.nombre,
            es_socio=u.es_socio
        )
        for u in usuarios
    ]


@router.post("/reset-password/{user_id}", response_model=ResetPasswordResponse)
def reset_password(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Resetea la contraseña de un usuario a una temporal (solo socios)."""
    if not current_user.es_socio:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo socios pueden resetear contraseñas"
        )
    
    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # No permitir resetear a sí mismo
    if str(usuario.id) == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes resetear tu propia contraseña. Usa 'Cambiar contraseña'"
        )
    
    temp_password = "Temporal123"
    usuario.password_hash = hash_password(temp_password)
    db.commit()
    
    return ResetPasswordResponse(
        message=f"Contraseña de {usuario.nombre} reseteada exitosamente",
        temp_password=temp_password
    )
