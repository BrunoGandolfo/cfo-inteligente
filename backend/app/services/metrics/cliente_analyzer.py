"""
ClienteAnalyzer - Analiza concentración y distribución de clientes

Calcula top clientes, análisis Pareto, índice HHI.
CRÍTICO para evaluar riesgo de concentración.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import List, Dict, Any
from decimal import Decimal
from collections import defaultdict
from app.models import Operacion, TipoOperacion
from app.services.metrics.base_calculator import BaseCalculator


class ClienteAnalyzer(BaseCalculator):
    """
    Analiza concentración y distribución de clientes.
    
    RESPONSABILIDAD: Análisis de cartera de clientes.
    
    Métricas calculadas:
    - Top 10 clientes por facturación
    - Top 5 clientes por localidad
    - Análisis Pareto (80/20)
    - Índice Herfindahl-Hirschman (HHI)
    - Distribución por rangos de facturación
    """
    
    def __init__(self, operaciones: List[Operacion]):
        super().__init__(operaciones)
    
    def calculate(self) -> Dict[str, Any]:
        """Calcula análisis completo de clientes."""
        return {
            'top_clientes': self._calc_top_clientes_total(limit=10),
            'top_clientes_por_localidad': self._calc_top_clientes_por_localidad(limit=5),
            'analisis_pareto': self._calc_analisis_pareto(),
            'indice_hhi': self._calc_indice_herfindahl(),
            'distribucion_rangos': self._calc_distribucion_por_rango()
        }
    
    def get_metric_names(self) -> List[str]:
        return [
            'top_clientes',
            'top_clientes_por_localidad',
            'analisis_pareto',
            'indice_hhi',
            'distribucion_rangos'
        ]
    
    def _calc_top_clientes_total(self, limit: int = 10) -> List[Dict]:
        """Top N clientes por facturación total."""
        clientes_data = defaultdict(lambda: {'monto': Decimal('0'), 'ops': 0, 'areas': defaultdict(lambda: Decimal('0'))})
        
        for op in self.operaciones:
            if op.tipo_operacion == TipoOperacion.INGRESO and op.cliente:
                clientes_data[op.cliente]['monto'] += op.monto_uyu
                clientes_data[op.cliente]['ops'] += 1
                # Agregar área principal
                if op.area:
                    clientes_data[op.cliente]['areas'][op.area.nombre] += op.monto_uyu
        
        # Calcular total para porcentajes
        total_facturacion = sum(c['monto'] for c in clientes_data.values())
        
        # Ordenar y limitar
        top = sorted(clientes_data.items(), key=lambda x: x[1]['monto'], reverse=True)[:limit]
        
        result = []
        acumulado = 0.0
        for cliente, data in top:
            monto = float(data['monto'])
            pct = (monto / float(total_facturacion) * 100) if total_facturacion > 0 else 0
            acumulado += pct
            
            # Determinar área principal (la de mayor facturación)
            area_principal = 'N/A'
            if data['areas']:
                area_principal = max(data['areas'].items(), key=lambda x: x[1])[0]
            
            result.append({
                'cliente': cliente,
                'facturacion': monto,
                'porcentaje': pct,
                'porcentaje_acumulado': acumulado,
                'cantidad_operaciones': data['ops'],
                'ticket_promedio': monto / data['ops'] if data['ops'] > 0 else 0,
                'area_principal': area_principal
            })
        
        return result
    
    def _calc_top_clientes_por_localidad(self, limit: int = 5) -> Dict[str, List[Dict]]:
        """Top N clientes por localidad."""
        por_localidad = {}
        
        for localidad_val in ['MONTEVIDEO', 'MERCEDES']:
            ops_loc = [op for op in self.operaciones 
                      if op.localidad and op.localidad.value == localidad_val]
            
            analyzer_loc = ClienteAnalyzer(ops_loc)
            por_localidad[localidad_val] = analyzer_loc._calc_top_clientes_total(limit)
        
        return por_localidad
    
    def _calc_analisis_pareto(self) -> Dict[str, Any]:
        """
        Análisis Pareto 80/20.
        
        Returns:
            {
                'clientes_80_pct': int,
                'porcentaje_clientes_80': float,
                'concentracion': str ('ALTA', 'MEDIA', 'BAJA')
            }
        """
        top = self._calc_top_clientes_total(limit=1000)  # Todos
        
        total_clientes = len(top)
        if total_clientes == 0:
            return {'clientes_80_pct': 0, 'porcentaje_clientes_80': 0, 'concentracion': 'SIN_DATOS'}
        
        # Contar hasta 80%
        clientes_80 = 0
        for cliente in top:
            clientes_80 += 1
            if cliente['porcentaje_acumulado'] >= 80:
                break
        
        pct_clientes = (clientes_80 / total_clientes) * 100
        
        # Interpretación
        if pct_clientes < 15:
            concentracion = 'ALTA'
        elif pct_clientes < 30:
            concentracion = 'MEDIA'
        else:
            concentracion = 'BAJA'
        
        return {
            'clientes_80_pct': clientes_80,
            'total_clientes': total_clientes,
            'porcentaje_clientes_80': pct_clientes,
            'concentracion': concentracion
        }
    
    def _calc_indice_herfindahl(self) -> Dict[str, Any]:
        """
        Índice Herfindahl-Hirschman (HHI).
        
        HHI = Σ(cuota_mercado²)
        
        Returns:
            {'hhi': float, 'interpretacion': str, 'nivel_riesgo': str}
        """
        clientes_data = defaultdict(lambda: Decimal('0'))
        
        for op in self.operaciones:
            if op.tipo_operacion == TipoOperacion.INGRESO and op.cliente:
                clientes_data[op.cliente] += op.monto_uyu
        
        total = sum(clientes_data.values())
        if total == 0:
            return {'hhi': 0, 'interpretacion': 'Sin datos', 'nivel_riesgo': 'N/A'}
        
        # Calcular HHI
        hhi = sum((float(monto) / float(total) * 100) ** 2 for monto in clientes_data.values())
        
        # Interpretación
        if hhi < 1500:
            interpretacion = 'Baja concentración'
            nivel_riesgo = 'BAJO'
        elif hhi < 2500:
            interpretacion = 'Concentración moderada'
            nivel_riesgo = 'MEDIO'
        else:
            interpretacion = 'Alta concentración'
            nivel_riesgo = 'ALTO'
        
        return {
            'hhi': hhi,
            'interpretacion': interpretacion,
            'nivel_riesgo': nivel_riesgo
        }
    
    def _calc_distribucion_por_rango(self) -> List[Dict]:
        """Distribución de clientes por rango de facturación."""
        clientes_data = defaultdict(lambda: Decimal('0'))
        
        for op in self.operaciones:
            if op.tipo_operacion == TipoOperacion.INGRESO and op.cliente:
                clientes_data[op.cliente] += op.monto_uyu
        
        total_facturacion = sum(clientes_data.values())
        
        # Definir rangos
        rangos = [
            {'nombre': '>$10M', 'min': 10000000, 'max': float('inf')},
            {'nombre': '$5M-$10M', 'min': 5000000, 'max': 10000000},
            {'nombre': '$1M-$5M', 'min': 1000000, 'max': 5000000},
            {'nombre': '<$1M', 'min': 0, 'max': 1000000}
        ]
        
        result = []
        for rango in rangos:
            clientes_rango = [m for m in clientes_data.values() 
                            if rango['min'] <= float(m) < rango['max']]
            
            cant = len(clientes_rango)
            fact = sum(clientes_rango)
            
            result.append({
                'rango': rango['nombre'],
                'cantidad_clientes': cant,
                'facturacion_total': float(fact),
                'porcentaje_clientes': (cant / len(clientes_data) * 100) if clientes_data else 0,
                'porcentaje_facturacion': (float(fact) / float(total_facturacion) * 100) if total_facturacion > 0 else 0
            })
        
        return result
