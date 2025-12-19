"""
Sistema de fallback robusto para queries comunes
Garantiza 100% de cobertura para preguntas críticas
"""

from typing import Optional, List, Tuple
import re


# Queries predefinidas: (patterns, sql)
# patterns: lista de strings que deben estar en la pregunta (OR)
# O tupla (required, any_of) donde required debe estar Y any_of es opcional
_QUERY_PATTERNS: List[Tuple] = [
    # RENTABILIDAD (orden importa - específicos primero)
    (
        ["rentabilidad por área", "rentabilidad de cada área"],
        "SELECT a.nombre,((SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END)-SUM(CASE WHEN o.tipo_operacion='GASTO' THEN o.monto_uyu ELSE 0 END))/NULLIF(SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END),0))*100 AS rent FROM operaciones o JOIN areas a ON a.id=o.area_id WHERE o.deleted_at IS NULL AND a.nombre NOT IN ('Gastos Generales','Otros') AND DATE_TRUNC('month',o.fecha)=DATE_TRUNC('month',CURRENT_DATE) GROUP BY a.nombre ORDER BY rent DESC"
    ),
    (
        ["rentabilidad por localidad"],
        "SELECT o.localidad,((SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END)-SUM(CASE WHEN o.tipo_operacion='GASTO' THEN o.monto_uyu ELSE 0 END))/NULLIF(SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END),0))*100 AS rent FROM operaciones o WHERE o.deleted_at IS NULL AND DATE_TRUNC('month',o.fecha)=DATE_TRUNC('month',CURRENT_DATE) GROUP BY o.localidad ORDER BY rent DESC"
    ),
    (
        ["rentabilidad este mes", "rentabilidad del mes", "cuál es la rentabilidad"],
        "SELECT ((SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END)-SUM(CASE WHEN o.tipo_operacion='GASTO' THEN o.monto_uyu ELSE 0 END))/NULLIF(SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END),0))*100 AS rentabilidad FROM operaciones o WHERE o.deleted_at IS NULL AND DATE_TRUNC('month',o.fecha)=DATE_TRUNC('month',CURRENT_DATE)"
    ),
    # COMPARACIONES GEOGRÁFICAS
    (
        ["mercedes vs montevideo", "mercedes montevideo", "comparar mercedes", "comparación mercedes"],
        "SELECT o.localidad,SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END) AS ing,SUM(CASE WHEN o.tipo_operacion='GASTO' THEN o.monto_uyu ELSE 0 END) AS gas FROM operaciones o WHERE o.deleted_at IS NULL AND DATE_TRUNC('month',o.fecha)=DATE_TRUNC('month',CURRENT_DATE) GROUP BY o.localidad ORDER BY ing DESC"
    ),
    # CÓMO VENIMOS
    (
        ["cómo venimos", "como venimos", "cómo vamos"],
        "SELECT SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END) AS ing,SUM(CASE WHEN tipo_operacion='GASTO' THEN monto_uyu ELSE 0 END) AS gas,SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END)-SUM(CASE WHEN tipo_operacion='GASTO' THEN monto_uyu ELSE 0 END) AS res FROM operaciones WHERE deleted_at IS NULL AND DATE_TRUNC('month',fecha)=DATE_TRUNC('month',CURRENT_DATE)"
    ),
    # OPERACIONES
    (
        ["cuántas operaciones"],
        "SELECT COUNT(*) AS total FROM operaciones WHERE deleted_at IS NULL AND DATE_TRUNC('month',fecha)=DATE_TRUNC('month',CURRENT_DATE)"
    ),
    # CAPITAL/FLUJO
    (
        ["capital de trabajo", "capital trabajo"],
        "SELECT SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END)-SUM(CASE WHEN tipo_operacion='GASTO' THEN monto_uyu ELSE 0 END)-SUM(CASE WHEN tipo_operacion='RETIRO' THEN monto_uyu ELSE 0 END)-SUM(CASE WHEN tipo_operacion='DISTRIBUCION' THEN monto_uyu ELSE 0 END) AS capital FROM operaciones WHERE deleted_at IS NULL"
    ),
    (
        ["flujo de caja", "flujo caja"],
        "SELECT SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END) AS ent,SUM(CASE WHEN tipo_operacion IN ('GASTO','RETIRO','DISTRIBUCION') THEN monto_uyu ELSE 0 END) AS sal,SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END)-SUM(CASE WHEN tipo_operacion IN ('GASTO','RETIRO','DISTRIBUCION') THEN monto_uyu ELSE 0 END) AS flujo FROM operaciones WHERE deleted_at IS NULL AND DATE_TRUNC('month',fecha)=DATE_TRUNC('month',CURRENT_DATE)"
    ),
    # TENDENCIAS
    (
        ["análisis de tendencias", "tendencias"],
        "SELECT DATE_TRUNC('month',fecha) AS mes,SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END) AS ing FROM operaciones WHERE deleted_at IS NULL AND fecha>=DATE_TRUNC('month',CURRENT_DATE)-INTERVAL'11 months' GROUP BY 1 ORDER BY 1"
    ),
]

# Queries con doble condición (requiere ambos patterns)
_QUERY_COMPOUND: List[Tuple[str, str, str]] = [
    ("retiro", "mercedes", "SELECT SUM(monto_uyu) AS total_uyu, SUM(monto_usd) AS total_usd, COUNT(*) AS cantidad FROM operaciones WHERE tipo_operacion='RETIRO' AND localidad='MERCEDES' AND deleted_at IS NULL AND DATE_TRUNC('year',fecha)=DATE_TRUNC('year',CURRENT_DATE)"),
    ("retiro", "montevideo", "SELECT SUM(monto_uyu) AS total_uyu, SUM(monto_usd) AS total_usd, COUNT(*) AS cantidad FROM operaciones WHERE tipo_operacion='RETIRO' AND localidad='MONTEVIDEO' AND deleted_at IS NULL AND DATE_TRUNC('year',fecha)=DATE_TRUNC('year',CURRENT_DATE)"),
]


class QueryFallback:
    """Queries predefinidas con matching basado en patrones estructurados."""
    
    @staticmethod
    def get_query_for(pregunta: str) -> Optional[str]:
        """Retorna SQL predefinido según patrones en la pregunta."""
        p = pregunta.lower()
        
        # Si menciona año específico, dejar que Claude maneje
        if re.search(r'\b(2024|2025|2023|2022)\b', p):
            return None
        
        # Buscar en queries compuestas (requieren 2 condiciones)
        for req1, req2, sql in _QUERY_COMPOUND:
            if req1 in p and req2 in p:
                return sql
        
        # Buscar en patterns simples
        for patterns, sql in _QUERY_PATTERNS:
            if any(pattern in p for pattern in patterns):
                return sql
        
        return None
