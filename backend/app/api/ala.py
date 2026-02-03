"""
API para verificaciones ALA (Anti-Lavado de Activos).

Decreto 379/018 - Arts. 17-18, 44.
Verificación contra listas: PEP (Uruguay), ONU, OFAC, UE, GAFI.
"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Usuario
from app.schemas.verificacion_ala import (
    VerificacionALACreate,
    VerificacionALAResponse,
    VerificacionALAUpdate,
)
from app.services import ala_service

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Helpers
# =============================================================================

def _verificar_permiso_verificacion(
    verificacion,
    current_user: Usuario,
    accion: str = "acceder"
) -> None:
    """
    Verifica que el usuario tenga permiso sobre la verificación.
    
    - Socios pueden ver/editar cualquier verificación
    - No socios solo pueden ver/editar las propias
    
    Raises:
        HTTPException 403 si no tiene permiso
    """
    if current_user.es_socio:
        return
    
    if verificacion.usuario_id != current_user.id:
        logger.warning(
            f"Usuario {current_user.email} intentó {accion} verificación "
            f"{verificacion.id} sin permiso"
        )
        raise HTTPException(
            status_code=403,
            detail=f"No tiene permiso para {accion} esta verificación"
        )


def _verificar_es_socio(current_user: Usuario, accion: str = "realizar esta acción") -> None:
    """
    Verifica que el usuario sea socio.
    
    Raises:
        HTTPException 403 si no es socio
    """
    if not current_user.es_socio:
        logger.warning(f"Usuario {current_user.email} intentó {accion} sin ser socio")
        raise HTTPException(
            status_code=403,
            detail=f"Solo socios pueden {accion}"
        )


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/verificar", response_model=VerificacionALAResponse, status_code=201)
def crear_verificacion(
    datos: VerificacionALACreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Ejecuta verificación completa ALA contra todas las listas.
    
    Consulta listas: PEP (Uruguay), ONU, OFAC, UE + clasificación GAFI.
    
    ⚠️ Este endpoint puede demorar 30-60 segundos (descarga 4 listas externas).
    
    Decreto 379/018 - Arts. 17-18, 44.
    """
    logger.info(
        f"🔍 Iniciando verificación ALA - Usuario: {current_user.email}, "
        f"Nombre: {datos.nombre_completo[:50]}..."
    )
    
    try:
        verificacion = ala_service.ejecutar_verificacion_completa(
            db=db,
            datos=datos,
            usuario_id=current_user.id,
        )
        
        logger.info(
            f"✅ Verificación ALA completada - ID: {verificacion.id}, "
            f"Riesgo: {verificacion.nivel_riesgo}, "
            f"Diligencia: {verificacion.nivel_diligencia}"
        )
        
        return verificacion
        
    except ValueError as e:
        logger.error(f"Error de validación en verificación ALA: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error inesperado en verificación ALA: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al ejecutar verificación: {str(e)}"
        )


