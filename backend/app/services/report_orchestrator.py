"""
Report Orchestrator - MAESTRO del Sistema de Reportes

Coordina TODO el flujo de generación de reportes PDF.
NO calcula, solo ORQUESTA.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from sqlalchemy.orm import Session

from app.schemas.report.request import ReportRequest
from app.repositories.operations_repository import OperationsRepository
from app.services.validators.request_validator import validate_request
from app.services.validators.data_validator import validate_sufficient_data, validate_data_quality
from app.services.metrics.metrics_aggregator import MetricsAggregator
from app.services.charts.chart_factory import ChartFactory
from app.services.ai.insights_orchestrator import InsightsOrchestrator
from app.services.pdf.report_builder import ReportBuilder
from app.utils.date_resolver import resolve_period, get_comparison_period
from app.core.logger import get_logger
from app.core.exceptions import PDFGenerationError, InsufficientDataError

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
                historico_mensual = self.repo.get_ingresos_mensuales_historico(meses=12)
                logger.info(f"✓ Histórico mensual: {len(historico_mensual)} meses")
            
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
                historico_mensual=historico_mensual
            )
            
            metricas = aggregator.aggregate_all()
            logger.info(f"✓ Métricas calculadas: {len(metricas)} métricas")
            
            # ═══════════════════════════════════════════════════════════════
            # PASO 6: GENERAR GRÁFICOS
            # ═══════════════════════════════════════════════════════════════
            
            logger.info("PASO 6: Generando gráficos")
            charts_paths = self._generate_charts(metricas)
            logger.info(f"✓ Gráficos generados: {len(charts_paths)} charts")
            
            # ═══════════════════════════════════════════════════════════════
            # PASO 7: GENERAR INSIGHTS CON IA
            # ═══════════════════════════════════════════════════════════════
            
            insights = {}
            if request.options.incluir_insights_ia and self.insights_orchestrator:
                logger.info("PASO 7: Generando insights con IA")
                try:
                    duracion_dias = (fecha_fin - fecha_inicio).days + 1
                    insights = self.insights_orchestrator.generate_all(
                        metricas=metricas,
                        duracion_dias=duracion_dias,
                        tiene_comparacion=bool(operaciones_comparacion),
                        metricas_comparacion=None,  # TODO: Si necesario
                        timeout=30,
                        usar_ia=True
                    )
                    logger.info("✓ Insights generados")
                    
                    # Check si usó fallback
                    if insights.get('_generated_by') == 'fallback':
                        warnings.append("Insights generados sin IA (fallback)")
                        
                except Exception as e:
                    logger.warning(f"Error generando insights: {e}")
                    warnings.append(f"Insights no disponibles: {str(e)}")
            else:
                logger.info("PASO 7: Insights IA desactivados")
            
            # ═══════════════════════════════════════════════════════════════
            # PASO 8: COMPILAR PDF
            # ═══════════════════════════════════════════════════════════════
            
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
    
    def _generate_charts(self, metricas: Dict[str, Any]) -> Dict[str, str]:
        """
        Genera todos los gráficos necesarios.
        
        Args:
            metricas: Métricas calculadas
            
        Returns:
            Dict con paths a gráficos generados
        """
        # Crear directorio temporal
        self.temp_dir = tempfile.mkdtemp(prefix='report_charts_')
        logger.debug(f"Directorio temporal: {self.temp_dir}")
        
        charts_paths = {}
        
        # TODO: Implementar generación de cada tipo de gráfico
        # Por ahora retornar dict vacío (templates manejan ausencia)
        
        # Ejemplo de cómo se generarían:
        # factory = ChartFactory()
        # 
        # 1. Waterfall chart
        # data = self._prepare_waterfall_data(metricas)
        # path = factory.create_and_save('waterfall', data, f'{self.temp_dir}/waterfall.png')
        # charts_paths['waterfall_chart_path'] = path
        
        logger.debug(f"Charts generados: {len(charts_paths)}")
        
        return charts_paths
    
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

