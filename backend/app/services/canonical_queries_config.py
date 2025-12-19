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

QUERIES_CANONICAS = {
    # ══════════════════════════════════════════════════════════════
    # FACTURACIÓN
    # ══════════════════════════════════════════════════════════════
    "facturacion_2025": {
        "patrones": ["facturación 2025", "facturamos 2025", "ingresos 2025", 
                    "facturación este año", "facturamos este año", "ingresos este año"],
        "sql_control": """
            SELECT SUM(monto_uyu) as total FROM operaciones 
            WHERE tipo_operacion = 'INGRESO' AND deleted_at IS NULL 
            AND EXTRACT(YEAR FROM fecha) = 2025
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01  # 1%
    },
    "facturacion_2024": {
        "patrones": ["facturación 2024", "facturamos 2024", "ingresos 2024"],
        "sql_control": """
            SELECT SUM(monto_uyu) as total FROM operaciones 
            WHERE tipo_operacion = 'INGRESO' AND deleted_at IS NULL 
            AND EXTRACT(YEAR FROM fecha) = 2024
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01
    },
    "facturacion_mes_actual": {
        "patrones": ["facturación este mes", "facturamos este mes", "ingresos del mes"],
        "sql_control": """
            SELECT SUM(monto_uyu) as total FROM operaciones 
            WHERE tipo_operacion = 'INGRESO' AND deleted_at IS NULL 
            AND DATE_TRUNC('month', fecha) = DATE_TRUNC('month', CURRENT_DATE)
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01
    },
    
    # ══════════════════════════════════════════════════════════════
    # GASTOS
    # ══════════════════════════════════════════════════════════════
    "gastos_2025": {
        "patrones": ["gastos 2025", "gastamos 2025", "gastos este año"],
        "sql_control": """
            SELECT SUM(monto_uyu) as total FROM operaciones 
            WHERE tipo_operacion = 'GASTO' AND deleted_at IS NULL 
            AND EXTRACT(YEAR FROM fecha) = 2025
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01
    },
    "gastos_2024": {
        "patrones": ["gastos 2024", "gastamos 2024"],
        "sql_control": """
            SELECT SUM(monto_uyu) as total FROM operaciones 
            WHERE tipo_operacion = 'GASTO' AND deleted_at IS NULL 
            AND EXTRACT(YEAR FROM fecha) = 2024
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01
    },
    
    # ══════════════════════════════════════════════════════════════
    # RENTABILIDAD
    # ══════════════════════════════════════════════════════════════
    "rentabilidad_2025": {
        "patrones": ["rentabilidad 2025", "rentabilidad este año", "margen 2025"],
        "sql_control": """
            SELECT ROUND(
                (SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN monto_uyu ELSE 0 END) -
                 SUM(CASE WHEN tipo_operacion = 'GASTO' THEN monto_uyu ELSE 0 END)) /
                NULLIF(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN monto_uyu ELSE 0 END), 0) * 100
            , 2) as porcentaje FROM operaciones 
            WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = 2025
        """,
        "campo_resultado": "porcentaje",
        "tolerancia": 0.5  # 0.5 puntos porcentuales
    },
    "rentabilidad_mes_actual": {
        "patrones": ["rentabilidad este mes", "rentabilidad del mes", "margen del mes"],
        "sql_control": """
            SELECT ROUND(
                (SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN monto_uyu ELSE 0 END) -
                 SUM(CASE WHEN tipo_operacion = 'GASTO' THEN monto_uyu ELSE 0 END)) /
                NULLIF(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN monto_uyu ELSE 0 END), 0) * 100
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
            SELECT SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN monto_uyu ELSE 0 END) -
                   SUM(CASE WHEN tipo_operacion = 'GASTO' THEN monto_uyu ELSE 0 END) -
                   SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN monto_uyu ELSE 0 END) -
                   SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN monto_uyu ELSE 0 END) as total
            FROM operaciones WHERE deleted_at IS NULL
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01
    },
    
    # ══════════════════════════════════════════════════════════════
    # POR LOCALIDAD
    # ══════════════════════════════════════════════════════════════
    "facturacion_montevideo_2025": {
        "patrones": ["facturación montevideo 2025", "facturamos montevideo", 
                    "ingresos montevideo 2025", "montevideo 2025 facturación"],
        "sql_control": """
            SELECT SUM(monto_uyu) as total FROM operaciones 
            WHERE tipo_operacion = 'INGRESO' AND deleted_at IS NULL 
            AND EXTRACT(YEAR FROM fecha) = 2025 AND localidad = 'MONTEVIDEO'
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01
    },
    "facturacion_mercedes_2025": {
        "patrones": ["facturación mercedes 2025", "facturamos mercedes", 
                    "ingresos mercedes 2025", "mercedes 2025 facturación"],
        "sql_control": """
            SELECT SUM(monto_uyu) as total FROM operaciones 
            WHERE tipo_operacion = 'INGRESO' AND deleted_at IS NULL 
            AND EXTRACT(YEAR FROM fecha) = 2025 AND localidad = 'MERCEDES'
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01
    },
    
    # ══════════════════════════════════════════════════════════════
    # POR ÁREA
    # ══════════════════════════════════════════════════════════════
    "facturacion_juridica_2025": {
        "patrones": ["facturación jurídica 2025", "jurídica 2025", 
                    "área jurídica 2025", "ingresos jurídica"],
        "sql_control": """
            SELECT SUM(o.monto_uyu) as total FROM operaciones o
            JOIN areas a ON o.area_id = a.id
            WHERE o.tipo_operacion = 'INGRESO' AND o.deleted_at IS NULL 
            AND EXTRACT(YEAR FROM o.fecha) = 2025 AND a.nombre = 'Jurídica'
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01
    },
    "facturacion_notarial_2025": {
        "patrones": ["facturación notarial 2025", "notarial 2025", 
                    "área notarial 2025", "ingresos notarial"],
        "sql_control": """
            SELECT SUM(o.monto_uyu) as total FROM operaciones o
            JOIN areas a ON o.area_id = a.id
            WHERE o.tipo_operacion = 'INGRESO' AND o.deleted_at IS NULL 
            AND EXTRACT(YEAR FROM o.fecha) = 2025 AND a.nombre = 'Notarial'
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01
    },
    "facturacion_contable_2025": {
        "patrones": ["facturación contable 2025", "contable 2025", 
                    "área contable 2025", "ingresos contable"],
        "sql_control": """
            SELECT SUM(o.monto_uyu) as total FROM operaciones o
            JOIN areas a ON o.area_id = a.id
            WHERE o.tipo_operacion = 'INGRESO' AND o.deleted_at IS NULL 
            AND EXTRACT(YEAR FROM o.fecha) = 2025 AND a.nombre = 'Contable'
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01
    },
    
    # ══════════════════════════════════════════════════════════════
    # DISTRIBUCIONES
    # ══════════════════════════════════════════════════════════════
    "distribuciones_2025": {
        "patrones": ["distribuciones 2025", "distribuciones este año", 
                    "total distribuido 2025", "cuánto se distribuyó 2025"],
        "sql_control": """
            SELECT SUM(dd.monto_uyu) as total 
            FROM distribuciones_detalle dd
            JOIN operaciones o ON dd.operacion_id = o.id
            WHERE o.tipo_operacion = 'DISTRIBUCION' AND o.deleted_at IS NULL
            AND EXTRACT(YEAR FROM o.fecha) = 2025
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01
    },
    "distribuciones_2024": {
        "patrones": ["distribuciones 2024", "total distribuido 2024", 
                    "cuánto se distribuyó 2024"],
        "sql_control": """
            SELECT SUM(dd.monto_uyu) as total 
            FROM distribuciones_detalle dd
            JOIN operaciones o ON dd.operacion_id = o.id
            WHERE o.tipo_operacion = 'DISTRIBUCION' AND o.deleted_at IS NULL
            AND EXTRACT(YEAR FROM o.fecha) = 2024
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01
    },
    
    # ══════════════════════════════════════════════════════════════
    # RETIROS
    # ══════════════════════════════════════════════════════════════
    "retiros_2025": {
        "patrones": ["retiros 2025", "retiros este año", "total retiros 2025"],
        "sql_control": """
            SELECT SUM(monto_uyu) as total FROM operaciones 
            WHERE tipo_operacion = 'RETIRO' AND deleted_at IS NULL 
            AND EXTRACT(YEAR FROM fecha) = 2025
        """,
        "campo_resultado": "total",
        "tolerancia": 0.01
    },
    
    # ══════════════════════════════════════════════════════════════
    # OPERACIONES
    # ══════════════════════════════════════════════════════════════
    "cantidad_operaciones_2025": {
        "patrones": ["cuántas operaciones 2025", "operaciones este año", 
                    "cantidad operaciones 2025"],
        "sql_control": """
            SELECT COUNT(*) as total FROM operaciones 
            WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = 2025
        """,
        "campo_resultado": "total",
        "tolerancia": 0  # Debe ser exacto
    },
}



