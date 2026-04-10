"""Modelo para vincular usuarios del sistema con chat IDs de Telegram."""

from datetime import datetime, timezone
import uuid

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


def utc_now():
    """Retorna la fecha actual en UTC."""
    return datetime.now(timezone.utc)


class TelegramUsuario(Base):
    """Vincula un usuario interno con un chat_id único de Telegram."""

    __tablename__ = "telegram_usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False, unique=True)
    chat_id = Column(BigInteger, nullable=False, unique=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    usuario = relationship("Usuario")

    def __repr__(self):
        return f"<TelegramUsuario(usuario_id={self.usuario_id}, chat_id={self.chat_id})>"
