"""
Generador de SQL usando Claude Sonnet 4.5 como modelo principal
Mayor precisión y determinismo que GPT-3.5
"""

import anthropic
import os
from dotenv import load_dotenv

from app.core.logger import get_logger
from app.core.constants import CLAUDE_MODEL, CLAUDE_MAX_TOKENS, CLAUDE_TEMPERATURE

load_dotenv()

logger = get_logger(__name__)


class ClaudeSQLGenerator:
    """
    Usa Claude Sonnet 4.5 para generar SQL directamente
    Más preciso y determinístico que Vanna+GPT-3.5
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
   - Límite razonable por socio: máximo $100.000 UYU
   - Si resultado > $100K: puede ser error de SQL
   - Usar tipo_cambio de la operación para conversiones

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

7. FILTROS TEMPORALES POR DEFECTO:
   - Si la pregunta NO especifica período temporal: SIEMPRE filtrar por año actual (2025)
   - Ejemplos: "¿Cuánto facturamos?", "¿Qué porcentaje es USD?", "rentabilidad" sin período
   - Usar: WHERE fecha >= '2025-01-01' AND fecha < '2026-01-01'
   - O mejor: WHERE DATE_TRUNC('year', fecha) = DATE_TRUNC('year', CURRENT_DATE)
   - SOLO omitir filtro temporal si pregunta dice "histórico", "todos los años", "desde inicio"

8. CONVERSIONES DE MONEDA EN AGREGACIONES:
   - Para totales en USD: usar SUM(monto_usd) SIN filtrar por moneda_original
   - Para totales en UYU: usar SUM(monto_uyu) SIN filtrar por moneda_original
   - Las columnas monto_usd y monto_uyu YA contienen TODO convertido
   - NUNCA usar: SUM(CASE WHEN moneda_original='USD' THEN monto_usd...)
   - SOLO filtrar por moneda_original si pregunta pide explícitamente "operaciones emitidas en USD"
   - Ejemplo CORRECTO: "Facturación en USD" = SUM(monto_usd)
   - Ejemplo INCORRECTO: SUM(CASE WHEN moneda_original='USD' THEN monto_usd ELSE 0 END)

9. PERÍODOS RODANTES VS TRIMESTRES:
   - "últimos X meses" = ventana RODANTE desde mes actual hacia atrás
   - NUNCA usar DATE_TRUNC('quarter') para "últimos X meses"
   - Usar: fecha >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL 'X months'
   - "trimestre actual" = DATE_TRUNC('quarter', CURRENT_DATE)
   - Ejemplo CORRECTO "últimos 3 meses":
     WHERE fecha >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '3 months'
       AND fecha < DATE_TRUNC('month', CURRENT_DATE)
   - Ejemplo CORRECTO "trimestre actual":
     WHERE DATE_TRUNC('quarter', fecha) = DATE_TRUNC('quarter', CURRENT_DATE)

10. UNION ALL Y ORDER BY:
   - Si usas UNION ALL: NO uses ORDER BY con CASE WHEN socio = 'TOTAL'
   - PostgreSQL requiere ORDER BY solo con nombres de columnas después de UNION
   - NUNCA: ORDER BY CASE WHEN socio = 'TOTAL' THEN 1 ELSE 0 END
   - Para ordenar TOTAL al final: usar subquery o CTE
   - Ejemplo CORRECTO con subquery:
     SELECT * FROM (
       SELECT ... UNION ALL SELECT 'TOTAL' AS socio, ...
     ) t ORDER BY socio

IMPORTANTE: Si una query viola alguna de estas reglas, usar approach alternativo más seguro.
"""
    
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY no encontrada en .env")
        
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def generar_sql(self, pregunta: str, contexto: list = None) -> str:
        """
        Genera SQL usando Claude Sonnet 4.5 con memoria de conversación
        
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
        
        # Construir mensajes para Claude
        mensajes = []
        
        # Agregar contexto de conversación si existe
        if contexto:
            for msg in contexto:
                mensajes.append(msg)
        
        # Agregar pregunta actual
        mensajes.append({
            "role": "user",
            "content": f"{prompt_sistema}\n\nPREGUNTA: {pregunta}"
        })

        try:
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=CLAUDE_MAX_TOKENS,
                temperature=CLAUDE_TEMPERATURE,
                messages=mensajes
            )
            
            sql_generado = response.content[0].text.strip()
            
            # Limpiar si viene con markdown
            if sql_generado.startswith("```"):
                sql_generado = sql_generado.replace("```sql", "").replace("```", "").strip()
            
            logger.info(f"SQL generado con {len(contexto)} mensajes de contexto")
            
            return sql_generado
            
        except Exception as e:
            logger.error(f"Error en Claude SQL Generator: {e}", exc_info=True)
            return f"ERROR: {str(e)}"

