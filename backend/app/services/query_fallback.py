"""
Sistema de fallback robusto para queries comunes.
Garantiza 100% de cobertura para preguntas críticas.

Incluye:
- Queries estáticas para preguntas comunes
- Queries PARAMETRIZADAS para comparaciones temporales (2024 vs 2025, etc.)
- Templates EJECUTIVOS COMPLETOS para informes de directorio
"""

from typing import Optional, List, Tuple
import re


# ═══════════════════════════════════════════════════════════════════════════════
# TEMPLATES PARAMETRIZADOS PARA COMPARACIONES TEMPORALES
# ═══════════════════════════════════════════════════════════════════════════════

def _template_comparar_dos_años(año1: str, año2: str) -> str:
    """Compara ingresos, gastos y resultado entre dos años."""
    return f"""
SELECT 
    periodo,
    ingresos,
    gastos,
    ingresos - gastos AS resultado,
    CASE WHEN ingresos > 0 THEN ROUND(((ingresos - gastos) / ingresos) * 100, 2) ELSE 0 END AS rentabilidad_pct
FROM (
    SELECT 
        '{año1}' AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND EXTRACT(YEAR FROM fecha) = {año1}
    
    UNION ALL
    
    SELECT 
        '{año2}' AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND EXTRACT(YEAR FROM fecha) = {año2}
) sub
ORDER BY periodo
"""


def _template_comparar_tres_años(año1: str, año2: str, año3: str) -> str:
    """Compara ingresos, gastos y resultado entre tres años."""
    return f"""
SELECT 
    periodo,
    ingresos,
    gastos,
    ingresos - gastos AS resultado,
    CASE WHEN ingresos > 0 THEN ROUND(((ingresos - gastos) / ingresos) * 100, 2) ELSE 0 END AS rentabilidad_pct
FROM (
    SELECT 
        '{año1}' AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND EXTRACT(YEAR FROM fecha) = {año1}
    
    UNION ALL
    
    SELECT 
        '{año2}' AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND EXTRACT(YEAR FROM fecha) = {año2}
    
    UNION ALL
    
    SELECT 
        '{año3}' AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND EXTRACT(YEAR FROM fecha) = {año3}
) sub
ORDER BY periodo
"""


def _template_informe_año(año: str) -> str:
    """Informe mensual completo de un año específico."""
    return f"""
SELECT 
    EXTRACT(MONTH FROM fecha)::INTEGER AS mes,
    TO_CHAR(fecha, 'Month') AS nombre_mes,
    COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos,
    COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos,
    COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) - 
    COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS resultado
FROM operaciones 
WHERE deleted_at IS NULL 
AND EXTRACT(YEAR FROM fecha) = {año}
GROUP BY EXTRACT(MONTH FROM fecha), TO_CHAR(fecha, 'Month')
ORDER BY mes
"""


def _template_año_vs_anterior(año: str) -> str:
    """Compara un año con el año anterior."""
    año_anterior = str(int(año) - 1)
    return _template_comparar_dos_años(año_anterior, año)


def _template_resumen_año(año: str) -> str:
    """Resumen totales de un año específico."""
    return f"""
SELECT 
    '{año}' AS año,
    COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_totales,
    COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_totales,
    COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) - 
    COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS resultado_neto,
    COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END), 0) AS distribuciones,
    COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros,
    COUNT(*) AS total_operaciones
FROM operaciones 
WHERE deleted_at IS NULL 
AND EXTRACT(YEAR FROM fecha) = {año}
"""


def _template_rentabilidad_por_area_año(año: str) -> str:
    """Rentabilidad por área en un año específico."""
    return f"""
SELECT 
    a.nombre AS area,
    COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos,
    COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos,
    COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) - 
    COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS resultado,
    CASE 
        WHEN SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) > 0 
        THEN ROUND(((SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) - 
                     SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END)) / 
                    SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END)) * 100, 2)
        ELSE 0 
    END AS rentabilidad_pct
FROM operaciones o
JOIN areas a ON a.id = o.area_id
WHERE o.deleted_at IS NULL 
AND a.nombre NOT IN ('Otros Gastos')
AND EXTRACT(YEAR FROM o.fecha) = {año}
GROUP BY a.nombre
ORDER BY rentabilidad_pct DESC
"""


def _template_comparar_trimestres(año1: str, año2: str) -> str:
    """Compara los 4 trimestres entre dos años."""
    return f"""
SELECT 
    periodo,
    trimestre,
    ingresos,
    gastos,
    ingresos - gastos AS resultado
FROM (
    SELECT '{año1}' AS periodo, 'Q1' AS trimestre,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos
    FROM operaciones WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = {año1} AND EXTRACT(QUARTER FROM fecha) = 1
    UNION ALL
    SELECT '{año1}', 'Q2',
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0),
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0)
    FROM operaciones WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = {año1} AND EXTRACT(QUARTER FROM fecha) = 2
    UNION ALL
    SELECT '{año1}', 'Q3',
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0),
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0)
    FROM operaciones WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = {año1} AND EXTRACT(QUARTER FROM fecha) = 3
    UNION ALL
    SELECT '{año1}', 'Q4',
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0),
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0)
    FROM operaciones WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = {año1} AND EXTRACT(QUARTER FROM fecha) = 4
    UNION ALL
    SELECT '{año2}', 'Q1',
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0),
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0)
    FROM operaciones WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = {año2} AND EXTRACT(QUARTER FROM fecha) = 1
    UNION ALL
    SELECT '{año2}', 'Q2',
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0),
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0)
    FROM operaciones WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = {año2} AND EXTRACT(QUARTER FROM fecha) = 2
    UNION ALL
    SELECT '{año2}', 'Q3',
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0),
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0)
    FROM operaciones WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = {año2} AND EXTRACT(QUARTER FROM fecha) = 3
    UNION ALL
    SELECT '{año2}', 'Q4',
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0),
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0)
    FROM operaciones WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = {año2} AND EXTRACT(QUARTER FROM fecha) = 4
) sub
ORDER BY periodo, trimestre
"""


