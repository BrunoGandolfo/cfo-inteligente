"""
Servicio que conecta Vanna (pregunta->SQL) con la ejecución real
"""
import re
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Dict, Any

# Comandos SQL que NUNCA deben ejecutarse
COMANDOS_PROHIBIDOS = [
    'DROP', 'DELETE', 'UPDATE', 'INSERT', 'TRUNCATE', 
    'ALTER', 'GRANT', 'REVOKE', 'CREATE', 'COPY'
]

def ejecutar_consulta_cfo(db: Session, sql_query: str) -> Dict[str, Any]:
    """
    Ejecuta el SQL generado y retorna resultados.
    Incluye validación de seguridad para bloquear comandos peligrosos.
    """
    # VALIDACIÓN DE SEGURIDAD
    sql_upper = sql_query.upper()
    
    for cmd in COMANDOS_PROHIBIDOS:
        # Busca el comando al inicio del SQL o después de un ; (nuevo statement)
        pattern = rf'(^|;\s*){cmd}\b'
        if re.search(pattern, sql_upper):
            return {
                "success": False,
                "error": "Consulta no permitida por seguridad"
            }
    
    # Bloquear múltiples statements (previene SQL injection)
    if sql_query.count(';') > 1:
        return {
            "success": False,
            "error": "Solo se permite una consulta a la vez"
        }
    
    try:
        result = db.execute(text(sql_query))
        
        rows = []
        for row in result:
            rows.append(dict(row._mapping))
        
        return {
            "success": True,
            "data": rows,
            "count": len(rows)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
