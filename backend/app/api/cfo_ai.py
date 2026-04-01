"""
Router API para gestión de conversaciones CFO AI.

Los endpoints de chat (/ask-stream) están en cfo_streaming.py.
Este módulo solo gestiona CRUD de conversaciones.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.conversacion_service import ConversacionService
from app.schemas.conversacion import ConversacionListResponse, ConversacionResponse
from app.models import Usuario

router = APIRouter()


# ══════════════════════════════════════════════════════════════
# ENDPOINTS DE GESTIÓN DE CONVERSACIONES
# ══════════════════════════════════════════════════════════════

@router.get("/conversaciones", response_model=List[ConversacionListResponse])
def listar_conversaciones(
    db: Session = Depends(get_db),
    limit: int = 50,
    current_user: Usuario = Depends(get_current_user)
):
    """Lista las conversaciones del usuario autenticado"""
    conversaciones = ConversacionService.listar_conversaciones(db, current_user.id, limit)

    return [
        {
            "id": conv.id,
            "titulo": conv.titulo,
            "updated_at": conv.updated_at,
            "cantidad_mensajes": len(conv.mensajes)
        }
        for conv in conversaciones
    ]


@router.get("/conversaciones/{conversacion_id}", response_model=ConversacionResponse)
def obtener_conversacion(
    conversacion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene una conversación completa con todos sus mensajes (solo del usuario)"""
    from app.models.conversacion import Conversacion
    conversacion = db.query(Conversacion).filter(
        Conversacion.id == conversacion_id,
        Conversacion.deleted_at == None  # noqa: E711
    ).first()

    if not conversacion:
        raise HTTPException(404, "Conversación no encontrada")

    if conversacion.usuario_id != current_user.id:
        raise HTTPException(403, "No tienes acceso a esta conversación")

    return conversacion


@router.delete("/conversaciones/{conversacion_id}")
def eliminar_conversacion(
    conversacion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Marca una conversación como eliminada (soft delete vía deleted_at)."""
    from app.models.conversacion import Conversacion
    conversacion = db.query(Conversacion).filter(
        Conversacion.id == conversacion_id,
        Conversacion.deleted_at == None  # noqa: E711
    ).first()

    if not conversacion:
        raise HTTPException(404, "Conversación no encontrada")

    if conversacion.usuario_id != current_user.id:
        raise HTTPException(403, "No tienes acceso a esta conversación")

    conversacion.deleted_at = datetime.now(timezone.utc)
    db.commit()

    return {"success": True, "message": "Conversación eliminada"}
