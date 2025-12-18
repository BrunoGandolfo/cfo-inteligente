"""
Fallback Generator - Genera insights sin IA

Genera insights basados en reglas + números cuando Claude no está disponible.
100% determinístico, sin llamadas externas.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import Dict, Any
from app.utils.formatters import format_currency, format_percentage


def generate_operativo_fallback(metricas: Dict[str, Any]) -> Dict[str, str]:
    """
    Genera insights operativos sin IA (solo reglas + números).
    
    Args:
        metricas: Dict con métricas calculadas
        
    Returns:
        Dict con 3 insights operativos
    """
    ingresos = float(metricas.get('ingresos_uyu', 0))
    _gastos = float(metricas.get('gastos_uyu', 0))  # noqa: F841 - preparado para expansión
    rentabilidad_neta = metricas.get('rentabilidad_neta', 0.0)
    
    area_lider = metricas.get('area_lider', {})
    area_nombre = area_lider.get('nombre', 'N/A')
    area_pct = area_lider.get('porcentaje', 0.0)
    
    ticket_ingreso = metricas.get('ticket_promedio_ingreso', 0.0)
    cantidad_ops = metricas.get('cantidad_operaciones', 0)
    
    # Insight 1: Rentabilidad general
    if rentabilidad_neta >= 35:
        nivel_rent = "excelente"
        accion = "Mantener estrategia actual y buscar escalamiento"
    elif rentabilidad_neta >= 25:
        nivel_rent = "buena"
        accion = "Optimizar gastos operativos para mejorar margen"
    else:
        nivel_rent = "por debajo del benchmark"
        accion = "Revisar estructura de costos urgentemente"
    
    insight_1 = (
        f"Rentabilidad neta {nivel_rent}: La rentabilidad de "
        f"{format_percentage(rentabilidad_neta)} sobre ingresos de "
        f"{format_currency(ingresos)} indica un desempeño {nivel_rent}. "
        f"Acción recomendada: {accion}."
    )
    
    # Insight 2: Área líder
    if area_pct >= 40:
        concentracion = "alta concentración"
        riesgo = "Riesgo: dependencia excesiva de un área"
    elif area_pct >= 30:
        concentracion = "concentración moderada"
        riesgo = "Balance adecuado"
    else:
        concentracion = "distribución equilibrada"
        riesgo = "Diversificación saludable"
    
    insight_2 = (
        f"Concentración de ingresos en {area_nombre}: "
        f"El área {area_nombre} genera {format_percentage(area_pct)} de los ingresos totales, "
        f"indicando {concentracion}. {riesgo}. "
        f"Considerar estrategias de diversificación o potenciación del área líder."
    )
    
    # Insight 3: Eficiencia operativa
    if cantidad_ops > 0:
        if ticket_ingreso >= 15000:
            eficiencia = "alto valor por operación"
            recomendacion = "Enfoque en clientes de alto valor agregado"
        elif ticket_ingreso >= 8000:
            eficiencia = "valor medio por operación"
            recomendacion = "Oportunidad de aumentar ticket con servicios adicionales"
        else:
            eficiencia = "bajo valor por operación"
            recomendacion = "Evaluar incremento de tarifas o reducción de operaciones de bajo valor"
        
        insight_3 = (
            f"Eficiencia operativa - ticket promedio: "
            f"{format_currency(ticket_ingreso)} en {cantidad_ops} operaciones "
            f"refleja {eficiencia}. {recomendacion}."
        )
    else:
        insight_3 = "Sin operaciones registradas en el período analizado."
    
    return {
        "insight_1": insight_1,
        "insight_2": insight_2,
        "insight_3": insight_3,
        "_generated_by": "fallback_operativo"
    }


def generate_estrategico_fallback(metricas: Dict[str, Any]) -> Dict[str, str]:
    """
    Genera insights estratégicos sin IA.
    
    Args:
        metricas: Dict con métricas calculadas
        
    Returns:
        Dict con 4 insights estratégicos
    """
    ingresos = float(metricas.get('ingresos_uyu', 0))
    _margen_operativo = metricas.get('margen_operativo', 0.0)  # noqa: F841 - preparado para expansión
    duracion_dias = metricas.get('duracion_dias', 0)
    
    rent_areas = metricas.get('rentabilidad_por_area', {})
    dist_areas = metricas.get('porcentaje_ingresos_por_area', {})
    
    # Tendencia (basada en margen)
    if rentabilidad_neta >= 30:
        tendencia_text = (
            f"Tendencia positiva sostenible: Rentabilidad neta de "
            f"{format_percentage(rentabilidad_neta)} durante {duracion_dias} días "
            f"indica operación eficiente con capacidad de crecimiento."
        )
    else:
        tendencia_text = (
            f"Oportunidad de mejora: Rentabilidad neta de "
            f"{format_percentage(rentabilidad_neta)} sugiere necesidad de "
            f"optimización de costos y revisión de estructura de precios."
        )
    
    # Patrón (análisis de áreas)
    if rent_areas:
        area_mas_rentable = max(rent_areas, key=rent_areas.get)
        rent_max = rent_areas[area_mas_rentable]
        area_menos_rentable = min(rent_areas, key=rent_areas.get)
        rent_min = rent_areas[area_menos_rentable]
        
        patron_text = (
            f"Disparidad en rentabilidad por área: {area_mas_rentable} lidera con "
            f"{format_percentage(rent_max)}, mientras {area_menos_rentable} muestra "
            f"{format_percentage(rent_min)}. Brecha de {format_percentage(rent_max - rent_min)} "
            f"indica oportunidad de estandarización de procesos."
        )
    else:
        patron_text = "Sin datos de rentabilidad por área para analizar patrones."
    
    # Oportunidad
    if dist_areas and rent_areas:
        # Encontrar área con alta rentabilidad pero baja participación
        oportunidades = []
        for area, rent in rent_areas.items():
            pct = dist_areas.get(area, 0.0)
            if rent >= 30 and pct < 25:
                oportunidades.append((area, rent, pct))
        
        if oportunidades:
            area_op, rent_op, pct_op = oportunidades[0]
            oportunidad_text = (
                f"Área subutilizada: {area_op} tiene rentabilidad de "
                f"{format_percentage(rent_op)} pero solo genera "
                f"{format_percentage(pct_op)} de ingresos. "
                f"Potencial de expansión significativo."
            )
        else:
            oportunidad_text = (
                f"Escalamiento: Con ingresos de {format_currency(ingresos)}, "
                f"existe oportunidad de inversión en marketing y captación "
                f"para aumentar volumen manteniendo márgenes."
            )
    else:
        oportunidad_text = "Recopilar más datos históricos para identificar oportunidades estratégicas."
    
    # Riesgo
    if dist_areas:
        max_pct = max(dist_areas.values())
        if max_pct >= 45:
            riesgo_text = (
                f"Riesgo de concentración: {format_percentage(max_pct)} de ingresos "
                f"en una sola área crea vulnerabilidad ante cambios de mercado. "
                f"Priorizar diversificación en próximos 6 meses."
            )
        else:
            riesgo_text = (
                f"Riesgo controlado: Distribución equilibrada de ingresos entre áreas "
                f"reduce vulnerabilidad. Monitorear cambios trimestrales."
            )
    else:
        riesgo_text = "Sin datos de distribución para evaluar riesgos."
    
    return {
        "tendencia": tendencia_text,
        "patron": patron_text,
        "oportunidad": oportunidad_text,
        "riesgo": riesgo_text,
        "_generated_by": "fallback_estrategico"
    }


def generate_comparativo_fallback(
    metricas_actual: Dict[str, Any],
    metricas_anterior: Dict[str, Any]
) -> Dict[str, str]:
    """
    Genera insights comparativos sin IA.
    
    Args:
        metricas_actual: Métricas período actual
        metricas_anterior: Métricas período anterior
        
    Returns:
        Dict con 3 insights comparativos
    """
    var_ingresos = metricas_actual.get('variacion_mom_ingresos')
    var_gastos = metricas_actual.get('variacion_mom_gastos')
    var_rentabilidad = metricas_actual.get('variacion_mom_rentabilidad')
    
    ingresos_actual = float(metricas_actual.get('ingresos_uyu', 0))
    ingresos_anterior = float(metricas_anterior.get('ingresos_uyu', 0))
    
    # Cambio principal
    if var_ingresos is not None:
        if var_ingresos > 10:
            calificacion = "crecimiento significativo"
            causa = "Posibles causas: nuevos clientes, aumento de tarifas, o estacionalidad positiva"
        elif var_ingresos > 0:
            calificacion = "crecimiento moderado"
            causa = "Evolución natural del negocio"
        elif var_ingresos > -10:
            calificacion = "estabilidad"
            causa = "Operación consistente sin cambios significativos"
        else:
            calificacion = "descenso preocupante"
            causa = "Requiere análisis detallado de retención de clientes"
        
        cambio_principal = (
            f"Variación de ingresos: {format_percentage(var_ingresos)} ({calificacion}). "
            f"Ingresos pasaron de {format_currency(ingresos_anterior)} a "
            f"{format_currency(ingresos_actual)}. {causa}."
        )
    else:
        cambio_principal = "Sin datos de variación disponibles."
    
    # Evaluación
    if var_rentabilidad is not None and var_ingresos is not None:
        diff_rent = rent_actual - rent_anterior
        if diff_rent > 5 and var_ingresos > 0:
            evaluacion = (
                f"Cambio positivo excepcional: Ingresos subieron {format_percentage(var_ingresos)} "
                f"Y rentabilidad mejoró {diff_rent:+.1f} puntos porcentuales. "
                f"Indica crecimiento eficiente con control de costos."
            )
        elif diff_rent < -5 and var_ingresos > 0:
            evaluacion = (
                f"Alerta: Ingresos crecieron {format_percentage(var_ingresos)} "
                f"pero rentabilidad cayó {diff_rent:.1f}pp. "
                f"Crecimiento no sostenible, costos aumentaron más rápido."
            )
        else:
            evaluacion = (
                f"Cambio moderado: Variación de rentabilidad ({diff_rent:+.1f}pp) "
                f"alineada con variación de ingresos ({format_percentage(var_ingresos)}). "
                f"Operación estable."
            )
    else:
        evaluacion = "Sin suficientes datos para evaluar tendencia."
    
    # Recomendación
    if var_ingresos is not None and var_gastos is not None:
        if var_ingresos > 0 and var_gastos < var_ingresos:
            recomendacion = (
                f"Mantener estrategia actual: Ingresos crecen ({format_percentage(var_ingresos)}) "
                f"más rápido que gastos ({format_percentage(var_gastos)}). "
                f"Capitalizar momento con inversión en áreas de alto ROI."
            )
        elif var_ingresos < 0:
            recomendacion = (
                f"Acción correctiva inmediata: Caída de ingresos ({format_percentage(var_ingresos)}) "
                f"requiere plan de recuperación. Priorizar retención de clientes "
                f"y revisión de propuesta de valor."
            )
        else:
            recomendacion = (
                "Revisión estratégica: Analizar qué funcionó y qué no en período anterior "
                "para ajustar plan del próximo trimestre."
            )
    else:
        recomendacion = "Continuar monitoreando métricas clave mensualmente."
    
    return {
        "cambio_principal": cambio_principal,
        "evaluacion": evaluacion,
        "recomendacion": recomendacion,
        "_generated_by": "fallback_comparativo"
    }

