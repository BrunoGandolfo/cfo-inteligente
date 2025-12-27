"""
Endpoint para exportar mensajes del chat CFO AI a PDF

POST /api/cfo/export-pdf - Genera PDF desde un mensaje del chat

Autor: Sistema CFO Inteligente
Fecha: Diciembre 2025
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from pathlib import Path

from app.core.database import get_db
from app.core.logger import get_logger
from app.core.security import get_current_user
from app.models import Usuario, Mensaje
from app.services.chat_pdf_generator import ChatPDFGenerator

logger = get_logger(__name__)

router = APIRouter()


class ExportPDFRequest(BaseModel):
    """Request body para exportar mensaje a PDF."""
    mensaje_id: str
    titulo: Optional[str] = None
    incluir_graficos: bool = True


def eliminar_archivo_temporal(path: str) -> None:
    """Background task para eliminar PDF temporal después de enviarlo."""
    try:
        archivo = Path(path)
        if archivo.exists():
            archivo.unlink()
            logger.debug(f"PDF temporal eliminado: {path}")
    except Exception as e:
        logger.warning(f"No se pudo eliminar PDF temporal {path}: {e}")


@router.post("/export-pdf", response_class=FileResponse)
async def exportar_chat_a_pdf(
    request: ExportPDFRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Exporta un mensaje del chat CFO AI a PDF profesional.
    
    Args:
        request: ExportPDFRequest con mensaje_id, titulo opcional, incluir_graficos
        
    Returns:
        FileResponse con el PDF generado
        
    Raises:
        404: Mensaje no encontrado
        400: Mensaje no es de assistant
        500: Error generando PDF
    """
    logger.info(f"Exportando mensaje {request.mensaje_id} a PDF (graficos={request.incluir_graficos})")
    
    try:
        # ═══════════════════════════════════════════════════════════════
        # PASO 1: VALIDAR Y OBTENER MENSAJE
        # ═══════════════════════════════════════════════════════════════
        
        try:
            mensaje_uuid = UUID(request.mensaje_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="mensaje_id inválido: debe ser un UUID válido"
            )
        
        mensaje = db.query(Mensaje).filter(Mensaje.id == mensaje_uuid).first()
        
        if not mensaje:
            raise HTTPException(
                status_code=404,
                detail=f"Mensaje con id {request.mensaje_id} no encontrado"
            )
        
        # Validar que es mensaje del assistant
        if mensaje.rol != 'assistant':
            raise HTTPException(
                status_code=400,
                detail="Solo se pueden exportar mensajes del assistant (rol='assistant')"
            )
        
        # Validar que el mensaje pertenece a una conversación del usuario actual
        conversacion = mensaje.conversacion
        if conversacion and conversacion.usuario_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para exportar este mensaje"
            )
        
        contenido = mensaje.contenido
        
        if not contenido or not contenido.strip():
            raise HTTPException(
                status_code=400,
                detail="El mensaje no tiene contenido para exportar"
            )
        
        logger.info(f"  → Mensaje encontrado: {len(contenido)} caracteres")
        
        # ═══════════════════════════════════════════════════════════════
        # PASO 2: GENERAR PDF
        # ═══════════════════════════════════════════════════════════════
        
        logger.info("  → Generando PDF...")
        
        generator = ChatPDFGenerator()
        resultado = generator.generar(
            contenido_markdown=contenido,
            titulo_override=request.titulo,
            incluir_graficos=request.incluir_graficos
        )
        
        pdf_path = resultado['pdf_path']
        filename = resultado['filename']
        
        logger.info(f"  → PDF generado: {filename} ({resultado['size_kb']:.1f} KB)")
        
        # ═══════════════════════════════════════════════════════════════
        # PASO 3: RETORNAR ARCHIVO
        # ═══════════════════════════════════════════════════════════════
        
        # Programar eliminación del archivo después de enviarlo
        background_tasks.add_task(eliminar_archivo_temporal, pdf_path)
        
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=filename,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Secciones-Count": str(resultado.get('secciones_count', 0)),
                "X-Graficos-Count": str(resultado.get('graficos_count', 0)),
                "X-Generation-Time-Ms": str(resultado.get('tiempo_generacion_ms', 0))
            }
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Error exportando chat a PDF: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generando PDF: {str(e)}"
        )

