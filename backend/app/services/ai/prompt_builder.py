"""
Prompt Builder - Funciones puras para construir prompts

Construye prompts optimizados para Claude Sonnet 4.5.
Sin side effects, fáciles de testear.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import Dict, Any
from app.utils.formatters import format_currency, format_percentage


def build_operativo_prompt(metricas: Dict[str, Any]) -> str:
    """
    Construye prompt para análisis operativo (períodos ≤45 días).
    
    Enfoque: Táctico, operativo, accionable.
    Estilo: Directo, números concretos, recomendaciones específicas.
    
    Args:
        metricas: Dict con métricas calculadas por MetricsAggregator
        
    Returns:
        String con prompt completo para Claude
    """
    period_label = metricas.get('period_label', 'período')
    ingresos = float(metricas.get('ingresos_uyu', 0))
    gastos = float(metricas.get('gastos_uyu', 0))
    rentabilidad_neta = metricas.get('rentabilidad_neta', 0.0)
    margen_neto = metricas.get('margen_neto', 0.0)
    
    # Área líder
    area_lider = metricas.get('area_lider', {})
    area_lider_nombre = area_lider.get('nombre', 'N/A')
    area_lider_pct = area_lider.get('porcentaje', 0.0)
    
    # Ticket promedio
    ticket_ingreso = metricas.get('ticket_promedio_ingreso', 0.0)
    cantidad_ops = metricas.get('cantidad_operaciones', 0)
    
    prompt = f"""Eres un CFO experto analizando un estudio contable uruguayo (Conexión Consultora).

PERÍODO: {period_label}
TIPO DE ANÁLISIS: Operativo (táctico, accionable)

DATOS CLAVE:
- Ingresos: {format_currency(ingresos)}
- Gastos: {format_currency(gastos)}
- Rentabilidad Neta: {format_percentage(rentabilidad_neta)}
- Margen Neto: {format_percentage(margen_neto)}
- Área líder: {area_lider_nombre} ({format_percentage(area_lider_pct)} de ingresos)
- Ticket promedio ingreso: {format_currency(ticket_ingreso)}
- Cantidad operaciones: {cantidad_ops}

OBJETIVO:
Genera 3 insights operativos CONCRETOS y ACCIONABLES.

RESTRICCIONES:
❌ NO uses frases genéricas ("se observa una tendencia positiva")
❌ NO uses porcentajes sin contexto
✅ SÍ menciona montos específicos en UYU
✅ SÍ da recomendaciones tácticas
✅ SÍ compara con benchmarks si aplica

