"""
Report Data Aggregator - Sistema CFO Inteligente

Agrega datos financieros desde PostgreSQL para reportes.
Recibe ReportParams y devuelve métricas calculadas.

Autor: Sistema CFO Inteligente
Fecha: Diciembre 2025
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func, desc, extract

from app.core.logger import get_logger
from app.models.operacion import Operacion
from app.models.area import Area
from app.models.socio import Socio
from app.models.distribucion import DistribucionDetalle
from app.services.report_params_extractor import ReportParams, PeriodoReporte

logger = get_logger(__name__)


@dataclass
class MetricasPeriodo:
    """Métricas calculadas para un período."""
    ingresos: float
    gastos: float
    resultado: float  # ingresos - gastos
    rentabilidad: float  # (ingresos - gastos) / ingresos * 100
    retiros: float
    distribuciones: float
    total_operaciones: int
    
    # Desglose opcional
    por_area: Optional[Dict[str, Dict[str, float]]] = None
    por_localidad: Optional[Dict[str, Dict[str, float]]] = None
    por_socio: Optional[Dict[str, float]] = None
    por_mes: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "ingresos": self.ingresos,
            "gastos": self.gastos,
            "resultado": self.resultado,
            "rentabilidad": round(self.rentabilidad, 2),
            "retiros": self.retiros,
            "distribuciones": self.distribuciones,
            "total_operaciones": self.total_operaciones,
            "por_area": self.por_area,
            "por_localidad": self.por_localidad,
            "por_socio": self.por_socio,
            "por_mes": self.por_mes
        }


@dataclass  
class DatosReporte:
    """Datos completos para generar el reporte."""
    params: ReportParams
    periodo_actual: MetricasPeriodo
    periodo_comparacion: Optional[MetricasPeriodo]
    variaciones: Optional[Dict[str, float]]
    top_clientes: List[Dict[str, Any]]
    top_proveedores: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización."""
        return {
            "params": self.params.to_dict(),
            "periodo_actual": self.periodo_actual.to_dict(),
            "periodo_comparacion": self.periodo_comparacion.to_dict() if self.periodo_comparacion else None,
            "variaciones": self.variaciones,
            "top_clientes": self.top_clientes,
            "top_proveedores": self.top_proveedores,
            "metadata": self.metadata
        }


