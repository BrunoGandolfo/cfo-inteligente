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
import base64
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
    
    def _generate_charts(self, metricas: Dict[str, Any], operaciones: list) -> Dict[str, str]:
        """
        Genera todos los gráficos necesarios.
        
        Args:
            metricas: Métricas calculadas
            operaciones: Lista de operaciones (para análisis adicional)
            
        Returns:
            Dict con paths a gráficos generados
        """
        # Crear directorio temporal
        self.temp_dir = tempfile.mkdtemp(prefix='report_charts_')
        logger.debug(f"Directorio temporal: {self.temp_dir}")
        
        charts_paths = {}
        
        try:
            # ═══════════════════════════════════════════════════════════════
            # 1. WATERFALL CHART - Flujo de Rentabilidad
            # ═══════════════════════════════════════════════════════════════
            
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
            
            waterfall_path = ChartFactory.create_and_save(
                'waterfall',
                waterfall_data,
                f'{self.temp_dir}/waterfall.png',
                {'title': 'Flujo de Rentabilidad (UYU)', 'height': 400}
            )
            charts_paths['waterfall_chart_path'] = waterfall_path
            logger.debug(f"✓ Waterfall generado: {waterfall_path}")
            
            # ═══════════════════════════════════════════════════════════════
            # 2. DONUT CHART - Distribución por Áreas
            # ═══════════════════════════════════════════════════════════════
            
            dist_areas = metricas.get('porcentaje_ingresos_por_area', {})
            logger.info(f"🔍 dist_areas obtenido: {dist_areas}")
            logger.info(f"🔍 Tipo: {type(dist_areas)}, Len: {len(dist_areas)}, Bool: {bool(dist_areas)}")
            
            if dist_areas:
                logger.info("🔍 Entrando a generar donut áreas...")
                try:
                    donut_areas_data = {
                        'labels': list(dist_areas.keys()),
                        'values': list(dist_areas.values())
                    }
                    logger.info(f"🔍 donut_areas_data preparado: labels={donut_areas_data['labels']}, values={donut_areas_data['values']}")
                    
                    donut_areas_path = ChartFactory.create_and_save(
                        'donut',
                        donut_areas_data,
                        f'{self.temp_dir}/donut_areas.png',
                        {'title': 'Distribución de Ingresos por Área', 'height': 350}
                    )
                    charts_paths['area_donut_chart_path'] = donut_areas_path
                    logger.info(f"✅ Donut áreas generado exitosamente: {donut_areas_path}")
                except Exception as e:
                    logger.error(f"❌ ERROR generando donut áreas: {type(e).__name__}: {str(e)}", exc_info=True)
            else:
                logger.warning("⚠️ dist_areas es falsy, saltando donut áreas")
            
            # ═══════════════════════════════════════════════════════════════
            # 3. DONUT CHART - Distribución por Localidades
            # ═══════════════════════════════════════════════════════════════
            
            dist_localidades = metricas.get('porcentaje_ingresos_por_localidad', {})
            logger.info(f"🔍 dist_localidades obtenido: {dist_localidades}")
            logger.info(f"🔍 Tipo: {type(dist_localidades)}, Len: {len(dist_localidades)}, Bool: {bool(dist_localidades)}")
            
            if dist_localidades:
                logger.info("🔍 Entrando a generar donut localidades...")
                try:
                    donut_loc_data = {
                        'labels': list(dist_localidades.keys()),
                        'values': list(dist_localidades.values())
                    }
                    logger.info(f"🔍 donut_loc_data preparado: labels={donut_loc_data['labels']}, values={donut_loc_data['values']}")
                    
                    donut_loc_path = ChartFactory.create_and_save(
                        'donut',
                        donut_loc_data,
                        f'{self.temp_dir}/donut_localidades.png',
                        {'title': 'Distribución por Localidad', 'height': 350}
                    )
                    charts_paths['localidad_donut_chart_path'] = donut_loc_path
                    logger.info(f"✅ Donut localidades generado exitosamente: {donut_loc_path}")
                except Exception as e:
                    logger.error(f"❌ ERROR generando donut localidades: {type(e).__name__}: {str(e)}", exc_info=True)
            else:
                logger.warning("⚠️ dist_localidades es falsy, saltando donut localidades")
            
            # ═══════════════════════════════════════════════════════════════
            # 4. LINE CHART - Evolución Temporal (ingresos/gastos/utilidad)
            # ═══════════════════════════════════════════════════════════════
            
            # Verificar si existen datos temporales
            ingresos_mes = metricas.get('ingresos_por_mes', [])
            gastos_mes = metricas.get('gastos_por_mes', [])
            meses = metricas.get('meses', [])
            
            if meses and len(meses) > 0 and len(ingresos_mes) > 0:
                logger.info("🔍 Generando line chart temporal...")
                try:
                    # Calcular utilidad por mes
                    utilidad_mes = []
                    for i in range(len(ingresos_mes)):
                        ing = ingresos_mes[i] if i < len(ingresos_mes) else 0
                        gas = gastos_mes[i] if i < len(gastos_mes) else 0
                        utilidad_mes.append(ing - gas)
                    
                    line_temporal_path = ChartFactory.create_and_save(
                        'line',
                        {
                            'labels': meses,  # API correcta: 'labels' en vez de 'x'
                            'series': [       # API correcta: 'series' en vez de 'y_series'
                                {'name': 'Ingresos', 'values': ingresos_mes, 'color': '#3B82F6'},
                                {'name': 'Gastos', 'values': gastos_mes, 'color': '#EF4444'},
                                {'name': 'Utilidad', 'values': utilidad_mes, 'color': '#10B981'}
                            ]
                        },
                        f'{self.temp_dir}/line_temporal.png',
                        {'title': 'Evolución Temporal (3 meses)', 'height': 400}
                    )
                    charts_paths['line_temporal_chart_path'] = line_temporal_path
                    logger.info(f"✅ Line chart temporal generado: {line_temporal_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Error generando line temporal: {e}")
            else:
                logger.info("⚠️ No hay datos temporales, saltando line chart")
            
            # ═══════════════════════════════════════════════════════════════
            # 5. BAR CHART - Top 10 Clientes por Facturación
            # ═══════════════════════════════════════════════════════════════
            
            top_clientes = metricas.get('top_clientes', [])
            
            if top_clientes and len(top_clientes) > 0:
                logger.info("🔍 Generando bar chart Top 10 clientes...")
                try:
                    # Top 10 clientes
                    top_10 = top_clientes[:10]
                    
                    bar_clientes_path = ChartFactory.create_and_save(
                        'bar',
                        {
                            'categories': [c.get('cliente', f'Cliente {i+1}') for i, c in enumerate(top_10)],  # API correcta: 'categories'
                            'series': [  # API correcta: 'series' con estructura de lista
                                {
                                    'name': 'Facturación',
                                    'values': [c.get('facturacion', 0) for c in top_10],  # Key correcta: 'facturacion'
                                    'color': '#3B82F6'
                                }
                            ]
                        },
                        f'{self.temp_dir}/bar_top_clientes.png',
                        {'title': 'Top 10 Clientes por Facturación', 'height': 500}
                    )
                    charts_paths['bar_top_clientes_chart_path'] = bar_clientes_path
                    logger.info(f"✅ Bar chart Top 10 generado: {bar_clientes_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Error generando bar Top 10: {e}")
            else:
                logger.info("⚠️ No hay top_clientes, saltando bar chart")
            
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