def _template_comparar_semestres(año1: str, año2: str) -> str:
    """Compara los 2 semestres entre dos años."""
    return f"""
SELECT 
    periodo,
    semestre,
    ingresos,
    gastos,
    ingresos - gastos AS resultado
FROM (
    SELECT '{año1}' AS periodo, 'S1' AS semestre,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos
    FROM operaciones WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = {año1} AND EXTRACT(MONTH FROM fecha) BETWEEN 1 AND 6
    UNION ALL
    SELECT '{año1}', 'S2',
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0),
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0)
    FROM operaciones WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = {año1} AND EXTRACT(MONTH FROM fecha) BETWEEN 7 AND 12
    UNION ALL
    SELECT '{año2}', 'S1',
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0),
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0)
    FROM operaciones WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = {año2} AND EXTRACT(MONTH FROM fecha) BETWEEN 1 AND 6
    UNION ALL
    SELECT '{año2}', 'S2',
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0),
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0)
    FROM operaciones WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = {año2} AND EXTRACT(MONTH FROM fecha) BETWEEN 7 AND 12
) sub
ORDER BY periodo, semestre
"""


def _template_comparar_mes_entre_años(mes: int, año1: str, año2: str) -> str:
    """Compara el mismo mes entre dos años (ej: enero 2024 vs enero 2025)."""
    meses_nombre = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    nombre_mes = meses_nombre.get(mes, f'Mes {mes}')
    
    return f"""
SELECT 
    periodo,
    ingresos,
    gastos,
    ingresos - gastos AS resultado,
    CASE WHEN ingresos > 0 THEN ROUND(((ingresos - gastos) / ingresos) * 100, 2) ELSE 0 END AS rentabilidad_pct
FROM (
    SELECT '{nombre_mes} {año1}' AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND EXTRACT(YEAR FROM fecha) = {año1} 
    AND EXTRACT(MONTH FROM fecha) = {mes}
    
    UNION ALL
    
    SELECT '{nombre_mes} {año2}' AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND EXTRACT(YEAR FROM fecha) = {año2} 
    AND EXTRACT(MONTH FROM fecha) = {mes}
) sub
ORDER BY periodo
"""


def _template_comparar_meses_mismo_año(mes1: int, mes2: int, año: str) -> str:
    """Compara dos meses del mismo año (ej: marzo vs abril 2024)."""
    meses_nombre = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    nombre_mes1 = meses_nombre.get(mes1, f'Mes {mes1}')
    nombre_mes2 = meses_nombre.get(mes2, f'Mes {mes2}')
    
    return f"""
SELECT 
    periodo,
    ingresos,
    gastos,
    ingresos - gastos AS resultado,
    CASE WHEN ingresos > 0 THEN ROUND(((ingresos - gastos) / ingresos) * 100, 2) ELSE 0 END AS rentabilidad_pct
FROM (
    SELECT '{nombre_mes1} {año}' AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND EXTRACT(YEAR FROM fecha) = {año} 
    AND EXTRACT(MONTH FROM fecha) = {mes1}
    
    UNION ALL
    
    SELECT '{nombre_mes2} {año}' AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND EXTRACT(YEAR FROM fecha) = {año} 
    AND EXTRACT(MONTH FROM fecha) = {mes2}
) sub
ORDER BY periodo
"""


def _template_comparar_trimestre_especifico(trimestre: int, año1: str, año2: str) -> str:
    """Compara un trimestre específico entre dos años (ej: Q1 2024 vs Q1 2025)."""
    return f"""
SELECT 
    periodo,
    ingresos,
    gastos,
    ingresos - gastos AS resultado,
    CASE WHEN ingresos > 0 THEN ROUND(((ingresos - gastos) / ingresos) * 100, 2) ELSE 0 END AS rentabilidad_pct
FROM (
    SELECT 'Q{trimestre} {año1}' AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND EXTRACT(YEAR FROM fecha) = {año1} 
    AND EXTRACT(QUARTER FROM fecha) = {trimestre}
    
    UNION ALL
    
    SELECT 'Q{trimestre} {año2}' AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND EXTRACT(YEAR FROM fecha) = {año2} 
    AND EXTRACT(QUARTER FROM fecha) = {trimestre}
) sub
ORDER BY periodo
"""


def _template_comparar_areas(area1: str, area2: str) -> str:
    """Compara dos áreas específicas (ej: Jurídica vs Contable)."""
    return f"""
SELECT 
    a.nombre AS area,
    COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos,
    COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos,
    COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) - 
    COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS resultado,
    CASE 
        WHEN SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) > 0 
        THEN ROUND(((SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) - 
                     SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END)) / 
                    SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END)) * 100, 2)
        ELSE 0 
    END AS rentabilidad_pct
FROM operaciones o
JOIN areas a ON a.id = o.area_id
WHERE o.deleted_at IS NULL 
AND a.nombre IN ('{area1}', '{area2}')
AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
GROUP BY a.nombre
ORDER BY ingresos DESC
"""


def _template_comparar_todas_areas() -> str:
    """Compara todas las áreas operativas."""
    return """
SELECT 
    a.nombre AS area,
    COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos,
    COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos,
    COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) - 
    COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS resultado,
    CASE 
        WHEN SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) > 0 
        THEN ROUND(((SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) - 
                     SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END)) / 
                    SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END)) * 100, 2)
        ELSE 0 
    END AS rentabilidad_pct
FROM operaciones o
JOIN areas a ON a.id = o.area_id
WHERE o.deleted_at IS NULL 
AND a.nombre NOT IN ('Otros Gastos')
AND DATE_TRUNC('year', o.fecha) = DATE_TRUNC('year', CURRENT_DATE)
GROUP BY a.nombre
ORDER BY rentabilidad_pct DESC
"""


# ═══════════════════════════════════════════════════════════════════════════════
# TEMPLATES EJECUTIVOS COMPLETOS (PARA DIRECTORIO)
# ═══════════════════════════════════════════════════════════════════════════════

