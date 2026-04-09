"""
API para gestión de contratos notariales.

Módulo Notarial - Plantillas de contratos DOCX.
Acceso público para lectura, solo socios para escritura.
"""

import json
import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.access_control import COLABORADORES_ACCESO_CONTRATOS
from app.models import Usuario
from app.schemas.contrato import (
    ContratoCreate,
    ContratoUpdate,
    ContratoResponse,
    ContratoListResponse,
)
from app.services import contratos_service
from app.services.contrato_fields_extractor import ContratoFieldsExtractor
from app.services.contrato_generator import ContratoGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/contratos", tags=["contratos"])


# ============================================================================
# HELPERS
# ============================================================================

def _tiene_acceso_contratos(usuario: Usuario) -> bool:
    """Retorna True si el usuario tiene acceso completo al módulo Contratos."""
    if usuario.es_socio:
        return True
    if usuario.email and usuario.email.strip().lower() in [e.lower() for e in COLABORADORES_ACCESO_CONTRATOS]:
        return True
    return False


def _verificar_acceso_escritura(usuario: Usuario) -> None:
    """Lanza 403 si el usuario no tiene acceso de escritura."""
    if not _tiene_acceso_contratos(usuario):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para esta acción",
        )


# ============================================================================
# ENDPOINTS PÚBLICOS (lectura)
# ============================================================================

