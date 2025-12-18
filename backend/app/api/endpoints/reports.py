"""
Reports Endpoints - API para generación de reportes

Define endpoints REST para sistema de reportes PDF.

Autor: Sistema CFO Inteligente
Fecha: Noviembre 2025
"""

from datetime import datetime, date
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.schemas.report.request import ReportRequest
from app.schemas.report.response import ReportResponse, ReportMetadata
from app.services.report_orchestrator import ReportOrchestrator
from app.services.ai.insights_orchestrator import InsightsOrchestrator
from app.services.pdf.report_builder import ReportBuilder
from app.core.dependencies import (
    get_db,
    get_chart_config,
    get_insights_orchestrator,
    get_report_builder
)
from app.core.logger import get_logger
from app.core.security import get_current_user
from app.core.exceptions import InvalidDateRangeError, InsufficientDataError, PDFGenerationError
from app.models import Usuario

logger = get_logger(__name__)

router = APIRouter(tags=["reports"])


# ═══════════════════════════════════════════════════════════════
# SCHEMAS PARA P&L LOCALIDAD
# ═══════════════════════════════════════════════════════════════

class PnLLocalidadRequest(BaseModel):
    """Request para reporte P&L por Localidad."""
    fecha_inicio: date = Field(..., description="Fecha inicio del período (YYYY-MM-DD)")
    fecha_fin: date = Field(..., description="Fecha fin del período (YYYY-MM-DD)")
    comparar_con_anterior: bool = Field(default=True, description="Incluir comparación con período anterior")
    incluir_narrativas_ia: bool = Field(default=True, description="Generar narrativas con Claude")
    
    class Config:
        json_schema_extra = {
            "example": {
                "fecha_inicio": "2025-11-01",
                "fecha_fin": "2025-11-30",
                "comparar_con_anterior": True,
                "incluir_narrativas_ia": True
            }
        }


# ═══════════════════════════════════════════════════════════════
# ENDPOINT PRINCIPAL: GENERAR REPORTE PDF DINÁMICO
# ═══════════════════════════════════════════════════════════════

@router.post(
    "/pdf/dinamico",
    response_class=FileResponse,
    summary="Generar Reporte PDF Dinámico",
    description="""
    Genera reporte ejecutivo CFO en PDF con:
    - 29+ métricas calculadas automáticamente
    - 7 tipos de gráficos profesionales
    - Insights generados por Claude Sonnet 4.5
    - Comparación con período anterior (opcional)
    - Proyecciones con regresión lineal (opcional)
    
    Formato: 10 páginas ejecutivas en A4, diseño moderno 2024.
    """
)
async def generate_dynamic_report(
    request: ReportRequest,
    db: Session = Depends(get_db),
    insights_orch: InsightsOrchestrator = Depends(get_insights_orchestrator),
    report_builder: ReportBuilder = Depends(get_report_builder),
    current_user: Usuario = Depends(get_current_user)
) -> FileResponse:
    """
    Genera reporte PDF dinámico.
    
    RESPONSABILIDAD: Solo HTTP (validar, inyectar deps, retornar).
    NO implementa lógica de negocio.
    
    Args:
        request: ReportRequest con configuración
        db: Session inyectada por Depends
        insights_orch: InsightsOrchestrator inyectado
        report_builder: ReportBuilder inyectado
        
    Returns:
        FileResponse con PDF generado
        
    Raises:
        HTTPException 400: Si request inválido
        HTTPException 404: Si no hay suficientes datos
        HTTPException 500: Si falla generación
    """
    logger.info(f"Request recibido: POST /api/reports/pdf/dinamico")
    logger.debug(f"Period: {request.period.tipo}, Options: {request.options.dict()}")
    
    try:
        # Obtener configuración de charts según paleta
        chart_config = get_chart_config(paleta=request.options.paleta)
        
        # Crear orchestrator con dependencias inyectadas
        orchestrator = ReportOrchestrator(
            db=db,
            chart_config=chart_config,
            insights_orchestrator=insights_orch,
            report_builder=report_builder
        )
        
        # Delegar generación al orchestrator
        result = orchestrator.generate(request)
        
        # Log resultado
        logger.info(
            f"Reporte generado: {result['filename']} "
            f"({result['pages']} páginas, {result['size_kb']:.1f} KB, "
            f"{result['generation_time_seconds']:.2f}s)"
        )
        
        # Retornar PDF como FileResponse
        return FileResponse(
            path=result['pdf_path'],
            media_type='application/pdf',
            filename=result['filename'],
            headers={
                'X-Report-Pages': str(result['pages']),
                'X-Report-Size-KB': f"{result['size_kb']:.1f}",
                'X-Generation-Time': f"{result['generation_time_seconds']:.2f}",
                'X-Warnings': '; '.join(result.get('warnings', []))
            }
        )
        
    except InvalidDateRangeError as e:
        logger.warning(f"Request inválido: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.detail if hasattr(e, 'detail') else str(e)
        )
    
    except InsufficientDataError as e:
        logger.warning(f"Datos insuficientes: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail if hasattr(e, 'detail') else str(e)
        )
    
    except PDFGenerationError as e:
        logger.error(f"Error generando PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.detail if hasattr(e, 'detail') else str(e)
        )
    
    except Exception as e:
        logger.error(f"Error inesperado: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando reporte: {str(e)}"
        )


# ═══════════════════════════════════════════════════════════════
# ENDPOINT: METADATA ONLY (sin generar PDF)
# ═══════════════════════════════════════════════════════════════

