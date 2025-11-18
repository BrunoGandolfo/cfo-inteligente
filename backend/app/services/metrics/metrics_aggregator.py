"""
MetricsAggregator - FACADE que coordina todos los calculadores

Orquesta el cálculo de las 29 métricas respetando dependencias.
NO hereda de BaseCalculator porque NO es un calculador, es un coordinador.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import date
from app.models import Operacion
from app.core.logger import get_logger

# Importar todos los calculadores
from app.services.metrics.totals_calculator import TotalsCalculator
from app.services.metrics.results_calculator import ResultsCalculator
from app.services.metrics.ratios_calculator import RatiosCalculator
from app.services.metrics.distribution_calculator import DistributionCalculator
from app.services.metrics.efficiency_calculator import EfficiencyCalculator
from app.services.metrics.trends_calculator import TrendsCalculator
from app.services.metrics.localidad_analyzer import LocalidadAnalyzer
from app.services.metrics.cliente_analyzer import ClienteAnalyzer

logger = get_logger(__name__)


class MetricsAggregator:
    """
    FACADE: Coordina todos los calculadores de métricas.
    
    RESPONSABILIDAD: Orquestar cálculos respetando dependencias (NO calcular).
    PATRÓN: Facade Pattern + Composition
    
    Flujo de dependencias:
    1. TotalsCalculator (independiente)
    2. ResultsCalculator (depende: totals)
    3. RatiosCalculator (depende: totals)
    4. DistributionCalculator (depende: totals)
    5. EfficiencyCalculator (depende: totals)
    6. TrendsCalculator (depende: totals + ratios + comparación)
    
    Principios aplicados:
    - Single Responsibility: Solo coordina, NO calcula
    - Dependency Injection: Inyecta dependencias a cada calculador
    - Composition over Inheritance: Compone calculadores, NO hereda
    - Open/Closed: Extensible (agregar nuevo calculador) sin modificar
    
    Ejemplo:
        >>> aggregator = MetricsAggregator(operaciones)
        >>> metricas = aggregator.aggregate_all()
        >>> print(len(metricas))  # 29+ métricas
        35
    """
    
    def __init__(
        self,
        operaciones: List[Operacion],
        fecha_inicio: date,
        fecha_fin: date,
        operaciones_comparacion: Optional[List[Operacion]] = None,
        historico_mensual: Optional[List[Decimal]] = None,
        operaciones_yoy: Optional[List[Operacion]] = None,
        operaciones_qoq: Optional[List[Operacion]] = None
    ):
        """
        Constructor.
        
        Args:
            operaciones: Operaciones del período principal
            fecha_inicio: Fecha inicio del período
            fecha_fin: Fecha fin del período
            operaciones_comparacion: Operaciones del período de comparación (opcional)
            historico_mensual: Histórico de ingresos mensuales para proyecciones (opcional)
        """
        self.operaciones = operaciones
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.operaciones_comparacion = operaciones_comparacion or []
        self.historico_mensual = historico_mensual or []
        self.operaciones_yoy = operaciones_yoy or []
        self.operaciones_qoq = operaciones_qoq or []
        
        self.logger = logger
    
    def aggregate_all(self) -> Dict[str, Any]:
        """
        Ejecuta todos los calculadores en orden de dependencias.
        
        Flujo:
        1. Calcular totals (sin deps)
        2. Calcular results, ratios, distribution, efficiency (dependen totals)
        3. Calcular comparación si hay datos
        4. Calcular trends (depende totals + ratios + comparación)
        5. Agregar metadata del período
        6. Retornar dict completo
        
        Returns:
            Dict con 29+ métricas organizadas por categoría
            
        Estructura retornada:
            {
                # Métricas base (M1-M26)
                'ingresos_uyu': Decimal('...'),
                'resultado_operativo_uyu': Decimal('...'),
                'margen_operativo': float,
                'porcentaje_ingresos_por_area': Dict,
                'ticket_promedio_ingreso': float,
                'variacion_mom_ingresos': Optional[float],
                
                # Metadata
                'fecha_inicio': date,
                'fecha_fin': date,
                'duracion_dias': int,
                'period_label': str,
                'tiene_comparacion': bool,
                
                # Extras (M27-M29)
                'area_lider': Dict,  # Área con más ingresos
                'localidad_lider': Dict,
                # ... otros
            }
        """
        self.logger.info(f"Iniciando agregación de métricas: {len(self.operaciones)} operaciones")
        
        # ═══════════════════════════════════════════════════════════════
        # PASO 1: TOTALS (sin dependencias)
        # ═══════════════════════════════════════════════════════════════
        
        totals_calc = TotalsCalculator(self.operaciones)
        totals = totals_calc.calculate()
        
        self.logger.debug(f"Totals calculados: ingresos_uyu={totals['ingresos_uyu']}")
        
        # ═══════════════════════════════════════════════════════════════
        # PASO 2: RESULTS, RATIOS, DISTRIBUTION, EFFICIENCY
        # (todas dependen de totals)
        # ═══════════════════════════════════════════════════════════════
        
        results_calc = ResultsCalculator(self.operaciones, totals)
        results = results_calc.calculate()
        
        ratios_calc = RatiosCalculator(self.operaciones, totals)
        ratios = ratios_calc.calculate()
        
        distribution_calc = DistributionCalculator(self.operaciones, totals)
        distribution = distribution_calc.calculate()
        
        efficiency_calc = EfficiencyCalculator(self.operaciones, totals)
        efficiency = efficiency_calc.calculate()
        
        # ═══════════════════════════════════════════════════════════════
        # PASO 3: COMPARACIÓN (si hay datos)
        # ═══════════════════════════════════════════════════════════════
        
        comparacion_totals = None
        comparacion_ratios = None
        
        if self.operaciones_comparacion:
            self.logger.info("Calculando métricas de comparación")
            
            comp_totals_calc = TotalsCalculator(self.operaciones_comparacion)
            comparacion_totals = comp_totals_calc.calculate()
            
            comp_ratios_calc = RatiosCalculator(self.operaciones_comparacion, comparacion_totals)
            comparacion_ratios = comp_ratios_calc.calculate()
        
        # ═══════════════════════════════════════════════════════════════
        # PASO 3B: COMPARACIONES YoY y QoQ (si hay datos)
        # ═══════════════════════════════════════════════════════════════
        
        totals_yoy = None
        totals_qoq = None
        
        if self.operaciones_yoy:
            self.logger.info("Calculando métricas YoY")
            yoy_totals_calc = TotalsCalculator(self.operaciones_yoy)
            totals_yoy = yoy_totals_calc.calculate()
        
        if self.operaciones_qoq:
            self.logger.info("Calculando métricas QoQ")
            qoq_totals_calc = TotalsCalculator(self.operaciones_qoq)
            totals_qoq = qoq_totals_calc.calculate()
        
        # ═══════════════════════════════════════════════════════════════
        # PASO 4: TRENDS (depende de totals + ratios + comparación)
        # ═══════════════════════════════════════════════════════════════
        
        trends_calc = TrendsCalculator(
            self.operaciones,
            totals,
            ratios,
            comparacion_totals=comparacion_totals,
            comparacion_ratios=comparacion_ratios,
            historico_mensual=self.historico_mensual,
            totals_yoy=totals_yoy,
            totals_qoq=totals_qoq
        )
        trends = trends_calc.calculate()
        
        # ═══════════════════════════════════════════════════════════════
        # PASO 5: ANALIZAR LOCALIDADES
        # ═══════════════════════════════════════════════════════════════
        
        localidad_calc = LocalidadAnalyzer(self.operaciones)
        localidad_analysis = localidad_calc.calculate()
        
        # ═══════════════════════════════════════════════════════════════
        # PASO 6: ANALIZAR CLIENTES
        # ═══════════════════════════════════════════════════════════════
        
        cliente_calc = ClienteAnalyzer(self.operaciones)
        cliente_analysis = cliente_calc.calculate()
        
        # ═══════════════════════════════════════════════════════════════
        # PASO 6B: CALCULAR SERIES TEMPORALES MENSUALES
        # ═══════════════════════════════════════════════════════════════
        
        series_temporales = self._calculate_series_temporales()
        
        # ═══════════════════════════════════════════════════════════════
        # PASO 7: CALCULAR EXTRAS (M27-M29)
        # ═══════════════════════════════════════════════════════════════
        
        area_lider = self._calc_area_lider(ratios['rentabilidad_por_area'], distribution['porcentaje_ingresos_por_area'])
        localidad_lider = self._calc_localidad_lider(distribution['porcentaje_ingresos_por_localidad'])
        
        # ═══════════════════════════════════════════════════════════════
        # PASO 6: AGREGAR METADATA
        # ═══════════════════════════════════════════════════════════════
        
        duracion_dias = (self.fecha_fin - self.fecha_inicio).days + 1
        
        from app.utils.date_resolver import get_period_label
        period_label = get_period_label(self.fecha_inicio, self.fecha_fin)
        
        # ═══════════════════════════════════════════════════════════════
        # PASO 7: COMPONER TODO (Composition Pattern)
        # ═══════════════════════════════════════════════════════════════
        
        metricas_completas = {
            # Totals (M1-M8)
            **totals,
            
            # Results (M9-M10)
            **results,
            
            # Ratios (M11-M14)
            **ratios,
            
            # Distribution (M15-M17)
            **distribution,
            
            # Efficiency (M18-M20)
            **efficiency,
            
            # Trends (M21-M26)
            **trends,
            
            # Localidad Analysis
            **localidad_analysis,
            
            # Cliente Analysis
            **cliente_analysis,
            
            # Series temporales (para gráficos)
            **series_temporales,
            
            # Extras (M27-M29)
            'area_lider': area_lider,
            'localidad_lider': localidad_lider,
            
            # Metadata
            'fecha_inicio': self.fecha_inicio,
            'fecha_fin': self.fecha_fin,
            'duracion_dias': duracion_dias,
            'period_label': period_label,
            'tiene_comparacion': bool(self.operaciones_comparacion)
        }
        
        self.logger.info(f"Agregación completada: {len(metricas_completas)} métricas totales (incluye análisis localidades y clientes)")
        
        return metricas_completas
    
    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS PRIVADOS (para extras M27-M29)
    # ═══════════════════════════════════════════════════════════════
    
    def _calc_area_lider(
        self,
        rentabilidad_por_area: Dict[str, float],
        porcentaje_por_area: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Identifica área líder (más ingresos).
        
        M27: Área con mayor porcentaje de ingresos.
        
        Returns:
            Dict {'nombre': str, 'porcentaje': float, 'rentabilidad': float}
        """
        if not porcentaje_por_area:
            return {'nombre': 'N/A', 'porcentaje': 0.0, 'rentabilidad': 0.0}
        
        # Área con mayor porcentaje de ingresos
        area_lider_nombre = max(porcentaje_por_area, key=porcentaje_por_area.get)
        
        return {
            'nombre': area_lider_nombre,
            'porcentaje': porcentaje_por_area[area_lider_nombre],
            'rentabilidad': rentabilidad_por_area.get(area_lider_nombre, 0.0)
        }
    
    def _calc_localidad_lider(
        self,
        porcentaje_por_localidad: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Identifica localidad líder (más ingresos).
        
        M28: Localidad con mayor porcentaje de ingresos.
        
        Returns:
            Dict {'nombre': str, 'porcentaje': float}
        """
        if not porcentaje_por_localidad:
            return {'nombre': 'N/A', 'porcentaje': 0.0}
        
        localidad_lider_nombre = max(porcentaje_por_localidad, key=porcentaje_por_localidad.get)
        
        return {
            'nombre': localidad_lider_nombre,
            'porcentaje': porcentaje_por_localidad[localidad_lider_nombre]
        }
    
    def _calculate_series_temporales(self) -> Dict[str, Any]:
        """
        Calcula series temporales mensuales para gráficos de línea.
        
        Agrupa operaciones por mes y calcula:
        - Ingresos mensuales
        - Gastos mensuales
        - Utilidad mensual (ingresos - gastos)
        
        Returns:
            Dict con 4 listas:
            {
                'meses': ['Oct 2025', 'Nov 2025', ...],
                'ingresos_por_mes': [150000, 180000, ...],
                'gastos_por_mes': [50000, 60000, ...],
                'utilidad_por_mes': [100000, 120000, ...]
            }
        """
        from datetime import datetime
        from collections import defaultdict
        from app.models import TipoOperacion
        
        # Agrupar operaciones por mes
        ops_por_mes = defaultdict(lambda: {'ingresos': 0, 'gastos': 0})
        
        for op in self.operaciones:
            mes_key = op.fecha.strftime('%Y-%m')
            
            if op.tipo_operacion == TipoOperacion.INGRESO:
                ops_por_mes[mes_key]['ingresos'] += float(op.monto_uyu)
            elif op.tipo_operacion == TipoOperacion.GASTO:
                ops_por_mes[mes_key]['gastos'] += float(op.monto_uyu)
        
        # Ordenar por fecha
        meses_ordenados = sorted(ops_por_mes.keys())
        
        # Preparar series
        meses = []
        ingresos_por_mes = []
        gastos_por_mes = []
        utilidad_por_mes = []
        
        for mes in meses_ordenados:
            # Formato: "Oct 2025"
            fecha = datetime.strptime(mes, '%Y-%m')
            mes_label = fecha.strftime('%b %Y')
            
            ing = ops_por_mes[mes]['ingresos']
            gas = ops_por_mes[mes]['gastos']
            util = ing - gas
            
            meses.append(mes_label)
            ingresos_por_mes.append(ing)
            gastos_por_mes.append(gas)
            utilidad_por_mes.append(util)
        
        return {
            'meses': meses,
            'ingresos_por_mes': ingresos_por_mes,
            'gastos_por_mes': gastos_por_mes,
            'utilidad_por_mes': utilidad_por_mes
        }

