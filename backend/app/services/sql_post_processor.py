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
    
    # Mapa de nombres de áreas sin tilde → con tilde correcta
    _AREA_ACCENT_MAP = {
        "'Juridica'": "'Jurídica'",
        "'Recuperacion'": "'Recuperación'",
        "'Administracion'": "'Administración'",
    }

    @staticmethod
    def corregir_acentos_areas(sql: str) -> str:
        """
        Corrige nombres de áreas sin tilde en SQL generado.

        Safety net: si Claude genera a.nombre = 'Juridica' (sin acento),
        lo corrige a 'Jurídica' para matchear los valores reales de la BD.
        Cubre: Jurídica, Recuperación, Administración.
        """
        if not sql:
            return sql

        resultado = sql
        for sin_tilde, con_tilde in SQLPostProcessor._AREA_ACCENT_MAP.items():
            resultado = resultado.replace(sin_tilde, con_tilde)

        return resultado

    @staticmethod
    def parentizar_union_all(sql: str) -> str:
        """
        Corrige UNION ALL/UNION sin paréntesis cuando las ramas tienen ORDER BY o LIMIT.

        PostgreSQL requiere paréntesis alrededor de cada SELECT que tenga
        ORDER BY o LIMIT dentro de un UNION ALL. Sin ellas da syntax error.

        Transforma:
          SELECT ... ORDER BY x LIMIT 5 UNION ALL SELECT ... ORDER BY y LIMIT 5
        En:
          (SELECT ... ORDER BY x LIMIT 5) UNION ALL (SELECT ... ORDER BY y LIMIT 5)

        Un ORDER BY final que aplica al resultado completo del UNION se preserva
        fuera de los paréntesis.
        """
        if not sql:
            return sql

        sql_upper = sql.upper()

        # Buscar UNION ALL o UNION (no dentro de subqueries ya parentizadas)
        has_union = 'UNION ALL' in sql_upper or re.search(r'\bUNION\b', sql_upper)
        if not has_union:
            return sql

        # Si ya está parentizado (empieza con '(' antes del primer SELECT), no tocar
        stripped = sql.strip()
        if stripped.startswith('('):
            return sql

        # Splitear respetando case del original: buscar posiciones de UNION ALL / UNION
        # Usar regex para encontrar separadores UNION ALL o UNION (word boundary)
        # Preservar el texto original entre separadores
        separador_pattern = re.compile(r'\bUNION\s+ALL\b|\bUNION\b(?!\s+ALL)', re.IGNORECASE)
        separadores = list(separador_pattern.finditer(sql))

        if not separadores:
            return sql

        # Extraer las ramas
        ramas = []
        prev_end = 0
        seps_text = []
        for m in separadores:
            ramas.append(sql[prev_end:m.start()])
            seps_text.append(m.group())
            prev_end = m.end()
        ramas.append(sql[prev_end:])

        # Limpiar whitespace de cada rama
        ramas = [r.strip() for r in ramas]

        if len(ramas) < 2:
            return sql

        # Detectar ORDER BY final que aplica al UNION completo (en la última rama).
        # Heurística: buscar el ÚLTIMO ORDER BY de nivel 0 (fuera de paréntesis)
        # en la última rama. Es un ORDER BY del UNION solo si:
        #   1) Las ramas anteriores tienen ORDER BY o LIMIT
        #   2) NO hay LIMIT después de este ORDER BY (si hay LIMIT, pertenece al SELECT)
        ultima = ramas[-1]
        ultima_upper = ultima.upper()
        order_final = ''

        # Encontrar todas las posiciones de ORDER BY de nivel 0 en la última rama
        depth = 0
        order_positions = []
        i = 0
        while i < len(ultima_upper):
            if ultima[i] == '(':
                depth += 1
            elif ultima[i] == ')':
                depth -= 1
            elif depth == 0 and ultima_upper[i:i+8] == 'ORDER BY':
                order_positions.append(i)
            i += 1

        if order_positions:
            last_order_pos = order_positions[-1]
            after_order = ultima_upper[last_order_pos:]
            has_limit_after = 'LIMIT' in after_order

            # Si hay LIMIT después del ORDER BY, el ORDER BY pertenece a este SELECT.
            # Solo separar como ORDER BY final si NO tiene LIMIT después Y las
            # ramas anteriores también tienen ORDER BY/LIMIT (señal de que el
            # ORDER BY es del UNION, no del SELECT).
            if not has_limit_after:
                ramas_internas_tienen_order = all(
                    'ORDER BY' in r.upper() or 'LIMIT' in r.upper()
                    for r in ramas[:-1]
                )
                if ramas_internas_tienen_order:
                    order_final = '\n' + ultima[last_order_pos:].strip()
                    ramas[-1] = ultima[:last_order_pos].strip()

        # Verificar si alguna rama necesita paréntesis
        alguna_necesita = False
        for rama in ramas:
            rama_upper = rama.upper()
            tiene_order = 'ORDER BY' in rama_upper
            tiene_limit = 'LIMIT' in rama_upper
            ya_parentizada = rama.strip().startswith('(') and rama.strip().endswith(')')
            if (tiene_order or tiene_limit) and not ya_parentizada:
                alguna_necesita = True
                break

        if not alguna_necesita:
            return sql

        # Envolver cada rama en paréntesis
        ramas_parentizadas = []
        for rama in ramas:
            rama = rama.strip().rstrip(';')
            ya_parentizada = rama.startswith('(') and rama.endswith(')')
            if ya_parentizada:
                ramas_parentizadas.append(rama)
            else:
                ramas_parentizadas.append(f'({rama})')

        # Reconstruir con los separadores originales
        resultado = ramas_parentizadas[0]
        for i, sep in enumerate(seps_text):
            resultado += f'\n{sep}\n{ramas_parentizadas[i + 1]}'

        if order_final:
            resultado += order_final

        return resultado

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
        
        # NO convertir si ya tiene AMBAS monedas (el SQL es dual - ej: "en pesos y dólares")
        tiene_ambas_monedas = 'monto_uyu' in sql_final.lower() and 'monto_usd' in sql_final.lower()
        
        # DESACTIVADO: Claude ya genera el SQL correcto según la intención del usuario
        # La detección de moneda por keywords causaba conversiones incorrectas

        # PASO 3: Corregir acentos en nombres de áreas
        sql_acentuado = SQLPostProcessor.corregir_acentos_areas(sql_final)
        if sql_acentuado != sql_final:
            sql_final = sql_acentuado
            cambios.append("Corregidos acentos en nombres de áreas")

        # PASO 4: Corregir UNION ALL sin paréntesis cuando las ramas tienen ORDER BY/LIMIT
        sql_corregido = SQLPostProcessor.parentizar_union_all(sql_final)
        if sql_corregido != sql_final:
            sql_final = sql_corregido
            cambios.append("Parentizado ramas de UNION ALL con ORDER BY/LIMIT")

        return {
            'sql': sql_final,
            'modificado': len(cambios) > 0,
            'cambios': cambios
        }

