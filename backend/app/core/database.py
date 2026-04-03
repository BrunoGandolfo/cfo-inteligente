"""Conexión SQLAlchemy (sync) a PostgreSQL y generador de sesiones para FastAPI."""

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


def utc_now():
    """Retorna datetime actual en UTC. Fuente única de verdad para timestamps del sistema."""
    return datetime.now(timezone.utc)

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
