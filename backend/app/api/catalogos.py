"""
Endpoints para catálogos (áreas, socios, etc.)
Estos datos se cargan desde la BD en lugar de estar hardcodeados en el frontend.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.area import Area
from app.models.socio import Socio
from app.models.usuario import Usuario

router = APIRouter()


class AreaResponse(BaseModel):
    id: UUID
    nombre: str
    
    class Config:
        from_attributes = True


class SocioResponse(BaseModel):
    id: UUID
    nombre: str
    porcentaje_participacion: float
    
    class Config:
        from_attributes = True


@router.get("/areas", response_model=List[AreaResponse])
def get_areas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Retorna todas las áreas activas ordenadas por nombre"""
    areas = db.query(Area).filter(Area.activo == True).order_by(Area.nombre).all()
    return areas


@router.get("/socios", response_model=List[SocioResponse])
def get_socios(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Retorna todos los socios activos ordenados por nombre"""
    socios = db.query(Socio).filter(Socio.activo == True).order_by(Socio.nombre).all()
    return socios