@router.post(
    "/preview",
    response_model=ReportResponse,
    summary="Preview de Reporte",
    description="""
    Retorna metadata de lo que se generaría SIN generar el PDF.
    Útil para preview en frontend antes de generar.
    """
)
async def preview_report(
    request: ReportRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
) -> ReportResponse:
    """
    Preview de reporte sin generar PDF.
    
    Calcula métricas y retorna metadata.
    """
    logger.info("Request recibido: POST /api/reports/preview")
    
    try:
        from app.services.validators.request_validator import validate_request
        from app.utils.date_resolver import resolve_period
        from app.repositories.operations_repository import OperationsRepository
        from app.services.validators.data_validator import validate_sufficient_data
        
        # Validar request
        validate_request(request)
        
        # Resolver fechas
        fecha_inicio, fecha_fin = resolve_period(
            tipo=request.period.tipo,
            fecha_inicio_custom=request.period.fecha_inicio,
            fecha_fin_custom=request.period.fecha_fin
        )
        
        # Obtener operaciones
        repo = OperationsRepository(db)
        operaciones = repo.get_by_period(fecha_inicio, fecha_fin)
        
        # Validar suficientes datos
        validate_sufficient_data(operaciones, minimo_requerido=20)
        
        # Preparar metadata (sin generar PDF)
        from app.utils.date_resolver import get_period_label
        
        metadata = ReportMetadata(
            filename=f"Reporte_CFO_{get_period_label(fecha_inicio, fecha_fin)}.pdf",
            size_kb=0.0,  # No generado aún
            pages=10,  # Estimado
            generation_time_seconds=0.0,
            period_label=get_period_label(fecha_inicio, fecha_fin),
            fecha_inicio=fecha_inicio.isoformat(),
            fecha_fin=fecha_fin.isoformat(),
            generated_at=datetime.now(),
            has_comparison=bool(request.comparison and request.comparison.activo),
            has_projections=request.options.incluir_proyecciones,
            has_ai_insights=request.options.incluir_insights_ia
        )
        
        return ReportResponse(
            success=True,
            metadata=metadata,
            warnings=None
        )
        
    except Exception as e:
        logger.error(f"Error en preview: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ═══════════════════════════════════════════════════════════════
# ENDPOINT: HEALTH CHECK (PÚBLICO)
# ═══════════════════════════════════════════════════════════════

@router.get(
    "/health",
    summary="Health Check",
    description="Verifica que el sistema de reportes esté operativo"
)
async def health_check() -> dict:
    """
    Health check del sistema de reportes.
    
    Verifica:
    - Database connection
    - Templates directory
    - Anthropic API key configurada
    """
    from app.core.dependencies import check_dependencies
    
    deps_status = check_dependencies()
    
    all_ok = all(deps_status.values())
    
    return {
        "status": "healthy" if all_ok else "degraded",
        "service": "reports",
        "dependencies": deps_status,
        "version": "1.0.0"
    }


# ═══════════════════════════════════════════════════════════════
# ENDPOINT: P&L POR LOCALIDAD
# ═══════════════════════════════════════════════════════════════

@router.post(
    "/pnl-localidad",
    response_class=StreamingResponse,
    summary="Generar Reporte P&L por Localidad",
    description="""
    Genera reporte PDF comparativo de P&L entre Montevideo y Mercedes.
    
    Incluye:
    - Resumen ejecutivo con KPIs consolidados
    - Detalle por localidad (ingresos, gastos, extracciones)
    - Narrativas generadas por Claude Sonnet 4.5 (opcional)
    - Comparación con período anterior (opcional)
    - Página de conclusiones y recomendaciones
    
    Formato: 4 páginas en A4, estilo Big 4 Consulting.
    """
)
async def generate_pnl_localidad_report(
    request: PnLLocalidadRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
) -> StreamingResponse:
    """
    Genera reporte P&L por Localidad en PDF.
    
    Args:
        request: PnLLocalidadRequest con fechas y opciones
        db: Session inyectada por Depends
        
    Returns:
        StreamingResponse con PDF generado
        
    Raises:
        HTTPException 400: Si fechas inválidas
        HTTPException 500: Si falla generación
    """
    logger.info(f"Request: POST /api/reports/pnl-localidad [{request.fecha_inicio} - {request.fecha_fin}]")
    
    try:
        # Validar rango de fechas
        if request.fecha_fin < request.fecha_inicio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="fecha_fin debe ser mayor o igual a fecha_inicio"
            )
        
        # Generar datos con PnLLocalidadGenerator
        from app.services.report_data.generators.pnl_localidad_generator import PnLLocalidadGenerator
        
        generator = PnLLocalidadGenerator(db)
        datos = generator.generate(
            fecha_inicio=request.fecha_inicio,
            fecha_fin=request.fecha_fin,
            comparar_con_anterior=request.comparar_con_anterior,
            incluir_narrativas=request.incluir_narrativas_ia
        )
        
        # Generar PDF con WeasyPrint
        from app.services.pdf.weasyprint_generator import PDFGenerator
        from pathlib import Path
        
        templates_dir = Path(__file__).parent.parent.parent / "templates" / "reports_big4"
        pdf_gen = PDFGenerator(templates_dir=str(templates_dir))
        pdf_bytes = pdf_gen.generar_pdf_desde_template(
            template_name="reports/pnl_localidad.html",
            datos=datos
        )
        
        # Generar nombre de archivo
        periodo = datos['metadata']['periodo_label'].replace(' ', '_').replace('/', '-')
        filename = f"PnL_Localidad_{periodo}.pdf"
        
        logger.info(f"PDF generado: {filename} ({len(pdf_bytes):,} bytes)")
        
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Report-Period": datos['metadata']['periodo_label'],
                "X-Has-Narrativas": str(request.incluir_narrativas_ia)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generando P&L Localidad: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando reporte: {str(e)}"
        )
