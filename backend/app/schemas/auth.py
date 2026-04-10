"""Schemas Pydantic para autenticación y usuarios."""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    nombre: str
    es_socio: bool


class RegisterRequest(BaseModel):
    prefijo_email: str
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


class UsuarioResponse(BaseModel):
    id: str
    email: str
    nombre: str
    es_socio: bool


class ResetPasswordResponse(BaseModel):
    message: str
    temp_password: str


class CambiarPasswordPublicoRequest(BaseModel):
    prefijo_email: str
    password_actual: str
    password_nueva: str


class CambiarPasswordPublicoResponse(BaseModel):
    message: str


class VincularTelegramRequest(BaseModel):
    email: str
    chat_id: int


class VincularTelegramResponse(BaseModel):
    exito: bool
    email: str
    chat_id: int