class ReportDataAggregator:
    """
    Agrega datos financieros para reportes.
    
    Ejemplo:
        >>> aggregator = ReportDataAggregator(db)
        >>> datos = aggregator.aggregate(params)
        >>> datos.periodo_actual.ingresos
        5200000.0
    """
    
    def __init__(self, db: Session):
        self.db = db
        logger.info("ReportDataAggregator inicializado")
    
    def _to_float(self, value: Any) -> float:
        """Convierte Decimal o None a float."""
        if value is None:
            return 0.0
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
    
    def _calcular_rentabilidad(self, ingresos: float, gastos: float) -> float:
        """Calcula rentabilidad evitando división por cero."""
        if ingresos == 0:
            return 0.0
        return ((ingresos - gastos) / ingresos) * 100
    
    def aggregate(self, params: ReportParams) -> DatosReporte:
        """
        Agrega todos los datos necesarios para el reporte.
        
        Args:
            params: Parámetros del reporte extraídos
            
        Returns:
            DatosReporte con todas las métricas calculadas
        """
        logger.info(f"Agregando datos para reporte: {params.tipo.value}")
        
        # 1. Calcular métricas período actual
        periodo_actual = self._calcular_metricas(
            params.periodo_actual,
            params.dimensiones,
            params.filtros_adicionales
        )
        
        # 2. Calcular métricas período comparación (si existe)
        periodo_comparacion = None
        if params.periodo_comparacion:
            periodo_comparacion = self._calcular_metricas(
                params.periodo_comparacion,
                params.dimensiones,
                params.filtros_adicionales
            )
        
        # 3. Calcular variaciones
        variaciones = None
        if periodo_comparacion:
            variaciones = self._calcular_variaciones(
                periodo_actual, 
                periodo_comparacion
            )
        
        # 4. Top clientes y proveedores
        top_clientes = self._get_top_clientes(params.periodo_actual, 5)
        top_proveedores = self._get_top_proveedores(params.periodo_actual, 5)
        
        # 5. Metadata
        metadata = {
            "generado_en": datetime.now().isoformat(),
            "periodo_label": params.periodo_actual.label,
            "dias_en_periodo": (params.periodo_actual.fecha_fin - params.periodo_actual.fecha_inicio).days + 1
        }
        
        logger.info(f"Datos agregados: ingresos={periodo_actual.ingresos:,.0f}, "
                   f"gastos={periodo_actual.gastos:,.0f}, "
                   f"rentabilidad={periodo_actual.rentabilidad:.1f}%")
        
        return DatosReporte(
            params=params,
            periodo_actual=periodo_actual,
            periodo_comparacion=periodo_comparacion,
            variaciones=variaciones,
            top_clientes=top_clientes,
            top_proveedores=top_proveedores,
            metadata=metadata
        )
    
    def _calcular_metricas(
        self, 
        periodo: PeriodoReporte,
        dimensiones: List[str],
        filtros: Dict[str, Any] = None
    ) -> MetricasPeriodo:
        """
        Calcula métricas para un período específico.
        
        Args:
            periodo: Período a calcular
            dimensiones: Lista de dimensiones a incluir ["area", "localidad", "socio"]
            filtros: Filtros adicionales (área específica, localidad, etc.)
        """
        filtros = filtros or {}
        
        # Query base: operaciones no eliminadas en el período
        base_filters = [
            Operacion.deleted_at.is_(None),
            Operacion.fecha >= periodo.fecha_inicio,
            Operacion.fecha <= periodo.fecha_fin
        ]
        
        # Aplicar filtros adicionales
        if "localidad" in filtros:
            base_filters.append(Operacion.localidad == filtros["localidad"].upper())
        
        if "area_id" in filtros:
            base_filters.append(Operacion.area_id == filtros["area_id"])
        
        # Calcular totales por tipo de operación
        totales = self.db.query(
            Operacion.tipo_operacion,
            func.sum(Operacion.monto_uyu).label("total"),
            func.count(Operacion.id).label("cantidad")
        ).filter(
            *base_filters
        ).group_by(
            Operacion.tipo_operacion
        ).all()
        
        # Extraer valores por tipo
        ingresos = 0.0
        gastos = 0.0
        retiros = 0.0
        distribuciones = 0.0
        total_ops = 0
        
        for row in totales:
            total = self._to_float(row.total)
            cantidad = row.cantidad or 0
            total_ops += cantidad
            
            tipo = str(row.tipo_operacion).upper()
            if tipo == "INGRESO":
                ingresos = total
            elif tipo == "GASTO":
                gastos = total
            elif tipo == "RETIRO":
                retiros = total
            elif tipo == "DISTRIBUCION":
                distribuciones = total
        
        # Calcular resultado y rentabilidad
        resultado = ingresos - gastos
        rentabilidad = self._calcular_rentabilidad(ingresos, gastos)
        
        # Calcular desgloses según dimensiones solicitadas
        por_area = None
        por_localidad = None
        por_socio = None
        por_mes = None
        
        if "area" in dimensiones:
            por_area = self._get_desglose_por_area(periodo, base_filters)
        
        if "localidad" in dimensiones:
            por_localidad = self._get_desglose_por_localidad(periodo, base_filters)
        
        if "socio" in dimensiones:
            por_socio = self._get_desglose_por_socio(periodo)
        
        # Siempre incluir evolución mensual si el período > 1 mes
        dias = (periodo.fecha_fin - periodo.fecha_inicio).days
        if dias > 31:
            por_mes = self._get_evolucion_mensual(periodo, base_filters)
        
        return MetricasPeriodo(
            ingresos=round(ingresos, 2),
            gastos=round(gastos, 2),
            resultado=round(resultado, 2),
            rentabilidad=round(rentabilidad, 2),
            retiros=round(retiros, 2),
            distribuciones=round(distribuciones, 2),
            total_operaciones=total_ops,
            por_area=por_area,
            por_localidad=por_localidad,
            por_socio=por_socio,
            por_mes=por_mes
        )
    
    def _calcular_variaciones(
        self,
        actual: MetricasPeriodo,
        anterior: MetricasPeriodo
    ) -> Dict[str, float]:
        """
        Calcula % de variación entre períodos.
        
        Args:
            actual: Métricas del período actual
            anterior: Métricas del período de comparación
            
        Returns:
            Dict con variaciones porcentuales
        """
        def variacion(actual_val: float, anterior_val: float) -> float:
            if anterior_val == 0:
                return 100.0 if actual_val > 0 else 0.0
            return ((actual_val - anterior_val) / abs(anterior_val)) * 100
        
        return {
            "ingresos": round(variacion(actual.ingresos, anterior.ingresos), 2),
            "gastos": round(variacion(actual.gastos, anterior.gastos), 2),
            "resultado": round(variacion(actual.resultado, anterior.resultado), 2),
            "rentabilidad_pp": round(actual.rentabilidad - anterior.rentabilidad, 2),  # Puntos porcentuales
            "retiros": round(variacion(actual.retiros, anterior.retiros), 2),
            "distribuciones": round(variacion(actual.distribuciones, anterior.distribuciones), 2),
            "operaciones": round(variacion(actual.total_operaciones, anterior.total_operaciones), 2)
        }
    
    def _get_desglose_por_area(
        self, 
        periodo: PeriodoReporte,
        base_filters: List
    ) -> Dict[str, Dict[str, float]]:
        """
        Calcula ingresos, gastos y rentabilidad por área.
        
        Returns:
            Dict con métricas por área
        """
        query = self.db.query(
            Area.nombre,
            Operacion.tipo_operacion,
            func.sum(Operacion.monto_uyu).label("total")
        ).join(
            Area, Operacion.area_id == Area.id
        ).filter(
            *base_filters,
            Operacion.tipo_operacion.in_(["INGRESO", "GASTO"])
        ).group_by(
            Area.nombre,
            Operacion.tipo_operacion
        ).all()
        
        # Agrupar por área
        areas: Dict[str, Dict[str, float]] = {}
        for row in query:
            area_nombre = row.nombre
            if area_nombre not in areas:
                areas[area_nombre] = {"ingresos": 0.0, "gastos": 0.0, "resultado": 0.0, "rentabilidad": 0.0}
            
            total = self._to_float(row.total)
            tipo = str(row.tipo_operacion).upper()
            
            if tipo == "INGRESO":
                areas[area_nombre]["ingresos"] = round(total, 2)
            elif tipo == "GASTO":
                areas[area_nombre]["gastos"] = round(total, 2)
        
        # Calcular resultado y rentabilidad por área
        for area, datos in areas.items():
            datos["resultado"] = round(datos["ingresos"] - datos["gastos"], 2)
            datos["rentabilidad"] = round(
                self._calcular_rentabilidad(datos["ingresos"], datos["gastos"]), 2
            )
        
        return areas
    
    def _get_desglose_por_localidad(
        self, 
        periodo: PeriodoReporte,
        base_filters: List
    ) -> Dict[str, Dict[str, float]]:
        """
        Calcula métricas por localidad (Montevideo vs Mercedes).
        
        Returns:
            Dict con métricas por localidad
        """
        query = self.db.query(
            Operacion.localidad,
            Operacion.tipo_operacion,
            func.sum(Operacion.monto_uyu).label("total")
        ).filter(
            *base_filters,
            Operacion.tipo_operacion.in_(["INGRESO", "GASTO", "RETIRO"])
        ).group_by(
            Operacion.localidad,
            Operacion.tipo_operacion
        ).all()
        
        # Agrupar por localidad
        localidades: Dict[str, Dict[str, float]] = {
            "MONTEVIDEO": {"ingresos": 0.0, "gastos": 0.0, "retiros": 0.0, "resultado": 0.0, "rentabilidad": 0.0},
            "MERCEDES": {"ingresos": 0.0, "gastos": 0.0, "retiros": 0.0, "resultado": 0.0, "rentabilidad": 0.0}
        }
        
        for row in query:
            loc = str(row.localidad).upper()
            if loc not in localidades:
                continue
                
            total = self._to_float(row.total)
            tipo = str(row.tipo_operacion).upper()
            
            if tipo == "INGRESO":
                localidades[loc]["ingresos"] = round(total, 2)
            elif tipo == "GASTO":
                localidades[loc]["gastos"] = round(total, 2)
            elif tipo == "RETIRO":
                localidades[loc]["retiros"] = round(total, 2)
        
        # Calcular resultado y rentabilidad
        for loc, datos in localidades.items():
            datos["resultado"] = round(datos["ingresos"] - datos["gastos"], 2)
            datos["rentabilidad"] = round(
                self._calcular_rentabilidad(datos["ingresos"], datos["gastos"]), 2
            )
        
        return localidades
    
    def _get_desglose_por_socio(self, periodo: PeriodoReporte) -> Dict[str, float]:
        """
        Calcula distribuciones por socio.
        
        Returns:
            Dict con total distribuido por socio
        """
        query = self.db.query(
            Socio.nombre,
            func.sum(DistribucionDetalle.monto_uyu).label("total")
        ).join(
            DistribucionDetalle, DistribucionDetalle.socio_id == Socio.id
        ).join(
            Operacion, DistribucionDetalle.operacion_id == Operacion.id
        ).filter(
            Operacion.deleted_at.is_(None),
            Operacion.tipo_operacion == "DISTRIBUCION",
            Operacion.fecha >= periodo.fecha_inicio,
            Operacion.fecha <= periodo.fecha_fin
        ).group_by(
            Socio.nombre
        ).all()
        
        return {
            row.nombre: round(self._to_float(row.total), 2)
            for row in query
        }
    
    def _get_evolucion_mensual(
        self, 
        periodo: PeriodoReporte,
        base_filters: List
    ) -> List[Dict[str, Any]]:
        """
        Calcula evolución mes a mes dentro del período.
        
        Returns:
            Lista de dicts con métricas por mes
        """
        query = self.db.query(
            extract('year', Operacion.fecha).label("anio"),
            extract('month', Operacion.fecha).label("mes"),
            Operacion.tipo_operacion,
            func.sum(Operacion.monto_uyu).label("total")
        ).filter(
            *base_filters,
            Operacion.tipo_operacion.in_(["INGRESO", "GASTO"])
        ).group_by(
            extract('year', Operacion.fecha),
            extract('month', Operacion.fecha),
            Operacion.tipo_operacion
        ).order_by(
            extract('year', Operacion.fecha),
            extract('month', Operacion.fecha)
        ).all()
        
        # Agrupar por año-mes
        meses_data: Dict[str, Dict[str, Any]] = {}
        meses_nombres = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
                        "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        
        for row in query:
            anio = int(row.anio)
            mes = int(row.mes)
            key = f"{anio}-{mes:02d}"
            
            if key not in meses_data:
                meses_data[key] = {
                    "label": f"{meses_nombres[mes-1]} {anio}",
                    "anio": anio,
                    "mes": mes,
                    "ingresos": 0.0,
                    "gastos": 0.0,
                    "resultado": 0.0,
                    "rentabilidad": 0.0
                }
            
            total = self._to_float(row.total)
            tipo = str(row.tipo_operacion).upper()
            
            if tipo == "INGRESO":
                meses_data[key]["ingresos"] = round(total, 2)
            elif tipo == "GASTO":
                meses_data[key]["gastos"] = round(total, 2)
        
        # Calcular resultado y rentabilidad por mes
        for key, datos in meses_data.items():
            datos["resultado"] = round(datos["ingresos"] - datos["gastos"], 2)
            datos["rentabilidad"] = round(
                self._calcular_rentabilidad(datos["ingresos"], datos["gastos"]), 2
            )
        
        # Ordenar y retornar como lista
        return [meses_data[k] for k in sorted(meses_data.keys())]
    
    def _get_top_clientes(self, periodo: PeriodoReporte, limit: int) -> List[Dict[str, Any]]:
        """
        Top N clientes por facturación.
        
        Returns:
            Lista de dicts con cliente y monto
        """
        query = self.db.query(
            Operacion.cliente,
            func.sum(Operacion.monto_uyu).label("total"),
            func.count(Operacion.id).label("operaciones")
        ).filter(
            Operacion.deleted_at.is_(None),
            Operacion.tipo_operacion == "INGRESO",
            Operacion.fecha >= periodo.fecha_inicio,
            Operacion.fecha <= periodo.fecha_fin,
            Operacion.cliente.isnot(None),
            Operacion.cliente != ""
        ).group_by(
            Operacion.cliente
        ).order_by(
            desc("total")
        ).limit(limit).all()
        
        return [
            {
                "cliente": row.cliente,
                "total": round(self._to_float(row.total), 2),
                "operaciones": row.operaciones
            }
            for row in query
        ]
    
    def _get_top_proveedores(self, periodo: PeriodoReporte, limit: int) -> List[Dict[str, Any]]:
        """
        Top N proveedores por gastos.
        
        Returns:
            Lista de dicts con proveedor y monto
        """
        query = self.db.query(
            Operacion.proveedor,
            func.sum(Operacion.monto_uyu).label("total"),
            func.count(Operacion.id).label("operaciones")
        ).filter(
            Operacion.deleted_at.is_(None),
            Operacion.tipo_operacion == "GASTO",
            Operacion.fecha >= periodo.fecha_inicio,
            Operacion.fecha <= periodo.fecha_fin,
            Operacion.proveedor.isnot(None),
            Operacion.proveedor != ""
        ).group_by(
            Operacion.proveedor
        ).order_by(
            desc("total")
        ).limit(limit).all()
        
        return [
            {
                "proveedor": row.proveedor,
                "total": round(self._to_float(row.total), 2),
                "operaciones": row.operaciones
            }
            for row in query
        ]


