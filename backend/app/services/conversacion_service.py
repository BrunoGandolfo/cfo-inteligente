from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from app.models.conversacion import Conversacion, Mensaje
from app.models.usuario import Usuario


class ConversacionService:
    
    @staticmethod
    def crear_conversacion(db: Session, usuario_id: UUID, titulo: Optional[str] = None) -> Conversacion:
        """Crea una nueva conversación"""
        conversacion = Conversacion(
            usuario_id=usuario_id,
            titulo=titulo or "Nueva conversación"
        )
        db.add(conversacion)
        db.commit()
        db.refresh(conversacion)
        return conversacion
    
    @staticmethod
    def obtener_conversacion(db: Session, conversacion_id: UUID, usuario_id: UUID) -> Optional[Conversacion]:
        """Obtiene una conversación con validación de propiedad"""
        return db.query(Conversacion).filter(
            Conversacion.id == conversacion_id,
            Conversacion.usuario_id == usuario_id
        ).first()
    
    @staticmethod
    def listar_conversaciones(db: Session, usuario_id: UUID, limit: int = 50) -> List[Conversacion]:
        """Lista conversaciones del usuario ordenadas por última actualización"""
        return db.query(Conversacion).filter(
            Conversacion.usuario_id == usuario_id
        ).order_by(desc(Conversacion.updated_at)).limit(limit).all()
    
    @staticmethod
    def agregar_mensaje(
        db: Session, 
        conversacion_id: UUID, 
        rol: str, 
        contenido: str,
        sql_generado: Optional[str] = None
    ) -> Mensaje:
        """Agrega un mensaje a la conversación"""
        mensaje = Mensaje(
            conversacion_id=conversacion_id,
            rol=rol,
            contenido=contenido,
            sql_generado=sql_generado
        )
        db.add(mensaje)
        
        # Actualizar timestamp de conversación
        conversacion = db.query(Conversacion).filter(Conversacion.id == conversacion_id).first()
        if conversacion:
            conversacion.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(mensaje)
        return mensaje
    
    @staticmethod
    def obtener_contexto(db: Session, conversacion_id: UUID, limite: int = 10) -> List[dict]:
        """
        Obtiene los últimos N mensajes de una conversación formateados para Claude
        Retorna lista de dicts con formato: {"role": "user|assistant", "content": "..."}
        """
        mensajes = db.query(Mensaje).filter(
            Mensaje.conversacion_id == conversacion_id
        ).order_by(desc(Mensaje.created_at)).limit(limite).all()
        
        # Invertir para tener orden cronológico
        mensajes = list(reversed(mensajes))
        
        # Formatear para API de Claude
        return [
            {
                "role": "user" if msg.rol == "user" else "assistant",
                "content": msg.contenido
            }
            for msg in mensajes
        ]
    
    @staticmethod
    def generar_titulo(pregunta: str) -> str:
        """Genera título corto de la primera pregunta"""
        titulo = pregunta[:50].strip()
        if len(pregunta) > 50:
            titulo += "..."
        return titulo

