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
from app.services.contrato_fields_extractor import ContratoFieldsExtractor
from app.services.contrato_generator import ContratoGenerator

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
        
        # Extraer campos automáticamente si hay contenido_texto
        # (solo si no se proporcionaron campos_editables manualmente)
        if nuevo_contrato.contenido_texto and not nuevo_contrato.campos_editables:
            try:
                logger.info(f"Extrayendo campos automáticamente para nuevo contrato {nuevo_contrato.id}")
                extractor = ContratoFieldsExtractor()
                campos_data = extractor.extract_fields(nuevo_contrato.contenido_texto)
                
                if campos_data:
                    # Guardar directamente como dict (SQLAlchemy JSON lo maneja automáticamente)
                    nuevo_contrato.campos_editables = campos_data
                    db.commit()
                    db.refresh(nuevo_contrato)
                    logger.info(
                        f"Campos extraídos automáticamente para contrato {nuevo_contrato.id}: "
                        f"{campos_data.get('total_campos', 0)} campos"
                    )
                else:
                    logger.warning(f"No se pudieron extraer campos para contrato {nuevo_contrato.id}")
            except Exception as e:
                # No fallar la creación si la extracción falla
                logger.error(
                    f"Error extrayendo campos automáticamente para contrato {nuevo_contrato.id}: {e}",
                    exc_info=True
                )
                # Continuar sin campos_editables (se pueden extraer después manualmente)
        
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