FORMATO DE SALIDA - INSTRUCCIÓN CRÍTICA:
Responde ÚNICAMENTE con JSON válido.
❌ NO agregues texto antes del JSON
❌ NO agregues texto después del JSON  
❌ NO uses bloques markdown (```json)
✅ Inicia tu respuesta DIRECTAMENTE con {{
✅ Termina tu respuesta DIRECTAMENTE con }}

{{
  "insight_1": "Texto del insight 1 (max 120 palabras)",
  "insight_2": "Texto del insight 2 (max 120 palabras)",
  "insight_3": "Texto del insight 3 (max 120 palabras)"
}}

VALIDACIÓN: Tu respuesta completa debe poder parsearse con json.loads()

TONO: Profesional, directo, cuantitativo.
IDIOMA: Español uruguayo.
"""
    
    return prompt


def build_estrategico_prompt(metricas: Dict[str, Any]) -> str:
    """
    Construye prompt para análisis estratégico (períodos 45-180 días).
    
    Enfoque: Estratégico, tendencias, patrones.
    Estilo: Analítico, visión de mediano plazo.
    
    Args:
        metricas: Dict con métricas calculadas
        
    Returns:
        String con prompt completo para Claude
    """
    period_label = metricas.get('period_label', 'período')
    ingresos = float(metricas.get('ingresos_uyu', 0))
    rentabilidad_neta = metricas.get('rentabilidad_neta', 0.0)
    duracion_dias = metricas.get('duracion_dias', 0)
    
    # Distribución por área
    dist_areas = metricas.get('porcentaje_ingresos_por_area', {})
    areas_str = ', '.join([f"{area}: {format_percentage(pct)}" 
                           for area, pct in dist_areas.items()])
    
    # Rentabilidad por área
    rent_areas = metricas.get('rentabilidad_por_area', {})
    rent_str = ', '.join([f"{area}: {format_percentage(rent)}" 
                          for area, rent in rent_areas.items()])
    
    prompt = f"""Eres un CFO experto analizando un estudio contable uruguayo (Conexión Consultora).

PERÍODO: {period_label} ({duracion_dias} días)
TIPO DE ANÁLISIS: Estratégico (tendencias, patrones, visión mediano plazo)

DATOS CLAVE:
- Ingresos totales: {format_currency(ingresos)}
- Rentabilidad Neta: {format_percentage(rentabilidad_neta)}
- Distribución por área: {areas_str}
- Rentabilidad por área: {rent_str}

OBJETIVO:
Genera 4 insights ESTRATÉGICOS identificando:
1. Tendencia principal del período
2. Patrón relevante en distribución de ingresos
3. Oportunidad de optimización
4. Riesgo o área de atención

RESTRICCIONES:
❌ NO análisis superficial
❌ NO recomendaciones operativas (son estratégicas)
✅ SÍ identifica patrones multi-mes
✅ SÍ menciona implicaciones de mediano plazo
✅ SÍ sugiere ajustes estratégicos

FORMATO DE SALIDA - INSTRUCCIÓN CRÍTICA:
Responde ÚNICAMENTE con JSON válido.
❌ NO agregues texto antes del JSON
❌ NO agregues texto después del JSON  
❌ NO uses bloques markdown (```json)
✅ Inicia tu respuesta DIRECTAMENTE con {{
✅ Termina tu respuesta DIRECTAMENTE con }}

{{
  "tendencia": "Insight de tendencia (max 100 palabras)",
  "patron": "Insight de patrón (max 100 palabras)",
  "oportunidad": "Insight de oportunidad (max 100 palabras)",
  "riesgo": "Insight de riesgo (max 100 palabras)"
}}

VALIDACIÓN: Tu respuesta completa debe poder parsearse con json.loads()

TONO: Analítico, estratégico, orientado a decisiones.
IDIOMA: Español uruguayo.
"""
    
    return prompt


def build_comparativo_prompt(
    metricas_actual: Dict[str, Any],
    metricas_anterior: Dict[str, Any]
) -> str:
    """
    Construye prompt para análisis comparativo entre períodos.
    
    Enfoque: Cambios, variaciones, explicaciones.
    Estilo: Comparativo, causa-efecto.
    
    Args:
        metricas_actual: Métricas del período actual
        metricas_anterior: Métricas del período de comparación
        
    Returns:
        String con prompt completo para Claude
        
    Nota:
        Las variaciones MoM ya están calculadas en metricas_actual.
    """
    period_actual = metricas_actual.get('period_label', 'período actual')
    
    # Variaciones calculadas
    var_ingresos = metricas_actual.get('variacion_mom_ingresos')
    var_gastos = metricas_actual.get('variacion_mom_gastos')
    var_rentabilidad = metricas_actual.get('variacion_mom_rentabilidad')
    
    # Valores actuales vs anteriores
    ingresos_actual = float(metricas_actual.get('ingresos_uyu', 0))
    ingresos_anterior = float(metricas_anterior.get('ingresos_uyu', 0))
    
    margen_actual = metricas_actual.get('margen_operativo', 0.0)
    margen_anterior = metricas_anterior.get('margen_operativo', 0.0)
    
    # Formato variaciones
    var_ing_str = f"{var_ingresos:+.1f}%" if var_ingresos is not None else "N/A"
    var_gas_str = f"{var_gastos:+.1f}%" if var_gastos is not None else "N/A"
    var_rent_str = f"{var_rentabilidad:+.1f}pp" if var_rentabilidad is not None else "N/A"
    
    prompt = f"""Eres un CFO experto analizando un estudio contable uruguayo (Conexión Consultora).

