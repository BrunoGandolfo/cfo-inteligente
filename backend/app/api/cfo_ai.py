"""
Router API para CFO Inteligente - Conecta Vanna con ejecución
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.cfo_ai_service import ejecutar_consulta_cfo
from pydantic import BaseModel
import sys
import os

# Agregar path para importar scripts
sys.path.append(os.path.join(os.path.dirname(__file__), '../../scripts'))
from configurar_vanna_local import my_vanna as vn

router = APIRouter()

class PreguntaCFO(BaseModel):
    pregunta: str

@router.post("/ask")
def preguntar_cfo(data: PreguntaCFO, db: Session = Depends(get_db)):
    """
    Endpoint que recibe pregunta en español y retorna datos
    """
    try:
        # Conectar Vanna a PostgreSQL
        vn.connect_to_postgres(
            host='localhost',
            dbname='cfo_inteligente',
            user='cfo_user',
            password='cfo_pass',
            port=5432
        )
        
        # Generar SQL con Vanna
        sql_generado = vn.generate_sql(data.pregunta)
        
        if not sql_generado:
            raise HTTPException(status_code=400, detail="No pude generar SQL para esa pregunta")
        
        # Ejecutar el SQL
        resultado = ejecutar_consulta_cfo(db, sql_generado)
        
        return {
            "pregunta": data.pregunta,
            "sql_generado": sql_generado,
            "resultado": resultado,
            "status": "success"
        }
        
    except Exception as e:
        return {
            "pregunta": data.pregunta,
            "sql_generado": None,
            "resultado": None,
            "error": str(e),
            "status": "error"
        }