def _template_informe_ejecutivo_año(año: str) -> str:
    """
    Informe ejecutivo completo de un año.
    Incluye: totales, por área, por localidad, por mes, retiros (por localidad/moneda),
    distribuciones por socio, rentabilidad, top clientes, top proveedores.
    
    NOTA: Retiros son de LA EMPRESA (no de socios), clasificados por localidad y moneda.
    """
    return f"""
WITH 
-- SECCIÓN 1: TOTALES GENERALES
totales AS (
    SELECT 
        '01_TOTALES' AS seccion,
        'GENERAL' AS dimension,
        '{año}' AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END), 0) AS distribuciones_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_dolarizado ELSE 0 END), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = {año}
),

-- SECCIÓN 2: POR ÁREA
por_area AS (
    SELECT 
        '02_POR_AREA' AS seccion,
        a.nombre AS dimension,
        '{año}' AS periodo,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones o
    JOIN areas a ON a.id = o.area_id
    WHERE o.deleted_at IS NULL AND EXTRACT(YEAR FROM o.fecha) = {año}
    GROUP BY a.nombre
),

-- SECCIÓN 3: POR LOCALIDAD
por_localidad AS (
    SELECT 
        '03_POR_LOCALIDAD' AS seccion,
        localidad::TEXT AS dimension,
        '{año}' AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = {año}
    GROUP BY localidad
),

-- SECCIÓN 4: POR MES
por_mes AS (
    SELECT 
        '04_POR_MES' AS seccion,
        TO_CHAR(fecha, 'MM-Mon') AS dimension,
        '{año}' AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END), 0) AS distribuciones_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_dolarizado ELSE 0 END), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = {año}
    GROUP BY TO_CHAR(fecha, 'MM-Mon')
),

-- SECCIÓN 5: RETIROS DE LA EMPRESA (por localidad y moneda)
retiros_empresa AS (
    SELECT 
        '05_RETIROS_EMPRESA' AS seccion,
        localidad::TEXT || ' - ' || moneda_original::TEXT AS dimension,
        '{año}' AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        COALESCE(SUM(total_pesificado), 0) AS retiros_uyu,
        COALESCE(SUM(total_dolarizado), 0) AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND tipo_operacion = 'RETIRO'
    AND EXTRACT(YEAR FROM fecha) = {año}
    GROUP BY localidad, moneda_original
),

-- SECCIÓN 6: DISTRIBUCIONES A SOCIOS
distribuciones_socios AS (
    SELECT 
        '06_DISTRIBUCIONES_SOCIOS' AS seccion,
        s.nombre || ' (' || dd.porcentaje || '%)' AS dimension,
        '{año}' AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        COALESCE(SUM(dd.total_pesificado), 0) AS distribuciones_uyu,
        COALESCE(SUM(dd.total_dolarizado), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM distribuciones_detalle dd
    JOIN operaciones o ON o.id = dd.operacion_id
    JOIN socios s ON s.id = dd.socio_id
    WHERE o.deleted_at IS NULL AND EXTRACT(YEAR FROM o.fecha) = {año}
    GROUP BY s.nombre, dd.porcentaje
),

-- SECCIÓN 7: RENTABILIDAD POR ÁREA
rentabilidad_area AS (
    SELECT 
        '07_RENTABILIDAD_AREA' AS seccion,
        a.nombre || ' -> ' || 
        ROUND(
            CASE WHEN SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) > 0
            THEN ((SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) - 
                   SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END)) /
                  SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) * 100)
            ELSE 0 END
        , 1)::TEXT || '% rentabilidad' AS dimension,
        '{año}' AS periodo,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones o
    JOIN areas a ON a.id = o.area_id
    WHERE o.deleted_at IS NULL 
    AND a.nombre != 'Otros Gastos'
    AND EXTRACT(YEAR FROM o.fecha) = {año}
    GROUP BY a.nombre
),

-- SECCIÓN 8: TOP 10 CLIENTES
top_clientes AS (
    SELECT 
        '08_TOP_CLIENTES' AS seccion,
        COALESCE(cliente, 'Sin especificar') AS dimension,
        '{año}' AS periodo,
        COALESCE(SUM(total_pesificado), 0) AS ingresos_uyu,
        COALESCE(SUM(total_dolarizado), 0) AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND tipo_operacion = 'INGRESO'
    AND EXTRACT(YEAR FROM fecha) = {año}
    AND cliente IS NOT NULL AND cliente != ''
    GROUP BY cliente
    ORDER BY SUM(total_pesificado) DESC
    LIMIT 10
),

-- SECCIÓN 9: TOP 10 PROVEEDORES
top_proveedores AS (
    SELECT 
        '09_TOP_PROVEEDORES' AS seccion,
        COALESCE(proveedor, 'Sin especificar') AS dimension,
        '{año}' AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        COALESCE(SUM(total_pesificado), 0) AS gastos_uyu,
        COALESCE(SUM(total_dolarizado), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND tipo_operacion = 'GASTO'
    AND EXTRACT(YEAR FROM fecha) = {año}
    AND proveedor IS NOT NULL AND proveedor != ''
    GROUP BY proveedor
    ORDER BY SUM(total_pesificado) DESC
    LIMIT 10
)

SELECT * FROM totales
UNION ALL SELECT * FROM por_area
UNION ALL SELECT * FROM por_localidad
UNION ALL SELECT * FROM por_mes
UNION ALL SELECT * FROM retiros_empresa
UNION ALL SELECT * FROM distribuciones_socios
UNION ALL SELECT * FROM rentabilidad_area
UNION ALL SELECT * FROM top_clientes
UNION ALL SELECT * FROM top_proveedores
ORDER BY seccion, dimension
"""


