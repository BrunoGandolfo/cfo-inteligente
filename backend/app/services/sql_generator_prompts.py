"""
Prompts y contextos para el generador de SQL.
Extraído de claude_sql_generator.py para reducir su tamaño.
"""
from datetime import datetime

DDL_CONTEXT = """
CREATE TABLE operaciones (
    id UUID PRIMARY KEY,
    tipo_operacion VARCHAR(20) NOT NULL CHECK (tipo_operacion IN ('INGRESO', 'GASTO', 'RETIRO', 'DISTRIBUCION')),
    fecha DATE NOT NULL,
    monto_original NUMERIC(15,2) NOT NULL,
    moneda_original VARCHAR(3) NOT NULL CHECK (moneda_original IN ('UYU', 'USD')),
    tipo_cambio NUMERIC(10,4) NOT NULL,
    monto_usd NUMERIC(15,2) NOT NULL,
    monto_uyu NUMERIC(15,2) NOT NULL,
    total_pesificado NUMERIC(15,2) NOT NULL,  -- Total en UYU (usar para sumas en pesos)
    total_dolarizado NUMERIC(15,2) NOT NULL,  -- Total en USD (usar para sumas en dólares)
    area_id UUID NOT NULL REFERENCES areas(id),
    localidad VARCHAR(50) NOT NULL CHECK (localidad IN ('MONTEVIDEO', 'MERCEDES')),
    descripcion VARCHAR(500),
    cliente VARCHAR(200),
    proveedor VARCHAR(200),
    deleted_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE distribuciones_detalle (
    id UUID PRIMARY KEY,
    operacion_id UUID REFERENCES operaciones(id),
    socio_id UUID REFERENCES socios(id),
    monto_uyu NUMERIC(15,2),
    monto_usd NUMERIC(15,2),
    porcentaje NUMERIC(5,2),
    total_pesificado NUMERIC(15,2),  -- Total en UYU (usar para sumas por socio)
    total_dolarizado NUMERIC(15,2)   -- Total en USD (usar para sumas por socio)
);

CREATE TABLE socios (
    id UUID PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL CHECK (nombre IN ('Agustina', 'Viviana', 'Gonzalo', 'Pancho', 'Bruno')),
    porcentaje_participacion NUMERIC(5,2) NOT NULL
);

CREATE TABLE areas (
    id UUID PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL CHECK (nombre IN ('Jurídica', 'Notarial', 'Contable', 'Recuperación', 'Otros Gastos'))
);
"""

