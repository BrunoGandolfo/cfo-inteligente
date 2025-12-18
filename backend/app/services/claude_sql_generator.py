"""
Generador de SQL con fallback multi-proveedor (Claude → OpenAI → Gemini)
Usa AIOrchestrator para mayor resiliencia
"""

from app.core.logger import get_logger
from app.core.constants import CLAUDE_MAX_TOKENS, CLAUDE_TEMPERATURE
from app.services.ai.ai_orchestrator import AIOrchestrator

logger = get_logger(__name__)


class ClaudeSQLGenerator:
    """
    Generador de SQL con fallback multi-proveedor.
    
    Usa AIOrchestrator para fallback automático:
    Claude → OpenAI → Gemini
    """
    
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
    porcentaje NUMERIC(5,2)
);

CREATE TABLE socios (
    id UUID PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL CHECK (nombre IN ('Agustina', 'Viviana', 'Gonzalo', 'Pancho', 'Bruno')),
    porcentaje_participacion NUMERIC(5,2) NOT NULL
);

CREATE TABLE areas (
    id UUID PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL CHECK (nombre IN ('Jurídica', 'Notarial', 'Contable', 'Recuperación', 'Gastos Generales', 'Otros'))
);
"""
    
    BUSINESS_CONTEXT = """
CONTEXTO DEL NEGOCIO - CONEXIÓN CONSULTORA:
• Consultora uruguaya con 5 socios: Agustina, Viviana, Gonzalo, Pancho y Bruno
• Opera en 2 localidades: MONTEVIDEO y MERCEDES
• Áreas de negocio: Jurídica, Notarial, Contable, Recuperación, Gastos Generales, Otros
• Tipos de operaciones: INGRESO, GASTO, RETIRO, DISTRIBUCION
• Monedas: UYU (pesos uruguayos) y USD (dólares estadounidenses)
• Fórmula de rentabilidad: (Ingresos - Gastos) / Ingresos * 100
• SIEMPRE filtrar deleted_at IS NULL para operaciones activas

REGLAS SQL CRÍTICAS:
• Si pide "en dólares/USD/dólares": usa monto_usd
• Si pide "en pesos/UYU": usa monto_uyu
• Si NO especifica moneda: usa monto_uyu (default)
• Para rentabilidad: SOLO tipos INGRESO y GASTO (excluir RETIRO y DISTRIBUCION)
• Para comparaciones "este X vs anterior": usar DATE_TRUNC y LIMIT con ORDER BY DESC
• Para "mejor/peor": ORDER BY + LIMIT 1
• Para "cómo venimos/estamos": mostrar ingresos, gastos, resultado y rentabilidad
• Para "trimestre actual/trimestre fiscal": DATE_TRUNC('quarter', CURRENT_DATE)
• Para "últimos X meses" (ventana rodante): fecha >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL 'X months'
• Para mes actual: DATE_TRUNC('month', CURRENT_DATE)
• Para año actual: DATE_TRUNC('year', CURRENT_DATE)
• Los nombres de localidades son MAYÚSCULAS: 'MONTEVIDEO', 'MERCEDES'
• Los nombres de áreas son con mayúscula inicial: 'Jurídica', 'Notarial', etc.
• Los nombres de socios son con mayúscula inicial: 'Bruno', 'Agustina', etc.

IMPORTANTE - CONTEXTO TEMPORAL:
• Fecha actual del sistema: Octubre 2025
• Si el usuario menciona fechas sin año (ej: "2 de octubre", "hoy", "ayer"), ASUMIR año 2025
• Solo usar años anteriores (2024, 2023) si el usuario los especifica explícitamente
• "hoy" = CURRENT_DATE (que está en 2025)
• "este mes" = DATE_TRUNC('month', CURRENT_DATE) en 2025
• "este año" = DATE_TRUNC('year', CURRENT_DATE) = 2025

REGLAS SQL CRÍTICAS (OBLIGATORIO CUMPLIR):