@router.post("/{contrato_id}/extraer-campos", status_code=status.HTTP_200_OK)
def extraer_campos_contrato(
    contrato_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Extrae campos editables de un contrato usando Claude.
    
    Analiza el contenido_texto y detecta placeholders (____________, [___], [...]).
    Guarda el resultado en campos_editables.
    
    Acceso: Solo socios.
    
    Returns:
        {
            "contrato_id": str,
            "campos_extraidos": int,
            "campos": [...]
        }
    """
    try:
        # Verificar que el usuario es socio
        if not current_user.es_socio:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los socios pueden extraer campos de contratos"
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
        
        # Verificar que tiene contenido_texto
        if not contrato.contenido_texto:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El contrato no tiene contenido_texto disponible"
            )
        
        # Extraer campos usando el servicio
        extractor = ContratoFieldsExtractor()
        campos_data = extractor.extract_fields(contrato.contenido_texto)
        
        if not campos_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al extraer campos del contrato. Verifique los logs para más detalles."
            )
        
        # Guardar en campos_editables (SQLAlchemy JSON maneja la serialización)
        contrato.campos_editables = campos_data
        
        db.commit()
        db.refresh(contrato)
        
        logger.info(
            f"Campos extraídos para contrato {contrato_id}: "
            f"{campos_data.get('total_campos', 0)} campos"
        )
        
        return {
            "contrato_id": str(contrato_id),
            "campos_extraidos": campos_data.get('total_campos', 0),
            "campos": campos_data.get('campos', [])
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error extrayendo campos del contrato {contrato_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al extraer campos del contrato"
        )


@router.post("/{contrato_id}/generar")
def generar_contrato(
    contrato_id: UUID,
    datos: dict,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Genera un contrato DOCX con los valores proporcionados.
    
    Reemplaza los placeholders en el documento con los valores del formulario.
    
    Acceso: Solo socios.
    
    Args:
        contrato_id: ID del contrato a generar
        datos: Dict con estructura {"valores": {campo_id: valor}}
    
    Returns:
        Response con el DOCX generado para descarga
    """
    import json
    
    try:
        # Verificar que el usuario es socio
        if not current_user.es_socio:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los socios pueden generar contratos"
            )
        
        # Obtener contrato
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
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El contrato no tiene archivo DOCX disponible"
            )
        
        if not contrato.campos_editables:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El contrato no tiene campos editables definidos"
            )
        
        # Parsear campos_editables si viene como string
        campos = contrato.campos_editables
        if isinstance(campos, str):
            try:
                campos = json.loads(campos)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error al parsear campos editables del contrato"
                )
        
        # Obtener valores del request
        valores = datos.get('valores', {})
        if not valores:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se proporcionaron valores para completar el contrato"
            )
        
        # Generar documento
        generator = ContratoGenerator()
        docx_generado = generator.generar(
            contenido_docx=contrato.contenido_docx,
            campos_editables=campos,
            valores=valores
        )
        
        # Generar nombre de archivo seguro
        nombre_archivo = contrato.titulo.replace(" ", "_").replace("/", "-")
        nombre_archivo = f"{nombre_archivo}_completado.docx"
        
        # Retornar como descarga
        return Response(
            content=docx_generado,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{nombre_archivo}"'
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generando contrato {contrato_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al generar contrato"
        )


@router.post("/extraer-campos-batch", status_code=status.HTTP_200_OK)
def extraer_campos_batch(
    solo_sin_campos: bool = Query(True, description="Solo procesar contratos sin campos_editables"),
    limite: int = Query(10, ge=1, le=50, description="Máximo de contratos a procesar"),
    max_intentos: int = Query(2, ge=1, le=5, description="Máximo intentos por contrato"),
    max_caracteres: int = Query(40000, ge=1000, description="Máximo caracteres de contenido"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Extrae campos editables de múltiples contratos (procesamiento batch inteligente).
    
    Características:
    - Máximo 2 intentos por contrato (configurable)
    - Skip automático de contratos muy largos (>40k caracteres)
    - Registro de errores para análisis
    - No reintenta contratos marcados como problemáticos
    
    Acceso: Solo socios.
    
    Args:
        solo_sin_campos: Si True, solo procesa contratos con campos_editables=NULL
        limite: Máximo de contratos a procesar por llamada (1-50)
        max_intentos: Máximo intentos por contrato antes de marcarlo como fallido
        max_caracteres: Máximo caracteres permitidos (contratos más largos se skipean)
    
    Returns:
        {
            "procesados": int,
            "exitosos": int,
            "errores": int,
            "skipped_por_intentos": int,
            "skipped_por_tamaño": int,
            "detalles": [...]
        }
    """
    try:
        # Verificar que el usuario es socio
        if not current_user.es_socio:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los socios pueden extraer campos de contratos"
            )
        
        # Construir query base con filtros inteligentes
        query = db.query(Contrato).filter(
            Contrato.deleted_at.is_(None),
            Contrato.activo == True,
            Contrato.contenido_texto.isnot(None),
            Contrato.requiere_procesamiento_manual == False,  # Excluir problemáticos
            Contrato.intentos_extraccion < max_intentos  # Solo los que no agotaron intentos
        )
        
        # Filtrar por campos_editables si es necesario
        if solo_sin_campos:
            query = query.filter(Contrato.campos_editables.is_(None))
        
        # Limitar cantidad
        contratos = query.limit(limite).all()
        
        if not contratos:
            return {
                "procesados": 0,
                "exitosos": 0,
                "errores": 0,
                "skipped_por_intentos": 0,
                "skipped_por_tamaño": 0,
                "detalles": [],
                "mensaje": "No hay contratos pendientes de procesar"
            }
        
        # Procesar cada contrato
        extractor = ContratoFieldsExtractor()
        detalles = []
        exitosos = 0
        errores = 0
        skipped_tamaño = 0
        
        for contrato in contratos:
            detalle = {
                "contrato_id": str(contrato.id),
                "titulo": contrato.titulo,
                "exito": False,
                "campos_extraidos": 0,
                "error": None,
                "intento": contrato.intentos_extraccion + 1,
                "caracteres": len(contrato.contenido_texto) if contrato.contenido_texto else 0
            }
            
            # Skip si es muy largo
            if contrato.contenido_texto and len(contrato.contenido_texto) > max_caracteres:
                contrato.requiere_procesamiento_manual = True
                contrato.ultimo_error_extraccion = f"Contenido demasiado largo: {len(contrato.contenido_texto)} caracteres (máx: {max_caracteres})"
                db.commit()
                
                detalle["error"] = f"Skipped: contenido muy largo ({len(contrato.contenido_texto)} chars)"
                detalle["skipped"] = True
                skipped_tamaño += 1
                detalles.append(detalle)
                logger.info(f"Batch: Skip {contrato.titulo} - muy largo ({len(contrato.contenido_texto)} chars)")
                continue
            
            try:
                # Incrementar contador de intentos ANTES de procesar
                contrato.intentos_extraccion += 1
                db.commit()
                
                # Extraer campos
                campos_data = extractor.extract_fields(contrato.contenido_texto)
                
                if campos_data:
                    # Guardar en campos_editables
                    contrato.campos_editables = campos_data
                    contrato.ultimo_error_extraccion = None  # Limpiar error previo
                    db.commit()
                    
                    detalle["exito"] = True
                    detalle["campos_extraidos"] = campos_data.get('total_campos', 0)
                    exitosos += 1
                    
                    logger.info(
                        f"Batch: ✅ {contrato.titulo}: {detalle['campos_extraidos']} campos "
                        f"(intento {detalle['intento']})"
                    )
                else:
                    error_msg = "No se pudieron extraer campos (respuesta vacía)"
                    contrato.ultimo_error_extraccion = error_msg
                    
                    # Si agotó intentos, marcar como problemático
                    if contrato.intentos_extraccion >= max_intentos:
                        contrato.requiere_procesamiento_manual = True
                        error_msg += f" - Marcado para procesamiento manual (agotó {max_intentos} intentos)"
                    
                    db.commit()
                    
                    detalle["error"] = error_msg
                    errores += 1
                    logger.warning(f"Batch: ❌ {contrato.titulo} - {error_msg}")
            
            except Exception as e:
                db.rollback()
                error_msg = str(e)[:500]
                
                # Actualizar error en el contrato
                try:
                    contrato.ultimo_error_extraccion = error_msg
                    if contrato.intentos_extraccion >= max_intentos:
                        contrato.requiere_procesamiento_manual = True
                    db.commit()
                except:
                    pass
                
                detalle["error"] = error_msg[:200]
                errores += 1
                logger.error(f"Batch: ❌ {contrato.titulo}: {e}")
            
            detalles.append(detalle)
        
        # Contar cuántos quedaron excluidos por intentos agotados
        skipped_intentos = db.query(Contrato).filter(
            Contrato.deleted_at.is_(None),
            Contrato.activo == True,
            Contrato.campos_editables.is_(None),
            Contrato.intentos_extraccion >= max_intentos
        ).count()
        
        return {
            "procesados": len(contratos),
            "exitosos": exitosos,
            "errores": errores,
            "skipped_por_intentos": skipped_intentos,
            "skipped_por_tamaño": skipped_tamaño,
            "detalles": detalles
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en extracción batch: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al procesar extracción batch"
        )