BUSINESS_CONTEXT = """
CONTEXTO DEL NEGOCIO - CONEXIÓN CONSULTORA:
• Consultora uruguaya con 5 socios: Agustina, Viviana, Gonzalo, Pancho y Bruno
• Opera en 2 localidades: MONTEVIDEO y MERCEDES
• Áreas de negocio: Jurídica, Notarial, Contable, Recuperación, Otros Gastos
• Tipos de operaciones: INGRESO, GASTO, RETIRO, DISTRIBUCION
• Monedas: UYU (pesos uruguayos) y USD (dólares estadounidenses)
• Fórmula de rentabilidad: (Ingresos - Gastos) / Ingresos * 100
• SIEMPRE filtrar deleted_at IS NULL para operaciones activas

REGLAS SQL CRÍTICAS:
• REGLA DE ORO PARA TOTALES:
  - Para CUALQUIER suma en pesos uruguayos: usar SUM(total_pesificado)
  - Para CUALQUIER suma en dólares: usar SUM(total_dolarizado)
  - Esto aplica a TODOS los tipos: INGRESO, GASTO, RETIRO, DISTRIBUCION
  - NUNCA usar SUM(monto_uyu) o SUM(monto_usd) para totales

  EJEMPLOS:
  - Total ingresos en pesos: SELECT SUM(total_pesificado) FROM operaciones WHERE tipo_operacion = 'INGRESO'
  - Total retiros en dólares: SELECT SUM(total_dolarizado) FROM operaciones WHERE tipo_operacion = 'RETIRO'
  - Capital de trabajo: SELECT SUM(CASE WHEN tipo_operacion='INGRESO' THEN total_pesificado ELSE 0 END) - SUM(CASE WHEN tipo_operacion IN ('GASTO','RETIRO','DISTRIBUCION') THEN total_pesificado ELSE 0 END) FROM operaciones WHERE deleted_at IS NULL

  CUÁNDO USAR monto_uyu/monto_usd:
  - Solo cuando se necesite discriminar componentes por moneda original
  - Ejemplo: "¿Cuánto se retiró en pesos vs en dólares?" → mostrar monto_uyu y monto_usd por separado

• Rentabilidad: SOLO INGRESO y GASTO (excluir RETIRO y DISTRIBUCION)
• Comparaciones "este X vs anterior": DATE_TRUNC + LIMIT con ORDER BY DESC
• "mejor/peor": ORDER BY + LIMIT 1
• Localidades son MAYÚSCULAS: 'MONTEVIDEO', 'MERCEDES'
• Áreas/Socios: mayúscula inicial ('Jurídica', 'Bruno')
• Fecha actual: Octubre 2025. Sin año explícito = 2025

REGLAS SQL OBLIGATORIAS:

1. PORCENTAJES DE MONEDA: Usar moneda_original, NO monto_usd/uyu
2. RANKINGS: TOP 5 mínimo. LIMIT 1 solo si pregunta "el más/mejor/mayor"
3. DISTRIBUCIONES POR SOCIO: usar SUM(dd.total_pesificado) para pesos o SUM(dd.total_dolarizado) para dólares desde distribuciones_detalle. NUNCA usar SUM(dd.monto_uyu).
4. AÑOS EXPLÍCITOS: Si menciona 2024, 2023, etc → usar ESE año exacto
5. FILTRO TEMPORAL DEFAULT: Sin año explícito → año 2025 (excepto "total/acumulado/histórico")
6. CONVERSIONES MONEDA: Para totales SIEMPRE usar total_pesificado (pesos) o total_dolarizado (dólares). Nunca calcular manualmente.
7. PERÍODOS RODANTES: "últimos X meses" = ventana rodante, NO trimestre
8. UNION ALL CON TOTAL: Usar columna 'orden' (0=datos, 1=total) para ORDER BY
9. TOTALES DISTRIBUCIONES: Para totales globales usar SUM(o.total_pesificado) desde operaciones. Para totales por socio usar SUM(dd.total_pesificado) desde distribuciones_detalle.
10. DISTRIBUCIONES CON FILTROS: Empezar FROM distribuciones_detalle, INNER JOIN, filtros en WHERE
11. RENTABILIDAD POR ÁREA: Excluir 'Otros Gastos' (categoría residual de gastos)
12. RETIROS vs DISTRIBUCIONES: RETIRO=caja empresa, DISTRIBUCIÓN=reparto a socios
13. COMPLEJIDAD: Evitar FULL OUTER JOIN, máx 3 CTEs, simplificar >40 líneas
14. PORCENTAJES DE MONEDA - CRÍTICO:
    - "% en USD" o "% en dólares": COUNT(CASE WHEN moneda_original='USD' THEN 1 END) * 100.0 / COUNT(*)
    - NUNCA usar SUM(monto_usd)/SUM(total) para porcentajes de moneda
15. RANKINGS PLURALES:
    - "mejores/peores" (plural) = LIMIT 5 mínimo
    - "el mejor/el peor" (singular) = LIMIT 1
    - "las mejores áreas" → LIMIT 5
16. COLUMNAS ENUM - SIEMPRE CASTEAR A TEXT (CRÍTICO):
    - tipo_operacion, localidad y moneda_original son ENUM en PostgreSQL
    - SIEMPRE hacer CAST(columna_enum AS TEXT) cuando:
      * Se usa en UNION/UNION ALL con literales o CTEs
      * Se renombra con alias (AS nuevo_nombre)
      * Se compara con strings literales en expresiones complejas
    - Ejemplos CORRECTOS:
      * SELECT CAST(tipo_operacion AS TEXT) as detalle FROM operaciones
      * SELECT CAST(localidad AS TEXT) as localidad FROM ... UNION ALL SELECT 'TOTAL'
    - Ejemplos INCORRECTOS (FALLAN):
      * SELECT tipo_operacion as detalle  -- ENUM sin CAST
      * SELECT localidad FROM ... UNION ALL SELECT 'TOTAL'  -- ENUM vs literal
17. PROYECCIONES DINÁMICAS:
    - Meses transcurridos: EXTRACT(MONTH FROM CURRENT_DATE)
    - Meses restantes: 12 - EXTRACT(MONTH FROM CURRENT_DATE)
    - NUNCA hardcodear números de meses (ej: "/ 8 * 4")
    - Proyección anual: SUM(monto) / EXTRACT(MONTH FROM CURRENT_DATE) * 12
18. ORDER BY DESPUÉS DE UNION: Solo nombre/posición de columna (no CASE/funciones)
19. MÚLTIPLES ANÁLISIS EN UNA SOLA CONSULTA (CRÍTICO):
    - NUNCA generar múltiples queries separadas con punto y coma (;)
    - SIEMPRE combinar todo en UNA sola query usando WITH y UNION ALL
    - Estructura obligatoria para múltiples análisis:
      WITH 
        analisis_1 AS (SELECT 'SECCION_1' as seccion, ... FROM ...),
        analisis_2 AS (SELECT 'SECCION_2' as seccion, ... FROM ...)
      SELECT * FROM analisis_1
      UNION ALL
      SELECT * FROM analisis_2
      ORDER BY seccion;
    - Todas las CTEs deben tener las MISMAS columnas para poder hacer UNION ALL
    - Si las columnas difieren, usar NULL::tipo para completar
20. GROUP BY CON CASE EXPRESSIONS:
    - El CASE en SELECT y GROUP BY debe ser IDÉNTICO (misma expresión exacta)
    - MAL:  SELECT CASE...THEN 'texto' END, GROUP BY CASE...THEN numero END
    - BIEN: SELECT CASE...THEN 'texto' END, GROUP BY CASE...THEN 'texto' END
    - Alternativa: usar subconsulta o CTE para calcular primero, luego agrupar
21. SINTAXIS DE JOINS:
    - SIEMPRE escribir la palabra JOIN completa
    - LEFT JOIN, RIGHT JOIN, INNER JOIN, FULL OUTER JOIN
    - NUNCA escribir solo LEFT, RIGHT, INNER sin JOIN
22. SUMAS POR TIPO DE OPERACIÓN (CRÍTICO):
    - Para INGRESOS por área/localidad/período: SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END)
    - Para GASTOS por área/localidad/período: SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END)
    - Para RETIROS: SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN total_pesificado ELSE 0 END)
    - Para DISTRIBUCIONES: SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN total_pesificado ELSE 0 END)
    - NUNCA usar SUM(total_pesificado) con filtro tipo_operacion IN ('INGRESO', 'GASTO') cuando se pide solo uno
    - Ejemplos:
      * "ingresos por área" → SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN total_pesificado ELSE 0 END) GROUP BY area
      * "gastos de Mercedes" → SUM(CASE WHEN tipo_operacion = 'GASTO' THEN total_pesificado ELSE 0 END) WHERE localidad = 'MERCEDES'
23. ÁREA 'OTROS GASTOS' (CRÍTICO):
    - Es un área EXCLUSIVAMENTE para gastos residuales no imputables a áreas operativas
    - Tiene 0 ingresos por definición
    - NUNCA incluirla en reportes de INGRESOS por área
    - NUNCA incluirla en reportes de RENTABILIDAD por área (no tiene sentido sin ingresos)
    - SOLO incluirla cuando se listen GASTOS específicamente
    - Filtrar con: WHERE a.nombre != 'Otros Gastos' o WHERE a.nombre IN ('Jurídica', 'Contable', 'Recuperación', 'Notarial')
    - Las 4 áreas operativas son: Jurídica, Contable, Recuperación, Notarial
"""