1. PORCENTAJES DE MONEDA:
   - Para calcular % USD vs UYU: SIEMPRE usar la columna moneda_original
   - NUNCA calcular porcentajes basándose en monto_usd o monto_uyu
   - Ejemplo correcto: COUNT(CASE WHEN moneda_original='USD' THEN 1 END)

2. RANKINGS Y TOP N:
   - Para rankings: SIEMPRE mostrar TOP 5 como mínimo
   - NUNCA usar LIMIT 1 a menos que la pregunta pida explícitamente "el más/mejor/mayor"
   - Si pregunta "mejores áreas", mostrar al menos 3
   - Ejemplo: ORDER BY rentabilidad DESC LIMIT 5

3. DISTRIBUCIONES POR SOCIO:
   - Usar tabla distribuciones_detalle para montos por socio
   - SIEMPRE usar dd.monto_uyu para pesos Y dd.monto_usd para dólares (columnas DIFERENTES)
   - NUNCA duplicar la misma columna: dd.monto_usd, dd.monto_usd es INCORRECTO
   - Ejemplo SQL CORRECTO para "distribuciones por socio en UYU y USD":
     SELECT s.nombre,
            SUM(dd.monto_uyu) AS total_uyu,
            SUM(dd.monto_usd) AS total_usd
     FROM distribuciones_detalle dd
     JOIN socios s ON dd.socio_id = s.id
     JOIN operaciones o ON dd.operacion_id = o.id
     WHERE o.deleted_at IS NULL
       AND o.tipo_operacion = 'DISTRIBUCION'
     GROUP BY s.nombre
     ORDER BY total_uyu DESC

4. AFIRMACIONES DE UNICIDAD:
   - NUNCA usar palabras "único", "solo", "únicamente" sin verificar
   - Si usas LIMIT 1, primero ejecutar COUNT para confirmar que hay solo 1
   - Para comparaciones: SIEMPRE mostrar todos los registros con GROUP BY
   - Ejemplo: Si dices "única oficina", verificar que COUNT(DISTINCT localidad) = 1

5. UNION ALL CON COLUMNAS ENUM:
   - Si necesitas UNION ALL con columna tipo ENUM: usar CAST explícito
   - NUNCA insertar strings literales en columnas ENUM directamente
   - Ejemplo: CAST('TOTAL' AS TEXT) en lugar de 'TOTAL'

6. PROYECCIONES TEMPORALES:
   - Para proyecciones fin de año: meses_restantes = 12 - EXTRACT(MONTH FROM CURRENT_DATE)
   - NUNCA asumir meses restantes sin calcular
   - Verificar que estás proyectando desde datos del año actual
   - Ejemplo: EXTRACT(MONTH FROM CURRENT_DATE) para mes actual

7. AÑOS EXPLÍCITOS - MÁXIMA PRIORIDAD (CRÍTICO):
   - Si el usuario menciona un año específico (2024, 2023, 2022, etc.), USAR ESE AÑO EXACTO
   - Esta regla tiene PRIORIDAD ABSOLUTA sobre cualquier filtro por defecto
   - NO sustituir el año especificado por el año actual bajo ninguna circunstancia
   - Ejemplos:
     * "facturación 2024" → WHERE EXTRACT(YEAR FROM fecha) = 2024
     * "gastos 2024" → WHERE fecha >= '2024-01-01' AND fecha < '2025-01-01'
     * "comparar 2024 vs 2025" → usar ambos años explícitamente
   - Si dice "año anterior" o "año pasado": EXTRACT(YEAR FROM CURRENT_DATE) - 1

