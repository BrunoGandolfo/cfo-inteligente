"""
API para gestión de contratos notariales.

Módulo Notarial - Plantillas de contratos DOCX.
Acceso público para lectura, solo socios para escritura.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Optional, List
from uuid import UUID
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Usuario
from app.models.contrato import Contrato
from app.schemas.contrato import (
    ContratoCreate,
    ContratoUpdate,
    ContratoResponse,
    ContratoListResponse,
    ContratoBusquedaParams
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/contratos", tags=["contratos"])


# ============================================================================
# ENDPOINTS PÚBLICOS (lectura)
# ============================================================================
# IMPORTANTE: Las rutas estáticas deben ir ANTES de las dinámicas
# para evitar que FastAPI interprete "buscar" o "categorias" como UUIDs

@router.get("/categorias", response_model=List[str])
def listar_categorias(
    db: Session = Depends(get_db)
):
    """
    Lista todas las categorías únicas disponibles.
    
    Acceso: Público (sin autenticación requerida).
    """
    try:
        categorias = db.query(Contrato.categoria).filter(
            Contrato.deleted_at.is_(None),
            Contrato.activo == True
        ).distinct().all()
        
        return sorted([cat[0] for cat in categorias])
    
    except Exception as e:
        logger.error(f"Error listando categorías: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al listar categorías"
        )


@router.get("/buscar", response_model=List[ContratoResponse])
def buscar_contratos(
    q: str = Query(..., description="Texto a buscar (requerido)"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    limit: int = Query(20, ge=1, le=100, description="Límite de resultados"),
    db: Session = Depends(get_db)
):
    """
    Búsqueda full-text en título y contenido de contratos.
    
    Usa ILIKE para búsqueda case-insensitive.
    
    Acceso: Público (sin autenticación requerida).
    """
    try:
        # Construir query
        query = db.query(Contrato).filter(
            Contrato.deleted_at.is_(None),
            Contrato.activo == True
        )
        
        # Filtro por categoría
        if categoria:
            query = query.filter(Contrato.categoria == categoria)
        
        # Búsqueda en título y contenido
        q_lower = f"%{q.lower()}%"
        query = query.filter(
            or_(
                func.lower(Contrato.titulo).like(q_lower),
                func.lower(Contrato.contenido_texto).like(q_lower)
            )
        )
        
        # Ordenar por relevancia (título primero)
        contratos = query.order_by(
            func.lower(Contrato.titulo).like(q_lower).desc(),
            Contrato.titulo
        ).limit(limit).all()
        
        return [ContratoResponse.model_validate(c) for c in contratos]
    
    except Exception as e:
        logger.error(f"Error buscando contratos con '{q}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al buscar contratos"
        )


@router.get("/", response_model=ContratoListResponse)
def listar_contratos(
    q: Optional[str] = Query(None, description="Búsqueda en título y contenido"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    activo: Optional[bool] = Query(True, description="Solo contratos activos"),
    skip: int = Query(0, ge=0, description="Offset para paginación"),
    limit: int = Query(50, ge=1, le=100, description="Límite de resultados"),
    db: Session = Depends(get_db)
):
    """
    Lista contratos con filtros y paginación.
    
    Acceso: Público (sin autenticación requerida).
    """
    try:
        # Construir query base
        query = db.query(Contrato).filter(Contrato.deleted_at.is_(None))
        
        # Filtro por activo
        if activo is not None:
            query = query.filter(Contrato.activo == activo)
        
        # Filtro por categoría
        if categoria:
            query = query.filter(Contrato.categoria == categoria)
        
        # Búsqueda en título y contenido
        if q:
            q_lower = f"%{q.lower()}%"
            query = query.filter(
                or_(
                    func.lower(Contrato.titulo).like(q_lower),
                    func.lower(Contrato.contenido_texto).like(q_lower)
                )
            )
        
        # Contar total
        total = query.count()
        
        # Ordenar y paginar
        contratos = query.order_by(Contrato.titulo).offset(skip).limit(limit).all()
        
        # Obtener lista de categorías únicas
        categorias = db.query(Contrato.categoria).filter(
            Contrato.deleted_at.is_(None),
            Contrato.activo == True
        ).distinct().all()
        categorias_list = sorted([cat[0] for cat in categorias])
        
        # Convertir a response
        contratos_response = [ContratoResponse.model_validate(c) for c in contratos]
        
        return ContratoListResponse(
            contratos=contratos_response,
            total=total,
            categorias=categorias_list
        )
    
    except Exception as e:
        logger.error(f"Error listando contratos: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al listar contratos"
        )


@router.get("/{contrato_id}", response_model=ContratoResponse)
def obtener_contrato(
    contrato_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Obtiene un contrato por ID (sin contenido_docx).
    
    Acceso: Público (sin autenticación requerida).
    """
    try:
        contrato = db.query(Contrato).filter(
            Contrato.id == contrato_id,
            Contrato.deleted_at.is_(None)
        ).first()
        
        if not contrato:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contrato no encontrado"
            )
        
        return ContratoResponse.model_validate(contrato)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo contrato {contrato_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener contrato"
        )


