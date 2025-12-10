"""
Narrative Builder - Genera texto explicativo automático para reportes

Funciones puras que convierten métricas en narrativa profesional.

Autor: Sistema CFO Inteligente
Fecha: Noviembre 2025
"""

from typing import Dict, Any
from app.utils.formatters import format_currency, format_percentage


def build_revenue_commentary(metricas: Dict[str, Any]) -> str:
    """
    Genera párrafo de análisis de ingresos.
    
    Args:
        metricas: Dict con métricas calculadas
        
    Returns:
        String con narrativa profesional (2-3 oraciones)
    """
    ingresos = metricas.get('ingresos_uyu', 0)
    var_mom = metricas.get('variacion_mom_ingresos')
    area_lider = metricas.get('area_lider', {})
    ticket_promedio = metricas.get('ticket_promedio_ingreso', 0)
    cantidad_ops = metricas.get('cantidad_ingresos', 0)
    
    parrafos = []
    
    # Párrafo 1: Resultado general con variación
    if var_mom is not None:
        if var_mom > 15:
            calificativo = "un crecimiento excepcional"
            emocion = "destacable"
        elif var_mom > 5:
            calificativo = "un incremento"
            emocion = "positivo"
        elif var_mom > -5:
            calificativo = "estabilidad"
            emocion = "estable"
        elif var_mom > -15:
            calificativo = "una disminución"
            emocion = "que requiere atención"
        else:
            calificativo = "una caída significativa"
            emocion = "preocupante"
        
        if abs(var_mom) > 5:
            parrafos.append(
                f"Los ingresos del período totalizaron {format_currency(ingresos)}, "
                f"registrando {calificativo} del {format_percentage(abs(var_mom))} "
                f"respecto al período anterior, resultado {emocion} para el estudio."
            )
        else:
            parrafos.append(
                f"Los ingresos del período alcanzaron {format_currency(ingresos)}, "
                f"manteniéndose estables respecto al período anterior."
            )
    else:
        parrafos.append(
            f"Los ingresos del período totalizaron {format_currency(ingresos)}."
        )
    
    # Párrafo 2: Composición (área líder)
    if area_lider and area_lider.get('nombre'):
        area_nombre = area_lider['nombre']
        area_pct = area_lider.get('porcentaje', 0)
        
        if area_pct > 50:
            concentracion = "una concentración significativa"
        elif area_pct > 30:
            concentracion = "el principal aporte"
        else:
            concentracion = "una contribución importante"
        
        parrafos.append(
            f"El área {area_nombre} representa {concentracion} con el "
            f"{format_percentage(area_pct)} de los ingresos totales."
        )
    
    # Párrafo 3: Eficiencia operativa
    if cantidad_ops > 0:
        parrafos.append(
            f"Se registraron {cantidad_ops} operaciones de ingreso con un ticket "
            f"promedio de {format_currency(ticket_promedio)}."
        )
    
    return ' '.join(parrafos)


def build_expense_commentary(metricas: Dict[str, Any]) -> str:
    """
    Genera párrafo de análisis de gastos.
    
    Args:
        metricas: Dict con métricas calculadas
        
    Returns:
        String con narrativa profesional
    """
    gastos = metricas.get('gastos_uyu', 0)
    var_mom = metricas.get('variacion_mom_gastos')
    ingresos = metricas.get('ingresos_uyu', 0)
    ratio_gastos = (gastos / ingresos * 100) if ingresos > 0 else 0
    
    parrafos = []
    
    # Párrafo 1: Nivel de gastos
    if ratio_gastos < 30:
        eficiencia = "excelente control de costos"
    elif ratio_gastos < 50:
        eficiencia = "estructura de costos eficiente"
    elif ratio_gastos < 70:
        eficiencia = "nivel de gastos aceptable"
    else:
        eficiencia = "oportunidad de optimización de costos"
    
    parrafos.append(
        f"Los gastos operativos totalizaron {format_currency(gastos)}, "
        f"representando el {format_percentage(ratio_gastos)} de los ingresos, "
        f"indicando {eficiencia}."
    )
    
    # Párrafo 2: Variación
    if var_mom is not None and abs(var_mom) > 10:
        if var_mom > 0:
            parrafos.append(
                f"Se observa un incremento del {format_percentage(var_mom)} en gastos "
                f"respecto al período anterior, que debe monitorearse."
            )
        else:
            parrafos.append(
                f"Los gastos disminuyeron {format_percentage(abs(var_mom))} "
                f"vs período anterior, reflejando mejoras en eficiencia operativa."
            )
    
    return ' '.join(parrafos)


def build_margin_commentary(metricas: Dict[str, Any]) -> str:
    """
    Genera párrafo de análisis de rentabilidad.
    
    Args:
        metricas: Dict con métricas calculadas
        
    Returns:
        String con narrativa profesional
    """
    rentabilidad_neta = metricas.get('rentabilidad_neta', 0)
    utilidad_neta = metricas.get('utilidad_neta_uyu', 0)
    var_margen = metricas.get('variacion_mom_rentabilidad')
    
    # Calificación del margen
    if rentabilidad_neta > 60:
        calificacion = "excepcional"
        benchmark = "superando ampliamente estándares de la industria"
    elif rentabilidad_neta > 40:
        calificacion = "sólido"
        benchmark = "ubicándose por encima del promedio del sector"
    elif rentabilidad_neta > 20:
        calificacion = "aceptable"
        benchmark = "alineado con estándares de mercado"
    else:
        calificacion = "bajo"
        benchmark = "requiriendo acciones para mejorar rentabilidad"
    
    texto = (
        f"La rentabilidad neta del período alcanzó {format_percentage(rentabilidad_neta)}, "
        f"nivel {calificacion} {benchmark}. "
        f"Esto se traduce en una utilidad neta de {format_currency(utilidad_neta)}."
    )
    
    # Evolución del margen
    if var_margen and abs(var_margen) > 3:
        if var_margen > 0:
            texto += (
                f" El margen mejoró {format_percentage(var_margen)} puntos porcentuales "
                f"vs período anterior, tendencia altamente favorable."
            )
        else:
            texto += (
                f" Se observa compresión de margen de {format_percentage(abs(var_margen))} "
                f"puntos porcentuales que requiere análisis de causas."
            )
    
    return texto