8. FILTROS TEMPORALES POR DEFECTO (SOLO si NO hay año explícito):
   - IMPORTANTE: Si el usuario menciona un año (2024, 2023, etc.), usar REGLA 7, NO esta regla
   - Esta regla SOLO aplica cuando la pregunta NO menciona ningún año específico
   - EXCEPCIÓN TOTAL/ACUMULADO (PRIORIDAD ALTA):
     * Si el usuario menciona "total", "acumulado", "histórico", "todos los años", "desde el inicio", "desde 2024", "completo" → NO aplicar filtro de año
     * Devolver datos de TODOS los períodos disponibles
     * Ejemplos: "facturación total", "gastos acumulados", "ingresos históricos", "total desde 2024"
   - Si NO especifica período Y NO menciona "total/acumulado/histórico": filtrar por año actual (2025)
   - Ejemplos donde SÍ aplica filtro 2025: "¿Cuánto facturamos este año?", "rentabilidad mensual", "gastos del mes"
   - Ejemplos donde NO aplica filtro (devolver TODO): "facturación total", "total acumulado", "histórico completo"
   - Usar para año actual: WHERE DATE_TRUNC('year', fecha) = DATE_TRUNC('year', CURRENT_DATE)
   - Usar para total histórico: SIN filtro de año (devolver todos los registros)

9. CONVERSIONES DE MONEDA EN AGREGACIONES:
   - Para totales en USD: usar SUM(monto_usd) SIN filtrar por moneda_original
   - Para totales en UYU: usar SUM(monto_uyu) SIN filtrar por moneda_original
   - Las columnas monto_usd y monto_uyu YA contienen TODO convertido
   - NUNCA usar: SUM(CASE WHEN moneda_original='USD' THEN monto_usd...)
   - SOLO filtrar por moneda_original si pregunta pide explícitamente "operaciones emitidas en USD"
   - Ejemplo CORRECTO: "Facturación en USD" = SUM(monto_usd)
   - Ejemplo INCORRECTO: SUM(CASE WHEN moneda_original='USD' THEN monto_usd ELSE 0 END)
   - CRÍTICO - AMBAS MONEDAS: Si el usuario pide "en pesos Y en dólares" o "UYU y USD":
     * SIEMPRE usar DOS columnas diferentes: SUM(monto_uyu) AS total_uyu, SUM(monto_usd) AS total_usd
     * NUNCA duplicar la misma columna para ambos valores
     * Ejemplo CORRECTO: SELECT SUM(monto_uyu) AS total_pesos, SUM(monto_usd) AS total_dolares
     * Ejemplo INCORRECTO: SELECT SUM(monto_usd) AS total_pesos, SUM(monto_usd) AS total_dolares

10. PERÍODOS RODANTES VS TRIMESTRES:
   - "últimos X meses" = ventana RODANTE desde mes actual hacia atrás
   - NUNCA usar DATE_TRUNC('quarter') para "últimos X meses"
   - Usar: fecha >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL 'X months'
   - "trimestre actual" = DATE_TRUNC('quarter', CURRENT_DATE)
   - Ejemplo CORRECTO "últimos 3 meses":
     WHERE fecha >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '3 months'
       AND fecha < DATE_TRUNC('month', CURRENT_DATE)
   - Ejemplo CORRECTO "trimestre actual":
     WHERE DATE_TRUNC('quarter', fecha) = DATE_TRUNC('quarter', CURRENT_DATE)

11. UNION ALL CON FILA DE TOTAL:
   - Para mostrar TOTAL al final después de UNION ALL: usa columna auxiliar de ordenamiento
   - Agrega columna 'orden' a cada SELECT: 0 para filas normales, 1 para TOTAL
   - Luego ordena por: ORDER BY orden, socio
   - Ejemplo CORRECTO:
     SELECT * FROM (
       SELECT 0 AS orden, socio, total_uyu, total_usd FROM por_socio
       UNION ALL
       SELECT 1 AS orden, socio, total_uyu, total_usd FROM total_general
     ) t ORDER BY orden, socio

12. TOTALES DE DISTRIBUCIONES:
   - Para totales de distribuciones: SIEMPRE sumar distribuciones_detalle.monto_uyu
   - NUNCA sumar operaciones.monto_uyu para totales (puede tener redondeo)
   - operaciones.monto_uyu = total de la operación (referencial)
   - distribuciones_detalle.monto_uyu = desglose exacto por socio (fuente de verdad)
   - Ejemplo CORRECTO para "total distribuido":
     SELECT SUM(dd.monto_uyu) AS total_uyu
     FROM distribuciones_detalle dd
     INNER JOIN operaciones o ON dd.operacion_id = o.id
     WHERE o.tipo_operacion = 'DISTRIBUCION'
       AND o.deleted_at IS NULL
       AND o.fecha >= ...
   - Esto garantiza que: SUM(por_socio) = total_general

