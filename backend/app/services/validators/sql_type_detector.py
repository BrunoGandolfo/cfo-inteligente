"""
SQL Type Detector - Detecta el tipo de query para aplicar validaciones específicas.
Extraído de validador_sql.py para responsabilidad única.
"""
from typing import Optional


class SQLTypeDetector:
    """Detecta el tipo de query según patrones en pregunta y SQL."""
    
    # Nombres de socios para detección de distribuciones específicas
    _SOCIOS = frozenset(['bruno', 'agustina', 'viviana', 'gonzalo', 'pancho'])
    
    # Patrones simples: keyword -> tipo (orden no importa)
    _PATTERNS_SIMPLES = {
        'rentabilidad': 'rentabilidad',
        'margen': 'rentabilidad',
        'retir': 'retiros',
        'tipo de cambio': 'tipo_cambio',
    }
    
    @classmethod
    def detectar_tipo_query(cls, pregunta: str, sql: str) -> str:
        """
        Detecta qué tipo de query es para aplicar validaciones específicas.
        Usa patrones estructurados para reducir complejidad ciclomática.
        
        Args:
            pregunta: Pregunta del usuario
            sql: SQL generado
            
        Returns:
            Tipo de query: 'distribucion_socio', 'rentabilidad', 'porcentaje',
                          'facturacion', 'facturacion_dia', 'gastos', 'gastos_dia',
                          'retiros', 'tipo_cambio', 'general'
        """
        pregunta_lower = pregunta.lower()
        
        # Caso especial: distribuciones con nombre de socio
        tipo_socio = cls._detectar_distribucion_socio(pregunta_lower)
        if tipo_socio:
            return tipo_socio
        
        # Patrones simples (búsqueda en diccionario)
        for keyword, tipo in cls._PATTERNS_SIMPLES.items():
            if keyword in pregunta_lower:
                return tipo
        
        # Patrones con variantes día/hoy
        return cls._detectar_con_variante_dia(pregunta_lower, sql.upper())
    
    @classmethod
    def _detectar_distribucion_socio(cls, pregunta: str) -> Optional[str]:
        """Detecta distribuciones por socio (caso especial con nombres)."""
        tiene_socio = any(s in pregunta for s in cls._SOCIOS)
        
        if tiene_socio:
            if any(p in pregunta for p in ['distribu', 'recib', 'toca']):
                return 'distribucion_socio'
            if 'retir' in pregunta:
                return 'retiros'
        
        if 'distribu' in pregunta and ('socio' in pregunta or 'cada socio' in pregunta):
            return 'distribucion_socio'
        
        return None
    
    @staticmethod
    def _detectar_con_variante_dia(pregunta: str, sql: str) -> str:
        """Detecta tipos con variante día/hoy (facturación, gastos)."""
        es_dia = 'día' in pregunta or 'hoy' in pregunta
        
        # Porcentajes (verificar SQL también)
        if 'porcentaje' in pregunta or '%%' in sql or '* 100' in sql:
            return 'porcentaje'
        
        # Facturación
        if 'factur' in pregunta or 'ingreso' in pregunta:
            return 'facturacion_dia' if es_dia else 'facturacion'
        
        # Gastos
        if 'gast' in pregunta:
            return 'gastos_dia' if es_dia else 'gastos'
        
        # Tipo de cambio (fallback si no se detectó antes)
        if 'cambio' in pregunta:
            return 'tipo_cambio'
        
        return 'general'



