"""
Generador de datos para reporte P&L por Localidad
Compara Montevideo vs Mercedes en un período dado
Incluye narrativas generadas por Claude Sonnet 4.5
"""

from datetime import date, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import json
import re

from app.models import Operacion, TipoOperacion, Localidad
from app.services.ai.claude_client import ClaudeClient
from app.core.logger import get_logger
from app.services.report_data.generators.pnl_localidad_prompts import (
    SYSTEM_PROMPT, build_localidad_prompt, generate_fallback_narrativas
)

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
        """Genera todos los datos necesarios para el reporte P&L por localidad."""
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
        """Delegado a pnl_localidad_prompts."""
        return build_localidad_prompt(datos)
    
    def _get_system_prompt(self) -> str:
        """Delegado a pnl_localidad_prompts."""
        return SYSTEM_PROMPT
    
    def _generar_narrativas_fallback(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Delegado a pnl_localidad_prompts."""
        return generate_fallback_narrativas(datos)
    
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