def build_area_commentary(metricas: Dict[str, Any]) -> str:
    """
    Genera párrafo de análisis por áreas.
    
    Args:
        metricas: Dict con métricas calculadas
        
    Returns:
        String con narrativa profesional
    """
    area_lider = metricas.get('area_lider', {})
    dist_areas = metricas.get('porcentaje_ingresos_por_area', {})
    rent_areas = metricas.get('rentabilidad_por_area', {})
    
    if not area_lider or not area_lider.get('nombre'):
        return "Análisis por áreas no disponible para este período."
    
    area_nombre = area_lider['nombre']
    area_pct = area_lider.get('porcentaje', 0)
    area_rent = rent_areas.get(area_nombre, 0) if rent_areas else 0
    
    # Análisis de concentración
    if area_pct > 60:
        concentracion = "alta concentración"
        riesgo = "diversificar cartera de servicios"
    elif area_pct > 40:
        concentracion = "concentración moderada"
        riesgo = "mantener estrategias actuales"
    else:
        concentracion = "distribución balanceada"
        riesgo = "continuar diversificación"
    
    texto = (
        f"El área {area_nombre} lidera la generación de ingresos con "
        f"{format_percentage(area_pct)} del total, evidenciando {concentracion}. "
    )
    
    if area_rent > 0:
        texto += f"Esta área presenta una rentabilidad de {format_percentage(area_rent)}. "
    
    texto += f"Recomendación estratégica: {riesgo}."
    
    # Mencionar segunda área si existe
    if len(dist_areas) > 1:
        areas_sorted = sorted(dist_areas.items(), key=lambda x: x[1], reverse=True)
        if len(areas_sorted) > 1:
            segunda_area = areas_sorted[1][0]
            segunda_pct = areas_sorted[1][1]
            texto += (
                f" La segunda área en importancia es {segunda_area} "
                f"con {format_percentage(segunda_pct)} de participación."
            )
    
    return texto


def build_executive_summary(metricas: Dict[str, Any]) -> str:
    """
    Genera párrafo de resumen ejecutivo para la página principal.
    
    Args:
        metricas: Dict con métricas calculadas
        
    Returns:
        String con 3-4 oraciones de síntesis ejecutiva
    """
    ingresos = metricas.get('ingresos_uyu', 0)
    gastos = metricas.get('gastos_uyu', 0)
    utilidad = metricas.get('utilidad_neta_uyu', 0)
    rentabilidad = metricas.get('rentabilidad_neta', 0)
    period_label = metricas.get('period_label', 'el período')
    var_mom = metricas.get('variacion_mom_ingresos')
    area_lider = metricas.get('area_lider', {})
    
    parrafos = []
    
    # Oración 1: Resultado general
    if rentabilidad >= 30:
        calificativo = "un desempeño financiero excelente"
    elif rentabilidad >= 15:
        calificativo = "resultados financieros saludables"
    elif rentabilidad >= 0:
        calificativo = "márgenes moderados que requieren optimización"
    else:
        calificativo = "resultados que demandan atención inmediata"
    
    parrafos.append(
        f"Durante {period_label}, la empresa registró {calificativo} "
        f"con ingresos de {format_currency(ingresos)} y una rentabilidad neta de {format_percentage(rentabilidad)}."
    )
    
    # Oración 2: Resultado neto
    if utilidad > 0:
        parrafos.append(
            f"El resultado neto fue positivo con una utilidad de {format_currency(utilidad)}, "
            f"después de gastos operativos de {format_currency(gastos)}."
        )
    else:
        parrafos.append(
            f"El resultado neto fue negativo por {format_currency(abs(utilidad))}, "
            f"con gastos operativos de {format_currency(gastos)} que superaron los ingresos."
        )
    
    # Oración 3: Tendencia (si hay variación)
    if var_mom is not None:
        if var_mom > 10:
            parrafos.append(f"Los ingresos muestran un crecimiento del {format_percentage(var_mom)} respecto al período anterior, indicando una tendencia positiva.")
        elif var_mom < -10:
            parrafos.append(f"Los ingresos disminuyeron {format_percentage(abs(var_mom))} respecto al período anterior, requiriendo análisis de causas.")
        else:
            parrafos.append(f"Los ingresos se mantienen estables con una variación del {format_percentage(var_mom)} respecto al período anterior.")
    
    # Oración 4: Área líder
    if area_lider and area_lider.get('nombre'):
        parrafos.append(
            f"El área {area_lider.get('nombre')} lidera la facturación con "
            f"{format_percentage(area_lider.get('porcentaje', 0))} del total de ingresos."
        )
    
    return " ".join(parrafos)