@router.get("/verificaciones")
def listar_verificaciones(
    limit: int = Query(50, ge=1, le=200, description="Máximo de resultados"),
    offset: int = Query(0, ge=0, description="Desplazamiento para paginación"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Lista verificaciones ALA con paginación.
    
    - Socios: ven todas las verificaciones
    - No socios: solo ven las propias
    """
    logger.info(f"Listando verificaciones ALA - Usuario: {current_user.email}")
    
    # Socios ven todas, no socios solo las propias
    usuario_id = None if current_user.es_socio else current_user.id
    
    try:
        resultado = ala_service.listar_verificaciones(
            db=db,
            usuario_id=usuario_id,
            limit=limit,
            offset=offset,
        )
        
        # Convertir verificaciones a response (usando from_attributes)
        verificaciones_response = [
            VerificacionALAResponse.model_validate(v)
            for v in resultado["verificaciones"]
        ]
        
        return {
            "total": resultado["total"],
            "verificaciones": verificaciones_response,
            "limit": resultado["limit"],
            "offset": resultado["offset"],
        }
        
    except Exception as e:
        logger.error(f"Error listando verificaciones ALA: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al listar verificaciones: {str(e)}"
        )


@router.get("/verificaciones/{verificacion_id}", response_model=VerificacionALAResponse)
def obtener_verificacion(
    verificacion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Obtiene una verificación ALA por ID.
    
    - Socios: pueden ver cualquier verificación
    - No socios: solo pueden ver las propias
    """
    logger.info(
        f"Obteniendo verificación ALA {verificacion_id} - Usuario: {current_user.email}"
    )
    
    verificacion = ala_service.obtener_verificacion(db, verificacion_id)
    
    if verificacion is None:
        raise HTTPException(
            status_code=404,
            detail="Verificación no encontrada"
        )
    
    _verificar_permiso_verificacion(verificacion, current_user, "ver")
    
    return verificacion


@router.patch("/verificaciones/{verificacion_id}", response_model=VerificacionALAResponse)
def actualizar_verificacion(
    verificacion_id: UUID,
    datos: VerificacionALAUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Actualiza campos Art. 44 C.4 de una verificación.
    
    Campos actualizables (búsquedas complementarias):
    - busqueda_google_realizada / busqueda_google_observaciones
    - busqueda_news_realizada / busqueda_news_observaciones
    - busqueda_wikipedia_realizada / busqueda_wikipedia_observaciones
    """
    logger.info(
        f"Actualizando verificación ALA {verificacion_id} - Usuario: {current_user.email}"
    )
    
    verificacion = ala_service.obtener_verificacion(db, verificacion_id)
    
    if verificacion is None:
        raise HTTPException(
            status_code=404,
            detail="Verificación no encontrada"
        )
    
    _verificar_permiso_verificacion(verificacion, current_user, "editar")
    
    try:
        # Actualizar solo campos que vengan (exclude_unset=True)
        datos_actualizacion = datos.model_dump(exclude_unset=True)
        
        for campo, valor in datos_actualizacion.items():
            setattr(verificacion, campo, valor)
        
        verificacion.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(verificacion)
        
        logger.info(f"Verificación ALA {verificacion_id} actualizada correctamente")
        
        return verificacion
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando verificación ALA: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar verificación: {str(e)}"
        )


@router.get("/listas/metadata")
def obtener_metadata_listas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Obtiene metadata de las listas ALA (PEP, ONU, OFAC, UE).
    
    Solo socios pueden acceder a esta información.
    
    Incluye: estado, última descarga, cantidad de registros, hash, errores.
    """
    _verificar_es_socio(current_user, "ver metadata de listas ALA")
    
    logger.info(f"Consultando metadata de listas ALA - Usuario: {current_user.email}")
    
    try:
        metadata_list = ala_service.obtener_metadata_listas(db)
        
        # Convertir a dict para respuesta JSON
        return [
            {
                "id": str(m.id),
                "nombre_lista": m.nombre_lista,
                "url_fuente": m.url_fuente,
                "estado": m.estado,
                "ultima_descarga": m.ultima_descarga.isoformat() if m.ultima_descarga else None,
                "cantidad_registros": m.cantidad_registros,
                "hash_contenido": m.hash_contenido,
                "error_detalle": m.error_detalle,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "updated_at": m.updated_at.isoformat() if m.updated_at else None,
            }
            for m in metadata_list
        ]
        
    except Exception as e:
        logger.error(f"Error obteniendo metadata de listas ALA: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener metadata de listas: {str(e)}"
        )


@router.delete("/verificaciones/{verificacion_id}")
def eliminar_verificacion(
    verificacion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Elimina una verificación ALA (soft delete).
    
    Solo socios pueden eliminar verificaciones.
    """
    _verificar_es_socio(current_user, "eliminar verificaciones ALA")
    
    logger.info(
        f"Eliminando verificación ALA {verificacion_id} - Usuario: {current_user.email}"
    )
    
    verificacion = ala_service.obtener_verificacion(db, verificacion_id)
    
    if verificacion is None:
        raise HTTPException(
            status_code=404,
            detail="Verificación no encontrada"
        )
    
    try:
        # Soft delete
        verificacion.deleted_at = datetime.now(timezone.utc)
        db.commit()
        
        logger.info(f"Verificación ALA {verificacion_id} eliminada (soft delete)")
        
        return {
            "mensaje": "Verificación eliminada",
            "id": str(verificacion_id),
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error eliminando verificación ALA: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar verificación: {str(e)}"
        )