def _template_comparacion_ejecutiva_años(año1: str, año2: str) -> str:
    """
    Comparación ejecutiva completa entre dos años.
    Incluye todas las dimensiones con datos de ambos años para comparación.
    
    NOTA: Retiros son de LA EMPRESA (por localidad/moneda), no de socios.
          Distribuciones SÍ son por socio.
    """
    return f"""
WITH 
-- SECCIÓN 1: TOTALES POR AÑO
totales AS (
    SELECT 
        '01_TOTALES' AS seccion,
        'AÑO ' || EXTRACT(YEAR FROM fecha)::TEXT AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END), 0) AS distribuciones_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_dolarizado ELSE 0 END), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) IN ({año1}, {año2})
    GROUP BY EXTRACT(YEAR FROM fecha)
),

-- SECCIÓN 2: POR ÁREA (cada área × cada año)
por_area AS (
    SELECT 
        '02_POR_AREA' AS seccion,
        a.nombre || ' (' || EXTRACT(YEAR FROM o.fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM o.fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones o
    JOIN areas a ON a.id = o.area_id
    WHERE o.deleted_at IS NULL AND EXTRACT(YEAR FROM o.fecha) IN ({año1}, {año2})
    GROUP BY a.nombre, EXTRACT(YEAR FROM o.fecha)
),

-- SECCIÓN 3: POR LOCALIDAD (cada localidad × cada año)
por_localidad AS (
    SELECT 
        '03_POR_LOCALIDAD' AS seccion,
        localidad::TEXT || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) IN ({año1}, {año2})
    GROUP BY localidad, EXTRACT(YEAR FROM fecha)
),

-- SECCIÓN 4: POR MES (mes × año)
por_mes AS (
    SELECT 
        '04_POR_MES' AS seccion,
        TO_CHAR(fecha, 'Mon') || ' ' || EXTRACT(YEAR FROM fecha)::TEXT AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT || '-' || TO_CHAR(fecha, 'MM') AS periodo,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END), 0) AS retiros_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_dolarizado ELSE 0 END), 0) AS retiros_usd,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END), 0) AS distribuciones_uyu,
        COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_dolarizado ELSE 0 END), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) IN ({año1}, {año2})
    GROUP BY EXTRACT(YEAR FROM fecha), TO_CHAR(fecha, 'MM'), TO_CHAR(fecha, 'Mon')
),

-- SECCIÓN 5: RETIROS DE LA EMPRESA (por localidad × moneda × año)
retiros_empresa AS (
    SELECT 
        '05_RETIROS_EMPRESA' AS seccion,
        localidad::TEXT || ' ' || moneda_original::TEXT || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        COALESCE(SUM(total_pesificado), 0) AS retiros_uyu,
        COALESCE(SUM(total_dolarizado), 0) AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones 
    WHERE deleted_at IS NULL 
    AND tipo_operacion = 'RETIRO'
    AND EXTRACT(YEAR FROM fecha) IN ({año1}, {año2})
    GROUP BY localidad, moneda_original, EXTRACT(YEAR FROM fecha)
),

-- SECCIÓN 6: DISTRIBUCIONES POR SOCIO (socio × año)
distribuciones_socios AS (
    SELECT 
        '06_DISTRIBUCIONES_SOCIOS' AS seccion,
        s.nombre || ' ' || dd.porcentaje || '% (' || EXTRACT(YEAR FROM o.fecha)::TEXT || ')' AS dimension,
        EXTRACT(YEAR FROM o.fecha)::TEXT AS periodo,
        0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
        0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        COALESCE(SUM(dd.total_pesificado), 0) AS distribuciones_uyu,
        COALESCE(SUM(dd.total_dolarizado), 0) AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM distribuciones_detalle dd
    JOIN operaciones o ON o.id = dd.operacion_id
    JOIN socios s ON s.id = dd.socio_id
    WHERE o.deleted_at IS NULL AND EXTRACT(YEAR FROM o.fecha) IN ({año1}, {año2})
    GROUP BY s.nombre, dd.porcentaje, EXTRACT(YEAR FROM o.fecha)
),

-- SECCIÓN 7: RENTABILIDAD POR ÁREA (área × año)
rentabilidad_area AS (
    SELECT 
        '07_RENTABILIDAD_AREA' AS seccion,
        a.nombre || ' (' || EXTRACT(YEAR FROM o.fecha)::TEXT || ') -> ' || 
        ROUND(
            CASE WHEN SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) > 0
            THEN ((SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) - 
                   SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END)) /
                  SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END) * 100)
            ELSE 0 END
        , 1)::TEXT || '%' AS dimension,
        EXTRACT(YEAR FROM o.fecha)::TEXT AS periodo,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_pesificado ELSE 0 END), 0) AS ingresos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'INGRESO' THEN o.total_dolarizado ELSE 0 END), 0) AS ingresos_usd,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_pesificado ELSE 0 END), 0) AS gastos_uyu,
        COALESCE(SUM(CASE WHEN o.tipo_operacion = 'GASTO' THEN o.total_dolarizado ELSE 0 END), 0) AS gastos_usd,
        0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
        0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
        COUNT(*) AS cantidad_operaciones
    FROM operaciones o
    JOIN areas a ON a.id = o.area_id
    WHERE o.deleted_at IS NULL 
    AND a.nombre != 'Otros Gastos'
    AND EXTRACT(YEAR FROM o.fecha) IN ({año1}, {año2})
    GROUP BY a.nombre, EXTRACT(YEAR FROM o.fecha)
),

-- SECCIÓN 8: TOP 5 CLIENTES POR AÑO
top_clientes AS (
    SELECT seccion, dimension, periodo, ingresos_uyu, ingresos_usd, 
           gastos_uyu, gastos_usd, retiros_uyu, retiros_usd, 
           distribuciones_uyu, distribuciones_usd, cantidad_operaciones
    FROM (
        SELECT 
            '08_TOP_CLIENTES' AS seccion,
            COALESCE(cliente, 'Sin especificar') || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
            EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
            COALESCE(SUM(total_pesificado), 0) AS ingresos_uyu,
            COALESCE(SUM(total_dolarizado), 0) AS ingresos_usd,
            0::NUMERIC AS gastos_uyu, 0::NUMERIC AS gastos_usd,
            0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
            0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
            COUNT(*) AS cantidad_operaciones,
            ROW_NUMBER() OVER (PARTITION BY EXTRACT(YEAR FROM fecha) ORDER BY SUM(total_pesificado) DESC) AS rn
        FROM operaciones 
        WHERE deleted_at IS NULL 
        AND tipo_operacion = 'INGRESO'
        AND EXTRACT(YEAR FROM fecha) IN ({año1}, {año2})
        AND cliente IS NOT NULL AND cliente != ''
        GROUP BY cliente, EXTRACT(YEAR FROM fecha)
    ) t WHERE rn <= 5
),

-- SECCIÓN 9: TOP 5 PROVEEDORES POR AÑO
top_proveedores AS (
    SELECT seccion, dimension, periodo, ingresos_uyu, ingresos_usd, 
           gastos_uyu, gastos_usd, retiros_uyu, retiros_usd, 
           distribuciones_uyu, distribuciones_usd, cantidad_operaciones
    FROM (
        SELECT 
            '09_TOP_PROVEEDORES' AS seccion,
            COALESCE(proveedor, 'Sin especificar') || ' (' || EXTRACT(YEAR FROM fecha)::TEXT || ')' AS dimension,
            EXTRACT(YEAR FROM fecha)::TEXT AS periodo,
            0::NUMERIC AS ingresos_uyu, 0::NUMERIC AS ingresos_usd,
            COALESCE(SUM(total_pesificado), 0) AS gastos_uyu,
            COALESCE(SUM(total_dolarizado), 0) AS gastos_usd,
            0::NUMERIC AS retiros_uyu, 0::NUMERIC AS retiros_usd,
            0::NUMERIC AS distribuciones_uyu, 0::NUMERIC AS distribuciones_usd,
            COUNT(*) AS cantidad_operaciones,
            ROW_NUMBER() OVER (PARTITION BY EXTRACT(YEAR FROM fecha) ORDER BY SUM(total_pesificado) DESC) AS rn
        FROM operaciones 
        WHERE deleted_at IS NULL 
        AND tipo_operacion = 'GASTO'
        AND EXTRACT(YEAR FROM fecha) IN ({año1}, {año2})
        AND proveedor IS NOT NULL AND proveedor != ''
        GROUP BY proveedor, EXTRACT(YEAR FROM fecha)
    ) t WHERE rn <= 5
)

SELECT * FROM totales
UNION ALL SELECT * FROM por_area
UNION ALL SELECT * FROM por_localidad
UNION ALL SELECT * FROM por_mes
UNION ALL SELECT * FROM retiros_empresa
UNION ALL SELECT * FROM distribuciones_socios
UNION ALL SELECT * FROM rentabilidad_area
UNION ALL SELECT * FROM top_clientes
UNION ALL SELECT * FROM top_proveedores
ORDER BY seccion, periodo, dimension
"""


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES HELPER PARA DETECTAR PATRONES TEMPORALES
# ═══════════════════════════════════════════════════════════════════════════════

