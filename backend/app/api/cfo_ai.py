"""
Router API para CFO Inteligente - Conecta Vanna con ejecución
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.cfo_ai_service import ejecutar_consulta_cfo
from pydantic import BaseModel

router = APIRouter()

class PreguntaCFO(BaseModel):
    pregunta: str

@router.post("/ask")
def preguntar_cfo(data: PreguntaCFO, db: Session = Depends(get_db)):
    """
    Endpoint que recibe pregunta en español y retorna datos
    """
    # Por ahora simulamos - cuando Vanna esté configurado, aquí irá vn.generate_sql()
    sql_ejemplo = "SELECT COUNT(*) as total FROM operaciones"
    
    # Ejecutar el SQL
    resultado = ejecutar_consulta_cfo(db, sql_ejemplo)
    
    return {
        "pregunta": data.pregunta,
        "sql_generado": sql_ejemplo,
        "resultado": resultado
    }
