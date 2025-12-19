"""
Dimension Calculators - Cálculos por dimensión para reportes.

Extraído de base_aggregator.py para reducir su tamaño.
Contiene métodos de agregación por área, localidad, socio y contexto histórico.

Autor: Sistema CFO Inteligente
Fecha: Diciembre 2025
"""
from datetime import date, timedelta
from typing import Dict, List, Any

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import Operacion, TipoOperacion


class DimensionCalculators:
    """Calculadores por dimensión para reportes financieros."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_by_area(self, operaciones: List[Operacion]) -> List[Dict[str, Any]]:
        """Agrega métricas por área de negocio."""
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
        
        resultado.sort(key=lambda x: x['ingresos'], reverse=True)
        return resultado
    
    def calculate_by_location(self, operaciones: List[Operacion]) -> Dict[str, Any]:
        """Agrega métricas por localidad."""
        localidades = {
            'Montevideo': {'ingresos': 0.0, 'gastos': 0.0, 'retiros': 0.0, 'cantidad_ops': 0},
            'Mercedes': {'ingresos': 0.0, 'gastos': 0.0, 'retiros': 0.0, 'cantidad_ops': 0}
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
        for data in localidades.values():
            if data['ingresos'] > 0:
                data['rentabilidad'] = round(
                    ((data['ingresos'] - data['gastos']) / data['ingresos']) * 100.0, 2
                )
            else:
                data['rentabilidad'] = 0.0
            
            data['resultado'] = round(data['ingresos'] - data['gastos'], 2)
            data['ingresos'] = round(data['ingresos'], 2)
            data['gastos'] = round(data['gastos'], 2)
            data['retiros'] = round(data['retiros'], 2)
        
        return localidades
    
    def calculate_by_socio(self, operaciones: List[Operacion]) -> List[Dict[str, Any]]:
        """Agrega distribuciones por socio."""
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
        """
        meses_atras = start_date - timedelta(days=180)
        
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