def _extraer_años(texto: str) -> List[str]:
    """Extrae todos los años (4 dígitos entre 2020-2030) de un texto."""
    años = re.findall(r'\b(20[2-3]\d)\b', texto)
    return sorted(set(años))


# Mapeo de nombres de meses a números
_MESES_MAP = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
    'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
    'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
    'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4,
    'may': 5, 'jun': 6, 'jul': 7, 'ago': 8,
    'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12,
}


def _extraer_meses(texto: str) -> List[int]:
    """Extrae los meses mencionados en el texto."""
    texto_lower = texto.lower()
    meses_encontrados = []
    
    for nombre, numero in _MESES_MAP.items():
        if nombre in texto_lower:
            if numero not in meses_encontrados:
                meses_encontrados.append(numero)
    
    return sorted(meses_encontrados)


def _extraer_trimestre_especifico(texto: str) -> Optional[int]:
    """Extrae número de trimestre específico (Q1, Q2, Q3, Q4, primer trimestre, etc)."""
    texto_lower = texto.lower()
    
    # Buscar Q1, Q2, Q3, Q4
    match = re.search(r'\bq([1-4])\b', texto_lower)
    if match:
        return int(match.group(1))
    
    # Buscar "primer/segundo/tercer/cuarto trimestre"
    ordinal_map = {
        'primer': 1, 'primero': 1, '1er': 1, '1º': 1,
        'segundo': 2, '2do': 2, '2º': 2,
        'tercer': 3, 'tercero': 3, '3er': 3, '3º': 3,
        'cuarto': 4, '4to': 4, '4º': 4,
    }
    
    for ordinal, num in ordinal_map.items():
        if ordinal in texto_lower and 'trimestre' in texto_lower:
            return num
    
    return None


# Mapeo de nombres de áreas (con variantes)
_AREAS_MAP = {
    'jurídica': 'Jurídica', 'juridica': 'Jurídica', 'legal': 'Jurídica',
    'contable': 'Contable', 'contabilidad': 'Contable',
    'recuperación': 'Recuperación', 'recuperacion': 'Recuperación', 'cobranzas': 'Recuperación',
    'notarial': 'Notarial', 'notaria': 'Notarial', 'escribanía': 'Notarial', 'escribania': 'Notarial',
}


def _extraer_areas(texto: str) -> List[str]:
    """Extrae las áreas mencionadas en el texto."""
    texto_lower = texto.lower()
    areas_encontradas = []
    
    for variante, nombre_oficial in _AREAS_MAP.items():
        if variante in texto_lower:
            if nombre_oficial not in areas_encontradas:
                areas_encontradas.append(nombre_oficial)
    
    return areas_encontradas


