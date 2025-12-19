"""
SQL Pre-Validators - Validación ANTES de ejecutar SQL.
Detecta problemas lógicos y sintaxis básica.
Extraído de validador_sql.py para responsabilidad única.
"""
from typing import Dict, Any, List, Optional


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
        
        # Sugerencia de fallback si hay problemas
        sugerencia = cls._obtener_sugerencia_fallback(pregunta, problemas)
        
        return {
            'valido': len(problemas) == 0,
            'problemas': problemas,
            'sugerencia_fallback': sugerencia
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
        
        try:
            from app.services.query_fallback import QueryFallback
            sql_predefinido = QueryFallback.get_query_for(pregunta)
            return 'query_predefinida' if sql_predefinido else 'vanna_fallback'
        except Exception:
            return 'vanna_fallback'
    
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

