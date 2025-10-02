"""
Servicio que conecta Vanna (pregunta->SQL) con la ejecución real
"""

from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Dict, Any

def ejecutar_consulta_cfo(db: Session, sql_query: str) -> Dict[str, Any]:
    """
    Ejecuta el SQL generado por Vanna y retorna resultados
    """
    try:
        # Ejecutar la query
        result = db.execute(text(sql_query))
        
        # Convertir resultados a lista de diccionarios
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
