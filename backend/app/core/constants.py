"""
Constantes del Sistema - CFO Inteligente

Centraliza todas las constantes, magic numbers, URLs y configuraciones.
Facilita mantenimiento y testing.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

# ══════════════════════════════════════════════════════════════
# URLs Y ENDPOINTS
# ══════════════════════════════════════════════════════════════

# Base URLs
API_BASE_URL = "http://localhost:8000"
FRONTEND_BASE_URL = "http://localhost:5173"

# Anthropic API
ANTHROPIC_API_URL = "https://api.anthropic.com"
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"

# PostgreSQL
DEFAULT_PG_HOST = "localhost"
DEFAULT_PG_PORT = 5432
DEFAULT_PG_DB = "cfo_inteligente"
DEFAULT_PG_USER = "cfo_user"
DEFAULT_PG_PASS = "cfo_pass"

# ══════════════════════════════════════════════════════════════
# LÍMITES DE VALIDACIÓN
# ══════════════════════════════════════════════════════════════

# Límites financieros (en UYU)
MAX_FACTURACION_DIA = 1_000_000
MAX_FACTURACION_MES = 50_000_000
MAX_GASTO_DIA = 500_000
MAX_GASTO_MES = 5_000_000

# Límites de rentabilidad (%)
MIN_RENTABILIDAD = -100
MAX_RENTABILIDAD = 100

# Límites de porcentajes
MIN_PORCENTAJE = 0
MAX_PORCENTAJE = 100
TOLERANCIA_SUMA_PORCENTAJES = 5  # ±5%

# Tipo de cambio UYU/USD
MIN_TIPO_CAMBIO = 30
MAX_TIPO_CAMBIO = 50

# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE MODELOS IA
# ══════════════════════════════════════════════════════════════

# Claude Sonnet 4.5
CLAUDE_MAX_TOKENS = 4000
CLAUDE_TEMPERATURE = 0.0  # Determinístico
CLAUDE_TIMEOUT_SECONDS = 600

# Vanna + GPT-3.5
GPT_MODEL = "gpt-3.5-turbo"
GPT_MAX_TOKENS = 1000
GPT_TEMPERATURE = 0.0
GPT_SEED = 42

# ══════════════════════════════════════════════════════════════
# TIMEOUTS Y REINTENTOS
# ══════════════════════════════════════════════════════════════

# HTTP Timeouts
HTTP_CONNECT_TIMEOUT = 5
HTTP_READ_TIMEOUT = 600
HTTP_WRITE_TIMEOUT = 600

# Reintentos
MAX_REINTENTOS_VANNA = 2
MAX_REINTENTOS_SQL = 3

# Timeout por query (segundos)
QUERY_TIMEOUT_SECONDS = 25

# ══════════════════════════════════════════════════════════════
# MENSAJES DE ERROR ESTÁNDAR
# ══════════════════════════════════════════════════════════════

ERROR_SQL_GENERATION_FAILED = "No pude generar SQL válido para esa pregunta"
ERROR_SQL_EXECUTION_FAILED = "El SQL generado falló al ejecutarse"
ERROR_NO_DATA = "No hay datos disponibles para ese período"
ERROR_VALIDACION_FALLIDA = "Los datos retornados no pasaron validación"
ERROR_API_TIMEOUT = "La consulta tardó demasiado tiempo"
ERROR_API_KEY_MISSING = "API key no configurada"

# ══════════════════════════════════════════════════════════════
# KEYWORDS TEMPORALES (Chain-of-Thought)
# ══════════════════════════════════════════════════════════════

KEYWORDS_TEMPORALES = [
    'proyección', 'proyeccion', 'proyectar',
    'últimos', 'ultimos', 'últimas', 'ultimas',
    'tendencia', 'evolución', 'evolucion',
    'promedio', 'media',
    'basado en', 'en base a',
    'fin de año', 'fin del año', 'cierre',
    'comparar', 'vs anterior', 'versus',
    'crecimiento', 'variación', 'variacion',
    'estimar', 'estimación', 'estimacion'
]

# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE NEGOCIO
# ══════════════════════════════════════════════════════════════

# Socios
SOCIOS = ['Agustina', 'Viviana', 'Gonzalo', 'Pancho', 'Bruno']

# Áreas de negocio
AREAS = ['Jurídica', 'Notarial', 'Contable', 'Recuperación', 'Otros Gastos']

# Localidades
LOCALIDADES = ['MONTEVIDEO', 'MERCEDES']

# Tipos de operación
TIPOS_OPERACION = ['INGRESO', 'GASTO', 'RETIRO', 'DISTRIBUCION']

# Monedas
MONEDAS = ['UYU', 'USD']

# Año actual del sistema
ANIO_ACTUAL = 2025

