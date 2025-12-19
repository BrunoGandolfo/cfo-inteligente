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

from sqlalchemy.orm import Session

from app.schemas.report.request import ReportRequest
from app.repositories.operations_repository import OperationsRepository
from app.models import TipoOperacion
from app.services.validators.request_validator import validate_request
from app.services.validators.data_validator import validate_sufficient_data, validate_data_quality
from app.services.metrics.metrics_aggregator import MetricsAggregator
from app.services.report_chart_generator import ReportChartGenerator
from app.services.ai.insights_orchestrator import InsightsOrchestrator
from app.services.pdf.report_builder import ReportBuilder
from app.utils.date_resolver import resolve_period, get_comparison_period
from app.core.logger import get_logger
from app.services.period_comparator import (
    is_period_comparable_yoy,
    is_period_comparable_qoq,
    get_quarter_before
)

logger = get_logger(__name__)


class ReportOrchestrator:
    """
    MAESTRO: Coordina TODA la generación de reportes PDF.
    
    Flujo: Validar → Resolver fechas → Obtener datos → Calcular métricas 
           → Generar gráficos → Insights IA → Compilar PDF → Cleanup
    
    Patrón: Facade + Orchestration (solo coordina, no implementa lógica).
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
        
        # Generador de charts (composición)
        self.chart_generator = ReportChartGenerator()
        
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
            
            if is_period_comparable_yoy(fecha_inicio, fecha_fin):
                try:
                    fecha_inicio_yoy = fecha_inicio.replace(year=fecha_inicio.year - 1)
                    fecha_fin_yoy = fecha_fin.replace(year=fecha_fin.year - 1)
                    
                    operaciones_yoy = self.repo.get_by_period(fecha_inicio_yoy, fecha_fin_yoy)
                    logger.info(f"✓ Operaciones YoY: {len(operaciones_yoy)}")
                except ValueError:
                    logger.warning("No se pudo calcular período YoY (edge case fechas)")
            
            if is_period_comparable_qoq(fecha_inicio, fecha_fin):
                fecha_inicio_qoq, fecha_fin_qoq = get_quarter_before(fecha_inicio, fecha_fin)
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
            charts_paths = self.chart_generator.generate_all(metricas)
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
            self.chart_generator.cleanup()
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
            self.chart_generator.cleanup()
            
            # Re-lanzar excepción
            raise
    
    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS PRIVADOS (helpers de orchestration)
    # ═══════════════════════════════════════════════════════════════
    
    def _generate_fallback_insights(
        self, 
        metricas: Dict[str, Any], 
        duracion_dias: int
    ) -> Dict[str, str]:
        """Genera insights algorítmicos cuando Claude falla."""
        from app.services.ai.fallback_generator import (
            generate_operativo_fallback,
            generate_estrategico_fallback
        )
        
        logger.info(f"  → Generando fallback para período de {duracion_dias} días")
        
        if duracion_dias <= 45:
            return generate_operativo_fallback(metricas)
        return generate_estrategico_fallback(metricas)
    