def _detectar_informe_ejecutivo(pregunta: str) -> Optional[str]:
    """
    Detecta si la pregunta es un informe ejecutivo de un año o comparación de años.
    
    Patrones detectados:
    - "informe 2024", "resumen ejecutivo 2025", "análisis del 2024"
    - "comparar 2024 vs 2025", "2024 contra 2025", "diferencia 2024 y 2025"
    """
    p = pregunta.lower()
    
    # Extraer años mencionados (4 dígitos que empiezan con 20)
    años = re.findall(r'20\d{2}', p)
    años = sorted(set(años))  # Únicos y ordenados
    
    if not años:
        return None
    
    # Palabras clave para informe ejecutivo completo
    palabras_informe = [
        'informe', 'resumen', 'análisis', 'reporte', 'executive', 
        'completo', 'todo', 'detallado', 'ejecutivo'
    ]
    
    # Palabras clave para comparación
    palabras_comparacion = [
        'vs', 'versus', 'contra', 'comparar', 'comparación', 'diferencia',
        'respecto', 'comparado', 'comparativa'
    ]
    
    es_informe = any(palabra in p for palabra in palabras_informe)
    es_comparacion = any(palabra in p for palabra in palabras_comparacion) or len(años) >= 2
    
    # CASO 1: Comparación de dos años
    if len(años) >= 2 and (es_comparacion or es_informe):
        return _template_comparacion_ejecutiva_años(años[0], años[1])
    
    # CASO 2: Informe de un año específico
    if len(años) == 1 and es_informe:
        return _template_informe_ejecutivo_año(años[0])
    
    return None


def _detectar_comparacion_años(pregunta: str) -> Optional[str]:
    """
    Detecta si la pregunta es una comparación temporal y retorna SQL parametrizado.
    
    Patrones soportados:
    - "Comparar 2024 vs 2025"
    - "2024 contra 2025"
    - "Comparación 2023, 2024 y 2025"
    - "Comparar trimestres de 2024 contra 2025"
    - "Q1 2024 vs Q1 2025"
    - "Primer trimestre 2024 vs 2025"
    - "Semestres de 2024 vs 2025"
    - "Enero 2024 vs enero 2025"
    - "Marzo vs abril 2024"
    """
    p = pregunta.lower()
    años = _extraer_años(p)
    meses = _extraer_meses(p)
    trimestre_especifico = _extraer_trimestre_especifico(p)
    
    # Detectar intención de comparación
    palabras_comparacion = ['compar', 'vs', 'versus', 'contra', 'diferencia', 'evolución', 'evolucion']
    es_comparacion = any(palabra in p for palabra in palabras_comparacion)
    
    # ═══════════════════════════════════════════════════════════════
    # PRIORIDAD 1: MESES ESPECÍFICOS
    # ═══════════════════════════════════════════════════════════════
    
    # Caso: "enero 2024 vs enero 2025" (mismo mes, diferentes años)
    if len(meses) == 1 and len(años) == 2 and es_comparacion:
        return _template_comparar_mes_entre_años(meses[0], años[0], años[1])
    
    # Caso: "marzo vs abril 2024" (diferentes meses, mismo año)
    if len(meses) == 2 and len(años) == 1 and es_comparacion:
        return _template_comparar_meses_mismo_año(meses[0], meses[1], años[0])
    
    # ═══════════════════════════════════════════════════════════════
    # PRIORIDAD 2: TRIMESTRE ESPECÍFICO (Q1, Q2, Q3, Q4)
    # ═══════════════════════════════════════════════════════════════
    
    # Caso: "Q1 2024 vs Q1 2025" o "primer trimestre 2024 vs 2025"
    if trimestre_especifico and len(años) == 2:
        return _template_comparar_trimestre_especifico(trimestre_especifico, años[0], años[1])
    
    # ═══════════════════════════════════════════════════════════════
    # PRIORIDAD 3: TODOS LOS TRIMESTRES/SEMESTRES
    # ═══════════════════════════════════════════════════════════════
    
    if len(años) >= 2:
        # TRIMESTRES: si menciona "trimestre" (sin especificar cuál), comparar todos
        if 'trimestre' in p and not trimestre_especifico:
            return _template_comparar_trimestres(años[0], años[1])
        
        # SEMESTRES: si menciona "semestre" con 2+ años
        if 'semestre' in p:
            return _template_comparar_semestres(años[0], años[1])
    
    # ═══════════════════════════════════════════════════════════════
    # PRIORIDAD 4: AÑOS COMPLETOS
    # ═══════════════════════════════════════════════════════════════
    
    if es_comparacion and len(años) >= 2:
        if len(años) == 2:
            return _template_comparar_dos_años(años[0], años[1])
        elif len(años) >= 3:
            return _template_comparar_tres_años(años[0], años[1], años[2])
    
    return None


def _detectar_comparacion_areas(pregunta: str) -> Optional[str]:
    """
    Detecta si la pregunta es una comparación de áreas.
    
    Patrones soportados:
    - "Comparar Jurídica vs Contable"
    - "Jurídica contra Notarial"
    - "Comparar todas las áreas"
    """
    p = pregunta.lower()
    areas = _extraer_areas(p)
    
    # Detectar intención de comparación
    palabras_comparacion = ['compar', 'vs', 'versus', 'contra', 'diferencia']
    es_comparacion = any(palabra in p for palabra in palabras_comparacion)
    
    # Caso: "comparar todas las áreas"
    if es_comparacion and ('todas' in p or 'cada' in p) and 'área' in p:
        return _template_comparar_todas_areas()
    
    # Caso: dos áreas específicas
    if len(areas) == 2 and es_comparacion:
        return _template_comparar_areas(areas[0], areas[1])
    
    return None


def _detectar_informe_año(pregunta: str) -> Optional[str]:
    """
    Detecta si la pregunta pide un informe/resumen de un año específico.
    
    Patrones soportados:
    - "Informe del 2024"
    - "Resumen 2025"
    - "Reporte completo del 2024"
    - "Cómo fue el 2024"
    """
    p = pregunta.lower()
    años = _extraer_años(p)
    
    if len(años) != 1:
        return None
    
    año = años[0]
    
    # Detectar tipo de informe
    if any(x in p for x in ['informe', 'reporte', 'detalle', 'desglose', 'mes a mes', 'mensual']):
        return _template_informe_año(año)
    
    if any(x in p for x in ['rentabilidad', 'área', 'area']):
        return _template_rentabilidad_por_area_año(año)
    
    if any(x in p for x in ['resumen', 'total', 'cuánto', 'cuanto', 'resultado']):
        return _template_resumen_año(año)
    
    if any(x in p for x in ['respecto', 'anterior', 'pasado', 'mejoramos', 'crecimos']):
        return _template_año_vs_anterior(año)
    
    # Default: resumen del año
    return _template_resumen_año(año)