13. DISTRIBUCIONES CON FILTROS TEMPORALES (CRÍTICO):
   - PROBLEMA IDENTIFICADO: LEFT JOIN con filtros temporales en ON causa errores del 49%
   - Para consultas de distribuciones filtradas por año/mes/período:
     * Empezar FROM distribuciones_detalle (NO desde socios)
     * Usar INNER JOIN (NO LEFT JOIN) para relacionar con operaciones
     * Filtros temporales SIEMPRE en WHERE cláusula (NUNCA en ON cláusula)
   - LEFT JOIN solo si la pregunta EXPLÍCITAMENTE pide incluir socios SIN distribuciones
   - Ejemplo CORRECTO "distribuciones por socio en 2024":
     SELECT s.nombre, SUM(dd.monto_uyu) as total
     FROM distribuciones_detalle dd
     INNER JOIN operaciones o ON dd.operacion_id = o.id
     INNER JOIN socios s ON dd.socio_id = s.id
     WHERE o.tipo_operacion = 'DISTRIBUCION'
       AND o.deleted_at IS NULL
       AND EXTRACT(YEAR FROM o.fecha) = 2024
     GROUP BY s.nombre
   - Ejemplo INCORRECTO (NO HACER - suma años incorrectos):
     FROM socios s
     LEFT JOIN distribuciones_detalle dd ON s.id = dd.socio_id
     LEFT JOIN operaciones o ON dd.operacion_id = o.id
       AND EXTRACT(YEAR FROM o.fecha) = 2024  -- ❌ Filtro en ON incluye otros años
   - Causa del error: LEFT JOIN mantiene filas sin match, sumando distribuciones de todos los años

EJEMPLO COMPLETO - DISTRIBUCIONES CON TOTAL:
Pregunta: "¿Cuánto se distribuyó en los últimos 3 meses por socio?"

Query CORRECTO:
WITH distribuciones_periodo AS (
    SELECT o.id
    FROM operaciones o
    WHERE o.tipo_operacion = 'DISTRIBUCION'
        AND o.deleted_at IS NULL
        AND o.fecha >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '3 months'
        AND o.fecha < DATE_TRUNC('month', CURRENT_DATE)
),
por_socio AS (
    SELECT 0 AS orden, s.nombre AS socio, 
           SUM(dd.monto_uyu) AS total_uyu, 
           SUM(dd.monto_usd) AS total_usd
    FROM distribuciones_detalle dd
    INNER JOIN socios s ON dd.socio_id = s.id
    INNER JOIN distribuciones_periodo dp ON dd.operacion_id = dp.id
    GROUP BY s.nombre
),
total_general AS (
    SELECT 1 AS orden, 'TOTAL' AS socio,
           SUM(dd.monto_uyu) AS total_uyu,
           SUM(dd.monto_usd) AS total_usd
    FROM distribuciones_detalle dd
    INNER JOIN distribuciones_periodo dp ON dd.operacion_id = dp.id
)
SELECT socio, total_uyu, total_usd 
FROM (
    SELECT * FROM por_socio
    UNION ALL
    SELECT * FROM total_general
) t
ORDER BY orden, socio;

