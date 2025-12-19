"""
Report Orchestrator - MAESTRO del Sistema de Reportes

Coordina TODO el flujo de generación de reportes PDF.
NO calcula, solo ORQUESTA.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import Dict, Any, Optional
from datetime import datetime, date
from pathlib import Path
import base64
import tempfile
import shutil

from sqlalchemy.orm import Session

from app.schemas.report.request import ReportRequest
from app.repositories.operations_repository import OperationsRepository
from app.models import TipoOperacion
from app.services.validators.request_validator import validate_request
from app.services.validators.data_validator import validate_sufficient_data, validate_data_quality
from app.services.metrics.metrics_aggregator import MetricsAggregator
from app.services.charts.chart_factory import ChartFactory
from app.services.ai.insights_orchestrator import InsightsOrchestrator
from app.services.pdf.report_builder import ReportBuilder
from app.utils.date_resolver import resolve_period, get_comparison_period
from app.core.logger import get_logger

logger = get_logger(__name__)


class ReportOrchestrator:
    """
    MAESTRO: Coordina TODA la generación de reportes PDF.
    
    RESPONSABILIDAD: Orquestar flujo completo (NO implementar lógica).
    PATRÓN: Facade Pattern + Orchestration Pattern.
    
    Flujo completo:
    1. Validar request
    2. Resolver fechas (períodos predefinidos → rangos)
    3. Obtener operaciones de BD
    4. Validar datos suficientes
    5. Calcular métricas (29+)
    6. Generar gráficos (7 tipos)
    7. Generar insights con IA
    8. Compilar PDF (templates → HTML → PDF)
    9. Cleanup archivos temporales
    10. Retornar metadata
    
    Dependencias inyectadas:
    - db: Session (SQLAlchemy)
    - chart_config: Dict (configuración charts)
    - insights_orchestrator: InsightsOrchestrator (opcional)
    - report_builder: ReportBuilder (opcional)
    
    Principios aplicados:
    - Single Responsibility: Solo coordina
    - Dependency Injection: Todas las deps inyectadas
    - Error Handling: Manejo robusto con cleanup
    - Logging: Completo para debugging
    
    Ejemplo:
        >>> orchestrator = ReportOrchestrator(
        ...     db=db,
        ...     chart_config=get_chart_config('moderna_2024'),
        ...     insights_orchestrator=insights_orch,
        ...     report_builder=builder
        ... )
        >>> result = orchestrator.generate(request)
        >>> print(result['pdf_path'])
        'output/reports/Reporte_CFO_Oct2025.pdf'
    """
    
    def __init__(
        self,
        db: Session,
        chart_config: Dict[str, Any],
        insights_orchestrator: Optional[InsightsOrchestrator] = None,
        report_builder: Optional[ReportBuilder] = None
    ):
        """
        Constructor con Dependency Injection.
        
        Args:
            db: Session de SQLAlchemy
            chart_config: Configuración de charts
            insights_orchestrator: Orchestrator de insights (opcional)
            report_builder: Builder de PDF (opcional)
        """
        self.db = db
        self.chart_config = chart_config
        self.insights_orchestrator = insights_orchestrator
        self.report_builder = report_builder or ReportBuilder()
        
        # Repository (composición)
        self.repo = OperationsRepository(db)
        
        # Directorio temporal para charts
        self.temp_dir = None
        
        logger.info("ReportOrchestrator inicializado")
    
    def generate(self, request: ReportRequest) -> Dict[str, Any]:
        """
        Genera reporte PDF completo.
        
        FLUJO MAESTRO - Coordina todo.
        
        Args:
            request: ReportRequest validado
            
        Returns:
            Dict con resultado:
            {
                'pdf_path': str,
                'filename': str,
                'size_kb': float,
                'pages': int,
                'generation_time_seconds': float,
                'metadata': dict,
                'warnings': List[str]
            }
            
        Raises:
            InvalidDateRangeError: Si request inválido
            InsufficientDataError: Si no hay suficientes datos
            PDFGenerationError: Si falla generación PDF
        """
        start_time = datetime.now()
        warnings = []
        
        logger.info("═" * 70)
        logger.info("INICIANDO GENERACIÓN DE REPORTE PDF")
        logger.info("═" * 70)
        
        try:
            # ═══════════════════════════════════════════════════════════════
            # PASO 1: VALIDAR REQUEST
            # ═══════════════════════════════════════════════════════════════
            
            logger.info("PASO 1: Validando request")
            validate_request(request)
            logger.info("✓ Request válido")
            
            # ═══════════════════════════════════════════════════════════════
            # PASO 2: RESOLVER FECHAS
            # ═══════════════════════════════════════════════════════════════
            
            logger.info("PASO 2: Resolviendo fechas")
            fecha_inicio, fecha_fin = resolve_period(
                tipo=request.period.tipo,
                fecha_inicio_custom=request.period.fecha_inicio,
                fecha_fin_custom=request.period.fecha_fin
            )
            logger.info(f"✓ Período: {fecha_inicio} a {fecha_fin}")
            
            # Resolver comparación si está activa
            fecha_inicio_comp = None
            fecha_fin_comp = None
            
            if request.comparison and request.comparison.activo:
                fecha_inicio_comp, fecha_fin_comp = get_comparison_period(
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    tipo_comparacion=request.comparison.tipo,
                    fecha_inicio_custom=request.comparison.fecha_inicio,
                    fecha_fin_custom=request.comparison.fecha_fin
                )
                logger.info(f"✓ Comparación: {fecha_inicio_comp} a {fecha_fin_comp}")
            
            # ═══════════════════════════════════════════════════════════════
            # PASO 3: OBTENER DATOS
            # ═══════════════════════════════════════════════════════════════
            
            logger.info("PASO 3: Obteniendo operaciones")
            operaciones = self.repo.get_by_period(fecha_inicio, fecha_fin)
            logger.info(f"✓ Operaciones encontradas: {len(operaciones)}")
            
            # Obtener operaciones de comparación si aplica
            operaciones_comparacion = None
            if fecha_inicio_comp and fecha_fin_comp:
                operaciones_comparacion = self.repo.get_by_period(
                    fecha_inicio_comp, fecha_fin_comp
                )
                logger.info(f"✓ Operaciones comparación: {len(operaciones_comparacion)}")
            
            # Obtener histórico para proyecciones si está activado
            historico_mensual = None
            if request.options.incluir_proyecciones:
                historico_mensual = self.repo.get_ingresos_mensuales_historico(
                    fecha_fin_reporte=fecha_fin,
                    meses=12
                )
                logger.info(f"✓ Histórico obtenido: {len(historico_mensual)} meses hasta {fecha_fin}")
            
            # Obtener operaciones YoY si el período es comparable
            operaciones_yoy = None
            operaciones_qoq = None
            
            if self._is_period_comparable_yoy(fecha_inicio, fecha_fin):
                try:
                    fecha_inicio_yoy = fecha_inicio.replace(year=fecha_inicio.year - 1)
                    fecha_fin_yoy = fecha_fin.replace(year=fecha_fin.year - 1)
                    
                    operaciones_yoy = self.repo.get_by_period(fecha_inicio_yoy, fecha_fin_yoy)
                    logger.info(f"✓ Operaciones YoY: {len(operaciones_yoy)}")
                except ValueError:
                    logger.warning("No se pudo calcular período YoY (edge case fechas)")
            
            if self._is_period_comparable_qoq(fecha_inicio, fecha_fin):
                fecha_inicio_qoq, fecha_fin_qoq = self._get_quarter_before(fecha_inicio, fecha_fin)
                if fecha_inicio_qoq and fecha_fin_qoq:
                    operaciones_qoq = self.repo.get_by_period(fecha_inicio_qoq, fecha_fin_qoq)
                    logger.info(f"✓ Operaciones QoQ: {len(operaciones_qoq)}")
            
            # ═══════════════════════════════════════════════════════════════
            # PASO 4: VALIDAR DATOS
            # ═══════════════════════════════════════════════════════════════
            
            logger.info("PASO 4: Validando datos")
            validate_sufficient_data(operaciones, minimo_requerido=20)
            
            # Validar calidad (no crítico, solo warnings)
            quality_report = validate_data_quality(operaciones)
            if quality_report['warnings']:
                warnings.extend(quality_report['warnings'])
            
            logger.info("✓ Datos suficientes y validados")
            
            # ═══════════════════════════════════════════════════════════════
            # PASO 5: CALCULAR MÉTRICAS
            # ═══════════════════════════════════════════════════════════════
            
            logger.info("PASO 5: Calculando métricas")
            aggregator = MetricsAggregator(
                operaciones=operaciones,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                operaciones_comparacion=operaciones_comparacion,
                historico_mensual=historico_mensual,
                operaciones_yoy=operaciones_yoy,
                operaciones_qoq=operaciones_qoq
            )
            
            metricas = aggregator.aggregate_all()
            logger.info(f"✓ Métricas calculadas: {len(metricas)} métricas")
            
            # ═══════════════════════════════════════════════════════════════
            # PASO 5B: OBTENER TOP 10 OPERACIONES
            # ═══════════════════════════════════════════════════════════════
            
            logger.info("PASO 5B: Obteniendo Top 10 operaciones")
            top_10_ingresos = self.repo.get_top_operaciones(
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                tipo_operacion=TipoOperacion.INGRESO,
                limit=10
            )
            logger.info(f"✓ Top 10 ingresos obtenidos: {len(top_10_ingresos)}")
            
            # ═══════════════════════════════════════════════════════════════
            # PASO 6: GENERAR GRÁFICOS
            # ═══════════════════════════════════════════════════════════════
            
            logger.info("PASO 6: Generando gráficos")
            charts_paths = self._generate_charts(metricas, operaciones)
            logger.info(f"✓ Gráficos generados: {len(charts_paths)} charts")
            
            # ═══════════════════════════════════════════════════════════════
            # PASO 7: GENERAR INSIGHTS CON IA
            # ═══════════════════════════════════════════════════════════════
            
            insights = {}
            if request.options.incluir_insights_ia and self.insights_orchestrator:
                logger.info("PASO 7: Generando insights con IA")
                try:
                    duracion_dias = (fecha_fin - fecha_inicio).days + 1
                    
                    # Calcular métricas de comparación si disponibles
                    metricas_comparacion = None
                    if operaciones_comparacion:
                        logger.info("  → Calculando métricas de comparación para insights")
                        comp_aggregator = MetricsAggregator(
                            operaciones=operaciones_comparacion,
                            fecha_inicio=fecha_inicio_comp,
                            fecha_fin=fecha_fin_comp
                        )
                        metricas_comparacion = comp_aggregator.aggregate_all()
                        logger.info(f"  ✓ Métricas comparación calculadas")
                    
                    # Generar insights con Claude
                    insights = self.insights_orchestrator.generate_all(
                        metricas=metricas,
                        duracion_dias=duracion_dias,
                        tiene_comparacion=bool(operaciones_comparacion),
                        metricas_comparacion=metricas_comparacion,
                        timeout=30,
                        usar_ia=True
                    )
                    
                    # Validar que insights no estén vacíos
                    if not insights or len(insights) == 0:
                        logger.warning("  ⚠️ Claude retornó insights vacíos")
                        raise ValueError("Insights vacíos")
                    
                    logger.info(f"✓ Insights generados con IA: {len(insights)} insights")
                    
                    # Check si usó fallback
                    if insights.get('_generated_by') == 'fallback':
                        warnings.append("Insights generados sin IA (fallback)")
                        
                except Exception as e:
                    logger.error(f"  ❌ Error generando insights con IA: {e}")
                    logger.warning("  → Usando insights algorítmicos de fallback")
                    
                    # Generar insights sin IA (fallback robusto)
                    insights = self._generate_fallback_insights(metricas, duracion_dias)
                    
                    warnings.append(
                        f"Insights generados algorítmicamente (Claude API: {str(e)[:100]})"
                    )
            else:
                logger.info("PASO 7: Insights IA desactivados")
            
            # ═══════════════════════════════════════════════════════════════
            # PASO 8: COMPILAR PDF
            # ═══════════════════════════════════════════════════════════════
            
            # Agregar top 10 ingresos al contexto de métricas
            metricas['top_10_ingresos'] = top_10_ingresos
            
            logger.info("PASO 8: Compilando PDF")
            result = self.report_builder.build(
                metricas=metricas,
                charts_paths=charts_paths,
                insights=insights,
                template_name='reports/ejecutivo_master.html'
            )
            logger.info(f"✓ PDF generado: {result['filename']}")
            
            # ═══════════════════════════════════════════════════════════════
            # PASO 9: CLEANUP
            # ═══════════════════════════════════════════════════════════════
            
            logger.info("PASO 9: Cleanup de archivos temporales")
            self._cleanup()
            logger.info("✓ Cleanup completado")
            
            # ═══════════════════════════════════════════════════════════════
            # PASO 10: RETORNAR RESULTADO
            # ═══════════════════════════════════════════════════════════════
            
            result['warnings'] = warnings
            
            generation_time = (datetime.now() - start_time).total_seconds()
            result['generation_time_seconds'] = generation_time
            
            logger.info("═" * 70)
            logger.info(f"REPORTE COMPLETADO EN {generation_time:.2f}s")
            logger.info(f"PDF: {result['filename']} ({result['pages']} páginas, {result['size_kb']:.1f} KB)")
            logger.info("═" * 70)
            
            return result
            
        except Exception as e:
            logger.error(f"ERROR GENERANDO REPORTE: {e}")
            
            # Cleanup en caso de error
            self._cleanup()
            
            # Re-lanzar excepción
            raise
    
    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS PRIVADOS (helpers de orchestration)
    # ═══════════════════════════════════════════════════════════════
    
    def _generate_charts(self, metricas: Dict[str, Any], operaciones: list) -> Dict[str, str]:
        """
        Genera todos los gráficos necesarios usando helpers especializados.
        """
        self.temp_dir = tempfile.mkdtemp(prefix='report_charts_')
        logger.debug(f"Directorio temporal: {self.temp_dir}")
        
        charts_paths = {}
        
        try:
            # Generar cada tipo de chart con helper
            self._gen_waterfall(metricas, charts_paths)
            self._gen_donut_areas(metricas, charts_paths)
            self._gen_donut_localidades(metricas, charts_paths)
            self._gen_line_temporal(metricas, charts_paths)
            self._gen_bar_clientes(metricas, charts_paths)
            
            logger.info(f"✓ Total gráficos generados: {len(charts_paths)}")
        except Exception as e:
            logger.error(f"Error generando gráficos: {str(e)}", exc_info=True)
            # Retornar paths parciales o vacíos - NO fallar el reporte
        
        # ═══════════════════════════════════════════════════════════════
        # CONVERSIÓN DE PNG A BASE64 PARA EMBEBER EN HTML/PDF
        # ═══════════════════════════════════════════════════════════════
        
        logger.info("Convirtiendo gráficos PNG a base64 data URIs...")
        charts_base64 = {}
        
        for key, path in charts_paths.items():
            try:
                if path and Path(path).exists():
                    with open(path, "rb") as f:
                        encoded = base64.b64encode(f.read()).decode()
                        charts_base64[key] = f"data:image/png;base64,{encoded}"
                        file_size_kb = len(encoded) / 1024
                        logger.debug(f"✓ {key} convertido a base64 ({file_size_kb:.1f} KB)")
                else:
                    logger.warning(f"⚠️ Path no existe para {key}: {path}")
            except Exception as e:
                logger.error(f"❌ Error convirtiendo {key} a base64: {e}")
        
        logger.info(f"✓ Total gráficos convertidos a base64: {len(charts_base64)}/{len(charts_paths)}")
        
        return charts_base64
    
    def _gen_waterfall(self, metricas: Dict[str, Any], charts_paths: dict) -> None:
        """Genera waterfall chart de flujo de rentabilidad."""
        waterfall_data = {
            'labels': ['Ingresos', 'Gastos', 'Retiros', 'Distribuciones', 'Resultado'],
            'values': [
                float(metricas.get('ingresos_uyu', 0)),
                -float(metricas.get('gastos_uyu', 0)),
                -float(metricas.get('retiros_uyu', 0)),
                -float(metricas.get('distribuciones_uyu', 0)),
                float(metricas.get('resultado_neto_uyu', 0))
            ],
            'measures': ['absolute', 'relative', 'relative', 'relative', 'total']
        }
        path = ChartFactory.create_and_save(
            'waterfall', waterfall_data, f'{self.temp_dir}/waterfall.png',
            {'title': 'Flujo de Rentabilidad (UYU)'}
        )
        charts_paths['waterfall_chart_path'] = path
        logger.debug(f"✓ Waterfall generado: {path}")
    
    def _gen_donut_areas(self, metricas: Dict[str, Any], charts_paths: dict) -> None:
        """Genera donut chart de distribución por áreas."""
        dist_areas = metricas.get('porcentaje_ingresos_por_area', {})
        if not dist_areas:
            return
        try:
            path = ChartFactory.create_and_save(
                'donut', {'labels': list(dist_areas.keys()), 'values': list(dist_areas.values())},
                f'{self.temp_dir}/donut_areas.png', {'title': 'Distribución de Ingresos por Área'}
            )
            charts_paths['area_donut_chart_path'] = path
            logger.info(f"✅ Donut áreas generado: {path}")
        except Exception as e:
            logger.error(f"Error generando donut áreas: {e}")
    
    def _gen_donut_localidades(self, metricas: Dict[str, Any], charts_paths: dict) -> None:
        """Genera donut chart de distribución por localidades."""
        dist_loc = metricas.get('porcentaje_ingresos_por_localidad', {})
        if not dist_loc:
            return
        try:
            path = ChartFactory.create_and_save(
                'donut', {'labels': list(dist_loc.keys()), 'values': list(dist_loc.values())},
                f'{self.temp_dir}/donut_localidades.png', {'title': 'Distribución por Localidad'}
            )
            charts_paths['localidad_donut_chart_path'] = path
            logger.info(f"✅ Donut localidades generado: {path}")
        except Exception as e:
            logger.error(f"Error generando donut localidades: {e}")
    
    def _gen_line_temporal(self, metricas: Dict[str, Any], charts_paths: dict) -> None:
        """Genera line chart de evolución temporal."""
        ingresos_mes = metricas.get('ingresos_por_mes', [])
        gastos_mes = metricas.get('gastos_por_mes', [])
        meses = metricas.get('meses', [])
        
        if not (meses and len(meses) >= 3 and len(ingresos_mes) >= 3):
            logger.info(f"⚠️ Datos insuficientes para tendencia ({len(meses) if meses else 0} meses)")
            return
        
        try:
            utilidad_mes = [ingresos_mes[i] - gastos_mes[i] if i < len(gastos_mes) else ingresos_mes[i] 
                          for i in range(len(ingresos_mes))]
            meses_texto = "1 mes" if len(meses) == 1 else f"{len(meses)} meses"
            
            path = ChartFactory.create_and_save(
                'line',
                {'labels': meses, 'series': [
                    {'name': 'Ingresos', 'values': ingresos_mes, 'color': '#5B9BD5'},
                    {'name': 'Gastos', 'values': gastos_mes, 'color': '#E74C3C'},
                    {'name': 'Utilidad', 'values': utilidad_mes, 'color': '#70AD47'}
                ]},
                f'{self.temp_dir}/line_temporal.png', {'title': f'Evolución Temporal ({meses_texto})'}
            )
            charts_paths['line_temporal_chart_path'] = path
            logger.info(f"✅ Line chart temporal generado: {path}")
        except Exception as e:
            logger.warning(f"Error generando line temporal: {e}")
    
    def _gen_bar_clientes(self, metricas: Dict[str, Any], charts_paths: dict) -> None:
        """Genera bar chart de top 10 clientes."""
        top_clientes = metricas.get('top_clientes', [])
        if not top_clientes:
            return
        
        try:
            top_10 = top_clientes[:10]
            path = ChartFactory.create_and_save(
                'bar',
                {
                    'categories': [c.get('cliente', f'Cliente {i+1}') for i, c in enumerate(top_10)],
                    'series': [{'name': 'Facturación', 'values': [c.get('facturacion', 0) for c in top_10], 'color': '#5B9BD5'}]
                },
                f'{self.temp_dir}/bar_top_clientes.png',
                {'title': 'Top 10 Clientes por Facturación', 'orientation': 'h', 'sort_by_value': True}
            )
            charts_paths['bar_top_clientes_chart_path'] = path
            logger.info(f"✅ Bar chart Top 10 generado: {path}")
        except Exception as e:
            logger.warning(f"Error generando bar Top 10: {e}")
    
    def _cleanup(self) -> None:
        """
        Limpia archivos temporales.
        
        Elimina directorio temporal de charts después de generar PDF.
        """
        if self.temp_dir and Path(self.temp_dir).exists():
            try:
                shutil.rmtree(self.temp_dir)
                logger.debug(f"Directorio temporal eliminado: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"No se pudo eliminar directorio temporal: {e}")
        
        self.temp_dir = None
    
    def _generate_fallback_insights(
        self, 
        metricas: Dict[str, Any], 
        duracion_dias: int
    ) -> Dict[str, str]:
        """
        Genera insights algorítmicos cuando Claude falla.
        
        Args:
            metricas: Dict con métricas calculadas
            duracion_dias: Duración del período
            
        Returns:
            Dict con insights generados sin IA
        """
        from app.services.ai.fallback_generator import (
            generate_operativo_fallback,
            generate_estrategico_fallback
        )
        
        logger.info(f"  → Generando fallback para período de {duracion_dias} días")
        
        if duracion_dias <= 45:
            insights = generate_operativo_fallback(metricas)
            logger.info("  → Fallback operativo generado")
        else:
            insights = generate_estrategico_fallback(metricas)
            logger.info("  → Fallback estratégico generado")
        
        return insights
    
    def _is_period_comparable_yoy(self, fecha_inicio: date, fecha_fin: date) -> bool:
        """
        Verifica si el período es comparable YoY (mes/trimestre/año completo).
        
        Args:
            fecha_inicio: Fecha inicio del período
            fecha_fin: Fecha fin del período
            
        Returns:
            True si es mes completo, trimestre completo o año completo
        """
        from calendar import monthrange
        
        # Mes completo
        if fecha_inicio.day == 1:
            ultimo_dia = monthrange(fecha_fin.year, fecha_fin.month)[1]
            if fecha_fin.day == ultimo_dia and fecha_inicio.month == fecha_fin.month:
                return True
        
        # Trimestre completo (inicia en ene/abr/jul/oct y dura 3 meses)
        if fecha_inicio.day == 1 and fecha_inicio.month in [1, 4, 7, 10]:
            if fecha_fin.day in [31, 30] and (fecha_fin.month - fecha_inicio.month) == 2:
                return True
        
        # Año completo
        if fecha_inicio == date(fecha_inicio.year, 1, 1) and \
           fecha_fin == date(fecha_fin.year, 12, 31):
            return True
        
        return False
    
    def _is_period_comparable_qoq(self, fecha_inicio: date, fecha_fin: date) -> bool:
        """Verifica si el período es un trimestre completo"""
        if fecha_inicio.day == 1 and fecha_inicio.month in [1, 4, 7, 10]:
            if fecha_fin.day in [31, 30] and (fecha_fin.month - fecha_inicio.month) == 2:
                return True
        return False
    
    def _get_quarter_before(self, fecha_inicio: date, fecha_fin: date):
        """Calcula el trimestre anterior"""
        # Determinar trimestre actual
        if fecha_inicio.month == 1:
            # Q1 → Q4 año anterior
            return date(fecha_inicio.year - 1, 10, 1), date(fecha_inicio.year - 1, 12, 31)
        elif fecha_inicio.month == 4:
            # Q2 → Q1
            return date(fecha_inicio.year, 1, 1), date(fecha_inicio.year, 3, 31)
        elif fecha_inicio.month == 7:
            # Q3 → Q2
            return date(fecha_inicio.year, 4, 1), date(fecha_inicio.year, 6, 30)
        elif fecha_inicio.month == 10:
            # Q4 → Q3
            return date(fecha_inicio.year, 7, 1), date(fecha_inicio.year, 9, 30)
        
        return None, None

