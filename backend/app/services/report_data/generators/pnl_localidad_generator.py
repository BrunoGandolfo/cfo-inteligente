"""
Generador de datos para reporte P&L por Localidad
Compara Montevideo vs Mercedes en un período dado
Incluye narrativas generadas por Claude Sonnet 4.5
"""

from datetime import date, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from decimal import Decimal
import json
import re

from app.models import Operacion, TipoOperacion, Localidad
from app.services.ai.claude_client import ClaudeClient
from app.core.logger import get_logger

logger = get_logger(__name__)


class PnLLocalidadGenerator:
    """Genera datos para el reporte P&L comparativo por localidad."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate(
        self,
        fecha_inicio: date,
        fecha_fin: date,
        comparar_con_anterior: bool = True,
        incluir_narrativas: bool = True
    ) -> Dict[str, Any]:
        """
        Genera todos los datos necesarios para el reporte.
        
        Args:
            fecha_inicio: Fecha inicio del período
            fecha_fin: Fecha fin del período
            comparar_con_anterior: Si calcular comparación con período anterior
            incluir_narrativas: Si generar narrativas con Claude
        
        Returns:
            Dict con estructura para el template Jinja2
        """
        # Datos período actual
        mvd_actual = self._get_metricas_localidad(fecha_inicio, fecha_fin, Localidad.MONTEVIDEO)
        mer_actual = self._get_metricas_localidad(fecha_inicio, fecha_fin, Localidad.MERCEDES)
        total_actual = self._get_metricas_totales(fecha_inicio, fecha_fin)
        
        # Datos período anterior (si se solicita)
        mvd_anterior = None
        mer_anterior = None
        total_anterior = None
        
        if comparar_con_anterior:
            dias_periodo = (fecha_fin - fecha_inicio).days + 1
            fecha_inicio_ant = fecha_inicio - timedelta(days=dias_periodo)
            fecha_fin_ant = fecha_inicio - timedelta(days=1)
            
            mvd_anterior = self._get_metricas_localidad(fecha_inicio_ant, fecha_fin_ant, Localidad.MONTEVIDEO)
            mer_anterior = self._get_metricas_localidad(fecha_inicio_ant, fecha_fin_ant, Localidad.MERCEDES)
            total_anterior = self._get_metricas_totales(fecha_inicio_ant, fecha_fin_ant)
        
        # Calcular variaciones
        mvd_variaciones = self._calcular_variaciones(mvd_actual, mvd_anterior) if mvd_anterior else {}
        mer_variaciones = self._calcular_variaciones(mer_actual, mer_anterior) if mer_anterior else {}
        total_variaciones = self._calcular_variaciones(total_actual, total_anterior) if total_anterior else {}
        
        result = {
            'metadata': {
                'fecha_inicio': fecha_inicio.isoformat(),
                'fecha_fin': fecha_fin.isoformat(),
                'periodo_label': self._get_periodo_label(fecha_inicio, fecha_fin),
                'fecha_generacion': date.today().isoformat(),
            },
            'montevideo': {
                'actual': mvd_actual,
                'anterior': mvd_anterior,
                'variaciones': mvd_variaciones,
            },
            'mercedes': {
                'actual': mer_actual,
                'anterior': mer_anterior,
                'variaciones': mer_variaciones,
            },
            'total': {
                'actual': total_actual,
                'anterior': total_anterior,
                'variaciones': total_variaciones,
            },
            'comparativa': self._generar_tabla_comparativa(mvd_actual, mer_actual, total_actual),
        }
        
        # Generar narrativas con Claude
        if incluir_narrativas:
            logger.info("Generando narrativas con Claude...")
            narrativas = self._generar_narrativas_claude(result)
            result['narrativas'] = narrativas
            logger.info(f"Narrativas generadas: {len(narrativas)} campos")
        
        return result
    
    def _generar_narrativas_claude(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Genera narrativas usando Claude Sonnet."""
        try:
            # Crear prompt específico para comparativa de localidades
            prompt = self._build_localidad_prompt(datos)
            
            # Llamar a Claude
            claude = ClaudeClient()
            response = claude.complete(
                prompt=prompt,
                temperature=0.3,
                max_tokens=800,
                system_prompt=self._get_system_prompt()
            )
            
            # Limpiar respuesta de markdown si existe
            clean_response = re.sub(r'```json\s*|\s*```', '', response).strip()
            narrativas = json.loads(clean_response)
            
            logger.info("Narrativas generadas exitosamente con Claude")
            return narrativas
            
        except Exception as e:
            logger.error(f"Error generando narrativas con Claude: {e}")
            logger.info("Usando narrativas de fallback")
            return self._generar_narrativas_fallback(datos)
    
    def _build_localidad_prompt(self, datos: Dict[str, Any]) -> str:
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
    
    def _get_system_prompt(self) -> str:
        """System prompt para análisis de localidades."""
        return """Eres un CFO senior con 20 años de experiencia en firmas de servicios profesionales (legal, contable, consultoría).

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
    
    def _generar_narrativas_fallback(self, datos: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def _get_metricas_localidad(
        self,
        fecha_inicio: date,
        fecha_fin: date,
        localidad: Localidad
    ) -> Dict[str, Any]:
        """Obtiene métricas para una localidad específica."""
        
        base_filter = and_(
            Operacion.fecha >= fecha_inicio,
            Operacion.fecha <= fecha_fin,
            Operacion.localidad == localidad,
            Operacion.deleted_at.is_(None)
        )
        
        # Ingresos
        ingresos = self.db.query(func.coalesce(func.sum(Operacion.monto_uyu), 0)).filter(
            and_(base_filter, Operacion.tipo_operacion == TipoOperacion.INGRESO)
        ).scalar() or 0
        
        # Gastos
        gastos = self.db.query(func.coalesce(func.sum(Operacion.monto_uyu), 0)).filter(
            and_(base_filter, Operacion.tipo_operacion == TipoOperacion.GASTO)
        ).scalar() or 0
        
        # Retiros
        retiros = self.db.query(func.coalesce(func.sum(Operacion.monto_uyu), 0)).filter(
            and_(base_filter, Operacion.tipo_operacion == TipoOperacion.RETIRO)
        ).scalar() or 0
        
        # Distribuciones
        distribuciones = self.db.query(func.coalesce(func.sum(Operacion.monto_uyu), 0)).filter(
            and_(base_filter, Operacion.tipo_operacion == TipoOperacion.DISTRIBUCION)
        ).scalar() or 0
        
        # Cantidad de operaciones
        cant_operaciones = self.db.query(func.count(Operacion.id)).filter(base_filter).scalar() or 0
        
        # Cálculos derivados
        ingresos = float(ingresos)
        gastos = float(gastos)
        retiros = float(retiros)
        distribuciones = float(distribuciones)
        
        resultado_neto = ingresos - gastos
        total_extraido = retiros + distribuciones
        retenido = resultado_neto - total_extraido
        
        rentabilidad = (resultado_neto / ingresos * 100) if ingresos > 0 else 0
        ratio_extraccion = (total_extraido / resultado_neto * 100) if resultado_neto > 0 else 0
        
        return {
            'ingresos': round(ingresos, 2),
            'gastos': round(gastos, 2),
            'resultado_neto': round(resultado_neto, 2),
            'rentabilidad': round(rentabilidad, 2),
            'retiros': round(retiros, 2),
            'distribuciones': round(distribuciones, 2),
            'total_extraido': round(total_extraido, 2),
            'retenido': round(retenido, 2),
            'ratio_extraccion': round(ratio_extraccion, 2),
            'cantidad_operaciones': cant_operaciones,
        }
    
    def _get_metricas_totales(self, fecha_inicio: date, fecha_fin: date) -> Dict[str, Any]:
        """Obtiene métricas totales (ambas localidades)."""
        
        base_filter = and_(
            Operacion.fecha >= fecha_inicio,
            Operacion.fecha <= fecha_fin,
            Operacion.deleted_at.is_(None)
        )
        
        ingresos = float(self.db.query(func.coalesce(func.sum(Operacion.monto_uyu), 0)).filter(
            and_(base_filter, Operacion.tipo_operacion == TipoOperacion.INGRESO)
        ).scalar() or 0)
        
        gastos = float(self.db.query(func.coalesce(func.sum(Operacion.monto_uyu), 0)).filter(
            and_(base_filter, Operacion.tipo_operacion == TipoOperacion.GASTO)
        ).scalar() or 0)
        
        retiros = float(self.db.query(func.coalesce(func.sum(Operacion.monto_uyu), 0)).filter(
            and_(base_filter, Operacion.tipo_operacion == TipoOperacion.RETIRO)
        ).scalar() or 0)
        
        distribuciones = float(self.db.query(func.coalesce(func.sum(Operacion.monto_uyu), 0)).filter(
            and_(base_filter, Operacion.tipo_operacion == TipoOperacion.DISTRIBUCION)
        ).scalar() or 0)
        
        resultado_neto = ingresos - gastos
        total_extraido = retiros + distribuciones
        retenido = resultado_neto - total_extraido
        
        rentabilidad = (resultado_neto / ingresos * 100) if ingresos > 0 else 0
        ratio_extraccion = (total_extraido / resultado_neto * 100) if resultado_neto > 0 else 0
        
        return {
            'ingresos': round(ingresos, 2),
            'gastos': round(gastos, 2),
            'resultado_neto': round(resultado_neto, 2),
            'rentabilidad': round(rentabilidad, 2),
            'retiros': round(retiros, 2),
            'distribuciones': round(distribuciones, 2),
            'total_extraido': round(total_extraido, 2),
            'retenido': round(retenido, 2),
            'ratio_extraccion': round(ratio_extraccion, 2),
        }
    
    def _calcular_variaciones(
        self,
        actual: Dict[str, Any],
        anterior: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calcula variaciones porcentuales."""
        variaciones = {}
        
        for key in ['ingresos', 'gastos', 'resultado_neto', 'retiros', 'distribuciones']:
            val_actual = actual.get(key, 0)
            val_anterior = anterior.get(key, 0)
            
            if val_anterior and val_anterior != 0:
                variaciones[key] = round(((val_actual - val_anterior) / abs(val_anterior)) * 100, 2)
            else:
                variaciones[key] = 0 if val_actual == 0 else 100
        
        # Variación de rentabilidad en puntos porcentuales
        variaciones['rentabilidad_pp'] = round(
            actual.get('rentabilidad', 0) - anterior.get('rentabilidad', 0), 2
        )
        
        return variaciones
    
    def _generar_tabla_comparativa(
        self,
        mvd: Dict[str, Any],
        mer: Dict[str, Any],
        total: Dict[str, Any]
    ) -> list:
        """Genera estructura para tabla comparativa MVD vs Mercedes."""
        
        def pct_total(valor, total_val):
            return round((valor / total_val * 100), 1) if total_val > 0 else 0
        
        return [
            {
                'metrica': 'Ingresos',
                'montevideo': mvd['ingresos'],
                'montevideo_pct': pct_total(mvd['ingresos'], total['ingresos']),
                'mercedes': mer['ingresos'],
                'mercedes_pct': pct_total(mer['ingresos'], total['ingresos']),
                'total': total['ingresos'],
            },
            {
                'metrica': 'Gastos',
                'montevideo': mvd['gastos'],
                'montevideo_pct': pct_total(mvd['gastos'], total['gastos']),
                'mercedes': mer['gastos'],
                'mercedes_pct': pct_total(mer['gastos'], total['gastos']),
                'total': total['gastos'],
            },
            {
                'metrica': 'Resultado Neto',
                'montevideo': mvd['resultado_neto'],
                'montevideo_pct': pct_total(mvd['resultado_neto'], total['resultado_neto']),
                'mercedes': mer['resultado_neto'],
                'mercedes_pct': pct_total(mer['resultado_neto'], total['resultado_neto']),
                'total': total['resultado_neto'],
            },
            {
                'metrica': 'Retiros',
                'montevideo': mvd['retiros'],
                'montevideo_pct': pct_total(mvd['retiros'], total['retiros']),
                'mercedes': mer['retiros'],
                'mercedes_pct': pct_total(mer['retiros'], total['retiros']),
                'total': total['retiros'],
            },
            {
                'metrica': 'Distribuciones',
                'montevideo': mvd['distribuciones'],
                'montevideo_pct': pct_total(mvd['distribuciones'], total['distribuciones']),
                'mercedes': mer['distribuciones'],
                'mercedes_pct': pct_total(mer['distribuciones'], total['distribuciones']),
                'total': total['distribuciones'],
            },
        ]
    
    def _get_periodo_label(self, fecha_inicio: date, fecha_fin: date) -> str:
        """Genera label del período."""
        meses = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        
        if fecha_inicio.month == fecha_fin.month and fecha_inicio.year == fecha_fin.year:
            return f"{meses[fecha_inicio.month]} {fecha_inicio.year}"
        else:
            return f"{fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}"