@router.get("/categorias", response_model=List[str])
def listar_categorias(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Lista todas las categorías únicas disponibles."""
    try:
        return contratos_service.listar_categorias(db)
    except Exception as e:
        logger.error(f"Error listando categorías: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al listar categorías")


@router.get("/buscar", response_model=List[ContratoResponse])
def buscar_contratos(
    q: str = Query(..., description="Texto a buscar (requerido)"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    limit: int = Query(20, ge=1, le=100, description="Límite de resultados"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Búsqueda full-text en título y contenido de contratos."""
    try:
        contratos = contratos_service.buscar_contratos(db, q=q, categoria=categoria, limit=limit)
        return [ContratoResponse.model_validate(c) for c in contratos]
    except Exception as e:
        logger.error(f"Error buscando contratos con '{q}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al buscar contratos")


@router.get("/", response_model=ContratoListResponse)
def listar_contratos(
    q: Optional[str] = Query(None, description="Búsqueda en título y contenido"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    activo: Optional[bool] = Query(True, description="Solo contratos activos"),
    skip: int = Query(0, ge=0, description="Offset para paginación"),
    limit: int = Query(50, ge=1, le=100, description="Límite de resultados"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Lista contratos con filtros y paginación."""
    try:
        result = contratos_service.listar_contratos(
            db, q=q, categoria=categoria, activo=activo, skip=skip, limit=limit,
        )
        contratos_response = [ContratoResponse.model_validate(c) for c in result["contratos"]]
        return ContratoListResponse(
            contratos=contratos_response,
            total=result["total"],
            categorias=result["categorias"],
        )
    except Exception as e:
        logger.error(f"Error listando contratos: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al listar contratos")


@router.get("/{contrato_id}", response_model=ContratoResponse)
def obtener_contrato(
    contrato_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Obtiene un contrato por ID."""
    try:
        contrato = contratos_service.obtener_contrato(db, contrato_id)
        if not contrato:
            raise HTTPException(status_code=404, detail="Contrato no encontrado")
        return ContratoResponse.model_validate(contrato)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo contrato {contrato_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al obtener contrato")


@router.get("/{contrato_id}/descargar")
def descargar_contrato(
    contrato_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Descarga el archivo DOCX del contrato."""
    try:
        contrato = contratos_service.obtener_contrato(db, contrato_id)
        if not contrato:
            raise HTTPException(status_code=404, detail="Contrato no encontrado")
        if not contrato.contenido_docx:
            raise HTTPException(status_code=404, detail="El contrato no tiene archivo DOCX disponible")

        return Response(
            content=contrato.contenido_docx,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{contrato.nombre_archivo}"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error descargando contrato {contrato_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al descargar contrato")


# ============================================================================
# ENDPOINTS PROTEGIDOS (solo socios)
# ============================================================================

@router.post("/", response_model=ContratoResponse, status_code=status.HTTP_201_CREATED)
def crear_contrato(
    contrato: ContratoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Crea un nuevo contrato. Solo socios."""
    try:
        _verificar_acceso_escritura(current_user)

        nuevo_contrato = contratos_service.crear_contrato(
            db,
            titulo=contrato.titulo,
            categoria=contrato.categoria,
            subcategoria=contrato.subcategoria,
            descripcion=contrato.descripcion,
            contenido_docx=contrato.contenido_docx,
            contenido_texto=contrato.contenido_texto,
            archivo_original=contrato.archivo_original,
            fuente_original=contrato.fuente_original,
            activo=contrato.activo,
        )

        # Extraer campos automáticamente si hay contenido_texto
        if nuevo_contrato.contenido_texto and not nuevo_contrato.campos_editables:
            try:
                extractor = ContratoFieldsExtractor()
                campos_data = extractor.extract_fields(nuevo_contrato.contenido_texto)
                if campos_data:
                    nuevo_contrato.campos_editables = campos_data
                    db.commit()
                    db.refresh(nuevo_contrato)
            except Exception as e:
                logger.error(f"Error extrayendo campos para contrato {nuevo_contrato.id}: {e}", exc_info=True)

        return ContratoResponse.model_validate(nuevo_contrato)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creando contrato: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al crear contrato")


@router.patch("/{contrato_id}", response_model=ContratoResponse)
def actualizar_contrato(
    contrato_id: UUID,
    contrato_update: ContratoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Actualiza un contrato existente. Solo socios."""
    try:
        _verificar_acceso_escritura(current_user)

        contrato = contratos_service.obtener_contrato(db, contrato_id)
        if not contrato:
            raise HTTPException(status_code=404, detail="Contrato no encontrado")

        update_data = contrato_update.model_dump(exclude_unset=True)
        contrato = contratos_service.actualizar_contrato(db, contrato, update_data)

        return ContratoResponse.model_validate(contrato)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando contrato {contrato_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al actualizar contrato")


@router.delete("/{contrato_id}", status_code=status.HTTP_200_OK)
def eliminar_contrato(
    contrato_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Elimina un contrato (soft delete). Solo socios."""
    try:
        _verificar_acceso_escritura(current_user)

        contrato = contratos_service.obtener_contrato(db, contrato_id)
        if not contrato:
            raise HTTPException(status_code=404, detail="Contrato no encontrado")

        contratos_service.eliminar_contrato(db, contrato)
        return {"message": "Contrato eliminado"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error eliminando contrato {contrato_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al eliminar contrato")


@router.post("/{contrato_id}/extraer-campos", status_code=status.HTTP_200_OK)
def extraer_campos_contrato(
    contrato_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Extrae campos editables de un contrato usando Claude. Solo socios."""
    try:
        _verificar_acceso_escritura(current_user)

        contrato = contratos_service.obtener_contrato(db, contrato_id)
        if not contrato:
            raise HTTPException(status_code=404, detail="Contrato no encontrado")
        if not contrato.contenido_texto:
            raise HTTPException(status_code=400, detail="El contrato no tiene contenido_texto disponible")

        extractor = ContratoFieldsExtractor()
        campos_data = extractor.extract_fields(contrato.contenido_texto)
        if not campos_data:
            raise HTTPException(status_code=500, detail="Error al extraer campos del contrato")

        contrato.campos_editables = campos_data
        db.commit()
        db.refresh(contrato)

        return {
            "contrato_id": str(contrato_id),
            "campos_extraidos": campos_data.get("total_campos", 0),
            "campos": campos_data.get("campos", []),
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error extrayendo campos del contrato {contrato_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al extraer campos del contrato")


@router.post("/{contrato_id}/generar")
def generar_contrato(
    contrato_id: UUID,
    datos: dict,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Genera un contrato DOCX con los valores proporcionados. Solo socios."""
    try:
        _verificar_acceso_escritura(current_user)

        contrato = contratos_service.obtener_contrato(db, contrato_id)
        if not contrato:
            raise HTTPException(status_code=404, detail="Contrato no encontrado")
        if not contrato.contenido_docx:
            raise HTTPException(status_code=400, detail="El contrato no tiene archivo DOCX disponible")
        if not contrato.campos_editables:
            raise HTTPException(status_code=400, detail="El contrato no tiene campos editables definidos")

        campos = contrato.campos_editables
        if isinstance(campos, str):
            try:
                campos = json.loads(campos)
            except json.JSONDecodeError:
                raise HTTPException(status_code=500, detail="Error al parsear campos editables")

        valores = datos.get("valores", {})
        if not valores:
            raise HTTPException(status_code=400, detail="No se proporcionaron valores para completar el contrato")

        generator = ContratoGenerator()
        docx_generado = generator.generar(
            contenido_docx=contrato.contenido_docx,
            campos_editables=campos,
            valores=valores,
        )

        nombre_archivo = f"{contrato.titulo.replace(' ', '_').replace('/', '-')}_completado.docx"

        return Response(
            content=docx_generado,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generando contrato {contrato_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al generar contrato")


@router.post("/extraer-campos-batch", status_code=status.HTTP_200_OK)
def extraer_campos_batch(
    solo_sin_campos: bool = Query(True, description="Solo procesar contratos sin campos_editables"),
    limite: int = Query(10, ge=1, le=50, description="Máximo de contratos a procesar"),
    max_intentos: int = Query(2, ge=1, le=5, description="Máximo intentos por contrato"),
    max_caracteres: int = Query(40000, ge=1000, description="Máximo caracteres de contenido"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Extrae campos editables de múltiples contratos (procesamiento batch). Solo socios."""
    try:
        _verificar_acceso_escritura(current_user)

        contratos = contratos_service.obtener_contratos_para_extraccion(
            db, solo_sin_campos=solo_sin_campos, max_intentos=max_intentos, limite=limite,
        )

        if not contratos:
            return {
                "procesados": 0, "exitosos": 0, "errores": 0,
                "skipped_por_intentos": 0, "skipped_por_tamaño": 0,
                "detalles": [], "mensaje": "No hay contratos pendientes de procesar",
            }

        extractor = ContratoFieldsExtractor()
        detalles = []
        exitosos = 0
        errores = 0
        skipped_tamaño = 0

        for contrato in contratos:
            detalle = {
                "contrato_id": str(contrato.id), "titulo": contrato.titulo,
                "exito": False, "campos_extraidos": 0, "error": None,
                "intento": contrato.intentos_extraccion + 1,
                "caracteres": len(contrato.contenido_texto) if contrato.contenido_texto else 0,
            }

            if contrato.contenido_texto and len(contrato.contenido_texto) > max_caracteres:
                contrato.requiere_procesamiento_manual = True
                contrato.ultimo_error_extraccion = (
                    f"Contenido demasiado largo: {len(contrato.contenido_texto)} caracteres (máx: {max_caracteres})"
                )
                db.commit()
                detalle["error"] = f"Skipped: contenido muy largo ({len(contrato.contenido_texto)} chars)"
                detalle["skipped"] = True
                skipped_tamaño += 1
                detalles.append(detalle)
                continue

            try:
                contrato.intentos_extraccion += 1
                db.commit()

                campos_data = extractor.extract_fields(contrato.contenido_texto)
                if campos_data:
                    contrato.campos_editables = campos_data
                    contrato.ultimo_error_extraccion = None
                    db.commit()
                    detalle["exito"] = True
                    detalle["campos_extraidos"] = campos_data.get("total_campos", 0)
                    exitosos += 1
                else:
                    error_msg = "No se pudieron extraer campos (respuesta vacía)"
                    contrato.ultimo_error_extraccion = error_msg
                    if contrato.intentos_extraccion >= max_intentos:
                        contrato.requiere_procesamiento_manual = True
                    db.commit()
                    detalle["error"] = error_msg
                    errores += 1
            except Exception as e:
                db.rollback()
                error_msg = str(e)[:500]
                try:
                    contrato.ultimo_error_extraccion = error_msg
                    if contrato.intentos_extraccion >= max_intentos:
                        contrato.requiere_procesamiento_manual = True
                    db.commit()
                except Exception:
                    pass
                detalle["error"] = error_msg[:200]
                errores += 1

            detalles.append(detalle)

        skipped_intentos = contratos_service.contar_contratos_agotados(db, max_intentos=max_intentos)

        return {
            "procesados": len(contratos), "exitosos": exitosos, "errores": errores,
            "skipped_por_intentos": skipped_intentos, "skipped_por_tamaño": skipped_tamaño,
            "detalles": detalles,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en extracción batch: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al procesar extracción batch")
