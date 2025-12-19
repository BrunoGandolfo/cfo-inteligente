"""
Report Builder - FACADE para generación de reportes PDF

Coordina: Template Rendering → HTML → PDF → Metadata
Implementa Facade Pattern.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from decimal import Decimal
import base64

from app.services.pdf.template_renderer import TemplateRenderer
from app.services.pdf.pdf_compiler_playwright import PlaywrightPDFCompiler
from app.core.logger import get_logger
from app.core.exceptions import PDFGenerationError
from app.utils.narrative_builder import (
    build_revenue_commentary,
    build_expense_commentary,
    build_margin_commentary,
    build_area_commentary,
    build_executive_summary
)
from app.services.analytics.variance_detector import VarianceDetector
from app.services.pdf.report_data_formatters import (
    prepare_summary_metrics,
    prepare_kpis,
    prepare_distribution,
    prepare_gastos_por_area,
    prepare_metadata,
    build_anterior_proxy
)

logger = get_logger(__name__)


class ReportBuilder:
    """
    FACADE: Coordina generación completa de reportes PDF.
    
    RESPONSABILIDAD: Orquestar flujo Template → HTML → PDF.
    PATRÓN: Facade Pattern + Composition.
    
    Flujo:
    1. Preparar contexto con métricas + charts + insights
    2. Renderizar template HTML (Jinja2)
    3. Compilar HTML a PDF (WeasyPrint)
    4. Agregar metadata
    5. Retornar path + metadata del PDF
    
    Principios aplicados:
    - Single Responsibility: Solo coordina, NO implementa
    - Composition: Compone Renderer + Compiler
    - Dependency Injection: Puede inyectar renderer/compiler custom
    
    Ejemplo:
        >>> builder = ReportBuilder()
        >>> result = builder.build(
        ...     metricas=metricas_dict,
        ...     charts_paths=charts_dict,
        ...     insights=insights_dict
        ... )
        >>> print(result['pdf_path'])
        'output/reports/Reporte_CFO_Oct2025.pdf'
    """
    
    def __init__(
        self,
        templates_dir: Optional[str] = None,
        output_dir: Optional[str] = None
    ):
        """
        Constructor.
        
        Args:
            templates_dir: Directorio de templates (default: backend/app/templates)
            output_dir: Directorio de output (default: backend/output/reports)
        """
        # Directorios
        self.templates_dir = templates_dir or self._get_default_templates_dir()
        self.output_dir = output_dir or self._get_default_output_dir()
        
        # Crear output_dir si no existe
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        # Componentes (Composition)
        self.renderer = TemplateRenderer(self.templates_dir)
        self.compiler = PlaywrightPDFCompiler()
        
        logger.info(f"ReportBuilder inicializado con Playwright: templates={self.templates_dir}, output={self.output_dir}")
    
    def build(
        self,
        metricas: Dict[str, Any],
        charts_paths: Optional[Dict[str, str]] = None,
        insights: Optional[Dict[str, str]] = None,
        template_name: str = 'reports/ejecutivo_master.html',
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Construye reporte PDF completo.
        
        Args:
            metricas: Dict con métricas calculadas (de MetricsAggregator)
            charts_paths: Dict con paths a gráficos generados (opcional)
            insights: Dict con insights de IA (opcional)
            template_name: Nombre del template a usar
            filename: Nombre del archivo PDF (si None, autogenera)
            
        Returns:
            Dict con resultado:
            {
                'pdf_path': str,
                'filename': str,
                'size_kb': float,
                'pages': int,
                'generation_time_seconds': float,
                'metadata': dict
            }
            
        Raises:
            PDFGenerationError: Si falla generación
        """
        start_time = datetime.now()
        
        logger.info("Iniciando construcción de reporte PDF")
        
        try:
            # ═══════════════════════════════════════════════════════════════
            # PASO 0: CONVERTIR DECIMALS A FLOAT
            # ═══════════════════════════════════════════════════════════════
            
            metricas = self._convert_decimals_to_float(metricas)
            
            # ═══════════════════════════════════════════════════════════════
            # PASO 1: DETECTAR VARIANZAS (si hay comparación)
            # ═══════════════════════════════════════════════════════════════
            
            variances_criticas = []
            if metricas.get('tiene_comparacion'):
                logger.info("Detectando variaciones significativas...")
                # Necesitamos recalcular métricas del período anterior
                # Por ahora, usar None (mejora futura: recibir como parámetro)
                # La detección se hará solo con las variaciones ya calculadas
                detector = VarianceDetector(threshold_percent=10.0, threshold_margin_pp=5.0)
                # Como no tenemos metricas_anterior completas, crear dict mínimo
                metricas_anterior_proxy = build_anterior_proxy(metricas)
                if metricas_anterior_proxy:
                    variances_criticas = detector.detect_variances(metricas, metricas_anterior_proxy)
                    logger.info(f"✓ Variaciones detectadas: {len(variances_criticas)}")
            
            # ═══════════════════════════════════════════════════════════════
            # PASO 2: PREPARAR CONTEXTO
            # ═══════════════════════════════════════════════════════════════
            
            context = self._prepare_context(metricas, charts_paths, insights, variances_criticas)
            
            logger.debug(f"Contexto preparado: {len(context)} variables")
            
            # ═══════════════════════════════════════════════════════════════
            # PASO 2: RENDERIZAR HTML
            # ═══════════════════════════════════════════════════════════════
            
            html_content = self.renderer.render(template_name, context)
            
            logger.info(f"HTML renderizado: {len(html_content)} caracteres")
            
            # ═══════════════════════════════════════════════════════════════
            # PASO 3: GENERAR NOMBRE DE ARCHIVO
            # ═══════════════════════════════════════════════════════════════
            
            if not filename:
                filename = self._generate_filename(metricas)
            
            output_path = str(Path(self.output_dir) / filename)
            
            # ═══════════════════════════════════════════════════════════════
            # PASO 4: COMPILAR PDF
            # ═══════════════════════════════════════════════════════════════
            
            metadata = prepare_metadata(metricas)
            
            pdf_path = self.compiler.compile(
                html_content=html_content,
                output_path=output_path,
                metadata=metadata
            )
            
            # ═══════════════════════════════════════════════════════════════
            # PASO 5: OBTENER INFO DEL PDF
            # ═══════════════════════════════════════════════════════════════
            
            pdf_info = self.compiler.get_pdf_info(pdf_path)
            
            # ═══════════════════════════════════════════════════════════════
            # PASO 6: PREPARAR RESULTADO
            # ═══════════════════════════════════════════════════════════════
            
            generation_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                'pdf_path': pdf_path,
                'filename': filename,
                'size_kb': pdf_info.get('size_kb', 0),
                'size_mb': pdf_info.get('size_mb', 0),
                'pages': pdf_info.get('pages', 0),
                'generation_time_seconds': generation_time,
                'metadata': metadata,
                'generated_at': datetime.now()
            }
            
            logger.info(
                f"Reporte PDF completado: {filename} "
                f"({pdf_info.get('pages', 0)} páginas, "
                f"{pdf_info.get('size_kb', 0):.1f} KB, "
                f"{generation_time:.2f}s)"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error construyendo reporte: {e}")
            raise PDFGenerationError(f"Error construyendo reporte: {str(e)}")
    
    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS PRIVADOS (helpers internos)
    # ═══════════════════════════════════════════════════════════════
    
    def _prepare_context(
        self,
        metricas: Dict[str, Any],
        charts_paths: Optional[Dict[str, str]],
        insights: Optional[Dict[str, str]],
        variances: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Prepara contexto completo para template.
        
        Args:
            metricas: Métricas calculadas
            charts_paths: Paths a gráficos
            insights: Insights de IA
            
        Returns:
            Dict con contexto completo para Jinja2
        """
        # Logo en base64
        logo_path = Path(__file__).parent.parent.parent / "static" / "logo-conexion.png"
        if logo_path.exists():
            with open(logo_path, "rb") as f:
                logo_base64 = base64.b64encode(f.read()).decode()
        else:
            logo_base64 = ""
            logger.warning(f"Logo no encontrado en: {logo_path}")
        
        context = {
            # Metadata general
            'generated_at': datetime.now(),
            'empresa_nombre': 'Conexión Consultora',
            'report_title': 'Reporte Ejecutivo CFO',
            
            # Período
            'period_label': metricas.get('period_label', 'Período'),
            'fecha_inicio': metricas.get('fecha_inicio'),
            'fecha_fin': metricas.get('fecha_fin'),
            'duracion_dias': metricas.get('duracion_dias', 0),
            
            # Comparación
            'tiene_comparacion': metricas.get('tiene_comparacion', False),
            'variacion_mom_ingresos': metricas.get('variacion_mom_ingresos'),
            'variacion_mom_gastos': metricas.get('variacion_mom_gastos'),
            'variacion_mom_rentabilidad': metricas.get('variacion_mom_rentabilidad'),
            
            # Logo
            'logo_base64': logo_base64,
            
            # Métricas (spread todas las métricas)
            **metricas,
            
            # Charts
            **(charts_paths or {}),
            
            # Insights
            'insights': insights or {},
            
            # Commentary narrativo
            'revenue_commentary': build_revenue_commentary(metricas),
            'expense_commentary': build_expense_commentary(metricas),
            'margin_commentary': build_margin_commentary(metricas),
            'area_commentary': build_area_commentary(metricas),
            'narrativa_resumen': build_executive_summary(metricas),
            
            # Variance analysis
            'variances_criticas': variances or [],
            'threshold_percent': 10.0,  # Para mostrar en template
            
            # Datos preparados para componentes
            'metrics': prepare_summary_metrics(metricas),
            'kpis': prepare_kpis(metricas),
            'ingresos_por_area': prepare_distribution(
                metricas.get('porcentaje_ingresos_por_area', {}),
                metricas.get('ingresos_uyu', 0)
            ),
            'ingresos_por_localidad': prepare_distribution(
                metricas.get('porcentaje_ingresos_por_localidad', {}),
                metricas.get('ingresos_uyu', 0)
            ),
            'gastos_por_area': prepare_gastos_por_area(metricas),
            
            # Análisis de localidades y clientes (nuevos)
            'utilidad_neta_por_localidad': metricas.get('utilidad_neta_por_localidad', {}),
            'distribuciones_por_localidad': metricas.get('distribuciones_por_localidad', {}),
            'ratio_distribucion_utilidad': metricas.get('ratio_distribucion_utilidad', {}),
            'top_clientes': metricas.get('top_clientes', []),
            'analisis_pareto': metricas.get('analisis_pareto', {}),
            'indice_hhi': metricas.get('indice_hhi', {})
        }
        
        return context
    
    def _generate_filename(self, metricas: Dict[str, Any]) -> str:
        """Genera nombre de archivo automático."""
        period_label = metricas.get('period_label', 'Periodo')
        # Sanitizar period_label para filename
        safe_period = period_label.replace(' ', '_').replace('/', '-')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return f"Reporte_CFO_{safe_period}_{timestamp}.pdf"
    
    def _get_default_templates_dir(self) -> str:
        """Retorna directorio default de templates."""
        # Asumir estructura: backend/app/services/pdf/ → backend/app/templates/
        current_file = Path(__file__)
        backend_dir = current_file.parent.parent.parent  # services/pdf/ → app/ → backend/
        templates_dir = backend_dir / 'templates'
        
        return str(templates_dir)
    
    def _get_default_output_dir(self) -> str:
        """Retorna directorio default de output."""
        current_file = Path(__file__)
        backend_dir = current_file.parent.parent.parent
        output_dir = backend_dir / 'output' / 'reports'
        
        return str(output_dir)
    
    def _convert_decimals_to_float(self, obj: Any) -> Any:
        """
        Convierte recursivamente Decimals a float.
        
        Jinja2/WeasyPrint no manejan bien Decimal.
        
        Args:
            obj: Objeto a convertir (dict, list, Decimal, etc)
            
        Returns:
            Objeto con Decimals convertidos a float
        """
        if isinstance(obj, dict):
            return {k: self._convert_decimals_to_float(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_decimals_to_float(item) for item in obj]
        elif isinstance(obj, Decimal):
            return float(obj)
        return obj