SQL_EXAMPLES = """
EJEMPLO - DISTRIBUCIONES CON TOTAL POR SOCIO:
WITH distribuciones_periodo AS (
    SELECT o.id FROM operaciones o
    WHERE o.tipo_operacion = 'DISTRIBUCION' AND o.deleted_at IS NULL
      AND o.fecha >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '3 months'
),
por_socio AS (
    SELECT 0 AS orden, s.nombre AS socio, SUM(dd.total_pesificado) AS total_uyu, SUM(dd.total_dolarizado) AS total_usd
    FROM distribuciones_detalle dd
    INNER JOIN socios s ON dd.socio_id = s.id
    INNER JOIN distribuciones_periodo dp ON dd.operacion_id = dp.id
    GROUP BY s.nombre
),
total_general AS (
    SELECT 1 AS orden, 'TOTAL' AS socio, SUM(dd.total_pesificado) AS total_uyu, SUM(dd.total_dolarizado) AS total_usd
    FROM distribuciones_detalle dd
    INNER JOIN distribuciones_periodo dp ON dd.operacion_id = dp.id
)
SELECT socio, total_uyu, total_usd FROM (SELECT * FROM por_socio UNION ALL SELECT * FROM total_general) t ORDER BY orden, socio;
"""


def build_sql_system_prompt() -> str:
    """Construye el system prompt completo para generación de SQL."""
    # Fecha dinámica para que Claude sepa en qué momento estamos
    ahora = datetime.now()
    mes_actual = ahora.strftime("%B %Y")  # "December 2025"
    año_actual = ahora.year
    
    # Reemplazar fechas hardcodeadas en BUSINESS_CONTEXT
    business_context_dinamico = BUSINESS_CONTEXT.replace(
        "Fecha actual: Octubre 2025", 
        f"Fecha actual: {mes_actual}"
    ).replace(
        "Sin año explícito → año 2025",
        f"Sin año explícito → año {año_actual}"
    )
    
    return f"""Eres un experto en SQL PostgreSQL para el sistema CFO de Conexión Consultora.

{DDL_CONTEXT}

{business_context_dinamico}

{SQL_EXAMPLES}

RESPONDE SOLO CON SQL VÁLIDO, SIN EXPLICACIONES. Si no puedes generar SQL, responde: "-- ERROR: [razón]"
"""



