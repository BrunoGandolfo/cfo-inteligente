"""
Reports API - Endpoints para generación de reportes PDF

Integra todas las capas del sistema de reportes:
- Agregación de datos
- Generación de gráficos
- Insights con IA
- Generación de PDF

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import date
from pathlib import Path
import tempfile
import os

from app.core.database import get_db
from app.core.logger import get_logger
from app.services.report_data import MonthlyAggregator
from app.services.charts import ChartFactory
from app.services.insights import (
    InsightContextBuilder,
    InsightGenerator,
    InsightFormatter
)
from app.services.pdf import PDFGenerator, AssetManager

logger = get_logger(__name__)

router = APIRouter()


@router.post("/generate/monthly")
def generar_reporte_mensual(
    mes: int,
    anio: int,
    db: Session = Depends(get_db)
):
    """
    Genera reporte PDF mensual completo con insights de IA.
    
    Args:
        mes: Número de mes (1-12)
        anio: Año (ej: 2025)
        
    Returns:
        FileResponse con PDF generado
    """
    logger.info(f"=== GENERANDO REPORTE MENSUAL: {mes}/{anio} ===")
    
    try:
        # PASO 1: Validar fechas
        from calendar import monthrange
        
        if not (1 <= mes <= 12):
            raise HTTPException(status_code=400, detail=f"Mes inválido: {mes}")
        
        start_date = date(anio, mes, 1)
        ultimo_dia = monthrange(anio, mes)[1]
        end_date = date(anio, mes, ultimo_dia)
        
        logger.info(f"Período: {start_date} a {end_date}")
        
        # PASO 2: Agregar datos con MonthlyAggregator
        logger.info("Agregando datos financieros...")
        aggregator = MonthlyAggregator(db)
        data = aggregator.aggregate(start_date, end_date)
        
        logger.info(f"Datos agregados: {data['metadata']['total_operations']} operaciones")
        
        # PASO 3: Generar gráficos
        logger.info("Generando gráficos...")
        temp_dir = Path(tempfile.mkdtemp(prefix='cfo_charts_'))
        
        charts_paths = {}
        
        # Gráfico 1: Evolución mensual (histórico)
        if data['historico']['meses']:
            chart_data = {
                'labels': [m['mes'] for m in data['historico']['meses']],
                'series': [
                    {
                        'name': 'Ingresos',
                        'values': [m['ingresos'] for m in data['historico']['meses']],
                        'color': '#10B981'
                    },
                    {
                        'name': 'Gastos',
                        'values': [m['gastos'] for m in data['historico']['meses']],
                        'color': '#EF4444'
                    }
                ]
            }
            charts_paths['evolucion'] = ChartFactory.create_and_save(
                'line',
                chart_data,
                str(temp_dir / 'evolucion.png'),
                {'title': 'Evolución Últimos 6 Meses'}
            )
        
        # Gráfico 2: Distribución por área
        if data['por_area']:
            chart_data = {
                'labels': [a['nombre'] for a in data['por_area'][:5]],
                'values': [a['ingresos'] for a in data['por_area'][:5]]
            }
            charts_paths['areas'] = ChartFactory.create_and_save(
                'pie',
                chart_data,
                str(temp_dir / 'areas.png'),
                {'title': 'Distribución por Área'}
            )
        
        logger.info(f"Gráficos generados: {len(charts_paths)}")
        
        # PASO 4: Generar insights con IA
        logger.info("Generando insights con Claude...")
        
        context_builder = InsightContextBuilder('monthly')
        context_builder.with_metrics(data['metricas_principales'])\
                      .with_historical(data['historico'])\
                      .with_period_info(start_date, end_date, data['metricas_periodo']['mes_nombre'])\
                      .select_analysis_lenses(mes)
        
        context_string = context_builder.to_prompt_string()
        
        insight_gen = InsightGenerator()
        insights = insight_gen.generate_insights(context_string, num_insights=4)
        
        insights_html = InsightFormatter.format_to_html(insights)
        
        logger.info(f"Insights generados: {len(insights)}")
        
        # PASO 5: Convertir gráficos a base64
        logger.info("Convirtiendo gráficos a base64...")
        charts_base64 = AssetManager.batch_convert(charts_paths)
        
        # PASO 6: Generar PDF
        logger.info("Generando PDF...")
        
        pdf_gen = PDFGenerator()
        
        template_context = {
            'period_label': data['metricas_periodo']['mes_nombre'],
            'metricas': data['metricas_principales'],
            'por_area': data['por_area'],
            'por_localidad': data['por_localidad'],
            'charts': charts_base64,
            'insights_html': insights_html,
            'generated_at': data['metadata']['generated_at']
        }
        
        output_pdf = temp_dir / f'reporte_{anio}_{mes:02d}.pdf'
        pdf_path = pdf_gen.generate('monthly_report.html', template_context, str(output_pdf))
        
        logger.info(f"✅ PDF generado: {pdf_path}")
        
        # PASO 7: Retornar archivo
        return FileResponse(
            path=pdf_path,
            media_type='application/pdf',
            filename=f'Reporte_CFO_{anio}_{mes:02d}.pdf'
        )
    
    except Exception as e:
        logger.error(f"Error generando reporte: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
def listar_tipos_reportes():
    """Lista tipos de reportes disponibles"""
    return {
        'available_types': [
            {
                'id': 'monthly',
                'name': 'Reporte Mensual',
                'description': 'Análisis completo de un mes específico'
            }
        ]
    }

