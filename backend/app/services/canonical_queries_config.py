"""
Configuración de Queries Canónicas - CFO Inteligente

Diccionario de queries de control pre-validadas para validación de respuestas.
Cada query tiene:
- patrones: Lista de frases que activan la validación
- sql_control: SQL que da el resultado correcto
- campo_resultado: Campo a extraer del resultado
- tolerancia: % de diferencia aceptable (0.01 = 1%)

Extraído de validador_canonico.py para mejor mantenibilidad.
"""

from app.core.constants import ANIO_ACTUAL

QUERIES_CANONICAS = {
    # ══════════════════════════════════════════════════════════════
    # FACTURACIÓN
    # ══════════════════════════════════════════════════════════════
    "facturacion_anio_actual": {
        "patrones": [f"facturación {ANIO_ACTUAL}", f"facturamos {ANIO_ACTUAL}", f"ingresos {ANIO_ACTUAL}", 
                    "facturación este año", "facturamos este año", "ingresos este año"],
        "sql_control": f"""
            SELECT SUM(total_pesificado) as total FROM operaciones 
            WHERE tipo_operacion = 'INGRESO' AND deleted_at IS NULL 
            AND EXTRACT(YEAR FROM fecha) = {ANIO_ACTUAL}
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01  # 1%
    },
    "facturacion_2024": {
        "patrones": ["facturación 2024", "facturamos 2024", "ingresos 2024"],
        "sql_control": """
            SELECT SUM(total_pesificado) as total FROM operaciones 
            WHERE tipo_operacion = 'INGRESO' AND deleted_at IS NULL 
            AND EXTRACT(YEAR FROM fecha) = 2024
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01
    },
    "facturacion_mes_actual": {
        "patrones": ["facturación este mes", "facturamos este mes", "ingresos del mes"],
        "sql_control": """
            SELECT SUM(total_pesificado) as total FROM operaciones 
            WHERE tipo_operacion = 'INGRESO' AND deleted_at IS NULL 
            AND DATE_TRUNC('month', fecha) = DATE_TRUNC('month', CURRENT_DATE)
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01
    },
    
    # ══════════════════════════════════════════════════════════════
    # GASTOS
    # ══════════════════════════════════════════════════════════════
    "gastos_anio_actual": {
        "patrones": [f"gastos {ANIO_ACTUAL}", f"gastamos {ANIO_ACTUAL}", "gastos este año"],
        "sql_control": f"""
            SELECT SUM(total_pesificado) as total FROM operaciones 
            WHERE tipo_operacion = 'GASTO' AND deleted_at IS NULL 
            AND EXTRACT(YEAR FROM fecha) = {ANIO_ACTUAL}
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01
    },
    "gastos_2024": {
        "patrones": ["gastos 2024", "gastamos 2024"],
        "sql_control": """
            SELECT SUM(total_pesificado) as total FROM operaciones 
            WHERE tipo_operacion = 'GASTO' AND deleted_at IS NULL 
            AND EXTRACT(YEAR FROM fecha) = 2024
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01
    },
    
    # ══════════════════════════════════════════════════════════════
    # RENTABILIDAD
    # ══════════════════════════════════════════════════════════════
    "rentabilidad_anio_actual": {
        "patrones": [f"rentabilidad {ANIO_ACTUAL}", "rentabilidad este año", f"margen {ANIO_ACTUAL}"],
        "sql_control": f"""
            SELECT ROUND(
                (SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END) -
                 SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END)) /
                NULLIF(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) * 100
            , 2) as porcentaje FROM operaciones 
            WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = {ANIO_ACTUAL}
        """,
        "campo_resultado": "porcentaje",
        "tolerancia": 0.5  # 0.5 puntos porcentuales
    },
    "rentabilidad_mes_actual": {
        "patrones": ["rentabilidad este mes", "rentabilidad del mes", "margen del mes"],
        "sql_control": """
            SELECT ROUND(
                (SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END) -
                 SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END)) /
                NULLIF(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END), 0) * 100
            , 2) as porcentaje FROM operaciones 
            WHERE deleted_at IS NULL 
            AND DATE_TRUNC('month', fecha) = DATE_TRUNC('month', CURRENT_DATE)
        """,
        "campo_resultado": "porcentaje",
        "tolerancia": 0.5
    },
    
    # ══════════════════════════════════════════════════════════════
    # CAPITAL Y FLUJO
    # ══════════════════════════════════════════════════════════════
    "capital_trabajo": {
        "patrones": ["capital de trabajo", "capital trabajo", "capital disponible"],
        "sql_control": """
            SELECT SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END) -
                   SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END) -
                   SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END) as total
            FROM operaciones WHERE deleted_at IS NULL
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01
    },
    
    # ══════════════════════════════════════════════════════════════
    # POR LOCALIDAD
    # ══════════════════════════════════════════════════════════════
    "facturacion_montevideo_anio_actual": {
        "patrones": [f"facturación montevideo {ANIO_ACTUAL}", "facturamos montevideo", 
                    f"ingresos montevideo {ANIO_ACTUAL}", f"montevideo {ANIO_ACTUAL} facturación"],
        "sql_control": f"""
            SELECT SUM(total_pesificado) as total FROM operaciones 
            WHERE tipo_operacion = 'INGRESO' AND deleted_at IS NULL 
            AND EXTRACT(YEAR FROM fecha) = {ANIO_ACTUAL} AND localidad = 'MONTEVIDEO'
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01
    },
    "facturacion_mercedes_anio_actual": {
        "patrones": [f"facturación mercedes {ANIO_ACTUAL}", "facturamos mercedes", 
                    f"ingresos mercedes {ANIO_ACTUAL}", f"mercedes {ANIO_ACTUAL} facturación"],
        "sql_control": f"""
            SELECT SUM(total_pesificado) as total FROM operaciones 
            WHERE tipo_operacion = 'INGRESO' AND deleted_at IS NULL 
            AND EXTRACT(YEAR FROM fecha) = {ANIO_ACTUAL} AND localidad = 'MERCEDES'
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01
    },
    
    # ══════════════════════════════════════════════════════════════
    # POR ÁREA
    # ══════════════════════════════════════════════════════════════
    "facturacion_juridica_anio_actual": {
        "patrones": [f"facturación jurídica {ANIO_ACTUAL}", f"jurídica {ANIO_ACTUAL}", 
                    f"área jurídica {ANIO_ACTUAL}", "ingresos jurídica"],
        "sql_control": f"""
            SELECT SUM(o.total_pesificado) as total FROM operaciones o
            JOIN areas a ON o.area_id = a.id
            WHERE o.tipo_operacion = 'INGRESO' AND o.deleted_at IS NULL 
            AND EXTRACT(YEAR FROM o.fecha) = {ANIO_ACTUAL} AND a.nombre = 'Jurídica'
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01
    },
    "facturacion_notarial_anio_actual": {
        "patrones": [f"facturación notarial {ANIO_ACTUAL}", f"notarial {ANIO_ACTUAL}", 
                    f"área notarial {ANIO_ACTUAL}", "ingresos notarial"],
        "sql_control": f"""
            SELECT SUM(o.total_pesificado) as total FROM operaciones o
            JOIN areas a ON o.area_id = a.id
            WHERE o.tipo_operacion = 'INGRESO' AND o.deleted_at IS NULL 
            AND EXTRACT(YEAR FROM o.fecha) = {ANIO_ACTUAL} AND a.nombre = 'Notarial'
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01
    },
    "facturacion_contable_anio_actual": {
        "patrones": [f"facturación contable {ANIO_ACTUAL}", f"contable {ANIO_ACTUAL}", 
                    f"área contable {ANIO_ACTUAL}", "ingresos contable"],
        "sql_control": f"""
            SELECT SUM(o.total_pesificado) as total FROM operaciones o
            JOIN areas a ON o.area_id = a.id
            WHERE o.tipo_operacion = 'INGRESO' AND o.deleted_at IS NULL 
            AND EXTRACT(YEAR FROM o.fecha) = {ANIO_ACTUAL} AND a.nombre = 'Contable'
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01
    },
    
    # ══════════════════════════════════════════════════════════════
    # DISTRIBUCIONES
    # ══════════════════════════════════════════════════════════════
    "distribuciones_anio_actual": {
        "patrones": [f"distribuciones {ANIO_ACTUAL}", "distribuciones este año", 
                    f"total distribuido {ANIO_ACTUAL}", f"cuánto se distribuyó {ANIO_ACTUAL}"],
        "sql_control": f"""
            SELECT SUM(total_pesificado) as total 
            FROM operaciones
            WHERE tipo_operacion = 'DISTRIBUCION' AND deleted_at IS NULL
            AND EXTRACT(YEAR FROM fecha) = {ANIO_ACTUAL}
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01
    },
    "distribuciones_2024": {
        "patrones": ["distribuciones 2024", "total distribuido 2024", 
                    "cuánto se distribuyó 2024"],
        "sql_control": """
            SELECT SUM(total_pesificado) as total 
            FROM operaciones
            WHERE tipo_operacion = 'DISTRIBUCION' AND deleted_at IS NULL
            AND EXTRACT(YEAR FROM fecha) = 2024
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01
    },
    
    # ══════════════════════════════════════════════════════════════
    # RETIROS
    # ══════════════════════════════════════════════════════════════
    "retiros_anio_actual": {
        "patrones": [f"retiros {ANIO_ACTUAL}", "retiros este año", f"total retiros {ANIO_ACTUAL}"],
        "sql_control": f"""
            SELECT SUM(total_pesificado) as total FROM operaciones 
            WHERE tipo_operacion = 'RETIRO' AND deleted_at IS NULL 
            AND EXTRACT(YEAR FROM fecha) = {ANIO_ACTUAL}
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01
    },
    
    # ══════════════════════════════════════════════════════════════
    # OPERACIONES
    # ══════════════════════════════════════════════════════════════
    "cantidad_operaciones_anio_actual": {
        "patrones": [f"cuántas operaciones {ANIO_ACTUAL}", "operaciones este año", 
                    f"cantidad operaciones {ANIO_ACTUAL}"],
        "sql_control": f"""
            SELECT COUNT(*) as total FROM operaciones 
            WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = {ANIO_ACTUAL}
        """,
        "campo_resultado": "total",
        "tolerancia": 0  # Debe ser exacto
    },
}


