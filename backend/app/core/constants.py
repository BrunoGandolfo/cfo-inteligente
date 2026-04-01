"""
Constantes del Sistema - CFO Inteligente

Centraliza constantes de configuración usadas por servicios y routers.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from datetime import datetime

# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE MODELOS IA
# ══════════════════════════════════════════════════════════════

CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
HAIKU_CLASSIFIER_MODEL = "claude-haiku-4-5-20251001"
CLAUDE_MAX_TOKENS = 4000
CLAUDE_MAX_TOKENS_INFORME = 12000
CLAUDE_TEMPERATURE = 0.0  # Determinístico

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
    'vs anterior', 'versus',
    'crecimiento', 'variación', 'variacion',
    'estimar', 'estimación', 'estimacion'
]

# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE NEGOCIO
# ══════════════════════════════════════════════════════════════

# Socios
SOCIOS = ['Agustina', 'Viviana', 'Gonzalo', 'Pancho', 'Bruno']

# Año actual del sistema
ANIO_ACTUAL = datetime.now().year

# ══════════════════════════════════════════════════════════════
# COTIZACIÓN USD — FALLBACK
# ══════════════════════════════════════════════════════════════

# Valores de emergencia cuando DolarApi no responde.
# Fuente única para tipo_cambio_service e indicadores_service.
FALLBACK_COTIZACION_USD = {
    "compra": 43.50,
    "venta": 44.50,
    "promedio": 44.00,
}
