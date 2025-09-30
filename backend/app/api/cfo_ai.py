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
import json
import anthropic
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar path para importar scripts
sys.path.append(os.path.join(os.path.dirname(__file__), '../../scripts'))
from configurar_vanna_local import my_vanna as vn

router = APIRouter()

# Cliente de Anthropic para Claude Sonnet 4.5
client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")  # Usar variable de entorno
)

class PreguntaCFO(BaseModel):
    pregunta: str

def generar_respuesta_narrativa(pregunta: str, datos: list, sql_generado: str) -> str:
    """
    Usa Claude Sonnet 4.5 para generar respuesta narrativa profesional
    """
    try:
        # Formatear datos de manera legible
        datos_texto = json.dumps(datos, indent=2, ensure_ascii=False, default=str)
        
        prompt = f"""Eres el CFO AI de Conexión Consultora, una consultora en Uruguay.

Pregunta del usuario: {pregunta}

Datos obtenidos de la base de datos:
{datos_texto}

SQL ejecutado:
{sql_generado}

INSTRUCCIONES:
- Genera una respuesta clara, profesional y útil en español rioplatense
- Destaca el dato principal de manera conversacional
- Si hay múltiples filas, resume los puntos clave
- Sé conciso (2-4 líneas máximo)
- Usa formato narrativo, NO JSON ni formato técnico
- Si es una cifra monetaria, usa el formato apropiado (ej: "$ 1.234.567")
- Si es un porcentaje, redondea a 2 decimales
- Si no hay datos, explica amablemente que no hay información para ese período

Genera SOLO la respuesta, sin preámbulos ni explicaciones adicionales."""
        
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=250,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return message.content[0].text
    
    except Exception as e:
        # Si falla Claude, retornar datos crudos formateados
        return f"Resultado: {json.dumps(datos, indent=2, ensure_ascii=False, default=str)}"

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
        sql_generado = vn.generate_sql(data.pregunta, allow_llm_to_see_data=True)
        
        if not sql_generado:
            raise HTTPException(status_code=400, detail="No pude generar SQL para esa pregunta")
        
        # Ejecutar el SQL
        resultado = ejecutar_consulta_cfo(db, sql_generado)
        
        # Generar respuesta narrativa con Claude Sonnet 4.5
        if resultado.get('success') and resultado.get('data'):
            respuesta_narrativa = generar_respuesta_narrativa(
                data.pregunta,
                resultado['data'],
                sql_generado
            )
            
            return {
                "pregunta": data.pregunta,
                "respuesta": respuesta_narrativa,
                "datos_raw": resultado['data'],
                "sql_generado": sql_generado,
                "status": "success"
            }
        else:
            # Si el SQL falló, retornar el error
            return {
                "pregunta": data.pregunta,
                "respuesta": f"No pude obtener datos para esa pregunta. Error: {resultado.get('error', 'Desconocido')}",
                "sql_generado": sql_generado,
                "resultado": resultado,
                "status": "error"
            }
            
    except Exception as e:
        return {
            "pregunta": data.pregunta,
            "sql_generado": None,
            "resultado": None,
            "error": str(e),
            "status": "error"
        }