14. RENTABILIDAD POR ÁREA - EXCLUSIONES (CRÍTICO):
   - Para preguntas de "rentabilidad por área" o "rentabilidad de cada área": EXCLUIR áreas no productivas
   - 'Gastos Generales': centro de costos operativos (alquiler, servicios), NO genera ingresos
   - 'Otros': categoría residual para ingresos varios, distorsiona análisis
   - SIEMPRE agregar filtro: AND a.nombre NOT IN ('Gastos Generales', 'Otros')
   - Ejemplo CORRECTO "rentabilidad por área":
     SELECT a.nombre, 
            ((SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END)
             -SUM(CASE WHEN o.tipo_operacion='GASTO' THEN o.monto_uyu ELSE 0 END))
            /NULLIF(SUM(CASE WHEN o.tipo_operacion='INGRESO' THEN o.monto_uyu ELSE 0 END),0))*100 AS rentabilidad
     FROM operaciones o
     JOIN areas a ON a.id = o.area_id
     WHERE o.deleted_at IS NULL
       AND a.nombre NOT IN ('Gastos Generales', 'Otros')
       AND DATE_TRUNC('month', o.fecha) = DATE_TRUNC('month', CURRENT_DATE)
     GROUP BY a.nombre
     ORDER BY rentabilidad DESC

15. RETIROS vs DISTRIBUCIONES (CONCEPTOS DIFERENTES - CRÍTICO):
   - RETIRO (tipo_operacion='RETIRO'): Salida de dinero de la EMPRESA (caja)
     * Se consulta SOLO en tabla operaciones
     * Tiene localidad (MERCEDES/MONTEVIDEO)
     * Campos: monto_uyu, monto_usd
     * Ejemplo: "retiros en Mercedes" → WHERE tipo_operacion='RETIRO' AND localidad='MERCEDES'
   
   - DISTRIBUCIÓN (tipo_operacion='DISTRIBUCION'): Reparto de UTILIDADES a los SOCIOS
     * Se consulta en distribuciones_detalle (JOIN con operaciones)
     * Tiene socio_id (los 5 socios: Bruno, Agustina, Viviana, Gonzalo, Pancho)
     * Campos: monto_uyu, monto_usd POR SOCIO
     * Ejemplo: "cuánto recibió Bruno" → distribuciones_detalle WHERE socio.nombre='Bruno'
   
   - NUNCA confundir estos conceptos:
     * "retiros de la empresa" → operaciones WHERE tipo_operacion='RETIRO'
     * "distribuciones a socios" / "cuánto recibió [socio]" → distribuciones_detalle
     * "retiros en Mercedes" → ES RETIRO de empresa, NO distribución
     * "cuánto retiró Bruno" → ES DISTRIBUCIÓN a socio, NO retiro de empresa

16. COMPLEJIDAD SQL (EVITAR ERRORES DE SINTAXIS):
   - EVITAR FULL OUTER JOIN - propenso a errores de sintaxis y truncamiento
   - Para comparaciones temporales (ej: "Q4 2024 vs Q4 2025"):
     * Usar 2 CTEs separados, uno por período
     * Luego LEFT JOIN por columna de agrupación
     * Estructura recomendada:
       WITH periodo1 AS (SELECT area, SUM(monto) as total FROM ... WHERE fecha BETWEEN '2024-10-01' AND '2024-12-31' GROUP BY area),
            periodo2 AS (SELECT area, SUM(monto) as total FROM ... WHERE fecha BETWEEN '2025-10-01' AND '2025-12-31' GROUP BY area)
       SELECT COALESCE(p1.area, p2.area) as area, p1.total as total_2024, p2.total as total_2025
       FROM periodo1 p1
       LEFT JOIN periodo2 p2 ON p1.area = p2.area
   - Máximo 3 CTEs por query
   - Si la query supera 40 líneas, simplificar el approach
   - SIEMPRE verificar que cada JOIN tenga su cláusula ON

