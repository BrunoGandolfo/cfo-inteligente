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
Fecha: Octubre 2025
"""

from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import Operacion, TipoOperacion
from app.core.logger import get_logger

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
        
        # PASO 4: Calcular métricas por dimensión
        metricas_por_area = self.calculate_by_area(operaciones)
        metricas_por_localidad = self.calculate_by_location(operaciones)
        metricas_por_socio = self.calculate_by_socio(operaciones)
        
        # PASO 5: Calcular datos históricos (contexto temporal)
        historico = self.calculate_historical_context(start_date, end_date)
        
        # PASO 6: Calcular métricas específicas del período (abstracto)
        metricas_especificas = self.calculate_period_specific_metrics(
            operaciones, start_date, end_date
        )
        
        # PASO 7: Detectar eventos destacados
        eventos = self.detect_remarkable_events(operaciones, metricas_principales)
        
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
        """
        Calcula métricas principales comunes a todos los períodos:
        - Ingresos, Gastos, Retiros, Distribuciones
        - Rentabilidad
        - Resultado operativo
        - Resultado neto
        """
        ingresos_uyu = sum(
            float(op.monto_uyu) for op in operaciones 
            if op.tipo_operacion == TipoOperacion.INGRESO
        ) or 0.0
        
        gastos_uyu = sum(
            float(op.monto_uyu) for op in operaciones 
            if op.tipo_operacion == TipoOperacion.GASTO
        ) or 0.0
        
        retiros_uyu = sum(
            float(op.monto_uyu) for op in operaciones 
            if op.tipo_operacion == TipoOperacion.RETIRO
        ) or 0.0
        
        distribuciones_uyu = sum(
            float(op.monto_uyu) for op in operaciones 
            if op.tipo_operacion == TipoOperacion.DISTRIBUCION
        ) or 0.0
        
        # Rentabilidad: (Ingresos - Gastos) / Ingresos * 100
        rentabilidad = 0.0
        if ingresos_uyu > 0:
            rentabilidad = ((ingresos_uyu - gastos_uyu) / ingresos_uyu) * 100.0
        
        # Resultado operativo: Ingresos - Gastos
        resultado_operativo = ingresos_uyu - gastos_uyu
        
        # Resultado neto: Resultado operativo - Retiros - Distribuciones
        resultado_neto = resultado_operativo - retiros_uyu - distribuciones_uyu
        
        return {
            'ingresos': {
                'uyu': round(ingresos_uyu, 2),
                'cantidad_operaciones': len([op for op in operaciones if op.tipo_operacion == TipoOperacion.INGRESO])
            },
            'gastos': {
                'uyu': round(gastos_uyu, 2),
                'cantidad_operaciones': len([op for op in operaciones if op.tipo_operacion == TipoOperacion.GASTO])
            },
            'retiros': {
                'uyu': round(retiros_uyu, 2),
                'cantidad_operaciones': len([op for op in operaciones if op.tipo_operacion == TipoOperacion.RETIRO])
            },
            'distribuciones': {
                'uyu': round(distribuciones_uyu, 2),
                'cantidad_operaciones': len([op for op in operaciones if op.tipo_operacion == TipoOperacion.DISTRIBUCION])
            },
            'rentabilidad_porcentaje': round(rentabilidad, 2),
            'resultado_operativo': round(resultado_operativo, 2),
            'resultado_neto': round(resultado_neto, 2)
        }
    
    def calculate_by_area(self, operaciones: List[Operacion]) -> List[Dict[str, Any]]:
        """Agrega métricas por área de negocio"""
        areas_data = {}
        
        for op in operaciones:
            if not op.area:
                continue
            
            area_nombre = op.area.nombre
            
            if area_nombre not in areas_data:
                areas_data[area_nombre] = {
                    'nombre': area_nombre,
                    'ingresos': 0.0,
                    'gastos': 0.0,
                    'cantidad_ops': 0
                }
            
            areas_data[area_nombre]['cantidad_ops'] += 1
            
            if op.tipo_operacion == TipoOperacion.INGRESO:
                areas_data[area_nombre]['ingresos'] += float(op.monto_uyu)
            elif op.tipo_operacion == TipoOperacion.GASTO:
                areas_data[area_nombre]['gastos'] += float(op.monto_uyu)
        
        # Calcular rentabilidad por área
        resultado = []
        for area_nombre, data in areas_data.items():
            rentabilidad = 0.0
            if data['ingresos'] > 0:
                rentabilidad = ((data['ingresos'] - data['gastos']) / data['ingresos']) * 100.0
            
            resultado.append({
                'nombre': area_nombre,
                'ingresos': round(data['ingresos'], 2),
                'gastos': round(data['gastos'], 2),
                'rentabilidad': round(rentabilidad, 2),
                'resultado': round(data['ingresos'] - data['gastos'], 2),
                'cantidad_operaciones': data['cantidad_ops']
            })
        
        # Ordenar por ingresos descendente
        resultado.sort(key=lambda x: x['ingresos'], reverse=True)
        
        return resultado
    
    def calculate_by_location(self, operaciones: List[Operacion]) -> Dict[str, Any]:
        """Agrega métricas por localidad"""
        localidades = {'Montevideo': {}, 'Mercedes': {}}
        
        for loc in localidades:
            localidades[loc] = {
                'ingresos': 0.0,
                'gastos': 0.0,
                'retiros': 0.0,
                'cantidad_ops': 0
            }
        
        for op in operaciones:
            loc = op.localidad.value if op.localidad else None
            if loc not in localidades:
                continue
            
            localidades[loc]['cantidad_ops'] += 1
            
            if op.tipo_operacion == TipoOperacion.INGRESO:
                localidades[loc]['ingresos'] += float(op.monto_uyu)
            elif op.tipo_operacion == TipoOperacion.GASTO:
                localidades[loc]['gastos'] += float(op.monto_uyu)
            elif op.tipo_operacion == TipoOperacion.RETIRO:
                localidades[loc]['retiros'] += float(op.monto_uyu)
        
        # Calcular rentabilidad y resultado por localidad
        for loc, data in localidades.items():
            if data['ingresos'] > 0:
                data['rentabilidad'] = round(((data['ingresos'] - data['gastos']) / data['ingresos']) * 100.0, 2)
            else:
                data['rentabilidad'] = 0.0
            
            data['resultado'] = round(data['ingresos'] - data['gastos'], 2)
            data['ingresos'] = round(data['ingresos'], 2)
            data['gastos'] = round(data['gastos'], 2)
            data['retiros'] = round(data['retiros'], 2)
        
        return localidades
    
    def calculate_by_socio(self, operaciones: List[Operacion]) -> List[Dict[str, Any]]:
        """Agrega distribuciones por socio"""
        from app.models import DistribucionDetalle
        
        # Obtener IDs de operaciones de tipo DISTRIBUCION
        dist_ids = [
            op.id for op in operaciones 
            if op.tipo_operacion == TipoOperacion.DISTRIBUCION
        ]
        
        if not dist_ids:
            return []
        
        # Query detalles de distribuciones
        detalles = self.db.query(DistribucionDetalle).filter(
            DistribucionDetalle.operacion_id.in_(dist_ids)
        ).all()
        
        # Agregar por socio
        socios_data = {}
        
        for detalle in detalles:
            socio_nombre = detalle.socio.nombre if detalle.socio else 'Desconocido'
            
            if socio_nombre not in socios_data:
                socios_data[socio_nombre] = {
                    'nombre': socio_nombre,
                    'total_uyu': 0.0,
                    'total_usd': 0.0,
                    'cantidad_distribuciones': 0
                }
            
            socios_data[socio_nombre]['total_uyu'] += float(detalle.monto_uyu or 0)
            socios_data[socio_nombre]['total_usd'] += float(detalle.monto_usd or 0)
            socios_data[socio_nombre]['cantidad_distribuciones'] += 1
        
        resultado = [
            {
                'nombre': data['nombre'],
                'total_uyu': round(data['total_uyu'], 2),
                'total_usd': round(data['total_usd'], 2),
                'cantidad_distribuciones': data['cantidad_distribuciones']
            }
            for data in socios_data.values()
        ]
        
        # Ordenar por monto UYU descendente
        resultado.sort(key=lambda x: x['total_uyu'], reverse=True)
        
        return resultado
    
    def calculate_historical_context(
        self, 
        start_date: date, 
        end_date: date
    ) -> Dict[str, Any]:
        """
        Calcula datos históricos para contexto comparativo.
        
        Retorna 6 meses anteriores agregados mensualmente.
        Reutilizable, puede sobreescribirse para períodos diferentes.
        """
        # Calcular inicio de 6 meses antes
        meses_atras = start_date - timedelta(days=180)
        
        # Query operaciones históricas
        ops_historicas = self.db.query(Operacion).filter(
            and_(
                Operacion.fecha >= meses_atras,
                Operacion.fecha < start_date,
                Operacion.deleted_at.is_(None)
            )
        ).all()
        
        # Agrupar por mes
        meses = {}
        
        for op in ops_historicas:
            mes_key = op.fecha.strftime('%Y-%m')
            
            if mes_key not in meses:
                meses[mes_key] = {
                    'mes': mes_key,
                    'ingresos': 0.0,
                    'gastos': 0.0,
                    'rentabilidad': 0.0
                }
            
            if op.tipo_operacion == TipoOperacion.INGRESO:
                meses[mes_key]['ingresos'] += float(op.monto_uyu)
            elif op.tipo_operacion == TipoOperacion.GASTO:
                meses[mes_key]['gastos'] += float(op.monto_uyu)
        
        # Calcular rentabilidad histórica
        for mes_data in meses.values():
            if mes_data['ingresos'] > 0:
                mes_data['rentabilidad'] = round(
                    ((mes_data['ingresos'] - mes_data['gastos']) / mes_data['ingresos']) * 100.0, 
                    2
                )
            mes_data['ingresos'] = round(mes_data['ingresos'], 2)
            mes_data['gastos'] = round(mes_data['gastos'], 2)
        
        # Retornar últimos 6 meses ordenados
        meses_ordenados = sorted(meses.values(), key=lambda x: x['mes'])[-6:]
        
        # Calcular promedios históricos
        if meses_ordenados:
            promedio_ingresos = sum(m['ingresos'] for m in meses_ordenados) / len(meses_ordenados)
            promedio_gastos = sum(m['gastos'] for m in meses_ordenados) / len(meses_ordenados)
            promedio_rentabilidad = sum(m['rentabilidad'] for m in meses_ordenados) / len(meses_ordenados)
        else:
            promedio_ingresos = promedio_gastos = promedio_rentabilidad = 0.0
        
        return {
            'meses': meses_ordenados,
            'promedios': {
                'ingresos': round(promedio_ingresos, 2),
                'gastos': round(promedio_gastos, 2),
                'rentabilidad': round(promedio_rentabilidad, 2)
            }
        }
    
    def detect_remarkable_events(
        self, 
        operaciones: List[Operacion],
        metricas: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Detecta eventos destacados que deberían mencionarse en el reporte.
        
        Ejemplos:
        - Día con facturación excepcional
        - Cliente nuevo de alto valor
        - Gasto inusualmente alto
        - Racha de días consecutivos sin ingresos
        """
        eventos = []
        
        # Agrupar por día
        por_dia = {}
        for op in operaciones:
            dia = op.fecha.isoformat()
            if dia not in por_dia:
                por_dia[dia] = {'ingresos': 0.0, 'gastos': 0.0}
            
            if op.tipo_operacion == TipoOperacion.INGRESO:
                por_dia[dia]['ingresos'] += float(op.monto_uyu)
            elif op.tipo_operacion == TipoOperacion.GASTO:
                por_dia[dia]['gastos'] += float(op.monto_uyu)
        
        # Detectar día con ingresos excepcionales (>3x promedio)
        if por_dia:
            promedio_diario = sum(d['ingresos'] for d in por_dia.values()) / len(por_dia)
            
            for dia, data in por_dia.items():
                if data['ingresos'] > promedio_diario * 3:
                    eventos.append({
                        'tipo': 'high_revenue_day',
                        'fecha': dia,
                        'descripcion': f"Facturación excepcional: ${data['ingresos']:,.2f} ({data['ingresos']/promedio_diario:.1f}x promedio)"
                    })
        
        return eventos
    
    # ═══════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════
    
    def _get_period_label(self, start_date: date, end_date: date) -> str:
        """Retorna label legible del período (ej: 'Octubre 2025', 'Q3 2025')"""
        return f"{start_date.isoformat()} a {end_date.isoformat()}"

