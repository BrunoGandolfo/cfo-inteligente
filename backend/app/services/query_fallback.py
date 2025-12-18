"""
Sistema de fallback robusto para queries comunes
Garantiza 100% de cobertura para preguntas críticas
"""

from typing import Optional


class QueryFallback:
    """
    Queries predefinidas con matching flexible
    """
    
    @staticmethod
    def get_query_for(pregunta: str) -> Optional[str]:
        """
        Retorna SQL predefinido según patrones en la pregunta
        """
        p = pregunta.lower()
        
        # Si menciona año específico, dejar que Claude maneje (más preciso)
        import re
        if re.search(r'\b(2024|2025|2023|2022)\b', p):
            return None
        
        # RENTABILIDAD (patrones específicos ANTES de generales)
        if "rentabilidad por área" in p or "rentabilidad de cada área" in p:
            return "SELECT a.nombre,((SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END)-SUM(CASE WHEN o.tipo_operacion='GASTO' THEN o.monto_uyu ELSE 0 END))/NULLIF(SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END),0))*100 AS rent FROM operaciones o JOIN areas a ON a.id=o.area_id WHERE o.deleted_at IS NULL AND a.nombre NOT IN ('Gastos Generales','Otros') AND DATE_TRUNC('month',o.fecha)=DATE_TRUNC('month',CURRENT_DATE) GROUP BY a.nombre ORDER BY rent DESC"
        
        if "rentabilidad por localidad" in p:
            return "SELECT o.localidad,((SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END)-SUM(CASE WHEN o.tipo_operacion='GASTO' THEN o.monto_uyu ELSE 0 END))/NULLIF(SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END),0))*100 AS rent FROM operaciones o WHERE o.deleted_at IS NULL AND DATE_TRUNC('month',o.fecha)=DATE_TRUNC('month',CURRENT_DATE) GROUP BY o.localidad ORDER BY rent DESC"
        
        if any(x in p for x in ["rentabilidad este mes", "rentabilidad del mes", "cuál es la rentabilidad"]):
            return "SELECT ((SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END)-SUM(CASE WHEN o.tipo_operacion='GASTO' THEN o.monto_uyu ELSE 0 END))/NULLIF(SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END),0))*100 AS rentabilidad FROM operaciones o WHERE o.deleted_at IS NULL AND DATE_TRUNC('month',o.fecha)=DATE_TRUNC('month',CURRENT_DATE)"
        
        # COMPARACIONES GEOGRÁFICAS
        if any(x in p for x in ["mercedes vs montevideo", "mercedes montevideo", "comparar mercedes", "comparación mercedes"]):
            return "SELECT o.localidad,SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END) AS ing,SUM(CASE WHEN o.tipo_operacion='GASTO' THEN o.monto_uyu ELSE 0 END) AS gas FROM operaciones o WHERE o.deleted_at IS NULL AND DATE_TRUNC('month',o.fecha)=DATE_TRUNC('month',CURRENT_DATE) GROUP BY o.localidad ORDER BY ing DESC"
        
        # RETIROS POR LOCALIDAD
        if "retiro" in p and "mercedes" in p:
            return "SELECT SUM(monto_uyu) AS total_uyu, SUM(monto_usd) AS total_usd, COUNT(*) AS cantidad FROM operaciones WHERE tipo_operacion='RETIRO' AND localidad='MERCEDES' AND deleted_at IS NULL AND DATE_TRUNC('year',fecha)=DATE_TRUNC('year',CURRENT_DATE)"
        
        if "retiro" in p and "montevideo" in p:
            return "SELECT SUM(monto_uyu) AS total_uyu, SUM(monto_usd) AS total_usd, COUNT(*) AS cantidad FROM operaciones WHERE tipo_operacion='RETIRO' AND localidad='MONTEVIDEO' AND deleted_at IS NULL AND DATE_TRUNC('year',fecha)=DATE_TRUNC('year',CURRENT_DATE)"
        
        # CÓMO VENIMOS
        if "cómo venimos" in p or "como venimos" in p or "cómo vamos" in p:
            return "SELECT SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END) AS ing,SUM(CASE WHEN tipo_operacion='GASTO' THEN monto_uyu ELSE 0 END) AS gas,SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END)-SUM(CASE WHEN tipo_operacion='GASTO' THEN monto_uyu ELSE 0 END) AS res FROM operaciones WHERE deleted_at IS NULL AND DATE_TRUNC('month',fecha)=DATE_TRUNC('month',CURRENT_DATE)"
        
        # OPERACIONES
        if "cuántas operaciones" in p:
            return "SELECT COUNT(*) AS total FROM operaciones WHERE deleted_at IS NULL AND DATE_TRUNC('month',fecha)=DATE_TRUNC('month',CURRENT_DATE)"
        
        # CAPITAL/FLUJO
        if "capital de trabajo" in p or "capital trabajo" in p:
            return "SELECT SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END)-SUM(CASE WHEN tipo_operacion='GASTO' THEN monto_uyu ELSE 0 END)-SUM(CASE WHEN tipo_operacion='RETIRO' THEN monto_uyu ELSE 0 END)-SUM(CASE WHEN tipo_operacion='DISTRIBUCION' THEN monto_uyu ELSE 0 END) AS capital FROM operaciones WHERE deleted_at IS NULL"
        
        if "flujo de caja" in p or "flujo caja" in p:
            return "SELECT SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END) AS ent,SUM(CASE WHEN tipo_operacion IN ('GASTO','RETIRO','DISTRIBUCION') THEN monto_uyu ELSE 0 END) AS sal,SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END)-SUM(CASE WHEN tipo_operacion IN ('GASTO','RETIRO','DISTRIBUCION') THEN monto_uyu ELSE 0 END) AS flujo FROM operaciones WHERE deleted_at IS NULL AND DATE_TRUNC('month',fecha)=DATE_TRUNC('month',CURRENT_DATE)"
        
        # TENDENCIAS/ANÁLISIS
        if "análisis de tendencias" in p or "tendencias" in p:
            return "SELECT DATE_TRUNC('month',fecha) AS mes,SUM(CASE WHEN tipo_operacion='INGRESO' THEN monto_uyu ELSE 0 END) AS ing FROM operaciones WHERE deleted_at IS NULL AND fecha>=DATE_TRUNC('month',CURRENT_DATE)-INTERVAL'11 months' GROUP BY 1 ORDER BY 1"
        
        return None
