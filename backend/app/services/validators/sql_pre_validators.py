"""
SQL Pre-Validators - Validación ANTES de ejecutar SQL.
Detecta problemas lógicos y sintaxis básica.
Extraído de validador_sql.py para responsabilidad única.
"""
from typing import Dict, Any, Optional


class SQLPreValidators:
    """Validadores pre-ejecución para SQL."""
    
    @classmethod
    def validar_sql_antes_ejecutar(cls, pregunta: str, sql: str) -> Dict[str, Any]:
        """
        VALIDACIÓN PRE-EJECUCIÓN: Detecta problemas lógicos en SQL ANTES de ejecutarlo.
        
        Args:
            pregunta: Pregunta del usuario
            sql: SQL a validar
            
        Returns:
            {'valido': bool, 'problemas': List[str], 'sugerencia_fallback': str|None}
        """
        pregunta_lower = pregunta.lower()
        sql_upper = sql.upper()
        
        problemas = []
        
        # Ejecutar validaciones
        cls._validar_rankings(pregunta_lower, sql_upper, problemas)
        cls._validar_proyecciones(pregunta_lower, sql_upper, sql, problemas)
        cls._validar_porcentaje_moneda(pregunta_lower, sql_upper, sql, problemas)
        cls._validar_filtro_temporal(pregunta_lower, sql_upper, problemas)
        cls._validar_window_en_having(sql_upper, problemas)
        cls._validar_union_order_by(sql_upper, sql, problemas)
        cls._validar_union_enum_literal(sql_upper, problemas)
        cls._validar_union_excesivo(sql_upper, problemas)
        
        # Sugerencia de fallback si hay problemas
        sugerencia = cls._obtener_sugerencia_fallback(pregunta, problemas)
        # Problemas que deben BLOQUEAR ejecución (ej.: enum en UNION ALL sin cast, mega-UNION)
        bloqueante = any(
            ('UNION ALL' in p and ('columna enum' in p or 'literal' in p))
            or ('6+ ramas UNION' in p)
            for p in problemas
        )
        return {
            'valido': len(problemas) == 0,
            'problemas': problemas,
            'sugerencia_fallback': sugerencia,
            'bloqueante': bloqueante,
        }
    
    @staticmethod
    def _validar_rankings(pregunta: str, sql_upper: str, problemas: list) -> None:
        """Valida rankings con LIMIT 1 sospechoso."""
        keywords_ranking = ['ranking', 'top', 'mejores', 'principales', 'cuáles', 'cuales']
        excepciones = ['el mejor', 'el mayor', 'el más', 'cuál es']
        
        if any(kw in pregunta for kw in keywords_ranking):
            if 'LIMIT 1' in sql_upper:
                if not any(kw in pregunta for kw in excepciones):
                    problemas.append("Ranking pidió múltiples pero SQL tiene LIMIT 1")
    
    @staticmethod
    def _validar_proyecciones(pregunta: str, sql_upper: str, sql: str, problemas: list) -> None:
        """Valida proyecciones sin calcular meses restantes."""
        keywords_proyeccion = ['proyecc', 'proyect', 'fin de año', 'fin del año', 'cierre', 'estimar']
        
        if any(kw in pregunta for kw in keywords_proyeccion):
            tiene_extract = 'EXTRACT(MONTH FROM' in sql_upper
            tiene_calculo = '12 -' in sql or '365 -' in sql
            
            if not (tiene_extract or tiene_calculo):
                problemas.append("Proyección sin calcular meses/días restantes dinámicamente")
    
    @staticmethod
    def _validar_porcentaje_moneda(pregunta: str, sql_upper: str, sql: str, problemas: list) -> None:
        """Valida porcentajes de moneda sin usar moneda_original."""
        keywords_moneda = ['usd', 'uyu', 'dólar', 'peso', 'moneda', 'divisa']
        
        es_query_porcentaje_moneda = 'porcentaje' in pregunta and any(m in pregunta for m in keywords_moneda)
        
        if es_query_porcentaje_moneda and 'moneda_original' not in sql.lower():
            if 'COUNT(' in sql_upper or 'SUM(CASE WHEN' not in sql_upper:
                problemas.append("Porcentaje de moneda debe usar columna moneda_original, no monto_usd/uyu")
    
    @staticmethod
    def _validar_window_en_having(sql_upper: str, problemas: list) -> None:
        """Detecta window functions dentro de HAVING (PostgreSQL no lo permite)."""
        if 'HAVING' not in sql_upper:
            return
        idx = sql_upper.find('HAVING')
        fragment = sql_upper[idx:]
        # Recortar hasta ORDER BY, LIMIT o ; (fin de sentencia)
        for sep in (' ORDER BY ', ' LIMIT ', ';'):
            pos = fragment.find(sep)
            if pos != -1:
                fragment = fragment[:pos]
        window_markers = [
            'OVER (', 'OVER(',
            'ROW_NUMBER', 'RANK(', 'DENSE_RANK', 'NTILE(', 'LAG(', 'LEAD(',
        ]
        if any(m in fragment for m in window_markers):
            problemas.append(
                "Window functions no permitidas en HAVING. Usar subconsulta o CTE."
            )

    @staticmethod
    def _validar_union_order_by(sql_upper: str, sql: str, problemas: list) -> None:
        """
        ORDER BY en UNION/INTERSECT/EXCEPT solo permite nombres de columnas.
        No expresiones, casts (::) ni funciones. Envolver en subquery si hace falta.
        """
        keywords = ['UNION ALL', 'UNION', 'INTERSECT', 'EXCEPT']
        if not any(kw in sql_upper for kw in keywords):
            return
        # Posición del último keyword de compound (para tomar el ORDER BY que aplica al resultado)
        last_pos = -1
        for kw in keywords:
            idx = sql_upper.rfind(kw)
            if idx != -1 and idx > last_pos:
                last_pos = idx
        if last_pos == -1:
            return
        suffix_upper = sql_upper[last_pos:]
        order_by_idx = suffix_upper.find('ORDER BY')
        if order_by_idx == -1:
            return
        # Extraer la cláusula ORDER BY hasta LIMIT, ; o fin
        clause_start = last_pos + order_by_idx
        clause_snippet = sql_upper[clause_start:]
        end = len(clause_snippet)
        for sep in (' LIMIT ', ';'):
            pos = clause_snippet.find(sep)
            if pos != -1:
                end = min(end, pos)
        order_by_clause = clause_snippet[:end]
        # En el ORDER BY no debe haber casts (::) ni llamadas a funciones (...)
        if '::' in order_by_clause or ('(' in order_by_clause and ')' in order_by_clause):
            problemas.append(
                "ORDER BY en UNION/INTERSECT/EXCEPT no permite expresiones ni casts. Envolver en subquery."
            )

    @staticmethod
    def _validar_union_enum_literal(sql_upper: str, problemas: list) -> None:
        """
        En UNION ALL: Detecta mezcla de literales string con columnas enum que causa
        type mismatch. Solo bloquea cuando hay literal ('TOTAL', 'TOTALES', etc.)
        en una rama y la columna enum real en otra. Si todas las ramas usan la misma
        columna enum de la tabla, es valido en PostgreSQL (mismo tipo en ambas ramas).
        """
        if 'UNION ALL' not in sql_upper:
            return
        literales = ("'TOTAL GENERAL'", "'TOTAL'", "'TOTALES'")
        aliases_sensibles = (
            " AS LOCALIDAD", " AS TIPO_OPERACION", " AS MONEDA_ORIGINAL",
            " AS AREA", " AS NOMBRE", " AS SOCIO",
        )
        columnas_enum = ('localidad', 'tipo_operacion', 'moneda_original')

        def _recortar_hasta_fin_rama(seg: str) -> str:
            for sep in (' ORDER BY ', ' LIMIT ', ';'):
                idx = seg.find(sep)
                if idx != -1:
                    seg = seg[:idx]
            return seg

        def _extraer_select_portion(seg: str) -> str:
            seg_lower = seg.lower()
            from_idx = seg_lower.find(' from ')
            return seg_lower[:from_idx] if from_idx != -1 else seg_lower

        partes = sql_upper.split('UNION ALL')

        # CHECK 1: literal 'TOTAL'/'TOTALES' asignado a alias de columna enum (siempre malo)
        for i in range(1, len(partes)):
            segmento = _recortar_hasta_fin_rama(partes[i])
            if any(lit in segmento for lit in literales) and any(
                al in segmento for al in aliases_sensibles
            ):
                problemas.append(
                    "UNION ALL asigna literal 'TOTAL'/'TOTAL GENERAL' a columna enum/CHECK (localidad, area, etc.). "
                    "Usar CAST(col AS TEXT) o col::TEXT en la rama de datos."
                )
                return

        # CHECK 2: columna enum sin cast — SOLO bloquear si alguna rama tiene
        # un literal string donde se espera la columna (type mismatch real).
        # Si TODAS las ramas usan la misma columna enum de la tabla, es valido.
        hay_rama_con_literal = any(
            any(lit in _recortar_hasta_fin_rama(partes[i]) for lit in literales)
            for i in range(len(partes))
        )

        if not hay_rama_con_literal:
            # Todas las ramas usan columnas reales de la tabla — no hay type mismatch
            return

        # Hay mezcla de literal + columna enum: verificar si la columna tiene CAST
        for col in columnas_enum:
            for i in range(len(partes)):
                select_portion = _extraer_select_portion(
                    _recortar_hasta_fin_rama(partes[i])
                )
                if col not in select_portion:
                    continue
                if f"{col}::text" in select_portion:
                    continue
                if f"cast({col} as text)" in select_portion or f"cast( {col} as text)" in select_portion:
                    continue
                problemas.append(
                    "UNION ALL mezcla columna enum sin CAST con literal string. "
                    "Usar col::TEXT o CAST(col AS TEXT) en todas las ramas."
                )
                return

    @staticmethod
    def _validar_union_excesivo(sql_upper: str, problemas: list) -> None:
        """
        Detecta UNION ALL con demasiadas ramas (señal de mega-query problemática).

        4+ ramas = warning (riesgo de type mismatch).
        6+ ramas = bloqueante (casi siempre falla en PostgreSQL por tipos incompatibles).
        """
        count = sql_upper.count('UNION ALL')
        if count >= 5:
            problemas.append(
                f"SQL con 6+ ramas UNION ALL ({count + 1} ramas): "
                "alto riesgo de type mismatch. Usar GROUP BY en vez de UNION ALL."
            )
        elif count >= 3:
            problemas.append(
                f"SQL con {count + 1} ramas UNION ALL: "
                "riesgo de type mismatch entre ramas. Verificar tipos de columnas."
            )

    @staticmethod
    def _validar_filtro_temporal(pregunta: str, sql_upper: str, problemas: list) -> None:
        """Valida pregunta genérica sin filtro temporal."""
        keywords_temporal = [
            'mes', 'año', 'trimestre', 'semestre', 'día', 'hoy', 'ayer', 'mañana',
            'histórico', 'desde inicio', 'total', 'todos', '2024', '2025', 'siempre'
        ]
        filtros_sql = ['DATE_TRUNC', 'EXTRACT(YEAR', 'EXTRACT(MONTH', "fecha >= '202", "fecha < '202", 'WHERE fecha']
        
        no_tiene_periodo = not any(t in pregunta for t in keywords_temporal)
        no_tiene_filtro = not any(f in sql_upper for f in filtros_sql)
        
        if no_tiene_periodo and no_tiene_filtro:
            problemas.append("Pregunta genérica sin filtro temporal - debería filtrar por año 2025")
    
    @staticmethod
    def _obtener_sugerencia_fallback(pregunta: str, problemas: list) -> Optional[str]:
        """Obtiene sugerencia de fallback si hay problemas."""
        if not problemas:
            return None
        return 'regenerar'
    
    @staticmethod
    def validar_sintaxis_basica(sql: str) -> Dict[str, Any]:
        """
        Detecta errores de sintaxis comunes ANTES de ejecutar SQL.
        Más rápido que esperar error de PostgreSQL.
        
        Args:
            sql: SQL a validar
            
        Returns:
            {'valido': bool, 'problemas': List[str]}
        """
        problemas = []
        sql_upper = sql.upper()
        
        # FULL sin JOIN completo
        if 'FULL' in sql_upper and 'FULL OUTER JOIN' not in sql_upper and 'FULL JOIN' not in sql_upper:
            problemas.append("FULL keyword sin JOIN completo")
        
        # Paréntesis desbalanceados
        if sql.count('(') != sql.count(')'):
            problemas.append(f"Paréntesis desbalanceados: {sql.count('(')} abiertos, {sql.count(')')} cerrados")
        
        # CTE vacío
        if 'AS ()' in sql or 'AS ( )' in sql:
            problemas.append("CTE con cuerpo vacío detectado")
        
        # JOIN sin ON o USING
        joins = ['LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN', 'FULL JOIN', 'FULL OUTER JOIN']
        for join_type in joins:
            if join_type in sql_upper:
                idx = sql_upper.find(join_type)
                # Buscar en los próximos 150 caracteres si hay ON o USING
                siguiente = sql_upper[idx:idx+150]
                if ' ON ' not in siguiente and ' USING' not in siguiente:
                    problemas.append(f"{join_type} sin cláusula ON o USING")
        
        return {
            'valido': len(problemas) == 0,
            'problemas': problemas
        }


# Alias retrocompatible para imports legacy.
ValidadorPreSQL = SQLPreValidators