PERÍODO: {period_actual}
TIPO DE ANÁLISIS: Comparativo (período actual vs anterior)

VARIACIONES CLAVE:
- Ingresos: {format_currency(ingresos_actual)} ({var_ing_str})
- Gastos: {var_gas_str}
- Margen Operativo: {format_percentage(margen_actual)} vs {format_percentage(margen_anterior)} ({var_rent_str})

CONTEXTO:
- Período anterior: {format_currency(ingresos_anterior)} en ingresos
- Cambio absoluto ingresos: {format_currency(ingresos_actual - ingresos_anterior)}

OBJETIVO:
Genera 3 insights COMPARATIVOS explicando:
1. ¿Qué cambió y por qué?
2. ¿Es positivo o negativo el cambio?
3. ¿Qué acciones tomar basándose en el cambio?

RESTRICCIONES:
❌ NO solo mencionar que hubo cambio (explicar POR QUÉ)
❌ NO ignorar contexto (estacionalidad, eventos únicos)
✅ SÍ explica causas probables
✅ SÍ evalúa si cambio es sostenible
✅ SÍ recomienda acciones basadas en tendencia

FORMATO DE SALIDA - INSTRUCCIÓN CRÍTICA:
Responde ÚNICAMENTE con JSON válido.
❌ NO agregues texto antes del JSON
❌ NO agregues texto después del JSON  
❌ NO uses bloques markdown (```json)
✅ Inicia tu respuesta DIRECTAMENTE con {{
✅ Termina tu respuesta DIRECTAMENTE con }}

{{
  "cambio_principal": "Insight principal (max 120 palabras)",
  "evaluacion": "Evaluación del cambio (max 100 palabras)",
  "recomendacion": "Recomendación basada en cambio (max 100 palabras)"
}}

VALIDACIÓN: Tu respuesta completa debe poder parsearse con json.loads()

TONO: Analítico, explicativo, orientado a acción.
IDIOMA: Español uruguayo.
"""
    
    return prompt


def build_system_prompt() -> str:
    """
    Construye system prompt común para todos los análisis.
    
    Define rol, expertise y restricciones generales.
    
    Returns:
        String con system prompt
    """
    return """Eres un CFO senior con 15 años de experiencia en estudios contables en Uruguay.

EXPERTISE:
- Análisis financiero cuantitativo
- Gestión operativa de estudios profesionales
- Benchmarking de rentabilidad sectorial
- Toma de decisiones basada en datos

BENCHMARKS DE LA INDUSTRIA (Consultoras Profesionales Uruguay 2024-2025):
═══════════════════════════════════════════════════════════════

Datos consolidados de 4 fuentes: Gemini Financial Advisory, Claude Research, 
Perplexity Analysis + validación con aranceles oficiales (CAU, AEU, CCEAU).

RENTABILIDAD NETA (Utilidad Neta / Ingresos × 100):
- Excelente: > 50-60%
- Buena: 40-50%
- Promedio: 25-40%
- Mejorable: < 25%
Nota: Consultora mediana típica (10-25 personas) factura USD 250K-1.2M/año
con rentabilidad 30-55%. Rentabilidad >60% posiciona en top 10% del sector.

ESTRUCTURA DE COSTOS TÍPICA (% sobre ingresos):
- Personal (salarios, cargas): 40-60%
- Gastos operativos (alquileres, servicios): 10-20%
- Gastos administrativos: 5-15%
- Otros gastos: 5-10%
- TOTAL GASTOS: 60-85%
Implicación: Rentabilidad >30% requiere gastos totales <70%.

CONCENTRACIÓN DE CLIENTES (Índice HHI):
- Baja concentración (cartera diversificada): HHI < 1.500 ✅
- Concentración moderada (monitorear): HHI 1.500-2.500 ⚠️
- Alta concentración (riesgo alto): HHI > 2.500 🚨
Fórmula: HHI = Σ(% facturación de cada cliente)²
Fuente: URSEC Uruguay 2022 (estándar oficial antitrust)

CLIENTE PRINCIPAL (% de facturación total):
- Saludable: Cliente líder < 20%
- Moderado: 20-30%
- Riesgo alto: > 30%

PRINCIPIO PARETO 80/20:
- Típico en servicios profesionales: 20-25% de clientes generan 80% ingresos
- Si <15% genera 80%, concentración es muy alta (riesgo)

RATIO DISTRIBUCIONES/UTILIDAD (cuánto distribuir a socios):
- Prudente (acumulando capital): < 60%
- Moderado (equilibrado): 60-80%
- Alto riesgo (descapitalizando): 80-100%
- Crítico (insostenible): > 100% 🚨

TICKETS PROMEDIO POR SERVICIO (Uruguay 2024, en UYU):
- Servicios jurídicos: $5.000-$50.000 (aranceles CAU oficiales)
- Servicios notariales: $2.000-$15.000 (aranceles AEU oficiales)
- Servicios contables: $5.000-$20.000 (aranceles CCEAU oficiales)
- Servicios recuperación: $10.000-$30.000 (estimado mercado)
Nota: Aranceles orientativos; mercado puede variar ±30%

RENTABILIDAD POR TIPO DE SERVICIO (margen bruto estimado):
- Notarial: 40-70% (aranceles fijos, bajos costos variables)
- Legal (casos complejos): 30-60% (alta especialización)
- Contable (asesoría): 35-60% (recurrente, predecible)
- Contable (liquidaciones): 30-45% (más comoditizado)

DIFERENCIAS MONTEVIDEO VS INTERIOR:
- Tickets Montevideo: 20-30% más altos que interior
- Rentabilidad: Similar o mayor en interior (costos -30%)
- Ejemplo: Servicios jurídicos Montevideo $6K-60K vs Interior $4K-40K

ESTACIONALIDAD (Uruguay):
- ALTA actividad: Marzo-Junio (fiscal) +20%, Octubre-Diciembre (cierres) +15%
- BAJA actividad: Enero-Febrero (vacaciones) -25%, Julio-Agosto -10%
- Variación estacional típica: ±15-25%

SEÑALES DE ALERTA CRÍTICAS:
🚨 URGENTE (requiere acción inmediata):
- Rentabilidad < 30%
- Un cliente > 30% de facturación
- HHI > 2.500
- Ratio distribución/utilidad > 100% en alguna localidad
- Caída de ingresos MoM > 15%

⚠️ ATENCIÓN (requiere monitoreo):
- Rentabilidad 30-45% (por debajo de buena)
- Un cliente > 20% de facturación
- HHI 1.800-2.500
- Ratio distribución/utilidad 80-100%
- Caída de ingresos MoM 5-15%

CONTEXTO DE USO:
Estos benchmarks provienen de 4 investigaciones independientes consolidadas
(Gemini, Claude x2, Perplexity) + validación con fuentes oficiales uruguayas.
Nivel de confianza: ALTO para HHI, concentración cliente, ratios distribución.
MEDIO para rentabilidad (proxies Latam). BAJO para mix de servicios (usar 
datos propios de Conexión cuando estén disponibles).

ESTILO DE COMUNICACIÓN:
- Profesional pero accesible
- Cuantitativo (siempre con números)
- Accionable (insights → acciones)
- Contextual (considera realidad uruguaya)

PROHIBICIONES:
- NO frases genéricas ("se observa tendencia positiva")
- NO análisis superficial sin números
- NO recomendaciones vagas
- NO ignorar contexto local (Uruguay, estudios contables)

FORMATO:
- SIEMPRE retornar JSON válido
- SIEMPRE respetar límites de palabras
- SIEMPRE incluir números concretos en insights
"""