# ═══════════════════════════════════════════════════════════════════════════════
# QUERIES ESTÁTICAS (sin parámetros)
# ═══════════════════════════════════════════════════════════════════════════════

_QUERY_PATTERNS: List[Tuple] = [
    # RENTABILIDAD (orden importa - específicos primero)
    (
        ["rentabilidad por área", "rentabilidad de cada área"],
        "SELECT a.nombre,((SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.total_pesificado ELSE 0 END)-SUM(CASE WHEN o.tipo_operacion='GASTO' THEN o.total_pesificado ELSE 0 END))/NULLIF(SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.total_pesificado ELSE 0 END),0))*100 AS rent FROM operaciones o JOIN areas a ON a.id=o.area_id WHERE o.deleted_at IS NULL AND a.nombre NOT IN ('Otros Gastos') AND DATE_TRUNC('month',o.fecha)=DATE_TRUNC('month',CURRENT_DATE) GROUP BY a.nombre ORDER BY rent DESC"
    ),
    (
        ["rentabilidad por localidad"],
        "SELECT o.localidad,((SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.total_pesificado ELSE 0 END)-SUM(CASE WHEN o.tipo_operacion='GASTO' THEN o.total_pesificado ELSE 0 END))/NULLIF(SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.total_pesificado ELSE 0 END),0))*100 AS rent FROM operaciones o WHERE o.deleted_at IS NULL AND DATE_TRUNC('month',o.fecha)=DATE_TRUNC('month',CURRENT_DATE) GROUP BY o.localidad ORDER BY rent DESC"
    ),
    (
        ["rentabilidad este mes", "rentabilidad del mes", "cuál es la rentabilidad"],
        "SELECT ((SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.total_pesificado ELSE 0 END)-SUM(CASE WHEN o.tipo_operacion='GASTO' THEN o.total_pesificado ELSE 0 END))/NULLIF(SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.total_pesificado ELSE 0 END),0))*100 AS rentabilidad FROM operaciones o WHERE o.deleted_at IS NULL AND DATE_TRUNC('month',o.fecha)=DATE_TRUNC('month',CURRENT_DATE)"
    ),
    # COMPARACIONES GEOGRÁFICAS
    (
        ["mercedes vs montevideo", "mercedes montevideo", "comparar mercedes", "comparación mercedes"],
        "SELECT o.localidad,SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.total_pesificado ELSE 0 END) AS ing,SUM(CASE WHEN o.tipo_operacion='GASTO' THEN o.total_pesificado ELSE 0 END) AS gas FROM operaciones o WHERE o.deleted_at IS NULL AND DATE_TRUNC('month',o.fecha)=DATE_TRUNC('month',CURRENT_DATE) GROUP BY o.localidad ORDER BY ing DESC"
    ),
    # CÓMO VENIMOS
    (
        ["cómo venimos", "como venimos", "cómo vamos"],
        "SELECT SUM(CASE WHEN tipo_operacion='INGRESO' THEN total_pesificado ELSE 0 END) AS ing,SUM(CASE WHEN tipo_operacion='GASTO' THEN total_pesificado ELSE 0 END) AS gas,SUM(CASE WHEN tipo_operacion='INGRESO' THEN total_pesificado ELSE 0 END)-SUM(CASE WHEN tipo_operacion='GASTO' THEN total_pesificado ELSE 0 END) AS res FROM operaciones WHERE deleted_at IS NULL AND DATE_TRUNC('month',fecha)=DATE_TRUNC('month',CURRENT_DATE)"
    ),
    # OPERACIONES
    (
        ["cuántas operaciones este mes", "operaciones del mes", "operaciones de este mes"],
        "SELECT COUNT(*) AS total FROM operaciones WHERE deleted_at IS NULL AND DATE_TRUNC('month',fecha)=DATE_TRUNC('month',CURRENT_DATE)"
    ),
    # CAPITAL/FLUJO
    (
        ["capital de trabajo", "capital trabajo"],
        "SELECT SUM(CASE WHEN tipo_operacion='INGRESO' THEN total_pesificado ELSE 0 END)-SUM(CASE WHEN tipo_operacion='GASTO' THEN total_pesificado ELSE 0 END)-SUM(CASE WHEN tipo_operacion='RETIRO' THEN total_pesificado ELSE 0 END)-SUM(CASE WHEN tipo_operacion='DISTRIBUCION' THEN total_pesificado ELSE 0 END) AS capital FROM operaciones WHERE deleted_at IS NULL"
    ),
    (
        ["flujo de caja", "flujo caja"],
        "SELECT SUM(CASE WHEN tipo_operacion='INGRESO' THEN total_pesificado ELSE 0 END) AS ent,SUM(CASE WHEN tipo_operacion='GASTO' THEN total_pesificado ELSE 0 END)+SUM(CASE WHEN tipo_operacion IN ('RETIRO','DISTRIBUCION') THEN total_pesificado ELSE 0 END) AS sal,SUM(CASE WHEN tipo_operacion='INGRESO' THEN total_pesificado ELSE 0 END)-SUM(CASE WHEN tipo_operacion='GASTO' THEN total_pesificado ELSE 0 END)-SUM(CASE WHEN tipo_operacion IN ('RETIRO','DISTRIBUCION') THEN total_pesificado ELSE 0 END) AS flujo FROM operaciones WHERE deleted_at IS NULL AND DATE_TRUNC('month',fecha)=DATE_TRUNC('month',CURRENT_DATE)"
    ),
    # TENDENCIAS
    (
        ["análisis de tendencias", "tendencias"],
        "SELECT DATE_TRUNC('month',fecha) AS mes,SUM(CASE WHEN tipo_operacion='INGRESO' THEN total_pesificado ELSE 0 END) AS ing FROM operaciones WHERE deleted_at IS NULL AND fecha>=DATE_TRUNC('month',CURRENT_DATE)-INTERVAL'11 months' GROUP BY 1 ORDER BY 1"
    ),
]