@router.get("/{contrato_id}/descargar")
def descargar_contrato(
    contrato_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Descarga el archivo DOCX del contrato.
    
    Acceso: Público (sin autenticación requerida).
    
    Returns:
        FileResponse con el archivo DOCX
    """
    try:
        contrato = db.query(Contrato).filter(
            Contrato.id == contrato_id,
            Contrato.deleted_at.is_(None)
        ).first()
        
        if not contrato:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contrato no encontrado"
            )
        
        if not contrato.contenido_docx:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El contrato no tiene archivo DOCX disponible"
            )
        
        # Generar nombre de archivo seguro
        nombre_archivo = contrato.nombre_archivo
        
        # Retornar archivo como respuesta binaria
        return Response(
            content=contrato.contenido_docx,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{nombre_archivo}"'
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error descargando contrato {contrato_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al descargar contrato"
        )


# ============================================================================
# ENDPOINTS PROTEGIDOS (solo socios)
# ============================================================================

@router.post("/", response_model=ContratoResponse, status_code=status.HTTP_201_CREATED)
def crear_contrato(
    contrato: ContratoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crea un nuevo contrato.
    
    Acceso: Solo socios.
    """
    try:
        # Verificar que el usuario es socio
        if not current_user.es_socio:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los socios pueden crear contratos"
            )
        
        # Crear contrato
        nuevo_contrato = Contrato(
            titulo=contrato.titulo,
            categoria=contrato.categoria,
            subcategoria=contrato.subcategoria,
            descripcion=contrato.descripcion,
            contenido_docx=contrato.contenido_docx,
            contenido_texto=contrato.contenido_texto,
            archivo_original=contrato.archivo_original,
            fuente_original=contrato.fuente_original,
            activo=contrato.activo
        )
        
        db.add(nuevo_contrato)
        db.commit()
        db.refresh(nuevo_contrato)
        
        return ContratoResponse.model_validate(nuevo_contrato)
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creando contrato: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al crear contrato"
        )


@router.patch("/{contrato_id}", response_model=ContratoResponse)
def actualizar_contrato(
    contrato_id: UUID,
    contrato_update: ContratoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualiza un contrato existente.
    
    Acceso: Solo socios.
    """
    try:
        # Verificar que el usuario es socio
        if not current_user.es_socio:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los socios pueden actualizar contratos"
            )
        
        # Buscar contrato
        contrato = db.query(Contrato).filter(
            Contrato.id == contrato_id,
            Contrato.deleted_at.is_(None)
        ).first()
        
        if not contrato:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contrato no encontrado"
            )
        
        # Actualizar campos proporcionados
        update_data = contrato_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(contrato, field, value)
        
        db.commit()
        db.refresh(contrato)
        
        return ContratoResponse.model_validate(contrato)
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando contrato {contrato_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al actualizar contrato"
        )


@router.delete("/{contrato_id}", status_code=status.HTTP_200_OK)
def eliminar_contrato(
    contrato_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Elimina un contrato (soft delete).
    
    Establece deleted_at en lugar de eliminar físicamente.
    
    Acceso: Solo socios.
    """
    try:
        # Verificar que el usuario es socio
        if not current_user.es_socio:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los socios pueden eliminar contratos"
            )
        
        # Buscar contrato
        contrato = db.query(Contrato).filter(
            Contrato.id == contrato_id,
            Contrato.deleted_at.is_(None)
        ).first()
        
        if not contrato:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contrato no encontrado"
            )
        
        # Soft delete
        from datetime import datetime, timezone
        contrato.deleted_at = datetime.now(timezone.utc)
        
        db.commit()
        
        return {"message": "Contrato eliminado"}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error eliminando contrato {contrato_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al eliminar contrato"
        )