17. ORDER BY DESPUÉS DE UNION/UNION ALL (RESTRICCIÓN PostgreSQL):
   - PostgreSQL NO permite expresiones CASE, funciones o cálculos en ORDER BY después de UNION
   - Error típico: "invalid UNION/INTERSECT/EXCEPT ORDER BY clause"
   - SOLO se puede ordenar por:
     a) Nombre de columna literal del SELECT
     b) Número de posición de columna (1, 2, 3...)
     c) Alias de columna definido en los SELECTs
   - Para comparaciones por año (2024 vs 2025) con distribuciones:
     * Usar columna auxiliar 'orden' numérica en cada SELECT
     * Ordenar por: ORDER BY orden, nombre_columna
   - Ejemplo CORRECTO (comparar distribuciones 2024 vs 2025):
     WITH d2024 AS (...), d2025 AS (...)
     SELECT * FROM (
       SELECT 0 AS orden, socio, total_2024, total_2025 FROM comparacion
       UNION ALL
       SELECT 1 AS orden, 'TOTAL', SUM(total_2024), SUM(total_2025) FROM comparacion
     ) t ORDER BY orden, socio
   - Ejemplo INCORRECTO (genera error):
     SELECT ... UNION ALL SELECT ...
     ORDER BY CASE WHEN socio = 'TOTAL' THEN 1 ELSE 0 END  -- ❌ CASE no permitido
   - Alternativa simple: Usar subquery para ordenar ANTES del UNION

IMPORTANTE: Si una query viola alguna de estas reglas, usar approach alternativo más seguro.
"""
    
    def __init__(self):
        self._orchestrator = AIOrchestrator()
        logger.info("ClaudeSQLGenerator inicializado con AIOrchestrator")
    
    def generar_sql(self, pregunta: str, contexto: list = None) -> str:
        """
        Genera SQL usando IA con fallback multi-proveedor y memoria de conversación
        
        Args:
            pregunta: Pregunta del usuario en lenguaje natural
            contexto: Lista de mensajes previos [{"role": "user|assistant", "content": "..."}]
            
        Returns:
            SQL válido de PostgreSQL o texto explicativo si no puede
        """
        contexto = contexto or []
        
        # Construir prompt del sistema
        prompt_sistema = f"""{self.DDL_CONTEXT}

{self.BUSINESS_CONTEXT}

INSTRUCCIONES:
• Genera SOLO el SQL query en PostgreSQL, sin explicaciones ni markdown
• NO uses triple backticks ni formato ```sql
• El SQL debe ser ejecutable directamente
• Si la pregunta es ambigua, genera el SQL más probable
• Si pide "en dólares" o "USD", usa monto_usd
• Si pide rentabilidad, usa la fórmula: (Ingresos - Gastos) / Ingresos * 100
• SIEMPRE incluye WHERE deleted_at IS NULL
• Para comparaciones temporales, usa CTEs con DATE_TRUNC
• Si hay contexto previo, usa las respuestas anteriores para entender referencias

Genera ÚNICAMENTE el SQL query:"""
        
        # Construir prompt completo incluyendo contexto previo
        prompt_completo = prompt_sistema + f"\n\nPREGUNTA: {pregunta}"
        
        # Si hay contexto previo, agregarlo al prompt
        if contexto:
            contexto_str = "\n\nCONTEXTO DE CONVERSACIÓN PREVIA:\n"
            for msg in contexto:
                role = "Usuario" if msg["role"] == "user" else "Asistente"
                content = msg['content'][:500] if len(msg['content']) > 500 else msg['content']
                contexto_str += f"{role}: {content}\n"
            prompt_completo = prompt_sistema + contexto_str + f"\n\nPREGUNTA ACTUAL: {pregunta}"

        try:
            # Usar AIOrchestrator con fallback automático
            sql_generado = self._orchestrator.complete(
                prompt=prompt_completo,
                max_tokens=CLAUDE_MAX_TOKENS,
                temperature=CLAUDE_TEMPERATURE
            )
            
            if not sql_generado:
                logger.error("AIOrchestrator retornó None - todos los proveedores fallaron")
                return "ERROR: Todos los proveedores de IA fallaron"
            
            sql_generado = sql_generado.strip()
            
            # Limpiar si viene con markdown
            if sql_generado.startswith("```"):
                sql_generado = sql_generado.replace("```sql", "").replace("```", "").strip()
            
            logger.info(f"SQL generado con {len(contexto)} mensajes de contexto")
            
            return sql_generado
            
        except Exception as e:
            logger.error(f"Error en SQL Generator: {e}", exc_info=True)
            return f"ERROR: {str(e)}"
