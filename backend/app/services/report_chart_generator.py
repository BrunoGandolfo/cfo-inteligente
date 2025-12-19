"""
Report Chart Generator - Generación de gráficos para reportes PDF.

Extraído de ReportOrchestrator para reducir God Object.
"""

from typing import Dict, Any
from pathlib import Path
import base64
import tempfile

from app.services.charts.chart_factory import ChartFactory
from app.core.logger import get_logger

logger = get_logger(__name__)


class ReportChartGenerator:
    """
    Genera todos los gráficos necesarios para reportes PDF.
    
    Responsabilidad única: Crear charts y convertirlos a base64.
    """
    
    def __init__(self):
        self.temp_dir = None
    
    def generate_all(self, metricas: Dict[str, Any]) -> Dict[str, str]:
        """
        Genera todos los gráficos y retorna como base64.
        
        Args:
            metricas: Dict con métricas calculadas
            
        Returns:
            Dict con charts en formato base64 data URI
        """
        self.temp_dir = tempfile.mkdtemp(prefix='report_charts_')
        logger.debug(f"Directorio temporal: {self.temp_dir}")
        
        charts_paths = {}
        
        try:
            self._gen_waterfall(metricas, charts_paths)
            self._gen_donut_areas(metricas, charts_paths)
            self._gen_donut_localidades(metricas, charts_paths)
            self._gen_line_temporal(metricas, charts_paths)
            self._gen_bar_clientes(metricas, charts_paths)
            
            logger.info(f"✓ Total gráficos generados: {len(charts_paths)}")
        except Exception as e:
            logger.error(f"Error generando gráficos: {str(e)}", exc_info=True)
        
        return self._convert_to_base64(charts_paths)
    
    def _convert_to_base64(self, charts_paths: dict) -> Dict[str, str]:
        """Convierte PNGs a base64 data URIs."""
        logger.info("Convirtiendo gráficos PNG a base64 data URIs...")
        charts_base64 = {}
        
        for key, path in charts_paths.items():
            try:
                if path and Path(path).exists():
                    with open(path, "rb") as f:
                        encoded = base64.b64encode(f.read()).decode()
                        charts_base64[key] = f"data:image/png;base64,{encoded}"
                        logger.debug(f"✓ {key} convertido ({len(encoded) / 1024:.1f} KB)")
                else:
                    logger.warning(f"⚠️ Path no existe para {key}: {path}")
            except Exception as e:
                logger.error(f"❌ Error convirtiendo {key}: {e}")
        
        logger.info(f"✓ Convertidos: {len(charts_base64)}/{len(charts_paths)}")
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
    
    def cleanup(self) -> None:
        """Limpia directorio temporal."""
        if self.temp_dir and Path(self.temp_dir).exists():
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
                logger.debug(f"Directorio temporal eliminado: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"No se pudo eliminar: {e}")
        self.temp_dir = None



