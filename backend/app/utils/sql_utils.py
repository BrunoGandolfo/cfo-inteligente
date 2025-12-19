"""
SQL Utilities - Extracción y validación de SQL.

Extraído de SQLRouter para reducir God Object.
"""

import re
import sqlparse
from typing import Dict, Any, Optional


def extraer_sql_limpio(texto: str) -> Optional[str]:
    """
    Extrae SQL limpio de texto que puede contener:
    - Backticks: ```sql ... ``` o ``` ... ```
    - Texto explicativo antes/después del SQL
    - Comentarios SQL
    
    Args:
        texto: Respuesta del LLM (puede ser SQL puro o texto mixto)
        
    Returns:
        SQL limpio o None si no se encuentra SQL válido
    """
    if not texto or len(texto) < 5:
        return None
    
    texto_stripped = texto.strip()
    
    # PASO 1: Buscar bloques con triple backticks ```sql...```
    match_sql = re.search(r'```sql\s*(.*?)\s*```', texto_stripped, re.DOTALL | re.IGNORECASE)
    if match_sql:
        return match_sql.group(1).strip()
    
    # PASO 2: Buscar bloques con triple backticks genéricos ```...```
    match_generic = re.search(r'```\s*(.*?)\s*```', texto_stripped, re.DOTALL)
    if match_generic:
        contenido = match_generic.group(1).strip()
        if 'SELECT' in contenido.upper() or 'WITH' in contenido.upper():
            return contenido
    
    # PASO 3: Si no hay backticks pero contiene SQL, extraer desde SELECT/WITH
    texto_upper = texto_stripped.upper()
    if 'SELECT' in texto_upper or 'WITH' in texto_upper:
        pos_select = texto_upper.find('SELECT')
        pos_with = texto_upper.find('WITH')
        
        if pos_with != -1 and (pos_select == -1 or pos_with < pos_select):
            sql_desde = texto_stripped[pos_with:]
        elif pos_select != -1:
            sql_desde = texto_stripped[pos_select:]
        else:
            return None
        
        if ';' in sql_desde:
            ultimo_semicolon = sql_desde.rfind(';')
            sql_desde = sql_desde[:ultimo_semicolon + 1]
        
        return sql_desde.strip()
    
    return None


def validar_sql(sql: str) -> Dict[str, Any]:
    """
    Valida que el SQL es sintácticamente correcto y ejecutable.
    
    Args:
        sql: Query SQL a validar
        
    Returns:
        {'valido': bool, 'tipo': str, 'parseado': bool, 'error': str}
    """
    if not sql or len(sql) < 5:
        return {'valido': False, 'tipo': None, 'parseado': False, 'error': 'SQL vacío'}
    
    sql_upper = sql.strip().upper()
    
    tiene_select = 'SELECT' in sql_upper
    tiene_with = 'WITH' in sql_upper
    
    if not (tiene_select or tiene_with):
        return {'valido': False, 'tipo': 'OTRO', 'parseado': False, 
                'error': 'SQL no contiene SELECT ni WITH'}
    
    tipo = 'WITH' if sql_upper.strip().startswith('WITH') else 'SELECT'
    
    try:
        parsed = sqlparse.parse(sql)
        if not parsed or len(parsed) == 0:
            return {'valido': False, 'tipo': tipo, 'parseado': False,
                    'error': 'sqlparse no pudo parsear el SQL'}
        
        primer_statement = parsed[0]
        if primer_statement.get_type() not in ['SELECT', 'UNKNOWN']:
            return {'valido': False, 'tipo': tipo, 'parseado': True,
                    'error': f'Tipo inesperado: {primer_statement.get_type()}'}
        
        return {'valido': True, 'tipo': tipo, 'parseado': True, 'error': None}
    
    except Exception as e:
        return {'valido': False, 'tipo': tipo, 'parseado': False,
                'error': f'Error en sqlparse: {str(e)}'}

