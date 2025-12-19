"""
Prompts para generación de narrativas del reporte P&L por Localidad.
Extraído de pnl_localidad_generator.py para reducir su tamaño.
"""
from typing import Dict, Any

SYSTEM_PROMPT = """Eres un CFO senior con 20 años de experiencia en firmas de servicios profesionales (legal, contable, consultoría).

Tu análisis debe ser:
- CONCRETO: Cita números específicos del período
- ACCIONABLE: Recomendaciones que se puedan implementar
- PROFESIONAL: Tono ejecutivo, sin emojis, sin exageraciones
- BALANCEADO: Reconoce logros pero señala riesgos

BENCHMARKS DE REFERENCIA:
- Rentabilidad saludable: >60%
- Ratio extracción sostenible: <70%
- Concentración geográfica ideal: 50-50 entre oficinas

Responde SIEMPRE en JSON válido."""


def build_localidad_prompt(datos: Dict[str, Any]) -> str:
    """Construye prompt específico para análisis de localidades."""
    mvd = datos['montevideo']['actual']
    mer = datos['mercedes']['actual']
    total = datos['total']['actual']
    var = datos['total'].get('variaciones', {})
    
    return f"""Analiza el desempeño financiero comparativo de las dos oficinas de Conexión Consultora (firma legal-contable uruguaya).

PERÍODO: {datos['metadata']['periodo_label']}

MONTEVIDEO:
- Ingresos: ${mvd['ingresos']:,.0f} ({mvd['ingresos']/total['ingresos']*100:.1f}% del total)
- Gastos: ${mvd['gastos']:,.0f}
- Resultado Neto: ${mvd['resultado_neto']:,.0f}
- Rentabilidad: {mvd['rentabilidad']:.1f}%
- Retiros: ${mvd['retiros']:,.0f}
- Distribuciones: ${mvd['distribuciones']:,.0f}
- Ratio Extracción: {mvd['ratio_extraccion']:.1f}%

MERCEDES:
- Ingresos: ${mer['ingresos']:,.0f} ({mer['ingresos']/total['ingresos']*100:.1f}% del total)
- Gastos: ${mer['gastos']:,.0f}
- Resultado Neto: ${mer['resultado_neto']:,.0f}
- Rentabilidad: {mer['rentabilidad']:.1f}%
- Retiros: ${mer['retiros']:,.0f}
- Distribuciones: ${mer['distribuciones']:,.0f}
- Ratio Extracción: {mer['ratio_extraccion']:.1f}%

TOTALES CONSOLIDADOS:
- Ingresos: ${total['ingresos']:,.0f}
- Resultado Neto: ${total['resultado_neto']:,.0f}
- Rentabilidad: {total['rentabilidad']:.1f}%
- Ratio Extracción Total: {total['ratio_extraccion']:.1f}%

VARIACIONES VS PERÍODO ANTERIOR:
- Ingresos: {var.get('ingresos', 0):+.1f}%
- Resultado: {var.get('resultado_neto', 0):+.1f}%
- Rentabilidad: {var.get('rentabilidad_pp', 0):+.1f} puntos porcentuales

GENERA UN ANÁLISIS EN FORMATO JSON CON EXACTAMENTE ESTAS CLAVES:

{{
  "resumen_ejecutivo": "Párrafo de 2-3 oraciones resumiendo el desempeño general del período. Menciona cifras clave.",
  "analisis_montevideo": "Párrafo analizando Montevideo: fortalezas, debilidades, tendencia. Máximo 80 palabras.",
  "analisis_mercedes": "Párrafo analizando Mercedes: fortalezas, debilidades, tendencia. Máximo 80 palabras.",
  "comparativa": "Párrafo comparando ambas oficinas: quién lidera, brechas, equilibrio. Máximo 80 palabras.",
  "alerta_extracciones": "Si ratio extracción >70% en alguna localidad, advertencia específica. Si no, escribir 'Sin alertas de extracción.'",
  "fortaleza_1": "Primera fortaleza del período (1 oración)",
  "fortaleza_2": "Segunda fortaleza del período (1 oración)",
  "atencion_1": "Primer punto de atención o riesgo (1 oración)",
  "atencion_2": "Segundo punto de atención o riesgo (1 oración)",
  "recomendacion_1": "Primera recomendación estratégica concreta",
  "recomendacion_2": "Segunda recomendación estratégica concreta",
  "recomendacion_3": "Tercera recomendación estratégica concreta"
}}

RESPONDE SOLO CON EL JSON, SIN TEXTO ADICIONAL."""


def generate_fallback_narrativas(datos: Dict[str, Any]) -> Dict[str, Any]:
    """Genera narrativas básicas sin IA cuando Claude falla."""
    mvd = datos['montevideo']['actual']
    mer = datos['mercedes']['actual']
    total = datos['total']['actual']
    
    lider = "Montevideo" if mvd['ingresos'] > mer['ingresos'] else "Mercedes"
    pct_lider = max(mvd['ingresos'], mer['ingresos']) / total['ingresos'] * 100 if total['ingresos'] > 0 else 0
    
    return {
        "resumen_ejecutivo": f"En {datos['metadata']['periodo_label']}, Conexión Consultora registró ingresos de ${total['ingresos']:,.0f} con una rentabilidad del {total['rentabilidad']:.1f}%. {lider} lideró la facturación con el {pct_lider:.1f}% del total.",
        "analisis_montevideo": f"Montevideo generó ${mvd['ingresos']:,.0f} con rentabilidad de {mvd['rentabilidad']:.1f}%. El ratio de extracción fue {mvd['ratio_extraccion']:.1f}%, {'requiriendo atención' if mvd['ratio_extraccion'] > 70 else 'dentro de parámetros saludables'}.",
        "analisis_mercedes": f"Mercedes generó ${mer['ingresos']:,.0f} con rentabilidad de {mer['rentabilidad']:.1f}%. El ratio de extracción fue {mer['ratio_extraccion']:.1f}%, {'requiriendo atención' if mer['ratio_extraccion'] > 70 else 'dentro de parámetros saludables'}.",
        "comparativa": f"{lider} concentra la mayor parte de los ingresos del período ({pct_lider:.1f}%). La rentabilidad consolidada de {total['rentabilidad']:.1f}% refleja la operación combinada de ambas oficinas.",
        "alerta_extracciones": f"Ratio de extracción elevado ({total['ratio_extraccion']:.1f}%). Revisar política de extracciones para mantener capital de trabajo." if total['ratio_extraccion'] > 70 else "Sin alertas de extracción. Los niveles de retención son adecuados.",
        "fortaleza_1": f"Rentabilidad consolidada del {total['rentabilidad']:.1f}%, indicando operación eficiente.",
        "fortaleza_2": f"Resultado neto positivo de ${total['resultado_neto']:,.0f} en el período.",
        "atencion_1": f"Concentración geográfica: {lider} representa {pct_lider:.1f}% de los ingresos.",
        "atencion_2": "Monitorear sostenibilidad del ratio de extracciones vs retención.",
        "recomendacion_1": "Analizar mix de servicios por localidad para identificar oportunidades de crecimiento.",
        "recomendacion_2": "Establecer política formal de retención mínima del 30% de utilidades.",
        "recomendacion_3": "Revisar asignación de gastos entre oficinas para optimizar rentabilidad por localidad."
    }