# Queries con doble condición (requiere ambos patterns)
_QUERY_COMPOUND: List[Tuple[str, str, str]] = [
    ("retiro", "mercedes", "SELECT SUM(total_pesificado) AS total_pesificado, SUM(monto_uyu) AS componente_uyu, SUM(monto_usd) AS componente_usd, COUNT(*) AS cantidad FROM operaciones WHERE tipo_operacion='RETIRO' AND localidad='MERCEDES' AND deleted_at IS NULL AND DATE_TRUNC('year',fecha)=DATE_TRUNC('year',CURRENT_DATE)"),
    ("retiro", "montevideo", "SELECT SUM(total_pesificado) AS total_pesificado, SUM(monto_uyu) AS componente_uyu, SUM(monto_usd) AS componente_usd, COUNT(*) AS cantidad FROM operaciones WHERE tipo_operacion='RETIRO' AND localidad='MONTEVIDEO' AND deleted_at IS NULL AND DATE_TRUNC('year',fecha)=DATE_TRUNC('year',CURRENT_DATE)"),
    # Distribuciones por socio
    ("distribu", "bruno", "SELECT SUM(dd.monto_uyu) AS total_uyu, SUM(dd.monto_usd) AS total_usd, COUNT(*) AS cantidad FROM distribuciones_detalle dd JOIN socios s ON s.id=dd.socio_id JOIN operaciones o ON o.id=dd.operacion_id WHERE s.nombre='Bruno' AND o.deleted_at IS NULL AND DATE_TRUNC('year',o.fecha)=DATE_TRUNC('year',CURRENT_DATE)"),
    ("distribu", "agustina", "SELECT SUM(dd.monto_uyu) AS total_uyu, SUM(dd.monto_usd) AS total_usd, COUNT(*) AS cantidad FROM distribuciones_detalle dd JOIN socios s ON s.id=dd.socio_id JOIN operaciones o ON o.id=dd.operacion_id WHERE s.nombre='Agustina' AND o.deleted_at IS NULL AND DATE_TRUNC('year',o.fecha)=DATE_TRUNC('year',CURRENT_DATE)"),
    ("distribu", "viviana", "SELECT SUM(dd.monto_uyu) AS total_uyu, SUM(dd.monto_usd) AS total_usd, COUNT(*) AS cantidad FROM distribuciones_detalle dd JOIN socios s ON s.id=dd.socio_id JOIN operaciones o ON o.id=dd.operacion_id WHERE s.nombre='Viviana' AND o.deleted_at IS NULL AND DATE_TRUNC('year',o.fecha)=DATE_TRUNC('year',CURRENT_DATE)"),
    ("distribu", "gonzalo", "SELECT SUM(dd.monto_uyu) AS total_uyu, SUM(dd.monto_usd) AS total_usd, COUNT(*) AS cantidad FROM distribuciones_detalle dd JOIN socios s ON s.id=dd.socio_id JOIN operaciones o ON o.id=dd.operacion_id WHERE s.nombre='Gonzalo' AND o.deleted_at IS NULL AND DATE_TRUNC('year',o.fecha)=DATE_TRUNC('year',CURRENT_DATE)"),
    ("distribu", "pancho", "SELECT SUM(dd.monto_uyu) AS total_uyu, SUM(dd.monto_usd) AS total_usd, COUNT(*) AS cantidad FROM distribuciones_detalle dd JOIN socios s ON s.id=dd.socio_id JOIN operaciones o ON o.id=dd.operacion_id WHERE s.nombre='Pancho' AND o.deleted_at IS NULL AND DATE_TRUNC('year',o.fecha)=DATE_TRUNC('year',CURRENT_DATE)"),
]


# ═══════════════════════════════════════════════════════════════════════════════
# CLASE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class QueryFallback:
    """
    Queries predefinidas con matching basado en patrones.
    
    Orden de prioridad:
    0. Informes ejecutivos completos (para directorio)
    1. Queries parametrizadas para comparaciones temporales
    2. Queries compuestas (requieren 2 condiciones)
    3. Queries simples (pattern matching)
    4. None (deja que Claude maneje)
    """
    
    @staticmethod
    def get_query_for(pregunta: str) -> Optional[str]:
        """Retorna SQL predefinido según patrones en la pregunta."""
        p = pregunta.lower()
        
        # ═══════════════════════════════════════════════════════════════
        # PRIORIDAD 0: INFORMES EJECUTIVOS COMPLETOS (PARA DIRECTORIO)
        # ═══════════════════════════════════════════════════════════════
        
        sql_ejecutivo = _detectar_informe_ejecutivo(p)
        if sql_ejecutivo:
            return sql_ejecutivo
        
        # ═══════════════════════════════════════════════════════════════
        # PRIORIDAD 1: QUERIES PARAMETRIZADAS (comparaciones temporales)
        # ═══════════════════════════════════════════════════════════════
        
        # Detectar comparación de años (2024 vs 2025, etc.)
        sql_comparacion = _detectar_comparacion_años(p)
        if sql_comparacion:
            return sql_comparacion
        
        # Detectar informe/resumen de año específico
        sql_informe = _detectar_informe_año(p)
        if sql_informe:
            return sql_informe
        
        # Detectar comparación de áreas (Jurídica vs Contable, etc.)
        sql_areas = _detectar_comparacion_areas(p)
        if sql_areas:
            return sql_areas
        
        # ═══════════════════════════════════════════════════════════════
        # PRIORIDAD 2: QUERIES COMPUESTAS (requieren 2 condiciones)
        # ═══════════════════════════════════════════════════════════════
        
        for req1, req2, sql in _QUERY_COMPOUND:
            if req1 in p and req2 in p:
                return sql
        
        # ═══════════════════════════════════════════════════════════════
        # PRIORIDAD 3: QUERIES SIMPLES (pattern matching)
        # ═══════════════════════════════════════════════════════════════
        
        for patterns, sql in _QUERY_PATTERNS:
            if any(pattern in p for pattern in patterns):
                return sql
        
        # ═══════════════════════════════════════════════════════════════
        # PRIORIDAD 4: DEJAR QUE CLAUDE MANEJE
        # ═══════════════════════════════════════════════════════════════
        
        return None