# ═══════════════════════════════════════════════════════════════════════════
# FUNCIÓN HELPER
# ═══════════════════════════════════════════════════════════════════════════

def aggregate_report_data(db: Session, params: ReportParams) -> DatosReporte:
    """
    Función helper para agregar datos de reporte.
    
    Args:
        db: Sesión de SQLAlchemy
        params: Parámetros del reporte
        
    Returns:
        DatosReporte con métricas calculadas
    """
    aggregator = ReportDataAggregator(db)
    return aggregator.aggregate(params)


# ═══════════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════════

def _run_tests():
    """Tests del agregador con datos reales."""
    from app.core.database import SessionLocal
    from app.services.report_params_extractor import ReportParams, PeriodoReporte, ReportType
    
    print("\n" + "="*70)
    print(" TEST DE AGREGACIÓN DE DATOS")
    print("="*70)
    
    db = SessionLocal()
    
    try:
        # Test 1: Período mensual
        print("\n📊 Test 1: Noviembre 2024")
        print("-" * 50)
        
        params = ReportParams(
            tipo=ReportType.MENSUAL,
            titulo="Reporte Noviembre 2024",
            periodo_actual=PeriodoReporte(
                fecha_inicio=date(2024, 11, 1),
                fecha_fin=date(2024, 11, 30),
                label="Noviembre 2024"
            ),
            periodo_comparacion=PeriodoReporte(
                fecha_inicio=date(2024, 10, 1),
                fecha_fin=date(2024, 10, 31),
                label="Octubre 2024"
            ),
            dimensiones=["area", "localidad"],
            moneda_preferida="UYU",
            incluir_graficos=True,
            incluir_narrativas_ia=True,
            filtros_adicionales={}
        )
        
        aggregator = ReportDataAggregator(db)
        datos = aggregator.aggregate(params)
        
        print(f"   Ingresos: ${datos.periodo_actual.ingresos:,.0f}")
        print(f"   Gastos: ${datos.periodo_actual.gastos:,.0f}")
        print(f"   Resultado: ${datos.periodo_actual.resultado:,.0f}")
        print(f"   Rentabilidad: {datos.periodo_actual.rentabilidad:.1f}%")
        print(f"   Operaciones: {datos.periodo_actual.total_operaciones}")
        
        if datos.variaciones:
            print(f"\n   Variaciones vs Oct 2024:")
            print(f"   - Ingresos: {datos.variaciones['ingresos']:+.1f}%")
            print(f"   - Gastos: {datos.variaciones['gastos']:+.1f}%")
            print(f"   - Rentabilidad: {datos.variaciones['rentabilidad_pp']:+.1f} pp")
        
        if datos.periodo_actual.por_area:
            print(f"\n   Por área:")
            for area, metricas in datos.periodo_actual.por_area.items():
                print(f"   - {area}: ${metricas['ingresos']:,.0f} ing, {metricas['rentabilidad']:.1f}% rent")
        
        if datos.top_clientes:
            print(f"\n   Top clientes:")
            for c in datos.top_clientes[:3]:
                print(f"   - {c['cliente']}: ${c['total']:,.0f}")
        
        print("\n✅ Test completado")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print("\n" + "="*70)


if __name__ == "__main__":
    _run_tests()

