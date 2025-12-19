"""
BaseAggregator - Clase abstracta para agregación de datos financieros

Define la interfaz común para todos los agregadores (semanal, mensual, trimestral, anual).
Implementa Template Method pattern para el flujo de agregación.

Principios SOLID:
- Single Responsibility: Solo agrega datos, no genera PDFs ni gráficos
- Open/Closed: Extensible vía herencia, cerrado a modificación
- Liskov Substitution: Todos los agregadores son intercambiables
- Dependency Inversion: Depende de abstracciones (Session, no implementaciones)

Autor: Sistema CFO Inteligente
Versión: 2.0 (modular)
Fecha: Diciembre 2025
"""
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Dict, List, Any

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import Operacion, TipoOperacion
from app.core.logger import get_logger
from app.services.report_data.dimension_calculators import DimensionCalculators

logger = get_logger(__name__)


class BaseAggregator(ABC):
    """
    Clase base abstracta para agregadores de datos financieros.
    
    Template Method Pattern:
    - aggregate() orquesta el flujo completo
    - Métodos abstractos implementados por subclases
    - Métodos concretos reutilizables
    """
    
    def __init__(self, db: Session):
        """
        Args:
            db: Sesión de SQLAlchemy para queries
        """
        self.db = db
        self.logger = logger
        self._dim_calc = DimensionCalculators(db)
    
    # ═══════════════════════════════════════════════════════════════
    # TEMPLATE METHOD (Flujo principal)
    # ═══════════════════════════════════════════════════════════════
    
    def aggregate(self, start_date: date, end_date: date, **kwargs) -> Dict[str, Any]:
        """
        Template Method: Flujo completo de agregación de datos.
        
        Este método NO debe ser sobreescrito por subclases.
        Define el algoritmo completo que llama a métodos abstractos.
        
        Args:
            start_date: Fecha inicio del período
            end_date: Fecha fin del período
            **kwargs: Parámetros adicionales (localidad, moneda_vista, etc)
            
        Returns:
            Dict con todas las métricas, datos históricos y metadatos
        """
        self.logger.info(f"Agregando datos para {self.__class__.__name__}: {start_date} a {end_date}")
        
        # PASO 1: Validar período
        self.validate_period(start_date, end_date)
        
        # PASO 2: Obtener operaciones del período
        operaciones = self.fetch_operations(start_date, end_date, **kwargs)
        self.logger.debug(f"Operaciones obtenidas: {len(operaciones)}")
        
        # PASO 3: Calcular métricas principales
        metricas_principales = self.calculate_main_metrics(operaciones)
        
        # PASO 4: Calcular métricas por dimensión (delegado a DimensionCalculators)
        metricas_por_area = self._dim_calc.calculate_by_area(operaciones)
        metricas_por_localidad = self._dim_calc.calculate_by_location(operaciones)
        metricas_por_socio = self._dim_calc.calculate_by_socio(operaciones)
        
        # PASO 5: Calcular datos históricos (contexto temporal)
        historico = self._dim_calc.calculate_historical_context(start_date, end_date)
        
        # PASO 6: Calcular métricas específicas del período (abstracto)
        metricas_especificas = self.calculate_period_specific_metrics(
            operaciones, start_date, end_date
        )
        
        # PASO 7: Detectar eventos destacados
        eventos = self._dim_calc.detect_remarkable_events(operaciones, metricas_principales)
        
        # PASO 8: Ensamblar resultado final
        return {
            'metadata': {
                'period_type': self.get_period_type(),
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'generated_at': datetime.now().isoformat(),
                'total_operations': len(operaciones)
            },
            'metricas_principales': metricas_principales,
            'por_area': metricas_por_area,
            'por_localidad': metricas_por_localidad,
            'por_socio': metricas_por_socio,
            'historico': historico,
            'metricas_periodo': metricas_especificas,
            'eventos_destacados': eventos
        }
    
    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS ABSTRACTOS (Implementar en subclases)
    # ═══════════════════════════════════════════════════════════════
    
    @abstractmethod
    def get_period_type(self) -> str:
        """Retorna tipo de período: 'weekly', 'monthly', 'quarterly', 'yearly'"""
    
    @abstractmethod
    def validate_period(self, start_date: date, end_date: date) -> None:
        """
        Valida que el período sea correcto para este tipo de agregador.
        Debe lanzar ValueError si el período no es válido.
        """
    
    @abstractmethod
    def calculate_period_specific_metrics(
        self, 
        operaciones: List[Operacion],
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Calcula métricas específicas del tipo de período.
        
        Ejemplo:
        - Monthly: días laborables, semanas completas
        - Quarterly: meses del trimestre, comparación con Q anterior
        - Yearly: trimestres, comparación YoY
        """
    
    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS CONCRETOS (Reutilizables, pueden sobreescribirse)
    # ═══════════════════════════════════════════════════════════════
    
    def fetch_operations(
        self, 
        start_date: date, 
        end_date: date,
        localidad: str = None
    ) -> List[Operacion]:
        """
        Obtiene operaciones del período especificado.
        
        Reutilizable pero puede sobreescribirse si se necesita lógica especial.
        """
        filtros = [
            Operacion.fecha >= start_date,
            Operacion.fecha <= end_date,
            Operacion.deleted_at.is_(None)
        ]
        
        if localidad and localidad != "Todas":
            from app.models import Localidad
            localidad_map = {
                "Montevideo": Localidad.MONTEVIDEO,
                "Mercedes": Localidad.MERCEDES
            }
            if localidad in localidad_map:
                filtros.append(Operacion.localidad == localidad_map[localidad])
        
        return self.db.query(Operacion).filter(and_(*filtros)).all()
    
    def calculate_main_metrics(self, operaciones: List[Operacion]) -> Dict[str, Any]:
        """Calcula métricas principales usando helpers para reducir complejidad."""
        totales = self._calcular_totales_por_tipo(operaciones)
        
        ingresos = totales[TipoOperacion.INGRESO]
        gastos = totales[TipoOperacion.GASTO]
        retiros = totales[TipoOperacion.RETIRO]
        distribuciones = totales[TipoOperacion.DISTRIBUCION]
        
        # Cálculos derivados
        rentabilidad = ((ingresos['uyu'] - gastos['uyu']) / ingresos['uyu'] * 100) if ingresos['uyu'] > 0 else 0.0
        resultado_operativo = ingresos['uyu'] - gastos['uyu']
        resultado_neto = resultado_operativo - retiros['uyu'] - distribuciones['uyu']
        
        return {
            'ingresos': {'uyu': round(ingresos['uyu'], 2), 'cantidad_operaciones': ingresos['cantidad']},
            'gastos': {'uyu': round(gastos['uyu'], 2), 'cantidad_operaciones': gastos['cantidad']},
            'retiros': {'uyu': round(retiros['uyu'], 2), 'cantidad_operaciones': retiros['cantidad']},
            'distribuciones': {'uyu': round(distribuciones['uyu'], 2), 'cantidad_operaciones': distribuciones['cantidad']},
            'rentabilidad_porcentaje': round(rentabilidad, 2),
            'resultado_operativo': round(resultado_operativo, 2),
            'resultado_neto': round(resultado_neto, 2)
        }
    
    def _calcular_totales_por_tipo(self, operaciones: List[Operacion]) -> Dict[TipoOperacion, Dict]:
        """Agrupa operaciones por tipo y calcula totales."""
        totales = {tipo: {'uyu': 0.0, 'cantidad': 0} for tipo in TipoOperacion}
        
        for op in operaciones:
            if op.tipo_operacion in totales:
                totales[op.tipo_operacion]['uyu'] += float(op.monto_uyu or 0)
                totales[op.tipo_operacion]['cantidad'] += 1
        
        return totales
    
    # Métodos delegados a DimensionCalculators (para compatibilidad)
    def calculate_by_area(self, operaciones: List[Operacion]) -> List[Dict[str, Any]]:
        """Agrega métricas por área (delegado a DimensionCalculators)."""
        return self._dim_calc.calculate_by_area(operaciones)
    
    def calculate_by_location(self, operaciones: List[Operacion]) -> Dict[str, Any]:
        """Agrega métricas por localidad (delegado a DimensionCalculators)."""
        return self._dim_calc.calculate_by_location(operaciones)
    
    def calculate_by_socio(self, operaciones: List[Operacion]) -> List[Dict[str, Any]]:
        """Agrega distribuciones por socio (delegado a DimensionCalculators)."""
        return self._dim_calc.calculate_by_socio(operaciones)
    
    def calculate_historical_context(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Calcula datos históricos (delegado a DimensionCalculators)."""
        return self._dim_calc.calculate_historical_context(start_date, end_date)
    
    def detect_remarkable_events(
        self, 
        operaciones: List[Operacion],
        metricas: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Detecta eventos destacados (delegado a DimensionCalculators)."""
        return self._dim_calc.detect_remarkable_events(operaciones, metricas)
    
    # ═══════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════
    
    def _get_period_label(self, start_date: date, end_date: date) -> str:
        """Retorna label legible del período (ej: 'Octubre 2025', 'Q3 2025')"""
        return f"{start_date.isoformat()} a {end_date.isoformat()}"
