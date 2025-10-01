"""
Post-procesador inteligente de SQL
Modifica SQL generado por Vanna según patrones detectados en la pregunta
Principio: Convention over configuration, DRY, KISS
"""

import re
from typing import Dict, Any, Optional


class SQLPostProcessor:
    """
    Procesa y mejora SQL generado por Vanna basándose en la pregunta del usuario
    """
    
    @staticmethod
    def detectar_moneda(pregunta: str) -> str:
        """Detecta si usuario pide USD o UYU"""
        pregunta_lower = pregunta.lower()
        
        keywords_usd = ['dólar', 'dollar', 'usd', 'en dólares', 'en dolares']
        keywords_uyu = ['peso', 'uyu', 'en pesos']
        
        if any(kw in pregunta_lower for kw in keywords_usd):
            return 'USD'
        elif any(kw in pregunta_lower for kw in keywords_uyu):
            return 'UYU'
        
        return 'UYU'  # Default
    
    @staticmethod
    def convertir_a_usd(sql: str) -> str:
        """Reemplaza monto_uyu por monto_usd en el SQL"""
        if not sql or 'SELECT' not in sql.upper():
            return sql
        
        # Reemplazar todas las referencias a monto_uyu por monto_usd
        sql_modificado = sql.replace('monto_uyu', 'monto_usd')
        sql_modificado = sql_modificado.replace('MONTO_UYU', 'MONTO_USD')
        
        return sql_modificado
    
    @staticmethod
    def extraer_sql_de_texto(texto: str) -> Optional[str]:
        """
        Extrae SQL de texto mezclado (como cuando Vanna genera ```sql...```)
        """
        if not texto:
            return None
        
        # Buscar bloques de código SQL
        sql_block_match = re.search(r'```sql\s*(.*?)\s*```', texto, re.DOTALL | re.IGNORECASE)
        if sql_block_match:
            return sql_block_match.group(1).strip()
        
        # Buscar bloques genéricos
        code_block_match = re.search(r'```\s*(SELECT.*?)\s*```', texto, re.DOTALL | re.IGNORECASE)
        if code_block_match:
            return code_block_match.group(1).strip()
        
        # Si el texto contiene SELECT/WITH pero también tiene explicaciones,
        # intentar extraer solo la parte SQL
        if 'SELECT' in texto.upper() or 'WITH' in texto.upper():
            # Buscar desde SELECT o WITH hasta el final, limpiando explicaciones
            match = re.search(r'((?:WITH|SELECT).*)', texto, re.DOTALL | re.IGNORECASE)
            if match:
                sql_candidato = match.group(1).strip()
                # Limpiar texto explicativo al final
                sql_candidato = re.sub(r'\n\n.*?(?:This|The|To|For|Note).*', '', sql_candidato, flags=re.DOTALL)
                return sql_candidato.strip()
        
        return None
    
    @staticmethod
    def procesar_sql(pregunta: str, sql_generado: str) -> Dict[str, Any]:
        """
        Procesa el SQL generado según la pregunta
        
        Returns:
            {
                'sql': str,  # SQL procesado
                'modificado': bool,  # Si se modificó
                'cambios': list  # Lista de cambios aplicados
            }
        """
        cambios = []
        sql_final = sql_generado
        
        # PASO 1: Intentar extraer SQL si está mezclado con texto
        sql_extraido = SQLPostProcessor.extraer_sql_de_texto(sql_generado)
        if sql_extraido and sql_extraido != sql_generado:
            sql_final = sql_extraido
            cambios.append("Extraído SQL de texto mixto")
        
        # PASO 2: Detección de moneda
        moneda_solicitada = SQLPostProcessor.detectar_moneda(pregunta)
        
        if moneda_solicitada == 'USD' and 'monto_uyu' in sql_final.lower():
            sql_final = SQLPostProcessor.convertir_a_usd(sql_final)
            cambios.append(f"Convertido a {moneda_solicitada}")
        
        return {
            'sql': sql_final,
            'modificado': len(cambios) > 0,
            'cambios': cambios
        }

